from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from .airport import Airport

class User(BaseModel):
    name: str
    email: EmailStr
    password: str
    location: Optional[dict] = None
    description: List[str] = []
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True
    }



class UserPreferences(BaseModel):
    description: str
    location: Airport