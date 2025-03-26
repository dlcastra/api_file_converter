from typing import Dict

import httpx

from src.settings.config import logger


async def callback(callback_url: str, status: str, data: Dict) -> Dict:
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
