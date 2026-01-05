import asyncio
import logging
import time

from fastapi import APIRouter, Request, Response, status
from fastapi.responses import JSONResponse

from app.models.schemas import ResearchRequest
from app.services.agent_service import AgentService, LLMUnavailableError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/research", tags=["research"])


@router.options("")
async def preflight(request: Request):
    origin = request.headers.get("origin", "*")
    req_headers = request.headers.get("access-control-request-headers", "content-type, authorization")
    return Response(
        status_code=204,
        headers={
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": req_headers,
            "Vary": "Origin",
        },
    )

@router.post("")
async def run_research(request: ResearchRequest):
    """
    Research endpoint that returns structured JSON matching ResearchResponse format.
    """
    try:
        # Use agent service directly
        # Wrap blocking call in asyncio.to_thread() to prevent event loop blocking
        # This is critical for Linux servers where blocking calls in async context can hang
        start_time = time.time()
        agent_service = AgentService()
        # Run the blocking search in a thread pool to avoid blocking the event loop
        raw_result = await asyncio.to_thread(
            agent_service.search,
            request.query,
            request.options or {}
        )
        execution_time_ms = int((time.time() - start_time) * 1000)

        result_payload = raw_result
        if isinstance(result_payload, dict):
            inner = result_payload.get("result")
            if isinstance(inner, dict):
                result_payload = inner

        # Transform agent result to match frontend ResearchData interface
        if isinstance(result_payload, dict):
            content = result_payload.get("content", "")
            query = result_payload.get("query", request.query)

            # Transform to frontend format
            response = {
                "success": True,
                "data": {
                    "query": query,
                    "summary": content,
                    "results": [],  # Agent doesn't provide individual search results
                    "sources": [],  # Agent doesn't provide source details
                    "statistics": {
                        "totalResults": 0,
                        "processingTime": execution_time_ms,
                        "searchTime": execution_time_ms,
                        "summaryTime": 0
                    },
                    "cached": False
                }
            }
            return JSONResponse(content=response)
        else:
            # If result is not a dict, wrap it as data
            response = {
                "success": True,
                "data": {
                    "query": request.query,
                    "summary": str(result_payload),
                    "results": [],
                    "sources": [],
                    "statistics": {
                        "totalResults": 0,
                        "processingTime": execution_time_ms,
                        "searchTime": execution_time_ms,
                        "summaryTime": 0
                    },
                    "cached": False
                }
            }
            return JSONResponse(content=response)

    except LLMUnavailableError as exc:
        logger.warning("LLM unavailable for research request", extra={"query": request.query})
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "success": False,
                "error": {
                    "code": "LLM_UNAVAILABLE",
                    "message": str(exc)
                }
            },
        )
    except Exception as e:
        logger.error("Research endpoint error", exc_info=True, extra={"query": request.query})
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": {
                    "code": "RESEARCH_ERROR",
                    "message": str(e)
                }
            }
        )
