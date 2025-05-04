from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List

class User(BaseModel):
    name: str
    email: EmailStr
    password: str
    location: str
    preferences: List[float] = Field(default_factory=list)
    
    model_config = {
        "populate_by_name": True,   
        "arbitrary_types_allowed": True
    }



class UserPreferences(BaseModel):
    question: str
    answer: str

class UserPreferencesRequest(BaseModel):
    preferences: List[UserPreferences]
    location: str