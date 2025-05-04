import os
import logging
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import requests
import aiohttp

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get API key from environment variable
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

class PexelsService:
    """
    Service for retrieving images from Pexels API.
    """
    BASE_URL = "https://api.pexels.com/v1"
    
    @staticmethod
    async def get_destination_photo(city:str, country:str) -> Optional[Dict[str, Any]]:
        if not PEXELS_API_KEY:
            logger.error("Pexels API key not set. Unable to retrieve photos.")
            return None
        
        headers = {
            "Authorization": PEXELS_API_KEY
        }
        
        params = {
            "query": f"{city}, {country}",
            "orientation": "portrait",
            "per_page": 1,
            "page": 1
        }

        result = await PexelsService.search_photos(
            query=f"{city}, {country}",
            per_page=1,
            orientation="portrait"
        )

        if result and result["photos"]:
            return result["photos"][0]["src"]["original"]
        else:
            return None
    
    @staticmethod
    async def search_photos(
        query: str, 
        per_page: int = 10, 
        page: int = 1, 
        orientation: str = None,
        size: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Search for photos on Pexels.
        """
        if not PEXELS_API_KEY:
            logger.error("Pexels API key not set. Unable to retrieve photos.")
            return None
        
        headers = {
            "Authorization": PEXELS_API_KEY
        }
        
        params = {
            "query": query,
            "per_page": per_page,
            "page": page
        }
        
        if orientation:
            params["orientation"] = orientation
        
        if size:
            params["size"] = size
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{PexelsService.BASE_URL}/search", 
                    headers=headers, 
                    params=params
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Pexels API error: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error searching Pexels photos: {str(e)}")
            return None

    @staticmethod
    async def get_destination_photos(
        destination: str, 
        count: int = 5,
        orientation: str = "landscape"
    ) -> List[Dict[str, Any]]:
        """
        Get travel destination photos.
        """
        # Enhance the query to get better travel images
        query = f"travel {destination} destination"
        
        # Add await here
        result = await PexelsService.search_photos(
            query=query,
            per_page=count,
            orientation=orientation
        )
        
        if not result or "photos" not in result:
            logger.warning(f"No photos found for destination: {destination}")
            return []
        
        # Format the photos to include only the data we need
        formatted_photos = []
        for photo in result["photos"]:
            formatted_photos.append({
                "id": photo["id"],
                "width": photo["width"],
                "height": photo["height"],
                "url": photo["url"],  # Original Pexels page URL
                "photographer": photo["photographer"],
                "photographer_url": photo["photographer_url"],
                "alt": photo.get("alt", destination),
                "src": {
                    "original": photo["src"]["original"],
                    "large": photo["src"]["large"],
                    "medium": photo["src"]["medium"],
                    "small": photo["src"]["small"],
                    "portrait": photo["src"]["portrait"],
                    "landscape": photo["src"]["landscape"],
                    "tiny": photo["src"]["tiny"]
                }
            })
        
        return formatted_photos
    