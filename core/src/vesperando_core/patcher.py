from concurrent.futures import ThreadPoolExecutor
from typing import Callable
import ctypes
import mmap
import json
import os

from vesperando_core import data, game_types as gtypes
from vesperando_core.res.enums import EventAction, TargetType, ArteEffects
from vesperando_core.conf.settings import Paths
from vesperando_core.utils import keys_to_int


class GamePatcher:
    build_dir: str = Paths.BUILD_DIR

    def __init__(self, patcher_id: str):
        self.build_dir = os.path.join(self.build_dir, patcher_id)

    def patch_artes(self, arte_patches: dict, prog_update: Callable):
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
                prog_update()

            mm.flush()
            mm.close()

    def patch_skills(self, skill_patches: dict, prog_update: Callable):
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

                prog_update()

            mm.flush()
            mm.close()

    def patch_items(self, item_patches: dict, prog_update: Callable):
        iwd: str = os.path.join(self.build_dir, "item")
        item_file: str = os.path.join(iwd, "ITEM.DAT")
        sort_file: str = os.path.join(iwd, "ITEMSORT.DAT")

        if 'base' in item_patches:
            self.patch_items_base(item_file, item_patches['base'], prog_update)
            self.generate_item_sort(sort_file, item_patches['base'], prog_update)

        if 'custom' in item_patches:
            self.patch_items_custom(item_file, item_patches['custom'])

    @staticmethod
    def patch_items_base(target_file: str, item_patches: dict, prog_update: Callable):
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

                prog_update()

            mm.flush()
            mm.close()

    def patch_items_custom(self, target_file: str, item_patches: dict):
        pass

    @staticmethod
    def generate_item_sort(target_file: str, item_patches: dict, prog_update: Callable):
        props: list = ['id', 'phys_attack', 'magic_attack', 'phys_defense', 'magic_defense']
        id_sort: list = [0, *sorted(item_patches, key=lambda i: item_patches.get(i, {}).get(props[0], 0), reverse=True)]
        pa_sort: list = [0, *sorted(item_patches, key=lambda i: item_patches.get(i, {}).get(props[1], 0), reverse=True)]
        ma_sort: list = [0, *sorted(item_patches, key=lambda i: item_patches.get(i, {}).get(props[2], 0), reverse=True)]
        md_sort: list = [0, *sorted(item_patches, key=lambda i: item_patches.get(i, {}).get(props[4], 0), reverse=True)]
        pd_sort: list = [0, *sorted(item_patches, key=lambda i: item_patches.get(i, {}).get(props[3], 0), reverse=True)]

        count: int = len(id_sort)
        size: int = (count * 11 * 0x4) + 4

        with open(target_file, 'w+b') as f:
            f.truncate(size)
            mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_WRITE)

            # Write Header
            mm.write(count.to_bytes(4, byteorder="big"))

            # Write Entries
            for index in range(count):
                # Entry Number
                mm.write(index.to_bytes(4, byteorder="big"))
                # Item ID Check
                ## Use of this prop is unknown; just use items from ID SOrt
                mm.write(id_sort[index].to_bytes(4, byteorder="big"))
                # Phys Attack Sort
                mm.write(pa_sort[index].to_bytes(4, byteorder="big"))
                # Phys Defense Sort
                mm.write(pd_sort[index].to_bytes(4, byteorder="big"))
                # Magic Attack Sort
                mm.write(ma_sort[index].to_bytes(4, byteorder="big"))
                # Magic Defense Sort
                mm.write(md_sort[index].to_bytes(4, byteorder="big"))
                # Unknown/Unused; duplicate entry number just in case
                mm.write(index.to_bytes(4, byteorder="big"))
                # Padding
                mm.write(b'\x00' * 0x4 * 0x4)

                prog_update()

            mm.flush()
            mm.close()

    def patch_shops(self, shop_patches: dict, lang: str = "ENG", prog_track: Callable = None):
        target: str = os.path.join(self.build_dir, "language", f".{lang}.dec", "0.dec")
        assert os.path.isfile(target), f"Expected file {target}, but it does not exist."

        if 'commons' in shop_patches or 'uniques' in shop_patches:
            patches: dict = {}
            if 'commons' in shop_patches:
                patches['commons'] = shop_patches['commons']
            if 'uniques' in shop_patches:
                patches['uniques'] = shop_patches['uniques']

            self.patch_shops_precise(target, patches, prog_track)

    @staticmethod
    def patch_shops_precise(target_file: str, patches: dict, prog_track: Callable = None):
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
            for shop, items in prog_track(shop_items.items()):
                if count >= item_count: break
                for item in items:
                    shop_entry_data = gtypes.ShopItemEntry(shop, item)
                    mm.write(bytearray(shop_entry_data))

                count += 1

            mm.flush()
            mm.close()

    def patch_events(self, patches: dict, lang: str = "ENG", threads: int = 8, prog_update: Callable = None):
        from vesperando_core import data as game_data
        original_data = game_data.get_events_data()['main']

        with ThreadPoolExecutor(max_workers=threads) as executor:
            for scenario, events in patches.items():
                executor.submit(
                    self.patch_scenario,
                    f"{scenario}.dec",
                    events,
                    original_data.get(scenario, events),
                    lang,
                    prog_update
                )

    def patch_scenario(self, target_file, patches, reference, lang: str = 'ENG', prog_update: Callable = None):
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
                    case 100:
                        self.patch_battle(mm, address)

            mm.flush()
            mm.close()
            f.close()

        prog_update()

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

    @staticmethod
    def patch_battle(mm: mmap.mmap, address: int):
        mm.seek(address)
        mm.write(b'\x00' * 4)

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
    def patch_search_points(target: str, patches: dict, prog_update: Callable):
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

                prog_update()

            mm.seek(header.content_start)
            last_item_index: int = 0
            for content in contents:
                content_data = gtypes.SearchPointContentEntry(content['chance'], last_item_index, content['item_range'])
                mm.write(bytearray(content_data))

                last_item_index += content['item_range']

                prog_update()

            header.content_entries = len(contents)
            header.item_entries = len(items)
            header.item_start = mm.tell()
            for item in items:
                item_data = gtypes.SearchPointItemEntry(*item.values())
                mm.write(bytearray(item_data))

                prog_update()

            header.entry_end = mm.tell()
            mm.write("dummy\x00".encode())

            mm.seek(0)
            header.file_size = mm.size()
            mm.write(bytearray(header))

    @staticmethod
    def patch_npc_items(target: str) -> None:
        with open(target, 'r+b') as f:
            mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_WRITE)
            mm.seek(0x68)

            while mm.tell() < 0x9BC:
                mm.write(int(0).to_bytes(4, byteorder="little"))
                mm.seek(0x0C, 1)

            mm.flush()
            mm.close()

    def patch_strings(self, string_dict: dict[int, dict], lang: str = "ENG") -> None:
        str_file = Paths.B_STRING_DICT % lang
        str_path: str = os.path.join(self.build_dir, "language", str_file)

        header_size: int = ctypes.sizeof(gtypes.TSSHeader)
        with open(str_path, "r+b") as f:
            mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_WRITE)

            header = gtypes.TSSHeader.from_buffer_copy(mm.read(header_size))
            mm.seek(header.code_start)

            # Get String Entries
            entries: dict[int, gtypes.TSSStringEntry] = self.get_string_pointers(
                mm, header.code_start, header.code_length
            )
            entries_values: list[gtypes.TSSStringEntry] = [*entries.values()]

            mm.seek(header.text_start)
            strings: bytearray = bytearray(mm.read(-1))

            offset: int = 0
            for index, (addr, entry) in enumerate(entries.items()):
                new_str = string_dict.get(entry.string_id, {})

                str_jpn = new_str.get("JPN", "")
                str_default = new_str.get(lang, "")

                p_jpn = entry.pointer_jpn + offset

                enc_jpn = str_jpn.encode() if str_jpn else b""
                enc_default: bytes = str_default.encode() if str_default else b""

                written: bool = True

                term = strings.find(b"\x00", p_jpn)
                if enc_jpn:
                    del strings[p_jpn:term + 1]
                    strings[p_jpn:p_jpn] = enc_jpn + b"\x00"
                    p_default = p_jpn + len(enc_jpn) + 2

                    written = True
                else:
                    p_default = term + 1

                term = strings.find(b"\x00", p_default)
                if enc_default:
                    del strings[p_default:term + 1]
                    strings[p_default:p_default] = enc_default + b"\x00"
                    term: int = p_default + len(enc_default) + 1

                    written = True
                else:
                    term += 1

                if offset:
                    # Go to Pointer for Japanese String
                    mm.seek(addr - 0x20)
                    mm.write(int.to_bytes(p_jpn, length=4, byteorder="little"))

                    # Go to pointer for Non-JP String
                    mm.seek(addr - 0x10)
                    mm.write(int.to_bytes(p_default, length=4, byteorder="little"))

                if written:
                    if index + 1 < len(entries):
                        next_start = entries_values[index + 1].pointer_jpn
                    else:
                        next_start = len(strings)
                    offset = term - next_start

            if offset < 0:
                strings = strings[:offset]

            mm.resize(header.text_start + len(strings))
            mm.seek(header.text_start)
            mm.write(strings)

            mm.flush()
            mm.close()


    @classmethod
    def get_string_pointers(cls, mm: mmap.mmap, start: int, region_len: int) -> dict[int, gtypes.TSSStringEntry]:
        end_marker: bytes = (0xFFFFFFFF).to_bytes(4, byteorder="little")
        entries: dict[int, gtypes.TSSStringEntry] = {}

        last_entry_index: int = start
        entry_index: int = mm.find(end_marker, last_entry_index + 4, region_len)

        while entry_index >= 0:
            length: int = entry_index - last_entry_index
            new_entry: gtypes.TSSStringEntry = gtypes.TSSStringEntry.from_buffer(mm.read(length))
            entries[mm.tell()] = new_entry

            last_entry_index: int = entry_index
            entry_index: int = mm.find(end_marker, last_entry_index + 4, region_len)

        return entries

    @classmethod
    def get_string_targets(cls, patch_data: dict) -> dict[int, dict]:
        strings: dict[int, dict] = {}

        if "artes" in patch_data:
            cls.generate_desc_from_artes(patch_data["artes"], strings)

        return strings

    @classmethod
    def generate_desc_from_artes(
            cls, patch_data: dict,
            strings: dict[int, dict] = None,
            lang: str = "ENG"
    ) -> dict[int, dict]:
        if type(strings) != dict:
            strings = {}

        arte_candidates: dict = {
            aid: artes for aid, artes in data.get_artes_data().items()
            if aid in set(sum(data.get_artes_by_char().values(), []))
        }
        skill_data: dict = data.get_skills_data()

        teaching_artes: set[int] = set()
        teaching_skills: set[int] = set()
        evolving_artes: set[int] = set()
        evolving_skills: set[int] = set()

        for aid, arte in arte_candidates.items():
            patched_data: dict = patch_data.get(aid, {})
            desc_key: int = arte.get('desc_string_key', 0)
            base_details: list = []

            # Get target type
            target_type: TargetType = TargetType(patched_data.get("target_type", arte.get("target_type", 0)))
            if target_type:
                target_desc: str = cls.generate_target_type_desc(target_type)
                if target_desc:
                    base_details.append(target_desc)

            # Get Global Effects
            g_effects_src: dict = patched_data if patched_data.get("status_effect1") else arte
            for _ in range(1, 3):
                effect: int = g_effects_src.get(f"status_effect{_}", 0)
                if not effect: break

                base_details.append(cls.generate_global_effect_desc(ArteEffects(effect)))

            # Format Base Details
            if base_details:
                strings.setdefault(desc_key, {})
                strings[desc_key][lang] = " ".join(base_details)

            # Get Skills/Artes that can teach an Arte
            learn_src: dict = patched_data if patched_data.get("learn_condition1") else arte
            for _ in range(1, 4):
                if learn_src.get(f'learn_condition{_}') == 2:
                    teaching_artes.add(learn_src[f'learn_parameter{_}'])
                elif learn_src.get(f'learn_condition{_}') == 3:
                    teaching_skills.add(learn_src[f'learn_parameter{_}'])

            # Get Artes that evolve into another, and the skills required for it
            evolve_src: dict = patched_data if patched_data.get("evolve_base") else arte
            if evolve_src['evolve_base'] and evolve_src['evolve_base'] not in evolving_artes:
                evolving_artes.add(evolve_src['evolve_base'])

                for _ in range(1, 5):
                    if not evolve_src.get(f'evolve_condition{_}', 0):
                        break

                    if evolve_src[f'evolve_parameter{_}'] in evolving_skills: continue
                    evolving_skills.add(evolve_src[f'evolve_parameter{_}'])

        for aid in teaching_artes.union(evolving_artes):
            hint_details: list[str] = []
            if aid in teaching_artes: hint_details.append("Required to learn an arte.")
            if aid in evolving_artes: hint_details.append("Can change to a new arte.")

            if not hint_details: continue

            desc_key: int = arte_candidates.get(aid, {}).get("desc_string_key", 0)
            full_desc: str = strings.get(desc_key, {}).get(lang, "")
            if not full_desc:
                strings[desc_key] = {lang: full_desc}
            else:
                full_desc += "\n"
            strings[desc_key][lang] = full_desc + " ".join(hint_details)

        for sid in teaching_artes.union(evolving_artes):
            hint_details: list[str] = []
            if sid in teaching_skills: hint_details.append("Required to learn an arte.")
            if sid in evolving_skills: hint_details.append("Can change to a new arte.")

            if not hint_details: continue

            desc_key: int = skill_data.get(sid, {}).get("desc_string_key", 0)
            full_desc: str = strings.get(desc_key, {}).get(lang, "")
            if not full_desc:
                strings[desc_key] = {lang: full_desc}
            else:
                full_desc += "\n"
            strings[desc_key][lang] = full_desc + " ".join(hint_details)

        return strings


    @classmethod
    def generate_target_type_desc(cls, target_type: TargetType):
        match target_type:
            case TargetType.ENEMIES_MULTI:
                return "[Enemy Target]"
            case TargetType.ALLY:
                return "[Single Ally]"
            case TargetType.ALLY_MULTI:
                return "[Area of Effect]"
            case TargetType.ENEMIES_ONLY:
                return "[All Enemies]"
            case TargetType.ALL_ALLIES:
                return "[All Allies]"
            case TargetType.SELF:
                return "[Self]"
            case TargetType.ALLIES_ONLY:
                return "[Allies Only]"
            case _:
                return ""

    @classmethod
    def generate_global_effect_desc(cls, effect: ArteEffects):
        match effect:
            case ArteEffects.HP_RECOVERY:
                return "\u2665\x06(FS1)"
            case ArteEffects.KO_RECOVERY:
                return "\x06(SC6)\x06(FS1)"
            case ArteEffects.CURE_PHYSICAL_AILMENTS:
                return "\x06(ST4)\x06(FS3)"
            case ArteEffects.P_ATK_UP:
                return "\x06(SC1)\x06(FS1)"
            case ArteEffects.M_ATK_UP:
                return "\x06(SC3)\x06(FS1)"
            case ArteEffects.P_DEF_UP:
                return "\x06(SC2)\x06(FS1)"
            case ArteEffects.M_DEF_UP:
                return "\x06(SC4)\x06(FS1)"
            case ArteEffects.AUTO_RECOVER:
                return "\x06(SC6)\x06(FS2)"
            case ArteEffects.IRON_STANCE:
                return "\x06(SC2)\x06(FS2)"
            case ArteEffects.INVULNERABILITY:
                return "\x06(SC4)\x06(FS2)"
            case ArteEffects.CURE_MAGICAL_AILMENTS:
                return "\x06(SC7)\x06(FS3)"
            case ArteEffects.IMBUE_ELEMENT:
                return "\x06(EL5)\x06(FS2)"
            case ArteEffects.TP_RECOVERY:
                return "\x06(EL7)\x06(FS1)"
            case ArteEffects.REDUCE_DAMAGE:
                return "\x06(EL7)\x06(FS2)"
            case ArteEffects.LUCK_UP:
                return "\x06(SC3)\x06(FS2)"
            case _:
                return ""


class PatchError(Exception):
    pass

class PatchValidationError(PatchError):
    pass