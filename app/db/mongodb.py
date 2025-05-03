from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure
import os
from dotenv import load_dotenv
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "planeit_db")

# MongoDB client instance
client = None
db = None

async def connect_to_mongo():
    """Connect to MongoDB."""
    global client, db
    try:
        client = AsyncIOMotorClient(MONGO_URI)
        # The ismaster command is cheap and does not require auth
        await client.admin.command('ismaster')
        db = client[DB_NAME]
        logger.info("Connected to MongoDB")
    except ConnectionFailure as e:
        logger.error(f"MongoDB connection failed: {e}")
        raise

async def close_mongo_connection():
    """Close MongoDB connection."""
    global client
    if client is not None:
        client.close()
        logger.info("MongoDB connection closed")

# Database collections
def get_collection(collection_name):
    return db[collection_name]

# Collection getters
def get_users_collection():
    return get_collection("users")

def get_plans_collection():
    return get_collection("plans") 