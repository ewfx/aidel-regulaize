from neo4j import GraphDatabase
from app.core.config import settings

# Connect to Neo4j
URI = f"bolt://{settings.NEO4J_HOST}:{settings.BOLT_PORT}"
AUTH = (f"{settings.NEO4J_LOGIN}", f"{settings.NEO4J_PASSWORD}")
neo4j_driver = GraphDatabase.driver(URI, auth=AUTH)

# {'cik': '0000320193', 'name': 'Apple Inc.', 'tickers': ['AAPL'], 'state_of_incorporation': 'CA', 'sic': '3571', 'address': {'street1': 'ONE APPLE PARK WAY', 'street2': None, 'city': 'CUPERTINO', 'stateOrCountry': 'CA', 'zipCode': '95014', 'stateOrCountryDescription': 'CA'}, 'owners': [{'name': 'WAGNER SUSAN', 'role': '1'}], 'latest_ownership_filings': {'form': '4', 'filing_date': '2025-02-27', 'accession_number': '0000320193-25-000036'}}

def add_entity(tx, cik, name, tickers, state, sic, address):
    """
    Adds a company node to the graph.
    """
    query = """
    MERGE (c:Company {cik: $cik})
    SET c.name = $name, 
        c.tickers = $tickers, 
        c.state_of_incorporation = $state, 
        c.sic = $sic,
        c.address = $address
    RETURN c
    """
    tx.run(query, cik=cik, name=name, tickers=tickers, state=state, sic=sic, address=address)

def add_person(tx, name, role):
    """
    Adds a person (owner/executive) to the graph.
    """
    query = """
    MERGE (p:Person {name: $name})
    SET p.role = $role
    RETURN p
    """
    tx.run(query, name=name, role=role)

def create_ownership_relationship(tx, person_name, company_cik):
    """
    Creates an ownership relationship between a Person and a Company.
    """
    query = """
    MATCH (p:Person {name: $person_name}), (c:Company {cik: $company_cik})
    MERGE (p)-[:OWNS]->(c)
    RETURN p, c
    """
    tx.run(query, person_name=person_name, company_cik=company_cik)

def add_filing_info(tx, cik, form, filing_date, accession_number):
    """
    Adds latest ownership filing information to a company.
    """
    query = """
    MATCH (c:Company {cik: $cik})
    SET c.latest_filing_form = $form,
        c.latest_filing_date = $filing_date,
        c.latest_filing_accession = $accession_number
    RETURN c
    """
    tx.run(query, cik=cik, form=form, filing_date=filing_date, accession_number=accession_number)

def process_entity_data(entity_data):
    with neo4j_driver.session() as session:
        # Insert company data
        address_str = f"{entity_data['address']['street1']}, {entity_data['address'].get('street2', '')}, {entity_data['address']['city']}, {entity_data['address']['stateOrCountry']} {entity_data['address']['zipCode']}"
        session.execute_write(
            add_entity, 
            entity_data["cik"], entity_data["name"], entity_data["tickers"], 
            entity_data["state_of_incorporation"], entity_data["sic"], address_str
        )

        # Insert owners
        for owner in entity_data["owners"]:
            session.execute_write(add_person, owner["name"], owner["role"])
            session.execute_write(create_ownership_relationship, owner["name"], entity_data["cik"])

        # Insert latest ownership filing
        session.execute_write(
            add_filing_info, entity_data["cik"], 
            entity_data["latest_ownership_filings"]["form"], 
            entity_data["latest_ownership_filings"]["filing_date"], 
            entity_data["latest_ownership_filings"]["accession_number"]
        )

# Example SEC Data