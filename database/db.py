from pymongo import MongoClient
from dotenv import load_dotenv
import os
import certifi

load_dotenv()
uri = os.environ.get("uri")

# Connect to MongoDB Atlas securely
client = MongoClient(uri, tlsCAFile=certifi.where())

# Test connection
try:
    client.admin.command("ping")
    print("Connected to MongoDB successfully!")
except Exception as e:
    print("Error connecting to MongoDB:", e)

# Database and collection
db = client["PostAI"]
signup_collection = db["postData"]
postlist_collection = db["postlist"]

