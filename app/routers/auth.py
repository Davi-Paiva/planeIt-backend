from fastapi import APIRouter, HTTPException, status, Depends, Security, Request
from app.models.auth import UserRegistration, UserLogin
from app.models.user import User
from typing import Dict, Optional
from datetime import datetime, timedelta
from jose import jwt, JWTError
import os
from dotenv import load_dotenv
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging
from app.db.mongodb import get_users_collection
from bson import ObjectId
import json

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Set up JWT configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-for-development")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Security
security = HTTPBearer()

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={404: {"description": "Not found"}},
)

# Helper function to convert MongoDB user document to User model
def user_doc_to_model(user_doc):
    if not user_doc:
        return None
    
    # Convert ObjectId to string
    if "_id" in user_doc:
        user_doc["id"] = str(user_doc["_id"])
        del user_doc["_id"]
    
    return User(**user_doc)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    """
    Dependency to get the current user from the JWT token
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
            
    except JWTError as e:
        raise credentials_exception
    
    # Find the user by email in MongoDB
    users_collection = get_users_collection()
    user_doc = await users_collection.find_one({"email": email})
    
    if not user_doc:
        raise credentials_exception
    
    # Convert MongoDB document to User model
    user = user_doc_to_model(user_doc)
    
    
    return user

@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=Dict)
async def register(user_data: UserRegistration):
    """
    Register a new user
    """
    logger.info(f"Registering user with email: {user_data.email}")
    
    # Get users collection
    users_collection = get_users_collection()
    
    # Check if email already exists
    existing_user = await users_collection.find_one({"email": user_data.email})
    if existing_user:
        logger.warning(f"Email already registered: {user_data.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create User model
    user = User(
        name=user_data.name,
        email=user_data.email,
        password=user_data.password,  # In production, should hash password
        interests=[],
        location="",
        preferences=[]
    )
    
    # Insert user into MongoDB
    user_dict = json.loads(user.model_dump_json())
    result = await users_collection.insert_one(user_dict)
    
    # Generate token for the newly registered user
    token_data = {"sub": user.email}
    token = create_access_token(data=token_data)
    logger.info(f"Generated token: {token[:10]}...")
    
    # Convert user model to dict for response
    user_response = {
        "name": user.name,
        "email": user.email,
        "id": str(result.inserted_id)
    }
    
    return {
        "access_token": token, 
        "token_type": "bearer", 
        "user": user_response
    }

@router.post("/login", response_model=Dict)
async def login(login_data: UserLogin):
    """
    Authenticate a user and return a token
    """
    logger.info(f"Login attempt for email: {login_data.email}")
    
    # Get users collection
    users_collection = get_users_collection()
    
    # Find user by email
    user_doc = await users_collection.find_one({"email": login_data.email})
    if not user_doc:
        logger.warning(f"User not found: {login_data.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Convert to User model
    user = user_doc_to_model(user_doc)
    
    # Check password (should use password hashing in production)
    if user.password != login_data.password:
        logger.warning(f"Incorrect password for user: {login_data.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logger.info(f"Login successful for: {user.email}")
    
    # Generate a JWT token with an expiration time
    token_data = {"sub": user.email}
    token = create_access_token(data=token_data)
    logger.info(f"Generated token: {token[:10]}...")
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "name": user.name,
            "email": user.email,
        }
    }

@router.get("/me", response_model=Dict)
async def get_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user information
    """
    logger.info(f"Getting user info for: {current_user.email}")
    return {
        "user": {
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email
        }
    }