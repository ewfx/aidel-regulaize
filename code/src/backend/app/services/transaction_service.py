from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.models.transaction import Transaction, TransactionCreate, TransactionUpdate
from app.services.entity_service import EntityService
from app.services.kafka_service import KafkaService
from app.services.graph_store import GraphStore
from typing import List, Optional, Dict, Tuple
import logging
from datetime import datetime
from uuid import uuid4
import json

logger = logging.getLogger(__name__)

class TransactionService:
    def __init__(self):
        self.collection_name = "transactions"
        self.entity_service = EntityService()
        self.kafka_service = KafkaService()
        self.graph_store = GraphStore()

    async def create_transaction(self, db: AsyncIOMotorDatabase, transaction_data: TransactionCreate) -> Transaction:
        """Create a new transaction"""
        try:
            # Create new transaction
            transaction = Transaction(
                id=str(uuid4()),
                transaction_id=transaction_data.transaction_id,
                raw_data=transaction_data.raw_data,
                file_id=transaction_data.file_id,
                sender=transaction_data.sender,
                receiver=transaction_data.receiver,
                amount=transaction_data.amount,
                date=transaction_data.date,
                additional_notes=transaction_data.additional_notes,
                status="PENDING"
            )
            
            # Insert into database
            await db[self.collection_name].insert_one(transaction.dict())
            
            # Publish to Kafka for async processing
            await self.kafka_service.publish_transaction(transaction.dict())
            
            return transaction
            
        except Exception as e:
            logger.error(f"Error creating transaction: {str(e)}")
            raise

    async def _calculate_risk_score(self, transaction: Dict) -> Dict:
        """
        Calculate transaction risk score and generate explanation using LLM
        Returns risk assessment with score, confidence, evidence, and reasoning
        """
        try:
            # Prepare transaction context for LLM
            context = self._prepare_llm_context(transaction)
            
            # Generate LLM prompt
            prompt = f"""
            Analyze the following transaction for risk assessment:
            
            Transaction Details:
            - ID: {transaction.get('transaction_id', 'Unknown')}
            - Amount: {json.dumps(transaction.get('amount', {}))}
            - Sender: {json.dumps(transaction.get('sender', {}))}
            - Receiver: {json.dumps(transaction.get('receiver', {}))}
            - Date: {transaction.get('date', 'Unknown')}
            - Notes: {transaction.get('additional_notes', '')}
            
            Extracted Entities:
            {json.dumps(transaction.get('extracted_entities', {}), indent=2)}
            
            Based on the above information, provide:
            1. Risk score (0.0 to 1.0)
            2. Confidence score (0.0 to 1.0)
            3. Supporting evidence (list)
            4. Detailed reasoning for the risk assessment
            """
            
            # Call local LLM for analysis
            llm_response = await self._get_llm_analysis(prompt)
            
            # Parse LLM response
            risk_score, confidence_score, evidence, reason = self._parse_llm_response(llm_response)
            
            # Combine with rule-based risk factors
            risk_factors = await self._calculate_rule_based_risk_factors(transaction)
            
            # Adjust final risk score
            final_risk_score = self._combine_risk_scores(
                llm_risk_score=risk_score,
                rule_based_factors=risk_factors
            )
            
            return {
                "risk_score": final_risk_score,
                "confidence_score": confidence_score,
                "supporting_evidence": evidence,
                "risk_factors": risk_factors,
                "reason": reason
            }
            
        except Exception as e:
            logger.error(f"Error calculating risk score: {str(e)}")
            return {
                "risk_score": 0.5,  # Default moderate risk
                "confidence_score": 0.0,
                "supporting_evidence": ["Error in risk calculation"],
                "risk_factors": [],
                "reason": f"Error calculating risk: {str(e)}"
            }

    def _prepare_llm_context(self, transaction: Dict) -> Dict:
        """Prepare transaction context for LLM analysis"""
        return {
            "transaction": {
                "id": transaction.get("transaction_id"),
                "amount": transaction.get("amount"),
                "date": transaction.get("date"),
                "notes": transaction.get("additional_notes")
            },
            "parties": {
                "sender": transaction.get("sender"),
                "receiver": transaction.get("receiver")
            },
            "entities": transaction.get("extracted_entities", {})
        }

    async def _get_llm_analysis(self, prompt: str) -> str:
        """Get risk analysis from local LLM"""
        try:
            # Example response format for development
            # In production, replace with actual LLM call
            return """
            {
                "risk_score": 0.65,
                "confidence_score": 0.95,
                "evidence": [
                    "Multiple high-risk jurisdictions involved",
                    "Complex transaction structure",
                    "Historical pattern analysis"
                ],
                "reasoning": "Transaction involves entities from high-risk jurisdictions with complex ownership structure. Historical analysis shows similar patterns to previously flagged transactions."
            }
            """
        except Exception as e:
            logger.error(f"Error getting LLM analysis: {str(e)}")
            raise

    def _parse_llm_response(self, response: str) -> Tuple[float, float, List[str], str]:
        """Parse LLM response into structured format"""
        try:
            data = json.loads(response)
            return (
                float(data.get("risk_score", 0.5)),
                float(data.get("confidence_score", 0.0)),
                data.get("evidence", []),
                data.get("reasoning", "No reasoning provided")
            )
        except Exception as e:
            logger.error(f"Error parsing LLM response: {str(e)}")
            return (0.5, 0.0, [], str(e))

    async def _calculate_rule_based_risk_factors(self, transaction: Dict) -> List[Dict]:
        """Calculate risk factors based on predefined rules"""
        risk_factors = []
        
        try:
            # Check amount thresholds
            amount = transaction.get("amount", {}).get("value", 0)
            if amount >= 1000000:
                risk_factors.append({
                    "type": "high_value",
                    "description": "Transaction amount exceeds $1,000,000",
                    "score": 0.4
                })
            elif amount >= 100000:
                risk_factors.append({
                    "type": "medium_value",
                    "description": "Transaction amount exceeds $100,000",
                    "score": 0.2
                })
            
            # Check high-risk jurisdictions
            high_risk_countries = {"BVI", "CAYMAN", "PANAMA", "UAE"}
            sender_address = transaction.get("sender", {}).get("address", "").upper()
            receiver_address = transaction.get("receiver", {}).get("address", "").upper()
            
            for country in high_risk_countries:
                if country in sender_address or country in receiver_address:
                    risk_factors.append({
                        "type": "high_risk_jurisdiction",
                        "description": f"Transaction involves {country}",
                        "score": 0.3
                    })
            
            # Check for suspicious patterns in notes
            suspicious_terms = {"urgent", "missing", "linked", "intermediary"}
            notes = transaction.get("additional_notes", "").lower()
            found_terms = [term for term in suspicious_terms if term in notes]
            
            if found_terms:
                risk_factors.append({
                    "type": "suspicious_terms",
                    "description": f"Suspicious terms found: {', '.join(found_terms)}",
                    "score": 0.2
                })
            
            return risk_factors
            
        except Exception as e:
            logger.error(f"Error calculating rule-based risk factors: {str(e)}")
            return []

    def _combine_risk_scores(self, llm_risk_score: float, rule_based_factors: List[Dict]) -> float:
        """Combine LLM and rule-based risk scores"""
        try:
            # Calculate rule-based score
            rule_based_score = sum(factor["score"] for factor in rule_based_factors)
            
            # Weight LLM score more heavily (70%) than rule-based score (30%)
            combined_score = (llm_risk_score * 0.7) + (min(rule_based_score, 1.0) * 0.3)
            
            # Cap final score at 1.0
            return min(combined_score, 1.0)
            
        except Exception as e:
            logger.error(f"Error combining risk scores: {str(e)}")
            return llm_risk_score

    async def store_extracted_transaction(self, db: AsyncIOMotorDatabase, transaction_data: Dict) -> str:
        """Store extracted transaction data with entities"""
        try:
            transaction_id = str(uuid4())
            
            # Calculate risk assessment
            risk_assessment = await self._calculate_risk_score(transaction_data)
            
            transaction = {
                "id": transaction_id,
                "transaction_id": transaction_data.get("transaction_id"),
                "raw_data": transaction_data.get("raw_content", ""),
                "sender": transaction_data.get("sender", {}),
                "receiver": transaction_data.get("receiver", {}),
                "amount": transaction_data.get("amount", {}),
                "date": transaction_data.get("date"),
                "additional_notes": transaction_data.get("additional_notes", ""),
                "extracted_entities": transaction_data.get("extracted_entities", {}),
                "risk_score": risk_assessment["risk_score"],
                "risk_factors": risk_assessment["risk_factors"],
                "supporting_evidence": risk_assessment["supporting_evidence"],
                "confidence_score": risk_assessment["confidence_score"],
                "reason": risk_assessment["reason"],
                "status": "EXTRACTED",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            # Insert transaction
            await db[self.collection_name].insert_one(transaction)
            
            # Create relationships between entities
            if "extracted_entities" in transaction_data:
                await self._create_entity_relationships(
                    db,
                    transaction_id,
                    transaction_data["extracted_entities"]
                )
            
            return transaction_id
            
        except Exception as e:
            logger.error(f"Error storing extracted transaction: {str(e)}")
            raise

    async def get_transaction(self, db: AsyncIOMotorDatabase, transaction_id: str) -> Optional[Transaction]:
        """Get transaction by ID"""
        try:
            transaction = await db[self.collection_name].find_one({"id": transaction_id})
            return Transaction(**transaction) if transaction else None
            
        except Exception as e:
            logger.error(f"Error getting transaction {transaction_id}: {str(e)}")
            raise

    async def list_transactions(
        self,
        db: AsyncIOMotorDatabase,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        risk_threshold: Optional[float] = None,
        file_id: Optional[str] = None
    ) -> List[Transaction]:
        """List transactions with optional filters"""
        try:
            # Build query
            query = {}
            if status:
                query["status"] = status
            if risk_threshold is not None:
                query["risk_score"] = {"$gte": risk_threshold}
            if file_id:
                query["file_id"] = file_id
            
            # Execute query with pagination
            cursor = db[self.collection_name].find(query).sort(
                [("risk_score", -1), ("created_at", -1)]
            ).skip(skip).limit(limit)
            
            transactions = await cursor.to_list(length=limit)
            return [Transaction(**t) for t in transactions]
            
        except Exception as e:
            logger.error(f"Error listing transactions: {str(e)}")
            raise

    async def update_transaction(
        self,
        db: AsyncIOMotorDatabase,
        transaction_id: str,
        update_data: TransactionUpdate
    ) -> Optional[Transaction]:
        """Update transaction"""
        try:
            # Prepare update data
            update_dict = update_data.dict(exclude_unset=True)
            update_dict["updated_at"] = datetime.utcnow()
            
            # Update in database
            result = await db[self.collection_name].update_one(
                {"id": transaction_id},
                {"$set": update_dict}
            )
            
            if result.modified_count:
                return await self.get_transaction(db, transaction_id)
            return None
            
        except Exception as e:
            logger.error(f"Error updating transaction {transaction_id}: {str(e)}")
            raise

    async def delete_transaction(self, db: AsyncIOMotorDatabase, transaction_id: str) -> bool:
        """Delete transaction"""
        try:
            # Delete transaction-entity relationships first
            await db["transaction_entities"].delete_many(
                {"transaction_id": transaction_id}
            )
            
            # Delete transaction
            result = await db[self.collection_name].delete_one(
                {"id": transaction_id}
            )
            
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"Error deleting transaction {transaction_id}: {str(e)}")
            raise

    async def _create_entity_relationships(
        self,
        db: AsyncIOMotorDatabase,
        transaction_id: str,
        extracted_entities: Dict
    ) -> None:
        """Create relationships between entities in Neo4j"""
        try:
            for category, entities in extracted_entities.items():
                for entity in entities:
                    # Create relationship between sender and receiver
                    if category == "organizations":
                        await self.graph_store.create_relationship(
                            from_id=entity["id"],
                            to_id=transaction_id,
                            relationship_type="INVOLVED_IN",
                            properties={
                                "role": "organization",
                                "timestamp": datetime.utcnow().isoformat()
                            }
                        )
                    elif category == "persons":
                        await self.graph_store.create_relationship(
                            from_id=entity["id"],
                            to_id=transaction_id,
                            relationship_type="PARTICIPATED_IN",
                            properties={
                                "role": "person",
                                "timestamp": datetime.utcnow().isoformat()
                            }
                        )
            
        except Exception as e:
            logger.error(f"Error creating entity relationships: {str(e)}")
            raise

    async def get_transaction_statistics(self, db: AsyncIOMotorDatabase) -> Dict:
        """Get transaction statistics"""
        try:
            pipeline = [
                {
                    "$group": {
                        "_id": None,
                        "total_count": {"$sum": 1},
                        "high_risk_count": {
                            "$sum": {"$cond": [{"$gte": ["$risk_score", 0.7]}, 1, 0]}
                        },
                        "medium_risk_count": {
                            "$sum": {
                                "$cond": [
                                    {
                                        "$and": [
                                            {"$gte": ["$risk_score", 0.4]},
                                            {"$lt": ["$risk_score", 0.7]}
                                        ]
                                    },
                                    1,
                                    0
                                ]
                            }
                        },
                        "low_risk_count": {
                            "$sum": {"$cond": [{"$lt": ["$risk_score", 0.4]}, 1, 0]}
                        },
                        "average_risk_score": {"$avg": "$risk_score"},
                        "total_amount": {
                            "$sum": {"$toDouble": "$amount.value"}
                        }
                    }
                }
            ]
            
            result = await db[self.collection_name].aggregate(pipeline).to_list(length=1)
            
            if not result:
                return {
                    "total_count": 0,
                    "high_risk_count": 0,
                    "medium_risk_count": 0,
                    "low_risk_count": 0,
                    "average_risk_score": 0,
                    "total_amount": 0
                }
            
            stats = result[0]
            stats.pop("_id")
            return stats
            
        except Exception as e:
            logger.error(f"Error getting transaction statistics: {str(e)}")
            raise