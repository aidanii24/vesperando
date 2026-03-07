from dotenv import load_dotenv
import shutil
import os

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

from vesperando_core import randomizer


if __name__ == "__main__":
    shutil.rmtree(os.path.join(".", "patches"), ignore_errors=True)

    template = randomizer.BasicRandomizerProcedure([])
    template.generate([], True)