from __future__ import annotations

import hashlib
import json
import logging
from typing import Any

import redis

from app.core.config import CACHE_TTL_SECONDS, REDIS_URL

logger = logging.getLogger(__name__)


class CacheClient:
    """Redis cache client with graceful degradation."""

    def __init__(self) -> None:
        self._client: redis.Redis[str] | None = None
        self._enabled = False

        if REDIS_URL:
            try:
                self._client = redis.from_url(REDIS_URL, decode_responses=True)
                # Test connection
                self._client.ping()
                self._enabled = True
                logger.info("Redis cache enabled", extra={"redis_url": REDIS_URL})
            except Exception as e:
                logger.warning(
                    "Redis cache unavailable, proceeding without caching",
                    extra={"error": str(e)},
                )
                self._client = None
                self._enabled = False
        else:
            logger.info("Redis URL not configured, caching disabled")

    def get(self, key: str) -> dict[str, Any] | None:
        """Get cached value by key."""
        if not self._enabled or not self._client:
            return None

        try:
            cached = self._client.get(key)
            if cached:
                logger.debug("Cache hit", extra={"key": key})
                return json.loads(cached)
            logger.debug("Cache miss", extra={"key": key})
            return None
        except Exception as e:
            logger.warning("Cache get failed", extra={"key": key, "error": str(e)})
            return None

    def set(self, key: str, value: dict[str, Any], ttl: int | None = None) -> bool:
        """Set cached value with TTL."""
        if not self._enabled or not self._client:
            return False

        try:
            ttl = ttl or CACHE_TTL_SECONDS
            serialized = json.dumps(value, default=str)
            self._client.setex(key, ttl, serialized)
            logger.debug("Cache set", extra={"key": key, "ttl": ttl})
            return True
        except Exception as e:
            logger.warning("Cache set failed", extra={"key": key, "error": str(e)})
            return False

    def generate_key(self, query: str) -> str:
        """Generate cache key from query."""
        normalized = " ".join(query.lower().split())
        hash_obj = hashlib.sha256(normalized.encode())
        return f"research:{hash_obj.hexdigest()}"

    @property
    def enabled(self) -> bool:
        """Check if caching is enabled."""
        return self._enabled






