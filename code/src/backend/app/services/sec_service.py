from typing import Dict, List, Optional
import logging
from datetime import datetime
import aiohttp

logger = logging.getLogger(__name__)

class SECService:
    def __init__(self):
        self.collection_name = "sec_data"
        self.edgar_base_url = "https://data.sec.gov/api"
        self.headers = {
            "User-Agent": "RiskAnalysisSystem 1.0",
            "Accept-Encoding": "gzip, deflate",
            "Host": "data.sec.gov"
        }

    async def get_company_info(self, cik: str, db) -> Optional[Dict]:
        """
        Retrieve company information from SEC EDGAR.
        """
        try:
            # First check local cache
            cached_data = await db[self.collection_name].find_one({"cik": cik})
            
            if cached_data and self._is_cache_valid(cached_data.get("last_updated")):
                return cached_data
            
            # If not in cache or cache expired, fetch from EDGAR
            async with aiohttp.ClientSession() as session:
                url = f"{self.edgar_base_url}/companies/{cik}"
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Transform and store in cache
                        company_data = {
                            "cik": cik,
                            "name": data.get("name"),
                            "sic": data.get("sic"),
                            "industry": data.get("industry"),
                            "state": data.get("state"),
                            "last_updated": datetime.utcnow()
                        }
                        
                        await db[self.collection_name].update_one(
                            {"cik": cik},
                            {"$set": company_data},
                            upsert=True
                        )
                        
                        return company_data
                    
                    elif response.status == 404:
                        logger.warning(f"Company with CIK {cik} not found in EDGAR")
                        return None
                    
                    else:
                        logger.error(f"SEC API error: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error retrieving SEC data for CIK {cik}: {str(e)}")
            raise

    async def get_filings(self, cik: str, db, filing_type: Optional[str] = None) -> List[Dict]:
        """
        Retrieve recent filings for a company.
        """
        try:
            query = {"cik": cik}
            if filing_type:
                query["form_type"] = filing_type
                
            filings = await db[f"{self.collection_name}_filings"].find(
                query
            ).sort("filing_date", -1).limit(10).to_list(length=10)
            
            return filings
            
        except Exception as e:
            logger.error(f"Error retrieving filings for CIK {cik}: {str(e)}")
            raise

    def _is_cache_valid(self, last_updated: datetime) -> bool:
        """
        Check if cached data is still valid (less than 24 hours old).
        """
        if not last_updated:
            return False
            
        age = datetime.utcnow() - last_updated
        return age.total_seconds() < 86400  # 24 hours

    async def update_company_filings(self, cik: str, db) -> None:
        """
        Update local cache of company filings from EDGAR.
        """
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.edgar_base_url}/companies/{cik}/filings"
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        filings = await response.json()
                        
                        # Transform and store filings
                        for filing in filings.get("filings", []):
                            filing_data = {
                                "cik": cik,
                                "form_type": filing.get("form"),
                                "filing_date": filing.get("filingDate"),
                                "description": filing.get("description"),
                                "file_number": filing.get("fileNumber"),
                                "last_updated": datetime.utcnow()
                            }
                            
                            await db[f"{self.collection_name}_filings"].update_one(
                                {
                                    "cik": cik,
                                    "file_number": filing.get("fileNumber")
                                },
                                {"$set": filing_data},
                                upsert=True
                            )
                            
                        logger.info(f"Updated filings for CIK {cik}")
                        
                    else:
                        logger.error(f"Error updating filings for CIK {cik}: {response.status}")
                        
        except Exception as e:
            logger.error(f"Error updating filings for CIK {cik}: {str(e)}")
            raise