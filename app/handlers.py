import asyncio
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor

from fastapi import HTTPException

from app.utils import generate_s3_download_url, download_file, upload_file_to_s3
from settings.config import settings, logger

executor = ThreadPoolExecutor()


async def convert_file(s3_key: str, old_format: str, format_to: str) -> dict:
    converted_s3_key = s3_key.replace(f".{old_format}", f".{format_to}")
    bucket = settings.AWS_S3_BUCKET_NAME

    logger.info("Generating download url")
    download_url = generate_s3_download_url(s3_key)
    logger.info("Download url has been generated")

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = f"{tmpdir}/{s3_key}"
        output_path = f"{tmpdir}/{converted_s3_key}"

        logger.info("Started downloading file")
        download_file(input_path, download_url)
        logger.info("File has been downloaded")
        logger.info("Started converting file")

        await convert_with_libreoffice(format_to, input_path, output_path, bucket, converted_s3_key)
        logger.info("Converted successfully")

        file_url = f"https://{bucket}.s3.{settings.AWS_S3_REGION}.amazonaws.com/{converted_s3_key}"
        return {"file_url": file_url, "new_s3_key": converted_s3_key}


async def convert_with_libreoffice(format_to, input_path, output_path, bucket, new_name):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(executor, libreoffice_subprocess, format_to, input_path)
    logger.info("File has been converted")
    logger.info("Started uploading file")
    upload_file_to_s3(output_path, bucket, new_name)


def libreoffice_subprocess(format_to, output_path):
    try:
        logger.info("Starting libreoffice subprocess")
        subprocess.run(["unoconv", "-f", format_to, output_path], check=True)

        logger.info("Subprocess finished")
    except subprocess.CalledProcessError:
        raise HTTPException(status_code=500, detail="File conversion error")
    except Exception as e:
        logger.error(f"Error during file conversion: {e}")
        raise HTTPException(status_code=500, detail="Unknown conversion error")
