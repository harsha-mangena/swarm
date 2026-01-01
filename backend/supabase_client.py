"""Supabase client initialization"""

from supabase import create_client, Client
from backend.config import settings

_supabase_admin: Client = None
_supabase_anon: Client = None


def get_supabase_admin() -> Client:
    """Get Supabase client with service role (admin) permissions.
    Use for server-side operations that bypass RLS.
    """
    global _supabase_admin
    if _supabase_admin is None:
        if not settings.supabase_url or not settings.supabase_service_key:
            raise ValueError("Supabase URL and Service Key must be configured")
        _supabase_admin = create_client(
            settings.supabase_url,
            settings.supabase_service_key
        )
    return _supabase_admin


def get_supabase_anon() -> Client:
    """Get Supabase client with anon key.
    Use for operations that should respect RLS.
    """
    global _supabase_anon
    if _supabase_anon is None:
        if not settings.supabase_url or not settings.supabase_anon_key:
            raise ValueError("Supabase URL and Anon Key must be configured")
        _supabase_anon = create_client(
            settings.supabase_url,
            settings.supabase_anon_key
        )
    return _supabase_anon


def is_supabase_configured() -> bool:
    """Check if Supabase is properly configured"""
    return bool(
        settings.supabase_url and 
        settings.supabase_anon_key and 
        settings.supabase_service_key
    )
