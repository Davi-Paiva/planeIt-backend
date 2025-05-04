from fastapi import APIRouter, HTTPException, status, Request
from typing import List
from app.models.user import User, UserPreferences, UserPreferencesRequest
from app.services.openai_service import OpenAIService
from app.services.auth import get_current_user_from_request
from pydantic import BaseModel
from app.db.mongodb import get_users_collection, get_plans_collection
import numpy as np
from app.data.destinations import destinations
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/user",
    tags=["user"],
    responses={404: {"description": "Not found"}},
)


def cosine_similarity(vec1, vec2):
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))


@router.post("/{code}/preferences")
async def addUserPreferences(code: str, user_preferences_request: UserPreferencesRequest, request: Request):
    user = await get_current_user_from_request(request) 

    preferences = user_preferences_request.preferences

    openai_service = OpenAIService()
    preferences_prompt = ""
    for preference in preferences:
        preferences_prompt += f"Question: '{preference.question}' Answer: '{preference.answer}'\n"

    user_summary = await openai_service.generate_user_summary(preferences_prompt)

    if user_summary is None:
        raise HTTPException(status_code=500, detail="Failed to generate user summary")

    user_embedding = await openai_service.generate_embedding(user_summary)

    # Get users collection from MongoDB
    users_collection = get_users_collection()

    logger.info(f"Updating user preferences for {user.email}")
    
    # Update user preferences in database
    result = await users_collection.update_one(
        {"email": user.email},
        {"$set": {
            "location": user_preferences_request.location,
            "preferences": user_embedding
        }}
    )

    plans_collection = get_plans_collection()
    result = await plans_collection.update_one(
        {"users.email": user.email, "code": code},
        {"$set": {
            "users.$.is_quiz_completed": True
        }}
    )

    if user_embedding is None:
       raise HTTPException(status_code=500, detail="Failed to generate user embedding")

    destinations_similarities = []
    
    for destination in destinations:
        destination_embedding = destination['embedding']
        similarity = cosine_similarity(user_embedding, destination_embedding)
        destinations_similarities.append((destination, similarity))

    sorted_destinations = sorted(destinations_similarities, key=lambda x: x[1], reverse=True)
    
    plans_collection.update_one({"users.email": user.email, "code": code}, 
    {"$set": {"users.$.top_destinations": [destination[0]['airport_code'] for destination in sorted_destinations[:25]]}})

    return user_summary
