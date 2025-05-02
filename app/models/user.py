from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Annotated
from app.models.airport import Airport

class User(BaseModel):
    name: str
    location: Airport
    interests: list[str]
    group: Optional["Group"] = None
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True
    }

# Import at the end to avoid circular import
from app.models.group import Group