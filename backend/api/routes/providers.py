"""Provider API routes"""

from fastapi import APIRouter
from backend.llm.providers import ProviderStatus

router = APIRouter(prefix="/api/providers", tags=["providers"])

provider_status = ProviderStatus()


@router.get("/status")
async def get_provider_status():
    """Get provider health status"""
    return await provider_status.check_all()

