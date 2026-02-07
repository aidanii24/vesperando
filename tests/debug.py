import ctypes
import struct
import json
import math

from game_types import VesperiaStructureEncoder


def test_structure(sample_struct):
    for attribute, ctype in sample_struct._fields_:
        value = getattr(sample_struct, attribute)

        if type(value) == int:
            as_hex = hex(value)
        elif type(value) == float:
            as_hex = hex(struct.unpack('<I', struct.pack('<f', value))[0])
        elif type(bytes):
            if "Array" in type(value).__name__:
                # print(type(type(value)))
                # print("Array Test:", issubclass(type(value), ctypes.Array))
                value = [*value]
                as_hex = [hex(arte_id) for arte_id in value]
            else:
                as_hex = value.hex()
        else:
            as_hex = "Unhandled"

        print(f"{attribute}: {value} | ({as_hex})")

    print(json.dumps(sample_struct, cls=VesperiaStructureEncoder, indent=4))
    as_bytes = bytearray(sample_struct)
    format_bytes(as_bytes)

def format_bytes(as_bytes: bytes):
    print(as_bytes)
    print("\n 0 1 2 3  4 5 6 7  8 9 A B  C D E F")
    for _ in range(math.ceil(len(as_bytes) / 16)):
        chunk = as_bytes[_ * 16: _ * 16 + 16].hex()
        final = ""
        for _ in range(min(4, math.ceil(len(chunk) / 4))):
            final += chunk[_ * 8: _ * 8 + 8] + " "

        print(final.upper())

import os
if __name__ == "__main__":
    test: str = "../dependencies/comptoe"

    print(os.access(test, os.X_OK))