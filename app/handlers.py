import asyncio
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor

from app.models.statuses import Status
from app.utils import generate_s3_download_url, download_file, upload_file_to_s3
from settings.config import settings, logger

executor = ThreadPoolExecutor()


async def convert_file(s3_key: str, old_format: str, format_to: str):
    converted_s3_key = s3_key.replace(f".{old_format}", f".{format_to}")
    bucket = settings.AWS_S3_BUCKET_NAME

    generation_result, is_generated = generate_s3_download_url(s3_key)
    if not is_generated:
        return Status.ERROR.value, generation_result

    details, is_processed = await file_processing(s3_key, generation_result, converted_s3_key, format_to, bucket)
    if not is_processed:
        return Status.ERROR.value, details

    file_url = f"https://{bucket}.s3.{settings.AWS_S3_REGION}.amazonaws.com/{converted_s3_key}"
    return Status.SUCCESS.value, {"file_url": file_url, "new_s3_key": converted_s3_key}


async def file_processing(s3_key: str, download_url: str, converted_key: str, format_to, bucket: str):
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = f"{tmpdir}/{s3_key}"
        output_path = f"{tmpdir}/{converted_key}"

        message, is_downloaded = download_file(input_path, download_url)
        if not is_downloaded:
            return message, None

        message, is_converted = await convert_with_libreoffice(format_to, input_path)
        if not is_converted:
            return message, None

        message, is_uploaded = upload_file_to_s3(output_path, bucket, converted_key)
        if not is_uploaded:
            return message, None

        return Status.SUCCESS.value, True


async def convert_with_libreoffice(format_to, input_path):
    try:
        loop = asyncio.get_event_loop()
        end_successfully = await loop.run_in_executor(executor, libreoffice_subprocess, format_to, input_path)
        if not end_successfully:
            return "Error converting", None

        logger.info("File has been converted")
        logger.info("Started uploading file")
        return "File has been converted", True

    except Exception as e:
        logger.error(str(e))
        return str(e), None


def libreoffice_subprocess(format_to, output_path):
    try:
        logger.info("Starting libreoffice subprocess")
        subprocess.run(["unoconv", "-f", format_to, output_path], check=True)
        logger.info("Subprocess finished")
        return True

    except subprocess.CalledProcessError:
        logger.error("File conversion error")
        return None

    except Exception as e:
        logger.error(f"Error during file conversion: {e}")
        return None
