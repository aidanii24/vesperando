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

    HYOUTA = "HyoutaToolsCLI"

class Keys:
    DEP_VESPERIA = "vesperia"
    DEP_DOTNET = "dotnet"
    DEP_HYOUTA = "hyouta"
    DEP_COMPTOE = "comptoe"

class Checksums:
    VESPERIA = "ee3212432d063c3551f8d5eb9c8dde6d55a22240912ae9ea3411b3808bfb3827"
    BTL = "bab8c0497665bd5a46f2ffabba5f4d2acc9fcdf0e4e0dd50c1b8199d3f6d7111"
    ITEM = "d86e4e3d7df4d60c9c752f999e916d495c77b2ae321c18fe281a51464a5d4d25"
    NPC = "71a7d13dc3254b6981cf88b0f6142ea3a0603e21784bfce956982a37afba1333"
    SCENARIO = "90a1e41ae829ba7f05e289aaba87cb4699e3ed27acc9448985f6f91261da8e2d"
