import platform
import ctypes
import os


# Build Command: gcc -fPIC -shared -o complib.so complib.c
lib_name: str = f"_complib.{"dll" if platform.system() == "Windows" else "so"}"
lib_path: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), lib_name)
c_lib = ctypes.CDLL(lib_path)

c_lib.EncodeFile.argtypes = ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int, ctypes.c_int
c_lib.DecodeFile.argtypes = ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int, ctypes.c_int


def decode(filename: str, output: str):
    if not os.path.isdir(os.path.dirname(output)):
        os.makedirs(os.path.dirname(output))

    c_lib.DecodeFile(filename.encode(), output.encode(), 0, 3)

def encode(filename: str, output: str):
    if not os.path.isdir(os.path.dirname(output)):
        os.makedirs(os.path.dirname(output))

    c_lib.EncodeFile(filename.encode(), output.encode(), 0, 3)