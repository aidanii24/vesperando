import logging
import hashlib
import shutil
import json
import sys
import os

from vesperando_core.conf.settings import Paths
from vesperando_core.lib import complib
from libvespy import fps4, scenario, tlzc


logger = logging.getLogger(os.environ.get('LOGGER_NAME', "vesperando"))

class GamePatchPacker:
    """Handler Instance for Extraction, Packing, Compressing and Decompressing files from the game."""
    game_dir: str = Paths.GAME_DIR
    backup_dir: str = Paths.BACKUP_DIR

    build_dir: str = Paths.BUILD_DIR
    manifest_dir: str = Paths.MANIFESTS_DIR
    output_dir: str = Paths.OUTPUT_dir

    checksums: dict[str, str] = {}

    apply_immediately: bool = False

    def __init__(self, config: dict, patch_id: str, apply_immediately: bool = False):
        with open(Paths.STATIC_PATH.joinpath("checksums.json")) as f:
            self.checksums: dict[str, str] = json.load(f)

        self.game_dir = config.get('paths', {}).get('game')
        self.backup_dir = os.path.join(self.game_dir, Paths.BACKUP_DIR)

        if not os.path.isdir(self.build_dir):
            os.makedirs(self.build_dir)

        build_path: str = os.path.join(self.build_dir, patch_id)
        if not os.path.isdir(build_path):
            os.makedirs(build_path)

        self.build_dir = build_path
        self.manifest_dir = os.path.join(build_path, ".manifests")

        if not os.path.isdir(self.manifest_dir):
            os.makedirs(self.manifest_dir)

        if not os.path.isdir(self.output_dir):
            os.makedirs(self.output_dir)

        self.output_dir = os.path.join(self.output_dir, patch_id)

        self.apply_immediately = apply_immediately

        if os.path.isdir(self.output_dir) and apply_immediately:
            logger.warning("The patched game files for this patch file has already been generated.")
            apply_patch(self.output_dir, self.game_dir)
            logger.info("Applied patch to game directory.")
            sys.exit(0)

    def check_dependencies(self):
        error_occurred: bool = False

        try:
            with open(os.path.join(self.game_dir, "TOV_DE.exe"), "rb") as file:
                as_bytes = file.read()
                exec_hash = hashlib.sha256(as_bytes).hexdigest()

                if not exec_hash == self.checksums["TOV_DE.exe"]:
                    raise PackerError("Wrong Dependency: The provided game executable did not meet the expected "
                                      "supported version. Please update the game then try again.")
                file.close()
        except FileNotFoundError:
            error_occurred = True
            print("Missing Dependency: The game was not found in the provided path.")

        return error_occurred

    def verify_vesperia_file(self, filepath: str) -> bool:
        basename = os.path.basename(filepath)

        try:
            with open(filepath, "rb") as file:
                as_bytes = file.read()
                file_hash = hashlib.sha256(as_bytes).hexdigest()

                if not file_hash == self.checksums[basename]:
                    raise PackerError(f"Invalid File: {basename} may have already been patched, "
                                      f"modified, or may be corrupted.")

                file.close()
        except PackerError:
            return False

        return True

    def check_vesperia_file(self, original_path: str) -> str:
        basename: str = os.path.basename(original_path)
        basedir: str = os.path.splitroot(original_path.split('Data64', maxsplit=1)[-1])[-1]
        backup_path: str = os.path.join(self.backup_dir, basedir)

        if os.path.isfile(backup_path) and self.verify_vesperia_file(backup_path):
            if self.apply_immediately and os.path.isfile(original_path):
                os.remove(original_path)

            return backup_path
        elif os.path.isfile(original_path):
            if self.verify_vesperia_file(original_path):
                raise PackerError(f"Invalid File: {basename} may have already been patched, "
                                  f"modified, or may be corrupted.")

            if not os.path.isdir(self.backup_dir):
                os.makedirs(self.backup_dir)

            if not os.path.isdir(os.path.dirname(backup_path)):
                os.makedirs(os.path.dirname(backup_path))

            shutil.copy2(original_path, backup_path)

            if self.apply_immediately:
                os.remove(original_path)

            return backup_path
        else:
            raise AssertionError(f"{basename} could not be found in the game directory.")

    def ensure_output_directory(self):
        if not os.path.isdir(self.output_dir):
            os.makedirs(self.output_dir)

    def set_build_dir(self, build_dir: str):
        self.build_dir = build_dir

    def unpack_btl(self):
        path: str = self.check_vesperia_file(os.path.join(self.game_dir, Paths.BTL))

        base_build: str = os.path.join(self.build_dir, "btl")
        if not os.path.isfile(path):
            os.mkdir(base_build)

        fps4.extract(path, base_build)

        pack_build: str = os.path.join(self.build_dir, "BTL_PACK")
        fps4.extract(os.path.join(base_build, "BTL_PACK.DAT"), pack_build,
                                os.path.join(self.manifest_dir, "BTL_PACK.DAT.json"))

    def extract_artes(self):
        path: str = os.path.join(self.build_dir, "BTL_PACK", "0004")
        assert os.path.isfile(path), f"Expected file {path}, but it does not exist."

        fps4.extract(path, manifest_dir=os.path.join(self.manifest_dir, "0004.json"))

    def extract_skills(self):
        path: str = os.path.join(self.build_dir, "BTL_PACK", "0010")
        assert os.path.isfile(path), f"Expected file {path}, but it does not exist."

        fps4.extract(path, manifest_dir=os.path.join(self.manifest_dir, "0010.json"))

    def unpack_item(self):
        path: str = self.check_vesperia_file(os.path.join(self.game_dir, Paths.ITEM))
        assert os.path.isfile(path), f"Expected file {path}, but it does not exist."

        base_build: str = os.path.join(self.build_dir, "item")
        if not os.path.isdir(base_build):
            os.makedirs(base_build)

        fps4.extract(path, base_build)

    def unpack_npc(self):
        path: str = self.check_vesperia_file(os.path.join(self.game_dir, Paths.NPC))
        base_build: str = os.path.join(self.build_dir, "npc")
        assert os.path.isfile(path), f"Expected file {path}, but it does not exist."

        fps4.extract(path, base_build)

    def extract_map(self, map_data: str):
        data_name: str = map_data if not map_data.endswith(".DAT") else map_data.replace(".DAT", "")
        data_file: str = data_name + ".DAT"

        path: str = os.path.join(self.build_dir, "npc", data_file)
        assert os.path.isfile(path), f"Expected file {path}, but it does not exist."

        work_dir: str = os.path.join(self.build_dir, "maps", data_name)
        if not os.path.isdir(work_dir): os.makedirs(work_dir)

        decompress_name: str = f"{data_name}.dec"
        field_decompress: str = os.path.join(work_dir, decompress_name)
        tlzc.decompress(path, field_decompress)
        fps4.extract(field_decompress, "", os.path.join(self.manifest_dir, decompress_name + ".json"))

    @staticmethod
    def decompress_data(file: str, out: str = ""):
        assert os.path.isfile(file), f"Expected file {file}, but it does not exist."

        output: str = file if not out else out + ".dec"
        tlzc.decompress(file, output)

    def unpack_ui(self):
        path: str = os.path.join(self.game_dir, Paths.UI)
        assert os.path.isfile(path), f"Expected file {path}, but it does not exist."

        work_dir: str = os.path.join(self.build_dir, "ui")
        if not os.path.isdir(work_dir): os.mkdir(work_dir)

        fps4.extract(path, work_dir)

    def extract_scenario(self, lang = "ENG"):
        # target: str = f"scenario_{lang}.dat"
        path: str = self.check_vesperia_file(os.path.join(self.game_dir, Paths.SCENARIO))
        assert os.path.isfile(path), f"Expected file {path}, but it does not exist."

        work_dir: str = os.path.join(self.build_dir, "language")
        if not os.path.isdir(work_dir): os.mkdir(work_dir)

        extract_dir: str = os.path.join(work_dir, "." + lang)
        if not os.path.isdir(extract_dir): os.mkdir(extract_dir)

        scenario.extract(path, extract_dir)

    def decompress_scenario(self, file: str, lang: str = "ENG"):
        assert file, f"Unexpected empty file entry."

        work_dir: str = os.path.join(self.build_dir, "language")
        if not os.path.isdir(work_dir): os.mkdir(work_dir)

        extract_dir: str = os.path.join(work_dir, "." + lang)
        if not os.path.isdir(extract_dir): os.mkdir(extract_dir)

        target: str = os.path.join(extract_dir, file)
        assert os.path.isfile(target), f"Expected file {target}, but it does not exist."

        decompress_dir: str = os.path.join(work_dir, f".{lang}.dec")
        if not os.path.isdir(decompress_dir): os.mkdir(decompress_dir)

        complib.decode(target, os.path.join(decompress_dir, file + ".dec"))

    def pack_btl(self):
        path: str = os.path.join(self.manifest_dir, "BTL_PACK.DAT.json")
        assert os.path.isfile(path), f"Expected file {path}, but it does not exist."

        self.ensure_output_directory()
        output_dir: str = os.path.join(self.output_dir, "Data64", "btl")

        shutil.copytree(os.path.join(self.build_dir, "btl"), output_dir, dirs_exist_ok=True)
        fps4.pack_from_manifest(os.path.join(output_dir, "BTL_PACK.DAT"), path)

    def pack_artes(self):
        path: str = os.path.join(self.manifest_dir, "0004.json")
        assert os.path.isfile(path), f"Expected file {path}, but it does not exist."

        fps4.pack_from_manifest(os.path.join(self.build_dir, "BTL_PACK", "0004"), path)

    def pack_skills(self):
        path: str = os.path.join(self.manifest_dir, "0010.json")
        assert os.path.isfile(path), f"Expected file {path}, but it does not exist."

        fps4.pack_from_manifest(os.path.join(self.build_dir, "BTL_PACK", "0010"), path)

    def pack_map(self, map_data: str):
        base_dir: str = os.path.join(self.build_dir, "maps")
        assert os.path.isdir(base_dir), f"Expected directory {base_dir}, but it does not exist."

        data_name: str = map_data if not map_data.endswith(".DAT") else map_data.replace(".DAT", "")
        work_dir: str = os.path.join(base_dir, data_name)
        extract_dir: str = os.path.join(work_dir, data_name + ".dec.ext")
        assert os.path.isdir(extract_dir), f"Expected directory {extract_dir}, but it does not exist."

        manifest: str = os.path.join(self.manifest_dir, data_name + ".dec.json")
        assert os.path.isfile(manifest), f"Expected manifest {manifest}, but it does not exist."

        map_decompressed: str = os.path.join(work_dir, data_name + ".dec")
        fps4.pack_from_manifest(map_decompressed, manifest)

        data_file: str = os.path.join(self.build_dir, "npc", data_name + ".DAT")
        tlzc.compress(map_decompressed, data_file)

    @staticmethod
    def compress_data(file: str, out: str = ""):
        assert os.path.isfile(file), f"Expected file {file}, but it does not exist."
        if not out:
            if file.endswith(".dec"):
                output: str = file.replace(".dec", "")
            else:
                output: str = file
                file = file + ".dec"
        else:
            output: str = out

        tlzc.compress(file, output)

    def pack_scenario(self, lang = "ENG"):
        path: str = os.path.join(self.build_dir, "language")
        main: str = os.path.join(path, "." + lang)
        dec: str = main + ".dec"
        assert os.path.isdir(path), f"Cannot find build directory for language: {lang}."
        assert os.path.isdir(main), f"Expected directory {path}, but it does not exist."
        assert os.path.isdir(dec), f"Expected file {dec}, but it does not exist."

        for dec_file in os.listdir(dec):
            file: str = os.path.join(dec, f"{dec_file}")
            out: str = os.path.join(main, dec_file.split(".")[0])

            if not os.path.isfile(file): continue

            complib.encode(file, out)

        self.ensure_output_directory()
        output_dir: str = os.path.join(self.output_dir, "Data64", "language")
        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)

        shutil.copytree(path, output_dir, dirs_exist_ok=True, ignore=shutil.ignore_patterns(".*"))

        output: str = os.path.join(output_dir, "scenario_ENG.dat")
        scenario.pack(main, output)

    def copy_to_output(self, dir_name: str, ):
        target: str = os.path.join(self.build_dir, dir_name)
        assert os.path.isdir(target), f"Cannot find {dir_name} in the build directory for the patch."

        self.ensure_output_directory()

        shutil.copytree(target, os.path.join(self.output_dir, "Data64", dir_name), dirs_exist_ok=True)

    def clean(self):
        if not os.path.isdir(self.build_dir): return
        shutil.rmtree(self.build_dir, ignore_errors=True)

    def apply(self):
        apply_patch(self.output_dir, self.game_dir)

