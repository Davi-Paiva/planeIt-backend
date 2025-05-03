from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List

class UserRegistration(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(..., min_length=6)
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "John Doe",
                "email": "john.doe@example.com",
                "password": "password123",
            }
        }
    }

class UserLogin(BaseModel):
    email: EmailStr
    password: str
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "john.doe@example.com",
                "password": "password123"
            }
        }
    } 