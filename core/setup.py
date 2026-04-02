from setuptools import setup
from setuptools.command.install import install
from setuptools.command.build_py import build_py
from setuptools.command.build import build
import subprocess
import platform
import shutil
import os

scd: str = os.getenv('scd', os.path.dirname(os.path.abspath(__file__)))
ltp: str = os.path.join(scd, 'src', 'lib')
mwd: str = os.path.join(scd, 'src', 'comptoe')
lbd: str = os.path.join(scd, 'src', 'vesperando_core', 'lib')
ext: str = ".so"

if platform.system() == "Windows":
    ext = ".dll"
elif platform.system() == "Darwin":
    ext = ".dylib"

class BuildPySharedLibrary(build_py):
    @classmethod
    def build_library(cls):
        os.makedirs(ltp)

        cls._clean_library()
        cls._compile_library()

    @staticmethod
    def _compile_library():
        if platform.system() == "Windows":
            subprocess.call(["gcc", "-shared", "-o", "_complib.dll", "complib.c", "-Wl,--export-all-symbols"],
                            cwd=mwd)
        else:
            subprocess.call(["gcc", "-fPIC", "-shared", "-o", f"_complib{ext}", "complib.c"], cwd=mwd)

    @staticmethod
    def _clean_library():
        extensions: tuple = ("_*.so", "_*.dll", "_*.dylib")
        for file in os.listdir(mwd):
            if file.endswith(extensions):
                os.remove(os.path.join(lbd, file))

    def run(self):
        self.build_library()
        shutil.move(os.path.join(mwd, f"_complib{ext}"), os.path.join(ltp, f"_complib{ext}"))
        super().run()


class InstallSharedLibrary(install):
    def run(self):
        shutil.copytree(ltp, lbd, dirs_exist_ok=True)
        super().run()


setup(
    cmdclass={
        'build_py': BuildPySharedLibrary,
        'install': InstallSharedLibrary,
    }
)