import mmap


def keys_to_int(x):
    return {int(k) if k.isdigit() else k: v for k, v in x.items()}

def strip_formatting(string: str) -> str:
    return string.replace("\n", "").replace("\t", "").replace("\r", "")

def read_null_terminated_string(mm: mmap.mmap, encoding: str = 'utf-8', start: int = -1,
                                reset_position: bool = True) -> str:
    cur: int = mm.tell()
    content: bytearray = bytearray()
    if start >= 0:
        mm.seek(start)

    while mm.tell() < mm.size():
        c: bytes = mm.read(1)
        if c == '\x00'.encode():
            break

        content.extend(c)

    if reset_position:
        mm.seek(cur)

    return content.decode(encoding)

def get_alignment_from_lowest_unset_bit(alignment: int) -> int:
    bits: int = 0
    for b in range(64):
        if alignment & (1 << b) == 0:
            break

        b += 1

    return bits