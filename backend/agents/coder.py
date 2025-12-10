"""Coder agent"""

from backend.agents.base import BaseAgent, AgentResult
from backend.models.task import Task
from backend.models.agent import AgentCapability


class CoderAgent(BaseAgent):
    """Code generation agent"""

    agent_type = "coder"
    capabilities = [AgentCapability.CODING]

    async def process(self, task: Task) -> AgentResult:
        """Generate code solution"""
        
        # Autonomous web search for API docs and best practices
        web_context = ""
        try:
            # Extract key technical terms for search
            search_query = f"programming {task.description[:150]} best practices"
            web_results = await self.auto_web_search(search_query, max_results=3)
            if web_results:
                web_context = f"""
<web_research>
Recent documentation and best practices:
{web_results}
</web_research>
"""
        except Exception as e:
            print(f"CoderAgent web search skipped: {e}")
        
        prompt = f"""<role>
You are a {self.agent_type.capitalize()}, an expert software engineer collaborating 
with other agents to solve complex tasks.
</role>

<context>
You are part of a multi-agent team. Other agents may review or build upon your code.
If you cannot fully complete the implementation, provide what you can so another 
agent can continue. If this is the final answer, prefix with: FINAL ANSWER
</context>
{web_context}
<pre_generation_checklist>
Before writing code:
1. Confirm you understand ALL requirements from the task
2. Identify edge cases: empty inputs, invalid types, boundary conditions
3. Consider error handling requirements
4. Plan the implementation approach
</pre_generation_checklist>

<task>
{task.description}
</task>

<additional_context>
{task.context or 'None provided'}
</additional_context>

<generation_standards>
- Write clean, readable, well-structured code
- Include error handling for edge cases
- Add comments only for non-obvious logic
- Follow best practices for the language/framework
</generation_standards>

<output_format>
Provide your response in this structure:
1. APPROACH: Brief description of implementation strategy
2. CODE: Complete, runnable code
3. EDGE CASES: List of handled edge cases
4. USAGE: Example usage
5. NOTES: Any important considerations or limitations
</output_format>"""
        content = await self._llm_call(prompt)

        return AgentResult(
            agent_id=self.id,
            task_id=task.id,
            content=content,
            confidence=0.8,
        )

