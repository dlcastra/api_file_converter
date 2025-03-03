from src.app.models.statuses import Status
from src.app.services.converter import FileConverterService
from src.app.services.scraper import FileScraperService
from src.app.typing.converter import ConverterHandler
from src.app.typing.scraper import ScraperHandler
from src.settings.config import settings, logger


async def convert_file(s3_key: str, old_format: str, format_to: str) -> ConverterHandler:
    """
    Function to convert the file from S3 bucket from one format to another.
    **Returns tuple with the str and the dict if the process was successful,
    otherwise returns tuple with the str and the str.**

    :param s3_key: name of the file in the S3 bucket - **str**.
    :param old_format: format of the file to convert - **str**.
    :param format_to: format to convert the file - **str**.
    :return: tuple with the status and the data. **status - str, data - str or dict**.
    """
    converter = FileConverterService()
    bucket = settings.AWS_S3_BUCKET_NAME
    region = settings.AWS_S3_REGION

    try:
        logger.info("File conversion started")
        converted_s3_key = s3_key.replace(f".{old_format}", f".{format_to}")
        details, is_processed = await converter.file_processing(
            s3_key=s3_key, converted_key=converted_s3_key, format_to=format_to, bucket=bucket
        )
        if not is_processed:
            logger.error(f"File conversion failed. Details: {details}")
            return Status.ERROR, {"message": details}

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
    scraper = FileScraperService()
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
