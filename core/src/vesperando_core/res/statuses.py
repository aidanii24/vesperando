from enum import Enum

class STATUS(Enum):
    SUCCESS = "000"
    ERROR = "001"
    WARNING = "003"
    PATCH_ALREADY_GENERATED = "P010"
    PATCH_ALREADY_APPLIED = "P011"