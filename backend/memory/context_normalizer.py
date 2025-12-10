"""Provider-aware context compression"""

from typing import Dict, List, Any
import tiktoken

from backend.config import settings


class ContextNormalizer:
    """Handle context window differences across providers"""

    PROVIDER_LIMITS = {
        "gemini-1.5-pro": 1_000_000,
        "gemini-1.5-flash": 1_000_000,
        "claude-3-sonnet": 200_000,
        "claude-3-haiku": 200_000,
        "claude-3-5-sonnet-20241022": 200_000,
        "claude-3-5-haiku-20241022": 200_000,
        "gpt-4o": 128_000,
        "gpt-4o-mini": 128_000,
        "llama3.2": 8_192,
        "mistral": 32_768,
        "auto": 100_000,  # Default conservative limit
    }

    def __init__(self):
        self.encoding = tiktoken.get_encoding("cl100k_base")

    def _count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return len(self.encoding.encode(text))

    async def prepare_context(
        self, full_context: Dict[str, Any], target_model: str
    ) -> Dict[str, Any]:
        """Compress context for target model's limits"""

        # Normalize model name
        model_key = target_model.lower()
        if "gemini" in model_key:
            model_key = "gemini-1.5-pro"
        elif "claude" in model_key:
            model_key = "claude-3-5-sonnet-20241022"
        elif "gpt" in model_key:
            model_key = "gpt-4o"
        elif "llama" in model_key:
            model_key = "llama3.2"

        limit = self.PROVIDER_LIMITS.get(model_key, 8_000)
        current_tokens = self._estimate_tokens(full_context)

        if current_tokens <= limit * 0.9:  # 90% threshold
            return full_context

        # Progressive compression strategy
        compressed = full_context.copy()

        # 1. Summarize older messages
        if "conversation_history" in compressed:
            compressed["conversation_history"] = self._summarize_history(
                compressed["conversation_history"], keep_recent=5
            )

        # 2. Truncate retrieved documents
        if "retrieved_context" in compressed:
            compressed["retrieved_context"] = self._truncate_documents(
                compressed["retrieved_context"], max_tokens=limit // 4
            )

        # 3. Limit memory entries
        if "memories" in compressed and isinstance(compressed["memories"], list):
            max_memories = limit // 1000  # Rough estimate
            compressed["memories"] = compressed["memories"][:max_memories]

        return compressed

    def _estimate_tokens(self, context: Dict[str, Any]) -> int:
        """Estimate total tokens in context"""
        total = 0
        for key, value in context.items():
            if isinstance(value, str):
                total += self._count_tokens(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, str):
                        total += self._count_tokens(item)
                    elif isinstance(item, dict):
                        total += self._estimate_tokens(item)
            elif isinstance(value, dict):
                total += self._estimate_tokens(value)
        return total

    def _summarize_history(
        self, history: List[Dict], keep_recent: int = 5
    ) -> List[Dict]:
        """Summarize older messages, keep recent ones"""
        if len(history) <= keep_recent:
            return history
        # Keep recent, summarize older
        recent = history[-keep_recent:]
        older = history[:-keep_recent]
        # Simple truncation for now - could use LLM summarization
        summarized = [
            {
                "role": "system",
                "content": f"Previous conversation ({len(older)} messages) summarized...",
            }
        ]
        return summarized + recent

    def _truncate_documents(
        self, documents: List[Dict], max_tokens: int
    ) -> List[Dict]:
        """Truncate documents to fit token limit"""
        result = []
        current_tokens = 0
        for doc in documents:
            content = doc.get("content", "")
            doc_tokens = self._count_tokens(content)
            if current_tokens + doc_tokens > max_tokens:
                # Truncate this document
                remaining = max_tokens - current_tokens
                if remaining > 100:  # Only if meaningful space left
                    truncated = self._truncate_text(content, remaining)
                    doc["content"] = truncated
                    result.append(doc)
                break
            result.append(doc)
            current_tokens += doc_tokens
        return result

    def _truncate_text(self, text: str, max_tokens: int) -> str:
        """Truncate text to max tokens"""
        tokens = self.encoding.encode(text)
        if len(tokens) <= max_tokens:
            return text
        truncated = tokens[:max_tokens]
        return self.encoding.decode(truncated) + "... [truncated]"

