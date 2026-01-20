"""Supabase database connection."""

from typing import Optional
from supabase import create_client, Client
from app.config import settings


def get_supabase_client() -> Client:
    """Get Supabase client instance."""
    if not settings.supabase_url or not settings.supabase_key:
        raise ValueError("Supabase URL and Key must be configured")
    return create_client(settings.supabase_url, settings.supabase_key)


def get_supabase_admin_client() -> Client:
    """Get Supabase client with service role key for admin operations."""
    if not settings.supabase_url or not settings.supabase_service_key:
        raise ValueError("Supabase URL and Service Key must be configured")
    return create_client(settings.supabase_url, settings.supabase_service_key)


# Singleton client instance
_client: Optional[Client] = None


def get_db() -> Client:
    """Get database client (dependency injection)."""
    global _client
    if _client is None:
        _client = get_supabase_client()
    return _client
