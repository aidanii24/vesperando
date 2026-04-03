from pydantic import AfterValidator
from typing import Annotated, Callable


def check_positive_strict(value: int | float) -> int | float:
    if value <= 0:
        raise ValueError(f"{value} is zero or negative, which is invalid.")

    return value

def check_max(value: int | float, max_value: int) -> int | float:
    if value >  max_value:
        raise ValueError(f"{value} is greater than {max_value}, which is invalid.")

    return value

def factory_check_max(max_value: int) -> Callable[[int | float], int | float]:
    return lambda x: check_max(x, max_value)

def check_weapon_skill_count(value: int | float) -> int | float:
    check_positive_strict(value)
    check_max(value, 3)
    return value

def check_max_ten_thousand(value: int | float) -> int | float:
    check_positive_strict(value)
    check_max(value, 9999)
    return value

def check_max_thousand(value: int | float) -> int | float:
    check_positive_strict(value)
    check_max(value, 999)
    return value

def check_max_hundred(value: int | float) -> int | float:
    check_positive_strict(value)
    check_max(value, 99)
    return value

def check_max_ten(value: int | float) -> int | float:
    check_positive_strict(value)
    check_max(value, 9)
    return value

def check_mod(value: int | float) -> int | float:
    check_positive_strict(value)
    check_max(value, 10)

    return value

def check_tp(value: int | float) -> int | float:
    check_positive_strict(value)
    check_max(value, 100)
    return value


IntPositiveStrict = Annotated[int, check_positive_strict]
MaxTenThousand = Annotated[int, check_max_ten_thousand]
MaxThousand = Annotated[int, check_max_thousand]
MaxHundred = Annotated[int, check_max_hundred]
MaxTen = Annotated[int, check_max_ten]
Mod = Annotated[float, AfterValidator(check_mod)]
TP = Annotated[int, AfterValidator(check_tp)]
WeaponSkillCount = Annotated[int, check_weapon_skill_count]