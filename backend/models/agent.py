"""Agent models"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel


class AgentStatus(str, Enum):
    """Agent status"""

    IDLE = "idle"
    PROCESSING = "processing"
    ERROR = "error"


class AgentCapability(str, Enum):
    """Agent capabilities"""

    RESEARCH = "research"
    ANALYSIS = "analysis"
    CODING = "coding"
    REVIEW = "review"
    SYNTHESIS = "synthesis"


class Agent(BaseModel):
    """Agent model"""

    id: str
    name: str
    agent_type: str
    provider: str
    status: AgentStatus = AgentStatus.IDLE
    capabilities: List[AgentCapability] = []
    current_load: float = 0.0
    success_rate: Optional[float] = None
    color: str = "#8b5cf6"  # Default accent color

