from pydantic import BaseModel, DirectoryPath
import platform
import os

from vesperando_core.conf.settings import Paths


def generateDefaultGamePath() -> DirectoryPath:
    game_path: str = Paths.GAME_DIR
    system: str = platform.system()
    if system == "Linux":
        game_path = os.path.join(os.path.expanduser("~"), ".steam", Paths.GAME_DIR)
    elif system == "Windows":
        game_path = os.path.join("C:\\Program Files (x86)", Paths.GAME_DIR)

    return game_path

class PathsSettings(BaseModel):
    game: DirectoryPath = generateDefaultGamePath()


class MainSettings(BaseModel):
    paths: PathsSettings = PathsSettings()