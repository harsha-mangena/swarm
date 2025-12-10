"""Unified memory interface"""

from typing import List, Optional, Dict, Any
import json

from backend.models.memory import MemoryEntry, MemoryScope
from .redis_store import RedisMemoryStore
from .vector_store import QdrantMemoryStore
from .postgres_store import PostgresMemoryStore
from .context_normalizer import ContextNormalizer


class MemoryManager:
    """Unified interface for all memory operations"""

    def __init__(
        self,
        redis_store: Optional[RedisMemoryStore],
        vector_store: Optional[QdrantMemoryStore],
        postgres_store: Optional[PostgresMemoryStore],
        normalizer: ContextNormalizer,
    ):
        self.redis = redis_store
        self.qdrant = vector_store
        self.postgres = postgres_store
        self.normalizer = normalizer

    @property
    def postgres_store(self) -> Optional[PostgresMemoryStore]:
        """Expose PostgresMemoryStore for direct access"""
        return self.postgres

    async def write(self, entry: MemoryEntry) -> str:
        """Write to appropriate store based on scope"""

        # Working memory (Redis) - ephemeral, fast access
        if entry.ttl_seconds and self.redis:
            try:
                await self.redis.set(
                    f"{entry.scope.value}:{entry.namespace}:{entry.id}",
                    entry.content,
                    ttl=entry.ttl_seconds,
                )
            except:
                pass

        # Semantic memory (Qdrant) - searchable by meaning
        if entry.embedding and self.qdrant:
            try:
                await self.qdrant.upsert(
                    collection_name=entry.namespace,
                    point_id=entry.id,
                    vector=entry.embedding,
                    payload={"content": entry.content, **entry.metadata},
                )
            except:
                pass

        # Persistent history (PostgreSQL)
        if self.postgres:
            try:
                await self.postgres.save(entry)
            except:
                pass

        # Publish update
        if self.redis:
            try:
                await self.redis.publish_memory_update(
                    entry.namespace.split(":")[-1] if ":" in entry.namespace else "global",
                    {"action": "write", "entry_id": entry.id},
                )
            except:
                pass

        return entry.id

    async def read(
        self,
        task_id: str,
        agent_id: str,
        query_embedding: Optional[List[float]] = None,
        provider: str = "auto",
        limit: int = 10,
    ) -> Dict[str, Any]:
        """Read with provider-aware context compression"""

        # Gather from all scopes with priority
        agent_memories = []
        task_memories = []
        global_memories = []

        if query_embedding and self.qdrant:
            try:
                agent_memories = await self.qdrant.search(
                    collection_name=f"agent:{agent_id}",
                    query_vector=query_embedding,
                    limit=3,
                )
                task_memories = await self.qdrant.search(
                    collection_name=f"task:{task_id}",
                    query_vector=query_embedding,
                    limit=5,
                )
                global_memories = await self.qdrant.search(
                    collection_name="global",
                    query_vector=query_embedding,
                    limit=3,
                )
            except:
                agent_memories = []
                task_memories = []
                global_memories = []
        else:
            # Fallback to Redis for recent entries
            if self.redis:
                try:
                    agent_memories = await self.redis.get_recent(f"agent:{agent_id}", limit=3)
                    task_memories = await self.redis.get_recent(f"task:{task_id}", limit=5)
                    global_memories = await self.redis.get_recent("global", limit=3)
                except:
                    agent_memories = []
                    task_memories = []
                    global_memories = []
            else:
                agent_memories = []
                task_memories = []
                global_memories = []

        combined = self._deduplicate_and_rank(
            agent_memories + task_memories + global_memories
        )

        # Compress based on provider context limits
        return await self.normalizer.prepare_context(combined, provider)

    async def query(
        self,
        namespace: str,
        scope: Optional[MemoryScope] = None,
        limit: int = 50,
    ) -> List[MemoryEntry]:
        """Query memory entries"""
        if self.postgres:
            try:
                return await self.postgres.query(namespace=namespace, scope=scope, limit=limit)
            except:
                return []
        return []

    async def subscribe_to_task(self, task_id: str):
        """Subscribe to memory updates for a task"""
        if self.redis:
            try:
                async for update in self.redis.subscribe_to_task(task_id):
                    yield update
            except:
                pass

    def _deduplicate_and_rank(self, memories: List[Dict]) -> List[Dict]:
        """Remove duplicates and rank by relevance"""
        seen = set()
        unique = []
        for mem in memories:
            content_id = mem.get("id") or mem.get("content", "")[:100]
            if content_id not in seen:
                seen.add(content_id)
                unique.append(mem)
        return unique

