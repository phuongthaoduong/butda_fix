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

        # DEBUG: Print raw result from agent service
        print("\n" + "="*80)
        print("DEBUG: Raw Result from Agent Service:")
        print("="*80)
        print(f"Type: {type(raw_result)}")
        if isinstance(raw_result, dict):
            print(f"Keys: {list(raw_result.keys())}")
            print("\nFull Result:")
            import json
            print(json.dumps(raw_result, indent=2, ensure_ascii=False))
        print("="*80 + "\n")

        result_payload = raw_result
        if isinstance(result_payload, dict):
            inner = result_payload.get("result")
            if isinstance(inner, dict):
                result_payload = inner
                # DEBUG: Print after extracting inner
                print("\nDEBUG: After extracting inner 'result':")
                print(json.dumps(result_payload, indent=2, ensure_ascii=False))
                print()

        # Transform agent result to match frontend ResearchData interface
        if isinstance(result_payload, dict):
            content = result_payload.get("content", "")
            query = result_payload.get("query", request.query)

            # First, try to get sources from search_results (has title, url, snippet)
            sources = result_payload.get("search_results", [])
            if not sources:
                # Fallback: try to extract sources from the JSON in content
                try:
                    import re
                    import json

                    # Content is wrapped in ```json ... ``` markdown, extract the JSON
                    json_match = re.search(r'```json\s*\n(.*?)\n```', content, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(1)
                        parsed_content = json.loads(json_str)
                        # Try sources_used first, then sources
                        sources = parsed_content.get("sources_used", []) or parsed_content.get("sources", [])
                        # Convert URLs to source format if needed
                        if sources and isinstance(sources[0], str):
                            sources = [{"url": s, "title": "", "snippet": ""} for s in sources]
                except Exception as e:
                    logger.warning(f"Failed to parse sources from content: {e}")

            # Transform to frontend format
            response = {
                "success": True,
                "data": {
                    "query": query,
                    "summary": content,
                    "results": [],  # Agent doesn't provide individual search results
                    "sources": sources,  # Extracted from parsed JSON in content
                    "statistics": {
                        "totalResults": len(sources),
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
