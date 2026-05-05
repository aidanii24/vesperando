from concurrent.futures import ThreadPoolExecutor
import ctypes
import mmap
import json
import os

from vesperando_core import game_types as gtypes
from vesperando_core.res.enums import EventAction
from vesperando_core.conf.settings import Paths
from vesperando_core.utils import keys_to_int



class GamePatcher:
    build_dir: str = Paths.BUILD_DIR

    def __init__(self, patcher_id: str):
        self.build_dir = os.path.join(self.build_dir, patcher_id)

    def patch_artes(self, arte_patches: dict):
        target: str = os.path.join(self.build_dir, "BTL_PACK", "0004.ext", "ALL.0000")

        with open(Paths.STATIC_PATH.joinpath("artes.json")) as f:
            original_data = json.load(f, object_hook=keys_to_int)['entries']

        total_searched: int = 0
        total_patched: int = 0
        patched_data: dict = {}

        candidates: set[int] = set()
        for arte in original_data:
            if arte['id'] in arte_patches:
                patched_data[arte['entry']] = {**arte, **arte_patches[arte['id']]}
                total_patched += 1

                candidates.add(arte['entry'])

            total_searched += 1
            if total_patched >= len(arte_patches):
                break

        header_size: int = ctypes.sizeof(gtypes.ArtesHeader)

        with open(target, 'r+b') as f:
            mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_WRITE)

            mm.seek(0)

            header: gtypes.ArtesHeader = gtypes.ArtesHeader.from_buffer_copy(mm.read(header_size))

            mm.seek(header_size)
            count: int = 0
            while len(patched_data) and mm.tell() < header.entry_end:
                next_entry: int = int.from_bytes(mm.read(4), byteorder="little")
                arte_entry: int = int.from_bytes(mm.read(4), byteorder="little")

                if arte_entry in candidates:
                    mm.seek(-8, 1)

                    arte_data: gtypes.ArtesEntry = gtypes.ArtesEntry(*patched_data[arte_entry].values())
                    if patched_data[arte_entry]['evolve_condition1']:
                        arte_data.can_evolve = 1

                    mm.write(bytearray(arte_data))
                    del patched_data[arte_entry]
                else:
                    mm.seek(next_entry - 8, 1)
                count += 1

            mm.flush()
            mm.close()

    def patch_skills(self, skill_patches: dict):
        target: str = os.path.join(self.build_dir, "BTL_PACK", "0010.ext", "ALL.0000")

        patches = {int(key): value for key, value in skill_patches.items()}
        if not patches:
            return

        with open(Paths.STATIC_PATH.joinpath("skills.json")) as f:
            original_data = json.load(f, object_hook=keys_to_int)['entries']

        patched_data: dict = {}
        for sid, patch in sorted(patches.items()):
            if not sid == original_data[sid]['id']:
                raise PatchValidationError(f"There was an error resolving the patch for Skill Entry {sid}")
            original_properties: dict = original_data[sid]
            patched_data[original_properties['entry']] = {**original_properties, **patch}

        header_size: int = ctypes.sizeof(gtypes.SkillsHeader)
        entry_size: int = ctypes.sizeof(gtypes.SkillsEntry)

        with open(target, 'r+b') as f:
            mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_WRITE)
            mm.seek(0)

            for entry, patch in patched_data.items():
                mm.seek(header_size + (entry * entry_size))

                skills_data: gtypes.SkillsEntry = gtypes.SkillsEntry(*patch.values())
                mm.write(bytearray(skills_data))

            mm.flush()
            mm.close()

    def patch_items(self, item_patches: dict):
        target: str = os.path.join(self.build_dir, "item", "ITEM.DAT")
        assert os.path.isfile(target), f"Expected file {target}, but it does not exist."

        if 'base' in item_patches:
            self.patch_items_base(target, item_patches['base'])

        if 'custom' in item_patches:
            self.patch_items_custom(target, item_patches['custom'])

    @staticmethod
    def patch_items_base(target_file: str, item_patches: dict):
        patches: dict[int, dict] = {int(key): value for key, value in item_patches.items()}

        with open(Paths.STATIC_PATH.joinpath("items.json")) as f:
            original_data = json.load(f, object_hook=keys_to_int)

        patched_data: dict = {}
        for entry, patch in sorted(patches.items()):
            if entry != original_data[entry]['id']:
                raise PatchValidationError(f"There was an error resolving patch data for Item ID {entry}")

            patched_data[original_data[entry]['entry']] = {**original_data[entry], **patch}

        entry_size: int = ctypes.sizeof(gtypes.ItemEntry)

        with open(target_file, 'r+b') as f:
            mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_WRITE)
            mm.seek(0)

            for entry, patch in patched_data.items():
                mm.seek(entry * entry_size)

                items_data = gtypes.ItemEntry(**patch)
                mm.write(bytearray(items_data))

            mm.flush()
            mm.close()

    def patch_items_custom(self, target_file: str, item_patches: dict):
        pass

    def patch_shops(self, shop_patches: dict, lang: str = "ENG"):
        target: str = os.path.join(self.build_dir, "language", f".{lang}.dec", "0.dec")
        assert os.path.isfile(target), f"Expected file {target}, but it does not exist."

        if 'commons' in shop_patches or 'uniques' in shop_patches:
            patches: dict = {}
            if 'commons' in shop_patches:
                patches['commons'] = shop_patches['commons']
            if 'uniques' in shop_patches:
                patches['uniques'] = shop_patches['uniques']

            self.patch_shops_precise(target, patches)

    @staticmethod
    def patch_shops_precise(target_file: str, patches: dict):
        with open(Paths.STATIC_PATH.joinpath("shop.json")) as f:
            original_data = json.load(f, object_hook=keys_to_int)

        shop_items: dict = {}
        if 'commons' in patches:
            for entry in patches['commons']:
                for shop in entry['shops']:
                    shop_items.setdefault(shop, set()).update(entry['items'])

            for entry in original_data['items']['commons']:
                m_shops: list = [shop for shop in entry['shops'] if shop in original_data['missables']]
                if not m_shops: continue
                for shop in m_shops:
                    shop_items.setdefault(shop, set()).update(entry['items'])

        if 'uniques' in patches:
            for shop, items in patches['uniques'].items():
                shop_items.setdefault(shop, set()).update(items)

            for shop in original_data['missables']:
                if shop not in original_data['items']['uniques']: continue
                shop_items.setdefault(shop, set()).update(original_data['items']['uniques'][shop])

        for shop, items in (shop_items.items()):
            shop_items[shop] = sorted(items)

        shop_items = dict(sorted(shop_items.items()))

        item_start: int = 0x980
        item_count: int = 1521

        with open(target_file, 'r+b') as f:
            mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_WRITE)
            mm.seek(item_start)

            count: int = 0
            for shop, items in shop_items.items():
                if count >= item_count: break
                for item in items:
                    shop_entry_data = gtypes.ShopItemEntry(shop, item)
                    mm.write(bytearray(shop_entry_data))

                count += 1

            mm.flush()
            mm.close()

    def patch_events(self, patches: dict, lang: str = "ENG", threads: int = 8):
        with open(Paths.STATIC_PATH.joinpath("events.json")) as f:
            original_data = json.load(f, object_hook=keys_to_int)

        with ThreadPoolExecutor(max_workers=threads) as executor:
            for scenario, events in patches.items():
                executor.submit(self.patch_scenario, f"{scenario}.dec", events, original_data[scenario], lang)

    def patch_scenario(self, target_file, patches, reference, lang: str = 'ENG'):
        target: str = os.path.join(self.build_dir, "language", f".{lang}.dec", target_file)
        with open(target, 'r+b') as f:
            mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_WRITE)

            skip_events: set = set()

            for address, properties in reference.items():
                if address in skip_events: continue

                if address in patches: properties.update(patches[address])

                action = properties.get('action', EventAction.ALLOW.value)
                event_type: int = properties.get('type', 0)

                correspondent: int = reference.get(address, {}).get('correspondent', 0)
                cor_action: int = reference.get(correspondent, {}).get('action', EventAction.ALLOW.value)

                match event_type:
                    case 10 | 20:
                        if action == EventAction.NULLIFY.value and 'character' in properties:
                            properties['target'] = 0
                        self.patch_learn_arte_skill(mm, address, properties)

                        if correspondent:
                            skip_events.add(correspondent)
                            if cor_action == EventAction.NULLIFY.value:
                                properties['target'] = 0

                            if event_type == 10:
                                self.patch_equip_arte(mm, correspondent, properties)
                            elif event_type == 20:
                                self.patch_equip_skill(mm, correspondent, properties)
                    case 30:
                        self.patch_add_item(mm, address, properties)
                    case 31:
                        if action == EventAction.NULLIFY.value and 'character' in properties:
                            properties['metadata'] = 0
                            properties['target'] = 0
                        self.patch_equip_item(mm, address, properties)
                    case 39:
                        self.patch_add_gald(mm, address, properties)

            mm.flush()
            mm.close()
            f.close()

    @staticmethod
    def patch_learn_arte_skill(mm: mmap.mmap, address: int, properties: dict):
        mm.seek(address)
        mm.write(int.to_bytes(properties['target'],2, 'little', signed=False))

        mm.seek(address - 0x10)
        mm.write(int.to_bytes(properties['character'], 1, 'little', signed=False))

    @staticmethod
    def patch_equip_arte(mm: mmap.mmap, address: int, properties: dict):
        mm.seek(address)
        mm.write(int.to_bytes(properties['target'], 2, 'little', signed=False))

        mm.seek(address - 0x1C)
        mm.write(int.to_bytes(properties['character'], 1, 'little', signed=False))

    @staticmethod
    def patch_equip_skill(mm: mmap.mmap, address: int, properties: dict):
        mm.seek(address)
        mm.write(int.to_bytes(properties['target'], 2, 'little', signed=False))

        mm.seek(address - 0x10)
        mm.write(int.to_bytes(properties['character'], 1, 'little', signed=False))

    @staticmethod
    def patch_add_item(mm: mmap.mmap, address: int, properties: dict):
        mm.seek(address)
        mm.write(int.to_bytes(properties['target'], 2, 'little', signed=False))

        mm.seek(address + 0xC)
        mm.write(int.to_bytes(properties['metadata'], 1, 'little', signed=False))

    @staticmethod
    def patch_equip_item(mm: mmap.mmap, address: int, properties: dict):
        mm.seek(address)
        mm.write(int.to_bytes(properties['target'], 2, 'little', signed=False))

        mm.seek(address - 0x10)
        mm.write(int.to_bytes(properties['metadata'], 1, 'little', signed=False))

        mm.seek(address - 0x20)
        mm.write(int.to_bytes(properties['character'], 1, 'little', signed=False))

    @staticmethod
    def patch_add_gald(mm: mmap.mmap, address: int, properties: dict):
        mm.seek(address)
        mm.write(int.to_bytes(properties['metadata'], 2, 'little', signed=False))

    def patch_chests(self, target_file: str, patches: dict):
        path: str = os.path.join(self.build_dir, "maps", target_file, "0004.dec")
        assert os.path.isfile(path), f"Expected file {path}, but it does not exist."

        header_size: int = ctypes.sizeof(gtypes.ChestHeader)
        item_size: int = ctypes.sizeof(gtypes.ChestItemEntry)

        with open(path, 'r+b') as f:
            mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_WRITE)

            header = gtypes.ChestHeader.from_buffer_copy(mm.read(header_size))

            chest_entries: list[dict] = []

            mm.seek(header.chest_start)
            for _ in range(header.chest_entries):
                chest_id: int = int.from_bytes(mm.read(4), byteorder="little")

                mm.seek(0x38, 1)
                item_count: int = int.from_bytes(mm.read(4), byteorder="little")

                chest_entries.append({
                    "chest_id": chest_id,
                    "item_count": item_count,
                })

            position: int = header.item_start
            for chest in chest_entries:
                if chest['chest_id'] in patches:
                    mm.seek(position)
                    for i, item in enumerate(patches[chest['chest_id']]['items']):
                        item = gtypes.ChestItemEntry(*item.values())
                        mm.write(bytearray(item))

                        # Break in case of mismatched item count and prevent writing to other chest's item data
                        if i - 1 >= chest['item_count']:
                            break

                # Correct position in case a chest/item is missing from the patch data
                position += chest['item_count'] * item_size

            mm.flush()
            mm.close()

    @staticmethod
    def patch_search_points(target: str, patches: dict):
        assert os.path.isfile(target), f"Expected file {target}, but it does not exist."

        header_size: int = ctypes.sizeof(gtypes.SearchPointHeader)
        content_size: int = ctypes.sizeof(gtypes.SearchPointContentEntry)
        item_size: int = ctypes.sizeof(gtypes.SearchPointItemEntry)

        definitions: list[dict] = patches['definitions']
        contents: list[dict] = patches['contents']
        items: list[dict] = patches['items']

        # The first two definitions have duplicate entries with different pools
        # Mimic the definition layout, but the BasicRandomizer will treat them as the same point
        # with the same pool
        definitions.insert(0, definitions[0])
        definitions.insert(2, definitions[2])

        content_duplicates: list[int] = [definitions[0]['content_range'], definitions[2]['content_range']]
        duplicated_contents: list = []
        duplicated_items: list = []

        last_content_range: int = 0
        last_item_range: int = 0
        for content_range in content_duplicates:
            current_contents: list = contents[last_content_range:last_content_range + content_range]

            item_range: int = sum([c['item_range'] for c in current_contents])
            current_items: list = items[last_item_range:last_item_range + item_range]

            duplicated_contents += current_contents + current_contents
            duplicated_items += current_items + current_items

            last_content_range += len(current_contents)
            last_item_range += len(current_items)

        contents = duplicated_contents + contents[last_content_range:]
        items = duplicated_items + items[last_item_range:]

        with open(target, 'r+b') as f:
            mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_WRITE)

            header = gtypes.SearchPointHeader.from_buffer_copy(mm.read(header_size))

            # Resize File
            # Add 7 bytes is for the "dummy\x00" string at the end
            data_end: int = header.content_start + len(contents) * content_size + len(items) * item_size
            new_size: int = data_end + 6

            mm.resize(new_size)

            mm.seek(header.definition_start)
            last_content_index: int = 0
            for definition in definitions:
                # Write Search Point Type
                mm.seek(0xC, 1)
                mm.write(definition['type'].to_bytes(4, byteorder="little"))

                # Write Chance to apper
                if patches.get('guarantee', False):
                    mm.seek(0x12, 1)
                    mm.write((100).to_bytes(2, byteorder="little"))

                    mm.seek(0x10, 1)
                else:
                    mm.seek(0x24, 1)

                # Write Max Use
                mm.write(definition['max_use'].to_bytes(2, byteorder="little"))

                # Write Content Start and Range
                mm.seek(0x2, 1)
                mm.write(last_content_index.to_bytes(4, byteorder="little"))
                mm.write(definition['content_range'].to_bytes(4, byteorder="little"))

                last_content_index += definition['content_range']

            mm.seek(header.content_start)
            last_item_index: int = 0
            for content in contents:
                content_data = gtypes.SearchPointContentEntry(content['chance'], last_item_index, content['item_range'])
                mm.write(bytearray(content_data))

                last_item_index += content['item_range']

            header.content_entries = len(contents)
            header.item_entries = len(items)
            header.item_start = mm.tell()
            for item in items:
                item_data = gtypes.SearchPointItemEntry(*item.values())
                mm.write(bytearray(item_data))

            header.entry_end = mm.tell()
            mm.write("dummy\x00".encode())

            mm.seek(0)
            header.file_size = mm.size()
            mm.write(bytearray(header))


class PatchError(Exception):
    pass

class PatchValidationError(PatchError):
    pass