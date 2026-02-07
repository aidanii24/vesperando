import ctypes
import random
import shutil
import json
import mmap
import time
import os

from game_types import VesperiaStructureEncoder, ItemEntry, ItemSortEntry


def item_to_json():
    test_file: str = "../builds/item/ITEM.DAT"

    start: float = time.time()

    items: list[ItemEntry] = []

    with open(test_file, "r+b") as f:
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)

        items_size: int = ctypes.sizeof(ItemEntry)

        mm.seek(0)
        while True:
            data = mm.read(items_size)

            if not data or len(data) < items_size or all(b == 0 for b in data): break

            items.append(ItemEntry.from_buffer_copy(data))

        mm.close()

    with open("../builds/manifests/item.json", "w+") as f:
        manifest: dict = {"items": items}
        json.dump(manifest, f, cls=VesperiaStructureEncoder, indent=4)

        f.close()

    end: float = time.time()
    print(f"[Writing JSON] Time taken: {end - start} seconds")

    print(f"Items: {len(items)}")

def add_items(extra_items: int):
    start = time.time()

    items: list[ItemEntry] = []
    base_data: dict = {}

    with open("builds/item.json", "r") as f:
        data = json.load(f)
        base_data: dict = data["items"][1]

        items = [ItemEntry(**entry) for entry in data["items"]]

        f.close()

    base_data["picture"] = "ITEM_AP"
    for _ in range(extra_items):
        new_data: dict = base_data.copy()
        new_data["id"] = 2000 + _
        new_data["name_string_key"] += 1 + _
        new_data["buy_price"] = random.randint(1, 500) * 10
        new_data["entry"] += _ + 1

        new_entry: ItemEntry = ItemEntry(**new_data)
        items.append(new_entry)

    patch_item_sort(items[-extra_items:])

    with open(f"builds/item-r{extra_items}.dat", "x+") as f:
        f.truncate(ctypes.sizeof(ItemEntry) * len(items))
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_WRITE)

        for item in items:
            mm.write(bytearray(item))

        mm.flush()
        mm.close()

    end: float = time.time()
    print(f"[Rebuilding File and Added 100 new Items] Time taken: {end - start} seconds")


def item_from_json():
    start = time.time()

    items: list[ItemEntry] = []

    with open("../data/item.json", "r") as f:
        data = json.load(f)

        items = [ItemEntry(**entry) for entry in data["items"]]

        f.close()

    with open("builds/item-r.dat", "x+") as f:
        f.truncate(ctypes.sizeof(ItemEntry) * len(items))
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_WRITE)

        for item in items:
            mm.write(bytearray(item))

        mm.flush()
        mm.close()

    end: float = time.time()
    print(f"[Rebuilding File] Time taken: {end - start} seconds")

def patch_item_sort(items: list[ItemEntry]):
    shutil.copyfile("../builds/item/ITEMSORT.DAT", f"builds/sort-r{len(items)}.dat")

    with open(f"builds/sort-r{len(items)}.dat", "r+b") as f:
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_WRITE)

        entries: int = int.from_bytes(mm.read(4))
        entry_size: int = ctypes.sizeof(ItemSortEntry)
        data_end: int = entries * entry_size + 4
        mm.resize(data_end + entry_size * len(items))

        mm.seek(0)
        entries += len(items)
        mm.write(entries.to_bytes(4))

        mm.seek(data_end)

        for i, item in enumerate(items):
            new_item: ItemSortEntry = ItemSortEntry.from_item_generic(2000 + i, item)
            mm.write(bytearray(new_item))

        mm.flush()
        mm.close()


if __name__ == "__main__":
    item_from_json()