import os

from lib.packing import fps4


target = os.path.join("..", "builds", "btl", "BTL_PACK.DAT")
outdir = os.path.join("..", "builds", "TEST", "BTL_PACK")
manifest_dir = os.path.join("..", "builds", "TEST", ".manifest", "BTL_PACK.json")

assert os.path.exists(target)

fps4.extract(target, outdir, manifest_dir)