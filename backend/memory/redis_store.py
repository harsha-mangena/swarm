"""Redis working memory"""

import json
from typing import Optional, List, Dict, Any, AsyncIterator
import redis.asyncio as aioredis

from backend.config import settings


class RedisMemoryStore:
    """Working memory with TTL and event streaming"""

    TTL_CONFIG = {
        "task_context": 3600,  # 1 hour
        "agent_state": 1800,  # 30 minutes
        "decision_cache": 300,  # 5 minutes
        "checkpoint": 86400,  # 24 hours
    }

    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None

    async def connect(self):
        """Connect to Redis"""
        self.redis = await aioredis.from_url(
            settings.redis_url, encoding="utf-8", decode_responses=True
        )

    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis:
            await self.redis.close()

    async def set(self, key: str, value: str, ttl: Optional[int] = None):
        """Set key-value with optional TTL"""
        if not self.redis:
            await self.connect()
        if ttl:
            await self.redis.setex(key, ttl, value)
        else:
            await self.redis.set(key, value)

    async def get(self, key: str) -> Optional[str]:
        """Get value by key"""
        if not self.redis:
            await self.connect()
        return await self.redis.get(key)

    async def get_recent(self, namespace: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent entries from namespace"""
        if not self.redis:
            await self.connect()
        pattern = f"{namespace}:*"
        keys = []
        async for key in self.redis.scan_iter(match=pattern):
            keys.append(key)
            if len(keys) >= limit:
                break
        if not keys:
            return []
        values = await self.redis.mget(keys)
        return [
            {"id": key.split(":")[-1], "content": val, "key": key}
            for key, val in zip(keys, values)
            if val
        ]

    async def publish_memory_update(self, task_id: str, update: Dict[str, Any]):
        """Publish to Redis Stream for real-time sync"""
        if not self.redis:
            await self.connect()
        await self.redis.xadd(
            f"memory:stream:{task_id}",
            {"data": json.dumps(update)},
            maxlen=1000,  # Keep last 1000 updates
        )

    async def subscribe_to_task(self, task_id: str) -> AsyncIterator[Dict[str, Any]]:
        """Subscribe to memory updates for a task"""
        if not self.redis:
            await self.connect()
        last_id = "$"
        while True:
            messages = await self.redis.xread(
                streams={f"memory:stream:{task_id}": last_id}, block=5000
            )
            for stream, msgs in messages:
                for msg_id, data in msgs:
                    last_id = msg_id
                    yield json.loads(data.get("data", "{}"))

