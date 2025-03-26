from enum import Enum


class AWSSuccessResponse(str, Enum):
    FILE_DOWNLOADED = "File has been downloaded"
    FILE_UPLOADED = "File has been uploaded"


class AWSErrorResponse(str, Enum):
    ERROR_DOWNLOAD_FILE = "File download failed"
    ERROR_UPLOAD_FILE = "File upload failed"
    FILE_MISSED_OR_EMPTY = "Download failed: file is missing or empty"
