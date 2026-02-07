import json
import os


def strip_formatting(string: str) -> str:
    return string.replace("\n", "").replace("\t", "").replace("\r", "")

class IDTables:
    manifest: str = "../builds/manifests"

    string_data: str = os.path.join(manifest, "strings.json")
    artes_data: str = os.path.join(manifest, "0004R.json")
    skills_data: str = os.path.join(manifest, "skills.json")
    items_data: str = os.path.join(manifest, "item.json")

    strings: dict = {}

    def __init__(self):
        assert os.path.isdir(self.manifest)
        assert os.path.isfile(self.string_data)

        self.strings = json.load(open(self.string_data))

    def get_artes_table(self) -> dict:
        assert os.path.isfile(self.artes_data)
        artes: dict = json.load(open(self.artes_data))["artes"]

        arte_table = {arte["id"]: strip_formatting(self.strings[f"{str(arte['name_string_key'])}"]) for arte in artes
                      if str(arte['name_string_key']) in self.strings}

        return arte_table

    def get_skills_table(self) -> dict:
        assert os.path.isfile(self.skills_data)
        skills: dict = json.load(open(self.skills_data))["skills"]

        skill_table = {skill["id"]: strip_formatting(self.strings[f"{str(skill['name_string_key'])}"])
                       for skill in skills
                       if str(skill['name_string_key']) in self.strings}

        return skill_table

    def get_item_table(self) -> dict:
        assert os.path.isfile(self.items_data)
        items: dict = json.load(open(self.items_data))["items"]

        item_table = {item["id"]: strip_formatting(self.strings[f"{str(item['name_string_key'])}"]) for item in items
                                if str(item['name_string_key']) in self.strings}

        return item_table