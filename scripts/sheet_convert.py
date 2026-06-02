import csv
import json
import os.path
import sys


def events_to_json(mf: str, vf: str, output: str = ""):
    entries: dict = {}
    with open(mf) as f:
        entries['main'] = {}

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

            entries['main'].setdefault(current_file, {})

            entry = {k: int(v, 0) for k, v in row.items() if v and k != "address"}
            entries['main'][current_file][address] = entry

    if os.path.exists(vf):
        with open(vf) as f:
            entries['var'] = {}

            reader = csv.DictReader(f)
            for row in reader:
                file, address = row.values()
                entries['var'][file] = [address]

    if not output or not os.path.isdir(os.path.dirname(output)):
        path = os.path.dirname(mf)
        basename = os.path.basename(mf).rsplit(".", 1)[0] + ".json"
        output = os.path.join(path, basename)

    with open(output, "w") as f:
        json.dump(entries, f)
        f.flush()
        f.close()

    print("Output written to {}".format(output))


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python sheet_convert.py <target> <file> [output]")
        sys.exit(1)

    target = sys.argv[1]
    main_file = sys.argv[2]
    var_file = sys.argv[3]

    if target == "events":
        events_to_json(main_file, var_file)