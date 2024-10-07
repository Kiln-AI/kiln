from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


def connect_custom_errors(app: FastAPI):
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        # Write user friendly error messages
        error_messages = []
        for error in exc.errors():
            field = error["loc"][-1]  # Get the field name
            message = error["msg"]
            error_messages.append(f"{field.capitalize()}: {message}")

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "message": ".\n".join(error_messages),
                "source_errors": exc.errors(),
            },
        )
