"""Debate models"""

from enum import Enum
from typing import List, Dict, Optional
from pydantic import BaseModel


class DebatePhase(str, Enum):
    """Debate phases"""

    PROPOSAL = "proposal"
    CRITIQUE = "critique"
    REBUTTAL = "rebuttal"
    VOTING = "voting"
    JUDGMENT = "judgment"
    CONVERGED = "converged"


class Proposal(BaseModel):
    """Agent proposal"""

    agent_id: str
    content: str
    confidence: float
    evidence: List[str] = []
    round: int


class Critique(BaseModel):
    """Critique of a proposal"""

    critic_id: str
    target_proposal_id: str
    strengths: List[str] = []
    weaknesses: List[str] = []
    score: float  # 1-10
    round: int


class Vote(BaseModel):
    """Vote for a proposal"""

    voter_id: str
    selected_proposal_id: str
    reasoning: Optional[str] = None


class DebateState(BaseModel):
    """Debate state"""

    task_id: str
    topic: str
    proposals: List[Dict] = []
    critiques: List[Dict] = []
    rebuttals: List[Dict] = []
    votes: Dict[str, str] = {}  # agent_id -> voted_proposal_id
    scores: Dict[str, float] = {}  # proposal_id -> score
    round: int = 1
    max_rounds: int = 5
    phase: DebatePhase = DebatePhase.PROPOSAL
    winner: Optional[str] = None
    converged: bool = False

