"""Quality validation for agent outputs"""

import re
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class ValidationIssue(BaseModel):
    """A single validation issue"""
    message: str
    severity: str = "medium"  # low, medium, high
    suggestion: Optional[str] = None


class ValidationResult(BaseModel):
    """Result of quality validation"""
    passed: bool
    score: float = 0.0
    issues: List[ValidationIssue] = []
    details: Dict[str, Any] = {}


# Minimum lengths by task type
MIN_LENGTHS = {
    "research": 600,
    "analysis": 500,
    "code": 200,
    "review": 300,
    "synthesis": 800,
    "default": 400
}

# Required citation counts by task type
MIN_CITATIONS = {
    "research": 3,
    "analysis": 2,
    "default": 0
}


class QualityValidator:
    """Validates agent output quality before delivery"""
    
    def validate(
        self, 
        content: str, 
        task_type: str = "default",
        sources_provided: int = 0
    ) -> ValidationResult:
        """
        Validate output quality.
        
        Args:
            content: The agent output to validate
            task_type: Type of task (research, analysis, code, etc.)
            sources_provided: Number of sources provided to agent
            
        Returns:
            ValidationResult with pass/fail and issues
        """
        issues = []
        details = {}
        
        # 1. Length check
        min_length = MIN_LENGTHS.get(task_type, MIN_LENGTHS["default"])
        word_count = len(content.split())
        details["word_count"] = word_count
        
        if word_count < min_length * 0.6:  # Very short
            issues.append(ValidationIssue(
                message=f"Output too short: {word_count} words (expected ~{min_length}+)",
                severity="high",
                suggestion="Rework with more depth and detail"
            ))
        elif word_count < min_length:
            issues.append(ValidationIssue(
                message=f"Output may be brief: {word_count} words (recommended {min_length}+)",
                severity="low"
            ))
        
        # 2. Citation check (if sources were provided)
        if sources_provided > 0:
            citations = re.findall(r'\[(\d+)\]', content)
            unique_citations = len(set(citations))
            details["citation_count"] = unique_citations
            
            min_citations = MIN_CITATIONS.get(task_type, MIN_CITATIONS["default"])
            if unique_citations < min_citations and min_citations > 0:
                issues.append(ValidationIssue(
                    message=f"Insufficient citations: {unique_citations} found, expected {min_citations}+",
                    severity="medium",
                    suggestion="Include more source citations [1], [2], etc."
                ))
        
        # 3. Truncation check
        truncation_indicators = [
            content.rstrip().endswith("..."),
            content.rstrip().endswith("…"),
            "continue" in content.lower()[-100:] and content.rstrip()[-1] not in ".!?",
            len(content) > 100 and content.rstrip()[-1] not in ".!?:;])",
        ]
        
        if any(truncation_indicators):
            issues.append(ValidationIssue(
                message="Output appears truncated (incomplete ending)",
                severity="high",
                suggestion="Continue generation or increase max_tokens"
            ))
            details["appears_truncated"] = True
        
        # 4. Shallow content check
        shallow_phrases = [
            "it depends",
            "there are many factors",
            "in general",
            "various approaches",
            "do your research",
            "consult an expert",
        ]
        
        shallow_count = sum(1 for phrase in shallow_phrases if phrase in content.lower())
        if shallow_count >= 3:
            issues.append(ValidationIssue(
                message=f"Output contains {shallow_count} shallow phrases",
                severity="medium",
                suggestion="Replace generic phrases with specific analysis"
            ))
            details["shallow_phrase_count"] = shallow_count
        
        # 5. Structure check (for research/analysis)
        if task_type in ["research", "analysis", "synthesis"]:
            expected_sections = ["summary", "analysis", "recommendation"]
            found_sections = sum(1 for s in expected_sections if s in content.lower())
            details["section_coverage"] = f"{found_sections}/{len(expected_sections)}"
            
            if found_sections < 2:
                issues.append(ValidationIssue(
                    message="Missing expected sections (summary/analysis/recommendations)",
                    severity="low",
                    suggestion="Add structured sections for clarity"
                ))
        
        # Calculate score
        high_issues = len([i for i in issues if i.severity == "high"])
        medium_issues = len([i for i in issues if i.severity == "medium"])
        low_issues = len([i for i in issues if i.severity == "low"])
        
        # Score: start at 100, deduct for issues
        score = max(0, 100 - (high_issues * 30) - (medium_issues * 15) - (low_issues * 5))
        
        # Pass if no high-severity issues and score >= 50
        passed = high_issues == 0 and score >= 50
        
        return ValidationResult(
            passed=passed,
            score=score / 100,
            issues=issues,
            details=details
        )
    
    def get_rework_feedback(self, result: ValidationResult) -> str:
        """Generate feedback for rework based on validation issues"""
        if result.passed:
            return ""
        
        feedback_parts = ["Your previous output needs improvement:"]
        
        for issue in result.issues:
            feedback_parts.append(f"- {issue.message}")
            if issue.suggestion:
                feedback_parts.append(f"  → {issue.suggestion}")
        
        return "\n".join(feedback_parts)
