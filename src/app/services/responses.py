from enum import Enum


class ServiceErrorResponse(str, Enum):
    UNSUPPORTED_FILE_FORMAT = "Unsupported file format"
    INTERNAL_ERROR = "Internal error"


class ConverterErrorResponse(str, Enum):
    INTERNAL_ERROR = "An internal error while converting the file"
