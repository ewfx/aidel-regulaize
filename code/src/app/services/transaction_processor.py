from typing import List, Dict
import asyncio
from datetime import datetime
from cachetools import TTLCache
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.models.transaction import TransactionRequest, TransactionResponse, EntityRiskProfile
from app.services.entity_extractor import EntityExtractor
from app.services.data_enricher import DataEnricher
from app.services.risk_scorer import RiskScorer
from app.core.logger import get_logger

logger = get_logger(__name__)

class TransactionProcessor:
    def __init__(self):
        self.entity_extractor = EntityExtractor()
        self.data_enricher = DataEnricher()
        self.risk_scorer = RiskScorer()
        self.cache = TTLCache(maxsize=1000, ttl=settings.CACHE_TTL)
        
    async def process(self, transaction: TransactionRequest) -> TransactionResponse:
        start_time = datetime.utcnow()
        
        # Extract entities
        entities = await self.entity_extractor.extract(
            transaction.payer,
            transaction.receiver,
            transaction.description
        )
        
        # Enrich data (parallel processing)
        enrichment_tasks = [
            self.enrich_entity(entity) for entity in entities
        ]
        enriched_entities = await asyncio.gather(*enrichment_tasks)
        
        # Score risks
        risk_profiles = [
            await self.risk_scorer.score(entity)
            for entity in enriched_entities
        ]
        
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return TransactionResponse(
            transactionID=transaction.transactionID,
            entities=risk_profiles,
            auditInfo={
                "processedAt": start_time.isoformat(),
                "processingTimeMs": processing_time
            }
        )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def enrich_entity(self, entity: Dict) -> Dict:
        cache_key = f"entity_{entity['name']}"
        
        # Check cache first
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Parallel enrichment from different sources
        enrichment_tasks = [
            self.data_enricher.get_opencorporates_data(entity),
            self.data_enricher.get_wikidata_info(entity),
            self.data_enricher.get_sec_edgar_data(entity),
            self.data_enricher.get_ofac_status(entity)
        ]
        
        results = await asyncio.gather(*enrichment_tasks, return_exceptions=True)
        
        enriched_data = self._combine_enrichment_results(results)
        self.cache[cache_key] = enriched_data
        
        return enriched_data
    
    async def log_transaction(self, transaction_id: str, result: TransactionResponse):
        # Implement audit logging logic here
        logger.info(f"Transaction {transaction_id} processed successfully")