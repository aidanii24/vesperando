from dotenv import load_dotenv
import ctypes
import json
import mmap
import time
import sys
import os

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

from vesperando_core.packer import GamePatchPacker
from vesperando_core import configs
from vesperando_core.game_types import VesperiaStructureEncoder, ShopItemEntry


wkd = os.path.abspath(os.path.dirname(__file__))

item_start: int = 0x980
base_shop_items: int = 1521

class ShopEvolutions:
    missable_shops_ids: set[int] = {27, 28, 29, 34, 36, 39}
    shop_evolutions: dict[int, dict] = {
        7: {'prev': None, 'next': 24},
        9: {'prev': None, 'next': 23},
        11: {'prev': None, 'next': 21},
        12: {'prev': None, 'next': 22},
        13: {'prev': None, 'next': 35},
        14: {'prev': None, 'next': 15},
        15: {'prev': 14, 'next': 37},
        16: {'prev': None, 'next': 19},
        17: {'prev': None, 'next': 41},
        19: {'prev': 19, 'next': 25},
        21: {'prev': 11, 'next': None},
        22: {'prev': 12, 'next': None},
        23: {'prev': 9, 'next': None},
        24: {'prev': 7, 'next': None},
        25: {'prev': 19, 'next': None},
        26: {'prev': None, 'next': 32},
        27: {'prev': None, 'next': 28},
        28: {'prev': 27, 'next': 29},
        29: {'prev': 29, 'next': None},
        32: {'prev': 26, 'next': 38},
        35: {'prev': 13, 'next': None},
        37: {'prev': 15, 'next': None},
        38: {'prev': 32, 'next': None},
        41: {'prev': 17, 'next': None},
    }

    @classmethod
    def find_evolution(cls, evs, base):
        if base is None or base in evs: return
        if base not in cls.shop_evolutions:
            evs.add(base)
            return

        evs.add(base)

        if cls.shop_evolutions[base]['prev'] is not None:
            cls.find_evolution(evs, cls.shop_evolutions[base]['prev'])

        if cls.shop_evolutions[base]['next'] is not None:
            cls.find_evolution(evs, cls.shop_evolutions[base]['next'])

    @classmethod
    def get_evolutions(cls, base) -> set[int]:
        if base not in cls.shop_evolutions: return set()

        evolutions: set[int] = set()
        cls.find_evolution(evolutions, base)
        return evolutions

def to_json():
    config = configs.Settings.get()
    packer = GamePatchPacker(config, "temp")

    base_dir = os.path.join(wkd, "build", "temp", "language")
    if not os.path.isdir(base_dir):
        packer.extract_scenario()

    file: str = os.path.join(base_dir, ".ENG.dec", "0.dec")
    if not os.path.isfile(file):
        packer.decompress_scenario('0')

    assert os.path.isfile(file), f"{file} does not exist"

    manifest: str = os.path.join(wkd, "artifacts", "shop_raw.json")

    item_entry_size: int = ctypes.sizeof(ShopItemEntry)

    item_entries: list[ShopItemEntry] = []

    start: float = time.time()

    with open(file, "rb") as f:
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)

        mm.seek(item_start)
        for _ in range(base_shop_items):
            item_entries.append(ShopItemEntry.from_buffer_copy(mm.read(item_entry_size)))

        mm.close()

    if not os.path.isdir(os.path.dirname(manifest)):
        os.makedirs(os.path.dirname(manifest))
    with open(manifest, "w+") as f:
        json.dump(item_entries, f, cls=VesperiaStructureEncoder, indent=4)

        f.close()

    end: float = time.time()
    print(f"[Shop Data Extraction] Time Taken: {end - start} seconds")

def generate_data():
    base_data_file: str = os.path.join(wkd, "artifacts", "shop_raw.json")
    assert os.path.isfile(base_data_file), f"{base_data_file} does not exist"

    base_data: dict = json.load(open(base_data_file))
    data: list[dict] = [{k: v for k, v in entry.items()
                         if k in ['shop_id', 'item_id']}
                        for entry in base_data]

    data_file: str = os.path.join(wkd, "artifacts", "shop.json")

    # Group items by shop
    items_by_shop: dict = {}
    for entry in data:
        items_by_shop.setdefault(entry['shop_id'], set()).add(entry['item_id'])

    # Identify Similarities and Uniques between Shop Evolution groups
    cache: dict[int, list[int]] = {}
    searched: set[int] = set()
    groups: dict[int, int] = {}
    commons: list[dict] = []
    uniques: dict[int, list[int]] = {}
    for shop, items in items_by_shop.items():
        # Immediately mark all items of a shop with no evolutions as unique
        if shop not in ShopEvolutions.shop_evolutions:
            uniques[shop] = items
            cache.setdefault(shop, []).extend(items)
            continue
        elif shop in searched and shop in cache:
            diffs: list[int] = [*set(items).difference(cache[shop])]
            if diffs:
                uniques[shop] = diffs
                cache.setdefault(shop, []).extend(diffs)
            continue

        evolutions: list[int] = sorted(ShopEvolutions.get_evolutions(shop))
        for ev_shop in evolutions:
            groups[ev_shop] = evolutions[0]

        base_commons = set.intersection(*[set(items_by_shop[ev_shop]) for ev_shop in evolutions])
        commons.append({
            'shops': evolutions,
            'items': [*base_commons]
        })

        for i in range(len(evolutions) - 1):
            # Get Unique items from current shop that is not present in other shops within the same evolution group
            ev_all = [items_by_shop[ev_shop] for ev_shop in evolutions if ev_shop != evolutions[i]]
            ev_uniques = set(items_by_shop[evolutions[i]]).difference(*ev_all)

            if ev_uniques:
                uniques[evolutions[i]] = [*ev_uniques]
                cache.setdefault(evolutions[i], []).extend([*ev_uniques])

            if len(evolutions) < 2 and i < 1: continue
            ev_shops = evolutions[i:i + 2]
            ev_commons = set(items_by_shop[ev_shops[0]]).intersection(items_by_shop[ev_shops[1]]).difference(base_commons)

            if ev_commons:
                commons.append({
                    'shops': ev_shops,
                    'items': [*ev_commons]
                })

            for ev_shop in ev_shops:
                cache.setdefault(ev_shop, []).extend(ev_commons)


        searched.update(evolutions)
        for ev_shop in evolutions:
            cache.setdefault(ev_shop, []).extend(base_commons)

    for group in commons:
        group['items'] = sorted(group['items'])

    output: dict = {
        'groups': groups,
        'missables': sorted(ShopEvolutions.missable_shops_ids),
        'items': {
            'commons': commons,
            'uniques': {shop: sorted(items) for shop, items in uniques.items()},
        }
    }

    with open(data_file, "w+") as f:
        json.dump(output, f)


if __name__ == "__main__":
    if os.getenv("ENV") == "DEBUG": os.environ["EXEC_DIR"] = os.path.dirname(os.path.abspath(__file__))

    args = sys.argv[1:]

    if "extract" in args:
        to_json()
    elif "data" in args:
        generate_data()

    sys.exit(0)