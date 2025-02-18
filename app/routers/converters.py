from fastapi import APIRouter
from pydantic import BaseModel

from app.handlers import convert_file, file_scraper
from app.utils import callback

router = APIRouter()


class ConvertFileRequest(BaseModel):
    s3_key: str
    format_from: str
    format_to: str
    callback_url: str


class FileParsingRequest(BaseModel):
    s3_key: str
    keywords: list[str]
    callback_url: str


@router.post("/convert-file")
async def convert_from_docx_to_pdf(request: ConvertFileRequest):
    try:
        status, result = await convert_file(request.s3_key, request.format_from, request.format_to)
        return await callback(request.callback_url, status=status, data=result)
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/parse-file")
async def parse_file(request: FileParsingRequest):
    try:
        status, result = await file_scraper(request.s3_key, request.keywords)
        result["s3_key"] = request.s3_key
        return await callback(request.callback_url, status=status, data=result)
    except Exception as e:
        return {"status": "error", "message": str(e)}
