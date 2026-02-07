import ctypes
import json
import mmap
import time

from game_types import VesperiaStructureEncoder, SkillsHeader, SkillsEntry

def skills_to_json():
    test_file: str = "../builds/BTL_PACK/0010.ext/ALL.0000"

    skills_size: int = ctypes.sizeof(SkillsEntry)

    start: float = time.time()

    skills: list[SkillsEntry] = []
    strings: list[str] = []

    with open(test_file, "r+b") as f:
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)

        mm.seek(0)
        header_size: int = ctypes.sizeof(SkillsHeader)

        header : SkillsHeader = SkillsHeader.from_buffer_copy(mm.read(header_size))

        mm.seek(ctypes.sizeof(SkillsHeader))
        for count in range(header.entries):
            skills.append(SkillsEntry.from_buffer_copy(mm.read(skills_size)))

        strings = (mm.read(-1).decode('utf-8').rstrip("\x00").split("\x00"))

        mm.close()

    with open("../builds/manifests/skills.json", "w+") as f:
        manifest: dict = {"skills": skills, "strings": strings}
        json.dump(manifest, f, cls=VesperiaStructureEncoder, indent=4)

        f.close()

    end: float = time.time()
    print(f"[Writing JSON] Time taken: {end - start} seconds")

    print(f"Skills: {len(skills)} | Strings: {len(strings)}")


if __name__ == "__main__":
    skills_to_json()