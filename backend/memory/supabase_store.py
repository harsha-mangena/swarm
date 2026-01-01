"""Supabase storage for tasks and memory"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from backend.supabase_client import get_supabase_admin, is_supabase_configured
from backend.models.memory import MemoryEntry, MemoryScope


class SupabaseStore:
    """Supabase-based storage for tasks and memory entries.
    Replaces PostgresMemoryStore when Supabase is configured.
    """

    def __init__(self):
        self._client = None

    @property
    def client(self):
        """Lazy initialization of Supabase client"""
        if self._client is None:
            self._client = get_supabase_admin()
        return self._client

    async def connect(self):
        """Connect to Supabase (no-op, client is lazy initialized)"""
        pass

    async def disconnect(self):
        """Disconnect from Supabase (no-op)"""
        pass

    # Task methods
    async def save_task(self, task_data: Dict[str, Any], user_id: Optional[str] = None):
        """Save or update a task"""
        # Convert datetime objects to ISO strings
        data = {}
        for key, value in task_data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
            else:
                data[key] = value
        
        # Add user_id for multi-tenancy
        if user_id:
            data["user_id"] = user_id
        
        # Check if task exists
        existing = self.client.table("tasks").select("id").eq("id", data["id"]).execute()
        
        if existing.data:
            # Update existing
            data["updated_at"] = datetime.utcnow().isoformat()
            self.client.table("tasks").update(data).eq("id", data["id"]).execute()
        else:
            # Create new
            self.client.table("tasks").insert(data).execute()

    async def get_task(self, task_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get a task by ID"""
        query = self.client.table("tasks").select("*").eq("id", task_id)
        
        # Filter by user if provided
        if user_id:
            query = query.eq("user_id", user_id)
        
        result = query.execute()
        
        if not result.data:
            return None
        
        return result.data[0]

    async def list_tasks(
        self, 
        status: Optional[str] = None, 
        limit: int = 20, 
        offset: int = 0,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List tasks with optional filtering"""
        query = self.client.table("tasks").select("*")
        
        # Filter by user if provided
        if user_id:
            query = query.eq("user_id", user_id)
        
        if status:
            query = query.eq("status", status)
        
        query = query.order("created_at", desc=True).limit(limit).offset(offset)
        
        result = query.execute()
        return result.data or []

    async def delete_task(self, task_id: str, user_id: Optional[str] = None) -> bool:
        """Delete a task"""
        query = self.client.table("tasks").delete().eq("id", task_id)
        
        if user_id:
            query = query.eq("user_id", user_id)
        
        result = query.execute()
        return bool(result.data)

    # Memory methods (for compatibility with MemoryManager)
    async def save(self, entry: MemoryEntry):
        """Save memory entry"""
        data = {
            "id": entry.id,
            "scope": entry.scope.value,
            "namespace": entry.namespace,
            "content": entry.content,
            "entry_metadata": entry.metadata,
            "created_at": datetime.utcnow().isoformat(),
        }
        
        self.client.table("memory_entries").upsert(data).execute()

    async def query(
        self,
        namespace: str,
        scope: Optional[MemoryScope] = None,
        limit: int = 50,
    ) -> List[MemoryEntry]:
        """Query memory entries"""
        query = self.client.table("memory_entries").select("*").eq("namespace", namespace)
        
        if scope:
            query = query.eq("scope", scope.value)
        
        query = query.order("created_at", desc=True).limit(limit)
        
        result = query.execute()
        
        return [
            MemoryEntry(
                id=r["id"],
                scope=MemoryScope(r["scope"]),
                namespace=r["namespace"],
                content=r["content"],
                metadata=r.get("entry_metadata") or {},
            )
            for r in (result.data or [])
        ]
