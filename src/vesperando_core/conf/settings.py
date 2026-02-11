import os
import sys


IS_EXEC: bool = hasattr(sys, '_MEIPASS')

class Paths:
    EXEC_DIR = os.getcwd() if not IS_EXEC else sys._MEIPASS
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if not IS_EXEC else sys._MEIPASS
    STATIC_DIR = os.path.join(BASE_DIR, 'static')

    CONFIG = os.path.join(EXEC_DIR, "config", "config.yaml")
    PATCHES = os.path.join(EXEC_DIR, "patches")
    BUILD = os.path.join(EXEC_DIR, "build")
    MANIFESTS = os.path.join(BUILD, ".manifests")
    OUTPUT = os.path.join(EXEC_DIR, "output")

    GAME = os.path.join("steam", "steamapps", "common", "Tales of Vesperia Definitive Edition")
    BACKUP = os.path.join("Data64", ".backup")
    BTL =os.path.join("Data64", "btl.svo")
    ITEM = os.path.join("Data64", "item.svo")
    NPC = os.path.join("Data64", "npc.svo")
    UI = os.path.join("Data64", "UI.svo")
    SCENARIO = os.path.join("Data64", "language", "scenario_ENG.dat")