import subprocess
import sys

# Function to install required packages
def install_packages():
    required_packages = ["pymongo", "python-dotenv", "pandas[performance]"]
    for package in required_packages:
        subprocess.run([sys.executable, "-m", "pip", "install", package], check=True)

# Install dependencies before execution
install_packages()

import pandas as pd
from pymongo import MongoClient
import os
from app.core.config import settings

# Load MongoDB Configuration (Update as needed)
MONGO_URI = f"mongodb://{settings.MONGO_HOST}:{settings.MONGO_PORT}"  # Default to localhost if not found
DATABASE_NAME = settings.MONGO_DB
COLLECTION_NAME = settings.MONGO_ENTITY_COLLECTION

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]

# CSV File Path
CSV_FILE = "/Users/shalini/Documents/Projects/Hackathon/regulaize/companies_sorted.csv"  # Change this to your actual file path
CHUNK_SIZE = 10000  # Process 10,000 rows at a time to optimize memory

def process_and_insert():
    # Open CSV file in chunks
    for chunk in pd.read_csv(CSV_FILE, chunksize=CHUNK_SIZE):
        records = chunk.to_dict(orient="records")  # Convert chunk to list of dicts
        if records:
            collection.insert_many(records)  # Bulk insert into MongoDB
            print(f"Inserted {len(records)} records into MongoDB")

    print("Data insertion complete!")

def search_entity(name):
    result = collection.find_one({"name": {"$regex": name, "$options": "i"}})
    return result if result else "No matching entity found."

if __name__ == "__main__":
    # Optional: Clear existing data before inserting
    confirm = input("Do you want to clear existing 'entity' collection? (y/n): ")
    if confirm.lower() == 'y':
        collection.delete_many({})
        print("Existing data cleared!")

    # Process and insert data
    process_and_insert()
    collection.create_index("name")

    print(search_entity("Bobcares"))
    print(search_entity("Nykaa"))
