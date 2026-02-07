import os


class Paths:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    STATIC_DIR = os.path.join(BASE_DIR, 'static')

    CONFIG = os.path.join(os.getcwd(), "config.json")
    PATCHES = os.path.join(os.getcwd(), "patches")
    BUILD = os.path.join(os.getcwd(), "build")
    MANIFESTS = os.path.join(BUILD, ".manifests")
    OUTPUT = os.path.join(os.getcwd(), "output")

    GAME = os.path.join("steam", "steamapps", "common", "Tales of Vesperia Definitive Edition")
    BACKUP = os.path.join("Data64", ".backup")
    BTL =os.path.join("Data64", "btl.svo")
    ITEM = os.path.join("Data64", "item.svo")
    NPC = os.path.join("Data64", "npc.svo")
    UI = os.path.join("Data64", "UI.svo")
    SCENARIO = os.path.join("Data64", "language", "scenario_ENG.dat")