from dotenv import load_dotenv
import shutil
import os

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
if os.getenv("ENV", "") == "DEBUG": os.environ["EXEC_DIR"] = os.path.dirname(os.path.abspath(__file__))

from vesperando_core import procedure, conf


if __name__ == "__main__":
    base_dir = os.getenv('EXEC_DIR', os.getcwd())
    shutil.rmtree(os.path.join(base_dir, "build"), ignore_errors=True)
    shutil.rmtree(os.path.join(base_dir, os.getenv('EXEC_DIR', os.getcwd()), "output"), ignore_errors=True)

    patch: str = ""
    for f in os.listdir(os.path.join(base_dir, "patches")):
        if conf.settings.Extensions.is_valid_patch(f):
            patch = os.path.join(base_dir, "patches", f)
            break

    assert os.path.isfile(patch), "No valid patch found to test!"

    print("[INTEGRATION TEST]")
    procedure = procedure.GamePatchProcedure(patch, 12)
    procedure.restore()
    procedure.patch()
    print("[TEST] Done.")