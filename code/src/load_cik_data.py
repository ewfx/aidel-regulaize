import subprocess
import sys

# Function to install required packages
def install_packages():
    required_packages = ["pymongo"]
    for package in required_packages:
        subprocess.run([sys.executable, "-m", "pip", "install", package], check=True)

# Install dependencies before execution
install_packages()
import json
from pymongo import MongoClient
from app.core.config import settings
from app.database import mongo_db
from app.services.datasources import secedgar_service
import re

# Load MongoDB Configuration (Update as needed)
# MONGO_URI = f"mongodb://{settings.MONGO_HOST}:{settings.MONGO_PORT}"  # Default to localhost if not found
# DATABASE_NAME = settings.MONGO_DB
#COLLECTION_NAME = mongo_db.get_collection(settings.MONGO_CIK_COLLECTION)

# Connect to MongoDB
# client = MongoClient(MONGO_URI)
# db = client[DATABASE_NAME]
# collection = db[COLLECTION_NAME]

collection=mongo_db.get_collection(settings.MONGO_CIK_COLLECTION)


def insert_cik_data():
    # Load JSON data from file
    with open("./static_data/companiesToCIK.json", "r") as file:
        sec_data = json.load(file)

    # # Convert JSON data into a list of dictionaries (MongoDB format)
    # formatted_data = [
    #     {
    #         "cik": str(entry["cik_str"]).zfill(10),  # Ensure CIK is a 10-digit string
    #         "ticker": entry["ticker"],
    #         "name": entry["title"]
    #     }
    #     for entry in sec_data.values()
    # ]

    # Insert data into MongoDB
    #collection.insert_many(formatted_data)
    collection.insert_many(sec_data)

    #collection.create_index([("name", "text")])  # Create a text index

    print(f"Inserted {len(sec_data)} records into MongoDB collection '{COLLECTION_NAME}'")

def get_cik_by_company(company_name):
    """
    Fetches the CIK number for a given company name from MongoDB.
    """
    # result = collection.find({"name": company_name}, {"_id": 0, "cik": 1})
    # return result["cik"] if result else "Company not found"
    escaped_term = re.escape(company_name)  # Escapes special characters
    query = {"name": {"$regex": escaped_term, "$options": "i"}}  # Case-insensitive search

    # Fetch and print results
    results = collection.find(query)
    for doc in results:
        print(doc)

def get_cik_by_company_fuzzy(company_name):
    """
    Fetches the CIK number for a given company name using case-insensitive, partial matching.
    """
    regex = re.compile(f".*{re.escape(company_name)}.*", re.IGNORECASE)  # Create a regex pattern for partial match
    result = collection.find({"name": regex}, {"_id": 0, "cik": 1, "name": 1})
    
    if result:
        return f"CIK for {result['name']} is {result['cik']}"
    return "Company not found"

def get_cik_by_company_text_search(company_name):
    """
    Fetches CIK using MongoDB's full-text search.
    """
    result = collection.find({"$text": {"$search": company_name}}, {"_id": 0, "cik": 1, "name": 1})
    return f"CIK for {result['name']} is {result['cik']}" if result else "Company not found"

def get_company_by_ticker(ticker):
    """
    Fetches company details using a stock ticker symbol.
    """
    result = collection.find_one({"ticker": ticker}, {"_id": 0})
    return result if result else "Ticker not found"

if __name__ == "__main__":
    # confirm = input("Do you want to clear existing 'entity' collection? (y/n): ")
    # if confirm.lower() == 'y':
    #     collection.delete_many({})
    #     print("Existing data cleared!")

    #insert_cik_data()

    # Example Usage
    #company_name = "golden sands"
    # cik = get_cik_by_company_text_search(company_name)
    # print(f"CIK for {company_name}: {cik}")
    # cik = get_cik_by_company(company_name)
    # print(f"CIK for {company_name}: {cik}")
    # cik = get_cik_by_company_fuzzy(company_name)
    # print(f"CIK for {company_name}: {cik}")

    # # Example Usage
    # ticker = "TSLA"
    # company_info = get_company_by_ticker(ticker)
    # print(company_info)

        # Example Usage
    cik = "0000320193"  # Apple Inc.
    company_info = secedgar_service.get_sec_company_info(cik)
    print(company_info)

