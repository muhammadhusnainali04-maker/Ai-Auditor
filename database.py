import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")

# Synchronous client for scripts (like your update_taxonomy_vectors.py)
sync_client = MongoClient(MONGO_URI)
sync_db = sync_client[DB_NAME]

# Asynchronous client for FastAPI (used by main.py)
async_client = AsyncIOMotorClient(MONGO_URI)
async_db = async_client[DB_NAME]

# THIS IS THE FUNCTION MAIN.PY IS LOOKING FOR:
def get_collection(name: str):
    """Returns an asynchronous MongoDB collection."""
    return async_db[name]