import os

from vesperando_core import ToVPatcher


if __name__ == "__main__":
    patch: str = ""
    for f in os.listdir(os.path.join(".", "patches")):
        if f.endswith(".tovdepatch"):
            patch = os.path.join(".", "patches", f)
            break

    procedure = ToVPatcher.GamePatchProcedure(patch, 12)
    procedure.begin()