def apply_patch(patched_path, game_dir):
    prepare_game(game_dir)
    shutil.copytree(patched_path, game_dir, dirs_exist_ok=True)

def prepare_game(game_dir: str):
    data_dir: str = os.path.join(game_dir, "Data64")
    contents: list[str] = os.listdir(data_dir)

    btl: str = os.path.join(game_dir, Paths.BTL)
    if "btl" in contents and os.path.isfile(btl):
        os.remove(btl)

    item: str = os.path.join(game_dir, Paths.ITEM)
    if "item" in contents and os.path.isfile(item):
        os.remove(item)

    npc: str = os.path.join(game_dir, Paths.NPC)
    if "npc" in contents and os.path.isfile(npc):
        os.remove(npc)

def clean_game(game_dir: str, quiet: bool = True):
    detected_patches: list[str] = []

    btl: str = os.path.join(game_dir, "Data64", "btl")
    if os.path.isdir(btl):
        detected_patches.append(btl)

    item: str = os.path.join(game_dir, "Data64", "item")
    if os.path.isdir(item):
        detected_patches.append(item)

    npc: str = os.path.join(game_dir, "Data64", "npc")
    if os.path.isdir(npc):
        detected_patches.append(npc)

    if detected_patches:
        for patches in detected_patches:
            shutil.rmtree(patches)

def restore_backup(game_dir: str, quiet: bool = False):
    backup_dir: str = os.path.join(game_dir, Paths.BACKUP_DIR)
    if not os.path.isdir(backup_dir):
        raise PackerError("Could not find backups of original game file."
                          "Please check the settings.yaml if the correct game directory is provided, "
                          "or reinstall the game.\n"
                          f"Backup Directory: {backup_dir}")

    clean_game(game_dir)

    shutil.copytree(backup_dir, os.path.join(game_dir, "Data64"), dirs_exist_ok=True)


class PackerError(Exception):
    """"""