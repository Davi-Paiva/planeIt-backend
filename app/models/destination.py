from pydantic import BaseModel, Field
from typing import List, Optional, Union
from app.db.mongodb import get_destinations_collection, connect_to_mongo
from app.data.destinations import destinations

class Destination(BaseModel):
    city: str
    country: str
    embedding: List[float]
    airport_code: str
    description: str
    image: str
    price: float
    likes: int = 0

    model_config = {
        "json_schema_extra": {
            "example": {
                "city": "New York",
                "country": "USA",
                "airport_code": "JFK",
                "embedding": [0.1, 0.2, 0.3],
                "description": "New York is a city of opportunity and excitement. It's a place where you can be anything you want to be.",
                "image": "https://www.google.com/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png",
                "price": 100,
                "likes": 2
            }
        }
    }

class DestinationSuggestion(BaseModel):
    country: str
    city: str
    airport_code: str
    description: str
    photo_url: Optional[str] = None
    image: Optional[str] = None
    price: Optional[Union[float, None]] = None
    likes: int = 0
    
    model_config = {
        "populate_by_name": True
    }

async def seed_destinations():
    # Connect to MongoDB
    await connect_to_mongo()
    
    # Get destinations collection
    destinations_collection = get_destinations_collection()
    
    # Sample destinations
    count = await destinations_collection.count_documents({})
    if count > 0:
        print(f"Destinations collection already has {count} documents. Skipping seed.")
        return

    await destinations_collection.insert_many(destinations)
    
    
    # Insert destinations
    result = await destinations_collection.insert_many(destinations)
    print(f"Added {len(result.inserted_ids)} destinations")