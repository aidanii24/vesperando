# Vesperando
Utilities for randomizing and patching aspects of Tales of Vesperia: Definitive Edition.

These tools were created in part for an eventual integration of the game into the 
[Archipelago](https://github.com/ArchipelagoMW/Archipelago) Randomizer framework, but can work
standalone with the bundled Basic Randomizer.
# Features
- Artes Randomization
  - TP
  - Cast Time (Magic only)
  - Learn Conditions
  - Evolve Conditions (for existing Altered artes only)
- Skills Randomization
  - Category
  - SP Cost
  - LP Cost
- Items Randomization
  - Price
  - Skills
- Shops Randomization
- Chests Randomization
- Search Point Randomization

# Use
Vesperando is available a command line utility. It is recommended to use a terminal to use this application.

## Configuration
The application must be provided the path to the game directory to function properly.
When running the application for the first time, it will attempt to detect where this directory is by itself.
This will create the path `config/config.yaml`. If the detected game directory is incorrect, this file can be 
edited to provide the correct path.
```yaml
# config.yaml
paths:
  game: path/to/game_directory
```
Forward slashes can be used in Windows filesystems. If using backslashes, please escape them with 
another backslash (e.g. `path\\to\\game_directory`).

## Commands
### Generate
A basic randomization patch can be generated using the generate command.
This will output a patch file that uses the file extension `.vbrp`.
```commandline
vesperando_cli generate targets
```
_targets_ can be any of `artes`, `skills`, `items`, `shops`, `chests`, `search` which specifies which aspect of the 
game should be randomized.

| Option            | Description                                          |
|-------------------|------------------------------------------------------|
| `-n`, `--name`    | Name of the Patch                                    |
| `-s`, `--spoil`   | Generate a Spoiler Sheet after generation            |
| `--seed`          | Seed to use for generation                           |

### Patch
When a patch file is ready, it a patch output can then be generated.
```commandline
vesperando_cli patch patch_file
```
If no `patch_file` is provided, the application will list all available patch files 
it can find in the PATCHES directory, and will prompt which one to use for patching.

| Option                      | Description                                      |
|-----------------------------|--------------------------------------------------|
| `-t`, `--threads`           | Amount of CPU Threads to use during patching     |
| `-c`, `--clean`             | Clear the build directory after patching         |
| `-a`, `--apply-immediately` | After patching, apply it to the game immediately |

### Spoil
A Spoiler Sheet can be generated from a patch file separately.
```commandline
vesperando_cli spoil patch_file
```
If no `patch_file` is provided, the application will list all available patch files 
it can find in the PATCHES directory, and will prompt which one to use for spoiling.

### Apply
Pre-exisiting Patch Outputs can be applied without running the Patch command again.
```commandline
vesperando_cli apply patch_name
```
`patch_name` can be the name of the patch output, or the patch file the output is generated from.
If no `patch_name` is provided, the application will list all available patch outputs 
it can find in the OUTPUT directory, and will prompt which one to use for applying.

### Restore
Any applied patches to the game can be reverted by using the restore command.
```commandline
vesperando_cli restore
```
In the event the game is not restored properly, it is recommended to verify its game files using Steam.
This can be done by going to `Steam` > `Library` > `Tales of Vesperia: Definitive Edition` > `Propterties` > 
`Installed Files` > `Verify integrity of game files`. Otherwise, the game must be reinstalled.


# Development
## Setup
First and foremost, clone this repository.
```
git clone --recurse-submodules https://github.com/aidanii24/vesperando
```

As good practice, please use a virtual environment.
```commandline
python -m venv .venv
```
## External Dependencies
The following utilities must be available on your system to properly build and install vesperando packages.
- `gcc` (for comptoe)

## Python Packages
Environment setup is largely automated by using the `setup_dev.py` script inside the `scripts` directory.
Simply run this script.
```commandline
python scripts/setup_dev.py
```

For a manual setup, `pip` can directly be provided the main directories to install dependencies, 
as they each have their own pyproject.toml. It is recommended to install the main modules in an editable state 
during development,
```
pip install -e core/
pip install -e cli/
```

# Build
Vesperando uses PyInstaller to bundle and create an executable. A `.spec` file is already provided to easily generate a release.
```commandline
pyinstaller vesperando_cli.spec
```
Note that `vesperando_core` will have to build `complib`.
The binaries will be available in the generated `dist` directory upon a successful build.
# Roadmap
- [ ] Event Rewards Patching
- [ ] Text Patching (string_dic_<lang>.so)
- [ ] Adding new Icons for in-game use
- [ ] Implement GUI
- [ ] Archipelago Support

# Acknowledgements
Thanks to @Sora3100 for providing me with the knowledge and resources to make this possible.

Thank you to @AdmiralCurtiss for the development of HyoutaTools, and the team behind @lifebottle
and the original work of @talestra for developing comptoe. These tools are necessary for the patcher to access
various files of the game, and this would not have been possible without them.