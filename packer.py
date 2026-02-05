import platform
import hashlib
import shutil
import json
import sys
import os

from libvespy import fps4, scenario, tlzc
from lib import complib
from config.settings import Paths, Keys


# Checksums
checksums: dict[str, str] = {
    "TOV_DE.exe": "ee3212432d063c3551f8d5eb9c8dde6d55a22240912ae9ea3411b3808bfb3827",
    "btl.svo": "bab8c0497665bd5a46f2ffabba5f4d2acc9fcdf0e4e0dd50c1b8199d3f6d7111",
    "item.svo": "d86e4e3d7df4d60c9c752f999e916d495c77b2ae321c18fe281a51464a5d4d25",
    "npc.svo": "71a7d13dc3254b6981cf88b0f6142ea3a0603e21784bfce956982a37afba1333",
    "scenario_ENG.dat": "90a1e41ae829ba7f05e289aaba87cb4699e3ed27acc9448985f6f91261da8e2d"
}

class VesperiaPacker:
    """Handler Instance for Extraction, Packing, Compressing and Decompressing files from the game."""
    vesperia_dir: str = Paths.VESPERIA
    backup_dir: str = Paths.BACKUP

    build_dir: str = Paths.BUILDS
    manifest_dir: str = Paths.MANIFESTS
    output_dir: str = Paths.OUTPUT

    apply_immediately: bool = False

    def __init__(self, patch_id: str = "singleton", apply_immediately: bool = False):
        config_present: bool = os.path.isfile(Paths.CONFIG)

        if not config_present:
            VesperiaPacker.generate_config()

        with open(Paths.CONFIG, 'r+') as file:
            data = json.load(file)

            if Keys.DEP_VESPERIA in data and data[Keys.DEP_VESPERIA]:
                self.vesperia_dir = data[Keys.DEP_VESPERIA]
                self.backup_dir = os.path.join(self.vesperia_dir, "Data64", ".backup")

            file.close()

        dependencies_error: bool = self.check_dependencies()
        if dependencies_error:
            if not config_present:
                print("\n> Some dependencies could not be automatically detected.\n"
                      "Please provide the correct paths to the dependencies in the config.json, then try again.")
                sys.exit(0)
            else:
                sys.exit(1)

        if patch_id == "singleton":
            return

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
            print("> The patched game files for this patch file has already been generated.")
            self.apply_patch()
            print("> Applied patch to game directory.")
            sys.exit(0)

    @classmethod
    def generate_config(cls):
        system: str = platform.system()

        vesperia: str = Paths.VESPERIA
        if system == "Linux":
            vesperia = os.path.join(os.path.expanduser("~"), ".steam", Paths.VESPERIA)
        elif system == "Windows":
            vesperia = os.path.join("C:\\Program Files (x86)", Paths.VESPERIA)

        with open(Paths.CONFIG, "x+") as file:
            json.dump({Keys.DEP_VESPERIA : vesperia}, file, indent=4)

            file.close()

    def check_dependencies(self):
        error_occurred: bool = False

        try:
            with open(os.path.join(self.vesperia_dir, "TOV_DE.exe"), "rb") as file:
                as_bytes = file.read()
                exec_hash = hashlib.sha256(as_bytes).hexdigest()

                assert exec_hash == checksums["TOV_DE.exe"]
                file.close()
        except AssertionError:
            error_occurred = True
            print("Wrong Dependency: The provided game executable did not meet the expected supported version."
                  "Please update the game then try again.")
        except FileNotFoundError:
            error_occurred = True
            print("Missing Dependency: The game was not found in the provided path.")

        return error_occurred

    @staticmethod
    def verify_vesperia_file(filepath: str) -> bool:
        basename = os.path.basename(filepath)

        try:
            with open(filepath, "rb") as file:
                as_bytes = file.read()
                file_hash = hashlib.sha256(as_bytes).hexdigest()

                assert file_hash == checksums[basename]

                file.close()
        except AssertionError:
            print(f"Invalid File: {basename} may have already been patched, modified, or may be corrupted.")
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
            assert self.verify_vesperia_file(original_path), \
                f"Invalid File: {basename} may have already been patched, modified, or may be corrupted."

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
        path: str = self.check_vesperia_file(os.path.join(self.vesperia_dir, Paths.BTL))

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
        path: str = self.check_vesperia_file(os.path.join(self.vesperia_dir, Paths.ITEM))
        assert os.path.isfile(path), f"Expected file {path}, but it does not exist."

        base_build: str = os.path.join(self.build_dir, "item")
        if not os.path.isdir(base_build):
            os.makedirs(base_build)

        fps4.extract(path, base_build)

    def unpack_npc(self):
        path: str = self.check_vesperia_file(os.path.join(self.vesperia_dir, Paths.NPC))
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

        decompress_name: str = f"{data_name}.tlzc"
        field_decompress: str = os.path.join(work_dir, decompress_name)
        tlzc.decompress(path, field_decompress)
        fps4.extract(field_decompress, "", os.path.join(self.manifest_dir, decompress_name + ".json"))

    @staticmethod
    def decompress_data(file: str, out: str = ""):
        assert os.path.isfile(file), f"Expected file {file}, but it does not exist."

        output: str = file if not out else out + ".tlzc"
        tlzc.decompress(file, output)

    def unpack_ui(self):
        path: str = os.path.join(self.vesperia_dir, Paths.UI)
        assert os.path.isfile(path), f"Expected file {path}, but it does not exist."

        work_dir: str = os.path.join(self.build_dir, "ui")
        if not os.path.isdir(work_dir): os.mkdir(work_dir)

        fps4.extract(path, work_dir)

    def extract_scenario(self, lang = "ENG"):
        # target: str = f"scenario_{lang}.dat"
        path: str = self.check_vesperia_file(os.path.join(self.vesperia_dir, Paths.SCENARIO))
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
        extract_dir: str = os.path.join(work_dir, data_name + ".tlzc.ext")
        assert os.path.isdir(extract_dir), f"Expected directory {extract_dir}, but it does not exist."

        manifest: str = os.path.join(self.manifest_dir, data_name + ".tlzc.json")
        assert os.path.isfile(manifest), f"Expected manifest {manifest}, but it does not exist."

        map_decompressed: str = os.path.join(work_dir, data_name + ".tlzc")
        fps4.pack_from_manifest(map_decompressed, manifest)

        data_file: str = os.path.join(self.build_dir, "npc", data_name + ".DAT")
        tlzc.compress(map_decompressed, data_file)

    @staticmethod
    def compress_data(file: str, out: str = ""):
        assert os.path.isfile(file), f"Expected file {file}, but it does not exist."
        if not out:
            if file.endswith(".tlzc"):
                output: str = file.replace(".tlzc", "")
            else:
                output: str = file
                file = file + ".tlzc"
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

    def apply_patch(self, custom_output: str = ""):
        if not custom_output and not self.apply_immediately:
            return

        print("> Applying Patch...")

        if custom_output:
            self.prepare_game(custom_output)
            shutil.copytree(custom_output, self.vesperia_dir, dirs_exist_ok=True)
        else:
            shutil.copytree(self.output_dir, self.vesperia_dir, dirs_exist_ok=True)

    def prepare_game(self, patched_path: str):
        data_dir: str = os.path.join(patched_path, "Data64")
        contents: list[str] = os.listdir(data_dir)

        if "btl" in contents:
            os.remove(os.path.join(self.vesperia_dir, Paths.BTL))

        if "item" in contents:
            os.remove(os.path.join(self.vesperia_dir, Paths.ITEM))

        if "npc" in contents:
            os.remove(os.path.join(self.vesperia_dir, Paths.NPC))

    def clean_game(self, quiet: bool = True):
        detected_patches: list[str] = []

        if os.path.isdir(os.path.join(self.vesperia_dir, "Data64", "btl")):
            detected_patches.append(os.path.join(self.vesperia_dir, "Data64", "btl"))

        if os.path.isdir(os.path.join(self.vesperia_dir, "Data64", "item")):
            detected_patches.append(os.path.join(self.vesperia_dir, "Data64", "item"))

        if os.path.isdir(os.path.join(self.vesperia_dir, "Data64", "npc")):
            detected_patches.append(os.path.join(self.vesperia_dir, "Data64", "npc"))

        if detected_patches:
            if not quiet: print("> Removing active patches...")
            for patches in detected_patches:
                shutil.rmtree(patches)

    def restore_backup(self, quiet: bool = False):
        if not os.path.isdir(self.backup_dir):
            if not quiet: print("> There is no backup to restore.")
            return

        self.clean_game()

        if not quiet: print("> Restoring Backup...")
        shutil.copytree(self.backup_dir, os.path.join(self.vesperia_dir, "Data64"), dirs_exist_ok=True)

        if not quiet: print("[-/-] Backup Restored")