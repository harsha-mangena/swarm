"""Authentication middleware for Supabase JWT verification"""

from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import jwt

from backend.config import settings
from backend.supabase_client import get_supabase_admin, is_supabase_configured

# Security scheme for Swagger UI
security = HTTPBearer(auto_error=False)


class AuthUser:
    """Authenticated user from Supabase JWT"""
    def __init__(self, id: str, email: str, role: str = "authenticated"):
        self.id = id
        self.email = email
        self.role = role


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[AuthUser]:
    """
    Verify Supabase JWT and return current user.
    Returns None if auth is not configured (for local development).
    """
    # Skip auth if Supabase is not configured (local dev mode)
    if not is_supabase_configured():
        return None
    
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    
    try:
        # Verify JWT with Supabase
        # The JWT secret is the Supabase JWT secret (derived from service key)
        # For simplicity, we'll use the Supabase auth API to verify
        supabase = get_supabase_admin()
        
        # Get user from Supabase using the token
        user_response = supabase.auth.get_user(token)
        
        if not user_response or not user_response.user:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = user_response.user
        return AuthUser(
            id=user.id,
            email=user.email,
            role=user.role or "authenticated"
        )
        
    except Exception as e:
        print(f"Auth error: {e}")
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[AuthUser]:
    """
    Get current user if authenticated, None otherwise.
    Use this for endpoints that work with or without auth.
    """
    if not is_supabase_configured():
        return None
    
    if not credentials:
        return None
    
    try:
        return await get_current_user(request, credentials)
    except HTTPException:
        return None


def require_auth(user: Optional[AuthUser] = Depends(get_current_user)) -> AuthUser:
    """
    Dependency that requires authentication.
    Raises 401 if not authenticated.
    """
    if not is_supabase_configured():
        # Return a fake user for local dev
        return AuthUser(id="local-dev-user", email="dev@localhost", role="authenticated")
    
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    return user
