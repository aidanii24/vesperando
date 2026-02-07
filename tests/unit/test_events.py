from enum import IntEnum
import ctypes
import mmap
import time
import json
import csv
import os

from packer import GamePatchPacker
from game_types import TSSHeader


arte_table: dict = {}
skill_table: dict = {}
item_table: dict = {}

class InstructionType(IntEnum):
    LEARN_ARTE = 0x183
    EQUIP_ARTE = 0x327
    CHECK_ARTE = 0x8B

    LEARN_SKILL = 0x6C
    EQUIP_SKILL = 0x2A4
    CHECK_SKILL = 0x98

    LEARN_TITLE = 0x1C0
    EQUIP_TITLE = 0x27B
    CHECK_TITLE = 0x2EE

    EQUIP_ITEM1 = 0xCB
    ADD_ITEM1 = 0xCC
    GET_ITEM1 = 0XCD
    GET_ITEM2 = 0x3BB
    EQUIP_ITEM2 = 0x3BC
    ADD_ITEM2 = 0x3BD

    UNLOCK_EVENT = 0xFFFF
    CHECK_UNLOCK = 0x000F

    @classmethod
    def is_valid(cls, inst_type: int) -> bool:
        return any(inst_type == inst for inst in cls)

    @classmethod
    def get_arte_events(cls) -> list[int]:
        return [cls.LEARN_ARTE, cls.EQUIP_ARTE, cls.CHECK_ARTE]

    @classmethod
    def get_skill_events(cls) -> list[int]:
        return [cls.LEARN_SKILL, cls.EQUIP_SKILL, cls.CHECK_SKILL]

    @classmethod
    def get_title_events(cls) -> list[int]:
        return [cls.LEARN_TITLE, cls.EQUIP_TITLE, cls.CHECK_TITLE]

    @classmethod
    def get_item_types(cls) -> list[int]:
        return [cls.EQUIP_ITEM1, cls.ADD_ITEM1, cls.GET_ITEM1, cls.GET_ITEM2, cls.EQUIP_ITEM2, cls.ADD_ITEM2]

class Character(IntEnum):
    UNKNOWN = 0
    YURI = 1
    ESTELLE = 2
    KAROL = 3
    RITA = 4
    RAVEN = 5
    JUDITH = 6
    REPEDE = 7
    FLYNN = 8
    PATTY = 9

    @classmethod
    def _missing_(cls, value):
        return cls.UNKNOWN

class InstructionData:
    def __init__(self, address: int, instruction_type: int, from_check: bool, is_sub_type: bool, slot: int, data_id: int,
                 character: int):
        self.address: int = address
        self.instruction_type: int = instruction_type
        self.from_check: bool = from_check
        self.sub_type: bool = is_sub_type
        self.slot: int = slot
        self.data_id: int = data_id
        self.character: int = character

    def __new__(cls, address: int, instruction_type: int, from_check: bool, is_sub_type: bool, slot: int, data_id: int,
                character: int):
        if not InstructionType.is_valid(instruction_type): return None
        return super().__new__(cls)

    def validate(self) -> bool:
        if self.instruction_type == InstructionType.UNLOCK_EVENT and self.data_id > 1971: return False
        if (self.instruction_type == InstructionType.UNLOCK_EVENT and
                self.character > 9 or self.character < 0): return False

        return True

    def tabulate(self, raw: bool = True) -> list:
        if raw:
            values: list = [hex(self.address), self.instruction_type, self.slot, self.data_id, self.character]
            return values

        address: hex = hex(self.address)
        instruction_type: str = InstructionType(self.instruction_type).name
        data = self.data_id
        if self.instruction_type in InstructionType.get_arte_events() and data in arte_table:
            data = arte_table[data]
        elif self.instruction_type in InstructionType.get_skill_events() and data in skill_table:
            data = skill_table[data]
        elif self.instruction_type in InstructionType.get_item_types() and data in item_table:
            data = item_table[data]

        character: str = Character(self.character).name

        return[address, instruction_type, self.slot, data, character]

    def report(self) -> str:
        report: str = f"{hex(self.address)} {InstructionType(self.instruction_type).name} | "

        if self.instruction_type in InstructionType.get_arte_events():
            arte: str = arte_table[self.data_id] if self.data_id in arte_table else f"Unknown Arte {self.data_id}"
            report += f"{Character(self.character).name}'s {arte}"
        elif self.instruction_type in InstructionType.get_skill_events():
            skill: str = skill_table[self.data_id] if self.data_id in skill_table else f"Unknown Skill {self.data_id}"
            report += f"{Character(self.character).name}'s {skill}"
        elif self.instruction_type in InstructionType.get_title_events():
            report += f"{Character(self.character).name}'s Title ID {self.data_id}"
        elif self.instruction_type == InstructionType.UNLOCK_EVENT:
            if self.data_id <= 1971:
                if -1 < self.character <= 9:
                    report += f"{Character(self.character).name}-related event giving ID {self.data_id}"
                else:
                    report = ""
            else:
                report = ""
        elif self.instruction_type in InstructionType.get_item_types():
            item: str = item_table[self.data_id] if self.data_id in item_table else f"Unknown Item {self.data_id}"

            if self.instruction_type in [InstructionType.ADD_ITEM1, InstructionType.ADD_ITEM2]:
                if self.data_id <= 1971:
                    report += f"{self.slot}x "
                report += f"{item}"
            elif self.instruction_type in [InstructionType.GET_ITEM1, InstructionType.GET_ITEM2]:
                if self.data_id <= 1971:
                    report += f"{item}"
                else:
                    report += "unknown item"
            elif self.instruction_type in [InstructionType.EQUIP_ITEM1, InstructionType.EQUIP_ITEM2]:
                if self.data_id <= 1971:
                    report += f"{self.slot}x {item}"
                else:
                    report += f"{item}\t< MIGHT BE EXTRACTED FROM FUNCTION CALL >"
        else:
            report += "unknown event"

        return report

