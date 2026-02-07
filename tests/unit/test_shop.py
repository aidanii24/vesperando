import ctypes
import json
import mmap
import time
import os

from game_types import VesperiaStructureEncoder, ShopItemEntry
import debug


item_start: int = 0x980
base_shop_items: int = 1521

from debug import test_structure

def to_json():
    file: str = "../builds/scenario/0/0.dec"
    assert os.path.isfile(file)

    manifest: str = "../builds/manifests/shop_items.json"

    item_entry_size: int = ctypes.sizeof(ShopItemEntry)

    item_entries: list[ShopItemEntry] = []

    start: float = time.time()

    with open(file, "rb") as f:
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)

        mm.seek(item_start)
        for _ in range(base_shop_items):
            item_entries.append(ShopItemEntry.from_buffer_copy(mm.read(item_entry_size)))

        mm.close()

    mode: str = "w+"
    if not os.path.isfile(manifest): mode = "x+"

    with open(manifest, mode) as f:
        json.dump(item_entries, f, cls=VesperiaStructureEncoder, indent=4)

        f.close()

    test_structure(item_entries[0])

    end: float = time.time()
    print(f"[Shop Data Extraction] Time Taken: {end - start} seconds")

if __name__ == "__main__":
    to_json()