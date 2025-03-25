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

def get_companies_and_executives():
    """
    Fetches all companies and their executives from Neo4j.
    """
    query = """
    MATCH (p:Person)-[:OWNS]->(c:Company)
    RETURN c.name AS company, p.name AS owner, p.role AS role
    """
    with neo4j_driver.session() as session:
        result = session.execute_read(lambda tx: tx.run(query))
        return [{"company": record["company"], "owner": record["owner"], "role": record["role"]} for record in result]

def get_company_filing_details(company_name):
    """
    Fetches a company's latest ownership filing details.
    """
    query = """
    MATCH (c:Company {name: $company_name})
    RETURN c.name AS company, 
           c.latest_filing_form AS form, 
           c.latest_filing_date AS filing_date, 
           c.latest_filing_accession AS accession_number
    """
    with neo4j_driver.session() as session:
        result = session.execute_read(lambda tx: tx.run(query, company_name=company_name))
        return [record for record in result] if result else {"error": "Company not found"}

def get_company_owners(company_name):
    """
    Fetches all owners of a given company.
    """
    query = """
    MATCH (p:Person)-[:OWNS]->(c:Company {name: $company_name})
    RETURN p.name AS owner, p.role AS role
    """
    with neo4j_driver.session() as session:
        result = session.execute_read(lambda tx: tx.run(query, company_name=company_name))
        return [{"owner": record["owner"], "role": record["role"]} for record in result]



# Example Usage
# risk_data = {
#     "offshore_registration": True,
#     "nominee_directors": True,
#     "transaction_count": 150,
#     "linked_to_sanctioned_entity": True,
#     "risk_score": "HIGH"
# }
def update_company_risk_info(cik, risk_factors):
    """
    Updates a company's risk factors dynamically in Neo4j.
    :param cik: The CIK of the company
    :param risk_factors: Dictionary containing risk-related fields and their values
    """
    set_clause = ", ".join([f"c.{key} = ${key}" for key in risk_factors.keys()])
    query = f"""
    MATCH (c:Company {{cik: $cik}})
    SET {set_clause}
    RETURN c.name AS company, c.cik AS cik, {", ".join([f"c.{key}" for key in risk_factors.keys()])}
    """
    
    with neo4j_driver.session() as session:
        result = session.execute_write(lambda tx: tx.run(query, cik=cik, **risk_factors))
        return [record for record in result]


def find_direct_relationships(entity_name):
    """
    Finds direct relationships of an entity.
    """
    query = """
    MATCH (e {name: $entity_name})-[r]-(other)
    RETURN e.name AS entity, type(r) AS relationship, other.name AS connected_entity
    """
    with neo4j_driver.session() as session:
        result = session.execute_read(lambda tx: tx.run(query, entity_name=entity_name))
        return [{"entity": record["entity"], "relationship": record["relationship"], "connected_entity": record["connected_entity"]} for record in result]

def find_indirect_relationships(entity_name, depth=3):
    """
    Finds indirect relationships of an entity up to a given depth.
    """
    query = f"""
    MATCH (start {{name: $entity_name}})-[*1..{depth}]-(other)
    RETURN start.name AS entity, other.name AS connected_entity, COUNT(*) AS connection_strength
    ORDER BY connection_strength DESC
    """
    with neo4j_driver.session() as session:
        result = session.execute_read(lambda tx: tx.run(query, entity_name=entity_name))
        return [{"entity": record["entity"], "connected_entity": record["connected_entity"], "connection_strength": record["connection_strength"]} for record in result]


def find_high_risk_relationships(identifier):
    """
    Finds all high-risk relationships for a given company or person based on CIK or name.
    :param identifier: CIK (for companies) or entity name
    :return: List of high-risk connections
    """
    query = """
    MATCH (e)-[r]-(connected)
    WHERE (e.cik = $identifier OR e.name = $identifier) 
    AND (connected.risk_score = "HIGH" OR e.risk_score = "HIGH")
    RETURN e.name AS entity, type(r) AS relationship, connected.name AS high_risk_entity, connected.risk_score AS risk_level
    """
    
    with neo4j_driver.session() as session:
        result = session.execute_read(lambda tx: tx.run(query, identifier=identifier))
        return [{"entity": record["entity"], "relationship": record["relationship"], 
                 "high_risk_entity": record["high_risk_entity"], "risk_level": record["risk_level"]} for record in result]
