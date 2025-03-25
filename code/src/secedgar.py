from bs4 import BeautifulSoup
import requests

def search_sec_cik(company_name):
    """
    Searches SEC EDGAR database for a company's CIK number by name.
    """
    search_url = f"https://www.sec.gov/cgi-bin/browse-edgar?company={company_name}&owner=exclude&action=getcompany"
    headers = {"User-Agent": "MyCompanyRiskProfiler/1.0 (shalini.thilakan@gmail.com)"}
    
    response = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    cik_tag = soup.find("a", {"id": "cik"})
    if cik_tag:
        return cik_tag.text.strip()
    return {"error": "CIK not found"}

# Example Usage
company_name = "Tesla"
cik_number = search_sec_cik(company_name)
print(f"CIK for {company_name}: {cik_number}")
