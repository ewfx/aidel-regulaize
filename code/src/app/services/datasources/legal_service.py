import requests
from app.core.config import settings
from datetime import datetime
from collections import defaultdict



# Set up headers
headers = {
    "Authorization": f"Token {settings.COURTLISTENER_API_KEY}",
    "Accept": settings.COURTLISTENER_RESPONSE_FORMAT
}

# Function to process JSON response from CourtListener API
def process_courtlistener_data(json_data, entity_name):
    cases = json_data.get("results", [])
    
    total_cases = len(cases)  # 1. Total number of cases
    ongoing_cases = []
    sued_cases = []
    court_outcomes = defaultdict(lambda: {"win": 0, "loss": 0, "unknown": 0})

    current_year = datetime.now().year

    for case in cases:
        case_name = case.get("caseName", "").lower()
        court = case.get("court", "Unknown Court")
        date_filed = case.get("dateFiled", "")
        docket_number = case.get("docketNumber", "N/A")
        case_url = case.get("absolute_url", "No URL Available")
        opinions = case.get("opinions", [])

        # Check if case is ongoing (no final ruling)
        if date_filed:
            case_year = int(date_filed[:4])  # Extract year
            if case_year >= (current_year - 2) and not opinions:  # No ruling yet
                ongoing_cases.append({
                    "case_name": case_name,
                    "docket_number": docket_number,
                    "court": court,
                    "url": case_url
                })

                # Check if Tesla is the defendant (being sued)
                if "v." in case_name:
                    parts = case_name.split(" v. ")
                    if len(parts) == 2:
                        plaintiff, defendant = parts
                        if entity_name.lower() in defendant:
                            sued_cases.append({
                                "case_name": case_name,
                                "docket_number": docket_number,
                                "court": court,
                                "url": case_url
                            })

        # Check case outcome (win/loss tracking)
        if "v." in case_name:
            parts = case_name.split(" v. ")
            if len(parts) == 2:
                plaintiff, defendant = parts
                if entity_name.lower() in plaintiff:
                    court_outcomes[court]["win"] += 1
                elif entity_name.lower() in defendant:
                    court_outcomes[court]["loss"] += 1
                else:
                    court_outcomes[court]["unknown"] += 1

    total_ongoing_cases = len(ongoing_cases)  # 2. Total ongoing cases
    total_sued_cases = len(sued_cases)  # 3. Cases where Tesla is the defendant

    # 4. Identify courts ruling against Tesla frequently
    court_loss_ratio = {
        court: outcomes["loss"] / (outcomes["win"] + outcomes["loss"] + 1)  # Avoid division by zero
        for court, outcomes in court_outcomes.items()
    }
    
    # Sort courts by highest loss ratio
    sorted_loss_courts = sorted(court_loss_ratio.items(), key=lambda x: x[1], reverse=True)

    # # Display Results
    # print(f"📌 Total cases against {entity_name}: {total_cases}")
    # print(f"📌 Total ongoing cases: {total_ongoing_cases}")
    # print(f"📌 Cases where {entity_name} is being sued: {total_sued_cases}")

    # print("\n📝 List of Ongoing Cases:")
    # for case in ongoing_cases[:10]:  # Show first 10 ongoing cases
    #     print(f"  📂 {case['case_name']} | Docket: {case['docket_number']} | Court: {case['court']}")
    #     print(f"  🔗 {case['url']}")
    #     print("-" * 80)

    # print("\n🏛 Courts that rule against Tesla frequently:")
    # for court, loss_ratio in sorted_loss_courts[:10]:  # Top 10 courts
    #     print(f"  🔴 {court}: {loss_ratio:.2f} loss ratio")

    return {
        "total_cases": total_cases,
        "total_ongoing_cases": total_ongoing_cases,
        "total_sued_cases": total_sued_cases,
        "ongoing_cases": ongoing_cases,
        "court_loss_ratios": sorted_loss_courts
    }

def fetch_legal_cases(entityname):
    # Define API URL
    url = f"{settings.COURTLISTENER_URL}?q={entityname}"
    # Make the GET request
    response = requests.get(url, headers=headers)

    # Check if request was successful
    if response.status_code == 200:
        # Save response to a file
        json_data = response.json()
        return process_courtlistener_data(json_data, entityname)
    else:
        print(f"Error {response.status_code}: {response.text}")
