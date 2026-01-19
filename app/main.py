from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.routes import api, pages
import os

# App configuration
APP_NAME = "Recipe Explorer"
VERSION = "1.0.0"
DEBUG = True

# Create FastAPI app
app = FastAPI(title=APP_NAME, version=VERSION)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Global handler for validation errors"""
    error_details = {}
    for error in exc.errors():
        # Skip 'body' in the location path for cleaner field names
        field_path = error["loc"][1:] if error["loc"][0] == "body" else error["loc"]
        field = " -> ".join(str(x) for x in field_path)
        error_details[field] = error["msg"]
    
    return JSONResponse(
        status_code=422,
        content={
            "error": True,
            "message": "Validation failed",
            "details": error_details,
            "status_code": 422
        }
    )

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(api.router)
app.include_router(pages.router)

# Basic health check
@app.get("/health")
def health_check():
    return {"status": "healthy"}
