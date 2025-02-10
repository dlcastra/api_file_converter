from app.models.statuses import Status
from app.services.scraper import FileScraperService
from app.utils import generate_s3_download_url
from settings.config import settings
from app.services.converter import FileConverterService


async def convert_file(s3_key: str, old_format: str, format_to: str):
    converter = FileConverterService()

    converted_s3_key = s3_key.replace(f".{old_format}", f".{format_to}")
    bucket = settings.AWS_S3_BUCKET_NAME

    generation_result, is_generated = generate_s3_download_url(s3_key)
    if not is_generated:
        return Status.ERROR.value, generation_result

    details, is_processed = await converter.file_processing(
        s3_key, generation_result, converted_s3_key, format_to, bucket
    )
    if not is_processed:
        return Status.ERROR.value, details

    file_url = f"https://{bucket}.s3.{settings.AWS_S3_REGION}.amazonaws.com/{converted_s3_key}"
    return Status.SUCCESS.value, {"file_url": file_url, "new_s3_key": converted_s3_key}


async def file_scraper(s3_key: str, keywords: list[str]):
    scraper = FileScraperService()

    generation_result, is_generated = generate_s3_download_url(s3_key)
    if not is_generated:
        return Status.ERROR.value, generation_result

    details, is_processed = await scraper.file_processing(s3_key, generation_result, keywords)
    if not is_processed:
        return Status.ERROR.value, details

    return Status.SUCCESS.value, details
