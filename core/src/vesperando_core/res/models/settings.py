from pydantic import BaseModel, DirectoryPath


class PathsSettings(BaseModel):
    game: DirectoryPath


class MainSettings(BaseModel):
    paths: PathsSettings