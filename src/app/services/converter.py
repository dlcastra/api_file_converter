import asyncio
import os
import tempfile

from botocore.exceptions import ClientError

from src.app.models.statuses import Status
from src.app.utils import upload_file_to_s3
from src.settings.aws_config import s3_client
from src.settings.config import logger
from src.app.typing.converter import ConverterService


class FileConverterService:
    async def file_processing(self, s3_key: str, converted_key: str, format_to: str, bucket: str) -> ConverterService:
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = f"{tmpdir}/{s3_key}"
            output_path = f"{tmpdir}/{converted_key}"

            try:
                s3_client.download_file(bucket, s3_key, input_path)
                if not os.path.exists(input_path) or os.path.getsize(input_path) == 0:
                    return f"Download failed: file {s3_key} is missing or empty", False

                message, is_converted = await self._convert_with_libreoffice(format_to, output_path, input_path)
                if not is_converted:
                    return message, False

                message, is_uploaded = await upload_file_to_s3(output_path, bucket, converted_key)
                if not is_uploaded:
                    return message, False

                return Status.SUCCESS, True

            except ClientError as error:
                return error.response["Error"]["Message"], False
            except Exception as e:
                return str(e), False

    async def _convert_with_libreoffice(self, format_to: str, output_path: str, input_path: str) -> ConverterService:
        try:
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
                return "Error converting", False

            logger.info("File has been converted")
            return "File has been converted", True

        except Exception as e:
            logger.error(f"Error during conversion: {str(e)}")
            return str(e), False
