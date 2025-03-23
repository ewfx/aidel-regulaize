from transformers import pipeline
from typing import List, Dict
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

class EntityExtractor:
    def __init__(self):
        self.ner_pipeline = pipeline(
            "ner",
            model="jean-baptiste/roberta-large-ner-english",
            tokenizer="jean-baptiste/roberta-large-ner-english"
        )
    
    async def extract(self, payer: Dict, receiver: Dict, description: str) -> List[Dict]:
        entities = []
        
        # Extract from structured data
        entities.extend([
            self._process_entity(payer),
            self._process_entity(receiver)
        ])
        
        # Extract from description if provided
        if description:
            extracted = self.ner_pipeline(description)
            # Process and deduplicate entities
            for ent in extracted:
                if ent['entity'].startswith('ORG'):
                    entities.append({
                        'name': ent['word'],
                        'confidence': ent['score']
                    })
        
        return self._deduplicate_entities(entities)
    
    def _process_entity(self, entity: Dict) -> Dict:
        return {
            'name': entity['name'],
            'address': entity['address'],
            'confidence': 1.0  # Structured data has full confidence
        }
    
    def _deduplicate_entities(self, entities: List[Dict]) -> List[Dict]:
        # Implement smart deduplication logic
        seen = {}
        unique = []
        
        for entity in entities:
            name = entity['name'].lower()
            if name not in seen or entity['confidence'] > seen[name]['confidence']:
                seen[name] = entity
                
        return list(seen.values())