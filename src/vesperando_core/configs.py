import platform
import yaml
import os

from vesperando_core.conf.settings import Paths


def generate_config():
    base_path: str = Paths.GAME
    system: str = platform.system()
    if system == "Linux":
        base_path = os.path.join(os.path.expanduser("~"), ".steam", Paths.GAME)
    elif system == "Windows":
        base_path = os.path.join("C:\\Program Files (x86)", Paths.GAME)

    config: dict = {
        'paths': {
            'game': base_path,
        }
    }

    if not (os.path.isdir(os.path.dirname(Paths.CONFIG))):
        os.makedirs(os.path.dirname(Paths.CONFIG))

    with open(Paths.CONFIG, "w") as f:
        yaml.safe_dump(config, f)
        f.close()

    return config

def get_config():
    config: dict = {}
    if not os.path.isfile(Paths.CONFIG):
        config = generate_config()
    else:
        try:
            with open(Paths.CONFIG, "r") as f:
                config = yaml.safe_load(f)
                f.close()
        except yaml.YAMLError as exc:
            raise ConfigError("[ERROR]\tCould not load config file") from exc

    return config

class ConfigError(Exception):
    pass