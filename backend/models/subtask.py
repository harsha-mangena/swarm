"""SubTask models for tracking individual work units within a task"""

from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import uuid4
from pydantic import BaseModel, Field


class SubTaskStatus(str, Enum):
    """SubTask execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class SubTask(BaseModel):
    """Individual work unit within a task"""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    parent_task_id: str
    description: str
    agent_id: Optional[str] = None
    agent_type: str  # researcher, analyst, coder, etc.
    status: SubTaskStatus = SubTaskStatus.PENDING
    result: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ValidationResult(BaseModel):
    """Result from debate/validation phase"""
    
    agent_id: str
    critique: str
    score: float  # 0-10
    strengths: List[str] = []
    weaknesses: List[str] = []
    suggestions: List[str] = []


class TaskValidation(BaseModel):
    """Complete validation phase results"""
    
    validations: List[ValidationResult] = []
    consensus_reached: bool = False
    final_score: float = 0.0
    summary: str = ""
