import requests
from fastapi import HTTPException
from pdf2docx import Converter

from settings.aws_config import s3_client
from settings.config import settings, logger


def convert_pdf_to_docx(pdf_path: str, docx_path: str):
    cv = Converter(pdf_path)
    cv.convert(docx_path, start=0, end=None, parse_lattice_table=False)
    cv.close()


def generate_s3_download_url(key: str) -> str:
    try:
        presigned_url = s3_client.generate_presigned_url(
            "get_object", Params={"Bucket": settings.AWS_S3_BUCKET_NAME, "Key": key}, ExpiresIn=300
        )
        return presigned_url

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error during link generation: {str(e)}")


def download_file(input_path: str, presigned_url: str):
    try:
        response = requests.get(presigned_url)
        response.raise_for_status()
        logger.info("Writing file to disk")
        with open(input_path, "wb") as file:
            file.write(response.content)
        logger.info(f"File written to {input_path}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error during download file: {str(e)}")


def upload_file_to_s3(file_path: str, bucket_name: str, key: str):
    try:
        s3_client.upload_file(file_path, bucket_name, key)
        logger.info("File has been uploaded to AWS S3")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"S3 upload error: {str(e)}")
