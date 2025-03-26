import logging
from typing import List, Dict, Optional
from transformers import AutoTokenizer, AutoModelForTokenClassification
import torch
import spacy
from pathlib import Path
import json

logger = logging.getLogger(__name__)

class EntityExtractor:
    def __init__(self):
        try:
            # Initialize BERT model for NER
            self.tokenizer = AutoTokenizer.from_pretrained("dslim/bert-base-NER")
            self.model = AutoModelForTokenClassification.from_pretrained("dslim/bert-base-NER")
            
            # Load spaCy model for additional entity extraction
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                logger.warning("SpaCy model not found. Downloading en_core_web_sm...")
                spacy.cli.download("en_core_web_sm")
                self.nlp = spacy.load("en_core_web_sm")
            
            # Cache directory for storing extracted entities
            self.cache_dir = Path("cache/entities")
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info("Entity extraction models loaded successfully")
            
        except Exception as e:
            logger.error(f"Error initializing entity extraction: {str(e)}")
            raise

    async def extract_entities(self, text: str) -> Dict[str, List[Dict]]:
        """
        Extract entities from text using BERT and spaCy
        """
        try:
            # BERT NER extraction
            bert_entities = await self._extract_bert_entities(text)
            
            # SpaCy extraction for additional entity types
            spacy_entities = self._extract_spacy_entities(text)
            
            # Merge and deduplicate entities
            merged_entities = self._merge_entities(bert_entities, spacy_entities)
            
            # Classify entity risk levels
            classified_entities = self._classify_entity_risk(merged_entities)
            
            return classified_entities
            
        except Exception as e:
            logger.error(f"Error extracting entities: {str(e)}")
            raise

    async def _extract_bert_entities(self, text: str) -> List[Dict]:
        """
        Extract entities using BERT NER model
        """
        try:
            # Tokenize text
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
            
            # Get predictions
            with torch.no_grad():
                outputs = self.model(**inputs)
                predictions = torch.argmax(outputs.logits, dim=2)
            
            # Convert predictions to entities
            tokens = self.tokenizer.convert_ids_to_tokens(inputs["input_ids"][0])
            labels = [self.model.config.id2label[t.item()] for t in predictions[0]]
            
            # Extract entities
            entities = []
            current_entity = None
            
            for token, label in zip(tokens, labels):
                if label.startswith("B-"):
                    if current_entity:
                        entities.append(current_entity)
                    current_entity = {
                        "text": token.replace("##", ""),
                        "type": label[2:],
                        "confidence": 1.0  # Add actual confidence scores if available
                    }
                elif label.startswith("I-") and current_entity:
                    current_entity["text"] += " " + token.replace("##", "")
                elif label == "O":
                    if current_entity:
                        entities.append(current_entity)
                        current_entity = None
            
            if current_entity:
                entities.append(current_entity)
            
            return entities
            
        except Exception as e:
            logger.error(f"Error in BERT entity extraction: {str(e)}")
            raise

    def _extract_spacy_entities(self, text: str) -> List[Dict]:
        """
        Extract entities using spaCy
        """
        try:
            doc = self.nlp(text)
            
            entities = []
            for ent in doc.ents:
                entities.append({
                    "text": ent.text,
                    "type": ent.label_,
                    "confidence": 1.0
                })
            
            return entities
            
        except Exception as e:
            logger.error(f"Error in spaCy entity extraction: {str(e)}")
            raise

    def _merge_entities(self, bert_entities: List[Dict], spacy_entities: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Merge and categorize entities from different sources
        """
        merged = {
            "organizations": [],
            "persons": [],
            "locations": [],
            "dates": [],
            "monetary_values": [],
            "other": []
        }
        
        # Process BERT entities
        for entity in bert_entities:
            category = self._categorize_entity(entity)
            if category in merged:
                if not self._is_duplicate(merged[category], entity):
                    merged[category].append(entity)
        
        # Process spaCy entities
        for entity in spacy_entities:
            category = self._categorize_entity(entity)
            if category in merged:
                if not self._is_duplicate(merged[category], entity):
                    merged[category].append(entity)
        
        return merged

    def _categorize_entity(self, entity: Dict) -> str:
        """
        Categorize entity into predefined types
        """
        type_mapping = {
            "ORG": "organizations",
            "ORGANIZATION": "organizations",
            "PERSON": "persons",
            "PER": "persons",
            "GPE": "locations",
            "LOC": "locations",
            "DATE": "dates",
            "MONEY": "monetary_values"
        }
        
        return type_mapping.get(entity["type"], "other")

    def _is_duplicate(self, entities: List[Dict], new_entity: Dict) -> bool:
        """
        Check if entity already exists in the list
        """
        return any(
            e["text"].lower() == new_entity["text"].lower()
            for e in entities
        )

    def _classify_entity_risk(self, entities: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
        """
        Classify risk level for each entity
        """
        try:
            for category in entities:
                for entity in entities[category]:
                    risk_score = self._calculate_entity_risk(entity, category)
                    entity["risk_score"] = risk_score
                    entity["risk_level"] = self._get_risk_level(risk_score)
            
            return entities
            
        except Exception as e:
            logger.error(f"Error classifying entity risk: {str(e)}")
            raise

    def _calculate_entity_risk(self, entity: Dict, category: str) -> float:
        """
        Calculate risk score for an entity
        """
        base_score = 0.0
        
        # Add category-specific risk factors
        if category == "organizations":
            # Check for high-risk terms in organization names
            high_risk_terms = {"shell", "offshore", "holding", "international"}
            if any(term in entity["text"].lower() for term in high_risk_terms):
                base_score += 0.3
        
        elif category == "locations":
            # Check for high-risk jurisdictions
            high_risk_locations = {"cayman islands", "panama", "dubai", "cyprus"}
            if any(loc in entity["text"].lower() for loc in high_risk_locations):
                base_score += 0.4
        
        # Add confidence-based adjustment
        base_score += (1 - entity.get("confidence", 1.0)) * 0.2
        
        return min(base_score, 1.0)

    def _get_risk_level(self, risk_score: float) -> str:
        """
        Convert risk score to risk level
        """
        if risk_score >= 0.7:
            return "HIGH"
        elif risk_score >= 0.4:
            return "MEDIUM"
        return "LOW"

    async def cache_entity(self, entity_id: str, entity_data: Dict):
        """
        Cache extracted entity data
        """
        try:
            cache_file = self.cache_dir / f"{entity_id}.json"
            async with aiofiles.open(cache_file, 'w') as f:
                await f.write(json.dumps(entity_data))
        except Exception as e:
            logger.error(f"Error caching entity data: {str(e)}")
            raise

    async def get_cached_entity(self, entity_id: str) -> Optional[Dict]:
        """
        Retrieve cached entity data
        """
        try:
            cache_file = self.cache_dir / f"{entity_id}.json"
            if cache_file.exists():
                async with aiofiles.open(cache_file, 'r') as f:
                    data = await f.read()
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error retrieving cached entity: {str(e)}")
            raise