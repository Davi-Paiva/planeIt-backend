from typing import Optional
from fastapi import HTTPException, status, Request
from jose import jwt, JWTError
import os
from dotenv import load_dotenv
from app.models.user import User
import logging
from app.db.mongodb import get_users_collection

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# JWT configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-for-development")
ALGORITHM = "HS256"

# Helper function to convert MongoDB user document to User model
def user_doc_to_model(user_doc):
    if not user_doc:
        return None
    
    # Convert ObjectId to string
    if "_id" in user_doc:
        user_doc["id"] = str(user_doc["_id"])
        del user_doc["_id"]
    
    return User(**user_doc)

async def get_current_user_from_token(token: str) -> Optional[User]:
    """
    Internal method to get the current user from a token
    
    Args:
        token: JWT token string
        
    Returns:
        User object if token is valid and user exists, None otherwise
    """
    logger.info(f"Processing token: {token[:10]}...")
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        logger.info(f"Token decoded, payload: {payload}")
        
        email: str = payload.get("sub")
        if email is None:
            logger.error("No 'sub' field found in token")
            return None
            
        logger.info(f"Looking for user with email: {email}")
        
    except JWTError as e:
        logger.error(f"JWT Error: {str(e)}")
        return None
    
    # Find the user by email in MongoDB
    users_collection = get_users_collection()
    user_doc = await users_collection.find_one({"email": email})
    
    if not user_doc:
        logger.error(f"No user found with email: {email}")
        return None
    
    # Convert MongoDB document to User model
    user = user_doc_to_model(user_doc)
    logger.info(f"User found: {user.name}")
    
    return user

async def get_current_user_from_request(request: Request) -> Optional[User]:
    """
    Get the current user from the request's Authorization header
    
    Args:
        request: FastAPI Request object
        
    Returns:
        User object if authenticated, None otherwise
    """
    logger.info("Processing request for authentication")
    
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        logger.error("No Authorization header found")
        return None
        
    if not auth_header.startswith("Bearer "):
        logger.error(f"Authorization header doesn't start with 'Bearer ': {auth_header[:15]}...")
        return None
    
    token = auth_header.replace("Bearer ", "")
    logger.info(f"Extracted token: {token[:10]}...")
    
    return await get_current_user_from_token(token)

async def get_user_or_raise_401(request: Request) -> User:
    """
    Get the current user or raise a 401 Unauthorized exception
    
    Args:
        request: FastAPI Request object
        
    Returns:
        User object if authenticated
        
    Raises:
        HTTPException: 401 Unauthorized if user is not authenticated
    """
    user = await get_current_user_from_request(request)
    if not user:
        logger.error("Authentication failed, raising 401")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user 