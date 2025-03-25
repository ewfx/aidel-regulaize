import subprocess
import sys
import argparse

# Function to install required packages
def install_packages():
    required_packages = ["pymongo", "xmltodict", "tqdm", "python-dotenv"]
    for package in required_packages:
        subprocess.run([sys.executable, "-m", "pip", "install", package], check=True)

# Install dependencies before execution
install_packages()

import xml.etree.ElementTree as ET
from pymongo import MongoClient
import os
from tqdm import tqdm
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Load MongoDB Configuration (Update as needed)
MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
MONGO_PORT = os.getenv("MONGO_PORT", "27017")
MONGO_URI = f"mongodb://{MONGO_HOST}:{MONGO_PORT}"  # Default to localhost if not found
DATABASE_NAME = os.getenv("MONGO_DB", "regulaizedb")
COLLECTION_NAME = os.getenv("MONGO_OFAC_COLLECTION", "ofac")

# Initialize MongoDB
client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]

# Argument parser for CLI flags
parser = argparse.ArgumentParser(description="Process OFAC SDN XML and store in MongoDB.")
parser.add_argument("--wipe", action="store_true", help="Wipe existing MongoDB data before inserting new records")
args = parser.parse_args()

# If --wipe flag is provided, clear the database
if args.wipe:
    confirm = input("⚠️ WARNING: This will delete all data in the MongoDB sanctions database. Proceed? (yes/no): ")
    if confirm.lower() == "yes":
        collection.delete_many({})
        print("✅ MongoDB sanctions database wiped successfully.")
    else:
        print("❌ Wipe operation canceled.")


def processOFACFile(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    # Extract Namespace
    namespace = {"ofac": "https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/XML"}

    # Process and Insert Data into MongoDB
    sanctions_data = []
    for entry in tqdm(root.findall("ofac:sdnEntry", namespace), desc="Processing XML"):
        data = {
            "uid": entry.findtext("ofac:uid", default="N/A", namespaces=namespace),
            "name": entry.findtext("ofac:lastName", default="N/A", namespaces=namespace),
            "type": entry.findtext("ofac:sdnType", default="N/A", namespaces=namespace),
            "programs": [p.text for p in entry.findall("ofac:programList/ofac:program", namespace)],
            "addresses": [
                {
                    "city": addr.findtext("ofac:city", default="N/A", namespaces=namespace),
                    "address1": addr.findtext("ofac:address1", default="N/A", namespaces=namespace),
                    "address2": addr.findtext("ofac:address2", default="N/A", namespaces=namespace),
                    "address3": addr.findtext("ofac:address3", default="N/A", namespaces=namespace),
                    "postalCode": addr.findtext("ofac:postalCode", default="N/A", namespaces=namespace),
                    "country": addr.findtext("ofac:country", default="N/A", namespaces=namespace),
                }
                for addr in entry.findall("ofac:addressList/ofac:address", namespace)
            ],
            "akaLists": [
                {
                    "uid": akalist.findtext("ofac:uid", default="N/A", namespaces=namespace),
                    "type": akalist.findtext("ofac:type", default="N/A", namespaces=namespace),
                    "category": akalist.findtext("ofac:category", default="N/A", namespaces=namespace),
                    "lastname": akalist.findtext("ofac:lastName", default="N/A", namespaces=namespace),
                }
                for akalist in entry.findall("ofac:akaList/ofac:aka", namespace)
            ],
            "idLists": [
                {
                    "uid": idList.findtext("ofac:uid", default="N/A", namespaces=namespace),
                    "type": idList.findtext("ofac:idType", default="N/A", namespaces=namespace),
                    "number": idList.findtext("ofac:idNumber", default="N/A", namespaces=namespace),
                    "country": idList.findtext("ofac:idCountry", default="N/A", namespaces=namespace),
                }
                for idList in entry.findall("ofac:idList/ofac:id", namespace)
            ],
            "remarks": entry.findtext("ofac:remarks", default="N/A", namespaces=namespace),
        }
        sanctions_data.append(data)

    # Insert Data into MongoDB
    if sanctions_data:
        collection.insert_many(sanctions_data)
        print(f"Inserted {len(sanctions_data)} records into MongoDB!")

    # Create Index for Faster Lookups
    collection.create_index("name")
    collection.create_index("uid")

    print("✅ Sanctions data successfully stored in MongoDB!")


# Parse XML File
sdn_file = "./static_data/sdn.xml"  # Ensure this is the correct path
consolidated_file = "./static_data/consolidated.xml"

# print("Processing SDN file...")
# processOFACFile(sdn_file)
# print("Processing consolidated OFAC file...")
# processOFACFile(consolidated_file)


# # Fetch a sample record
# record = collection.find_one({}, {"_id": 0})
# print(record)

def search_sanctioned_entity(name):
    result = collection.find_one({"name": {"$regex": name, "$options": "i"}})
    return result if result else "No matching entity found."

#print(search_sanctioned_entity("HAVIN BANK LIMITED"))
#print(search_sanctioned_entity("BANK OF KUNLUN CO LTD"))
print(search_sanctioned_entity("golden sands"))
