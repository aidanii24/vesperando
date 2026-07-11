from pydantic import BaseModel, DirectoryPath
import vdf
import platform
import os

from vesperando_core.conf.settings import Paths

def resolve_game_path_from_keyvalues(kv: str) -> str:
    appid: str = "738540"

    md: vdf = vdf.load(open(kv))
    for k, v in md.get('libraryfolders', {}).items():
        if appid in v.get('apps', {}):
            return os.path.join(str(v['path']), Paths.GAME_DIR)

    return Paths.GAME_DIR

def generate_default_game_path() -> DirectoryPath:
    game_path: str = Paths.GAME_DIR
    system: str = platform.system()
    if system == "Linux":
        home_path: str = os.path.expanduser("~")
        if os.path.isdir(os.path.join(home_path, ".steam", "steam")):
            steam_path = os.path.join(home_path, ".steam", "steam")
        else:
            steam_path = os.path.join(home_path, ".local", "share", "Steam")

        return resolve_game_path_from_keyvalues(os.path.join(steam_path, Paths.STEAM_LIBFOL))
    elif system == "Windows":
        import winreg

        key_path: str = r"HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\Valve\Steam"
        sub_key: int = winreg.HKEY_CURRENT_USER
        h_key = winreg.OpenKey(sub_key, key_path, 0, winreg.KEY_QUERY_VALUE)
        steam_path, vtype = winreg.QueryValueEx(h_key, "InstallPath")
        if type(steam_path) == str:
            return resolve_game_path_from_keyvalues(os.path.join(str(steam_path), Paths.STEAM_LIBFOL))

    return game_path

class PathsSettings(BaseModel):
    game: DirectoryPath = generate_default_game_path()


class MainSettings(BaseModel):
    paths: PathsSettings = PathsSettings()