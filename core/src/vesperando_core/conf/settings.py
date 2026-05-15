from importlib import resources
from dataclasses import dataclass
import os
import sys

from vesperando_core import static, lib


IS_EXEC: bool = hasattr(sys, '_MEIPASS')

@dataclass(frozen=True)
class Paths:
    EXEC_DIR = os.path.dirname(sys._MEIPASS) if IS_EXEC else os.getenv('EXEC_DIR', os.getcwd())
    LOG_DIR = os.path.join(EXEC_DIR, 'logs')
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if not IS_EXEC \
        else os.path.join(sys._MEIPASS, 'vesperando_core')
    STATIC_PATH = resources.files(static)
    LIB_PATH = resources.files(lib)

    CONFIG = os.path.join(EXEC_DIR, "config", "settings.yaml")
    OPTIONS_DIR = os.path.join(EXEC_DIR, "options")
    PATCHES_DIR = os.path.join(EXEC_DIR, "patches")
    BUILD_DIR = os.path.join(EXEC_DIR, "build")
    MANIFESTS_DIR = os.path.join(BUILD_DIR, ".manifests")
    OUTPUT_dir = os.path.join(EXEC_DIR, "output")

    GAME_DIR = os.path.join("steam", "steamapps", "common", "Tales of Vesperia Definitive Edition")
    BACKUP_DIR = os.path.join("Data64", ".backup")
    BTL =os.path.join("Data64", "btl.svo")
    ITEM = os.path.join("Data64", "item.svo")
    NPC = os.path.join("Data64", "npc.svo")
    UI = os.path.join("Data64", "UI.svo")
    SCENARIO = os.path.join("Data64", "language", "scenario_ENG.dat")


@dataclass(frozen=True)
class Extensions:
    BASIC_PATCH = ".vbrp"
    APPATCH = ".vapp"
    PATCHES = [BASIC_PATCH, APPATCH]

    @classmethod
    def is_valid_patch(cls, patch_name: str):
        return any(patch_name.endswith(ext) for ext in cls.PATCHES)


