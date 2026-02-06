from contextlib import contextmanager
import platform
import logging
import ctypes
import sys
import os

from conf.settings import Paths


# Build Command: gcc -fPIC -shared -o complib.so complib.c
libname = os.path.join(Paths.LIB_DIR, "libs", f"complib.{"dll" if platform.system() == "Windows" else "so"}")
c_lib = ctypes.CDLL(libname)

c_lib.EncodeFile.argtypes = ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int, ctypes.c_int
c_lib.DecodeFile.argtypes = ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int, ctypes.c_int


def decode(filename: str, output: str):
    if not os.path.isdir(os.path.dirname(output)):
        os.makedirs(os.path.dirname(output))

    stdout_redirected(lambda: c_lib.DecodeFile(filename.encode(), output.encode(), 0, 3))

def encode(filename: str, output: str):
    if not os.path.isdir(os.path.dirname(output)):
        os.makedirs(os.path.dirname(output))

    stdout_redirected(lambda: c_lib.EncodeFile(filename.encode(), output.encode(), 0, 3))

# Capture stdout
# https://stackoverflow.com/a/17954769
@contextmanager
def stdout_redirected(command, to=os.devnull):
    fd = sys.stdout.fileno()

    def _redirect_stdout(to):
        sys.stdout.close() # + implicit flush()
        os.dup2(to.fileno(), fd) # fd writes to 'to' file
        sys.stdout = os.fdopen(fd, 'w') # Python writes to fd

    with os.fdopen(os.dup(fd), 'w') as old_stdout:
        with open(to, 'w') as file:
            _redirect_stdout(to=file)
        try:
            command() # allow code to be run with the redirected stdout
        finally:
            _redirect_stdout(to=old_stdout)

logger = logging.getLogger("default")
logging.basicConfig(
    level=logging.DEBUG,
    format="%(message)s",
    handlers=[
        logging.FileHandler("test.log"),
        logging.StreamHandler()
    ]
)