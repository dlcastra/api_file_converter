from fastapi import APIRouter
from pydantic import BaseModel

from app.handlers import convert_file
from app.utils import callback

router = APIRouter()


class RequestS3Key(BaseModel):
    s3_key: str
    format_from: str
    format_to: str
    callback_url: str


@router.post("/convert-file")
async def convert_from_docx_to_pdf(request: RequestS3Key):
    status, result = await convert_file(request.s3_key, request.format_from, request.format_to)
    return await callback(request.callback_url, status=status, data=result)
