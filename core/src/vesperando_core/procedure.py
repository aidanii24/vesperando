from concurrent.futures import ThreadPoolExecutor
from enum import IntEnum
import datetime
import logging
import time
import json
import sys
import os

from vesperando_core.conf.settings import Paths, Extensions
from vesperando_core.patcher import GamePatcher
from vesperando_core import packer, configs, utils


logger = logging.getLogger(os.environ.get('LOGGER_NAME', "vesperando"))

class GamePatchProcedure:
    packer: packer.GamePatchPacker
    patcher: GamePatcher

    identifier: str = ""
    patch_data: dict
    targets: list = []

    apply_immediately = False
    clean: bool = False
    threads: int

    config: dict = {}

    def __init__(self, patch_data: str, max_threads: int = 4, apply_immediately: bool = False,
                 clean_build: bool = False):
        self.config = configs.Settings.get()
        self.patch_data = json.load(open(patch_data), object_hook=utils.keys_to_int)

        self.identifier = f"{self.patch_data.get('player', "sicily")}-{self.patch_data.get(
            'created', datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")
        )}"
        self.packer = packer.GamePatchPacker(self.config, self.identifier, apply_immediately)
        self.patcher = GamePatcher(self.identifier)
        self.threads = max_threads
        self.apply_immediately = apply_immediately
        self.clean = clean_build

    def patch(self):
        start: float = time.time()

        logger.info(f"Patch {self.identifier}")
        logger.info(f"{">":>4} {"Player:":<16} {self.patch_data.get('player', 'vesperando-player')}")
        logger.info(f"{">":>4} {"Seed:":<16} {self.patch_data.get('seed', 'unknown')}")
        logger.info(f"{">":>4} {"Generation Date:":<16} {self.patch_data.get('created', 'unknown')}")
        if sys.stdout.encoding == "utf-8":
            logger.info(f"\n{"\u2609":>4} Threads: {self.threads}")
        else:
            logger.info(f"\n{">":>4} Threads: {self.threads}")
        logger.info("")

        if 'artes' in self.patch_data or 'skills' in self.patch_data:
            self.patch_btl()

        if 'items' in self.patch_data:
            self.patch_items()

        if 'shops' in self.patch_data or 'events' in self.patch_data:
            self.patch_scenario()

        if 'chests' in self.patch_data or 'search' in self.patch_data:
            self.patch_npc()

        if self.apply_immediately:
            self.packer.apply()

        end: float = time.time()

        if self.clean:
            self.packer.clean()

        logger.info(f"\nPatch Applied. Finished in {end - start:.2f} seconds.")
        if self.apply_immediately:
            if sys.stdout.encoding == "utf-8":
                logger.info("\u2713 Automatically applied patch to the game directory.")
            else:
                logger.info("> Automatically applied patch to the game directory.")
        else:
            logger.info(f"Patch Output: {self.packer.output_dir}")

    def patch_btl(self):
        self.packer.unpack_btl()

        if 'artes' in self.patch_data:
            logger.info("> Patching Artes")
            self.packer.extract_artes()
            self.patcher.patch_artes(self.patch_data['artes'])
            self.packer.pack_artes()

        if 'skills' in self.patch_data:
            logger.info("> Patching Skills")
            self.packer.extract_skills()
            self.patcher.patch_skills(self.patch_data['skills'])
            self.packer.pack_skills()

        self.packer.pack_btl()

    def patch_items(self):
        logger.info("> Patching Items")
        self.packer.unpack_item()
        self.patcher.patch_items(self.patch_data['items'])
        self.packer.copy_to_output('item')

    def patch_scenario(self):
        self.packer.extract_scenario()

        if 'shops' in self.patch_data:
            logger.info("> Patching Shops")
            self.packer.decompress_scenario('0')
            self.patcher.patch_shops(self.patch_data['shops'])

        if 'events' in self.patch_data:
            logger.info("> Patching Events")
            files: list = [*self.patch_data['events'].keys()]

            with ThreadPoolExecutor(max_workers=self.threads) as executor:
                dec_queue = files.copy()
                if 0 in dec_queue and 'shops' in self.patch_data:
                    dec_queue.remove(0)

                for file_index in dec_queue:
                    filename: str = str(file_index)
                    executor.submit(self.packer.decompress_scenario, filename)

            self.patcher.patch_events(self.patch_data['events'], threads=self.threads)

        self.packer.pack_scenario()

    def patch_npc(self):
        self.packer.unpack_npc()

        base_dir: str = os.path.join(self.packer.build_dir, "maps")
        if 'chests' in self.patch_data:
            logger.info("> Patching Chests")

            def _extract_job(room: str, chest_path: str, dec_path: str):
                self.packer.extract_map(room)
                self.packer.decompress_data(chest_path, dec_path)

            def _pack_job(room: str, chest_path: str, dec_path: str):
                self.packer.compress_data(dec_path, chest_path)
                self.packer.pack_map(room)

            with ThreadPoolExecutor(max_workers=self.threads) as executor:
                for area in self.patch_data['chests'].keys():
                    work_dir: str = os.path.join(base_dir, area)
                    chest: str = os.path.join(work_dir, area + ".dec.ext", "0004")
                    decomp_path: str = os.path.join(work_dir, "0004")

                    executor.submit(_extract_job, area, chest, decomp_path)

            with ThreadPoolExecutor(max_workers=self.threads) as executor:
                for area, chests in self.patch_data['chests'].items():
                    executor.submit(self.patcher.patch_chests, area, chests)

            with ThreadPoolExecutor(max_workers=self.threads) as executor:
                for area in self.patch_data['chests'].keys():
                    work_dir: str = os.path.join(base_dir, area)
                    dec_data: str = os.path.join(work_dir, "0004.dec")
                    chest_data: str = os.path.join(work_dir, area + ".dec.ext", "0004")

                    executor.submit(_pack_job, area, chest_data, dec_data)

        if 'search' in self.patch_data:
            logger.info("> Patching Search Points")
            search_room: str = "FIELD"
            work_dir: str = os.path.join(base_dir, search_room)
            search_path: str = os.path.join(work_dir, f"{search_room}.dec.ext", "0005")
            decomp_path: str = os.path.join(work_dir, "0005")

            self.packer.extract_map(search_room)
            self.packer.decompress_data(search_path, decomp_path)

            self.patcher.patch_search_points(decomp_path + ".dec", self.patch_data['search'])

            self.packer.compress_data(decomp_path + ".dec", search_path)
            self.packer.pack_map(search_room)

        self.packer.copy_to_output('npc')

    def restore(self):
        packer.restore_backup(self.packer.game_dir)


