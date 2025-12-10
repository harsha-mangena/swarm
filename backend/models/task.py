"""Task models"""

from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Task execution status"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    VALIDATING = "validating"  # Post-completion debate/validation
    DEBATING = "debating"  # Legacy - kept for compatibility
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Task(BaseModel):
    """Task model"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    description: str
    status: TaskStatus = TaskStatus.PENDING
    provider: str = "auto"
    context: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    tokens_used: Optional[int] = None
    agents_count: int = 0
    progress: Optional[float] = None
    debate_state: Optional[Dict[str, Any]] = None
    subtasks: List[Dict[str, Any]] = []  # List of subtask dicts
    validation_results: Optional[Dict[str, Any]] = None  # Debate/validation output

    class Config:
        from_attributes = True


class CreateTaskRequest(BaseModel):
    """Request to create a task"""

    description: str
    provider: str = "auto"
    auto_execute: bool = True
    context: Optional[Dict[str, Any]] = None


class TaskResponse(BaseModel):
    """Task creation response"""

    id: str
    status: TaskStatus
    description: str
    expansion: Optional[Dict[str, Any]] = None


class TaskSummary(BaseModel):
    """Task summary for lists"""

    id: str
    description: str
    status: TaskStatus
    provider: str
    created_at: datetime
    agents_count: int
    tokens_used: Optional[int] = None
    progress: Optional[float] = None

    @classmethod
    def from_orm(cls, task: Task) -> "TaskSummary":
        """Create from ORM model"""
        return cls(
            id=task.id,
            description=task.description,
            status=task.status,
            provider=task.provider,
            created_at=task.created_at,
            agents_count=task.agents_count,
            tokens_used=task.tokens_used,
            progress=task.progress,
        )


class TaskDetail(BaseModel):
    """Detailed task information"""

    id: str
    description: str
    status: TaskStatus
    provider: str
    context: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    tokens_used: Optional[int] = None
    agents_count: int
    progress: Optional[float] = None
    debate_state: Optional[Dict[str, Any]] = None

    @classmethod
    def from_orm(cls, task: Task) -> "TaskDetail":
        """Create from ORM model"""
        return cls(
            id=task.id,
            description=task.description,
            status=task.status,
            provider=task.provider,
            context=task.context,
            result=task.result,
            error=task.error,
            created_at=task.created_at,
            updated_at=task.updated_at,
            completed_at=task.completed_at,
            tokens_used=task.tokens_used,
            agents_count=task.agents_count,
            progress=task.progress,
            debate_state=task.debate_state,
        )

