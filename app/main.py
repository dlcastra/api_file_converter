from fastapi import FastAPI

from fastapi.exceptions import RequestValidationError
from starlette.responses import JSONResponse
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

from app.routers import converters

app = FastAPI()
app.include_router(converters.router, prefix="/converter", tags=["Converters"])


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    errors = [{"field": err["loc"][-1], "msg": err["msg"]} for err in exc.errors()]
    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": errors},
    )
