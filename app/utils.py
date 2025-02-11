import httpx
import requests
from pdf2docx import Converter

from settings.aws_config import s3_client
from settings.config import settings, logger
from app.models.statuses import Status


def convert_pdf_to_docx(pdf_path: str, docx_path: str):
    cv = Converter(pdf_path)
    cv.convert(docx_path, start=0, end=None, parse_lattice_table=False)
    cv.close()


def generate_s3_download_url(key: str) -> bool and str:
    try:
        params = {"Bucket": settings.AWS_S3_BUCKET_NAME, "Key": key}
        presigned_url = s3_client.generate_presigned_url("get_object", Params=params, ExpiresIn=300)
        return presigned_url, True

    except Exception as e:
        logger.error(f"Error during link generation: {str(e)}")
        return str(e), None


def download_file(input_path: str, presigned_url: str):
    try:
        response = requests.get(presigned_url)
        response.raise_for_status()

        logger.info("Writing file to disk")
        with open(input_path, "wb") as file:
            file.write(response.content)
        logger.info(f"File written to {input_path}")
        return "Successfully downloaded", True

    except Exception as e:
        logger.error(f"Error during download file: {str(e)}")
        return str(e), None


def upload_file_to_s3(file_path: str, bucket_name: str, key: str):
    try:
        logger.info("Started uploading file")
        s3_client.upload_file(file_path, bucket_name, key)
        logger.info("File has been uploaded to AWS S3")
        return "Successfully uploaded", True

    except Exception as e:
        logger.error(f"S3 upload error: {str(e)}")
        return str(e), None


async def callback(callback_url, status, data):
    async with httpx.AsyncClient() as client:
        try:
            data["status"] = status
            response = await client.post(callback_url, json=data)
            response.raise_for_status()
            return {"status": status}

        except Exception as e:
            logger.error(e)
            await client.post(callback_url, json={"error": str(e)})
