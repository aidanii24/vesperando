import shutil
import os

from vesperando_core import procedure


if __name__ == "__main__":
    shutil.rmtree(os.path.join(".", "build"), ignore_errors=True)
    shutil.rmtree(os.path.join(".", "output"), ignore_errors=True)

    patch: str = ""
    for f in os.listdir(os.path.join(".", "patches")):
        if f.endswith(".tovdepatch"):
            patch = os.path.join(".", "patches", f)
            break

    procedure = ToVPatcher.GamePatchProcedure(patch, 12)
    procedure.begin()