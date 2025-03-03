import asyncio
import tempfile

from src.app.models.statuses import Status
from src.app.typing.converter import ConverterService
from src.app.utils import upload_file_to_s3, download_file
from src.settings.config import logger


class FileConverterService:
    async def file_processing(self, s3_key: str, converted_key: str, format_to: str, bucket: str) -> ConverterService:
        """
        Process the file using the internal methods. First, download the file from the S3 bucket, after that convert it
        to chosen format and finally upload it back to the S3 bucket.

        :param s3_key: File name in the S3 bucket.
        :param converted_key: Expected file name after conversion.
        :param format_to: File format to convert to.
        :param bucket: Name of the S3 bucket.
        :return: A tuple (`str`, `True`) if the process is successful.
                 A tuple (`str`, `False`) with an error message if the process fails.
        """

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = f"{tmpdir}/{s3_key}"
            output_path = f"{tmpdir}/{converted_key}"

            try:
                message, is_downloaded = await download_file(bucket, s3_key, input_path)
                if not is_downloaded:
                    return message, False

                message, is_converted = await self._convert_file(format_to, output_path, input_path)
                if not is_converted:
                    return message, False

                message, is_uploaded = await upload_file_to_s3(output_path, bucket, converted_key)
                if not is_uploaded:
                    return message, False

                logger.info("File processing operation completed successfully")
                return Status.SUCCESS, True

            except Exception as e:
                logger.error(f"An internal error occurred: {str(e)}")
                return str(e), False

    async def _convert_with_libreoffice(self, format_to: str, output_path: str, input_path: str) -> ConverterService:
        """
        Convert the file from one format to another using LibreOffice.

        :param format_to: File format to convert to.
        :param output_path: Path to save the converted file.
        :param input_path: Path to get the file to convert.
        :return: A tuple (`str`, `True`) if the conversion is successful.
                 A tuple (`str`, `False`) with an error message if the conversion fails
        """
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

    async def _convert_file(self, format_to: str, output_path: str, input_path: str) -> ConverterService:
        """
        Convert the file from one format to another.
        :param format_to: Format to convert the file to.
        :param output_path: Path to save the converted file.
        :param input_path: Path to the file to convert.
        :return: A tuple (`str`, `True`) if the conversion is successful.
                 A tuple (`str`, `False`) with an error message if the conversion fails.
        """

        try:
            logger.info("File conversion started")

            message, is_converted = await self._convert_with_libreoffice(format_to, output_path, input_path)
            if not is_converted:
                logger.error(f"File conversion failed: {message}")
                return message, False

            logger.info("File conversion successful")
            return "File has been converted", True
        except Exception as e:
            logger.error(f"An internal error occurred: {str(e)}")
            return str(e), False
