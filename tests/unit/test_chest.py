import ctypes
import mmap
import json
import csv
import os

from GameMeta import IDTables
from debug import test_structure

from vesperando_core import configs
from vesperando_core.packer import GamePatchPacker
from vesperando_core.game_types import ChestHeader, ChestEntry, ChestItemEntry


chest_files_data: str = os.path.join("artifacts", "chest_files.txt")

item_table = IDTables().get_item_table()

def to_bytes():
    chest_item: ChestItemEntry = ChestItemEntry(17, 1)

    test_structure(chest_item)

def get_item_name(item_id: int) -> str:
    return item_table[item_id] if item_id in item_table else f"ID {item_id}"

def test_header(target_file):
    subject: str = "target_file"
    assert os.path.isfile(subject)

    header_size: int = ctypes.sizeof(ChestHeader)
    item_size: int = ctypes.sizeof(ChestItemEntry)

    items: list[ChestItemEntry] = []

    with open(subject, "rb") as f:
        mm = mmap.mmap(f.fileno(), 0, prot=mmap.PROT_READ)

        header: ChestHeader = ChestHeader.from_buffer_copy(mm.read(header_size))

        mm.seek(header.item_start)
        for i in range(header.item_entries):
            items.append(ChestItemEntry.from_buffer_copy(mm.read(item_size)))

        mm.close()

    for item in items:
        test_structure(item)

# TODO: Test using async functions to see if it provides better performance
def get_chest_maps() -> list[str]:
    if os.path.isfile(chest_files_data):
        print("[-!-] Using Cache!")
        with open(chest_files_data, "r") as f:
            table = [line.replace("\n", "") for line in f.readlines()]
            f.close()

        return table

    packer: GamePatchPacker = GamePatchPacker(configs.get_config(), "temp")


    work_dir: str = os.path.join("build", "temp")

    maps_dir: str = os.path.join(work_dir, "maps")

    npc: str = os.path.join(work_dir, "npc")

    if not os.path.isdir(npc) or len(os.listdir(npc)) < 290:
        packer.unpack_npc()

    game_maps: list[str] = []
    npc_files = os.listdir(npc)

    for npc_file in sorted(npc_files):
        print(f"> Processing {npc_file}")
        file_name: str = npc_file.rstrip(".DAT")
        if not os.path.isdir(os.path.join(work_dir, file_name)):
            packer.extract_map(npc_file)

        chests_file: str = os.path.join(maps_dir, file_name, f"{file_name}.tlzc.ext", "0004")
        if not os.path.isfile(chests_file):
            print(f"<!> No chest file! Expected at {chests_file}")
            continue

        extracted_file: str = chests_file + ".dec"
        game_maps.append(extracted_file)
        print(f"[-/-] Successfully extracted.")
        if not os.path.isfile(extracted_file):
            packer.decompress_data(chests_file)

    with open(chest_files_data, "w+") as f:
        formatted = [file + "\n" for file in game_maps]
        f.writelines(formatted)
        f.close()

    return game_maps

def generate_maps(dirs: list[str]):
    out_dir: str = os.path.join("artifacts")
    assert os.path.isdir(out_dir)

    output: str = os.path.join(out_dir, "maps.csv")
    with open(output, "w+") as f:
        writer = csv.writer(f)
        writer.writerow(["Filename"])
        writer.writerows([[d.split("/")[-3]] for d in dirs])

def generate_chest_table(game_maps: list[str]):
    chests: dict = {}
    for file in game_maps:
        file_name: str = file.split("/")[-3]
        if file_name == "NPC": continue
        print(f"Processing {file_name}")

        entries: dict = get_chests(file)
        chests[file_name] = entries

    output: str = os.path.join("artifacts", "chests.json")
    with open(output, "w+") as f:
        json.dump(chests, f, indent=4)

    output: str = os.path.join("artifacts", "chest_table.csv")
    with open(output, "w+") as f:
        writer = csv.writer(f)
        writer.writerow(["Chest ID", "Amount", "Item"])

        for game_map, contents in chests.items():
            writer.writerow([game_map])
            for chest, items in contents.items():
                item_list: list = items["items"]
                writer.writerow([chest, items['chest_type']])
                if len(items) > 1:
                    writer.writerows([["", item['amount'], item['item_id']] for item in item_list])

    # output: str = os.path.join("..", "helper", "artifacts", "chests.txt")
    # with open(output, "w+") as f:
    #     for game_map, contents in chests.items():
    #         f.write(f"--- {game_map} ---------------------\n")
    #         for chest, items in contents.items():
    #             f.write(f"> Chest {chest}: {[f"x{item.amount} "
    #                                          f"{item_table[item.item_id] if item.item_id in item_table
    #                                          else f"ID {item.item_id}"}" for item in items]}\n")
    #         f.write("\n")

def get_chests(target) -> dict:
    assert os.path.isfile(target), f"Expected file {target}, but it does not exist."

    header_size: int = ctypes.sizeof(ChestHeader)
    item_size: int = ctypes.sizeof(ChestItemEntry)

    chests: list[ChestEntry] = []
    chests_table: dict = {}

    with open(target, "rb") as f:
        mm = mmap.mmap(f.fileno(), 0, prot=mmap.PROT_READ)

        header: ChestHeader = ChestHeader.from_buffer_copy(mm.read(header_size))

        mm.seek(header.chest_start)
        for i in range(header.chest_entries):
            chests.append(ChestEntry.from_buffer_copy(mm.read(ctypes.sizeof(ChestEntry))))

        mm.seek(header.item_start)
        for found_chest in chests:
            chest_data: dict = {
                'chest_type': found_chest.chest_type,
                # 'scenario_begin': found_chest.scenario_begin,
                # 'scenario_end': found_chest.scenario_end,
                'items': []
            }

            for _ in range(found_chest.item_count):
                item : ChestItemEntry = ChestItemEntry.from_buffer_copy(mm.read(item_size))

                chest_data.setdefault('items', []).append(item.to_dict())

            chests_table[found_chest.chest_id] = chest_data

        mm.close()

    print(chests_table)
    return chests_table

if __name__ == "__main__":
    maps: list[str] = get_chest_maps()
    generate_maps(maps)
    generate_chest_table(maps)

