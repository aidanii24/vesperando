from typing import Optional

from pydantic import BaseModel


class ArtesOptions(BaseModel):
    tp_mod: float = 1.0
    tp_min: int = 1
    tp_max: int = 99
    learn_arte_usage_mod: float = 1.0
    learn_arte_usage_min: int = 5
    learn_arte_usage_max: int = 200
    enable_non_altered_evolve: bool = False


class SkillsOptions(BaseModel):
    sp_mod: float = 1.0
    sp_min: int = 1
    sp_max: int = 30


class ItemsOptions(BaseModel):
    price_mod: float = 1.0
    weapon_skill_lp_min: int = 100
    weapon_skill_lp_max: int = 1600
    weapon_skills_min: int = 0
    weapon_skills_max: int = 3


class SearchOptions(BaseModel):
    pools_min: int = 1
    pools_max: int = 5
    items_min: int = 1
    items_max: int = 5


class MainOptions(BaseModel):
    artes: Optional[ArtesOptions] = ArtesOptions()
    skills: SkillsOptions = SkillsOptions()
    items: ItemsOptions = ItemsOptions()
    search: SearchOptions = SearchOptions()