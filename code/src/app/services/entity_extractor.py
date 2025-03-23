from transformers import pipeline
from typing import List, Dict
from app.core.config import settings
from app.core.logger import get_logger
from app.models.transaction import Entity

logger = get_logger(__name__)


class EntityExtractor:
    def __init__(self):
        self.ner_pipeline = pipeline(
            "ner",
            model="dslim/bert-base-NER",
            tokenizer="dslim/bert-base-NER",
            aggregation_strategy="simple"  # Merge overlapping entities
        )

    async def extract(self, payer: Entity, receiver: Entity, description: str) -> List[Dict]:
        entities = []

        # Extract from structured data
        entities.extend([
            self._process_entity(payer),
            self._process_entity(receiver)
        ])

        # Extract from description if provided
        if description:
            try:
                extracted = self.ner_pipeline(description)
                # Process extracted entities
                for ent in extracted:
                    if ent['entity_group'] in ['ORG', 'MISC']:  # Focus on organization names
                        entities.append({
                            'name': ent['word'],
                            'confidence': ent['score'],
                            'type': ent['entity_group']
                        })
            except Exception as e:
                logger.error(f"Error in NER extraction: {str(e)}")

        return self._deduplicate_entities(entities)

    def _process_entity(self, entity: Entity) -> Dict:
        return {
            'name': entity.name,
            'address': entity.address.dict(),
            'confidence': 1.0,  # Structured data has full confidence
            'type': 'ORG'  # Default type for structured entities
        }

    def _deduplicate_entities(self, entities: List[Dict]) -> List[Dict]:
        seen = {}

        for entity in entities:
            name = entity['name'].lower()
            if name not in seen or entity['confidence'] > seen[name]['confidence']:
                seen[name] = entity

        return list(seen.values())