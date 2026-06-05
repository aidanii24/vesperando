# Options
Vesperando's Basic Randomizer cam be customized to suit a desired experience. 
During generation, an options file can be provided to tell the generator to fine tune the randomization to a certain way, 
or to place some restrictions on randomization. It can also be used to remove some randomizations completely.

An option file can be created using the `make-config` command.
```commandline
vesperando_cli make-config options
```

The options file can be provided to the generator as follows.
```commandline
vesperando_cli generate -o path/to/options.yaml
```

The option file can also be manually created. Regardless, for editing the options file, it will be useful to know what the options are and understand what they do.

## Artes
| Property                    | Description                                                                                                | Value               | Default |
|-----------------------------|------------------------------------------------------------------------------------------------------------|---------------------|---------|
| `enable_non_altered_evolve` | Allow randomization of evolve conditions for non-altered artes (**Experimental**)                          | [`true`, `false`]   | `false` |
| `learn_arte_usage_max`      | The maximum Arte Usage requirement that can be randomized into required for learning an Arte               | `int` (0, 1000)     | 200     |
| `learn_arte_usage_min`      | The minimum Arte Usage requirement that can be randomized into required for learning an Arte               | `int` (0, 1000)     | 5       |
| `learn_arte_usage_mod`      | Modifier to apply for the Arte Usage requirement that can be randomized into required for learning an Arte | `float` (0, 10.0]   | 1.0     |
| `tp_max`                    | The maximum TP Cost that an Arte can be randomized to have                                                 | `int` (0, 200]      | 100     |
| `tp_min`                    | The minimum TP Cost that an Arte can be randomized to have                                                 | `int` (0, 200]      | 1       |
| `tp_mod`                    | Modifier to apply to the TP Cost that an Arte can be randomized to have                                    | `float` (0, 10.0]   | 1.0     |

## Skills
| Property | Description                                                                             | Value             | Default |
|----------|-----------------------------------------------------------------------------------------|-------------------|---------|
| `lp_max` | The maximum LP Cost that a Skill can be randomized to require for learning              | `int` (0, 10000)  | 1600    |
| `lp_min` | The minimum LP Cost that a Skill can be randomized to require for learning              | `int` (0, 10000)  | 100     |
| `lp_mod` | Modifier to apply to the LP Cost that a Skill can be randomized to require for learning | `float` (0, 10.0] | 1.0     |
| `sp_max` | The maximum SP Cost that a Skill can be randomized cost for equipping                   | `int` (0, 100)    | 30      |
| `sp_min` | The minimum SP Cost that a Skill can be randomized cost for equipping                   | `int` (0, 100)    | 1       |
| `sp_mod` | Modifier to apply to the SP Cost that a Skill can be randomized cost for equipping      | `float` (0, 10.0] | 1.0     |

## Items
| Property                    | Description                                                                                                     | Value             | Default |
|-----------------------------|-----------------------------------------------------------------------------------------------------------------|-------------------|---------|
| `price_mod`                 | Modifier to apply for the cost of Items for purchase from Shops                                                 | `float` (0, 10.0] | 1.0     |
| `weapon_skill_lp_ratio_max` | The maximum LP Percentage to modify from a Skill's base LP requirement for learning with this item              | `int` (0, 100]    | 100     |
| `weapon_skill_lp_ratio_min` | The minimum LP Percentage to modify from a Skill's base LP requirement for learning with this item              | `int` (0, 100]    | 10      |
| `weapon_skill_lp_ratio_mod` | Modifier to apply to the LP Percentage to modify from a Skill's base LP requirement for learning with this item | `float` (0, 10.0] | 1.0     |
| `weapon_skills_max`         | The maximum amount of skills a weapon/sub-weapon can be randomized to have                                      | `int` (0, 3]      | 3       |
| `weapon_skills_min`         | The minimum amount of skills a weapon/sub-weapon can be randomized to have                                      | `int` (0, 3]      | 1       |

## Shops
_Shops have no options aside from whether it should be randomized at all_

## Chests
_Chests have no options aside from whether it should be randomized at all_

## Search (Search Points)
| Property    | Description                                                                                                | Value         | Default |
|-------------|------------------------------------------------------------------------------------------------------------|---------------|---------|
| `items_max` | The maximum amount of items a Search Point pool can be randomized to have                                  | `int` (0, 10) | 5       |
| `items_min` | The maximum amount of items a Search Point pool can be randomized to have                                  | `int` (0, 10) | 1       |
| `pools_max` | The maximum amount of pools a Search Point pool can be randomized to have                                  | `int` (0, 10) | 5       |
| `items_min` | The maximum amount of pools a Search Point pool can be randomized to have                                  | `int` (0, 10) | 1       |
| `uses_max`  | The maximum amount of time a Search Point can be interacted with before it becomes exhausted and disappear | `int` (0, 10) | 5       |
| `uses_min`  | The minimum amount of time a Search Point can be interacted with before it becomes exhausted and disappear | `int` (0, 10) | 1       |

## Example
```yaml
# The default YAML
## These are the options used even if they are not specified, except for the root option keys (artes, skills, items, etc.),
## where the absence of their keys will indicate to the generator that they should not be randomized
artes:
  enable_non_altered_evolve: false
  learn_arte_usage_max: 200
  learn_arte_usage_min: 5
  learn_arte_usage_mod: 1.0
  tp_max: 100
  tp_min: 1
  tp_mod: 1.0
chests: null
items:
  price_mod: 1.0
  weapon_skill_lp_ratio_max: 100
  weapon_skill_lp_ratio_min: 10
  weapon_skill_lp_ratio_mod: 1.0
  weapon_skills_max: 3
  weapon_skills_min: 0
search:
  items_max: 5
  items_min: 1
  pools_max: 5
  pools_min: 1
  uses_max: 5
  uses_min: 1
shops: null
skills:
  lp_max: 1600
  lp_min: 100
  lp_mod: 1.0
  sp_max: 30
  sp_min: 1
  sp_mod: 1.0
```