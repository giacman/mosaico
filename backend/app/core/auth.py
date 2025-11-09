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
        # Clerk's authenticate_request expects an httpx.Request.
        # We can construct a minimal httpx.Request with the Authorization header.
        headers = {"Authorization": f"Bearer {credentials.credentials}"}
        httpx_request = httpx.Request("GET", "/", headers=headers) # Minimal dummy request
        
        # Authenticate the request
        # The authorized_parties is optional but good for security
        # For now, let's omit it for initial testing.
        request_state = clerk_client.authenticate_request(httpx_request, AuthenticateRequestOptions())
        
        if not request_state.is_signed_in:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Access user information from the user object within RequestState
        # Ensure request_state.user is not None before accessing its attributes
        if not request_state.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authenticated but user object not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user_id = request_state.user.id
        # user_name and user_email might be nested or direct attributes depending on ClerkUser object
        # Check common patterns or refer to ClerkUser object structure
        user_name = request_state.user.first_name
        if request_state.user.last_name:
            user_name += f" {request_state.user.last_name}"
        user_name = user_name or request_state.user.email_addresses[0].email_address if request_state.user.email_addresses else "Unknown User"
        
        # Fallback if first_name/last_name are not set, use email
        if user_name == "": # If first_name and last_name were empty strings
            if request_state.user.email_addresses and request_state.user.email_addresses[0].email_address:
                user_name = request_state.user.email_addresses[0].email_address
            else:
                user_name = "Unknown User"
        
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

