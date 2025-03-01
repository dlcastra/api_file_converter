from fastapi import FastAPI, APIRouter

from fastapi.exceptions import RequestValidationError
from starlette.responses import JSONResponse
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

from src.app.routers import converters, parsers

app = FastAPI()
api_router = APIRouter(prefix="/api/v1")

api_router.include_router(converters.router, prefix="/converter", tags=["Converters"])
api_router.include_router(parsers.router, prefix="/parser", tags=["Parsers"])
app.include_router(api_router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    errors = [{"field": err["loc"][-1], "msg": err["msg"]} for err in exc.errors()]
    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": errors},
    )
