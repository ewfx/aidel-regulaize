from neo4j import AsyncGraphDatabase
from app.core.config import settings
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class GraphStore:
    def __init__(self):
        self.driver = AsyncGraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )
        self.relationship_types = [
            'ASSOCIATED_WITH',
            'LOCATED_IN',
            'TRANSACTS_WITH',
            'OWNS'
        ]

    async def close(self):
        await self.driver.close()

    async def create_entity(self, entity_data: Dict):
        """Create or update entity node in Neo4j"""
        async with self.driver.session() as session:
            try:
                query = """
                MERGE (e:Entity {id: $id})
                SET e += $properties
                RETURN e
                """
                properties = {
                    "id": str(entity_data["id"]),  # Ensure ID is string
                    "name": entity_data["name"],
                    "type": entity_data["type"],
                    "role": entity_data["role"],
                    "risk_score": float(entity_data.get("risk_score", 0.0))
                }
                await session.run(query, {"id": str(entity_data["id"]), "properties": properties})
                logger.info(f"Created/updated entity node for {entity_data['name']}")
            except Exception as e:
                logger.error(f"Error creating entity node: {str(e)}")
                raise

    async def get_entity_connections(self, entity_id: str, depth: int = 2) -> List[Dict]:
        """Get entity connections up to specified depth with risk scores"""
        async with self.driver.session() as session:
            try:
                query = """
                MATCH (e:Entity {id: $entity_id})
                CALL {
                    WITH e
                    MATCH (e)-[r:ASSOCIATED_WITH|LOCATED_IN|TRANSACTS_WITH|OWNS*1..$depth]-(connected:Entity)
                    RETURN connected.id AS connected_id,
                           connected.name AS connected_name,
                           connected.risk_score AS risk_score,
                           type(last(r)) AS relationship_type,
                           length(r) AS distance
                }
                RETURN collect({
                    id: connected_id,
                    name: connected_name,
                    risk_score: risk_score,
                    relationship_type: relationship_type,
                    distance: distance
                }) AS connections
                """
                
                result = await session.run(query, {
                    "entity_id": str(entity_id),
                    "depth": depth
                })
                
                connections = []
                async for record in result:
                    connections.extend(record["connections"])
                
                return connections
            except Exception as e:
                logger.error(f"Error getting entity connections: {str(e)}")
                raise

    async def create_relationship(self, from_id: str, to_id: str, relationship_type: str, properties: Dict = None):
        """Create relationship between entities"""
        async with self.driver.session() as session:
            try:
                # Convert relationship type to valid Neo4j format
                rel_type = relationship_type.upper().replace(" ", "_")
                
                if rel_type not in self.relationship_types:
                    logger.warning(f"Invalid relationship type: {rel_type}. Using ASSOCIATED_WITH instead.")
                    rel_type = "ASSOCIATED_WITH"
                
                query = """
                MATCH (from:Entity)
                WHERE from.id = $from_id
                MATCH (to:Entity)
                WHERE to.id = $to_id
                MERGE (from)-[r:`%s`]->(to)
                SET r += $properties
                RETURN r
                """ % rel_type
                
                await session.run(query, {
                    "from_id": str(from_id),
                    "to_id": str(to_id),
                    "properties": properties or {
                        "created_at": datetime.utcnow().isoformat(),
                        "weight": 1.0
                    }
                })
                logger.info(f"Created relationship {rel_type} between entities {from_id} and {to_id}")
            except Exception as e:
                logger.error(f"Error creating relationship: {str(e)}")
                raise

    async def calculate_centrality(self, entity_type: str = None):
        """Calculate PageRank centrality for entities"""
        async with self.driver.session() as session:
            try:
                # First check if we have any relationships
                count_query = """
                MATCH ()-[r]->() 
                RETURN count(r) as rel_count
                """
                count_result = await session.run(count_query)
                rel_count = 0
                async for record in count_result:
                    rel_count = record["rel_count"]

                if rel_count == 0:
                    logger.warning("No relationships found. Creating default relationships.")
                    await self._create_default_relationships(session)

                # Drop existing graph if it exists
                await session.run("""
                CALL gds.graph.exists('entityGraph')
                YIELD exists
                WITH exists
                WHERE exists
                CALL gds.graph.drop('entityGraph')
                YIELD graphName
                RETURN graphName
                """)

                # Create graph projection
                create_query = """
                CALL gds.graph.project(
                    'entityGraph',
                    'Entity',
                    {
                        ASSOCIATED_WITH: {orientation: 'UNDIRECTED'},
                        LOCATED_IN: {orientation: 'UNDIRECTED'},
                        TRANSACTS_WITH: {orientation: 'UNDIRECTED'},
                        OWNS: {orientation: 'UNDIRECTED'}
                    }
                )
                """
                await session.run(create_query)

                # Run PageRank
                pagerank_query = """
                CALL gds.pageRank.write('entityGraph', {
                    writeProperty: 'pagerank',
                    maxIterations: 20,
                    dampingFactor: 0.85
                })
                YIELD nodePropertiesWritten
                RETURN nodePropertiesWritten
                """
                await session.run(pagerank_query)

                # Clean up
                await session.run("""
                CALL gds.graph.drop('entityGraph')
                YIELD graphName
                RETURN graphName
                """)

                logger.info("Successfully calculated centrality scores")
            except Exception as e:
                logger.error(f"Error calculating centrality: {str(e)}")
                raise

    async def _create_default_relationships(self, session):
        """Create default relationships between entities if none exist"""
        try:
            query = """
            MATCH (e1:Entity), (e2:Entity)
            WHERE e1 <> e2 AND NOT (e1)-[:ASSOCIATED_WITH]-(e2)
            WITH e1, e2
            LIMIT 100
            CREATE (e1)-[r:ASSOCIATED_WITH {
                created_at: datetime()
            }]->(e2)
            RETURN count(r) as created
            """
            result = await session.run(query)
            
            created = 0
            async for record in result:
                created = record["created"]
            
            logger.info(f"Created {created} default ASSOCIATED_WITH relationships")
        except Exception as e:
            logger.error(f"Error creating default relationships: {str(e)}")
            raise

    async def create_initial_constraints(self):
        """Create necessary Neo4j constraints"""
        async with self.driver.session() as session:
            try:
                # Create constraint on Entity id
                await session.run("""
                CREATE CONSTRAINT entity_id IF NOT EXISTS
                FOR (e:Entity) REQUIRE e.id IS UNIQUE
                """)
                
                logger.info("Created Neo4j constraints")
            except Exception as e:
                logger.error(f"Error creating constraints: {str(e)}")
                raise