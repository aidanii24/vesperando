from typing import Literal
from copy import deepcopy
import datetime
import random
import math
import uuid
import json
import time
import sys
import os

from vesperando_core.conf.settings import Paths, Extensions, Weights
from vesperando_core.res import enums, schema
from vesperando_core.utils import keys_to_int
from vesperando_core.spoil import PatchSpoiler


class BaseRandomizer:
    candidates: dict
    random: random.Random

    def randomize(self):
        pass

    def plandomize(self, plando: dict):
        self.candidates.update(deepcopy(plando))

    def fetch(self):
        return self.candidates

    def random_from_distribution(self, mu: float, sigma: float, range_min: float = -math.inf,
                                 range_max: float = math.inf):
        return int(math.ceil(min(max(self.random.gauss(mu, sigma), range_min), range_max)))

    def random_from_triangular(self, minimum: int, maximum: int, mode: Literal['min', 'max'] = "min"):
        if mode == "max":
            return max(self.random.randint(minimum, maximum), self.random.randint(minimum, maximum))
        else:
            return min(self.random.randint(minimum, maximum), self.random.randint(minimum, maximum))


class ArteRandomizer(BaseRandomizer):
    def __init__(self, random_obj: random.Random, data: dict, options: dict) -> None:
        self.random = random_obj
        self.artes_data = data['artes_data']
        self.artes_by_char = data['artes_by_char']
        self.skills_by_char = data['skills_by_char']
        self.options = options
        self.statistics: dict = {
            'Artes': 0,
            'TP Cost': 0,
            'Cast Time': 0,
            'Fatal Strikes': 0,
            'Evolutions': 0,
            'Learn Conditions': 0
        }

        # `artes_by_char` should already have all the valid candidates
        candidates: dict = {aid: artes for aid, artes in self.artes_data.items()
                            if aid in set(sum(self.artes_by_char.values(), []))}

        self.candidates = schema.Artes.extract(candidates)

    def randomize(self):
        for arte in self.candidates.values():
            # Candidacy
            if self.random.random() <= Weights.ARTE_CANDIDACY:
                continue

            self.statistics['Artes'] += 1
            data: dict = self.artes_data[arte['id']]
            user: int = data['character_ids'][0]

            # TP Cost
            if self.random.random() <= Weights.ARTE_TP_COST:
                self.randomize_tp_cost(arte)

            # Cast Time
            if arte['cast_time'] > 0 and self.random.random() <= Weights.ARTE_CAST_TIME:
                self.randomize_cast_time(arte)

            # Fatal Strike
            if self.random.random() <= Weights.ARTE_FS:
                self.randomize_fatal_strike(arte)

            # Evolutions
            has_evolve: bool = bool(arte.get('evolve', False))
            if has_evolve:
                if self.random.random() <= Weights.ARTE_EVOLVE:
                    self.randomize_evolutions(arte, user)
                ## On failed roll, instead randomize the usage requirements for learning the evolution
                elif self.random.random() > Weights.ARTE_EVOLVE_REQUIREMENT:
                    self.randomize_evolution_requirement(arte)


            # Learn Conditions
            if self.random.random() < Weights.ARTE_LEARN_OPPORTUNITIES[has_evolve + 1]:
                self.randomize_learn(arte, user, has_evolve)

    def randomize_tp_cost(self, arte):
        self.statistics['TP Cost'] += 1
        arte['tp_cost'] = math.ceil(int(arte['tp_cost']) * self.random_from_triangular(10, 200) * 0.01)

    def randomize_cast_time(self, arte):
        self.statistics['Cast Time'] += 1
        arte['cast_time'] = math.ceil(int(arte['cast_time']) * self.random.randrange(10, 200) * 0.01)

    def randomize_fatal_strike(self, arte):
        self.statistics['Fatal Strikes'] += 1
        arte['fatal_strike_type'] = self.random.randrange(0, 3)

    def randomize_evolutions(self, arte, user):
        self.statistics['Evolutions'] += 1

        arte['evolve_base'] = self.random.choice(self.artes_by_char[user])

        continue_iter: bool = True
        iterations: int = 1
        while iterations < len(Weights.ARTE_EVOLVE_OPPORTUNITIES):
            if continue_iter:
                arte[f'evolve_condition{iterations}'] = 3
                arte[f'evolve_parameter{iterations}'] = self.random.choice(self.skills_by_char[user])
            else:
                arte[f'evolve_condition{iterations}'] = 0
                arte[f'evolve_parameter{iterations}'] = 0

            if continue_iter and self.random.random() > Weights.ARTE_EVOLVE_OPPORTUNITIES[iterations]:
                continue_iter = False

            iterations += 1

        arte['learn_condition1'] = enums.ArteLearningTypes.ARTE_USAGE.value
        arte['learn_parameter1'] = int(arte['id'])

        self.randomize_evolution_requirement(arte)

    def randomize_evolution_requirement(self, arte):
        arte['unknown3'] = self.random.randrange(50, 200)

    def randomize_learn(self, arte, user, has_evolve: bool):
        self.statistics['Learn Conditions'] += 1

        continue_iter: bool = True
        iterations: int = 2 if has_evolve else 1
        while iterations < len(Weights.ARTE_LEARN_OPPORTUNITIES):
            if continue_iter:
                condition_population: list[int] = [_ for _ in range((1 if iterations <= 1 else 2), 4)]
                condition_chances: list[float] = [0.6] if iterations <= 1 else []
                condition_chances.extend(Weights.ARTE_LEARN_TYPE_OPPORTUNITIES[iterations])

                meta: int = 0

                condition: int = self.random.choices(condition_population, weights=condition_chances)[0]
                if condition == 1:
                    cap_level: int = self.random_from_triangular(5, 100)
                    parameter = self.random.randint(1, cap_level)
                elif condition == 2:
                    parameter: int = self.random.choice(self.artes_by_char[user])
                    ranges = sorted([int(self.random_from_triangular(50, 100)),
                                    int(self.random_from_triangular(50, 200))])
                    meta = max(self.random_from_triangular(*ranges) // 5 * 5, 5)
                else:
                    parameter: int = self.random.choice(self.skills_by_char[user])

                arte[f'learn_condition{iterations}'] = condition
                arte[f'learn_parameter{iterations}'] = parameter
                arte[f'unknown{iterations + 2}'] = meta
            else:
                arte[f"learn_condition{iterations}"] = 0
                arte[f"learn_parameter{iterations}"] = 0
                arte[f"unknown{iterations + 2}"] = 0

            if continue_iter and self.random.random() > Weights.ARTE_LEARN_OPPORTUNITIES[iterations]:
                continue_iter = False

            iterations += 1

        # If Arte has Evolve Conditions from Vanilla, remove them if Learn Condition is randomized
        if not has_evolve and arte['evolve_base']:
            arte['evolve_base'] = 0
            for _ in range(1, 5):
                arte[f'evolve_condition{_}'] = 0
                arte[f'evolve_parameter{_}'] = 0


class SkillRandomizer(BaseRandomizer):
    def __init__(self, random_obj: random.Random, data: dict, options: dict):
        self.random = random_obj
        self.skills_data = data['skills_data']

        self.statistics: dict = {
            'Skills': 0,
            'SP Cost': 0,
            'LP': 0,
            'Symbols': 0,
            'Symbol Weights': 0,
        }

        # Filter out dummy skill and enemy exclusive skill "Heal Down" (id 445)
        candidates: dict = {sid: skill for sid, skill in self.skills_data.items()
                            if sid > 0 and sid != 445}
        self.candidates = schema.Skills.extract(candidates)

    def randomize(self):
        for skill in self.candidates.values():
            # Candidacy
            if self.random.random() <= Weights.SKILL_CANDIDACY:
                continue

            self.statistics['Skills'] += 1

            # SP Cost
            if skill['sp_cost'] and self.random.random() <= 0.95:
                self.statistics['SP Cost'] += 1
                skill['sp_cost'] = self.random_from_distribution(Weights.SKILL_SP_MU, Weights.SKILL_SP_SIGMA,
                                                                 1, 30)

            # LP
            if skill['lp_cost']:
                self.statistics['LP'] += 1
                ranges = sorted([int(self.random_from_triangular(100, 1600)),
                                 int(self.random_from_triangular(100, 600))])
                base = round(self.random_from_triangular(*ranges), -2)
                skill['lp_cost'] = base

            # Symbol Type
            if self.random.random() <= Weights.SKILL_SYMBOL:
                self.statistics['Symbols'] += 1
                skill['symbol'] = self.random.choices([c.value for c in enums.SkillSymbols],
                                                      Weights.SKILL_SYMBOL_DISTRIBUTION)[0]

            # Symbol Weight
            if self.random.random() <= Weights.SKILL_SYMBOL_WEIGHT:
                self.statistics['Symbol Weights'] += 1
                skill['symbol_weight'] = self.random_from_distribution(Weights.SKILL_SYMBOL_WEIGHT_MU,
                                                                       Weights.SKILL_SYMBOL_WEIGHT_SIGMA,
                                                                       1, 30)


class ItemRandomizer(BaseRandomizer):
    def __init__(self, random_obj: random.Random, data: dict, options: dict):
        self.random = random_obj
        self.items_list = data['items_list']
        self.skills_lp_table = data['skills_lp_table']
        self.skills_by_char = data['skills_by_char']
        self.items_data_table: dict = {item['id'] : item for item in self.items_list}

        self.statistics: dict = {
            'Items': 0,
            'Prices': 0,
            'Skills': 0,
        }

        self.candidates = {
            'base': schema.Items.extract(self.items_data_table)
        }

    def randomize(self):
        set_skills_per_char: dict[int, set] = {c.value: set() for c in enums.Characters}
        for iid, item in self.candidates['base'].items():
            # Candidacy
            if self.random.random() <= Weights.ITEM_CANDIDACY:
                continue

            self.statistics['Items'] += 1
            data: dict = self.items_data_table[iid]

            # Get Characters that equip this item
            users: list[int] = []
            for i, character in enumerate(enums.Characters):
                if data['character_usable'] & character.bitflag() > 0:
                    users.append(character.value)

            # Buy Price
            if item['buy_price'] and self.random.random() <= 0.95:
                self.statistics['Prices'] += 1
                base = int(item['buy_price'] * self.random_from_triangular(25, 200) / 100)
                item['buy_price'] = base // 10 * 10

            # Weapon Properties
            if enums.ItemCategory.is_weapon(data['category']):
                skills_candidates: set[int] = set(skill for char in users
                                                 for skill in self.skills_by_char[char]
                                                 if char in self.skills_by_char)

                skills_set: set[int] =  skills_candidates.difference(*[set_skills_per_char[s] for s in users])

                ## Get all valid skill candidates that are not already set
                if abs(len(skills_candidates) - len(skills_set)) > 3:
                    skills_candidates -= skills_set
                ## If there are not enough candidates left, reset the skills set list for the involved characters
                else:
                    for u in users:
                        set_skills_per_char[u] -= skills_candidates

                # Skills
                continue_iter: bool = True
                for i, opp in enumerate(Weights.ITEM_SKILL_OPPORTUNITIES):
                    if continue_iter and self.random.random() <= opp:
                        self.statistics['Skills'] += 1
                        skill: int = self.random.choice([*skills_candidates])

                        item[f'skill{i + 1}'] = skill

                        if skill in self.skills_lp_table:
                            item[f'skill{i + 1}_lp'] = self.skills_lp_table[skill]
                        else:
                            item[f'skill{i + 1}_lp'] = int(self.random_from_distribution(Weights.SKILL_LP_MU,
                                                                                         Weights.SKILL_LP_SIGMA,
                                                                                         100, 1600))

                        skills_candidates.discard(skill)
                        for u in users:
                            set_skills_per_char[u].discard(skill)

                        if not len(skills_candidates):
                            continue_iter = False
                    else:
                        item[f'skill{i + 1}'] = 0
                        item[f'skill{i + 1}_lp'] = 0

                        continue_iter = False


class ShopRandomizer(BaseRandomizer):
    def __init__(self, random_obj: random.Random, data: dict, options: dict):
        self.random = random_obj
        self.shop_data = data['shop_data']
        self.item_to_category = data['item_to_category']
        self.item_by_category = data['item_by_category']
        self.common_items = data['common_items']

        self.statistics: dict = {
            'Items': 0,
            'Full Shuffle': 0,
            'Same Category': 0
        }

        self.candidates = deepcopy(self.shop_data['items'])

    def randomize(self):
        items_cache: dict[int, set[int]] = {}
        for shop_group in self.candidates['commons']:
            placed: set[int] = set(items_cache.get(shop_group['shops'][0], []))

            new_items: set[int] = set()
            for item in shop_group['items']:
                # Do not randomize dummy items, Key Items and DLC
                if not enums.ItemCategory.is_common(self.item_to_category[item]):
                    new_items.add(item)
                    continue

                new_items.add(self.randomize_item(item, set.union(placed, new_items)))

            shop_group['items'] = [*new_items]
            for evolution in shop_group['shops']:
                items_cache.setdefault(evolution, set()).update(new_items)

        for shop, items in self.candidates['uniques'].items():
            placed: set[int] = set(items_cache.get(shop, []))

            new_items: set[int] = set()
            for item in items:
                # Do not randomize dummy items, Key Items and DLC
                if not enums.ItemCategory.is_common(self.item_to_category[item]):
                    new_items.add(item)
                    continue

                new_items.add(self.randomize_item(item, set.union(placed, new_items)))

            self.candidates['uniques'][shop] = [*new_items]

    def randomize_item(self, item: int, blacklist: set[int]):
        self.statistics['Items'] += 1

        category = self.item_to_category[item]
        new_item: int = item

        # Set up weights depending on item category
        ## Consumables should be rarely randomized
        if category == enums.ItemCategory.CONSUMABLE.value:
            if item in blacklist:
                candidacy_chance = -1.00
                same_category_chance = -1.00
            else:
                candidacy_chance = Weights.SHOP_CANDIDACY_CONSUMABLE
                same_category_chance = Weights.SHOP_CANDIDACY_CONSUMABLE_REPEAT
        else:
            if item in blacklist:
                candidacy_chance = -1.00
            else:
                candidacy_chance = Weights.SHOP_CANDIDACY
            same_category_chance = Weights.SHOP_CANDIDACY_REPEAT

        if self.random.random() >= candidacy_chance:
            self.statistics['Items'] += 1
            category: int = self.item_to_category[item]
            category_candidates: set[int] = set(self.item_by_category[category]).difference(blacklist)
            if category_candidates and self.random.random() <= same_category_chance:
                self.statistics['Same Category'] += 1
                new_item: int = self.random.choice([*category_candidates])
            else:
                self.statistics['Full Shuffle'] += 1
                new_item: int = self.random.choice(self.common_items)

        return new_item


class ChestRandomizer(BaseRandomizer):
    GALD_ID = 0xFFFFFFFE

    def __init__(self, random_obj: random.Random, data: dict, options: dict):
        self.random = random_obj
        self.chest_data = data['chest_data']
        self.item_to_category = data['item_to_category']
        self.item_by_category = data['item_by_category']
        self.eligible_items = data['common_items'] + tuple([self.GALD_ID])

        self.statistics: dict = {
            'Chests': 0,
            'Full Shuffle': 0,
            'Same Category': 0,
            'Item Amount': 0,
            'Gald Amount': 0,
        }

        self.candidates = deepcopy(self.chest_data)

    def randomize(self):
        chest_types: list[int] = [c.value for c in enums.ChestType]

        for area, chests in self.candidates.items():
            for chest, details in chests.items():
                # Type
                if self.random.random() <= Weights.CHEST_TYPE:
                    self.candidates[area][chest]['chest_type'] = self.random.choice(chest_types)

                # Items
                new_items: list[dict] = []
                for item in details['items']:
                    iid: int = item['item_id']
                    category: int = self.item_to_category.get(iid, -1)
                    if iid == self.GALD_ID or enums.ItemCategory.is_common(category):
                        new_items.append(self.randomize_item(iid, item['amount'], category))
                    else:
                        new_items.append(item)

                self.candidates[area][chest]['items'] = new_items

    def randomize_item(self, item: int, amount: int = 1, item_category: int = enums.ItemCategory.DUMMY.value) -> dict:
        if not item_category:
            item_category = self.item_to_category[item]

        new_item: int = item
        new_category = item_category
        new_amount: int = amount

        # Set up weights depending on item category
        ## Consumables should be rarely randomized
        same_category_chance: float = 0.2 if not item_category == enums.ItemCategory.CONSUMABLE.value else 0.85

        if self.random.random() <= Weights.CHEST_CANDIDACY:
            self.statistics['Chests'] += 1
            if new_item != self.GALD_ID and self.random.random() <= same_category_chance:
                self.statistics['Same Category'] += 1
                new_item = random.choice(self.item_by_category[item_category])
            else:
                self.statistics['Full Shuffle'] += 1
                new_item = random.choice(self.eligible_items)
                new_category = self.item_to_category[new_item]

        is_new_item_abundant: bool = enums.ItemCategory.is_abundant(new_category)

        # Set up new amount of the item
        ## All normal items should be rarely randomized
        if new_item != self.GALD_ID and self.random.random() <= Weights.CHEST_ITEM_AMOUNT:
            self.statistics['Item Amount'] += 1
            if is_new_item_abundant:
                new_amount = self.random.randrange(1, 15)
            else:
                new_amount = 1
                while self.random.random() <= (Weights.CHEST_ITEM_AMOUNT / new_amount) and new_amount < 15:
                    new_amount += 1
        elif new_item == self.GALD_ID:
            self.statistics['Gald Amount'] += 1
            new_amount = self.randomize_gald_amount(new_amount)
        elif item == self.GALD_ID and new_item != item:
            new_amount = amount % 15

        return {
            'item_id': new_item,
            'amount': new_amount,
        }

    def randomize_gald_amount(self, amount_basis = 100):
        if self.random.random() <= Weights.CHEST_CANDIDACY:
            return math.ceil(amount_basis * self.random_from_triangular(1, 100) / 10)

        return amount_basis


class SearchPointRandomizer(BaseRandomizer):
    def __init__(self, random_obj: random.Random, data: dict, options: dict):
        self.random = random_obj
        self.item_to_category = data['item_to_category']
        self.item_by_category = data['item_by_category']
        self.common_items = data['common_items']

        self.statistics: dict = {
            'Contents': [],
            'Items': [],
            'Average Contents per Definition': 0,
            'Average Items per Content': 0,
        }

        self.candidates = {
            'guarantee': True,
            'definitions': [],
            'contents': [],
            'items': [],
        }

    def randomize(self):
        # We offset back by the two duplicate definitons present in Vanilla
        definition_count = 88

        definition_types: list[int] = [d.value for d in enums.SearchPointType]

        for _ in range(definition_count):
            # Randomize Definition
            content_range: int = self.random_from_triangular(1, 5)
            self.candidates['definitions'].append({
                'type': self.random.choice(definition_types),
                'content_range': content_range,
                'max_use': self.random_from_triangular(1, 5)
            })

            # Randomize Content
            item_ranges: list[int] = [self.random.randint(1, 5) for _ in range(content_range)]
            for r in item_ranges:
                self.candidates['contents'].append({
                    'item_range': r,
                    'chance': self.random_from_triangular(1, 10, 'max')
                })

            # Randomize Items
            for count in item_ranges:
                placed: set[int] = set()
                for _ in range(count):
                    iid: int = self.random.choice([*set(self.common_items).difference(placed)])
                    count: int = 1
                    if enums.ItemCategory.is_abundant(self.item_to_category[iid]):
                        count = self.random_from_triangular(1, 15)

                    self.candidates['items'].append({
                        'id': iid,
                        'count': count
                    })

            self.statistics['Contents'].append(content_range)
            self.statistics['Items'].extend(item_ranges)


class BasicRandomizerProcedure:
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
    common_items: tuple # Any valid non-key and non-DLC item

    seed: int
    random: random.Random

    arte_randomizer: ArteRandomizer
    skill_randomizer: SkillRandomizer
    item_randomizer: ItemRandomizer
    shop_randomizer: ShopRandomizer
    chest_randomizer: ChestRandomizer
    search_point_randomizer: SearchPointRandomizer

    identifier: str = "randomizer"
    patch_output: str = os.path.join(Paths.PATCHES, f"randomizer.{Extensions.BASIC_PATCH}")
    report_output: str = os.path.join(Paths.PATCHES, "tovde-spoiler.ods")

    def __init__(self, targets: list[str], seed = random.randint(1, 0xFFFFFFFF)):
        self.seed = uuid.uuid1().int
        self.random = random.Random(seed)

        self.identifier = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")
        self.patch_output = os.path.join(Paths.PATCHES, f"{self.identifier}{Extensions.BASIC_PATCH}")
        self.report_output = os.path.join(Paths.PATCHES, f"tovde-spoiler-{self.identifier}.ods")

        if not targets or 'artes' in targets:
            self.load_artes_data()

        if not targets or {'artes', 'skills', 'items'}.intersection(targets):
            self.load_skills_data()

        item_dependents: set[str] = set(targets).intersection({'items', 'shops', 'chests', 'search'})
        is_search_only: bool = len(item_dependents) == 1 and 'search' in item_dependents
        if not targets or item_dependents:
            self.load_items_data(not is_search_only)

        if not os.path.isdir(Paths.PATCHES):
            os.makedirs(Paths.PATCHES)

    def load_artes_data(self):
        artes_data_table = json.load(open(os.path.join(Paths.STATIC_DIR, "artes.json")), object_hook=keys_to_int)

        properties_table = {}
        artes_by_char = {}
        for arte in artes_data_table['entries']:
            properties_table[int(arte['id'])] = arte

            # We get all the valid artes for randomization here as well, conforming to these conditions:
            ##  a. Must be only used by a playable character
            ##  b. Must not be a special arte type (This filters out Fatal Strikes, Overlimits and Skill)
            ##  c. Must have a TP Cost (This filters out variations of artes if any)
            only_used_by_playable: bool = any(0 < chara < 10 for chara in arte['character_ids'])
            if not only_used_by_playable: continue
            for char in arte['character_ids']:
                # Check if arte is not special (Fatal Strike, Overlimit or Skill)
                if enums.ArteTypes.is_normal(arte['arte_type']): continue
                # Check if arte has TP Cost
                if arte['tp_cost'] <= 0: continue

                artes_by_char.setdefault(char, []).append(arte['id'])

        self.artes_data_table = properties_table
        self.artes_by_char = artes_by_char

    def load_skills_data(self):
        skills_data_table: dict = json.load(open(os.path.join(Paths.STATIC_DIR, 'skills.json')),
                                            object_hook=keys_to_int)
        self.skills_data_table = {int(sid): skill['properties']
                                  for sid, skill in skills_data_table['entries'].items()}

        skills_by_char = {}
        for sid, data in skills_data_table['entries'].items():
            if not data['users']: continue
            for user in data['users']:
                skills_by_char.setdefault(user, []).append(sid)

        self.skills_by_char = skills_by_char

    def load_items_data(self, map_categories: bool = False):
        self.items_list = json.load(open(os.path.join(Paths.STATIC_DIR, "items.json")))

        self.item_by_category = {}
        self.item_to_category = {}
        self.common_items = tuple()

        for item in self.items_list:
            self.item_by_category.setdefault(item['category'], []).append(item['id'])

            if not map_categories: continue
            self.item_to_category[item['id']] = item['category']

        if map_categories:
            self.common_items = tuple([item for category, items in self.item_by_category.items()
                                       for item in items
                                       if enums.ItemCategory.is_common(category)])

    def generate(self, targets: list, spoil: bool = False):
        output: str = self.patch_output

        patch_data: dict = {
            'version': '0.2',
            'created': self.identifier,
            'seed': self.seed,
            'player': "test",
        }

        if os.path.isfile(self.report_output):
            os.remove(self.report_output)

        if not targets or 'artes' in targets:
            data: dict = {
                'artes_data': self.artes_data_table,
                'artes_by_char': self.artes_by_char,
                'skills_by_char': self.skills_by_char,
            }
            self.arte_randomizer = ArteRandomizer(self.random, data, {})
            self.arte_randomizer.randomize()
            patch_data['artes'] = self.arte_randomizer.fetch()

        if not targets or 'skills' in targets:
            data: dict = {
                'skills_data': self.skills_data_table,
            }

            self.skill_randomizer = SkillRandomizer(self.random, data, {})
            self.skill_randomizer.randomize()
            patch_data['skills'] = self.skill_randomizer.fetch()

        if not targets or 'items' in targets:
            skills_lp_table: dict = {}
            if 'skills' in patch_data:
                skills_lp_table = {sid: v['lp_cost'] for sid,v in patch_data['skills'].items()}

            data: dict = {
                'items_list': self.items_list,
                'skills_lp_table': skills_lp_table,
                'skills_by_char': self.skills_by_char,
            }

            self.item_randomizer = ItemRandomizer(self.random, data, {})
            self.item_randomizer.randomize()
            patch_data['items'] = self.item_randomizer.fetch()

        if not targets or 'shops' in targets:
            data: dict = {
                'shop_data': json.load(open(os.path.join(Paths.STATIC_DIR, "shop.json")), object_hook=keys_to_int),
                'item_to_category': self.item_to_category,
                'item_by_category': self.item_by_category,
                'common_items': self.common_items,
            }

            self.shop_randomizer = ShopRandomizer(self.random, data, {})
            self.shop_randomizer.randomize()
            patch_data['shops'] = self.shop_randomizer.fetch()

        if not targets or 'chests' in targets:
            data: dict = {
                'chest_data': json.load(open(os.path.join(Paths.STATIC_DIR, "chests.json")), object_hook=keys_to_int),
                'item_to_category': self.item_to_category,
                'item_by_category': self.item_by_category,
                'common_items': self.common_items,
            }

            self.chest_randomizer = ChestRandomizer(self.random, data, {})
            self.chest_randomizer.randomize()
            patch_data['chests'] = self.chest_randomizer.fetch()

        if not targets or 'search' in targets:
            data: dict = {
                'item_to_category': self.item_to_category,
                'item_by_category': self.item_by_category,
                'common_items': self.common_items,
            }

            self.search_point_randomizer = SearchPointRandomizer(self.random, data, {})
            self.search_point_randomizer.randomize()
            patch_data['search'] = self.search_point_randomizer.fetch()

        with open(output, 'w') as f:
            json.dump(patch_data, f)

        if spoil:
            patch_data: dict = dict(item for item in [*patch_data.items()][4:])

            spoiler = PatchSpoiler()
            spoiler.write_spreadsheet(patch_data, self.report_output)


if __name__ == "__main__":
    VALID_TARGETS: list[str] = [
        'artes',
        'skills',
        'items',
        'shops',
        'chests',
        'search'
    ]

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

    template = BasicRandomizerProcedure(target_list)
    template.generate(target_list, create_spoiler)

    total: float = time.time() - start

    print(f"\n[-/-] Patch Generation Finished\t\tTime: {total:.2f} seconds")
    print(f"Patch File: {os.path.abspath(template.patch_output)}")

    if create_spoiler:
        print(f"Spoiler File: {os.path.abspath(template.report_output)}")
