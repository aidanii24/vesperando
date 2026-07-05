import json

from vesperando_core import utils
from vesperando_core.res import enums
from vesperando_core.conf.settings import Paths


_artes_data: dict = {}
_artes_by_char: dict = {}

_skills_data: dict = {}
_skills_by_char: dict = {}

_items_data: dict = {}
_items_by_category = {}
_item_to_category = {}
_common_items = tuple()

_events_data: dict = {}

_metadata: dict = {}

def get_artes_data() -> dict:
    if not _artes_data: _load_artes_data()
    return _artes_data

def get_artes_by_char() -> dict:
    if not _artes_by_char:
        for arte in get_artes_data().values():
            # We get all the valid artes for randomization here as well, conforming to these conditions:
            ##  a. Must be only used by a playable character
            ##  b. Must not be a special arte type (This filters out Fatal Strikes, Overlimits and Skill)
            ##  c. Must have a TP Cost (This filters out variations of artes if any)
            only_used_by_playable: bool = any(0 < chara < 10 for chara in arte['character_ids'])
            if not only_used_by_playable: continue
            for char in arte['character_ids']:
                # Check if arte is not special (Fatal Strike, Overlimit or Skill)
                if enums.ArteTypes.is_normal(arte['arte_type']): continue
                # Check if arte has TP Cost
                if arte['tp_cost'] <= 0: continue

                _artes_by_char.setdefault(char, []).append(arte['id'])

    return _artes_by_char

def get_artes_names() -> dict:
    if not _metadata.get('artes'):
        _load_metadata()
    return _metadata.get('artes')

def get_skills_data() -> dict:
    if not _skills_data: _load_skills_data()
    return _skills_data

def get_skills_by_char() -> dict:
    if not _skills_by_char:
        for sid, data in get_skills_data().items():
            character_usable = data.get('character_usable', 0)
            if not character_usable: continue

            for character in enums.Characters:
                if character.bitflag() & character_usable:
                    _skills_by_char.setdefault(character.value, []).append(sid)

    return _skills_by_char

def get_skills_names() -> dict:
    if not _metadata.get('skills'):
        _load_metadata()
    return _metadata.get('skills')

def get_items_data() -> dict:
    if not _items_data: _load_items_data()
    return _items_data

def get_items_by_category() -> dict:
    if not _items_by_category:
        for iid, item in get_items_data().items():
            _items_by_category.setdefault(item['category'], []).append(item['id'])

    return _items_by_category

def get_item_to_category() -> dict:
    if not _item_to_category:
        for iid, item in get_items_data().items():
            _item_to_category[item['id']] = item['category']

    return _item_to_category

def get_common_items() -> tuple:
    global _common_items
    if not _common_items:
        _common_items = tuple([item for category, items in get_items_by_category().items()
                               for item in items
                               if enums.ItemCategory.is_common(category)])

    return _common_items

def get_events_data() -> dict:
    if not _events_data: _load_events_data()
    return _events_data

def _load_artes_data():
    with open(Paths.STATIC_PATH.joinpath("artes.json")) as f:
        artes_data_table = json.load(f, object_hook=utils.keys_to_int)

        for arte in artes_data_table['entries']:
            _artes_data[int(arte['id'])] = arte

def _load_skills_data():
    with open(Paths.STATIC_PATH.joinpath("skills.json")) as f:
        skills_data_table = json.load(f, object_hook=utils.keys_to_int)

    global _skills_data
    _skills_data = {int(sid): skill for sid, skill in skills_data_table['entries'].items()}

def _load_items_data():
    with open(Paths.STATIC_PATH.joinpath("items.json")) as f:
        global _items_data
        _items_data = json.load(f, object_hook=utils.keys_to_int)

def _load_events_data():
    global _events_data
    with open(Paths.STATIC_PATH.joinpath("events.json")) as f:
        _events_data = json.load(f, object_hook=utils.keys_to_int)

def _load_metadata():
    global _metadata
    with open(Paths.STATIC_PATH.joinpath("metadata.json")) as f:
        _metadata = json.load(f, object_hook=utils.keys_to_int)