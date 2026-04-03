import json
import os

from odfdo import Document, Table, Row

from vesperando_core.conf.settings import Paths
from vesperando_core.res import enums
from vesperando_core.utils import keys_to_int


class PatchSpoiler:
    arte_name_table: dict[int, str]
    skill_name_table: dict[int, str]
    item_name_table: dict[int, str]
    map_name_table: dict[str, str]
    search_names: list[str]
    shop_name_table: dict[str, str]

    spoiler: dict

    def __init__(self):
        with open(Paths.STATIC_PATH.joinpath("metadata.json")) as f:
            data = json.load(f, object_hook=keys_to_int)

        self.arte_name_table = data['artes']
        self.skill_name_table = data['skills']
        self.item_name_table = data['items']
        self.map_name_table = data['maps']
        self.search_names= data['search']['FIELD']
        self.shop_name_table = data['shops']

        self.spoiler = {}

    def write_spreadsheet(self, patch: dict, output):
        reports: list[Table] = []

        if 'artes' in patch:
            reports.append(self.spoil_artes(patch['artes']))

        if 'skills' in patch:
            reports.append(self.spoil_skills(patch['skills']))

        if 'items' in patch:
            reports.append(self.spoil_items(patch['items']))

        if 'shops' in patch:
            reports.append(self.spoil_shops(patch['shops']))

        if 'chests' in patch:
            reports.append(self.spoil_chests(patch['chests']))

        if 'search' in patch:
            reports.append(self.spoil_search(patch['search']))

        spoiler_sheet: Document = Document("spreadsheet")
        spoiler_sheet.body.clear()
        spoiler_sheet.body.extend(reports)
        spoiler_sheet.save(output)

    def spoil_artes(self, patch: dict) -> Table:
        report_list: list = []
        for arte in [*patch.values()]:
            learn_conditions: list = []
            # Parse Learn Conditions
            for _ in range(1, 4):
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
                    learn_conditions.extend(["Arte Usage", self.arte_name_table[parameter_id], f"x{meta_id}"])
                elif condition_id == 3:
                    learn_conditions.extend(["Equip Skill", self.skill_name_table[parameter_id], ""])
                else:
                    learn_conditions.extend(["INVALID", "!", "!"])

            # Parse Evolve Conditions
            evolve_conditions: list = [self.arte_name_table[arte['evolve_base']] if arte['evolve_base'] != 0
                                       else ""]
            for _ in range(1, 5):
                condition_id = arte[f'evolve_condition{_}']
                parameter_id = arte[f'evolve_parameter{_}']

                if condition_id == 0:
                    evolve_conditions.extend(["" for _ in range(2)])
                elif condition_id == 3:
                    evolve_conditions.extend(["Equip Skill", self.skill_name_table[parameter_id]])
                else:
                    evolve_conditions.extend(["INVALID", "!"])

            details: list = [
                self.arte_name_table[arte['id']], arte['tp_cost'], arte['cast_time'] if arte['cast_time'] else "N/A",
                *learn_conditions, *evolve_conditions,
                enums.FatalStrikeType(arte['fatal_strike_type']).name
            ]

            report_list.append(details)

        field_names: list[str] = ["Arte", "TP", "Cast Time",
                                  "Learn Condition 1", "Learn Parameter 1", "Learn Meta 1",
                                  "Learn Condition 2", "Learn Parameter 2", "Learn Meta 2",
                                  "Learn Condition 3", "Learn Parameter 3", "Learn Meta 3",
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

    def spoil_skills(self, patch: dict) -> Table:
        report_list: list = []
        for skill in [*patch.values()]:
            report_list.append([
                self.skill_name_table[skill['id']], skill['sp_cost'], skill['lp_cost'],
                enums.SkillSymbols(skill['symbol']).name,
                skill['symbol_weight'], 'Yes' if skill['is_equippable'] else 'No'
            ])

        field_names: list[str] = ["Skill", "SP", "LP", "Symbol", "Symbol Weight", "Equippable"]

        report: Table = Table("SKILLS")
        report.set_row_values(0, field_names)
        for i, row in enumerate(report_list):
            report.set_row_values(i + 1, row)

        return report

    def spoil_items(self, patch: dict) -> Table:
        report_list: list = []
        for item in [*patch['base'].values()]:
            entry: list = [self.item_name_table[item['id']], item['buy_price']]
            for _ in range(1, 4):
                if item[f'skill{_}']:
                    entry.extend([self.skill_name_table[item[f'skill{_}']], item[f'skill{_}_lp']])
                else:
                    entry.extend(["", ""])

            report_list.append(entry)

        field_names: list[str] = ["Item", "Price", "Skill 1", "Skill 1 LP", "Skill 2", "Skill 2 LP",
                                  "Skill 3", "Skill 3 LP", ]

        report: Table = Table("ITEMS")
        report.set_row_values(0, field_names)
        for i, row in enumerate(report_list):
            report.set_row_values(i + 1, row)

        return report

    def spoil_shops(self, patch: dict) -> Table:
        processed_groups: set[int] = set()

        items_by_shop: dict = {}
        for groups in patch['commons']:
            processed_groups.update(groups['shops'])
            for shop in groups['shops']:
                items_by_shop.setdefault(shop, []).extend(groups['items'])

        for shop, items in patch['uniques'].items():
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
            report.set_column_values(count, [self.shop_name_table[shop],
                                             *[self.item_name_table[i] for i in items],
                                             *["" for _ in range(max_count - (len(items) + 1))]])
            count += 1

        return report

    def spoil_chests(self, patch: dict) -> Table:
        report_list = []
        for area, chests in sorted(patch.items()):
            report_list.append([self.map_name_table.get(area, area)])
            for chest, details in chests.items():
                report_list.append([(self.map_name_table.get(chest, chest))])
                for content in details['items']:
                    report_list.append(["", self.resolve_chest_item_name(content['item_id']), content['amount']])

        field_names: list[str] = ["Chest", "Item", "Amount"]

        report: Table = Table("CHESTS")
        report.set_row_values(0, field_names)
        for i, row in enumerate(report_list):
            report.set_row_values(i + 1, row)

        return report

    def spoil_search(self, patch: dict) -> Table:
        report_list: list = []
        last_cont_idx: int = 0
        last_itm_idx: int = 0
        for i, definition in enumerate(patch['definitions']):
            next_cont_end: int = last_cont_idx + definition['content_range']
            item_ranges: list[int] = []
            for content in patch['contents'][last_cont_idx:next_cont_end]:
                item_ranges.append(content['item_range'])

            report_list.append([self.search_names[i], enums.SearchPointType(definition['type']).name])
            for idx, r in enumerate(item_ranges):
                report_list.append([f"Item Pool #{idx}",
                                    self.item_name_table[patch['items'][last_itm_idx]['id']],
                                    patch['items'][last_itm_idx]['count']])
                last_itm_idx += 1
                if r < 2: continue

                for count in range(r - 1):
                    report_list.append(["",
                                        self.item_name_table[patch['items'][last_itm_idx]['id']],
                                        patch['items'][last_itm_idx]['count']])
                    last_itm_idx += 1

            last_cont_idx = next_cont_end

        field_names: list[str] = ["Search Point", "Item", "Amount"]

        report: Table = Table("SEARCH POINTS")
        report.set_row_values(0, field_names)
        for i, row in enumerate(report_list):
            report.set_row_values(i + 1, row)

        return report

    def resolve_chest_item_name(self, item_id: int) -> str:
        if item_id == 0xFFFFFFFE:
            return "Gald"
        elif item_id in self.item_name_table:
            return self.item_name_table[item_id]
        else:
            return str(item_id)


if __name__ == '__main__':
    spoiler = PatchSpoiler()