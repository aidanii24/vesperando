import shutil
import os

from vesperando_core import randomizer


if __name__ == "__main__":
    shutil.rmtree(os.path.join(".", "patches"), ignore_errors=True)

    template = randomizer.BasicRandomizerProcedure([])
    template.generate([], True)