"""Depth requirements for anti-shallow output prompts"""

DEPTH_REQUIREMENTS = """
<depth_requirements>
Your response MUST include:
- Specific data points, numbers, statistics, or concrete examples
- Edge cases, exceptions, and counterarguments
- At least 600 words for substantive analysis
- Actionable, specific recommendations (not generic advice)

DO NOT summarize - provide COMPREHENSIVE analysis with full detail.
</depth_requirements>
"""

FORBIDDEN_OUTPUTS = """
<forbidden_phrases>
NEVER use these shallow phrases without expanding on them:
- "It depends" → Always explain WHAT it depends on
- "There are many factors" → LIST the specific factors
- "In general" → Be SPECIFIC, not general
- "Various approaches exist" → NAME and explain the approaches
- "Consider your needs" → Specify WHICH needs and HOW to evaluate them
- "Do your research" → Provide the research findings
- "Consult an expert" → Provide expert-level analysis yourself
</forbidden_phrases>
"""

STRUCTURED_OUTPUT_REQUIREMENTS = """
<output_structure>
Your response MUST include these sections (adapt headings to context):

1. EXECUTIVE SUMMARY (2-3 sentences)
   - Key finding or recommendation

2. DETAILED ANALYSIS (main body)
   - Specific facts with citations
   - Data points and examples
   - Comparisons where relevant

3. EDGE CASES & CONSIDERATIONS
   - When this doesn't apply
   - Important caveats
   - Alternative perspectives

4. ACTIONABLE RECOMMENDATIONS
   - Specific next steps
   - Priority order
   - Expected outcomes
</output_structure>
"""

# Combined prompt injection for all agents
QUALITY_PROMPT_ADDITIONS = f"""
{DEPTH_REQUIREMENTS}
{FORBIDDEN_OUTPUTS}
{STRUCTURED_OUTPUT_REQUIREMENTS}
"""
