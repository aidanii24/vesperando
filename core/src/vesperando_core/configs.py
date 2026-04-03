import pydantic
import platform
import yaml
import os

from vesperando_core.res.models.settings import MainSettings
from vesperando_core.conf.settings import Paths


class Settings:
    @staticmethod
    def generate():
        base_path: str = Paths.GAME_DIR
        system: str = platform.system()
        if system == "Linux":
            base_path = os.path.join(os.path.expanduser("~"), ".steam", Paths.GAME_DIR)
        elif system == "Windows":
            base_path = os.path.join("C:\\Program Files (x86)", Paths.GAME_DIR)

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

    @staticmethod
    def get():
        config: dict = {}
        if not os.path.isfile(Paths.CONFIG):
            config = Settings.generate()
        else:
            try:
                with open(Paths.CONFIG, "r") as f:
                    config = yaml.safe_load(f)
                    f.close()

                MainSettings.model_validate(config)
            except yaml.YAMLError as exc:
                raise ConfigError("[ERROR]\tThere was a loading the configuration file") from exc
            except pydantic.ValidationError as exc:
                raise ConfigError(f"[ERROR]\tThe configuration file is invalid.\n{exc}") from exc

        return config


class ConfigError(Exception):
    pass