from pydantic import BaseModel, model_validator, field_validator
from typing import Optional, Self

from vesperando_core.res.models.annotations import (MaxTenThousand, MaxThousand, MaxHundred, MaxTen, Mod, TP,
                                                    WeaponSkillCount)


class ArtesOptions(BaseModel):
    tp_mod: Mod = 1.0
    tp_min: TP= 1
    tp_max: TP = 100
    learn_arte_usage_mod: Mod = 1.0
    learn_arte_usage_min: MaxThousand = 5
    learn_arte_usage_max: MaxThousand = 200
    enable_non_altered_evolve: bool = False
    keep_azure_edge_fs: bool = True

    @model_validator(mode='after')
    def check_tp_range(self) -> Self:
        if self.tp_min > self.tp_max:
            raise ValueError("\"tp_min\" must be less than \"tp_max\".")

        return self

    @model_validator(mode='after')
    def check_learn_arte_usage_range(self) -> Self:
        if self.learn_arte_usage_min > self.learn_arte_usage_max:
            raise ValueError("\"learn_arte_usage_min\" must be less than \"learn_arte_usage_max\".")

        return self


class SkillsOptions(BaseModel):
    sp_mod: Mod = 1.0
    sp_min: MaxHundred = 1
    sp_max: MaxHundred = 30

    @model_validator(mode='after')
    def check_sp_range(self) -> Self:
        if self.sp_min > self.sp_max:
            raise ValueError("\"sp_min\" must be less than \"sp_max\".")

        return self


class ItemsOptions(BaseModel):
    price_mod: Mod = 1.0
    weapon_skills_min: WeaponSkillCount = 0
    weapon_skills_max: WeaponSkillCount = 3
    weapon_skill_lp_mod: Mod = 1.0
    weapon_skill_lp_min: MaxTenThousand = 100
    weapon_skill_lp_max: MaxTenThousand = 1600

    @model_validator(mode='after')
    def check_skill_count_range(self) -> Self:
        if self.weapon_skills_min > self.weapon_skills_max:
            raise ValueError("\"weapon_skills_min\" must be less than \"weapon_skills_max\".")

        return self

    @model_validator(mode='after')
    def check_skills_lp_range(self) -> Self:
        if self.weapon_skill_lp_min > self.weapon_skill_lp_max:
            raise ValueError("\"weapon_skill_lp_min\" must be less than \"weapon_skill_lp_max\".")

        return self


class SearchOptions(BaseModel):
    uses_min: MaxTen = 1
    uses_max: MaxTen = 5
    pools_min: MaxTen = 1
    pools_max: MaxTen = 5
    items_min: MaxTen = 1
    items_max: MaxTen = 5

    @model_validator(mode='after')
    def check_uses_range(self) -> Self:
        if self.uses_min > self.uses_max:
            raise ValueError("\"uses_min\" must be less than \"uses_max\".")

        return self

    @model_validator(mode='after')
    def check_pools_range(self) -> Self:
        if self.pools_min > self.pools_max:
            raise ValueError("\"pools_min\" must be less than \"pools_max\".")

        return self

    @model_validator(mode='after')
    def check_items_range(self) -> Self:
        if self.uses_min > self.uses_max:
            raise ValueError("\"items_min\" must be less than \"items_max\".")

        return self


class MainOptions(BaseModel):
    artes: Optional[ArtesOptions] = None
    skills: Optional[SkillsOptions] = None
    items: Optional[ItemsOptions] = None
    shops: Optional[dict] = None
    chests: Optional[dict] = None
    search: Optional[SearchOptions] = None

    # Handle Key-only entries and partial entries
    # Targets (Root Entries) that are not present in the options yaml are not processed here,
    # but after validation will be populated with the specified default of "None"
    # After validation, model_dump with exclude_none will return only target entries present
    # in the original options yaml
    @field_validator("*", mode='before')
    @classmethod
    def check_targets(cls, value):
        # For key-only entries, return an empty dictionary, which during validation will be
        # populated with the default values of that model
        if value is None:
            return dict()

        # Partial target entries will be given the default values
        return value


class MainOptionsDefault(BaseModel):
    artes: Optional[ArtesOptions] = ArtesOptions()
    skills: Optional[SkillsOptions] = SkillsOptions()
    items: Optional[ItemsOptions] = ItemsOptions()
    shops: Optional[dict] = None
    chests: Optional[dict] = None
    search: Optional[SearchOptions] = SearchOptions()