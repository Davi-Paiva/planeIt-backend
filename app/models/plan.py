from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.destination import DestinationSuggestion

class PlanUser(BaseModel):
    name: str
    email: str
    is_quiz_completed: bool
    top_destinations: List[str] = []
    has_voted: bool = False

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
    suggested_destinations: List[DestinationSuggestion] = []

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
    