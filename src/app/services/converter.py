import asyncio
import tempfile
import uuid
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from pathlib import Path
from typing import Tuple

import fitz
from pdf2docx import Converter

from src.app.constants import ALLOWED_IMAGES_TYPES, ALLOWED_FILE_FORMATS
from src.app.services.responses import ConverterErrorResponse
from src.app.typing.converter import ConverterService
from src.settings.config import logger


class FileConverterService:
    def __init__(self, tmp_dir="/tmp"):
        self.tmp_dir = Path(tmp_dir)

    async def file_processing(self, format_from: str, format_to: str, file_bytes: BytesIO) -> ConverterService:
        """
        The main class method to call the conversion process.

        :param format_from: Input file format.
        :param format_to: Output file format.
        :param file_bytes: Content of the file as BytesIO.
        :return: Tuple with the converted file as BytesIO or str with the error message and boolean flag.
        """

        try:
            result, is_converted = await self._convert_file(format_from, format_to, file_bytes)
            if is_converted and isinstance(result, BytesIO):
                logger.info("File successfully converted")
                result.seek(0)

            return result, is_converted

        except Exception as e:
            logger.error(f"Internal error: {str(e)}")
            return ConverterErrorResponse.INTERNAL_ERROR, False

    async def _convert_file(self, format_from: str, format_to: str, file_bytes: BytesIO) -> ConverterService:
        """
        Convert a file from one format to another using LibreOffice or custom PDF converter.

        :param format_from: Input file format.
        :param format_to: Output file format.
        :param file_bytes: The file content as BytesIO.
        :return: Tuple with the converted file as BytesIO or str with the error message and boolean flag.
        """

        try:
            is_from_pdf_or_image = format_from == "pdf" or format_from in ALLOWED_IMAGES_TYPES
            is_to_image = format_to in ALLOWED_IMAGES_TYPES
            is_to_file_allowed_format = format_to in ALLOWED_FILE_FORMATS

            if (is_from_pdf_or_image and is_to_image) or (format_from != "pdf" and is_to_file_allowed_format):
                return await self._convert_with_libreoffice(file_bytes, format_to)

            return await self._pdf_converter(file_bytes, format_to)

        except Exception as e:
            logger.error(f"Conversion error: {e}")
            return ConverterErrorResponse.INTERNAL_ERROR, False

    async def _convert_with_libreoffice(self, file_bytes: BytesIO, format_to: str) -> ConverterService:
        """
        Convert a file using LibreOffice using RAM storage and parallel execution.

        :param file_bytes: The file content as BytesIO.
        :param format_to: The target format (e.g., "pdf", "docx").
        :return: Converted file as BytesIO or error message as string and boolean flag.
        """

        try:
            temp_dir = Path(tempfile.gettempdir())
            input_path = temp_dir / f"{uuid.uuid4()}.input"
            output_path = temp_dir / f"{uuid.uuid4()}.{format_to}"

            input_path.write_bytes(file_bytes.getvalue())
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
                Path(input_path).unlink(missing_ok=True)
                Path(output_path).unlink(missing_ok=True)
                logger.error(f"LibreOffice conversion failed: {stderr.decode().strip()}")
                return ConverterErrorResponse.INTERNAL_ERROR, False

            converted_bytes = BytesIO(Path(output_path).read_bytes())
            Path(input_path).unlink(missing_ok=True)
            Path(output_path).unlink(missing_ok=True)

            return converted_bytes, True

        except Exception as e:
            logger.error(f"Error during conversion: {e}")
            return ConverterErrorResponse.INTERNAL_ERROR, False

    async def _pdf_converter(self, file_bytes: BytesIO, format_to: str) -> Tuple[BytesIO, bool]:
        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor() as executor:
            if format_to == "docx":
                return await loop.run_in_executor(executor, self._convert_pdf_to_docx, file_bytes)
            elif format_to == "txt":
                return await loop.run_in_executor(executor, self._convert_pdf_to_txt, file_bytes)
            elif format_to == "doc":
                docx_file, _ = await loop.run_in_executor(executor, self._convert_pdf_to_docx, file_bytes)
                return await self._convert_with_libreoffice(docx_file, "doc")
            else:
                return BytesIO(), False

    def _convert_pdf_to_docx(self, file_bytes: BytesIO) -> Tuple[BytesIO, bool]:
        output_stream = BytesIO()
        cv = Converter(stream=file_bytes.getvalue())

        try:
            cv.convert(output_stream, start=0, end=None, parse_lattice_table=False)
            cv.close()
            output_stream.seek(0)
            return output_stream, True
        except Exception as e:
            logger.error(f"Error during conversion: {str(e)}")
            cv.close()
            return BytesIO(), False

    def _convert_pdf_to_txt(self, file_bytes) -> Tuple[BytesIO, bool]:
        try:
            doc = fitz.open("pdf", file_bytes.read())
            text = "\n".join([page.get_text() for page in doc])

            output = BytesIO()
            output.write(text.encode("utf-8"))
            output.seek(0)
            return output, True
        except Exception as e:
            logger.error(f"Error during convertion from pdf to txt: {e}")
            return BytesIO(), False
