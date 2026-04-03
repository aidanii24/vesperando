import pydantic
import yaml
import os

from vesperando_core.res.models.settings import MainSettings
from vesperando_core.conf.settings import Paths


class Settings:
    @staticmethod
    def generate():
        config: dict = MainSettings().model_dump()

        if not (os.path.isdir(os.path.dirname(Paths.CONFIG))):
            os.makedirs(os.path.dirname(Paths.CONFIG))

        with open(Paths.CONFIG, "w") as f:
            yaml.safe_dump(config, f)
            f.close()

        try:
            MainSettings.model_validate(config)
        except pydantic.ValidationError as e:
            raise ConfigError(f"Failed to automatically detect best configuration.\n{e}") from e

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
            except yaml.YAMLError as e:
                raise ConfigError("There was a problem loading the configuration file.") from e
            except pydantic.ValidationError as e:
                raise ConfigError(f"The configuration file is invalid.\n{e}") from e

        return config


class ConfigError(Exception):
    pass