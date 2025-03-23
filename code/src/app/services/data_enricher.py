import aiohttp
import ssl
from typing import Dict, Optional
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


class DataEnricher:
    def __init__(self):
        self.session = None
        # Create a default SSL context
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            connector = aiohttp.TCPConnector(ssl=self.ssl_context)
            self.session = aiohttp.ClientSession(connector=connector)
        return self.session

    async def get_opencorporates_data(self, entity: Dict) -> Optional[Dict]:
        try:
            session = await self._get_session()
            # Implement OpenCorporates API call
            return {"status": "active"}  # Placeholder
        except Exception as e:
            logger.error(f"OpenCorporates API error: {str(e)}")
            return None

    async def get_wikidata_info(self, entity: Dict) -> Optional[Dict]:
        try:
            company_name = entity['name']
            entity_id = await self._get_entity_by_label(company_name)

            if not entity_id:
                logger.warning(f"No Wikidata entity found for: {company_name}")
                return None

            details = await self._get_entity_details(entity_id)
            if not details:
                logger.warning(f"Could not fetch Wikidata details for entity ID: {entity_id}")
                return None

            # Extract relevant information
            labels = details.get("labels", {})
            descriptions = details.get("descriptions", {})
            claims = details.get("claims", {})

            return {
                "entityID": details.get("id"),
                "label": labels.get("en", {}).get("value", "N/A"),
                "description": descriptions.get("en", {}).get("value", "N/A"),
                "inception": self._extract_property(claims, "P571"),
                "official_website": self._extract_property(claims, "P856"),
                "headquarters_location": self._extract_property(claims, "P159"),
                "industry": self._extract_property(claims, "P452"),
                "country": self._extract_property(claims, "P17")
            }

        except Exception as e:
            logger.error(f"Wikidata API error: {str(e)}")
            return None

    async def _get_entity_by_label(self, label: str) -> Optional[str]:
        """Search for a Wikidata entity by label using the wbsearchentities API."""
        search_url = "https://www.wikidata.org/w/api.php"
        params = {
            'action': 'wbsearchentities',
            'format': 'json',
            'language': 'en',
            'search': label,
            'type': 'item'
        }

        try:
            session = await self._get_session()
            async with session.get(search_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    search_results = data.get("search", [])
                    if search_results:
                        return search_results[0].get("id")
        except Exception as e:
            logger.error(f"Error searching Wikidata entity: {str(e)}")
        return None

    async def _get_entity_details(self, entity_id: str) -> Optional[Dict]:
        """Fetch detailed information for a given entity using the Wikibase REST API."""
        entity_url = f"https://www.wikidata.org/wiki/Special:EntityData/{entity_id}.json"

        try:
            session = await self._get_session()
            async with session.get(entity_url) as response:
                if response.status == 200:
                    data = await response.json()
                    entities = data.get("entities", {})
                    if entity_id in entities:
                        return entities[entity_id]
        except Exception as e:
            logger.error(f"Error fetching Wikidata entity details: {str(e)}")
        return None

    def _extract_property(self, claims: Dict, prop: str, sub_prop: str = "value") -> Optional[str]:
        """Extracts a property value from claims."""
        if prop in claims:
            try:
                claim = claims[prop][0]
                datavalue = claim.get("mainsnak", {}).get("datavalue", {})
                if sub_prop == "value":
                    return datavalue.get("value")
                else:
                    return datavalue.get(sub_prop)
            except (IndexError, KeyError, TypeError):
                return None
        return None

    async def get_sec_edgar_data(self, entity: Dict) -> Optional[Dict]:
        try:
            session = await self._get_session()
            # Implement SEC EDGAR API call
            return {"filings": []}  # Placeholder
        except Exception as e:
            logger.error(f"SEC EDGAR API error: {str(e)}")
            return None

    async def get_ofac_status(self, entity: Dict) -> Dict:
        try:
            session = await self._get_session()
            # Implement OFAC API call
            return {"listed": False}  # Placeholder
        except Exception as e:
            logger.error(f"OFAC API error: {str(e)}")
            return {"listed": False, "error": str(e)}