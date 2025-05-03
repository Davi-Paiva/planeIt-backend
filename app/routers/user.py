from fastapi import APIRouter, HTTPException, status, Request
from typing import List
from app.models.user import User, UserPreferences

router = APIRouter(
    prefix="/user",
    tags=["user"],
    responses={404: {"description": "Not found"}},
)



@router.post("/preferences")
async def addUserPreferences(preferences: UserPreferences,request: Request):
    user = get_current_user_from_request()

