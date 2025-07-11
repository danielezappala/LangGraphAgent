import sys
from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

router = APIRouter(tags=["ping"])

@router.get("/ping")
async def ping():
    """A simple ping endpoint to check if the server is running."""
    print("Ping endpoint called successfully")
    print(f"Python version: {sys.version}")
    return PlainTextResponse("pong")
