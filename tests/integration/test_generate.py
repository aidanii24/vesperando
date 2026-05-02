from dotenv import load_dotenv
import traceback
import sys
import os

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
if os.getenv("ENV", "") == "DEBUG": os.environ["EXEC_DIR"] = os.path.dirname(os.path.abspath(__file__))

from click.testing import CliRunner
from vesperando_cli.__main__ import cli

def test_generate():
    print("[TEST] Testing 'generate' command")

    print("[TEST] Cleaning 'patches'")
    bdr: str = os.path.dirname(os.path.abspath(__file__))
    for filename in os.listdir(os.path.join(bdr, "patches")):
        try: os.remove(os.path.join(bdr, "patches", filename))
        except Exception as e: print(f"[TEST] Failed to remove {filename}")

    print("[TEST] Running Application")
    args: list[str] = ["generate", *sys.argv[1:], "-s"]
    print(f"> vesperando_cli", *args)

    runner = CliRunner()
    result = runner.invoke(cli, args)

    print("[TEST] OUTPUT:")
    print(result.output)
    if result.exception:
        traceback.print_exception(*result.exc_info)

    assert result.exit_code == 0

    print("[TEST] Done.")

test_generate()