"""
Authentication middleware using Clerk
"""
import logging
from typing import NamedTuple
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from clerk_backend_api import Clerk
from app.core.config import settings

logger = logging.getLogger(__name__)


class User(NamedTuple):
    """User information from authentication"""
    id: str
    name: str | None


# HTTP Bearer token scheme
security = HTTPBearer()

# Initialize Clerk client
clerk_client = None
if settings.clerk_secret_key:
    clerk_client = Clerk(bearer_auth=settings.clerk_secret_key)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """
    Dependency to get current authenticated user from JWT token
    
    Returns:
        User: User object with id and name
        
    Raises:
        HTTPException: If token is invalid or user not authenticated
    """
    if not clerk_client:
        # For development/testing without Clerk
        if settings.environment == "development":
            logger.warning("Clerk not configured, using development mode")
            return User(id="dev-user-123", name="Dev User")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication not configured"
        )
    
    token = credentials.credentials
    
    try:
        # Verify JWT token with Clerk
        session = clerk_client.verify_token(token)
        
        if not session or not session.get("sub"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user_id = session["sub"]
        # Try to get user name from session claims
        user_name = session.get("name") or session.get("email") or "Unknown User"
        
        return User(id=user_id, name=user_name)
        
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security)
) -> User | None:
    """
    Optional authentication dependency
    Returns User object if authenticated, None otherwise
    """
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None

