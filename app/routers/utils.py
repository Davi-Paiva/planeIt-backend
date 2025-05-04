from fastapi import APIRouter, HTTPException
from app.services.pexels_service import PexelsService

router = APIRouter(
    prefix="/utils",
    tags=["utilities"],
    responses={404: {"description": "Not found"}},
)

@router.get("/photos/{city}/{country}")
async def get_destination_photos(city: str, country: str):
    """
    Get photos for a specific destination using Pexels API
    """
    photo = await PexelsService.get_destination_photo(city, country)
    
    return photo