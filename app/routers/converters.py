import os
import tempfile

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.handlers import convert_file
from app.utils import convert_pdf_to_docx, generate_s3_download_url, download_file, upload_file_to_s3
from settings.config import settings

router = APIRouter()


class RequestS3Key(BaseModel):
    s3_key: str


@router.post("/from-docx-to-pdf")
async def convert_from_docx_to_pdf(request: RequestS3Key):
    return await convert_file(request.s3_key, "docx", "pdf")


@router.post("/from-pdf-to-docx")
async def convert_from_pdf_to_docx(request: RequestS3Key):
    s3_key = request.s3_key
    converted_s3_key = s3_key.replace(".pdf", ".docx")
    download_url = generate_s3_download_url(s3_key)

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, s3_key)
        output_path = os.path.join(tmpdir, converted_s3_key)

        await download_file(input_path, download_url)

        try:
            convert_pdf_to_docx(input_path, output_path)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"File conversion error: {e}")

        output_s3_key = converted_s3_key
        await upload_file_to_s3(output_path, settings.AWS_S3_BUCKET_NAME, output_s3_key)

        file_url = f"https://{settings.AWS_S3_BUCKET_NAME}.s3.{settings.AWS_S3_REGION}.amazonaws.com/{output_s3_key}"
        return {"file_url": file_url, "new_s3_key": converted_s3_key}


@router.post("/from-txt-to-docx")
async def convert_from_txt_to_docx(request: RequestS3Key):
    return await convert_file(request.s3_key, "txt", "docx")


@router.post("/from-txt-to-pdf")
async def convert_from_txt_to_pdf(request: RequestS3Key):
    return await convert_file(request.s3_key, "txt", "pdf")
