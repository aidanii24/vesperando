from pydantic import AfterValidator
from typing import Annotated, Callable


def check_positive(value: int | float) -> int | float:
    """Must be a positive integer, including 0"""
    if value < 0:
        raise ValueError(f"{value} is negative, which is invalid.")

    return value

def check_positive_strict(value: int | float) -> int | float:
    """Must be a positive integer, but more than 0"""
    if value <= 0:
        raise ValueError(f"{value} is zero or negative, which is invalid.")

    return value

def check_max(value: int | float, max_value: int) -> int | float:
    """value must not be more than max_value"""
    if value >  max_value:
        raise ValueError(f"{value} is greater than {max_value}, which is invalid.")

    return value

def check_weapon_skill_count(value: int | float) -> int | float:
    """Must be any integer from 1 to 3"""
    check_positive(value)
    check_max(value, 3)
    return value

def check_max_ten_thousand(value: int | float) -> int | float:
    """Must be any integer from 1 to 9999"""
    check_positive_strict(value)
    check_max(value, 9999)
    return value

def check_max_thousand(value: int | float) -> int | float:
    """Must be any integer from 1 to 999"""
    check_positive_strict(value)
    check_max(value, 999)
    return value

def check_max_hundred(value: int | float) -> int | float:
    """Must be any integer from 1 to 99"""
    check_positive_strict(value)
    check_max(value, 99)
    return value

def check_max_ten(value: int | float) -> int | float:
    """Must be any integer from 1 to 9"""
    check_positive_strict(value)
    check_max(value, 9)
    return value

def check_mod(value: int | float) -> int | float:
    """Must be any non-zero positive float less than 10"""
    check_positive_strict(value)
    check_max(value, 10)

    return value

def check_tp(value: int | float) -> int | float:
    """Must be any integer from 1 to 200"""
    check_positive_strict(value)
    check_max(value, 200)
    return value

def check_lp_ratio(value: int) -> int:
    """Must be any integer from 1 to 100"""
    check_positive_strict(value)
    check_max(value, 100)
    return value

def create_annotation(t, ann, doc_from_ann: bool = True) -> Callable:
    a = Annotated[t, ann]
    if doc_from_ann:
        a.__doc__ = ann.__doc__

    return a

IntPositiveStrict = create_annotation(int, AfterValidator(check_positive_strict))
MaxTenThousand = create_annotation(int, AfterValidator(check_max_ten_thousand))
MaxThousand = create_annotation(int, AfterValidator(check_max_thousand))
MaxHundred = create_annotation(int, AfterValidator(check_max_hundred))
MaxTen = create_annotation(int, AfterValidator(check_max_ten))
Mod = create_annotation(float, AfterValidator(check_mod))
TP = create_annotation(int, AfterValidator(check_tp))
LPRatio = create_annotation(int, AfterValidator(check_lp_ratio))
WeaponSkillCount = create_annotation(int, AfterValidator(check_weapon_skill_count))
PydBool = bool

IntPositiveStrict.__doc__ = check_positive_strict.__doc__
MaxTenThousand.__doc__ = check_max_ten_thousand.__doc__
MaxThousand.__doc__ = check_max_thousand.__doc__
MaxHundred.__doc__ = check_max_hundred.__doc__
MaxTen.__doc__ = check_max_ten.__doc__
Mod.__doc__ = check_mod.__doc__
TP.__doc__ = check_tp.__doc__
LPRatio.__doc__ = check_lp_ratio.__doc__
WeaponSkillCount.__doc__ = check_weapon_skill_count.__doc__