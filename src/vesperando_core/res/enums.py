import enum


class Characters(enum.Enum):
    YURI = 1
    ESTELLE = 2
    KAROL = 4
    RITA = 8
    RAVEN = 16
    JUDITH = 32
    REPEDE = 64
    FLYNN = 128
    PATTY = 256

class Symbol(enum.Enum):
    FLECK = 0
    ROCKRA = 1
    STRHIM = 2
    LAYTOS = 3

    @classmethod
    def _missing_(cls, value):
        return cls.FLECK

class FatalStrikeType(enum.Enum):
    INDIGO = 0
    CRIMSON = 1
    VIRIDIAN = 2
    NONE = 3

    @classmethod
    def _missing_(cls, value):
        return cls.NONE

class SearchPointType(enum.Enum):
    TREE_STUMP = 0
    SHELL = 1
    BONES = 2
    SEAGULL = 3