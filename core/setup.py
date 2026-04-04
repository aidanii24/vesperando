from setuptools import setup
from setuptools.command.install import install
from setuptools.command.egg_info import egg_info
import subprocess
import platform
import shutil
import os

scd: str = os.getenv('scd', os.path.dirname(os.path.abspath(__file__)))
mwd: str = os.path.join(scd, 'src', 'comptoe')
lbd: str = os.path.join(scd, 'src', 'vesperando_core', 'lib')
ext: str = ".so"

if platform.system() == "Windows":
    ext = ".dll"
elif platform.system() == "Darwin":
    ext = ".dylib"

def _compile_library():
    if platform.system() == "Windows":
        subprocess.call(["gcc", "-shared", "-o", "_complib.dll", "complib.c", "-Wl,--export-all-symbols"],
                        cwd=mwd)
    else:
        subprocess.call(["gcc", "-fPIC", "-shared", "-o", f"_complib{ext}", "complib.c"], cwd=mwd)

def _clean_library():
    extensions: tuple = ("_*.so", "_*.dll", "_*.dylib")
    for file in os.listdir(mwd):
        if file.endswith(extensions):
            os.remove(os.path.join(lbd, file))

def _install_library():
    shutil.move(os.path.join(mwd, f"_complib{ext}"), os.path.join(lbd, f"_complib{ext}"))

class InstallSharedLibrary(install):
    def run(self):
        _clean_library()
        _compile_library()
        _install_library()
        super().run()


class EggInfoSharedLibrary(egg_info):
    def run(self):
        _clean_library()
        _compile_library()
        _install_library()
        super().run()


setup(
    cmdclass={
        'install': InstallSharedLibrary,
        'egg_info': EggInfoSharedLibrary,
    }
)