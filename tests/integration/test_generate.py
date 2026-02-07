import shutil
import os

from vesperando_core import ToVBasicRandomizer


if __name__ == "__main__":
    shutil.rmtree(os.path.join(".", "patches"), ignore_errors=True)

    template = ToVBasicRandomizer.InputTemplate([])
    template.generate([], True)