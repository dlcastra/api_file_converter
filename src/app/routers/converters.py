from fastapi import APIRouter
from pydantic import BaseModel
from starlette.responses import JSONResponse

from src.app.handlers import convert_file
from src.app.models.statuses import Status
from src.app.utils import callback

router = APIRouter()


class ConvertFileRequest(BaseModel):
    s3_key: str
    format_from: str
    format_to: str
    callback_url: str


@router.post("/convert-file")
async def convert_from_docx_to_pdf(request: ConvertFileRequest) -> JSONResponse:
    try:
        status, result = await convert_file(request.s3_key, request.format_from, request.format_to)
        response: dict = await callback(request.callback_url, status=status, data=result)
        if response["status"] == Status.SUCCESS:
            return JSONResponse(status_code=201, content={"status": Status.SUCCESS})
        return JSONResponse(status_code=500, content=response)
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})
