from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class PlanUser(BaseModel):
    name: str
    email: str
    
    model_config = {
        "populate_by_name": True
    }

class Plan(BaseModel):
    name: str
    startDate: datetime
    endDate: datetime
    code: str
    description: str
    users: List[PlanUser] = []
    creator: PlanUser

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {
            "example": {
                "name": "My Plan",
                "members": [{"name": "John Doe", "email": "john.doe@example.com"}],
                "startDate": "2023-01-01T00:00:00Z",
                "endDate": "2023-01-01T00:00:00Z",
                "code": "123456",
                "description": "This is a description of my plan"
            }
        }
    }

class PlanCreate(BaseModel):
    name: str
    startDate: str
    endDate: str
    description: str

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {
            "example": {
                "name": "My Plan",
                "startDate": "2023-01-01",
                "endDate": "2023-01-01",
                "description": "This is a description of my plan"
            }
        }
    }

# Import at the end to avoid circular import
from app.models.user import User
    