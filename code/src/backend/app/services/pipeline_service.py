from typing import Dict, List, Optional
from datetime import datetime
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from app.services.file_service import FileService
from app.services.entity_service import EntityService
from app.services.transaction_service import TransactionService
from app.services.vector_store import VectorStore
from app.services.graph_store import GraphStore
from app.services.entity_extraction import EntityExtractor
from app.models.entity import Entity
from app.models.transaction import Transaction

logger = logging.getLogger(__name__)


class PipelineService:
    def __init__(self):
        self.file_service = FileService()
        self.entity_service = EntityService()
        self.transaction_service = TransactionService()
        self.vector_store = VectorStore()
        self.graph_store = GraphStore()
        self.entity_extractor = EntityExtractor()

    async def process_file(self, file_id: str, db: AsyncIOMotorClient) -> Dict:
        """
        Orchestrate the complete data processing pipeline:
        1. Ingestion: Load and validate file data
        2. Extraction: Parse and extract entities and relationships
        3. Enrichment: Enhance data with external sources
        4. Assessment: Analyze patterns and relationships
        5. Risk Scoring: Calculate risk scores
        6. Reporting: Generate analysis report
        """
        try:
            # 1. Ingestion
            file_data = await self._ingest_file(file_id, db)

            # 2. Extraction
            extracted_data = await self._extract_data(file_data, db)

            # 3. Enrichment
            enriched_data = await self._enrich_data(extracted_data, db)

            # 4. Assessment
            assessment_results = await self._assess_data(enriched_data, db)

            # 5. Risk Scoring
            risk_scores = await self._calculate_risk_scores(assessment_results)

            # 6. Reporting
            report = await self._generate_report(risk_scores)

            # Update file status
            await self.file_service.update_metadata({
                "id": file_id,
                "status": "COMPLETED",
                "pipeline_progress": report
            }, db)

            return report

        except Exception as e:
            logger.error(f"Pipeline processing failed for file {file_id}: {str(e)}")
            # Update file status to failed
            await self.file_service.update_metadata({
                "id": file_id,
                "status": "FAILED",
                "error": str(e)
            }, db)
            raise

    async def _ingest_file(self, file_id: str, db: AsyncIOMotorClient) -> Dict:
        """Load and validate file data"""
        try:
            # Get file metadata
            file_metadata = await self.file_service.get_file(file_id, db)
            if not file_metadata:
                raise ValueError(f"File {file_id} not found")

            # Read file content based on format
            file_path = self.file_service.upload_dir / f"{file_id}.{file_metadata.format.lower()}"

            with open(file_path, 'r') as f:
                content = f.read()

            return {
                "file_id": file_id,
                "metadata": file_metadata.dict(),
                "content": content
            }

        except Exception as e:
            logger.error(f"Error ingesting file {file_id}: {str(e)}")
            raise

    async def _extract_data(self, file_data: Dict, db: AsyncIOMotorClient) -> Dict:
        """Extract entities and relationships from file content"""
        try:
            content = file_data["content"]
            extracted_entities = await self.entity_extractor.extract_entities(content)

            # Store extracted entities
            stored_entities = []
            for category, entities in extracted_entities.items():
                for entity in entities:
                    stored_entity = await self.entity_service.create_or_update_entity(
                        name=entity["text"],
                        entity_type=category.upper(),
                        risk_score=entity.get("risk_score", 0.0),
                        db=db
                    )
                    stored_entities.append(stored_entity)

            return {
                "file_id": file_data["file_id"],
                "entities": stored_entities,
                "raw_entities": extracted_entities
            }

        except Exception as e:
            logger.error(f"Error extracting data: {str(e)}")
            raise

    async def _enrich_data(self, extracted_data: Dict, db: AsyncIOMotorClient) -> Dict:
        """Enrich entities with external data"""
        try:
            enriched_entities = []
            for entity in extracted_data["entities"]:
                enriched_entity = await self.entity_service.enrich_entity(entity.dict(), db)
                enriched_entities.append(enriched_entity)

            return {
                "file_id": extracted_data["file_id"],
                "entities": enriched_entities,
                "raw_entities": extracted_data["raw_entities"]
            }

        except Exception as e:
            logger.error(f"Error enriching data: {str(e)}")
            raise

    async def _assess_data(self, enriched_data: Dict, db: AsyncIOMotorClient) -> Dict:
        """Analyze patterns and relationships"""
        try:
            # Create relationships in graph database
            for entity in enriched_data["entities"]:
                # Store entity in graph database
                await self.graph_store.create_entity(entity.dict())

                # Create relationships with other entities
                for other_entity in enriched_data["entities"]:
                    if entity.id != other_entity.id:
                        relationship_type = self._determine_relationship_type(
                            entity.type,
                            other_entity.type
                        )
                        if relationship_type:
                            await self.graph_store.create_relationship(
                                from_id=str(entity.id),
                                to_id=str(other_entity.id),
                                relationship_type=relationship_type
                            )

            # Calculate centrality scores
            #await self.graph_store.calculate_centrality()

            return enriched_data

        except Exception as e:
            logger.error(f"Error assessing data: {str(e)}")
            raise

    async def _calculate_risk_scores(self, assessment_results: Dict) -> Dict:
        """Calculate risk scores for entities and relationships"""
        try:
            risk_analysis = {
                'entity_risks': [],
                'overall_risk': 0.0,
                'risk_factors': []
            }

            # Calculate entity risk scores
            total_risk = 0
            for entity in assessment_results["entities"]:
                # Base risk score from entity enrichment
                risk_score = entity.risk_score

                # Adjust based on relationships
                relationship_risk = await self._calculate_relationship_risk(entity.id)
                adjusted_risk = (risk_score + relationship_risk) / 2

                risk_analysis['entity_risks'].append({
                    'entity_id': str(entity.id),
                    'name': entity.name,
                    'type': entity.type,
                    'risk_score': adjusted_risk,
                    'risk_factors': self._get_risk_factors(entity)
                })

                total_risk += adjusted_risk

            # Calculate overall risk score
            if risk_analysis['entity_risks']:
                risk_analysis['overall_risk'] = total_risk / len(risk_analysis['entity_risks'])

            return risk_analysis

        except Exception as e:
            logger.error(f"Error calculating risk scores: {str(e)}")
            raise

    async def _generate_report(self, risk_scores: Dict) -> Dict:
        """Generate final analysis report"""
        try:
            report = {
                'timestamp': datetime.utcnow().isoformat(),
                'risk_summary': {
                    'overall_risk_score': risk_scores['overall_risk'],
                    'high_risk_entities': len([e for e in risk_scores['entity_risks'] if e['risk_score'] >= 0.7]),
                    'medium_risk_entities': len(
                        [e for e in risk_scores['entity_risks'] if 0.3 <= e['risk_score'] < 0.7]),
                    'low_risk_entities': len([e for e in risk_scores['entity_risks'] if e['risk_score'] < 0.3])
                },
                'entity_analysis': risk_scores['entity_risks'],
                'risk_factors': risk_scores['risk_factors']
            }

            return report

        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            raise

    # Update the _calculate_relationship_risk method in PipelineService

    async def _calculate_relationship_risk(self, entity_id: str) -> float:
        """Calculate risk score based on entity relationships"""
        try:
            # Get entity connections from graph database
            connections = await self.graph_store.get_entity_connections(str(entity_id))

            if not connections:
                return 0.0

            # Calculate risk based on connected entities
            risk_scores = []
            for connection in connections:
                if connection.get('risk_score') is not None:
                    # Weight risk score by distance (closer connections have more impact)
                    distance_weight = 1.0 / connection['distance']
                    weighted_risk = float(connection['risk_score']) * distance_weight
                    risk_scores.append(weighted_risk)

            # Return maximum weighted risk score or 0 if no valid scores
            return max(risk_scores) if risk_scores else 0.0

        except Exception as e:
            logger.error(f"Error calculating relationship risk: {str(e)}")
            return 0.0

    def _get_risk_factors(self, entity: Entity) -> List[Dict]:
        """Extract risk factors from entity data"""
        risk_factors = []

        # Check OFAC sanctions
        if entity.enrichment_data.ofac and entity.enrichment_data.ofac.get('sanctioned'):
            risk_factors.append({
                'type': 'OFAC_SANCTIONS',
                'severity': 'HIGH',
                'description': 'Entity appears on OFAC sanctions list'
            })

        # Check SEC violations
        if entity.enrichment_data.sec and entity.enrichment_data.sec.get('violations'):
            risk_factors.append({
                'type': 'SEC_VIOLATIONS',
                'severity': 'MEDIUM',
                'description': f"Entity has {len(entity.enrichment_data.sec['violations'])} SEC violations"
            })

        # Check negative media sentiment
        if entity.enrichment_data.media and entity.enrichment_data.media.get('sentiment', 0) < -0.5:
            risk_factors.append({
                'type': 'NEGATIVE_MEDIA',
                'severity': 'MEDIUM',
                'description': 'Entity has significant negative media coverage'
            })

        return risk_factors

    def _determine_relationship_type(self, type1: str, type2: str) -> Optional[str]:
        """Determine the appropriate relationship type between entities"""
        relationship_mapping = {
            ('ORGANIZATION', 'PERSON'): 'ASSOCIATED_WITH',
            ('ORGANIZATION', 'LOCATION'): 'LOCATED_IN',
            ('PERSON', 'LOCATION'): 'LOCATED_IN',
            ('ORGANIZATION', 'ORGANIZATION'): 'TRANSACTS_WITH',
            ('PERSON', 'PERSON'): 'TRANSACTS_WITH'
        }

        pair = tuple(sorted([type1, type2]))
        return relationship_mapping.get(pair)