def strip_formatting(string: str) -> str:
    return string.replace("\n", "").replace("\t", "").replace("\r", "")

def get_meta_data():
    manifest: str = "../builds/manifests"
    assert os.path.isdir(manifest)

    string_data: str = os.path.join(manifest, "strings.json")
    artes_data: str = os.path.join(manifest, "0004R.json")
    skills_data: str = os.path.join(manifest, "skills.json")
    items_data: str = os.path.join(manifest, "item.json")

    assert os.path.isfile(string_data)
    assert os.path.isfile(artes_data)
    assert os.path.isfile(skills_data)
    assert os.path.isfile(items_data)

    strings = json.load(open(string_data))
    artes = json.load(open(artes_data))["artes"]
    skills = json.load(open(skills_data))["skills"]
    items = json.load(open(items_data))["items"]

    global arte_table
    arte_table = {arte["id"]: strip_formatting(strings[f"{str(arte['name_string_key'])}"]) for arte in artes
                  if str(arte['name_string_key']) in strings}

    global skill_table
    skill_table = {skill["id"]: strip_formatting(strings[f"{str(skill['name_string_key'])}"]) for skill in skills
                             if str(skill['name_string_key']) in strings}

    global item_table
    item_table = {item["id"]: strip_formatting(strings[f"{str(item['name_string_key'])}"]) for item in items
                            if str(item['name_string_key']) in strings}

def get_events() -> list[str]:
    packer: GamePatchPacker = GamePatchPacker()
    packer.check_dependencies()

    work_dir: str = os.path.join("../builds/scenario")
    assert os.path.isdir(work_dir)

    scenario: str = os.path.join(work_dir, "ENG")
    assert os.path.isdir(scenario)

    files = os.listdir(scenario)
    for file in files:
        if os.path.isdir(os.path.join(scenario, file)):
            continue

        packer.decompress_scenario(file)

    dirs = [d for d in os.listdir(scenario)
            if d.isdigit()]

    return dirs

