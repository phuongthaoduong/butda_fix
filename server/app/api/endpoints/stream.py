import asyncio
import json
import logging
import os
import traceback
from typing import AsyncGenerator
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from app.services.agent_service import AgentService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/research/stream")
async def stream_research(
    query: str = Query(..., min_length=2, max_length=500, description="Research query to process"),
):
    """Stream research results with real-time progress updates."""
    client_host = "unknown"  # Could be extracted from request if needed
    logger.info(f"[STREAM] Request received", extra={"query": query, "client": client_host})

    if not query or query.strip() != query:
        logger.warning(f"[STREAM] Invalid query format", extra={"query": query})
        async def error_generator():
            yield "event: error\ndata: {\"stage\": \"error\", \"message\": \"Please enter a valid search query\"}\n\n"

        return StreamingResponse(
            error_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control",
            }
        )

    normalized_query = query.strip()

    async def generate_thoughts() -> AsyncGenerator[str, None]:
        queue: asyncio.Queue[str] = asyncio.Queue()
        agent_service = AgentService()
        event_count = 0
        start_time = asyncio.get_event_loop().time()

        async def heartbeat():
            try:
                while True:
                    await asyncio.sleep(10)
                    await queue.put(": heartbeat\n\n")
                    logger.debug(f"[STREAM] Heartbeat sent", extra={"query": normalized_query, "events": event_count})
            except asyncio.CancelledError:
                return

        async def run_agent():
            nonlocal event_count
            try:
                logger.info(f"[STREAM] Starting agent service", extra={"query": normalized_query})
                async for ev in agent_service.search_with_thoughts(normalized_query):
                    event_count += 1
                    stage = ev.get("stage")
                    logger.debug(f"[STREAM] Event #{event_count}: {stage}", extra={
                        "query": normalized_query,
                        "stage": stage,
                        "event_message": ev.get("message"),
                        "event_num": event_count
                    })

                    if stage == "error":
                        # Provide detailed error info for debugging
                        user_message = ev.get("message")
                        error_code = ev.get("error", "unknown")
                        logger.error(f"[STREAM] Error event from agent", extra={
                            "query": normalized_query,
                            "error_code": error_code,
                            "error_message": user_message
                        })
                        # Keep full error message for debugging, don't truncate
                        if not user_message:
                            user_message = "Unable to process your request"
                        data = json.dumps({
                            "stage": "error",
                            "message": user_message,
                            "code": error_code
                        })
                        await queue.put(f"event: error\ndata: {data}\n\n")
                        break
                    if stage == "complete":
                        elapsed = asyncio.get_event_loop().time() - start_time
                        logger.info(f"[STREAM] Research completed", extra={
                            "query": normalized_query,
                            "events": event_count,
                            "elapsed_ms": int(elapsed * 1000)
                        })
                        final_data = json.dumps({"stage": "complete", "success": True, "data": ev.get("data")})
                        await queue.put(f"event: complete\ndata: {final_data}\n\n")
                        break
                    payload = {"stage": stage, "message": ev.get("message")}
                    if ev.get("details") is not None:
                        payload["details"] = ev.get("details")
                    if ev.get("article_url") is not None:
                        payload["article_url"] = ev.get("article_url")
                    await queue.put(f"event: progress\ndata: {json.dumps(payload)}\n\n")
            except Exception as e:
                logger.error(f"[STREAM] Exception in run_agent", exc_info=True, extra={
                    "query": normalized_query,
                    "error": str(e),
                    "traceback": traceback.format_exc()
                })
                # Send actual error message for debugging
                err = json.dumps({
                    "stage": "error",
                    "message": f"{type(e).__name__}: {str(e)}",
                    "code": "internal_error"
                })
                await queue.put(f"event: error\ndata: {err}\n\n")

        hb_task = asyncio.create_task(heartbeat())
        agent_task = asyncio.create_task(run_agent())

        try:
            while True:
                if agent_task.done():
                    hb_task.cancel()
                    while not queue.empty():
                        yield await queue.get()
                    break
                try:
                    item = await asyncio.wait_for(queue.get(), timeout=5.0)
                    yield item
                except asyncio.TimeoutError:
                    continue
        finally:
            if not hb_task.done():
                hb_task.cancel()

    return StreamingResponse(
        generate_thoughts(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control",
        }
    )
