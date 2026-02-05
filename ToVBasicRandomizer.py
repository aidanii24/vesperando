import datetime
import random
import math
import uuid
import json
import time
import sys
import os

from odfdo import Document, Table, Row

from utils import keys_to_int
from res.enums import Characters, Symbol, FatalStrikeType, SearchPointType
from config.settings import Paths


VALID_TARGETS: list[str] = [
    'artes',
    'skills',
    'items',
    'shops',
    'chests',
    'search'
]

class InputTemplate:
    artes_data_table: dict
    skills_data_table: dict

    artes_ids: dict
    skill_ids: dict
    item_ids: dict

    artes_by_char: dict[int, list[int]]
    skills_by_char: dict[int, list[int]]

    items_list: dict
    item_to_category: dict
    item_by_category: dict
    common_items: list[int] # Any valid non-key and non-DLC item
    key_items: list[int]

    seed: int
    random: random.Random

    identifier: str = "randomizer"
    patch_output: str = os.path.join(".", "patches", "randomizer.tovdepatch")
    report_output: str = os.path.join(".", "patches", "tovde-spoiler.ods")

    def __init__(self, targets: list[str], seed = random.randint(1, 0xFFFFFFFF)):
        self.seed = uuid.uuid1().int
        self.random = random.Random(seed)

        self.identifier = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")
        self.patch_output = os.path.join(".", "patches", f"{self.identifier}.tovdepatch")
        self.report_output = os.path.join(".", "patches", f"tovde-spoiler-{self.identifier}.ods")

        if not targets or 'artes' in targets:
            artes_ids_file: str = os.path.join(Paths.STATIC_DIR, 'artes_id_table.json')
            artes_data_file: str = os.path.join(Paths.STATIC_DIR, 'artes.json')

            assert os.path.isfile(artes_ids_file), f'{artes_ids_file} does not exist'
            assert os.path.isfile(artes_data_file), f'{artes_data_file} does not exist'

            self.artes_ids = json.load(open(artes_ids_file), object_hook=keys_to_int)
            artes_data = json.load(open(artes_data_file))['artes']

            artes_data_table = {}
            artes_by_char = {}
            for arte in artes_data:
                artes_data_table[int(arte['id'])] = arte

                for char in arte['character_ids']:
                    if arte['arte_type'] not in [12, 14, 15] and any(0 < chara < 10 for chara in arte['character_ids']) \
                            and arte['tp_cost'] > 0:
                        artes_by_char.setdefault(char, []).append(arte['id'])

            self.artes_data_table = artes_data_table
            self.artes_by_char = artes_by_char

        if not targets or {'artes', 'skills', 'items'}.intersection(targets):
            skills_ids_file: str = os.path.join(Paths.STATIC_DIR, 'skills_id_table.json')
            skills_data_file: str = os.path.join(Paths.STATIC_DIR, 'skills.json')
            skills_char_data_file: str = os.path.join(Paths.STATIC_DIR, 'skills_by_char.json')

            assert os.path.isfile(skills_data_file), f'{skills_ids_file} does not exist'
            assert os.path.isfile(skills_data_file), f'{skills_data_file} does not exist'
            assert os.path.isfile(skills_char_data_file), f'{skills_char_data_file} does not exist'

            self.skill_ids = json.load(open(skills_ids_file), object_hook=keys_to_int)

            self.skills_data_table = {int(skill['id']) : skill
                                      for skill in json.load(open(skills_data_file))['skills']}

            self.skills_by_char = json.load(open(skills_char_data_file), object_hook=keys_to_int)

        item_dependents: set[str] = set(targets).intersection({'items', 'shops', 'chests', 'search'})
        search_only: bool = len(item_dependents) == 1 and 'search' in item_dependents
        if not targets or item_dependents:
            items_ids_file: str = os.path.join(Paths.STATIC_DIR, "items_id_table.json")
            items_file: str = os.path.join(Paths.STATIC_DIR, "item.json")

            assert os.path.isfile(items_ids_file), f"File {items_file} does not exist."
            assert os.path.isfile(items_file), f"File {items_file} does not exist."

            self.item_ids = json.load(open(items_ids_file), object_hook=keys_to_int)
            self.items_list = json.load(open(items_file))['items']

            self.item_by_category = {}
            self.common_items = []
            self.key_items = []

            if not search_only:
                self.item_to_category = {}

            for item in self.items_list:
                self.item_by_category.setdefault(item['category'], []).append(item['id'])

                if 1 < item['category'] < 10:
                    self.common_items.append(item['id'])
                elif item['category'] == 10:
                    self.key_items.append(item['id'])

                if search_only: continue
                self.item_to_category[item['id']] = item['category']

        if not os.path.isdir("patches"):
            os.makedirs("patches")

    def random_from_distribution(self, mu: float, sigma: float, range_min: float = -math.inf,
                                 range_max: float = math.inf):
        return int(math.ceil(min(max(self.random.gauss(mu, sigma), range_min), range_max)))

    def random_from_triangular(self, minimum: int, maximum: int, mode: str = "min"):
        if mode == "max":
            return max(self.random.randint(minimum, maximum), self.random.randint(minimum, maximum))
        else:
            return min(self.random.randint(minimum, maximum), self.random.randint(minimum, maximum))

    def generate(self, targets: list, spoil: bool = False):
        output: str = self.patch_output

        patch_data: dict = {
            'version': '0.1',
            'created': self.identifier,
            'seed': self.seed,
            'player': "test",
        }

        if os.path.isfile(self.report_output):
            os.remove(self.report_output)

        if not targets or 'artes' in targets:
            artes_input = self.randomize_artes_input([arte_entry for arte_entry in self.generate_artes_input()])
            patch_data['artes'] = artes_input

        if not targets or 'skills' in targets:
            skills_input = self.randomize_skills_input(self.generate_skills_input())
            patch_data['skills'] = skills_input

        if not targets or 'items' in targets:
            items_input = self.randomize_items_input(self.generate_items_input())
            patch_data['items'] = items_input

        if not targets or 'shops' in targets:
            shop_input = self.randomize_shops_input(self.generate_shop_items_input())
            patch_data['shops'] = shop_input

        if not targets or 'chests' in targets:
            chests_input = self.randomize_chests_input(self.generate_chests_input())
            patch_data['chests'] = chests_input

        if not targets or 'search' in targets:
            patch_data['search'] = self.randomize_search_points()

        if spoil:
            self.generate_spoiler_file(dict(item for item in [*patch_data.items()][4:]))

        with open(output, 'w') as f:
            json.dump(patch_data, f, indent=4)

    @staticmethod
    def generate_artes_input():
        artes_data: str = os.path.join(Paths.STATIC_DIR, "templates", "artes_api.json")
        assert os.path.isfile(artes_data)

        return json.load(open(artes_data))

    @staticmethod
    def generate_skills_input() -> dict:
        skills_data: str = os.path.join(Paths.STATIC_DIR, "templates", "skills_api.json")
        assert os.path.isfile(skills_data)

        return json.load(open(skills_data))

    @staticmethod
    def generate_items_input() -> dict:
        items_data: str = os.path.join(Paths.STATIC_DIR, "templates", "items_api.json")
        assert os.path.isfile(items_data)

        return json.load(open(items_data))

    @staticmethod
    def generate_shop_items_input() -> dict:
        shop_items_data: str = os.path.join(Paths.STATIC_DIR, "templates", "shop_items_api.json")
        assert os.path.isfile(shop_items_data)

        return json.load(open(shop_items_data), object_hook=keys_to_int)

    @staticmethod
    def generate_chests_input() -> dict:
        chests_data: str = os.path.join(Paths.STATIC_DIR, "chests.json")
        assert os.path.isfile(chests_data)

        return json.load(open(chests_data))

    def generate_artes_report(self, patched_artes: dict) -> Table:
        report_list: list = []
        for arte in [*patched_artes.values()]:
            learn_conditions: list = []
            # Parse Learn Conditions
            for _ in range(1, 7):
                condition_id = arte[f'learn_condition{_}']
                parameter_id = arte[f'learn_parameter{_}']
                meta_id = arte[f'unknown{_ + 2}']

                if condition_id == 0:
                    if parameter_id >= 300:
                        learn_conditions.extend(["Event", "", ""])
                    else:
                        learn_conditions.extend(["" for _ in range(3)])
                elif condition_id == 1:
                    learn_conditions.extend(["Level", parameter_id, ""])
                elif condition_id == 2:
                    learn_conditions.extend(["Arte Usage", self.artes_ids[parameter_id], f"x{meta_id}"])
                elif condition_id == 3:
                    learn_conditions.extend(["Equip Skill", self.skill_ids[parameter_id], ""])
                else:
                    learn_conditions.extend(["INVALID", "!", "!"])

            # Parse Evolve Conditions
            evolve_conditions: list = [self.artes_ids[arte['evolve_base']] if arte['evolve_base'] != 0
                                       else ""]
            for _ in range(1, 5):
                condition_id = arte[f'evolve_condition{_}']
                parameter_id = arte[f'evolve_parameter{_}']

                if condition_id == 0:
                    evolve_conditions.extend(["" for _ in range(2)])
                elif condition_id == 3:
                    evolve_conditions.extend(["Equip Skill", self.skill_ids[parameter_id]])
                else:
                    evolve_conditions.extend(["INVALID", "!"])

            details: list = [
                self.artes_ids[arte['id']], arte['tp_cost'], arte['cast_time'] if arte['cast_time'] else "N/A",
                *learn_conditions, *evolve_conditions,
                FatalStrikeType(arte['fatal_strike_type']).name
            ]

            report_list.append(details)

        field_names: list[str] = ["Arte", "TP", "Cast Time",
                                  "Learn Condition 1", "Learn Parameter 1", "Learn Meta 1",
                                  "Learn Condition 2", "Learn Parameter 2", "Learn Meta 2",
                                  "Learn Condition 3", "Learn Parameter 3", "Learn Meta 3",
                                  "Learn Condition 4", "Learn Parameter 4", "Learn Meta 4",
                                  "Learn Condition 5", "Learn Parameter 5", "Learn Meta 5",
                                  "Learn Condition 6", "Learn Parameter 6", "Learn Meta 6",
                                  "Evolves From",
                                  "Evolve Condition 1", "Evolve Parameter 1",
                                  "Evolve Condition 2", "Evolve Parameter 2",
                                  "Evolve Condition 3", "Evolve Parameter 3",
                                  "Evolve Condition 4", "Evolve Parameter 4",
                                  "Fatal Strike Type"]

        report: Table = Table("ARTES")
        report.set_row_values(0, field_names)
        for i, row in enumerate(report_list):
            report.set_row_values(i + 1, row)

        return report

    def generate_skills_report(self, patched_skills: dict) -> Table:
        report_list: list = []
        for skill in [*patched_skills.values()]:
            report_list.append([
                self.skill_ids[skill['id']], skill['sp_cost'], skill['lp_cost'], Symbol(skill['symbol']).name,
                skill['symbol_weight'], 'Yes' if skill['is_equippable'] else 'No'
            ])

        field_names: list[str] = ["Skill", "SP", "LP", "Symbol", "Symbol Weight", "Equippable"]

        report: Table = Table("SKILLS")
        report.set_row_values(0, field_names)
        for i, row in enumerate(report_list):
            report.set_row_values(i + 1, row)

        return report

    def generate_items_report(self, patched_items: dict) -> Table:
        report_list: list = []
        for item in [*patched_items['base'].values()]:
            entry: list = [self.item_ids[item['id']], item['buy_price']]
            for _ in range(1, 4):
                if item[f'skill{_}']:
                    entry.extend([self.skill_ids[item[f'skill{_}']], item[f'skill{_}_lp']])
                else:
                    entry.extend(["", ""])

            report_list.append(entry)

        field_names: list[str] = ["Item", "Price", "Skill 1", "Skill 1 LP", "Skill 2", "Skill 2 LP",
                                  "Skill 3", "Skill 3 LP",]

        report: Table = Table("ITEMS")
        report.set_row_values(0, field_names)
        for i, row in enumerate(report_list):
            report.set_row_values(i + 1, row)

        return report

    def generate_shop_items_report(self, patched_items: dict) -> Table:
        # data_file: str = os.path.join(".", "artifacts", "shop_items_data.json")
        # assert os.path.isfile(data_file)

        # missable_shops_ids: set[int] = {1, 27, 28, 29, 34, 36, 39}
        shop_to_name: dict = {
            1: "Dummy",
            7: "Fortune's Market (Imperial Capital) I",
            8: "Vendor's Stall \"Vega\"",
            9: "General Store \"Regulu\" I",
            10: "Fortune's Market (Aspio)",
            11: "Fortune's Market (Nor) I",
            12: "Fortune's Market (Torim) I",
            13: "Fortune's Market (Heliord) I",
            14: "Fortune's Market (Dahngrest) I",
            15: "Fortune's Market (Dahngrest) II",
            16: "Fortune's Market (Nordopolica) I",
            17: "Fortune's Market (Mantaic) I",
            18: "General Store \"Polaris\"",
            19: "Fortune's Market (Nordopolica) II",
            20: "General Store \"Deneb\"",
            21: "Fortune's Market (Nor) II",
            22: "Fortune's Market (Torim) II",
            23: "General Store \"Regulu\" II",
            24: "Fortune's Market (Imperial Capital) II",
            25: "Fortune's Market (Nordopolica) III",
            26: "Fortune's Market I",
            27: "Vendor's Stall \"Capella\" I",
            28: "Vendor's Stall \"Capella\" II",
            29: "Vendor's Stall \"Capella\" III",
            31: "Fortune's Market (Yumanju)",
            32: "Fortune's Market II",
            33: "Fortune's Market (Aurnion 2)",
            34: "Supply Depot \"Adecor\"",
            35: "Fortune's Market (Heliord) II",
            36: "Fortune's Market (1)",
            37: "Fortune's Market (Dahngrest) III",
            38: "Fortune's Market (Aurnion 1)",
            39: "Vendor's Stall \"Mallow\"",
            40: "Guild Gormet Banquet",
            41: "Fortune's Market (Mantaic) II",
        }

        # groupings: dict = json.load(open(data_file), object_hook=utils.keys_to_int)['groups']

        processed_groups: set[int] = set()

        items_by_shop: dict = {}
        for groups in patched_items['commons']:
            processed_groups.update(groups['shops'])
            for shop in groups['shops']:
                items_by_shop.setdefault(shop, []).extend(groups['items'])

        for shop, items in patched_items['uniques'].items():
            processed_groups.add(shop)
            items_by_shop.setdefault(shop, []).extend(items)

        max_count: int = 0
        for shop, items in items_by_shop.items():
            max_count = max(max_count, len(items))
            items_by_shop[shop] = [*sorted(items)]

        max_count += 1

        report: Table = Table("SHOPS")

        for _ in range(max_count):
            report.append_row(Row(len(items_by_shop.keys())))

        count: int = 0
        for shop, items in items_by_shop.items():
            if shop < 7: continue
            report.set_column_values(count, [shop_to_name[shop],
                                             *[self.item_ids[i] for i in items],
                                             *["" for _ in range(max_count - (len(items) + 1))]])
            count += 1

        return report

    def generate_chests_report(self, patched_items: dict) -> Table:
        def _get_item_name(item_id: int) -> str:
            if item_id == 0xFFFFFFFE:
                return "Gald"
            elif item_id in self.item_ids:
                return self.item_ids[item_id]
            else:
                return str(item_id)

        name_file: str = os.path.join(Paths.STATIC_DIR, "named_npc_maps.json")
        assert os.path.isfile(name_file), f"'{name_file}' not found"

        id_to_name: dict[str, str] = json.load(open(name_file))

        report_list = []
        for area, chests in sorted(patched_items.items()):
            report_list.append([id_to_name.get(area, area)])
            for chest, contents in chests.items():
                report_list.append([(id_to_name.get(chest, chest)),
                                    _get_item_name(contents[0]['item_id']),
                                    contents[0]['amount']])
                for content in contents[1:]:
                    report_list.append(["", _get_item_name(content['item_id']), content['amount']])

        field_names: list[str] = ["Chest", "Item", "Amount"]

        report: Table = Table("CHESTS")
        report.set_row_values(0, field_names)
        for i, row in enumerate(report_list):
            report.set_row_values(i + 1, row)

        return report

    def generate_search_report(self, patched_items: dict) -> Table:
        search_point_file: str = os.path.join(Paths.STATIC_DIR, "named_search_points.json")
        assert os.path.isfile(search_point_file), f"'{search_point_file}' not found"

        search_point_names: list[str] = json.load(open(search_point_file))['FIELD']

        report_list: list = []
        last_cont_idx: int = 0
        last_itm_idx: int = 0
        for i, definition in enumerate(patched_items['definitions']):
            next_cont_end: int = last_cont_idx + definition['content_range']
            item_ranges: list[int] = []
            for content in patched_items['contents'][last_cont_idx:next_cont_end]:
                item_ranges.append(content['item_range'])

            report_list.append([search_point_names[i], SearchPointType(definition['type']).name])
            for idx, r in enumerate(item_ranges):
                report_list.append([f"Item Pool #{idx}",
                                    self.item_ids[patched_items['items'][last_itm_idx]['id']],
                                    patched_items['items'][last_itm_idx]['count']])
                last_itm_idx += 1
                if r < 2: continue

                for count in range(r - 1):
                    report_list.append(["",
                                        self.item_ids[patched_items['items'][last_itm_idx]['id']],
                                        patched_items['items'][last_itm_idx]['count']])
                    last_itm_idx += 1

            last_cont_idx = next_cont_end

        field_names: list[str] = ["Search Point", "Item", "Amount"]

        report: Table = Table("SEARCH POINTS")
        report.set_row_values(0, field_names)
        for i, row in enumerate(report_list):
            report.set_row_values(i + 1, row)

        return report

    def generate_spoiler_file(self, patch_data: dict):
        print("> Generating Spoiler...")
        reports: list[Table] = []

        for entry, data in patch_data.items():
            if entry == "artes":
                reports.append(self.generate_artes_report(data))
            elif entry == "skills":
                reports.append(self.generate_skills_report(data))
            elif entry == "items":
                reports.append(self.generate_items_report(data))
            elif entry == "shops":
                reports.append(self.generate_shop_items_report(data))
            elif entry == "chests":
                reports.append(self.generate_chests_report(data))
            elif entry == "search":
                reports.append(self.generate_search_report(data))

        if not reports or None in reports: return

        spoiler: Document = Document("spreadsheet")
        spoiler.body.clear()
        spoiler.body.extend(reports)
        spoiler.save(self.report_output)

    def randomize_artes_input(self, patch):
        # Based on average amount of character artes with evolve conditions
        evolve_opportunities: list[int] = [0, 0.0258, 0.0041, 0.0005, 0.005]
        # Based on average amount of character artes with learn conditions
        learn_opportunities: list[int] = [0, 0.75, 0.042, 0.8, 0.077]
        learn_type_opportunities: list[list[int]] = [[0, 0], [0.35, 0.05], [0.005, 0.005], [0.75, 0.05], [0.5, 0.5]]

        def _randomize_evolve(target_arte, character, count):
            target_arte[f'evolve_condition{count}'] = 3
            target_arte[f'evolve_parameter{count}'] = self.random.choice(self.skills_by_char[character])

        def _randomize_learn(target_arte, character, count):
            condition_pop: list[int] = [_ for _ in range(1 if count <= 1 else 2, 4)]
            condition_chances: list[float] = [0.6] if count <= 1 else []
            condition_chances.extend(learn_type_opportunities[count])

            meta: int = 0

            condition: int = self.random.choices(condition_pop, weights=condition_chances)[0]
            if condition == 1:
                cap_level: int = self.random.randint(5, 20)
                parameter = self.random.randint(1, cap_level)
            elif condition == 2:
                parameter: int = self.random.choice(self.artes_by_char[character])
                meta = int(math.ceil(10 * (self.random.randrange(10, 200) / 100)))
            else:
                parameter: int = self.random.choice(self.skills_by_char[character])

            target_arte[f'learn_condition{count}'] = condition
            target_arte[f'learn_parameter{count}'] = parameter
            target_arte[f'unknown{count + 2}'] = meta

        print("> Randomizing Artes...")
        new_input = {}

        r_candidates: int = 0
        r_tp: int = 0
        r_cast: int = 0
        r_fs: int = 0
        r_evolve: int = 0
        r_learn: int = 0
        for arte in patch:
            # Randomize Candidacy
            if self.random.random() <= 0.05:
                continue

            r_candidates += 1
            data = self.artes_data_table[int(arte['id'])]

            # Randomize TP Cost
            if self.random.random() <= 0.4:
                r_tp += 1
                arte['tp_cost'] = math.ceil(int(arte['tp_cost']) * (self.random.randrange(10, 200) * 0.01))

            # Randomize Cast Time
            if int(arte['cast_time']) > 0 and self.random.random() >= 0.3:
                r_cast += 1
                arte['cast_time'] = math.ceil(int(arte['cast_time']) *
                                              (self.random.randrange(10, 200) * 0.01))

            # Randomize FS Type
            if self.random.random() <= 0.75:
                r_fs += 1
                arte['fatal_strike_type'] = self.random.randrange(0, 3)

            # Randomize Evolution
            ## Only Randomize Artes with Evolve Conditions already, as other artes seems to require
            ## their arte type changed to Altered Artes to apply properly
            ## Meebo reports this wasn't necessary, but currently cannot consistently reproduce
            has_evolve: bool = False
            if arte['evolve_base']:
                has_evolve = True

                # Average Total Artes over Altered Artes Count across all Party Members
                if self.random.random() <= 0.6:   # 0.258
                    r_evolve += 1

                    arte['evolve_base'] = self.random.choice(self.artes_by_char[data['character_ids'][0]])

                    continue_iter: bool = True
                    iterations: int = 1
                    while iterations < len(evolve_opportunities):

                        if continue_iter:
                            _randomize_evolve(arte, data['character_ids'][0], iterations)
                        else:
                            arte[f'evolve_condition{iterations}'] = 0
                            arte[f'evolve_parameter{iterations}'] = 0

                        if continue_iter and self.random.random() > evolve_opportunities[iterations]:
                            continue_iter = False

                        iterations += 1

                    usage_req: int = self.random.randrange(5, 20)
                    if self.random.random() <= 0.4: math.ceil(usage_req *
                                                              (self.random.randrange(10, 100) / 100))

                    arte['learn_condition1'] = 2
                    arte['learn_parameter1'] = int(arte['id'])
                    arte['unknown3'] = usage_req
                else:
                    arte['unknown3'] = self.random.randrange(5, 20)

            # Randomize Learn Condition
            if self.random.random() < learn_opportunities[has_evolve + 1]:
                r_learn += 1
                continue_iter: bool = True
                iterations: int = 2 if has_evolve else 1
                while iterations < len(learn_opportunities):
                    if continue_iter: _randomize_learn(arte, data['character_ids'][0], iterations)
                    else:
                        arte[f"learn_condition{iterations}"] = 0
                        arte[f"learn_parameter{iterations}"] = 0
                        arte[f"unknown{iterations + 2}"] = 0

                    if continue_iter and self.random.random() > learn_opportunities[iterations]:
                        continue_iter = False

                    iterations += 1

                # If Arte has Evolve Conditions from Vanilla, remove them if Learn Condition is randomized
                if not has_evolve and arte['evolve_base']:
                    arte['evolve_base'] = 0
                    for _ in range(1, 5):
                        arte[f'evolve_condition{_}'] = 0
                        arte[f'evolve_parameter{_}'] = 0

            new_input[data['entry']] = arte

        print("--- Artes Results -------------------")
        print(f"Total Artes: {len(patch)}")

        print(f"Randomized: {r_candidates} ({r_candidates / len(patch) * 100:.2f}%)")
        print(f"Randomized TP: {r_tp} ({r_tp / r_candidates * 100:.2f}%)")
        print(f"Randomized Cast Time: {r_cast} ({r_cast / r_candidates * 100:.2f}%)")
        print(f"Randomized Fatal Strike Type: {r_fs} ({r_fs / r_candidates * 100:.2f}%)")
        print(f"Randomized Evolve Conditions: {r_evolve} ({r_evolve / r_candidates * 100:.2f}%)")
        print(f"Randomized Learn Conditions: {r_learn} ({r_learn / r_candidates * 100:.2f}%)\n")

        return new_input

    def randomize_skills_input(self, patch):
        symbol_distribution: list[float] = [0.28, 0.20, 0.27, 0.25]

        print("> Randomizing Skills...")
        new_input: dict = {}

        r_candidates: int = 0
        r_sp: int = 0
        r_lp: int = 0
        r_sym: int = 0
        r_sym_w: int = 0
        for skill in patch:
            # Randomize Candidacy
            if self.random.random() <= 0.05:
                continue

            r_candidates += 1
            data = self.skills_data_table[skill['id']]

            # Randomize SP Cost
            if skill['sp_cost'] and self.random.random() <= 0.95:
                r_sp += 1
                skill['sp_cost'] = self.random_from_distribution(7.6, 5, 0, 30)

            # Randomize LP
            if skill['lp_cost']:
                if self.random.random() <= 0.95:
                    r_lp += 1
                    base = self.random_from_distribution(329.16, 226.17, 100, 1600)
                    skill['lp_cost'] = int(max(int(math.ceil(base / 100.0)) * 10, 10) if base % 100 != 0 else base / 10)
                else:
                    skill['lp_cost'] = int(skill['lp_cost'] / 10)

            # Randomize Symbol
            if self.random.random() <= 0.75:
                r_sym += 1
                skill['symbol'] = self.random.choices([_ for _ in range(4)], symbol_distribution)[0]

            # Randomize Symbol Weight
            if self.random.random() <= 0.75:
                r_sym_w += 1
                skill['symbol_weight'] = self.random_from_distribution(3.48, 2.58, 0, 30)

            new_input[data['entry']] = skill

        print("--- Skills Results -------------------")
        print(f"Total Skills: {len(patch)}")

        print(f"Randomized: {r_candidates} ({r_candidates / len(patch) * 100:.2f}%)")
        print(f"Randomized SP: {r_sp} ({r_sp / r_candidates * 100:.2f}%)")
        print(f"Randomized LP: {r_lp} ({r_lp / r_candidates * 100:.2f}%)")
        print(f"Randomized Symbol: {r_sym} ({r_sym / r_candidates * 100:.2f}%)")
        print(f"Randomized Symbol Weight: {r_sym_w} ({r_sym_w / r_candidates * 100:.2f}%)\n")

        return new_input

    def randomize_items_input(self, patch):
        skill_opportunities: list[float] = [0.96, 0.875, 0.61]

        items_data_table: dict = {item['id'] : item for item in self.items_list}

        new_input: dict = {}
        if 'custom' in patch:
            new_input['custom'] = patch['custom']

        if 'base' not in patch:
            return new_input

        print("> Randomizing Items...")
        new_input['base'] = {}

        r_candidates: int = 0
        r_price: int = 0
        r_skills: int = 0
        for item in patch['base']:
            # Randomize Candidacy
            if self.random.random() <= 0.05:
                continue

            r_candidates += 1
            data = items_data_table[item['id']]

            characters: list[int] = []
            for i, character in enumerate(Characters):
                if data['character_usable'] & character.value > 0:
                    characters.append(i + 1)

            # Randomize Buy Price
            if item['buy_price'] and self.random.random() <= 0.95:
                r_price += 1
                item['buy_price'] = int(item['buy_price'] * (self.random.randrange(25, 200, 5) / 100))

            # Randomize Weapon Properties
            ## Main Weapons are Category ID 3, Sub Items are Category ID 4
            if data['category'] in [3, 4]:
                valid_skills: list[int] = [*set(skills for char in characters
                                                for skills in self.skills_by_char[char]
                                                if char in self.skills_by_char)]

                # Randomize Skills
                continue_iter: bool = True
                for i, opp in enumerate(skill_opportunities):
                    if continue_iter and self.random.random() < opp:
                        item[f'skill{i+1}'] = random.choice(valid_skills)
                        item[f'skill{i+1}_lp'] = self.random.randrange(10, 100, 10)
                    else:
                        item[f'skill{i + 1}'] = 0
                        item[f'skill{i + 1}_lp'] = 100

                        continue_iter = False

                    if i == 0:
                        r_skills += 1

            new_input['base'][data['entry']] = item

        print("--- Items Results -------------------")
        print(f"Total Items: {len(patch['base'])}")

        print(f"Randomized: {r_candidates} ({r_candidates / len(patch['base']) * 100:.2f}%)")
        print(f"Randomized Price: {r_price} ({r_price / r_candidates * 100:.2f}%)")
        print(f"Randomized Skills: {r_skills} ({r_skills / r_candidates * 100:.2f}%)\n")

        return new_input

    def randomize_shops_input(self, patch):
        new_input: dict = {}

        if 'custom' in patch:
            new_input['custom'] = patch['custom']

        if 'commons' not in patch and 'uniques' not in patch:
            return new_input

        def _randomize_item(itm, blacklist, stats_struct) -> int:
            category: int = self.item_to_category[itm]

            stats_struct['total'] += 1
            new_item: int = itm

            # Consumables should rarely be randomized, but guarantee randomization if duplicated
            if category == 2:
                if itm in blacklist:
                    candidacy_chance = 2.00
                    same_category_chance = 2.00
                else:
                    candidacy_chance = 0.3
                    same_category_chance = 0.4
            else:
                same_category_chance = 0.25
                if itm in blacklist:
                    candidacy_chance = 2.00
                else:
                    candidacy_chance = 0.9

            if self.random.random() <= candidacy_chance:
                stats_struct['candidates'] += 1
                # Randomize to an item of the same category
                category_candidates = [*set(self.item_by_category[category]).difference(blacklist)]
                if category_candidates and self.random.random() <= same_category_chance:
                    stats_struct['sameCategory'] += 1
                    new_item = random.choice(category_candidates)
                # Randomize to any eligible item
                else:
                    stats_struct['fullRandom'] += 1
                    new_item = random.choice([*set(self.common_items).difference(blacklist)])

            return new_item

        print("> Randomizing Shop Items...")
        stats: dict[str, int] = {
            'total' : 0,
            'candidates': 0,
            'sameCategory': 0,
            'fullRandom': 0,
        }
        items_cache: dict[int, list[int]] = {}
        new_input['commons'] = []
        for grouping in patch['commons']:
            new_grouping: dict[str, list] = grouping
            already_present: list[int] = items_cache.get(new_grouping['shops'][0], [])
            new_items = []
            for item in grouping['items']:
                # Do not randomize dummy items, Key Items and DLC
                if item not in self.common_items:
                    new_items.append(item)
                    continue

                new_items.append(_randomize_item(item, {*new_items, *already_present}, stats))

            new_grouping['items'] = new_items
            new_input['commons'].append(new_grouping)

            for ev_shop in new_grouping['shops']:
                items_cache.setdefault(ev_shop, []).extend(new_items)

        new_input['uniques'] = {}
        for shop, items in patch['uniques'].items():
            new_items = []
            already_present: list[int] = items_cache.get(shop, [])
            for item in items:
                # Do not randomize dummy items, Key Items and DLC
                if item not in self.common_items:
                    new_items.append(item)
                    continue

                new_items.append(_randomize_item(item, {*new_items, *already_present}, stats))

            new_input['uniques'][shop] = new_items

        print("--- Shop Items Results -------------------")
        print(f"Total Shop Items: {stats['total']}")

        print(f"Randomized: {stats['candidates']} ({stats['candidates'] / stats['total'] * 100:.2f}%)")
        print(f"Randomized by Same Category: "
              f"{stats['sameCategory']} ({stats['sameCategory'] / stats['candidates'] * 100:.2f}%)")
        print(f"Randomized against any Item: "
              f"{stats['fullRandom']} ({stats['fullRandom'] / stats['candidates'] * 100:.2f}%)\n")

        return new_input

    def randomize_chests_input(self, patch):
        new_input: dict = {}

        gald_id: int = 0xFFFFFFFE

        eligible_items: list[int] = [*self.common_items, gald_id]

        def _randomize_entry(itm, stats_struct) -> dict[str, int]:
            category: int = self.item_to_category.get(itm['item_id'], 0) if itm['item_id'] != gald_id else -1

            if category != -1 and (category <= 1 or category >= 10): return itm
            stats_struct['total'] += 1

            new_id: int = itm['item_id']
            new_amt: int = itm['amount']

            # Consumables should rarely be randomized, but guarantee randomization if duplicated
            candidacy_chance : float = 0.85
            same_category_chance : float = 0.2 if not category == -1 else 0.85

            if self.random.random() <= candidacy_chance:
                stats_struct['candidates'] += 1
                # Randomize to an item of the same category
                if self.random.random() <= same_category_chance:
                    if category != -1:
                        stats_struct['sameCategory'] += 1
                        new_id = random.choice(self.item_by_category[category])
                # Randomize to any eligible item
                else:
                    stats_struct['fullRandom'] += 1
                    new_id = random.choice(eligible_items)


            if new_id != gald_id and self.random.random() <= 0.1:
                stats_struct['amount'] += 1
                new_amt = self.random.randrange(1, 15)
            elif new_id == gald_id:
                stats_struct['gald_amount'] += 1
                new_amt = _randomize_gald_amount(new_amt)

            new_item: dict = {
                'item_id': new_id,
                'amount': new_amt,
            }

            return new_item

        def _randomize_gald_amount(base_amount: int) -> int:
            new_amt: int = base_amount

            if self.random.random() <= 0.9:
                if self.random.random() <= 0.5 and base_amount > 100:
                    new_amt = math.ceil(new_amt * self.random.randrange(1, 15) / 10)
                else:
                    new_amt = math.ceil(new_amt * self.random.randrange(2, 10))

            return new_amt

        print("> Randomizing Chest Items...")
        stats: dict[str, int] = {
            'total': 0,
            'candidates': 0,
            'sameCategory': 0,
            'fullRandom': 0,
            'gald_amount': 0,
            'amount': 0
        }
        for area, chests in patch.items():
            new_input[area] = {}
            for chest, items in chests.items():
                new_input[area][chest] = []
                for item in items:
                    if item['item_id'] == gald_id or 1 < self.item_to_category.get(item['item_id'], 0) < 10:
                        new_input[area][chest].append(_randomize_entry(item, stats))
                    else:
                        new_input[area][chest].append(item)

        print("--- Chests Results -------------------")
        print(f"Total Chest Items: {stats['total']}")

        print(f"Randomized: {stats['candidates']} ({stats['candidates'] / stats['total'] * 100:.2f}%)")
        print(f"Randomized by Same Category: "
              f"{stats['sameCategory']} ({stats['sameCategory'] / stats['candidates'] * 100:.2f}%)")
        print(f"Randomized against any Item: "
              f"{stats['fullRandom']} ({stats['fullRandom'] / stats['candidates'] * 100:.2f}%)")
        print(f"Randomized Amount: "
              f"{stats['amount']} ({stats['amount'] / stats['candidates'] * 100:.2f}%)")
        print(f"Randomized Gald: "
              f"{stats['gald_amount']} ({stats['gald_amount'] / stats['candidates'] * 100:.2f}%)\n")

        return new_input

    def randomize_search_points(self):
        def _randomize_item() -> int:
            if self.random.random() <= 0.7:
                return random.choice(self.item_by_category[9])
            else:
                return random.choice(self.common_items)

        print("> Randomizing Search Points Items...")
        new_input: dict = {
            'guarantee': True,
            'definitions': [],
            'contents': [],
            'items': []
        }

        r_def_conts: list[int] = []
        r_cont_itms: list[int] = []

        for _ in range(88):
            content_range: int = self.random_from_triangular(1, 5)
            new_input['definitions'].append({
                "type": self.random.randint(0, 3),
                "content_range": content_range,
                "max_use": self.random_from_triangular(1, 5)
            })

            item_ranges: list[int] = [self.random.randint(1, 5) for _ in range(content_range)]
            for r in item_ranges:
                new_input['contents'].append({
                    "item_range": r,
                    "chance": self.random_from_triangular(1, 10, "max") * 10
                })

            for _ in range(sum(item_ranges)):
                new_input['items'].append({
                    'id': _randomize_item(),
                    'count': self.random_from_triangular(1, 15)
                })

            r_def_conts.append(content_range)
            r_cont_itms.extend(item_ranges)

        print("--- Search Point Results -------------------")
        print(f"Total Item Pools: {len(new_input['contents'])}")
        print(f"Total Items: {len(new_input['items'])}")
        print(f"Average Item Pools per Search Point: {sum(r_def_conts) / len(r_def_conts):.2f}")
        print(f"Average Items per Item Pool: {sum(r_cont_itms) / len(r_cont_itms):.2f}\n")

        return new_input


if __name__ == "__main__":
    target_list: list[str] = []
    create_spoiler: bool = False

    scanning_content: int = 0
    for index, arg in enumerate(sys.argv[1:]):
        if arg in ("-h", "--help"):
            print(
                "Usage:\tToVBasicRandomizer [OPTIONS] [TARGETS]"
                "\n\tA basic randomizer for use with ToVPatcher."
                "\n\n\tOptions:"
                "\n\t\t-s | --spoil\tCreate spoiler file."
                f"\n\n\tTargets: {" | ".join(VALID_TARGETS)}"
                "\n\tSpecifies targets to randomize. When left unspecified, will randomize all targets."
            )
            sys.exit(0)
        elif arg in ("-s", "--spoil"):
            create_spoiler = True
        elif str(arg).lower() in VALID_TARGETS:
            target_list.append(str(arg).lower())

    start: float = time.time()

    template = InputTemplate(target_list)
    template.generate(target_list, create_spoiler)

    total: float = time.time() - start

    print(f"\n[-/-] Patch Generation Finished\t\tTime: {total:.2f} seconds")
    print(f"Patch File: {os.path.abspath(template.patch_output)}")

    if create_spoiler:
        print(f"Spoiler File: {os.path.abspath(template.report_output)}")
