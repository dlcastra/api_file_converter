from typing import Tuple, Dict

from src.app.aws.utils import download_file_as_bytes, upload_bytes_to_s3
from src.app.models.statuses import Status
from src.app.services import get_file_scraper_service, get_file_converter_service
from src.app.typing.scraper import ScraperHandler
from src.settings.config import settings, logger
from src.app.constants import CONTENT_TYPES


async def convert_file(s3_key: str, old_format: str, format_to: str) -> Tuple[str, Dict]:
    """
    Function to convert the file as bytes from S3 bucket from one format to another.
    **Returns tuple with the str and the dict if the process was successful,
    otherwise returns tuple with the str and the str.**

    :param s3_key: name of the file in the S3 bucket - **str**.
    :param old_format: format of the file to convert - **str**.
    :param format_to: format to convert the file - **str**.
    :return: tuple with the status and the data. **status - str, data - str or dict**.
    """

    converter = get_file_converter_service()
    bucket = settings.AWS_S3_BUCKET_NAME
    region = settings.AWS_S3_REGION

    try:
        logger.info("File conversion started")
        converted_s3_key = s3_key.replace(f".{old_format}", f".{format_to}")

        download_result, is_downloaded = await download_file_as_bytes(bucket, s3_key)
        if not is_downloaded:
            logger.error(f"File download failed. Details: {download_result}")
            return Status.ERROR, {"message": download_result}

        conv_result, is_processed = await converter.file_processing(old_format, format_to, download_result)
        if not is_processed:
            logger.error(f"File conversion failed.")
            return Status.ERROR, {"message": conv_result}

        message, is_uploaded = await upload_bytes_to_s3(bucket, converted_s3_key, conv_result, CONTENT_TYPES[format_to])
        if not is_uploaded:
            logger.error(f"File upload failed. Details: {message}")
            return Status.ERROR, {"message": message}

        file_url = f"https://{bucket}.s3.{region}.amazonaws.com/{converted_s3_key}"
        logger.info("File conversion successful")
        return Status.SUCCESS, {"file_url": file_url, "new_s3_key": converted_s3_key}
    except Exception as e:
        logger.error(f"An internal error occurred: {str(e)}")
        return Status.ERROR, {"message": str(e)}


async def file_scraper(s3_key: str, keywords: list[str]) -> ScraperHandler:
    """
    Function to scrape the file from the S3 bucket.
    It searches the concrete sentence or a few sentences in the file be the list of keywords.
    **Returns tuple with the str and the dict if the process was successful,
    otherwise returns tuple with the str and the str.**

    :param s3_key: name of the file in the S3 bucket - **str**.
    :param keywords: list of keywords to search in the file - **list[str]***.
    :return: tuple with the status and the data. ***status - str, data - str or dict**.
    """

    scraper = get_file_scraper_service()
    bucket = settings.AWS_S3_BUCKET_NAME

    try:
        logger.error("File parsing has started")
        details, is_processed = await scraper.file_processing(s3_key, bucket, keywords)
        if not is_processed:
            logger.error(f"File parsing failed. Details: {details}")
            return Status.ERROR, {"message": details}

        logger.info("File parsing successful")
        return Status.SUCCESS, {"count": len(details), "sentences": details}
    except Exception as e:
        logger.error(f"An internal error occurred: {str(e)}")
        return Status.ERROR, {"message": str(e)}
