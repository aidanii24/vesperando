import os


class Paths:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    STATIC_DIR = os.path.join(BASE_DIR, 'static')
    RES_DIR = os.path.join(BASE_DIR, 'res')
    LIB_DIR = os.path.join(BASE_DIR, 'lib')

    CONFIG = os.path.join(os.getcwd(), "config.json")
    PATCHES = os.path.join(os.getcwd(), "patches")
    BUILDS = os.path.join(os.getcwd(), "builds")
    MANIFESTS = os.path.join(BUILDS, "manifests")
    OUTPUT = os.path.join(os.getcwd(), "output")

    VESPERIA = os.path.join("steam", "steamapps", "common", "Tales of Vesperia Definitive Edition")
    BACKUP = os.path.join(VESPERIA, "Data64", ".backup")
    BTL =os.path.join(VESPERIA, "Data64", "btl.svo")
    ITEM = os.path.join(VESPERIA, "Data64", "item.svo")
    NPC = os.path.join(VESPERIA, "Data64", "npc.svo")
    UI = os.path.join(VESPERIA, "Data64", "UI.svo")
    SCENARIO = os.path.join(VESPERIA, "Data64", "language", "scenario_ENG.dat")

class Keys:
    DEP_VESPERIA = "vesperia"
