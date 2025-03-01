from src.app.models.statuses import Status
from src.app.services.converter import FileConverterService
from src.app.services.scraper import FileScraperService
from src.app.typing.converter import ConverterHandler
from src.app.typing.scraper import ScraperHandler

from src.settings.config import settings


async def convert_file(s3_key: str, old_format: str, format_to: str) -> ConverterHandler:
    converter = FileConverterService()
    bucket = settings.AWS_S3_BUCKET_NAME
    region = settings.AWS_S3_REGION

    try:
        converted_s3_key = s3_key.replace(f".{old_format}", f".{format_to}")
        details, is_processed = await converter.file_processing(
            s3_key=s3_key, converted_key=converted_s3_key, format_to=format_to, bucket=bucket
        )
        if not is_processed:
            return Status.ERROR, details

        file_url = f"https://{bucket}.s3.{region}.amazonaws.com/{converted_s3_key}"
        return Status.SUCCESS, {"file_url": file_url, "new_s3_key": converted_s3_key}
    except Exception as e:
        return Status.ERROR, str(e)


async def file_scraper(s3_key: str, keywords: list[str]) -> ScraperHandler:
    scraper = FileScraperService()
    bucket = settings.AWS_S3_BUCKET_NAME

    try:
        details, is_processed = await scraper.file_processing(s3_key, bucket, keywords)
        if not is_processed:
            return Status.ERROR, details

        return Status.SUCCESS, {"count": len(details), "sentences": details}
    except Exception as e:
        return Status.ERROR, str(e)
