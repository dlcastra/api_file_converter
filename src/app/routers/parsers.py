from fastapi import APIRouter
from pydantic import BaseModel
from starlette.responses import JSONResponse

from src.app.handlers import file_scraper
from src.app.models.statuses import Status
from src.app.utils import callback

router = APIRouter()


class FileParsingRequest(BaseModel):
    s3_key: str
    keywords: list[str]
    callback_url: str


@router.post("/parse-file")
async def parse_file(request: FileParsingRequest) -> JSONResponse:
    try:
        status, result = await file_scraper(request.s3_key, request.keywords)
        response: dict = await callback(request.callback_url, status=status, data=result)
        if response["status"] == Status.SUCCESS:
            return JSONResponse(status_code=201, content={"status": Status.SUCCESS})
        return JSONResponse(status_code=500, content=response)
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})
