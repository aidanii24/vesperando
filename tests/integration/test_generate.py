from dotenv import load_dotenv
import os

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

from vesperando_core import randomizer


if __name__ == "__main__":
    ptd = os.path.join(os.getenv('EXEC_DIR', os.getcwd()), "patches")
    for content in os.listdir(ptd):
        path = os.path.join(ptd, content)
        if os.path.isfile(path):
            os.remove(path)

    targets: list[str] = ['artes']

    print("[INTEGRATION TEST] Generating Patches...")
    print("\t-| Targets: ", targets if targets else "ALL")
    template = randomizer.BasicRandomizerProcedure(targets)
    template.generate(targets, True)
    print("[TEST] Done.")