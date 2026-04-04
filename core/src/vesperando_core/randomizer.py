from typing import Literal
from copy import deepcopy
import datetime
import logging
import random
import math
import uuid
import json
import time
import sys
import os

from vesperando_core.res.models.options import MainOptionsDefault
from vesperando_core.conf.settings import Paths, Extensions, Weights
from vesperando_core.res import enums, schema
from vesperando_core.utils import keys_to_int, safe_divide
from vesperando_core.spoil import PatchSpoiler


logger = logging.getLogger(os.environ.get('LOGGER_NAME', "vesperando"))

class BaseRandomizer:
    candidates: dict
    random: random.Random

    def randomize(self):
        pass

    def plandomize(self, plando: dict):
        self.candidates.update(deepcopy(plando))

    def fetch(self):
        return self.candidates

    def report(self):
        pass

    def random_from_distribution(self, mu: float, sigma: float, range_min: float = -math.inf,
                                 range_max: float = math.inf):
        return int(math.ceil(min(max(self.random.gauss(mu, sigma), range_min), range_max)))

    def random_from_triangular(self, minimum: int, maximum: int, mode: Literal['min', 'max'] = "min"):
        if mode == "max":
            return max(self.random.randint(minimum, maximum), self.random.randint(minimum, maximum))
        else:
            return min(self.random.randint(minimum, maximum), self.random.randint(minimum, maximum))


class ArteOptions:
    def __init__(self, options: dict):
        self.tp_mod: float = options.get("tp_mod", 1.0)
        self.tp_min: int = options.get("tp_min", 1)
        self.tp_max: int = options.get("tp_max", 100)
        self.learn_arte_usage_mod: float = options.get("learn_arte_usage_min", 1.0)
        self.learn_arte_usage_min: int = options.get("learn_arte_usage_min", 5)
        self.learn_arte_usage_max: int = options.get("learn_arte_usage_max", 200)
        self.enable_non_altered_evolve: bool = options.get("enable_non_altered_evolve", False)


