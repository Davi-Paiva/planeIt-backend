from pydantic import BaseModel, Field
from typing import Optional

class Airport(BaseModel):
    code: str = Field(description="IATA airport code (3 letters)")
    name: str = Field(description="Full airport name")
    city: str = Field(description="City where the airport is located")
    country: str = Field(description="Country where the airport is located")
    latitude: Optional[float] = Field(None, description="Airport latitude coordinate")
    longitude: Optional[float] = Field(None, description="Airport longitude coordinate")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "code": "BCN",
                "name": "Barcelona El Prat Airport",
                "city": "Barcelona",
                "country": "Spain",
                "latitude": 41.2971,
                "longitude": 2.0785,
            }
        }
    } 