"""API endpoint for version information."""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
import sys
import os
from pathlib import Path

# Add parent directory to path to import version
sys.path.append(str(Path(__file__).parent.parent))
from version import get_version

router = APIRouter()

@router.get("/version")
async def get_api_version():
    """
    Return the current version information for the API.
    
    Returns:
        dict: Version information including version number and build details.
    """
    try:
        version_info = get_version()
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "data": version_info
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"Failed to retrieve version information: {str(e)}"
            }
        )
