import json
import csv
import os.path
import sys

from vesperando_core.conf.settings import Paths
from vesperando_core.utils import keys_to_int


wd: str = os.path.dirname(os.path.abspath(__file__))

def export_data(res):
    data: dict = {}
    with open(Paths.STATIC_PATH.joinpath(f"{res}.json")) as f:
        file_data = json.load(f, object_hook=keys_to_int)
        if res == "items":
            data = file_data
        else:
            data = file_data.get('entries', {})

    if not data:
        raise AssertionError("Failed to load skills data.")

    output = os.path.join(wd, "artifacts", f"{res}.csv")
    with open(output, "w") as f:
        fieldnames = data[0].keys()
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        if res == "artes":
            writer.writerows(data)
        else:
            writer.writerows(data.values())

    print("Exported to ", output)

if __name__ == "__main__":
    targets: list = sys.argv[1:]
    if not targets:
        print("Usage: export [artes|skills|items]")
    for target in targets:
        print("Exporting", target)
        if target in ["artes", "skills", "items"]:
            export_data(target)

    print("Done.")