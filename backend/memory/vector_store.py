"""Qdrant vector store"""

from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient, AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue

from backend.config import settings


class QdrantMemoryStore:
    """Semantic memory with per-task collections"""

    def __init__(self):
        self.client: Optional[AsyncQdrantClient] = None

    async def connect(self):
        """Connect to Qdrant"""
        self.client = AsyncQdrantClient(url=settings.qdrant_url)

    async def disconnect(self):
        """Disconnect from Qdrant"""
        if self.client:
            await self.client.close()

    async def create_task_collection(self, task_id: str):
        """Create isolated collection for task"""
        if not self.client:
            await self.connect()
        try:
            await self.client.create_collection(
                collection_name=f"task_{task_id}",
                vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
            )
        except Exception:
            # Collection may already exist
            pass

    async def upsert(
        self,
        collection_name: str,
        point_id: str,
        vector: List[float],
        payload: Dict[str, Any],
    ):
        """Upsert a point"""
        if not self.client:
            await self.connect()
        await self.client.upsert(
            collection_name=collection_name,
            points=[
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload,
                )
            ],
        )

    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Search with optional metadata filtering"""
        if not self.client:
            await self.connect()

        filter_conditions = None
        if filters:
            filter_conditions = Filter(
                must=[
                    FieldCondition(key=k, match=MatchValue(value=v))
                    for k, v in filters.items()
                ]
            )

        try:
            results = await self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                query_filter=filter_conditions,
                limit=limit,
            )
            return [
                {"id": str(r.id), "score": r.score, **r.payload}
                for r in results
            ]
        except Exception:
            # Collection may not exist
            return []

