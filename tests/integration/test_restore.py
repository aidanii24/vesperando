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

from vesperando_core import packer, configs


if __name__ == "__main__":
    print("[TEST] Testing 'restore' command")

    runner = CliRunner()
    result = runner.invoke(cli, ["restore"])

    print("[TEST] OUTPUT:")
    print(result.output)
    if result.exception:
        traceback.print_exception(*result.exc_info)

    assert result.exit_code == 0

    print("[TEST] Done.")