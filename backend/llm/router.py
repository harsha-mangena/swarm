"""LiteLLM router wrapper"""

from typing import Optional, List, Dict, Any
from litellm import Router
from litellm import acompletion as litellm_acompletion

from backend.config import settings
from .circuit_breaker import CircuitBreaker


class SwarmOSRouter:
    """Unified LLM interface with fallbacks and circuit breakers"""

    def __init__(self):
        self.router = self._build_router()
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}

    def _build_router(self) -> Optional[Router]:
        """Configure LiteLLM router"""

        model_list = []

        # Ollama (local) - highest priority
        if settings.ollama_base_url:
            model_list.extend(
                [
                    {
                        "model_name": "local-fast",
                        "litellm_params": {
                            "model": "ollama/llama3.2",
                            "api_base": settings.ollama_base_url,
                        },
                        "model_info": {"priority": 1},
                    },
                    {
                        "model_name": "local-code",
                        "litellm_params": {
                            "model": "ollama/codellama",
                            "api_base": settings.ollama_base_url,
                        },
                        "model_info": {"priority": 1},
                    },
                ]
            )

        # Claude
        if settings.anthropic_api_key:
            model_list.extend(
                [
                    {
                        "model_name": "claude-sonnet",
                        "litellm_params": {
                            "model": "claude-3-5-sonnet-20241022",
                            "api_key": settings.anthropic_api_key,
                        },
                        "model_info": {"priority": 2},
                    },
                    {
                        "model_name": "claude-haiku",
                        "litellm_params": {
                            "model": "claude-3-5-haiku-20241022",
                            "api_key": settings.anthropic_api_key,
                        },
                        "model_info": {"priority": 2},
                    },
                ]
            )

        # Gemini
        if settings.google_api_key:
            model_list.extend(
                [
                    {
                        "model_name": "gemini-pro",
                        "litellm_params": {
                            "model": "gemini/gemini-1.5-pro",
                            "api_key": settings.google_api_key,
                        },
                        "model_info": {"priority": 2},
                    },
                    {
                        "model_name": "gemini-flash",
                        "litellm_params": {
                            "model": "gemini/gemini-2.0-flash-exp",  # Gemini 2.0 Flash Experimental
                            "api_key": settings.google_api_key,
                        },
                        "model_info": {"priority": 2},
                    },
                    {
                        "model_name": "gemini-flash-2",
                        "litellm_params": {
                            "model": "gemini/gemini-1.5-flash",  # Fallback to 1.5 Flash
                            "api_key": settings.google_api_key,
                        },
                        "model_info": {"priority": 3},
                    },
                ]
            )

        # OpenAI
        if settings.openai_api_key:
            model_list.extend(
                [
                    {
                        "model_name": "gpt-4o",
                        "litellm_params": {
                            "model": "gpt-4o",
                            "api_key": settings.openai_api_key,
                        },
                        "model_info": {"priority": 3},
                    },
                    {
                        "model_name": "gpt-4o-mini",
                        "litellm_params": {
                            "model": "gpt-4o-mini",
                            "api_key": settings.openai_api_key,
                        },
                        "model_info": {"priority": 3},
                    },
                ]
            )

        # OpenRouter (fallback)
        if settings.openrouter_api_key:
            model_list.append(
                {
                    "model_name": "openrouter-claude",
                    "litellm_params": {
                        "model": "openrouter/anthropic/claude-3-sonnet",
                        "api_key": settings.openrouter_api_key,
                    },
                    "model_info": {"priority": 4},
                }
            )

        if not model_list:
            return None

        fallbacks = []
        if any("claude" in m["model_name"] for m in model_list):
            fallbacks.append({"claude-sonnet": ["gpt-4o", "openrouter-claude"]})
        if any("gpt" in m["model_name"] for m in model_list):
            fallbacks.append({"gpt-4o": ["claude-sonnet", "gemini-pro"]})
        if any("local" in m["model_name"] for m in model_list):
            fallbacks.append({"local-fast": ["claude-haiku", "gpt-4o-mini"]})

        return Router(
            model_list=model_list,
            fallbacks=fallbacks if fallbacks else None,
            routing_strategy="simple-shuffle",
            num_retries=3,
            allowed_fails=3,
            cooldown_time=60,
        )

    def _get_provider(self, model: str) -> str:
        """Extract provider name from model"""
        if "claude" in model.lower():
            return "anthropic"
        elif "gemini" in model.lower():
            return "google"
        elif "gpt" in model.lower():
            return "openai"
        elif "local" in model.lower() or "ollama" in model.lower():
            return "ollama"
        elif "openrouter" in model.lower():
            return "openrouter"
        return "unknown"

    def _get_fallback(self, model: str) -> str:
        """Get fallback model in LiteLLM format"""
        fallback_map = {
            "claude-3-5-sonnet-20241022": "gpt-4o",
            "gpt-4o": "claude-3-5-sonnet-20241022",
            "gemini/gemini-2.0-flash-exp": "gpt-4o",
            "gemini/gemini-1.5-flash": "gpt-4o",
        }
        # Check if model is in fallback map
        if model in fallback_map:
            return fallback_map[model]
        # Check by provider
        if "gemini" in model.lower():
            return "gpt-4o"
        elif "claude" in model.lower():
            return "gpt-4o"
        elif "gpt" in model.lower():
            return "gemini/gemini-2.0-flash-exp"
        return "gpt-4o"  # Default fallback

    async def completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List] = None,
        stream: bool = False,
        response_format: Optional[Dict] = None,
    ):
        """Execute completion with circuit breaker protection"""

        # Model name mapping to actual LiteLLM model identifiers
        model_mapping = {
            "auto": None,  # Will be handled below
            "google": "gemini/gemini-2.0-flash-exp",
            "gemini-flash": "gemini/gemini-2.0-flash-exp",
            "claude-sonnet": "claude-3-5-sonnet-20241022",
            "gpt-4o": "gpt-4o",
        }
        
        # Normalize model name to actual LiteLLM format
        original_model = model
        if model == "auto":
            # Try to find first available cloud model (skip Ollama/local)
            if self.router and hasattr(self.router, 'model_list') and self.router.model_list:
                # Get the actual litellm model name from the first available cloud model
                # Skip local/Ollama models (priority 1) and prefer cloud models (priority 2+)
                for router_model in self.router.model_list:
                    if isinstance(router_model, dict) and "litellm_params" in router_model:
                        # Skip Ollama/local models
                        model_name = router_model["litellm_params"].get("model", "")
                        if "ollama" not in model_name.lower() and "local" not in model_name.lower():
                            model = model_name
                            break
                # If no cloud model found, try any model
                if model == "auto":
                    for router_model in self.router.model_list:
                        if isinstance(router_model, dict) and "litellm_params" in router_model:
                            model = router_model["litellm_params"].get("model", "gemini/gemini-2.0-flash-exp")
                            break
                    else:
                        model = "gemini/gemini-2.0-flash-exp"
            else:
                # Fallback: use direct litellm model name (prefer Gemini)
                model = "gemini/gemini-2.0-flash-exp"
        elif model in model_mapping:
            # Map to actual litellm model name
            mapped = model_mapping[model]
            if mapped:
                model = mapped
            else:
                model = "gemini/gemini-2.0-flash-exp"
        elif "/" not in model and model not in ["auto"]:
            # If it's a router model_name, try to find it in router and get actual model
            if self.router and hasattr(self.router, 'model_list'):
                for router_model in self.router.model_list:
                    if isinstance(router_model, dict) and router_model.get("model_name") == original_model:
                        if "litellm_params" in router_model:
                            model = router_model["litellm_params"].get("model", model)
                            break
                # If still not found and doesn't have "/", it's likely invalid
                if "/" not in model and model not in ["auto"]:
                    # Default to gemini
                    model = "gemini/gemini-2.0-flash-exp"
        # If model already has provider prefix (e.g., "gemini/..."), use it directly
        # Ensure model is in correct format before proceeding
        if "/" not in model and model != "auto":
            # Last resort: default to gemini
            model = "gemini/gemini-2.0-flash-exp"

        provider = self._get_provider(model)

        # Initialize circuit breaker if needed
        if provider not in self.circuit_breakers:
            self.circuit_breakers[provider] = CircuitBreaker()

        # Check circuit breaker
        if not self.circuit_breakers[provider].allow_request():
            # Use fallback
            model = self._get_fallback(model)
            provider = self._get_provider(model)

        try:
            # Build completion kwargs
            completion_kwargs = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "tools": tools,
                "stream": stream,
            }
            
            # Add response_format if provided
            if response_format:
                completion_kwargs["response_format"] = response_format
            
            # Always use direct litellm_completion with the actual model name
            # The model should now be in LiteLLM format (e.g., "gemini/gemini-2.0-flash-exp")
            # Pass API key directly in completion kwargs for better reliability
            import os
            original_env = {}
            
            # Set API key in both environment and completion kwargs
            if provider == "google" and settings.google_api_key:
                # LiteLLM for Gemini requires BOTH GEMINI_API_KEY and GOOGLE_API_KEY
                original_env["GEMINI_API_KEY"] = os.environ.get("GEMINI_API_KEY")
                original_env["GOOGLE_API_KEY"] = os.environ.get("GOOGLE_API_KEY")
                os.environ["GEMINI_API_KEY"] = settings.google_api_key
                os.environ["GOOGLE_API_KEY"] = settings.google_api_key
                # Also pass directly in kwargs as fallback
                completion_kwargs["api_key"] = settings.google_api_key
            elif provider == "anthropic" and settings.anthropic_api_key:
                original_env["ANTHROPIC_API_KEY"] = os.environ.get("ANTHROPIC_API_KEY")
                os.environ["ANTHROPIC_API_KEY"] = settings.anthropic_api_key
                completion_kwargs["api_key"] = settings.anthropic_api_key
            elif provider == "openai" and settings.openai_api_key:
                original_env["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY")
                os.environ["OPENAI_API_KEY"] = settings.openai_api_key
                completion_kwargs["api_key"] = settings.openai_api_key
            elif provider == "openrouter" and settings.openrouter_api_key:
                original_env["OPENROUTER_API_KEY"] = os.environ.get("OPENROUTER_API_KEY")
                os.environ["OPENROUTER_API_KEY"] = settings.openrouter_api_key
                completion_kwargs["api_key"] = settings.openrouter_api_key
            
            try:
                response = await litellm_acompletion(**completion_kwargs)
            finally:
                # Restore original environment variables
                for key, value in original_env.items():
                    if value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = value

            self.circuit_breakers[provider].record_success()
            return response

        except Exception as e:
            self.circuit_breakers[provider].record_failure()
            print(f"LLM completion error: {e}")
            import traceback
            traceback.print_exc()
            raise

