import shutil
import os

from vesperando_core import procedure, conf


if __name__ == "__main__":
    shutil.rmtree(os.path.join(".", "build"), ignore_errors=True)
    shutil.rmtree(os.path.join(".", "output"), ignore_errors=True)

    patch: str = ""
    for f in os.listdir(os.path.join(".", "patches")):
        if conf.settings.Extensions.is_valid_patch(f):
            patch = os.path.join(".", "patches", f)
            break

    assert patch, "No valid patch found to test!"

    procedure = procedure.GamePatchProcedure(patch, 12)
    procedure.patch()