import json
import csv
import os

from utils import strip_formatting

def generate_ids(mode: str = "json"):
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

    artes_id_table: dict = {arte["id"] : strip_formatting(strings[f"{str(arte['name_string_key'])}"])
                            for arte in artes
                            if str(arte['name_string_key']) in strings}

    skills_id_table: dict = {skill["id"]: strip_formatting(strings[f"{str(skill['name_string_key'])}"])
                            for skill in skills
                            if str(skill['name_string_key']) in strings}

    items_id_table: dict = {item["id"] : strip_formatting(strings[f"{str(item['name_string_key'])}"])
                            for item in items
                            if str(item['name_string_key']) in strings}

    if mode == "json":
        artes_id_table_out: str = "../artifacts/artes_id_table.json"
        skills_id_table_out: str = "../artifacts/skills_id_table.json"
        items_id_table_out: str = "../artifacts/items_id_table.json"

        with open(artes_id_table_out, "w+") as f:
            json.dump(artes_id_table, f, indent=4)

        with open(skills_id_table_out, "w+") as f:
            json.dump(skills_id_table, f, indent=4)

        with open(items_id_table_out, "w+") as f:
            json.dump(items_id_table, f, indent=4)
    elif mode == "csv":
        artes_id_table_out: str = "../artifacts/artes_id_table.csv"
        skills_id_table_out: str = "../artifacts/skills_id_table.csv"
        items_id_table_out: str = "../artifacts/items_id_table.csv"

        with open(artes_id_table_out, "w+") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Name"])
            writer.writerows(artes_id_table.items())

        with open(skills_id_table_out, "w+") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Name"])
            writer.writerows(skills_id_table.items())

        with open(items_id_table_out, "w+") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Name"])
            writer.writerows(items_id_table.items())


if __name__ == "__main__":
    generate_ids()