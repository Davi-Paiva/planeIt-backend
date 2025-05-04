import os
import aiohttp
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get API key from environment variable
AMADEUS_API_KEY = os.getenv("AMADEUS_API_KEY")
AMADEUS_API_SECRET = os.getenv("AMADEUS_API_SECRET")

class AmadeusService:
    """
    Service for interacting with the Amadeus API.
    Documentation: https://developers.amadeus.com/
    """

    @staticmethod
    async def get_token() -> str:
        """
        Get a new token for the Amadeus API.
        
        Args:
            None
            
        Returns:
            str: New token for the Amadeus API
        """
        if not AMADEUS_API_KEY or not AMADEUS_API_SECRET:
            logger.error("Amadeus API key or secret not set. Unable to get token.")
            return None
            
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://test.api.amadeus.com/v1/security/oauth2/token",
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    data={
                        "grant_type": "client_credentials",
                        "client_id": AMADEUS_API_KEY,
                        "client_secret": AMADEUS_API_SECRET
                    }
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("access_token")
                    else:
                        logger.error(f"Amadeus login API error: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error getting token: {str(e)}")
            return None
    
    @staticmethod
    async def get_cheapest_quotes(
        origin: str,
        destination: str,
        outbound_date: str,
        inbound_date: str,
        participants: int
    ) -> List[Dict[str, Any]]:
        """
        Get the cheapest quotes for a route.
        
        Args:
            origin (str): Origin place (IATA code)
            destination (str): Destination place (IATA code)
        """
        logger.info(f"Getting cheapest quotes for {origin} to {destination} on {outbound_date} to {inbound_date} for {participants} participants")
        if not AMADEUS_API_KEY or not AMADEUS_API_SECRET:
            logger.error("Amadeus API key or secret not set. Unable to get token.")
            return None
            
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://test.api.amadeus.com/v2/shopping/flight-offers",
                    headers={"Authorization": f"Bearer {await AmadeusService.get_token()}"},
                    params={
                        "originLocationCode": origin,
                        "destinationLocationCode": destination,
                        "departureDate": outbound_date,
                        "returnDate": inbound_date,
                        "adults": participants,
                        "max": 1,
                        "currencyCode": "EUR"
                    }
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        price = data.get("data", [])[0].get("price", {}).get("total", 0)
                        return price
                    else:
                        logger.error(f"Amadeus quotes API error: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error getting quotes: {str(e)}")
            return None
        