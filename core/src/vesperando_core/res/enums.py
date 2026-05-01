import enum


class Characters(enum.Enum):
    YURI = 1
    ESTELLE = 2
    KAROL = 3
    RITA = 4
    RAVEN = 5
    JUDITH = 6
    REPEDE = 7
    FLYNN = 8
    PATTY = 9

    def bitflag(self):
        return 1 << (self.value - 1)


class ArteTypes(enum.Enum):
    NORMALS = 0
    NOVICE = 1
    INTERMEDIATE = 2
    ADVANCED = 3
    BASE = 4
    ARCANE = 5
    BURST_MAGIC = 6
    BURST_PHYSICAL = 7
    ALTERED_MAGIC = 8
    ALTERED_PHYSICAL = 9
    BURST_VAR_MAGIC = 10
    BURST_VAR_PHYSICAL = 11
    FATAL_STRIKE = 12
    MYSTIC = 13
    OVERLIMIT = 14
    SKILL = 15

    @classmethod
    def is_normal(cls, atype):
        specials: list[cls] = [cls.FATAL_STRIKE, cls.OVERLIMIT, cls.SKILL]

        if isinstance(atype, cls):
            return atype in specials
        elif isinstance(atype, int):
            return cls(atype) in specials
        elif isinstance(atype, str):
            return cls[atype] in specials

        return False

    @classmethod
    def _missing_(cls, value):
        return -1


class ArteLearningTypes(enum.Enum):
    NONE = 0
    LEVEL = 1
    ARTE_USAGE = 2
    SKILL = 3


class SkillSymbols(enum.Enum):
    FLECK = 0
    ROCKRA = 1
    STRHIM = 2
    LAYTOS = 3

    @classmethod
    def _missing_(cls, value):
        return cls.FLECK

class ItemCategory(enum.Enum):
    DUMMY = 0
    UNKNOWN = 1
    CONSUMABLE = 2
    MAIN = 3
    SUB = 4
    HEAD = 5
    BODY = 6
    ACCESSORY = 7
    INGREDIENTS = 8
    MATERIALS = 9
    VALUABLES = 10
    DLC = 11

    @classmethod
    def is_valid(cls, category):
        if isinstance(category, cls):
            return 12 > category.value > 1
        elif isinstance(category, int):
            return 12 > category > 1
        elif isinstance(category, str):
            try:
                validity = 12 > cls[category].value > 1
                return validity
            except AttributeError:
                return False

        return False

    @classmethod
    def is_common(cls, category):
        if not cls.is_valid(category): return False

        if isinstance(category, cls):
            return category.value < 10
        elif isinstance(category, int):
            return category < 10
        elif isinstance(category, str):
            try:
                validity = cls[category].value < 10
                return validity
            except AttributeError:
                return False

        return False

    @classmethod
    def is_abundant(cls, category):
        abundant_categories = [cls.CONSUMABLE.value, cls.INGREDIENTS.value, cls.MATERIALS.value]

        if isinstance(category, cls):
            return category.value in abundant_categories
        elif isinstance(category, int):
            return category in abundant_categories
        elif isinstance(category, str):
            try:
                validity = cls[category].value in abundant_categories
                return validity
            except AttributeError:
                return False

        return False

    @classmethod
    def is_weapon(cls, category):
        if not cls.is_valid(category): return False

        if isinstance(category, cls):
            return 2 < category.value < 5
        elif isinstance(category, int):
            return 2 < category < 5
        elif isinstance(category, str):
            try:
                validity = 2 < cls[category].value < 5
                return validity
            except AttributeError:
                return False

        return False


class FatalStrikeType(enum.Enum):
    INDIGO = 0
    CRIMSON = 1
    VIRIDIAN = 2
    NONE = 3

    @classmethod
    def _missing_(cls, value):
        return cls.NONE


class ChestType(enum.Enum):
    NORMAL = 0x0
    WOODEN = 0x1
    ROYAL = 0x2
    STONE = 0x3
    PURPLE = 0x4
    RED_ROYAL = 0x6
    BLUE_ROYAL = 0x7
    INVISIBLE = 0xFFFFFFFF


class SearchPointType(enum.Enum):
    TREE_STUMP = 0
    SHELL = 1
    BONES = 2
    SEAGULL = 3

class PCParamSlot(enum.Enum):
    INVALID = 0x0
    MAIN = 0xB
    SUB = 0xC
    BODY = 0xD
    HEAD = 0xE

    @classmethod
    def __missing__(cls, key):
        return cls.INVALID