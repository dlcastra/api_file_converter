import asyncio
import json
from typing import Optional

from src.app.handlers import convert_file, file_scraper
from src.app.utils import callback
from src.settings.config import settings


async def process_sqs_messages(sqs_client):
    while True:
        response = sqs_client.receive_message(
            QueueUrl=settings.AWS_SQS_QUEUE_URL, MaxNumberOfMessages=10, WaitTimeSeconds=20, VisibilityTimeout=30
        )

        messages = response.get("Messages", [])
        if not messages:
            await asyncio.sleep(0.5)
            continue

        tasks = [asyncio.create_task(handle_message(sqs_client, message)) for message in messages]
        await asyncio.gather(*tasks)


async def handle_message(sqs_client, message: dict) -> None:
    try:
        message_body = json.loads(message["Body"])
        s3_key = message_body.get("s3_key")
        callback_url = message_body.get("callback_url")

        status, result = await process_message_body(message_body, s3_key)

        await callback(callback_url, status=status, data=result)

    finally:
        await delete_sqs_message(sqs_client, message)


async def process_message_body(message_body: dict, s3_key: Optional[str]):
    format_from, format_to = message_body.get("format_from"), message_body.get("format_to")
    keywords = message_body.get("keywords")

    if format_from and format_to:
        return await convert_file(s3_key=s3_key, old_format=format_from, format_to=format_to)
    elif keywords:
        return await file_scraper(s3_key=s3_key, keywords=keywords)

    return None, None


async def delete_sqs_message(sqs_client, message: dict) -> None:
    sqs_client.delete_message(QueueUrl=settings.AWS_SQS_QUEUE_URL, ReceiptHandle=message["ReceiptHandle"])