class ArteRandomizer(BaseRandomizer):
    def __init__(self, random_obj: random.Random, data: dict, options: dict) -> None:
        self.random = random_obj
        self.artes_data = data['artes_data']
        self.artes_by_char = data['artes_by_char']
        self.skills_by_char = data['skills_by_char']
        self.options = ArteOptions(options)
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
            is_candidate: bool = self.random.random() > Weights.ARTE_CANDIDACY
            if is_candidate:
                self.statistics['Artes'] += 1

            data: dict = self.artes_data[arte['id']]
            user: int = data['character_ids'][0]

            # TP Cost
            tp: int = arte.get('tp_cost', 0)
            if is_candidate and self.random.random() <= Weights.ARTE_TP_COST:
                tp = self.randomize_tp_cost(arte)

            arte['tp_cost'] = min(max(int(tp * self.options.tp_mod), self.options.tp_min), self.options.tp_max)

            # Cast Time
            if is_candidate and arte['cast_time'] > 0 and self.random.random() <= Weights.ARTE_CAST_TIME:
                self.randomize_cast_time(arte)

            # Fatal Strike
            if is_candidate and self.random.random() <= Weights.ARTE_FS:
                self.randomize_fatal_strike(arte)

            # Evolutions
            has_evolve: bool = bool(arte.get('evolve_base', False))
            randomize_evolve: bool = has_evolve or self.options.enable_non_altered_evolve
            evolve_randomized: bool = False
            if is_candidate and randomize_evolve:
                chance = Weights.ARTE_EVOLVE if has_evolve else Weights.ARTE_NON_ALTERED_EVOLVE

                if self.random.random() <= chance:
                    self.randomize_evolutions(arte, user)

                    if not has_evolve:
                        self.randomize_evolution_requirement(arte)

                    evolve_randomized = True

                if has_evolve and self.random.random() > Weights.ARTE_EVOLVE_REQUIREMENT:
                    self.randomize_evolution_requirement(arte)
                    evolve_randomized = True

            # Learn Conditions
            if is_candidate and self.random.random() < Weights.ARTE_LEARN_OPPORTUNITIES[evolve_randomized + 1]:
                self.randomize_learn(arte, user, evolve_randomized)
            else:
                for i in range(1, 4):
                    usage: int = arte.get(f'unknown{i + 2}', 0)
                    if arte.get(f'learn_condition{i}', 0) == 2 and usage:
                        arte[f'unknown{i + 2}'] = min(
                            max(int(usage * self.options.learn_arte_usage_mod), self.options.learn_arte_usage_min),
                            self.options.learn_arte_usage_max
                        )

    def randomize_tp_cost(self, arte):
        self.statistics['TP Cost'] += 1
        return math.ceil(int(arte['tp_cost']) * self.random_from_triangular(10, 200) * 0.01)


    def randomize_cast_time(self, arte):
        self.statistics['Cast Time'] += 1
        arte['cast_time'] = math.ceil(int(arte['cast_time']) * self.random.randrange(10, 200) * 0.01)

    def randomize_fatal_strike(self, arte):
        self.statistics['Fatal Strikes'] += 1
        arte['fatal_strike_type'] = self.random.randrange(0, 3)

    def randomize_evolutions(self, arte, user):
        self.statistics['Evolutions'] += 1

        arte['evolve_base'] = self.random.choice([a for a in self.artes_by_char[user] if a != arte['id']])

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
        meta = self.random.randrange(50, 200) // 5
        arte['unknown3'] = max(min(int(meta * self.options.learn_arte_usage_mod), self.options.learn_arte_usage_max),
                               self.options.learn_arte_usage_min)

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
                    parameter: int = self.random.choice([a for a in self.artes_by_char[user] if a != arte['id']])
                    ranges = sorted([int(self.random_from_triangular(self.options.learn_arte_usage_min,
                                                                     self.options.learn_arte_usage_max // 2)),
                                    int(self.random_from_triangular(self.options.learn_arte_usage_min,
                                                                    self.options.learn_arte_usage_max))])
                    meta = max(self.random_from_triangular(*ranges) // 5 * 5, 5)
                    meta = max(min(int(meta * self.options.learn_arte_usage_mod), self.options.learn_arte_usage_max),
                               self.options.learn_arte_usage_min)
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

    def report(self):
        if sys.stdout.encoding == "utf-8":
            logger.info(f"{"\u2748 ARTES":>4}")
        else:
            logger.info(f"{"> ARTES":>4}")

        artes_ratio: str = f"{self.statistics['Artes']:<4}/{len(self.candidates)}"
        tp_ratio: str = f"{self.statistics['TP Cost']:<4}/{self.statistics['Artes']}"
        cast_time_ratio: str = f"{self.statistics['Cast Time']:<4}/{self.statistics['Artes']}"
        fatal_strike_ratio: str = f"{self.statistics['Fatal Strikes']:<4}/{self.statistics['Artes']}"
        evolution_ratio: str = f"{self.statistics['Evolutions']:<4}/{self.statistics['Artes']}"
        learn_condition_ratio: str = f"{self.statistics['Learn Conditions']:<4}/{self.statistics['Artes']}"

        artes_percentage: float = safe_divide(self.statistics['Artes'], len(self.candidates))
        tp_percentage: float = safe_divide(self.statistics['TP Cost'], self.statistics['Artes'])
        cast_time_percentage: float = safe_divide(self.statistics['Cast Time'], self.statistics['Artes'])
        fatal_strike_percentage: float = safe_divide(self.statistics['Fatal Strikes'], self.statistics['Artes'])
        evolution_percentage: float = safe_divide(self.statistics['Evolutions'], self.statistics['Artes'])
        learn_condition_percentage: float = safe_divide(self.statistics['Learn Conditions'], self.statistics['Artes'])

        logger.info(f"{"":>4}{"> Candidates:":<21}{artes_ratio:<12}{artes_percentage:.2f}%")
        logger.info(f"{"":>4}{"> TP Cost:":<21}{tp_ratio:<12}{tp_percentage:.2f}%")
        logger.info(f"{"":>4}{"> Cast Time:":<21}{cast_time_ratio:<12}{cast_time_percentage:.2f}%")
        logger.info(f"{"":>4}{"> Fatal Strikes:":<21}{fatal_strike_ratio:<12}{fatal_strike_percentage:.2f}%")
        logger.info(f"{"":>4}{"> Evolutions:":<21}{evolution_ratio:<12}{evolution_percentage:.2f}%")
        logger.info(f"{"":>4}{"> Learn Conditions:":<21}{learn_condition_ratio:<12}{learn_condition_percentage:.2f}%")
        logger.info("")


class SkillOptions:
    def __init__(self, options: dict):
        self.sp_mod: float = options.get('sp_mod', 1.0)
        self.sp_min: int = options.get('sp_min', 1)
        self.sp_max: int = options.get('sp_max', 30)


class SkillRandomizer(BaseRandomizer):
    def __init__(self, random_obj: random.Random, data: dict, options: dict):
        self.random = random_obj
        self.skills_data = data['skills_data']
        self.options = SkillOptions(options)

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
            is_candidate: bool = self.random.random() > Weights.SKILL_CANDIDACY

            if is_candidate:
                self.statistics['Skills'] += 1

            # SP Cost
            sp: int = skill.get('sp_cost', 0)
            if is_candidate and sp and self.random.random() <= 0.95:
                self.statistics['SP Cost'] += 1
                sp = self.random_from_distribution(Weights.SKILL_SP_MU, Weights.SKILL_SP_SIGMA,
                                                   self.options.sp_min, self.options.sp_max)

            skill['sp_cost'] = max(min(int(sp * self.options.sp_mod), self.options.sp_max),
                                   self.options.sp_min)

            # LP
            if is_candidate and skill['lp_cost']:
                self.statistics['LP'] += 1
                ranges = sorted([int(self.random_from_triangular(100, 1600)),
                                 int(self.random_from_triangular(100, 600))])
                base = round(self.random_from_triangular(*ranges), -2)
                skill['lp_cost'] = base

            # Symbol Type
            if is_candidate and self.random.random() <= Weights.SKILL_SYMBOL:
                self.statistics['Symbols'] += 1
                skill['symbol'] = self.random.choices([c.value for c in enums.SkillSymbols],
                                                      Weights.SKILL_SYMBOL_DISTRIBUTION)[0]

            # Symbol Weight
            if is_candidate and self.random.random() <= Weights.SKILL_SYMBOL_WEIGHT:
                self.statistics['Symbol Weights'] += 1
                skill['symbol_weight'] = self.random_from_distribution(Weights.SKILL_SYMBOL_WEIGHT_MU,
                                                                       Weights.SKILL_SYMBOL_WEIGHT_SIGMA,
                                                                       1, 30)

    def report(self):
        logger.info("& SKILLS")

        skills_ratio: str = f"{self.statistics['Skills']:<4}/{len(self.candidates)}"
        sp_cost_ratio: str = f"{self.statistics['SP Cost']:<4}/{self.statistics['Skills']}"
        lp_ratio: str = f"{self.statistics['LP']:<4}/{self.statistics['Skills']}"
        symbols_ratio: str = f"{self.statistics['Symbols']:<4}/{self.statistics['Skills']}"
        symbol_weights_ratio: str = f"{self.statistics['Symbol Weights']:<4}/{self.statistics['Skills']}"

        skills_percentage: float = safe_divide(self.statistics['Skills'], len(self.candidates))
        sp_cost_percentage: float = safe_divide(self.statistics['SP Cost'], self.statistics['Skills'])
        lp_percentage: float = safe_divide(self.statistics['LP'], self.statistics['Skills'])
        symbols_percentage: float = safe_divide(self.statistics['Symbols'], self.statistics['Skills'])
        symbol_weights_percentage: float = safe_divide(self.statistics['Symbol Weights'], self.statistics['Skills'])

        logger.info(f"{"":>4}{"> Candidates:":<21}{skills_ratio:<12}{skills_percentage:.2f}%")
        logger.info(f"{"":>4}{"> SP Cost:":<21}{sp_cost_ratio:<12}{sp_cost_percentage:.2f}%")
        logger.info(f"{"":>4}{"> LP:":<21}{lp_ratio:<12}{lp_percentage:.2f}%")
        logger.info(f"{"":>4}{"> Symbols:":<21}{symbols_ratio:<12}{symbols_percentage:.2f}%")
        logger.info(f"{"":>4}{"> Symbol Weights:":<21}{symbol_weights_ratio:<12}{symbol_weights_percentage:.2f}%")
        logger.info("")


class ItemOptions:
    def __init__(self, options: dict):
        self.price_mod: float = options.get('price_mod', 1.0)
        self.weapon_skills_min: int = options.get('weapon_skills_min', 1)
        self.weapon_skills_max: int = options.get('weapon_skills_max', 3)
        self.weapon_skill_lp_mod: float = options.get('weapon_skill_lp_mod', 1.0)
        self.weapon_skill_lp_min: int = options.get('weapon_skill_lp_min', 100)
        self.weapon_skill_lp_max: int = options.get('weapon_skill_lp_max', 1600)


class ItemRandomizer(BaseRandomizer):
    def __init__(self, random_obj: random.Random, data: dict, options: dict):
        self.random = random_obj
        self.items_data = data['items_data']
        self.skills_lp_table = data['skills_lp_table']
        self.skills_by_char = data['skills_by_char']
        self.options = ItemOptions(options)

        self.statistics: dict = {
            'Items': 0,
            'Prices': 0,
            'Skills': 0,
        }

        candidates = {iid: item for iid, item in self.items_data.items() if iid > 0}
        self.candidates = {
            'base': schema.Items.extract(candidates)
        }

    def randomize(self):
        set_skills_per_char: dict[int, set] = {c.value: set() for c in enums.Characters}
        for iid, item in self.candidates['base'].items():
            # Candidacy
            is_candidate: bool = self.random.random() > Weights.ITEM_CANDIDACY

            if is_candidate:
                self.statistics['Items'] += 1

            data: dict = self.items_data[iid]

            # Get Characters that equip this item
            users: list[int] = []
            for i, character in enumerate(enums.Characters):
                if data['character_usable'] & character.bitflag() > 0:
                    users.append(character.value)

            # Buy Price
            buy_price: int = item.get('buy_price', 0)
            if buy_price:
                if is_candidate and self.random.random() <= 0.95:
                    self.statistics['Prices'] += 1
                    base = int(item['buy_price'] * self.random_from_triangular(25, 200) / 100)
                    buy_price = base // 5 * 5
            else:
                base = self.random_from_triangular(25, 1000000)
                buy_price = base // 5 * 5

            item['buy_price'] = int(buy_price * self.options.price_mod)

            # Weapon Properties
            if enums.ItemCategory.is_weapon(data['category']):
                skills_candidates: set[int] = set(skill for char in users
                                                  for skill in self.skills_by_char[char]
                                                  if char in self.skills_by_char)

                skills_set: set[int] = skills_candidates.difference(*[set_skills_per_char[s] for s in users])

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
                    roll: float = self.random.random() if i + 1 < self.options.weapon_skills_min else -1
                    if continue_iter and roll <= opp:
                        self.statistics['Skills'] += 1

                        skill: int = item.get(f'skill{i + 1}', 0)
                        lp: int = item.get(f'skill{i + 1}_lp', 0)

                        if is_candidate or (not is_candidate and not skill):
                            skill = self.random.choice([*skills_candidates])
                            item[f'skill{i + 1}'] = skill

                            if skill in self.skills_lp_table:
                                base = self.skills_lp_table[skill]
                                mod_range = sorted([self.random_from_triangular(25, 500),
                                                    self.random_from_triangular(25, 150)])
                                mod = self.random_from_triangular(*mod_range)
                                lp = int(max(
                                    min(base * mod * 0.01 // 5 * 5, self.options.weapon_skill_lp_max),
                                    self.options.weapon_skill_lp_min
                                ))
                            else:
                                lp = int(self.random_from_distribution(
                                    Weights.SKILL_LP_MU, Weights.SKILL_LP_SIGMA,
                                    self.options.weapon_skill_lp_min,
                                    self.options.weapon_skill_lp_max
                                ))

                            skills_candidates.discard(skill)
                            for u in users:
                                set_skills_per_char[u].discard(skill)

                            if not len(skills_candidates):
                                continue_iter = False

                        item[f'skill{i + 1}_lp'] = max(
                            min(int(lp * self.options.weapon_skill_lp_mod), self.options.weapon_skill_lp_max),
                            self.options.weapon_skill_lp_min
                        )

                        if i + 1 >= self.options.weapon_skills_max:
                            continue_iter = False
                    else:
                        item[f'skill{i + 1}'] = 0
                        item[f'skill{i + 1}_lp'] = 0

                        continue_iter = False

    def report(self):
        if sys.stdout.encoding == "utf-8":
            logger.info("\u2B2C ITEMS")
        else:
            logger.info("> ITEMS")

        base_total: int = len(self.candidates['base'])

        items_ratio: str = f"{self.statistics['Items']:<4}/{base_total}"
        prices_ratio: str = f"{self.statistics['Prices']:<4}/{self.statistics['Items']}"
        skills_ratio: str = f"{self.statistics['Skills']:<4}/{self.statistics['Items']}"

        items_percentage: float = safe_divide(self.statistics['Items'], base_total)
        prices_percentage: float = safe_divide(self.statistics['Prices'], self.statistics['Items'])
        skills_percentage: float = safe_divide(self.statistics['Skills'], self.statistics['Items'])

        logger.info(f"{"":>4}{"> Candidates:":<21}{items_ratio:<12}{items_percentage:.2f}%")
        logger.info(f"{"":>4}{"> Prices:":<21}{prices_ratio:<12}{prices_percentage:.2f}%")
        logger.info(f"{"":>4}{"> Skills:":<21}{skills_ratio:<12}{skills_percentage:.2f}%")
        logger.info("")


class ShopRandomizer(BaseRandomizer):
    def __init__(self, random_obj: random.Random, data: dict, _options: dict):
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

        blacklisted: set[int] = set(self.shop_data['missables'])
        candidates = deepcopy(self.shop_data['items'])
        candidates['commons'] = [group for group in candidates['commons']
                                 if not (blacklisted.intersection(group.get("shops", [])))]

        candidates['uniques'] = {shop: items for shop, items in candidates['uniques'].items()
                                 if shop not in blacklisted}

        self.candidates = deepcopy(candidates)

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

            shop_group['items'] = sorted(new_items)
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

            self.candidates['uniques'][shop] = sorted(new_items)

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

    def report(self):
        if sys.stdout.encoding == "utf-8":
            logger.info("\u20B2 SHOPS")
        else:
            logger.info("> SHOPS")

        items_ratio: str = f"{self.statistics['Items']:<4}"
        full_shuffle_ratio: str = f"{self.statistics['Full Shuffle']:<4}/{self.statistics['Items']}"
        same_category_ratio: str = f"{self.statistics['Same Category']:<4}/{self.statistics['Items']}"

        full_shuffle_percentage: float = safe_divide(self.statistics['Full Shuffle'], self.statistics['Items'])
        same_category_percentage: float = safe_divide(self.statistics['Same Category'], self.statistics['Items'])

        logger.info(f"{"":>4}{"> Candidates:":<21}{items_ratio}")
        logger.info(f"{"":>4}{"> Full Shuffle:":<21}{full_shuffle_ratio:<12}{full_shuffle_percentage:.2f}%")
        logger.info(f"{"":>4}{"> Same Category:":<21}{same_category_ratio:<12}{same_category_percentage:.2f}%")
        logger.info("")


class ChestRandomizer(BaseRandomizer):
    GALD_ID = 0xFFFFFFFE

    def __init__(self, random_obj: random.Random, data: dict, _options: dict):
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

        candidates = deepcopy(self.chest_data)
        for area, data in candidates.items():
            for chest, properties in data.items():
                candidates[area][chest] = {'items': properties['items']}

        self.candidates = deepcopy(candidates)

    def randomize(self):
        for area, chests in self.candidates.items():
            for chest, details in chests.items():
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
                new_category = self.item_to_category.get(new_item, -1)

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

    def report(self):
        if sys.stdout.encoding == "utf-8":
            logger.info("\u225B CHESTS")
        else:
            logger.info("> CHESTS")

        chests_ratio: str = f"{self.statistics['Chests']:<4}"
        full_shuffle_ratio: str = f"{self.statistics['Full Shuffle']:<4}/{self.statistics['Chests']}"
        same_category_ratio: str = f"{self.statistics['Same Category']:<4}/{self.statistics['Chests']}"
        item_amount_ratio: str = f"{self.statistics['Item Amount']:<4}/{self.statistics['Chests']}"
        gald_amount_ratio: str = f"{self.statistics['Gald Amount']:<4}/{self.statistics['Chests']}"

        full_shuffle_percentage: float = safe_divide(self.statistics['Full Shuffle'], self.statistics['Chests'])
        same_category_percentage: float = safe_divide(self.statistics['Same Category'], self.statistics['Chests'])
        item_amount_percentage: float = safe_divide(self.statistics['Item Amount'], self.statistics['Chests'])
        gald_amount_percentage: float = safe_divide(self.statistics['Gald Amount'], self.statistics['Chests'])

        logger.info(f"{"":>4}{"> Candidates:":<21}{chests_ratio}")
        logger.info(f"{"":>4}{"> Full Shuffle:":<21}{full_shuffle_ratio:<12}{full_shuffle_percentage:.2f}%")
        logger.info(f"{"":>4}{"> Same Category:":<21}{same_category_ratio:<12}{same_category_percentage:.2f}%")
        logger.info(f"{"":>4}{"> Item Amount:":<21}{item_amount_ratio:<12}{item_amount_percentage:.2f}%")
        logger.info(f"{"":>4}{"> Gald Amount:":<21}{gald_amount_ratio:<12}{gald_amount_percentage:.2f}%")
        logger.info("")


class SearchPointOptions:
    def __init__(self, options: dict):
        self.uses_min = options.get('uses_min', 1)
        self.uses_max = options.get('uses_max', 5)
        self.pools_min = options.get('pools_min', 1)
        self.pools_max = options.get('pools_max', 5)
        self.items_min = options.get('items_min', 1)
        self.items_max = options.get('items_max', 5)


class SearchPointRandomizer(BaseRandomizer):
    def __init__(self, random_obj: random.Random, data: dict, options: dict):
        self.random = random_obj
        self.item_to_category = data['item_to_category']
        self.item_by_category = data['item_by_category']
        self.common_items = data['common_items']
        self.abundant_items = set(item for c in {2, 8, 9} for item in self.item_by_category[c])
        self.options = SearchPointOptions(options)

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
            content_range: int = self.random_from_triangular(self.options.pools_min, self.options.pools_max)
            self.candidates['definitions'].append({
                'type': self.random.choice(definition_types),
                'content_range': content_range,
                'max_use': self.random_from_triangular(self.options.uses_min, self.options.uses_max)
            })

            # Randomize Content
            item_ranges: list[int] = [self.random.randint(self.options.items_min, self.options.items_max)
                                      for _ in range(content_range)]
            for r in item_ranges:
                self.candidates['contents'].append({
                    'item_range': r,
                    'chance': self.random_from_triangular(1, 10, 'max')
                })

            # Randomize Items
            for count in item_ranges:
                placed: set[int] = set()
                for _ in range(count):
                    if random.random() <= Weights.SEARCH_ABUNDANTS:
                        iid: int = self.random.choice([*self.abundant_items.difference(placed)])
                    else:
                        iid: int = self.random.choice([*set(self.common_items).difference(placed)])

                    count: int = 1
                    if enums.ItemCategory.is_abundant(self.item_to_category[iid]):
                        count = self.random_from_triangular(1, 15)

                    placed.add(iid)
                    self.candidates['items'].append({
                        'id': iid,
                        'count': count
                    })

            self.statistics['Contents'].append(content_range)
            self.statistics['Items'].extend(item_ranges)

    def report(self):
        if sys.stdout.encoding == "utf-8":
            logger.info("\u219F SEARCH POINTS")
        else:
            logger.info("> SEARCH POINTS")

        avg_con: int = sum(self.statistics['Contents']) / 88
        avg_itm: int = safe_divide(sum(self.statistics['Items']), sum(self.statistics['Contents']))

        contents_count: str = f"{sum(self.statistics['Contents'])}"
        items_count: str = f"{sum(self.statistics['Items'])}"
        average_contents: str = f"{avg_con:.2f}"
        average_items: str = f"{avg_itm:.2f}"

        logger.info(f"{"":>4}{"> Contents:":<40}{contents_count}")
        logger.info(f"{"":>4}{"> Items:":<40}{items_count}")
        logger.info(f"{"":>4}{"> Average Contents per Search Point:":<40}{average_contents}")
        logger.info(f"{"":>4}{"> Average Items per Content:":<40}{average_items}")
        logger.info("")


class BasicRandomizerProcedure:
    artes_data_table: dict
    skills_data_table: dict

    artes_ids: dict
    skill_ids: dict
    item_ids: dict

    artes_by_char: dict[int, list[int]]
    skills_by_char: dict[int, list[int]]

    items_data_table: dict
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
    patch_output: str = os.path.join(Paths.PATCHES_DIR, f"randomizer.{Extensions.BASIC_PATCH}")
    report_output: str = os.path.join(Paths.PATCHES_DIR, "tovde-spoiler.ods")

    def __init__(self, targets: list[str], identifier: str = "", seed = random.randint(1, 0xFFFFFFFF)):
        self.seed = uuid.uuid1().int
        self.random = random.Random(seed)

        self.name = identifier if identifier else "sicily"
        self.date = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")
        self.identifier = f"{self.name}-{self.date}"
        self.patch_output = os.path.join(Paths.PATCHES_DIR, f"{self.identifier}{Extensions.BASIC_PATCH}")
        self.report_output = os.path.join(Paths.PATCHES_DIR, f"tovde-spoiler-{self.identifier}.ods")

        if not targets or 'artes' in targets:
            self.load_artes_data()

        if not targets or {'artes', 'skills', 'items'}.intersection(targets):
            self.load_skills_data()

        item_dependents: set[str] = set(targets).intersection({'items', 'shops', 'chests', 'search'})
        if not targets or item_dependents:
            self.load_items_data()

        if not os.path.isdir(Paths.PATCHES_DIR):
            os.makedirs(Paths.PATCHES_DIR)

    def load_artes_data(self):
        with open(Paths.STATIC_PATH.joinpath("artes.json")) as f:
            artes_data_table = json.load(f, object_hook=keys_to_int)

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
        with open(Paths.STATIC_PATH.joinpath("skills.json")) as f:
            skills_data_table = json.load(f, object_hook=keys_to_int)

        self.skills_data_table = {int(sid): skill['properties']
                                  for sid, skill in skills_data_table['entries'].items()}

        skills_by_char = {}
        for sid, data in skills_data_table['entries'].items():
            if not data['users']: continue
            for user in data['users']:
                skills_by_char.setdefault(user, []).append(sid)

        self.skills_by_char = skills_by_char

    def load_items_data(self):
        with open(Paths.STATIC_PATH.joinpath("items.json")) as f:
            self.items_data_table = json.load(f, object_hook=keys_to_int)

        self.item_by_category = {}
        self.item_to_category = {}
        self.common_items = tuple()

        for iid, item in self.items_data_table.items():
            self.item_by_category.setdefault(item['category'], []).append(item['id'])
            self.item_to_category[item['id']] = item['category']

        self.common_items = tuple([item for category, items in self.item_by_category.items()
                                   for item in items
                                   if enums.ItemCategory.is_common(category)])

    def generate(self, targets: list, options: dict = MainOptionsDefault().model_dump() , spoil: bool = False):
        output: str = self.patch_output

        patch_data: dict = {
            'version': '0.2',
            'created': self.date,
            'seed': self.seed,
            'player': self.name,
        }

        if os.path.isfile(self.report_output):
            os.remove(self.report_output)

        start_time: float = time.time()

        if not targets or 'artes' in targets:
            data: dict = {
                'artes_data': self.artes_data_table,
                'artes_by_char': self.artes_by_char,
                'skills_by_char': self.skills_by_char,
            }

            logger.info("> Randomizing Artes")
            self.arte_randomizer = ArteRandomizer(self.random, data, options.get('artes', {}),)
            self.arte_randomizer.randomize()

            patch_data['artes'] = self.arte_randomizer.fetch()

            self.arte_randomizer.report()

        if not targets or 'skills' in targets:
            data: dict = {
                'skills_data': self.skills_data_table,
            }

            logger.info("> Randomizing Skills")
            self.skill_randomizer = SkillRandomizer(self.random, data, options.get('skills', {}))
            self.skill_randomizer.randomize()

            patch_data['skills'] = self.skill_randomizer.fetch()
            self.skill_randomizer.report()

        if not targets or 'items' in targets:
            skills_lp_table: dict = {}
            if 'skills' in patch_data:
                skills_lp_table = {sid: v['lp_cost'] for sid,v in patch_data['skills'].items()}

            logger.info("> Randomizing Items")
            data: dict = {
                'items_data': self.items_data_table,
                'skills_lp_table': skills_lp_table,
                'skills_by_char': self.skills_by_char,
            }

            self.item_randomizer = ItemRandomizer(self.random, data, options.get('items', {}))
            self.item_randomizer.randomize()

            patch_data['items'] = self.item_randomizer.fetch()
            self.item_randomizer.report()

        if not targets or 'shops' in targets:
            with open(Paths.STATIC_PATH.joinpath("shop.json")) as f:
                shop_data: dict = json.load(f, object_hook=keys_to_int)

            data: dict = {
                'shop_data': shop_data,
                'item_to_category': self.item_to_category,
                'item_by_category': self.item_by_category,
                'common_items': self.common_items,
            }

            logger.info("> Randomizing Shops")
            self.shop_randomizer = ShopRandomizer(self.random, data, options.get('shops', {}))
            self.shop_randomizer.randomize()

            patch_data['shops'] = self.shop_randomizer.fetch()
            self.shop_randomizer.report()

        if not targets or 'chests' in targets:
            with open(Paths.STATIC_PATH.joinpath("chests.json")) as f:
                chest_data: dict = json.load(f, object_hook=keys_to_int)

            data: dict = {
                'chest_data': chest_data,
                'item_to_category': self.item_to_category,
                'item_by_category': self.item_by_category,
                'common_items': self.common_items,
            }

            logger.info("> Randomizing Chests")
            self.chest_randomizer = ChestRandomizer(self.random, data, options.get('chests', {}))
            self.chest_randomizer.randomize()

            patch_data['chests'] = self.chest_randomizer.fetch()
            self.chest_randomizer.report()

        if not targets or 'search' in targets:
            data: dict = {
                'item_to_category': self.item_to_category,
                'item_by_category': self.item_by_category,
                'common_items': self.common_items,
            }

            logger.info("> Randomizing Search Points")
            self.search_point_randomizer = SearchPointRandomizer(self.random, data, options.get('search', {}))
            self.search_point_randomizer.randomize()

            patch_data['search'] = self.search_point_randomizer.fetch()
            self.search_point_randomizer.report()

        end_time: float = time.time()

        logger.info(f"\nRandomization Complete. Finished in {end_time - start_time:.2f} seconds.")
        with open(output, 'w') as f:
            json.dump(patch_data, f)

            logger.info(f"Patch File: {os.path.abspath(output)}")

        if spoil:
            patch_data: dict = dict(item for item in [*patch_data.items()][4:])

            start_time = time.time()
            logger.info(f"\n> Generating Spoiler Sheet")

            spoiler = PatchSpoiler()
            spoiler.write_spreadsheet(patch_data, self.report_output)

            end_time = time.time()
            logger.info(f"\nSpoiler Sheet Generated. Finished in {end_time - start_time:.2f} seconds.")
            logger.info(f"Spoiler Sheet: {os.path.abspath(self.report_output)}")


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
    template.generate(target_list, {}, create_spoiler)

    total: float = time.time() - start

    if create_spoiler:
        print(f"Spoiler File: {os.path.abspath(template.report_output)}")
