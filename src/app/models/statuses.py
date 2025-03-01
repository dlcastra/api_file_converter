from enum import Enum


class Status(str, Enum):
    SUCCESS = "success"
    PROCESSING = "processing"
    WAITING = "waiting"
    ERROR = "error"
