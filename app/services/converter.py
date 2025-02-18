import asyncio
import tempfile

from app.models.statuses import Status
from app.utils import download_file, upload_file_to_s3
from settings.config import logger


class FileConverterService:
    async def file_processing(self, s3_key: str, download_url: str, converted_key: str, format_to, bucket: str):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = f"{tmpdir}/{s3_key}"
            output_path = f"{tmpdir}/{converted_key}"

            message, is_downloaded = download_file(input_path, download_url)
            if not is_downloaded:
                return message, None

            message, is_converted = await self.convert_with_libreoffice(format_to, output_path, input_path)
            if not is_converted:
                return message, None

            message, is_uploaded = upload_file_to_s3(output_path, bucket, converted_key)
            if not is_uploaded:
                return message, None

            return Status.SUCCESS.value, True

    async def convert_with_libreoffice(self, format_to, output_path, input_path):
        try:
            if input_path.endswith(".pdf"):
                process = await asyncio.create_subprocess_exec(
                    "pdf2smth",
                    format_to,
                    input_path,
                    output_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
            else:

                process = await asyncio.create_subprocess_exec(
                    "unoconv",
                    "-f",
                    format_to,
                    "-o",
                    output_path,
                    input_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                logger.error(f"LibreOffice conversion failed: {stderr.decode().strip()}")
                return "Error converting", None

            logger.info("File has been converted")
            return "File has been converted", True

        except Exception as e:
            logger.error(f"Error during conversion: {str(e)}")
            return str(e), None
