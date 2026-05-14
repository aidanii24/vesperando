class Patch:
    schema: set = {}

    @classmethod
    def extract(cls, props: dict) -> dict:
        return {oid: {k: v for k, v in data.items() if k in cls.schema} for oid, data in props.items()}


class Artes(Patch):
    schema: set = {
        'id',
        'tp_cost',
        'cast_time',
        'fatal_strike_type',
        'fire_elemental',
        'water_elemental',
        'earth_elemental',
        'wind_elemental',
        'light_elemental',
        'dark_elemental',
        'target_type',
        'status_effect1',
        'status_effect1_parameter',
        'status_effect1_duration',
        'status_effect2',
        'status_effect2_parameter',
        'status_effect2_duration',
        'status_effect3',
        'status_effect3_parameter',
        'status_effect3_duration',
        'power',
        "vs_human_power",
        "vs_beast_power",
        "vs_bird_power",
        "vs_magic_power",
        "vs_plant_power",
        "vs_aquatic_power",
        "vs_insect_power",
        "vs_inorganic_power",
        "vs_scale_power",
        "vs_small_power",
        "vs_normal_power",
        "vs_big_power",
        "vs_large_power",
        "day_weather_power",
        "cloudy_weather_power",
        "fog_weather_power",
        "night_weather_power",
        "rain_weather_power",
        "snow_weather_power",
        "sandstorm_weather_power",
        "evening_weather_power",
        'learn_condition1',
        'learn_parameter1',
        'unknown3',
        'learn_condition2',
        'learn_parameter2',
        'unknown4',
        'learn_condition3',
        'learn_parameter3',
        'unknown5',
        'evolve_base',
        'evolve_condition1',
        'evolve_parameter1',
        'evolve_condition2',
        'evolve_parameter2',
        'evolve_condition3',
        'evolve_parameter3',
        'evolve_condition4',
        'evolve_parameter4',
    }


class Skills(Patch):
    schema: set = {
        'name_string_key',
        'id',
        'sp_cost',
        'lp_cost',
        'symbol',
        'symbol_weight',
        'parameter1',
        'parameter2',
        'parameter3',
        'is_equippable'
    }


class Items(Patch):
    schema: set = {
        'id',
        'buy_price',
        'skill1',
        'skill1_lp',
        'skill2',
        'skill2_lp',
        'skill3',
        'skill3_lp',
    }
