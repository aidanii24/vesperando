import ctypes
import mmap
import time
import json
import pdb
import os

from game_types import TSSHeader, TSSStringEntry, VesperiaStructureEncoder

from debug import test_structure, format_bytes


def parse_tss():
    test_file: str = "../builds/strings/string_dic_ENG.so"
    dump_file: str = "../builds/strings/output.txt"
    extract_file: str = "../builds/manifests/strings.json"
    data_file: str = "../builds/strings/strings.json"
    stop: bytes = (0xFFFFFFFF).to_bytes(4, byteorder="little")

    header_size: int = ctypes.sizeof(TSSHeader)

    string_entries: list = []
    string_id_table: dict[int, str] = {}

    start_time: float = time.time()

    with open(test_file, "rb") as f:
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)

        header = TSSHeader.from_buffer_copy(mm.read(header_size))
        mm.seek(header.code_start)

        last_max: int = header.code_start
        stop_index: int = mm.find(stop, last_max + 4, header.code_length)

        while stop_index >= 0:
            length: int = stop_index - last_max
            new_entry: TSSStringEntry = TSSStringEntry.from_buffer(mm.read(length))
            string_entries.append(new_entry)

            last_max: int = stop_index
            stop_index = mm.find(stop, last_max + 4, header.code_length)

        for string in string_entries:
            start: int = string.pointer_eng + header.text_start

            mm.seek(start)
            end: int = mm.find("\x00".encode(), start)

            if end == -1:
                raise AssertionError(f"Cannot find String endpoint for {string.string_id}")

            if end >= string.pointer_eng:
                result = mm.read(end - start)

                try:
                    decoded = "\t" + (result.decode("utf-8"))
                    string_id_table[string.string_id] = decoded
                except UnicodeDecodeError:
                    continue

        mm.close()
        f.close()

    with open(data_file, "w+") as f:
        as_dict: dict[int, dict] = {string.string_id : string.to_json() for string in string_entries}
        json.dump(as_dict, f, cls=VesperiaStructureEncoder, indent=4)

    with open(extract_file, "w+") as f:
        json.dump(string_id_table, f, cls=VesperiaStructureEncoder, indent=4)

    end_time: float = time.time()
    print("Parsing and Dumping Time Taken:", end_time - start_time, "seconds")

    ids = [entry.string_id for entry in string_entries]
    print(f"Highest ID: {max(*ids)}")   # 966589

    print(string_entries[-1].string_id, hex(string_entries[-1].pointer_jpn), hex(string_entries[-1].pointer_eng))

def add_entry():
    test_file: str = "../builds/strings/string_dic_ENG.so"
    stop: bytes = (0xFFFFFFFF).to_bytes(4, byteorder="little")

    header_size: int = ctypes.sizeof(TSSHeader)

    test_entry: TSSStringEntry = TSSStringEntry(7, 966590, 0x2FDC02, 0x2FDC0B)
    test_string: str = "\x00テスト\x00This is a sample string! Please be careful!\x00"
    bytecode: bytes = test_entry.encode_tss()

    strings_size: int = len(test_string.encode('shift_jis'))
    additional_size: int = len(bytecode) + strings_size

    with open(test_file, "r+b") as f:
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_WRITE)

        header = TSSHeader.from_buffer_copy(mm.read(header_size))

        entries_end: int = mm.rfind(stop, header.code_start, header.code_length)
        original_size: int = mm.size()

        header.code_length += len(bytecode)
        header.text_start += len(bytecode)
        header.text_length += strings_size
        header.entry_pointer_end += len(bytecode)

        mm.seek(mm.size())
        mm.resize(mm.size() + additional_size)
        mm.write(test_string.encode('shift_jis'))

        mm.seek(entries_end)
        mm.move(entries_end + len(bytecode), entries_end, original_size - entries_end + strings_size)

        mm.seek(entries_end)
        mm.write(bytecode)

        mm.seek(0)
        mm.write(bytearray(header))

        mm.flush()
        mm.close()
        f.close()

def replace_entry():
    test_file: str = "../builds/strings/string_dic_ENG.so"
    stop: bytes = (0xFFFFFFFF).to_bytes(4, byteorder="little")

    header_size: int = ctypes.sizeof(TSSHeader)

    test_entry: TSSStringEntry = TSSStringEntry(7, 860048, 0x297B94, 0x297B95)
    str_jpn: str = "テスト\x00"
    str_eng: str = "This is a test string! Be careful!\x00"

    extra_size: int = len(str_jpn.encode()) + len(str_eng.encode())

    with open(test_file, "r+b") as f:
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_WRITE)

        header = TSSHeader.from_buffer_copy(mm.read(header_size))
        header.text_length += extra_size

        mm.seek(0)
        mm.write(bytearray(header))

        mm.seek(header.text_start)
        string_data: bytearray = bytearray(mm.read(-1))

        mm.seek(header.code_start)
        last_max: int = header.code_start
        stop_index: int = mm.find(stop, last_max + 4, header.code_length)

        offset: int = 0
        while stop_index >= 0:
            length: int = stop_index - last_max
            entry: TSSStringEntry = TSSStringEntry.from_buffer(mm.read(length))

            if entry.string_id == test_entry.string_id:
                p_eng = entry.pointer_eng + offset
                p_jpn = entry.pointer_jpn + offset

                del string_data[p_eng]
                string_data[p_eng:p_eng] = str_eng.encode()

                del string_data[p_jpn]
                string_data[p_jpn:p_jpn] = str_jpn.encode()
                offset += extra_size - 2

                entry.pointer_eng = entry.pointer_jpn + len(str_jpn.encode())

                mm.seek(-0x10, 1)
                mm.write(int.to_bytes(entry.pointer_eng, length=4, byteorder="little"))
                mm.seek(0xC, 1)

            elif offset > 0:
                entry.pointer_jpn += offset
                entry.pointer_eng += offset

                mm.seek(-0x20, 1)
                mm.write(int.to_bytes(entry.pointer_jpn, length=4, byteorder="little"))

                mm.seek(0xC, 1)
                mm.write(int.to_bytes(entry.pointer_eng, length=4, byteorder="little"))

                mm.seek(0xC, 1)

            last_max: int = stop_index
            stop_index = mm.find(stop, last_max + 4, header.code_length)

        mm.seek(header.text_start)

        content_end: int = header.text_start + len(string_data)
        mm.resize(max(mm.size(), content_end))
        mm.write(string_data)

        mm.close()
        f.close()


if __name__ == "__main__":
    parse_tss()