from pydantic import BaseModel, model_validator, field_validator
from typing import Optional, Self

from vesperando_core.res.models.annotations import (MaxTenThousand, MaxThousand, MaxHundred, MaxTen, Mod, TP, LPRatio,
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
            raise ValueError(
                f"\"tp_min\" ({self.tp_min}) must not be greater than \"tp_max\" ({self.tp_max})."
            )

        return self

    @model_validator(mode='after')
    def check_learn_arte_usage_range(self) -> Self:
        if self.learn_arte_usage_min > self.learn_arte_usage_max:
            raise ValueError(
                f"\"learn_arte_usage_min\" ({self.learn_arte_usage_min}) "
                f"must not be greater than \"learn_arte_usage_max\". ({self.learn_arte_usage_max})"
            )

        return self


class SkillsOptions(BaseModel):
    sp_mod: Mod = 1.0
    sp_min: MaxHundred = 1
    sp_max: MaxHundred = 30
    lp_mod: Mod = 1.0
    lp_min: MaxTenThousand = 100
    lp_max: MaxTenThousand = 1600

    @model_validator(mode='after')
    def check_sp_range(self) -> Self:
        if self.sp_min > self.sp_max:
            raise ValueError(f"\"sp_min\" ({self.sp_min}) must not be greater than \"sp_max\" ({self.sp_max}).")

        return self

    @model_validator(mode='after')
    def check__lp_range(self) -> Self:
        if self.lp_min > self.lp_max:
            raise ValueError(f"\"lp_min\" ({self.lp_min}) must not be greater than \"lp_max\" ({self.lp_max}).")

        return self

class ItemsOptions(BaseModel):
    price_mod: Mod = 1.0
    weapon_skills_min: WeaponSkillCount = 0
    weapon_skills_max: WeaponSkillCount = 3
    weapon_skill_lp_ratio_mod: Mod = 1.0
    weapon_skill_lp_ratio_min: LPRatio = 10
    weapon_skill_lp_ratio_max: LPRatio = 100

    @model_validator(mode='after')
    def check_skill_count_range(self) -> Self:
        if self.weapon_skills_min > self.weapon_skills_max:
            raise ValueError(
                f"\"weapon_skills_min\" ({self.weapon_skills_min}) "
                f"must not be greater than \"weapon_skills_max\" ({self.weapon_skills_max})."
            )

        return self

    @model_validator(mode='after')
    def check_skill_lp_ratio_range(self) -> Self:
        if self.weapon_skills_min > self.weapon_skills_max:
            raise ValueError(
                f"\"weapon_skill_lp_ratio_min\" ({self.weapon_skill_lp_ratio_min}) "
                f"must not be greater than \"weapon_skill_lp_ratio_max\" ({self.weapon_skill_lp_ratio_max})."
            )

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
            raise ValueError(f"\"uses_min\" ({self.uses_min}) must not be greater than \"uses_max\" ({self.uses_max}).")

        return self

    @model_validator(mode='after')
    def check_pools_range(self) -> Self:
        if self.pools_min > self.pools_max:
            raise ValueError(
                f"\"pools_min\" ({self.pools_min}) must not be greater than \"pools_max\" ({self.pools_max})."
            )

        return self

    @model_validator(mode='after')
    def check_items_range(self) -> Self:
        if self.uses_min > self.uses_max:
            raise ValueError(
                f"\"items_min\" ({self.items_min}) must not be greater than \"items_max\" ({self.items_max})."
            )

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