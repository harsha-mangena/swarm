"""Supervisor Agent - Watches, guides, and critiques other agents' work"""
import json
import re
from typing import Dict, Any, Optional
from backend.agents.base import BaseAgent, AgentResult
from backend.models.task import Task
from backend.prompts import get_prompt, ReworkDecision


class SupervisorAgent(BaseAgent):
    """
    Supervisor agent that reviews and critiques other agents' work.
    Created automatically for every task to ensure quality control.
    Uses structured prompts for consistent, high-quality feedback.
    """
    
    agent_type = "supervisor"
    quality_threshold = 7.0  # Minimum score to accept without rework
    max_rework_attempts = 2  # Maximum reworks per agent
    
    def __init__(self, agent_id: str, provider: str = "google", **kwargs):
        super().__init__(
            agent_id=agent_id,
            provider=provider,
            **kwargs
        )
        self._rework_counts: Dict[str, int] = {}  # Track reworks per agent
    
    async def process(self, task: Task) -> AgentResult:
        """
        Process task - supervisor provides initial task assessment
        defining quality criteria for the task.
        """
        prompt = get_prompt(
            "supervisor_initial",
            task_description=task.description
        )
        
        assessment = await self._llm_call(prompt)
        
        return AgentResult(
            agent_id=self.id,
            task_id=task.id,
            agent_type=self.agent_type,
            content=assessment,
            metadata={"role": "initial_assessment"}
        )
    
    async def critique_agent_work(
        self, 
        agent_type: str, 
        agent_id: str,
        agent_output: str, 
        task_description: str,
        quality_criteria: str = ""
    ) -> Dict[str, Any]:
        """
        Critique another agent's work and provide feedback.
        Uses the enhanced supervisor_critique prompt for structured output.
        
        Returns:
            Dict with 'critique', 'score', 'decision', 'rework_instructions'
        """
        prompt = get_prompt(
            "supervisor_critique",
            agent_type=agent_type,
            task_description=task_description,
            agent_output=agent_output,
            quality_criteria=quality_criteria or "Standard quality criteria apply"
        )
        
        critique_text = await self._llm_call(prompt)
        
        # Try to parse as JSON first
        evaluation = self._parse_structured_response(critique_text)
        
        # Get score and decision
        score = evaluation.get("overall_score", self._extract_score(critique_text))
        
        # Create ReworkDecision
        rework_decision = ReworkDecision.from_evaluation(evaluation, self.quality_threshold)
        
        # Track rework attempts
        if rework_decision.action == "REWORK":
            self._rework_counts[agent_id] = self._rework_counts.get(agent_id, 0) + 1
            if self._rework_counts[agent_id] > self.max_rework_attempts:
                # Force accept if max reworks exceeded
                rework_decision = ReworkDecision(
                    action="ACCEPT",
                    reason=f"Max rework attempts ({self.max_rework_attempts}) exceeded. Accepting with current quality.",
                    focus_areas=[],
                    score=score
                )
                print(f"[Supervisor] Agent {agent_id} - max reworks exceeded, forcing accept")
        
        # Log decision
        if rework_decision.action == "REWORK":
            print(f"[Supervisor] Agent {agent_type} ({agent_id}) scored {score:.1f}/10 - triggering rework")
        else:
            print(f"[Supervisor] Agent {agent_type} ({agent_id}) scored {score:.1f}/10 - {rework_decision.action.lower()}")
        
        return {
            "agent_id": agent_id,
            "agent_type": agent_type,
            "critique": critique_text,
            "score": score,
            "decision": rework_decision.action,
            "rework_required": rework_decision.action == "REWORK",
            "rework_instructions": {
                "reason": rework_decision.reason,
                "focus_areas": rework_decision.focus_areas
            },
            "evaluation": evaluation,
            "supervisor_id": self.id
        }
    
    def _parse_structured_response(self, response: str) -> Dict[str, Any]:
        """Parse structured JSON response from supervisor critique."""
        # Try to extract JSON from response
        try:
            # Look for JSON block
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
        
        # Fallback: extract key fields manually
        evaluation = {
            "overall_score": self._extract_score(response),
            "verdict": self._extract_decision(response),
            "rework_required": False,
            "rework_instructions": {
                "priority_fixes": [],
                "specific_guidance": ""
            }
        }
        
        # Determine rework_required from verdict
        verdict = evaluation["verdict"]
        if verdict in ["NEEDS_REWORK", "REVISE", "REJECT"]:
            evaluation["rework_required"] = True
        
        # Extract suggestions as priority fixes
        suggestions = self._extract_suggestions(response)
        if suggestions:
            evaluation["rework_instructions"]["priority_fixes"] = suggestions
        
        return evaluation
    
    def _extract_score(self, critique: str) -> float:
        """Extract numerical score from critique text"""
        # Look for patterns like "Score: 7/10" or "8/10" or "overall_score: 7.5"
        patterns = [
            r'overall_score["\s:]+(\d+(?:\.\d+)?)',
            r'score[:\s]+(\d+(?:\.\d+)?)/10',
            r'(\d+(?:\.\d+)?)/10',
            r'rate[sd]?\s+(\d+(?:\.\d+)?)',
            r'score[:\s]+(\d+(?:\.\d+)?)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, critique.lower())
            if match:
                try:
                    score = float(match.group(1))
                    if score > 10:
                        score = score / 10
                    return min(10.0, max(0.0, score))
                except (ValueError, IndexError):
                    continue
        
        # Default to 7.0 if no score found
        return 7.0

    def _extract_decision(self, critique: str) -> str:
        """Extract verdict/decision from critique text"""
        text = critique.lower()
        patterns = [
            r'"verdict"[:\s]+"([^"]+)"',
            r'verdict[:\s]+(accept|needs_rework|needs_minor_improvement|reject)',
            r'rework_decision[:\s]+(accept|revise|reject)',
            r'decision[:\s]+(accept|revise|reject)',
        ]
        for pattern in patterns:
            m = re.search(pattern, text)
            if m:
                verdict = m.group(1).upper().replace(" ", "_")
                # Normalize to expected values
                if verdict in ["REVISE", "NEEDS_REWORK", "NEEDS_MINOR_IMPROVEMENT"]:
                    return "NEEDS_REWORK"
                return verdict
        
        # Use score thresholds if no explicit decision
        score = self._extract_score(critique)
        if score >= 8.0:
            return "ACCEPT"
        elif score >= 5.0:
            return "NEEDS_REWORK"
        return "REJECT"
    
    def _extract_suggestions(self, critique: str) -> list:
        """Extract improvement suggestions from critique text"""
        suggestions = []
        
        # Look for numbered suggestions or bullet points
        patterns = [
            r'\d+\.\s*([^\n]+)',  # Numbered lists
            r'[-•]\s*([^\n]+)',   # Bullet points
            r'suggestion[s]?[:\s]+([^\n]+)',  # Explicit suggestions
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, critique, re.IGNORECASE)
            for match in matches:
                if len(match) > 10:  # Filter out very short matches
                    suggestions.append(match.strip())
        
        return suggestions[:5]  # Return top 5 suggestions
    
    def reset_rework_count(self, agent_id: str):
        """Reset rework count for an agent (e.g., when starting new task)"""
        if agent_id in self._rework_counts:
            del self._rework_counts[agent_id]
    
    def get_rework_count(self, agent_id: str) -> int:
        """Get current rework count for an agent"""
        return self._rework_counts.get(agent_id, 0)
