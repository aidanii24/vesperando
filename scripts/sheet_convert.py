import csv
import json
import os.path
import sys


def events_to_json(filename: str, output: str = ""):
    entries: dict = {}
    with open(filename) as f:
        reader = csv.DictReader(f)
        reader.fieldnames = [field[:1].lower() + field[1:] for field in reader.fieldnames]

        current_file: str = "unknown"
        for row in reader:
            try:
                address = int(row.get('address', 'unknown'), 0)
            except ValueError:
                header: str = row.get('address', "unknown")
                if header.startswith("File "):
                    current_file = header[5:]
                else:
                    current_file = "unknown"

                entries.setdefault(current_file, {})
                continue

            entry = {k: int(v, 0) for k, v in row.items() if v and k != "address"}
            entries[current_file][address] = entry

    if not output or not os.path.isdir(os.path.dirname(output)):
        path = os.path.dirname(filename)
        basename = os.path.basename(filename).rsplit(".", 1)[0] + ".json"
        output = os.path.join(path, basename)

    with open(output, "w") as f:
        json.dump(entries, f)
        f.flush()
        f.close()


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python sheet_convert.py <target> <file> [output]")
        sys.exit(1)

    target = sys.argv[1]
    file = sys.argv[2]

    if target == "events":
        events_to_json(file)