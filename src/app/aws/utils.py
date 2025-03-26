import asyncio
import os
from concurrent import futures
from io import BytesIO
from typing import Tuple, Union

from botocore.exceptions import BotoCoreError, ClientError

from src.app.aws.clients import s3_client
from src.settings.config import logger
from src.app.constants import CONTENT_TYPES
from src.app.aws.responses import AWSErrorResponse, AWSSuccessResponse


def sync_download_file_as_bytes(bucket: str, s3_key: str) -> Tuple[Union[BytesIO, str], bool]:
    """
    Downloads a file from S3 and returns it as BytesIO object.

    :param bucket: S3 bucket name.
    :param s3_key: Destination file name in S3.
    :return: A Tuple (`BytesIO`, `True`) if the download is successful.
             A Tuple (`str`, `False`) if the download fails.
    """

    try:
        response = s3_client.get_object(Bucket=bucket, Key=s3_key)
        logger.info(f"File {s3_key} downloaded from S3")
        return BytesIO(response["Body"].read()), True
    except (BotoCoreError, ClientError) as e:
        logger.error(f"Failed to download file from S3: {str(e)}")
        return AWSErrorResponse.ERROR_DOWNLOAD_FILE, False


def sync_upload_bytes_to_s3(bucket: str, s3_key: str, file_bytes: BytesIO, file_format: str) -> Tuple[str, bool]:
    """
    Uploads a BytesIO object to S3.

    :param bucket: S3 bucket name.
    :param s3_key: Destination file name in S3.
    :param file_bytes: File content in BytesIO.
    :param file_format: Target file format (used for MIME type).
    :return: Tuple (status message, success flag).
    """

    content_type = CONTENT_TYPES.get(file_format, "application/octet-stream")

    try:
        file_bytes.seek(0)
        s3_client.upload_fileobj(file_bytes, bucket, s3_key, ExtraArgs={"ContentType": content_type})
        logger.info(f"File {s3_key} uploaded to S3")
        return AWSSuccessResponse.FILE_UPLOADED, True

    except (BotoCoreError, ClientError) as e:
        logger.error(f"Failed to upload file to S3: {str(e)}")
        return AWSErrorResponse.ERROR_UPLOAD_FILE, False


def sync_download_file(bucket: str, s3_key: str, input_path: str) -> Tuple[str, bool]:
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
        return AWSSuccessResponse.FILE_DOWNLOADED, True
    except ClientError as error:
        logger.error(f"Client error: {error.response['Error']['Message']}")
        return AWSErrorResponse.ERROR_DOWNLOAD_FILE, False
    except Exception as e:
        logger.error(f"An internal error occurred: {str(e)}")
        return AWSErrorResponse.ERROR_DOWNLOAD_FILE, False


def sync_upload_file(file_path: str, bucket_name: str, key: str) -> Tuple[str, bool]:
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
            return AWSErrorResponse.ERROR_UPLOAD_FILE, False

        logger.info("File has been uploaded to AWS S3")
        return AWSSuccessResponse.FILE_UPLOADED, True

    except Exception as e:
        logger.error(f"S3 upload error: {str(e)}")
        return AWSErrorResponse.ERROR_UPLOAD_FILE, False


async def download_file_as_bytes(bucket: str, s3_key: str) -> Tuple[Union[BytesIO, str], bool]:
    """
    Downloads a file from S3 and returns it as BytesIO object.

    :param bucket: S3 bucket name.
    :param s3_key: Destination file name in S3.
    :return: A Tuple (`BytesIO`, True) if the download is successful.
             A Tuple (None, False) if the download fails.
    """

    loop = asyncio.get_event_loop()
    with futures.ThreadPoolExecutor() as pool:
        result = await loop.run_in_executor(pool, sync_download_file_as_bytes, bucket, s3_key)

    return result


async def upload_bytes_to_s3(bucket: str, s3_key: str, file_bytes: BytesIO, file_format: str) -> Tuple[str, bool]:
    """
    Uploads a BytesIO object to S3.

    :param bucket: S3 bucket name.
    :param s3_key: Destination file name in S3.
    :param file_bytes: File content in BytesIO.
    :param file_format: Target file format (used for MIME type).
    :return: Tuple (status message, success flag).
    """

    loop = asyncio.get_event_loop()
    with futures.ThreadPoolExecutor() as pool:
        result = await loop.run_in_executor(pool, sync_upload_bytes_to_s3, bucket, s3_key, file_bytes, file_format)

    return result


async def download_file(bucket: str, s3_key: str, input_path: str) -> Tuple[str, bool]:
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


async def upload_file_to_s3(file_path: str, bucket_name: str, key: str) -> Tuple[str, bool]:
    """
    Through the `upload_file_sync` function to own event loop. Makes the sync upload_file_sync function async.

    :param file_path: Path to convert the file.
    :param bucket_name: Name of the S3 bucket.
    :param key: New name of the file in the S3 bucket.
    :return: A tuple (`str`, `True`) if the file is uploaded successfully.
             A tuple (`str`, `False`) with an error message if the file is not uploaded.
    """

    loop = asyncio.get_event_loop()
    with futures.ThreadPoolExecutor() as pool:
        result = await loop.run_in_executor(pool, sync_upload_file, file_path, bucket_name, key)

    return result
