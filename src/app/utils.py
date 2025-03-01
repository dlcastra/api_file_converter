import os

import httpx
from pdf2docx import Converter

from src.settings.aws_config import s3_client
from src.settings.config import logger
from src.app.typing.common import TupleStrBool


def convert_pdf_to_docx(pdf_path: str, docx_path: str):
    cv = Converter(pdf_path)
    cv.convert(docx_path, start=0, end=None, parse_lattice_table=False)
    cv.close()


async def upload_file_to_s3(file_path: str, bucket_name: str, key: str) -> TupleStrBool:
    try:
        logger.info("Started uploading file")
        s3_client.upload_file(file_path, bucket_name, key)
        if not os.path.exists(file_path) and os.path.getsize(file_path) <= 0:
            logger.info("An error while uploading file")
            return "An error while uploading file", False

        logger.info("File has been uploaded to AWS S3")
        return "Successfully uploaded", True

    except Exception as e:
        logger.error(f"S3 upload error: {str(e)}")
        return str(e), False


async def callback(callback_url: str, status: str, data: dict) -> dict:
    async with httpx.AsyncClient() as client:
        try:
            data["status"] = status
            response = await client.post(callback_url, json=data)
            response.raise_for_status()
            return {"status": status}

        except TypeError:
            logger.error(f"Type error | Data format: {type(data)}, while dict was expected.")
            await client.post(callback_url, json={"error": "Type error during response data generation"})
            return {"status": "error", "message": "Callback: Type error"}

        except Exception as e:
            logger.error(e)
            await client.post(callback_url, json={"error": str(e)})
            return {"status": "error", "message": "Callback: Unexpected error"}
