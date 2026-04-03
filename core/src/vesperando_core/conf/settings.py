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

    CONFIG = os.path.join(EXEC_DIR, "config", "config.yaml")
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
    SKILL_CANDIDACY = 0.05
    SKILL_SP_COST = 0.95
    SKILL_SP_MU = 7.6
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
    ITEM_CANDIDACY = 0.05
    ITEM_PRICE = 0.95
    ITEM_SKILL_OPPORTUNITIES: tuple = (
        0.96,
        0.875,
        0.61
    )
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