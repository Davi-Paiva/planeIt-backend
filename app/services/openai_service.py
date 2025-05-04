import openai
import os
from dotenv import load_dotenv
import logging
from typing import List, Dict, Any, Optional
from app.data.destinations import destinations
from app.db.mongodb import get_destinations_collection
# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get API key from environment variable
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Set up OpenAI client
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY
else:
    logger.warning("OpenAI API key not found. OpenAI services will not work.")

class OpenAIService:
    """
    Service for interacting with OpenAI's API.
    """
    
    @staticmethod
    async def generate_user_summary(prompt: str) -> Optional[str]:
        if not OPENAI_API_KEY:
            logger.error("OpenAI API key not set. Unable to generate response.")
            return None
        
        try:
            client = openai.OpenAI()

            response = client.responses.create(
                model="gpt-4.1-mini",
                input="You are an expert travel assistant generating personalized travel profiles. Based on the user's quiz answers, write a concise but rich paragraph summarizing their travel personality, including their interests, energy level, travel style, budget, preferred destinations, and social preferences. Use a natural, human tone. The persona should feel like a person you could recommend a city to — include what types of places they like, how they like to travel, and what matters most to them." + prompt
            )
            
            return response.output_text
        except Exception as e:
            logger.error(f"Error generating OpenAI response: {str(e)}")
            return None
    
    
    
    @staticmethod
    async def generate_embedding(prompt: str) -> Optional[str]:

        if not OPENAI_API_KEY:
            logger.error("OpenAI API key not set. Unable to generate response.")
            return None
        
        try:
            client = openai.OpenAI()
            response = client.embeddings.create(
                model="text-embedding-3-small",
                input=prompt,
            )
            
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating OpenAI response: {str(e)}")
            return None

    @staticmethod
    async def generate_destination_embeddings() -> Optional[str]:
        if not OPENAI_API_KEY:
            logger.error("OpenAI API key not set. Unable to generate response.")
            return None

        count = await get_destinations_collection().count_documents({"embedding": {"$ne": None}})
        if count >= 50:
            logger.info(f"Destinations collection already has {count} embeddings. Skipping.")
            return

        try:
            for destination in destinations:
                client = openai.OpenAI()

                response = client.responses.create(
                    model="gpt-4.1-mini",
                    input=f"Describe the city {destination['city']}, {destination['country']}. You are a travel assistant generating personality-style profiles for cities, to match them with the right travelers. For each city, write a rich, 4-5 sentence paragraph that describes: The city's overall vibe and energy level Its cultural strengths (food, nightlife, history, nature, etc.)The types of travelers who typically enjoy it The typical budget level (low, medium, high) The pace of life (fast, relaxed, mixed) Avoid listing specific attractions. Instead, describe the feeling of visiting, and what kind of person would fall in love with the place"
                )

                destination_embedding = await OpenAIService.generate_embedding(response.output_text)

                get_destinations_collection().update_one(
                    {"airport_code": destination['airport_code']},
                    {"$set": {"embedding": destination_embedding}}
                )
    
        except Exception as e:
            logger.error(f"Error generating OpenAI response: {str(e)}")
            return None


        return OpenAIService.generate_embedding(response.output_text)

    @staticmethod
    async def check_is_valid_destination(user_summary: str, cities: List[str]) -> Optional[str]:
        if not OPENAI_API_KEY:
            logger.error("OpenAI API key not set. Unable to generate response.")
            return None
        
        try:
            client = openai.OpenAI()

            response = client.responses.create(
                model="gpt-4.1-mini",
                input=f"I have a user with the following summary: {user_summary}. Choose the 15 best cities for this user from the following list: {cities}. Answer with a list of cities separated by commas."
            )

            cities = response.output_text.split(",")
            cities = [city.strip() for city in cities]

            return cities
        except Exception as e:
            logger.error(f"Error generating OpenAI response: {str(e)}")
            return None

        
        
        