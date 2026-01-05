import time

from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_check() -> dict[str, object]:
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "research-agent-api",
    }


