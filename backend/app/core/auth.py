"""
Authentication middleware using Clerk
"""
import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from clerk_backend_api import Clerk
from app.core.config import settings

logger = logging.getLogger(__name__)

# HTTP Bearer token scheme
security = HTTPBearer()

# Initialize Clerk client
clerk_client = None
if settings.clerk_secret_key:
    clerk_client = Clerk(bearer_auth=settings.clerk_secret_key)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    Dependency to get current authenticated user from JWT token
    
    Returns:
        str: User ID from Clerk
        
    Raises:
        HTTPException: If token is invalid or user not authenticated
    """
    if not clerk_client:
        # For development/testing without Clerk
        if settings.environment == "development":
            logger.warning("Clerk not configured, using development mode")
            return "dev-user-123"
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
        return user_id
        
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security)
) -> str | None:
    """
    Optional authentication dependency
    Returns user ID if authenticated, None otherwise
    """
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None

