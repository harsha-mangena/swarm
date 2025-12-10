"""Memory models"""

from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel


class MemoryScope(str, Enum):
    """Memory scope levels"""

    GLOBAL = "global"
    TASK = "task"
    AGENT = "agent"


class MemoryEntry(BaseModel):
    """Memory entry"""

    id: str
    scope: MemoryScope
    namespace: str  # e.g., "task:abc123" or "agent:researcher-1"
    content: str
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = {}
    ttl_seconds: Optional[int] = None
    created_at: Optional[str] = None

