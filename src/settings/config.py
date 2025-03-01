import logging

from colorama import Fore, Style
from decouple import config
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SECRET_KEY: str = config("SECRET_KEY", "mock-secret-key")

    AWS_ACCESS_KEY_ID: str = config("AWS_ACCESS_KEY_ID", "mock-access-key")
    AWS_SECRET_ACCESS_KEY: str = config("AWS_SECRET_ACCESS_KEY", "mock-secret-key")
    AWS_S3_BUCKET_NAME: str = config("AWS_S3_BUCKET_NAME", "mock-bucket")
    AWS_S3_REGION: str = config("AWS_S3_REGION", "eu-north-1")


class ColorLogFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: Fore.BLUE,
        logging.INFO: Fore.GREEN,
        logging.WARNING: Fore.LIGHTYELLOW_EX,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.RED + Style.BRIGHT,
    }

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelno, "")
        message = super().format(record)
        return f"{color}{message}{Style.RESET_ALL}"


console_handler = logging.StreamHandler()
console_handler.setFormatter(ColorLogFormatter("%(levelname)s: %(message)s"))
logging.basicConfig(level=logging.DEBUG, handlers=[console_handler])
logger = logging.getLogger(__name__)

settings = Settings()
