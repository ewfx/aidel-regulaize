import requests

def get_entity_by_label(label):
    """
    Search for a Wikidata entity by label using the wbsearchentities API.
    Returns the first matching entity ID if found.
    """
    search_url = "https://www.wikidata.org/w/api.php"
    params = {
        'action': 'wbsearchentities',
        'format': 'json',
        'language': 'en',
        'search': label
    }
    response = requests.get(search_url, params=params)
    if response.status_code == 200:
        data = response.json()
        search_results = data.get("search", [])
        if search_results:
            # Return the entity id of the top result
            return search_results[0].get("id")
    return None

def get_entity_details(entity_id):
    """
    Fetch detailed information for a given entity using the Wikibase REST API.
    Uses the Special:EntityData endpoint which returns a JSON representation.
    """
    entity_url = f"https://www.wikidata.org/wiki/Special:EntityData/{entity_id}.json"
    response = requests.get(entity_url)
    if response.status_code == 200:
        data = response.json()
        entities = data.get("entities", {})
        if entity_id in entities:
            return entities[entity_id]
    return None

def extract_property(claims, prop, sub_prop="value"):
    """
    Extracts a property value from claims.
    This helper function retrieves the 'datavalue' of the first claim for the given property.
    """
    if prop in claims:
        claim = claims[prop][0]
        datavalue = claim.get("mainsnak", {}).get("datavalue", {})
        if sub_prop == "value":
            return datavalue.get("value")
        else:
            return datavalue.get(sub_prop)
    return None

def get_company_details(company_label):
    """
    Given a company label, this function searches for the company in Wikidata
    and then retrieves its detailed information including additional properties.
    """
    entity_id = get_entity_by_label(company_label)
    if not entity_id:
        print("Entity not found for label:", company_label)
        return None

    details = get_entity_details(entity_id)
    if not details:
        print("Could not fetch details for entity ID:", entity_id)
        return None

    # Basic details
    labels = details.get("labels", {})
    descriptions = details.get("descriptions", {})
    claims = details.get("claims", {})

    company_info = {
        "entityID": details.get("id"),
        "label": labels.get("en", {}).get("value", "N/A"),
        "description": descriptions.get("en", {}).get("value", "N/A"),
        "inception": extract_property(claims, "P571"),          # Inception Date
        "official_website": extract_property(claims, "P856"),     # Official Website
        "headquarters_location": extract_property(claims, "P159"),# Headquarters Location
        "industry": extract_property(claims, "P452"),             # Industry
        "country": extract_property(claims, "P17")                # Country
    }

    return company_info

# Example usage:
if __name__ == "__main__":
    company_name = "Tesla inc"
    company_details = get_company_details(company_name)
    if company_details:
        print("Company Details:")
        print(f"Entity ID: {company_details.get('entityID')}")
        print(f"Label: {company_details.get('label')}")
        print(f"Description: {company_details.get('description')}")
        print(f"Inception Date: {company_details.get('inception')}")
        print(f"Official Website: {company_details.get('official_website')}")
        print(f"Headquarters Location: {company_details.get('headquarters_location')}")
        print(f"Industry: {company_details.get('industry')}")
        print(f"Country: {company_details.get('country')}")
    else:
        print("No details found for the company.")
