import pydantic
import yaml
import os

from vesperando_core.res.models.options import MainOptions
from vesperando_core.conf.settings import Paths


class Options:
    @staticmethod
    def generate():
        options = MainOptions().model_dump()

        if not (os.path.isdir(Paths.OPTIONS_DIR)):
            os.makedirs(os.path.dirname(Paths.OPTIONS_DIR))

        with open(os.path.join(Paths.OPTIONS_DIR, "options.yaml"), "w") as f:
            yaml.safe_dump(options, f)
            f.close()

        return options

    @staticmethod
    def get(options_path: str = os.path.join(Paths.OPTIONS_DIR, "options.yaml")):
        options: dict = {}
        if not os.path.isfile(options_path):
            options = Options.generate()
        else:
            try:
                with open(options_path, "r") as f:
                    options = yaml.safe_load(f)
                    f.close()

                MainOptions.model_validate(options)
            except yaml.YAMLError as exc:
                raise OptionsError("[ERROR]\tThere was a problem loading the options file.") from exc
            except pydantic.ValidationError as exc:
                raise OptionsError(f"[ERROR]\tThe options file is invalid.\n{exc}") from exc

        return options


class OptionsError(Exception):
    pass