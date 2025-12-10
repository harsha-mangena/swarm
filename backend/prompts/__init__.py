"""
SwarmOS Prompts Module
======================

Optimized prompts for multi-agent orchestration with anti-groupthink mechanisms.

Usage:
    from backend.prompts import get_prompt, get_schema, build_agent_prompt

    # Get a prompt with variables
    prompt = get_prompt("task_analysis", task_description="...")

    # Get schema for structured output
    schema = get_schema("researcher")

    # Build complete agent prompt
    agent_prompt = build_agent_prompt(
        agent_type="Energy Markets Analyst",
        task_description="...",
        context={...},
        contrarian_mandate="Challenge the consensus on renewable energy timelines"
    )
"""

from .prompts import (
    get_prompt,
    build_agent_prompt,
    ReworkDecision,
    PromptCategory,
    
    # Individual prompts for direct access
    TASK_ANALYSIS_PROMPT,
    TASK_DECOMPOSITION_PROMPT,
    QUERY_EXPANSION_PROMPT,
    RESEARCHER_PROMPT,
    ANALYST_PROMPT,
    CODER_PROMPT,
    REVIEWER_PROMPT,
    SYNTHESIZER_PROMPT,
    DEBATE_PROPOSAL_PROMPT,
    DEBATE_CRITIQUE_PROMPT,
    DEBATE_REBUTTAL_PROMPT,
    DEBATE_VOTING_PROMPT,
    DEBATE_JUDGE_PROMPT,
    QUALITY_EVALUATION_PROMPT,
    REWORK_INSTRUCTION_PROMPT,
    VALIDATION_PROMPT,
    SUPERVISOR_INITIAL_ASSESSMENT_PROMPT,
    SUPERVISOR_CRITIQUE_PROMPT,
)

from .schemas import (
    get_schema,
    get_openai_response_format,
    get_gemini_response_schema,
    validate_output,
    SCHEMAS,
)

__all__ = [
    # Main functions
    "get_prompt",
    "build_agent_prompt",
    "get_schema",
    "get_openai_response_format",
    "get_gemini_response_schema",
    "validate_output",
    
    # Classes
    "ReworkDecision",
    "PromptCategory",
    
    # Schema registry
    "SCHEMAS",
    
    # Individual prompts
    "TASK_ANALYSIS_PROMPT",
    "TASK_DECOMPOSITION_PROMPT",
    "QUERY_EXPANSION_PROMPT",
    "RESEARCHER_PROMPT",
    "ANALYST_PROMPT",
    "CODER_PROMPT",
    "REVIEWER_PROMPT",
    "SYNTHESIZER_PROMPT",
    "DEBATE_PROPOSAL_PROMPT",
    "DEBATE_CRITIQUE_PROMPT",
    "DEBATE_REBUTTAL_PROMPT",
    "DEBATE_VOTING_PROMPT",
    "DEBATE_JUDGE_PROMPT",
    "QUALITY_EVALUATION_PROMPT",
    "REWORK_INSTRUCTION_PROMPT",
    "VALIDATION_PROMPT",
    "SUPERVISOR_INITIAL_ASSESSMENT_PROMPT",
    "SUPERVISOR_CRITIQUE_PROMPT",
]

print("✓ Prompts module loaded")
