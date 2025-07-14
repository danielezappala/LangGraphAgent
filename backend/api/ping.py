import sys
from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

# No prefix in the router since we'll add it in server.py
router = APIRouter(prefix="", tags=["ping"])

@router.get("", include_in_schema=False)
@router.get("/")
async def ping():
    """A simple ping endpoint to check if the server is running."""
    print("Ping endpoint called successfully")
    print(f"Python version: {sys.version}")
    return PlainTextResponse("pong")
