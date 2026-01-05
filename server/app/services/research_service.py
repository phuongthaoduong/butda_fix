from __future__ import annotations

import logging
import time
from typing import Any

from app.services.agent_service import AgentService
from app.services.cache_client import CacheClient

logger = logging.getLogger(__name__)


class ResearchService:
    def __init__(self) -> None:
        self.cache = CacheClient()
        self.agent_service = AgentService()

    async def process_research(
        self, query: str, options: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Process research query - returns raw agent result.
        For now, just call agent service directly.
        """
        normalized_query = " ".join(query.split())
        logger.info("Processing research query", extra={"query": normalized_query})
        
        # Call agent service directly - get raw result
        raw_result = self.agent_service.search(normalized_query, options or {})
        return raw_result
