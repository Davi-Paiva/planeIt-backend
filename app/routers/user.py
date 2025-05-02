from fastapi import APIRouter, HTTPException, status
from typing import List
from app.models.user import User

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)

# This is just an example; in a real app, you'd connect to a database
fake_users_db = []

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(user: User):
    fake_users_db.append(user)
    return user