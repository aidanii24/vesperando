import ctypes
import json
import mmap
import time

from game_types import VesperiaStructureEncoder, SearchPointHeader, SearchPointDefinitionEntry, \
    SearchPointContentEntry, SearchPointItemEntry


def search_point_to_json():
    test_file: str = "../builds/npc/FIELD/FIELD.tlzc.ext/0005.tlzc"

    start: float = time.time()

    definitions: list[SearchPointDefinitionEntry] = []
    contents: list[SearchPointContentEntry] = []
    items: list[SearchPointItemEntry] = []

    header_size: int = ctypes.sizeof(SearchPointHeader)
    definition_size: int = ctypes.sizeof(SearchPointDefinitionEntry)
    contents_size: int = ctypes.sizeof(SearchPointContentEntry)
    item_size: int = ctypes.sizeof(SearchPointItemEntry)

    with open(test_file, "r+b") as f:
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)

        header: SearchPointHeader = SearchPointHeader.from_buffer_copy(mm.read(header_size))

        mm.seek(header.definition_start)
        for i in range(header.definition_entries):
            definitions.append(SearchPointDefinitionEntry.from_buffer_copy(mm.read(definition_size)))

        mm.seek(header.content_start)
        for i in range(header.content_entries):
            contents.append(SearchPointContentEntry.from_buffer_copy(mm.read(contents_size)))

        mm.seek(header.item_start)
        for i in range(header.item_entries):
            items.append(SearchPointItemEntry.from_buffer_copy(mm.read(item_size)))

        mm.close()

    with open("../builds/manifests/search_points.json", "w+") as f:
        manifest: dict = {
            "definitions": definitions,
            "contents": contents,
            "items": items,
        }

        json.dump(manifest, f, cls=VesperiaStructureEncoder, indent=4)

        f.close()

    end: float = time.time()
    print(f"[Writing JSON] Time taken: {end - start} seconds")

def search_point_from_json():
    start = time.time()

    definitions: list[SearchPointDefinitionEntry] = []
    contents: list[SearchPointContentEntry] = []
    items: list[SearchPointItemEntry] = []

    with open("../builds/manifests/search_points.json", "r") as f:
        data = json.load(f)

        definitions = [SearchPointDefinitionEntry(**d) for d in data["definitions"]]
        contents = [SearchPointContentEntry(**c) for c in data["contents"]]
        items: list[SearchPointItemEntry] = [SearchPointItemEntry(**i) for i in data["items"]]

        f.close()

    header_size: int = ctypes.sizeof(SearchPointHeader)
    definition_size: int = ctypes.sizeof(SearchPointDefinitionEntry)
    contents_size: int = ctypes.sizeof(SearchPointContentEntry)
    item_size: int = ctypes.sizeof(SearchPointItemEntry)

    definition_entries: int = len(definitions)
    content_entries: int = len(contents)
    item_entries: int = len(items)

    definition_start: int = header_size
    contents_start: int = definition_start + definition_entries * definition_size
    item_start: int = contents_start + content_entries * contents_size
    data_end: int = item_start + item_entries * item_size

    header: SearchPointHeader = SearchPointHeader(data_end + 6,
                                                  definition_start, definition_entries,
                                                  contents_start, content_entries,
                                                  item_start, item_entries,
                                                  data_end)

    with open("builds/0005", "x+") as f:
        f.truncate(data_end + 6)
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_WRITE)

        mm.write(bytearray(header))
        for d in definitions:
            mm.write(bytearray(d))

        for c in contents:
            mm.write(bytearray(c))

        for i in items:
            mm.write(bytearray(i))

        mm.write("dummy\x00".encode())

        mm.flush()
        mm.close()

    end: float = time.time()
    print(f"[Rebuilding File] Time taken: {end - start} seconds")


if __name__ == "__main__":
    search_point_to_json()