if __name__ == '__main__':
    class Mode(IntEnum):
        PATCH = 0,
        SET = 1
        RESTORE = 2,

    patch_file: str = ""
    threads: int = 4
    mode: Mode = Mode.PATCH
    clean: bool = False
    apply: bool = False

    skip: bool = False
    for i, arg in enumerate(sys.argv[1:]):
        if skip:
            skip = False
            continue

        if arg in ("-h", "--help"):
            print(
                "Usage:\tToVPatcher [OPTIONS] <patch_file>"
                "\n\tPatcher for Tales of Vesperia: Definitive Edition on PC/Steam."
                "\n\n\tPatcher Options:"
                "\n\t\t-t | --threads <amount>\t\tThe number of threads to use. Default: 4." 
                "\n\t\t-c | --clean\t\t\tDelete the used builds subdirectory after patching."
                "\n\t\t-a | --apply-immediately\tImmediately apply the patched files into the game directory, "
                "and move the affected original files to a backup directory (<game_directory>/Data64/.backup)."
                "\n\n\tManagement Options"
                "\n\t\t-s | --set <output>\t\tApply the specified patch output."
                "\n\t\t-r | --restore-backup\t\tRestore Backups of the original unmodified files if present "
                "and remove all instances of patched files in the game directory"
            )
            sys.exit(0)
        elif arg in ("-t", "--threads"):
            if len(sys.argv) - 1 - i > 1 and sys.argv[i + 2].isdigit():
                threads = max(1, int(sys.argv[i + 2]))
                skip = True
        elif arg in ("-a", "--apply-immediately"):
            apply = True
        elif arg in ("-c", "--clean"):
            clean = True
        elif arg in ("-s", "--set"):
            mode = Mode.SET
        elif arg in ("-r", "--restore-backup"):
            mode = Mode.RESTORE
        elif os.path.isfile(arg) and Extensions.is_valid_patch(arg):
            patch_file = arg

    if mode == Mode.PATCH:
        try:
            assert patch_file != ""
        except AssertionError:
            print("<!> No Valid Patch File was provided!")
            sys.exit(1)

        app = GamePatchProcedure(patch_file, threads, apply, clean)
        app.patch()
        sys.exit(0)

    game_dir: str = configs.Settings.get().get('paths', {}).get('game', '')
    if mode == Mode.RESTORE:
        packer.restore_backup(game_dir)
    elif mode == Mode.SET:
        patched_path: str = patch_file
        if Extensions.is_valid_patch(patched_path):
            data = json.load(open(patch_file), object_hook=utils.keys_to_int)
            identifier = f"{data['player']}-{data['created']}"

            patched_path = os.path.join(Paths.OUTPUT_dir, identifier)

        if not os.path.isdir(patched_path):
            raise NotADirectoryError("[ERROR]\tPatch does not exist")

        packer.apply_patch(patched_path, game_dir)
