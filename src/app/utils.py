import asyncio
import os
from concurrent import futures

import httpx
from botocore.exceptions import ClientError
from pdf2docx import Converter

from src.app.typing.common import TupleStrBool
from src.settings.aws_config import s3_client
from src.settings.config import logger


def convert_pdf_to_docx(pdf_path: str, docx_path: str):
    cv = Converter(pdf_path)
    cv.convert(docx_path, start=0, end=None, parse_lattice_table=False)
    cv.close()


def sync_upload_file(file_path: str, bucket_name: str, key: str) -> TupleStrBool:
    """
    Function to upload the file to the AWS S3 bucket.

    :param file_path: Path to convert the file.
    :param bucket_name: Name of the S3 bucket.
    :param key: New name of the file in the S3 bucket.
    :return: A tuple (`str`, `True`) if the file is uploaded successfully.
                A tuple (`str`, `False`) with an error message if the file is not uploaded.
    """

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


def sync_download_file(bucket: str, s3_key: str, input_path: str) -> TupleStrBool:
    """
    Downloads a file from an S3 bucket.

    :param bucket: Name of the S3 bucket.
    :param s3_key: File name (key) in the S3 bucket.
    :param input_path: Local path to save the downloaded file.
    :return: A tuple (`str`, `True`) if the download is successful.
             A tuple (`str`, `False`) with an error message if the download fails.
    """

    try:
        logger.info("File download started")

        s3_client.download_file(bucket, s3_key, input_path)
        if not os.path.exists(input_path) or os.path.getsize(input_path) == 0:
            logger.error("Download failed: file is missing or empty")
            return "Download failed: file is missing or empty", False

        logger.info("File has been downloaded")
        return "File has been downloaded", True
    except ClientError as error:
        logger.error(f"Client error: {error.response['Error']['Message']}")
        return error.response["Error"]["Message"], False
    except Exception as e:
        logger.error(f"An internal error occurred: {str(e)}")
        return str(e), False


async def download_file(bucket: str, s3_key: str, input_path: str) -> TupleStrBool:
    """
    Downloads a file from an S3 bucket.

    :param bucket: Name of the S3 bucket.
    :param s3_key: File name (key) in the S3 bucket.
    :param input_path: Local path to save the downloaded file.
    :return: A tuple (`str`, `True`) if the download is successful.
             A tuple (`str`, `False`) with an error message if the download fails.
    """

    loop = asyncio.get_event_loop()
    with futures.ProcessPoolExecutor() as pool:
        result = await loop.run_in_executor(pool, sync_download_file, bucket, s3_key, input_path)

    return result


async def upload_file_to_s3(file_path: str, bucket_name: str, key: str) -> object:
    """
    Through the `upload_file_sync` function to own event loop. Makes the sync upload_file_sync function async.

    :param file_path: Path to convert the file.
    :param bucket_name: Name of the S3 bucket.
    :param key: New name of the file in the S3 bucket.
    :return: A tuple (`str`, `True`) if the file is uploaded successfully.
             A tuple (`str`, `False`) with an error message if the file is not uploaded.
    """
    loop = asyncio.get_event_loop()
    with futures.ProcessPoolExecutor() as pool:
        result = await loop.run_in_executor(pool, sync_upload_file, file_path, bucket_name, key)

    return result


async def callback(callback_url: str, status: str, data: dict) -> dict:
    """
    Function to send the data to the external service.
    Response data is a dictionary with data on the result of the function work
    in which the status passed after the completion of the file processing functions is added.

    :param callback_url: callback URL of an external service
    :param status: status of the process - success, processing, waiting, error etc.
    :param data: the dict with the data to send after the process.
    :return: **A dict with the status of the process.**
             Statuses: success, processing, waiting, error etc.
    """
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
