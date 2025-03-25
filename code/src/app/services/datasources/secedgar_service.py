from bs4 import BeautifulSoup
import requests
import re
from app.database import mongo_db
from app.core.config import settings
import xml.etree.ElementTree as ET

cik_collection = mongo_db.get_collection(settings.MONGO_CIK_COLLECTION)
headers = {"User-Agent": f"MyCompanyRiskProfiler/1.0 ({settings.EMAIL})"}

def get_cik_by_company(company_name):
    """
    Fetches the CIK number for a given company name from MongoDB.
    """
    # result = collection.find({"name": company_name}, {"_id": 0, "cik": 1})
    # return result["cik"] if result else "Company not found"
    escaped_term = re.escape(company_name)  # Escapes special characters
    query = {"name": {"$regex": escaped_term, "$options": "i"}}  # Case-insensitive search

    # Fetch and print results
    results = cik_collection.find(query)
    for doc in results:
        print(doc)

# def search_sec_cik(company_name):
#     """
#     Searches SEC EDGAR database for a company's CIK number by name.
#     """
#     search_url = f"https://www.sec.gov/cgi-bin/browse-edgar?company={company_name}&owner=exclude&action=getcompany"
#     headers = {"User-Agent": "MyCompanyRiskProfiler/1.0 (shalini.thilakan@gmail.com)"}
    
#     response = requests.get(search_url, headers=headers)
#     soup = BeautifulSoup(response.text, 'html.parser')

#     cik_tag = soup.find("a", {"id": "cik"})
#     if cik_tag:
#         return cik_tag.text.strip()
#     return {"error": "CIK not found"}

import requests

def get_latest_ownership_filing(forms, filing_dates, accession_numbers):
    for i, form in enumerate(forms):
        if form in ["4", "13D", "13G"]:  # Look for ownership filings
            return {
                "form": form,
                "filing_date": filing_dates[i],
                "accession_number": accession_numbers[i]
            }
    return False


def get_filing_directory(cik, accession_number):
    """
    Fetches the SEC filing directory to find XML files.
    """
    base_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_number.replace('-', '')}/"

    response = requests.get(base_url, headers=headers)
    if response.status_code != 200:
        print(f"failed here : {response.status_code}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    # Find the XML file (Form 4, 13D, 13G filings are usually in XML format)
    for link in soup.find_all("a"):
        href = link.get("href")
        if href and href.endswith(".xml"):
            return f"https://www.sec.gov{href}"

    return None


def get_beneficial_owners(cik, accession_number):
    """
    Fetches beneficial owners from SEC Form 4, 13D, or 13G XML filing.
    :param cik: Central Index Key (CIK) of the company
    :param accession_number: Accession Number of the filing
    :return: List of owners and their roles
    """
    print(f"Fetching beneficial owners for {cik} and {accession_number}")
    xml_url = get_filing_directory(cik, accession_number)
    if not xml_url:
        print(f"No XML filing found for this accession number : {accession_number}")
        return None
    

    response = requests.get(xml_url, headers=headers)

    if response.status_code != 200:
        print(f"failed here : {response.status_code}")
        return None

    # Parse XML content
    #print(response.text)
    root = ET.fromstring(response.text)
    owners = []

    for owner in root.findall(".//reportingOwner"):
        owner_name = owner.findtext(".//rptOwnerName", default="Unknown")

        # Extract officer title, default to None
        officer_title = owner.findtext(".//officerTitle")

        # Check if the person is a director
        is_director = owner.findtext(".//isDirector", default="0")
        is_officer = owner.findtext(".//isOfficer", default="0")
        is_ten_percent_owner = owner.findtext(".//isTenPercentOwner", default="0")
        is_other = owner.findtext(".//isOther", default="0")

        # Map numeric roles to human-readable labels
        role = officer_title if officer_title else None
        if is_director == "1":
            role = "Director"
        elif is_officer == "1" and not role:
            role = "Officer"
        elif is_ten_percent_owner == "1":
            role = "10%+ Shareholder"
        elif is_other == "1":
            role = "Other"

        if not role:
            role = "Investor/Director"  # Default fallback

        owners.append({"name": owner_name, "role": role})

    return owners


def get_sec_company_info(cik):
    """
    Fetches company information from SEC EDGAR filings.
    :param cik: Central Index Key (CIK) of the company
    :return: JSON response with company details
    """
    base_url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    headers = {"User-Agent": f"MyCompanyRiskProfiler/1.0 ({settings.EMAIL})"}  # SEC requires a custom user agent

    response = requests.get(base_url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()

        # Extract relevant fields
        company_info = {
            "cik": cik,
            "name": data.get("name", "N/A"),
            "tickers": data.get("tickers", []),
            "state_of_incorporation": data.get("stateOfIncorporation", "N/A"),
            "sic": data.get("sic", "N/A"),
            "address": data.get("addresses", {}).get("business", {}),
            "owners": [],
            "latest_ownership_filings": ""
        }

        # Extract latest SEC filings
        filings = data.get("filings", {}).get("recent", {})

        # Extract filing types and accession numbers
        forms = filings.get("form", [])
        filing_dates = filings.get("filingDate", [])
        accession_numbers = filings.get("accessionNumber", [])

        latest_ownership_filing = get_latest_ownership_filing(forms, filing_dates, accession_numbers)
        if(latest_ownership_filing):
            company_info["latest_ownership_filings"] = latest_ownership_filing
            owners = get_beneficial_owners(cik, latest_ownership_filing.get("accession_number"))
            if(owners):
                company_info["owners"] = owners


        # for form, filing_date, accession in zip(filings.get("form", []), filings.get("filingDate", []), filings.get("accessionNumber", [])):
        #     if form in ["10-K", "8-K", "S-1"]:
        #         company_info["latest_filings"].append({
        #             "form": form,
        #             "filing_date": filing_date,
        #             "accession_number": accession
        #         })
        #     elif form in ["3", "4", "5", "13D", "13G"]:
        #         company_info["latest_ownership_filings"].append({
        #             "form": form,
        #             "filing_date": filing_date,
        #             "accession_number": accession
        #         })

        return company_info
    else:
        return {"error": f"Failed to fetch data for CIK {cik}. Status Code: {response.status_code}"}





# # Example Usage
# company_name = "Tesla"
# cik_number = search_sec_cik(company_name)
# print(f"CIK for {company_name}: {cik_number}")
