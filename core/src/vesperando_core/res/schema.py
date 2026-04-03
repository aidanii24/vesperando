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