@dataclass(frozen=True)
class Weights:
    ARTE_CANDIDACY = 0.05
    ARTE_TP_COST = 0.4
    ARTE_TP_COST_MULTIPLIER = 0.4
    ARTE_CAST_TIME = 0.7
    ARTE_FS = 0.75
    ARTE_EVOLVE = 0.6   # 0.258 for actual ration of character artes with evolves in Vanilla
    ARTE_NON_ALTERED_EVOLVE = 0.1
    ARTE_EVOLVE_REQUIREMENT = 0.4
    ARTE_EVOLVE_OPPORTUNITIES: tuple = (
        0,
        0.0258,
        0.0041,
        0.0005,
        0.005
    )
    ARTE_LEARN_OPPORTUNITIES: tuple = (
        0,
        0.75,
        0.042,
        0.8,
        # 0.077
    )
    ARTE_LEARN_TYPE_OPPORTUNITIES: tuple = (
        (0, 0),
        (0.35, 0.05),
        (0.005, 0.005),
        (0.75, 0.05),
        (0.5, 0.5)
    )
    ARTE_EFFECT_OPPORTUNITY: float = 0.185
    ARTE_EFFECT_OPPORTUNITY_MULTI: float = 0.37
    ARTE_EFFECT_NEXT_OPPORTUNITY: float = 0.21
    ARTE_EFFECT_ONLY_OPPORTUNITY: float = 0.18
    ARTE_POWER_OPPORTUNITY: float = 0.4
    ARTE_POWER_MU: float = 243.60
    ARTE_POWER_SIGMA: float = 280.62
    ARTE_POWER_MOD_OPPORTUNITY: float = 0.4
    ARTE_POWER_MOD_MISTYPE_OPPORTUNITY: float = 0.15
    ARTE_TARGET_OPPORTUNITY: float = 0.1
    ARTE_TARGET_DISTRIBUTION: tuple = (
        0.5,
        0.4,
        0.15,
        0.1,
        0.5
    )
    ARTE_ELEMENT_OPPORTUNITY: float = 0.25
    ARTE_ELEMENT_COUNT_DISTRIBUTION: tuple = (
        0.75,
        0.10,
        0.15
    )
    ARTE_ELEMENT_DISTRIBUTION: tuple = (
        0.27,
        0.14,
        0.14,
        0.23,
        0.14,
        0.06,
    )
    SKILL_CANDIDACY = 0.05
    SKILL_SP_COST = 0.95
    SKILL_SP_MU = 3.8   # Vanilla is at 7.6
    SKILL_SP_SIGMA = 5
    SKILL_LP = 0.95
    SKILL_LP_MU = 329.16
    SKILL_LP_SIGMA = 226.17
    SKILL_SYMBOL = 0.75
    SKILL_SYMBOL_WEIGHT = 0.75
    SKILL_SYMBOL_WEIGHT_MU = 3.48
    SKILL_SYMBOL_WEIGHT_SIGMA = 3.58
    SKILL_SYMBOL_DISTRIBUTION: tuple = (
        0.28,
        0.20,
        0.27,
        0.25
    )
    SKILL_PARAMETER = 0.12
    SKILL_PARAMETER_NEXT = 0.4
    ITEM_CANDIDACY = 0.05
    ITEM_PRICE = 0.95
    ITEM_PRICE_MULTIPLIER = 0.99
    ITEM_ELEMENT_OPPORTUNITY = 0.67
    ITEM_WEAPON_ELEMENT_COUNT_DISTRIBUTION: tuple = (
        0.5,
        0.35,
        0.1,
        0.025,
        0.025,
        0,
        0,
    )
    ITEM_WEAPON_ELEMENT_DISTRIBUTION: tuple = (
        0.25,
        0.15,
        0.15,
        0.21,
        0.14,
        0.10,
    )
    ITEM_EQUIPMENT_ELEMENT_COUNT_DISTRIBUTION: tuple = (
        0.2,
        0.1,
        0.2,
        0.1,
        0.2,
        0.1,
        0.1
    )
    ITEM_EQUIPMENT_ELEMENT_DISTRIBUTION: tuple = (
        0.22,
        0.20,
        0.18,
        0.18,
        0.12,
        0.10,
    )
    ITEM_STATS_OPPORTUNITY: float = 0.78
    ITEM_STATS_MATCH: float = 0.2
    ITEM_STATS_SUB_ZERO: float = 0.42
    ITEM_STATS_RELATED = 0.12    # Randomize main stat counterpart
    ITEM_STATS_AUX = 0.06   # Randomize other stats (e.g. Agility)
    ITEM_STATS_AUX_COUNT_DISTRIBUTION: tuple = (
        0.55,
        0.40,
        0.05
    )
    ITEM_STATS_AUX_DISTRIBUTION: tuple = (
        0.9,
        0.1
    )
    ITEM_SKILL_OPPORTUNITIES: tuple = (
        0.96,
        0.875,
        0.61
    )
    ITEM_SKILL_LP = 0.1
    SHOP_CANDIDACY = 0.1
    SHOP_CANDIDACY_REPEAT = 0.75
    SHOP_CANDIDACY_CONSUMABLE = 0.7
    SHOP_CANDIDACY_CONSUMABLE_REPEAT = 0.6
    CHEST_CANDIDACY = 0.85
    CHEST_TYPE = 0.65
    CHEST_CANDIDACY_REPEAT = 0.85
    CHEST_CANDIDACY_CONSUMABLE_REPEAT = 0.2
    CHEST_ITEM_AMOUNT = 0.1
    SEARCH_ABUNDANTS = 0.85
    EVENTS_CANDIDACY = 0.08
    EVENTS_CHARACTER_TARGET = 0.3
    EVENTS_ITEM_WEAPON_AMOUNT = 0.2