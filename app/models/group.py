from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

class Group(BaseModel):
    name: str
    members: List["User"] = []
    available_from: datetime
    available_to: datetime
    code: str
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True
    }

# Import at the end to avoid circular import
from app.models.user import User
    