from dotenv import load_dotenv
import traceback
import shutil
import sys
import os

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
if os.getenv("ENV", "") == "DEBUG": os.environ["EXEC_DIR"] = os.path.dirname(os.path.abspath(__file__))

from vesperando_core import conf

from click.testing import CliRunner
from vesperando_cli.__main__ import cli


if __name__ == "__main__":
    print("[TEST] Testing 'patch' command")

    print("[TEST] Cleaning 'build'")
    base_dir = os.getenv('EXEC_DIR', os.getcwd())
    shutil.rmtree(os.path.join(base_dir, "build"), ignore_errors=True)

    print("[TEST] Cleaning 'output'")
    shutil.rmtree(os.path.join(base_dir, os.getenv('EXEC_DIR', os.getcwd()), "output"), ignore_errors=True)

    print("[TEST] Fetching patch")
    patch: str = ""
    for f in os.listdir(os.path.join(base_dir, "patches")):
        if conf.settings.Extensions.is_valid_patch(f):
            patch = os.path.join(base_dir, "patches", f)
            break

    assert os.path.isfile(patch), "No valid patch found to test!"
    print("Patch:", patch)

    print("[TEST] Running Application")
    args: list[str] = ["patch", patch, *sys.argv[1:]]
    print(f"> vesperando_cli", *args)

    runner = CliRunner()
    result = runner.invoke(cli, args)

    print("[TEST] OUTPUT:")
    print(result.output)
    if result.exception:
        traceback.print_exception(*result.exc_info)

    assert result.exit_code == 0

    print("[TEST] Done.")