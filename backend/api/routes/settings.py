"""Settings API routes"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
import json
import os

router = APIRouter(prefix="/api/settings", tags=["settings"])

# Settings file path (persisted across restarts)
SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "../../../.settings.json")


class ModelSettings(BaseModel):
    """Model preferences per provider"""
    google_model: str = "gemini/gemini-2.0-flash-exp"
    anthropic_model: str = "claude-3-5-sonnet-20241022"
    openai_model: str = "gpt-4o"
    openrouter_model: str = "openrouter/anthropic/claude-3-sonnet"


# In-memory cache of settings
_settings_cache: Optional[ModelSettings] = None


def load_settings() -> ModelSettings:
    """Load settings from file"""
    global _settings_cache
    if _settings_cache is not None:
        return _settings_cache
    
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                data = json.load(f)
                _settings_cache = ModelSettings(**data)
                return _settings_cache
        except Exception as e:
            print(f"Failed to load settings: {e}")
    
    _settings_cache = ModelSettings()
    return _settings_cache


def save_settings(settings: ModelSettings):
    """Save settings to file"""
    global _settings_cache
    _settings_cache = settings
    
    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings.dict(), f, indent=2)
    except Exception as e:
        print(f"Failed to save settings: {e}")
        raise


def get_model_for_provider(provider: str) -> str:
    """Get the configured model for a provider"""
    settings = load_settings()
    
    model_map = {
        "google": settings.google_model,
        "anthropic": settings.anthropic_model,
        "openai": settings.openai_model,
        "openrouter": settings.openrouter_model,
    }
    
    return model_map.get(provider, settings.google_model)


@router.get("", response_model=ModelSettings)
async def get_settings():
    """Get current model settings"""
    return load_settings()


@router.post("", response_model=ModelSettings)
async def update_settings(settings: ModelSettings):
    """Update model settings"""
    save_settings(settings)
    return settings


@router.get("/models")
async def get_available_models():
    """Get list of available models per provider"""
    return {
        "google": [
            {"id": "gemini/gemini-1.5-flash", "name": "Gemini 1.5 Flash (Recommended)"},
            {"id": "gemini/gemini-1.5-pro", "name": "Gemini 1.5 Pro"},
            {"id": "gemini/gemini-2.0-flash-exp", "name": "Gemini 2.0 Flash (Experimental)"},
        ],
        "anthropic": [
            {"id": "claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet"},
            {"id": "claude-3-5-haiku-20241022", "name": "Claude 3.5 Haiku"},
            {"id": "claude-3-opus-20240229", "name": "Claude 3 Opus"},
        ],
        "openai": [
            {"id": "gpt-4o", "name": "GPT-4o"},
            {"id": "gpt-4o-mini", "name": "GPT-4o Mini"},
            {"id": "gpt-4-turbo", "name": "GPT-4 Turbo"},
        ],
        "openrouter": [
            {"id": "openrouter/anthropic/claude-3-sonnet", "name": "Claude 3 Sonnet (via OpenRouter)"},
            {"id": "openrouter/google/gemini-pro", "name": "Gemini Pro (via OpenRouter)"},
            {"id": "openrouter/openai/gpt-4o", "name": "GPT-4o (via OpenRouter)"},
        ],
    }
