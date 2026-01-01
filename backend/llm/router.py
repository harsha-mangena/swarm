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

        # Import settings to get configured models
        from backend.api.routes.settings import get_model_for_provider
        
        # Get configured models from settings
        default_google = get_model_for_provider("google")
        default_anthropic = get_model_for_provider("anthropic")
        default_openai = get_model_for_provider("openai")
        default_openrouter = get_model_for_provider("openrouter")
        
        # Model name mapping to actual LiteLLM model identifiers (using settings)
        model_mapping = {
            "auto": None,  # Will be handled below
            "google": default_google,
            "gemini-flash": default_google,
            "anthropic": default_anthropic,
            "claude-sonnet": default_anthropic,
            "openai": default_openai,
            "gpt-4o": default_openai,
            "openrouter": default_openrouter,
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
                # If no cloud model found, use default from settings
                if model == "auto":
                    model = default_google
            else:
                # Fallback: use configured default
                model = default_google
        elif model in model_mapping:
            # Map to actual litellm model name from settings
            mapped = model_mapping[model]
            if mapped:
                model = mapped
            else:
                model = default_google
        elif "/" not in model and model not in ["auto"]:
            # If it's a router model_name, try to find it in router and get actual model
            if self.router and hasattr(self.router, 'model_list'):
                for router_model in self.router.model_list:
                    if isinstance(router_model, dict) and router_model.get("model_name") == original_model:
                        if "litellm_params" in router_model:
                            model = router_model["litellm_params"].get("model", model)
                            break
                # If still not found and doesn't have "/", use settings default
                if "/" not in model and model not in ["auto"]:
                    model = default_google
        # If model already has provider prefix (e.g., "gemini/..."), use it directly
        # Ensure model is in correct format before proceeding
        if "/" not in model and model != "auto":
            # Last resort: use settings default
            model = default_google

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
            # Set explicit max_tokens to prevent truncation
            effective_max_tokens = max_tokens if max_tokens else 4096
            
            completion_kwargs = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": effective_max_tokens,
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
                
                # Check for truncation and attempt continuation
                if (hasattr(response, 'choices') and 
                    response.choices and 
                    hasattr(response.choices[0], 'finish_reason') and
                    response.choices[0].finish_reason == "length"):
                    
                    print(f"Output truncated for model {model}, attempting continuation...")
                    
                    # Get the partial content
                    partial_content = response.choices[0].message.content or ""
                    
                    # Request continuation
                    continuation_messages = messages + [
                        {"role": "assistant", "content": partial_content},
                        {"role": "user", "content": "Continue from exactly where you left off. Do not repeat any previous content."}
                    ]
                    
                    continuation_kwargs = {**completion_kwargs, "messages": continuation_messages}
                    continuation_response = await litellm_acompletion(**continuation_kwargs)
                    
                    # Combine responses
                    continuation_content = continuation_response.choices[0].message.content or ""
                    response.choices[0].message.content = partial_content + "\n" + continuation_content
                    print("Continuation successful, combined output returned.")
                    
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

