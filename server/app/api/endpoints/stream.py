import asyncio
import json
import logging
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
    if not query or query.strip() != query:
        async def error_generator():
            # Simplified user-friendly error message (Phase 4: Resilience)
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

        async def heartbeat():
            try:
                while True:
                    await asyncio.sleep(10)
                    await queue.put(": heartbeat\n\n")
            except asyncio.CancelledError:
                return

        async def run_agent():
            try:
                async for ev in agent_service.search_with_thoughts(normalized_query):
                    stage = ev.get("stage")
                    if stage == "error":
                        # Simplify error message for users (Phase 4: Resilience)
                        user_message = ev.get("message")
                        if user_message and len(user_message) > 100:
                            user_message = "Something went wrong while processing your request"
                        elif not user_message:
                            user_message = "Unable to process your request"
                        data = json.dumps({"stage": "error", "message": user_message})
                        await queue.put(f"event: error\ndata: {data}\n\n")
                        break
                    if stage == "complete":
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
                # Generic user-friendly error (Phase 4: Resilience)
                logger.error(f"Research error: {e}")
                err = json.dumps({"stage": "error", "message": "Something went wrong. Please try again."})
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
