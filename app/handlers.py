import os
import subprocess
import tempfile

from fastapi import HTTPException

from app.utils import generate_s3_download_url, download_file, upload_file_to_s3
from settings.config import settings


async def convert_file(s3_key: str, old_format, format_to: str) -> dict:
    converted_s3_key = s3_key.replace(f".{old_format}", f".{format_to}")
    bucket = settings.AWS_S3_BUCKET_NAME
    download_url = generate_s3_download_url(s3_key)

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, s3_key)
        output_path = os.path.join(tmpdir, converted_s3_key)

        download_file(input_path, download_url)
        convert_with_libreoffice(format_to, tmpdir, input_path, output_path, bucket, converted_s3_key)

        file_url = f"https://{bucket}.s3.{settings.AWS_S3_REGION}.amazonaws.com/{converted_s3_key}"
        return {"file_url": file_url, "new_s3_key": converted_s3_key}


def convert_with_libreoffice(format_to, tempdir, input_path, output_path, bucket, new_name):
    libreoffice_subprocess(format_to, tempdir, input_path),
    upload_file_to_s3(output_path, bucket, new_name)


def libreoffice_subprocess(format_to, tempdir, input_path):
    try:
        subprocess.run(
            ["libreoffice", "--headless", "--convert-to", format_to, "--outdir", tempdir, input_path], check=True
        )
    except subprocess.CalledProcessError:
        raise HTTPException(status_code=500, detail="File conversion error")
