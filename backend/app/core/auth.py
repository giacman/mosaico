"""
Authentication middleware using Clerk
"""
import logging
from typing import NamedTuple
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from clerk_backend_api import Clerk
from app.core.config import settings
from fastapi import Request # Import Request
from clerk_backend_api.jwks_helpers import AuthenticateRequestOptions # Import AuthenticateRequestOptions
import httpx # Import httpx for httpx.Request

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
    try:
        clerk_client = Clerk(bearer_auth=settings.clerk_secret_key)
        logger.debug(f"Clerk client initialized: {clerk_client}")
        logger.debug(f"Type of clerk_client: {type(clerk_client)}")
    except Exception as e:
        logger.error(f"Failed to initialize Clerk client: {e}", exc_info=True)
        clerk_client = None # Ensure it's None if init fails
else:
    logger.warning("CLERK_SECRET_KEY not provided. Running without Clerk authentication.")
    logger.info(f"Clerk client is active. Settings environment: {settings.environment}")


def _get_httpx_request(request: Request) -> httpx.Request:
    """Converts a FastAPI Request to an httpx.Request."""
    # Extract headers, excluding host, as httpx will add it.
    headers = {k: v for k, v in request.headers.items() if k.lower() != 'host'}

    # Get the full URL
    url = str(request.url)

    # Reconstruct the httpx.Request
    return httpx.Request(
        method=request.method,
        url=url,
        headers=headers,
    )


async def get_current_user(
    request: Request,  # Inject FastAPI's Request object
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
        if settings.environment == "development":
            logger.info(f"Running in development mode with settings.environment: {settings.environment}")
            logger.warning("Clerk not configured, using development mode")
            return User(id="dev-user-123", name="Dev User")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication not configured"
        )
    
    try:
        httpx_request = _get_httpx_request(request)
        
        # Authenticate the request with Clerk
        # Note: The 'options' parameter is currently an empty dict. 
        # For now, let's omit it for initial testing.
        request_state = clerk_client.authenticate_request(httpx_request, AuthenticateRequestOptions())
        
        if not request_state.is_signed_in:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # ONLY attempt to access user details if authentication was successful
        # With clerk-backend-api v1.5.0, user_id is directly on the RequestState object
        # if the user is signed in. There is no .user or .claims nested object.
        # The user ID is the 'sub' (subject) claim in the JWT payload.
        user_id = request_state.payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID (sub) not found in token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Fetch user details from Clerk to get email/name
        user_name = None
        try:
            user_details = clerk_client.users.get(user_id=user_id)
            if user_details:
                # Prefer email, fallback to first_name + last_name, then username
                if user_details.email_addresses and len(user_details.email_addresses) > 0:
                    user_name = user_details.email_addresses[0].email_address
                elif user_details.first_name:
                    user_name = f"{user_details.first_name} {user_details.last_name or ''}".strip()
                elif user_details.username:
                    user_name = user_details.username
        except Exception as e:
            logger.warning(f"Could not fetch user details from Clerk: {e}")
        
        # Fallback if we couldn't get name
        if not user_name:
            user_name = f"User {user_id[:8]}..."
        
        return User(id=user_id, name=user_name)
        
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}", exc_info=True) # Log full traceback
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

