import os
import sys
from pymongo import MongoClient
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Add the root directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 1. Load Environment Variables
load_dotenv()

GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")

if not GEMINI_API_KEY:
    print("ERROR: GOOGLE_API_KEY not found in .env file.")
    sys.exit(1)

# 2. Initialize Clients
try:
    ai_client = genai.Client(api_key=GEMINI_API_KEY)
    
    mongo_client = MongoClient(MONGO_URI)
    db = mongo_client[DB_NAME]
    collection = db["opportunity_taxonomy"]
except Exception as e:
    print(f"ERROR: Failed to connect to services: {e}")
    sys.exit(1)

def get_embedding(text):
    """Generates a 768-dimension vector using the latest Gemini Embedding 2 model."""
    try:
        response = ai_client.models.embed_content(
            model="gemini-embedding-2",
            contents=text,
            # We force it to 768 so it matches your MongoDB Atlas index!
            config=types.EmbedContentConfig(output_dimensionality=768)
        )
        return response.embeddings[0].values
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return None

def update_taxonomy_with_embeddings():
    """Iterates through all documents and adds the embedding_vector field."""
    docs = list(collection.find({"embedding_vector": {"$exists": False}}))
    
    if not docs:
        print("No documents found that need embeddings.")
        return

    for doc in docs:
        print(f"Generating embedding for: {doc.get('name', 'Unnamed Doc')}")
        
        vector = get_embedding(doc['embedding_text'])
        
        if vector:
            collection.update_one(
                {"_id": doc["_id"]},
                {"$set": {"embedding_vector": vector}}
            )
            print(f"Successfully updated {doc['_id']} with Gemini vector.")
        else:
            print(f"Failed to generate vector for {doc['_id']}")

if __name__ == "__main__":
    update_taxonomy_with_embeddings()