def find_instructions(target: str) -> list[InstructionData]:
    target_file: str = os.path.join(f"./builds/scenario/{target}/{target}.dec")
    assert os.path.isfile(target_file)

    type_size: int = 2
    find_target: bytes = (0xFFFFFFFF).to_bytes(4, byteorder="little")
    find_target_event: bytes = (0xFFFF).to_bytes(2, byteorder="little")

    instructions: list[InstructionData] = []

    with open(target_file, "r+b") as f:
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)

        header = TSSHeader.from_buffer_copy(mm.read(ctypes.sizeof(TSSHeader)))

        pos: int = mm.find(find_target, header.code_start, mm.size())
        next_pos: int = mm.find(find_target, pos + 4, mm.size())

        while pos >= 0 and next_pos >= 0:
            is_sub_type: bool = False
            slot: int = 0xFFFFFF
            character: int = 0xFFFFFF

            mm.seek(pos - 0x4)
            inst_type = int.from_bytes(mm.read(type_size), byteorder="little")

            if InstructionType.is_valid(inst_type):
                if inst_type == InstructionType.EQUIP_ARTE:
                    mm.seek(pos - 0xC - 0x4)
                    data_id = int.from_bytes(mm.read(4), byteorder="little")

                    mm.seek(pos - 0x1C - 0x4)
                    slot = int.from_bytes(mm.read(1), byteorder="little")

                    mm.seek(pos - 0x28 - 0x4)
                    character = int.from_bytes(mm.read(4), byteorder="little")
                elif inst_type in InstructionType.get_item_types():
                    mm.seek(next_pos - 0x1E)
                    sub_type: int = int.from_bytes(mm.read(2), byteorder="little")
                    if sub_type == 0x203:
                        is_sub_type = True

                        mm.seek(pos - 0x1C - 0x4)
                        slot = int.from_bytes(mm.read(1), byteorder="little")

                        mm.seek(pos - 0x2C - 0x4)
                        data_id = int.from_bytes(mm.read(4), byteorder="little")
                    else:
                        mm.seek(pos - 0x18 - 0x4)
                        slot = int.from_bytes(mm.read(1), byteorder="little")

                        mm.seek(pos - 0x24 - 0x4)
                        data_id = int.from_bytes(mm.read(4), byteorder="little")
                else:
                    mm.seek(pos - 0xC - 0x4)
                    data_id = int.from_bytes(mm.read(4), byteorder="little")

                    mm.seek(pos - 0x1C - 0x4)
                    character = int.from_bytes(mm.read(4), byteorder="little")

                if inst_type != InstructionType.CHECK_UNLOCK:
                    instructions.append(InstructionData(pos, inst_type, False, is_sub_type, slot, data_id,
                                                        character))

                if inst_type in [InstructionType.CHECK_ARTE, InstructionType.CHECK_TITLE, InstructionType.CHECK_UNLOCK]:
                    event_pos: int = mm.find(find_target_event, pos + 4, next_pos)

                    is_sub_type = False
                    slot = 0xFF

                    while event_pos >= pos:
                        if event_pos % 4 == 0:
                            mm.seek(event_pos - 0x26)
                            sub_type: int = int.from_bytes(mm.read(2), byteorder="little")
                            if sub_type == 0x207:
                                is_sub_type = True
                                character = -1

                                mm.seek(event_pos)
                                inst_type = int.from_bytes(mm.read(2), byteorder="little")

                                mm.seek(event_pos - 0x24)
                                data_id = int.from_bytes(mm.read(4), byteorder="little")
                            else:
                                mm.seek(event_pos - 0x1C)
                                character = int.from_bytes(mm.read(4), byteorder="little")

                                mm.seek(event_pos)
                                inst_type = int.from_bytes(mm.read(2), byteorder="little")

                                mm.seek(event_pos - 0xC)
                                data_id = int.from_bytes(mm.read(4), byteorder="little")

                            instructions.append(InstructionData(pos, inst_type, True, is_sub_type, slot,
                                                                data_id, character))

                        event_pos: int = mm.find(find_target_event, event_pos + 4, next_pos)

            pos = next_pos
            next_pos = mm.find(find_target, pos + 4, mm.size())
            while next_pos % 4 != 0 and next_pos > pos:
                next_pos = mm.find(find_target, next_pos + 4, mm.size())

    return instructions

def get_instructions() -> dict[str, list[InstructionData]]:
    get_meta_data()

    dirs: list[str] = get_events()
    dirs.sort()
    instructions: dict[str, list[InstructionData]] = {}

    for d in dirs:
        instructions[d] = find_instructions(d)

    return instructions

def write_report(instructions: dict[str, list[InstructionData]]):
    out_dir: str = os.path.join("..", "helper", "artifacts")
    assert os.path.isdir(out_dir)

    output: str = os.path.join(out_dir, f"events.txt")
    with open(output, "w+") as f:
        for file, instruction in instructions.items():
            f.write(f"--- File {file} -------------------------\n")
            if instruction:
                count: int = 0
                for inst in instruction:
                    report: str = inst.report()
                    if report:
                        f.write(report + "\n")
                        count += 1

                if not count: f.write("Invalid Events\n")
                f.write("\n")
            else:
                f.write(f"No Events\n\n")

def write_table(instructions: dict[str, list[InstructionData]], raw = True):
    out_dir: str = os.path.join("..", "helper", "artifacts")
    assert os.path.isdir(out_dir)

    output: str = os.path.join(out_dir, f"events{"-raw" if raw else ""}.csv")
    with open(output, "w+") as f:
        writer = csv.writer(f)
        writer.writerow(["Address", "Type", "Slot", "Object", "Character"])

        for file, instruction in instructions.items():
            if not instruction or all(not inst.validate() for inst in instruction):
                continue

            writer.writerow([f"File {file}"])
            for inst in instruction:
                writer.writerow(inst.tabulate(raw))

            writer.writerow([])

def generate_report():
    start: float = time.time()

    print("--- Generating Event Report -------------------------\n")
    instructions: dict[str, list[InstructionData]] = get_instructions()
    write_report(instructions)

    end: float = time.time()
    print("\n[-/-] Finished Generating Event Report")
    print(f"> Time Taken: {end - start} seconds" )

def generate_table(raw: bool = True):
    out_dir: str = os.path.join("..", "helper", "artifacts")
    assert os.path.isdir(out_dir)

    start: float = time.time()

    print("--- Generating Event Table -------------------------\n")
    instructions: dict[str, list[InstructionData]] = get_instructions()
    write_table(instructions, raw)

    end: float = time.time()
    print("\n[-/-] Finished Generating Event Table")
    print(f"> Time Taken: {end - start} seconds")

def generate_maps(dirs: list[str]):
    out_dir: str = os.path.join("..", "artifacts")
    assert os.path.isdir(out_dir)

    output: str = os.path.join(out_dir, "maps.csv")
    with open(output, "w+") as f:
        writer = csv.writer(f)
        writer.writerow(["Filename"])
        writer.writerows([[dir] for dir in dirs])

if __name__ == "__main__":
    maps: list[str] = get_events()
    generate_maps(maps)