import json
import logging
from typing import Dict, List, Callable, Any
from datetime import datetime
import re
from confluent_kafka import Producer, Consumer, KafkaError, KafkaException
from app.core.config import settings

logger = logging.getLogger(__name__)

class KafkaService:
    def __init__(self):
        self.producer_config = {
            'bootstrap.servers': 'localhost:9092',
            'client.id': 'risk-analysis-producer'
        }
        
        self.consumer_config = {
            'bootstrap.servers': 'localhost:9092',
            'group.id': 'risk-analysis-consumer',
            'auto.offset.reset': 'earliest',
            'enable.auto.commit': True,
            'auto.commit.interval.ms': 5000,
            'max.poll.interval.ms': 300000  # 5 minutes
        }
        
        self.producer = Producer(self.producer_config)
        
        # Define required topics
        self.required_topics = [
            'transactions.high_risk',
            'transactions.medium_risk',
            'transactions.low_risk'
        ]
        
        # Ensure topics exist
        self._ensure_topics_exist()

    def _ensure_topics_exist(self):
        """Ensure required Kafka topics exist"""
        try:
            consumer = Consumer(self.consumer_config)
            try:
                # Get list of existing topics
                metadata = consumer.list_topics(timeout=10)
                existing_topics = metadata.topics
                
                # Create missing topics using admin client
                missing_topics = [
                    topic for topic in self.required_topics 
                    if topic not in existing_topics
                ]
                
                if missing_topics:
                    from confluent_kafka.admin import AdminClient, NewTopic
                    
                    admin_client = AdminClient({
                        'bootstrap.servers': 'localhost:9092'
                    })
                    
                    new_topics = [
                        NewTopic(
                            topic,
                            num_partitions=3,
                            replication_factor=1
                        ) for topic in missing_topics
                    ]
                    
                    # Create topics
                    fs = admin_client.create_topics(new_topics)
                    
                    # Wait for each operation to finish
                    for topic, f in fs.items():
                        try:
                            f.result()  # The result itself is None
                            logger.info(f"Topic {topic} created")
                        except Exception as e:
                            logger.error(f"Failed to create topic {topic}: {str(e)}")
            finally:
                consumer.close()
                        
        except KafkaException as e:
            logger.error(f"Error ensuring Kafka topics exist: {str(e)}")
            raise

    def parse_transaction_blocks(self, content: str) -> List[Dict]:
        """Parse raw content into transaction blocks"""
        # Split content by Transaction ID pattern
        blocks = re.split(r'(?=Transaction ID: )', content)
        transactions = []
        
        for block in blocks:
            if not block.strip():
                continue
                
            try:
                transaction = self._parse_single_block(block)
                transactions.append(transaction)
            except Exception as e:
                logger.error(f"Error parsing transaction block: {str(e)}")
                continue
                
        return transactions

    def _parse_single_block(self, block: str) -> Dict:
        """Parse a single transaction block into structured data"""
        transaction = {}
        
        # Extract Transaction ID
        txn_id_match = re.search(r'Transaction ID: ([\w-]+)', block)
        if txn_id_match:
            transaction['transaction_id'] = txn_id_match.group(1)
            
        # Extract Date
        date_match = re.search(r'Date:?\s*(\d{4}-\d{2}-\d{2}(?:\s+\d{2}:\d{2}:\d{2})?)', block)
        if date_match:
            transaction['date'] = date_match.group(1)
            
        # Extract Sender information
        sender_info = re.search(r'Sender:.*?(?=Receiver:|$)', block, re.DOTALL)
        if sender_info:
            sender_text = sender_info.group(0)
            transaction['sender'] = self._parse_party_info(sender_text)
            
        # Extract Receiver information
        receiver_info = re.search(r'Receiver:.*?(?=Amount:|$)', block, re.DOTALL)
        if receiver_info:
            receiver_text = receiver_info.group(0)
            transaction['receiver'] = self._parse_party_info(receiver_text)
            
        # Extract Amount
        amount_match = re.search(r'Amount:\s*\$?([\d,]+\.?\d*)\s*\((\w+)\)', block)
        if amount_match:
            transaction['amount'] = {
                'value': float(amount_match.group(1).replace(',', '')),
                'currency': amount_match.group(2)
            }
            
        # Extract Additional Notes
        notes_match = re.search(r'Additional Notes:(.*?)(?=\n\w+:|$)', block, re.DOTALL)
        if notes_match:
            transaction['additional_notes'] = notes_match.group(1).strip()
            
        # Add metadata
        transaction['parsed_at'] = datetime.utcnow().isoformat()
        transaction['raw_content'] = block.strip()
        
        return transaction

    def _parse_party_info(self, text: str) -> Dict:
        """Parse party (sender/receiver) information"""
        party_info = {}
        
        # Extract Name
        name_match = re.search(r'Name:?\s*["\']?(.*?)["\']?(?=\n|$)', text)
        if name_match:
            party_info['name'] = name_match.group(1).strip()
            
        # Extract Account
        account_match = re.search(r'Account:?\s*([\w\s-]+)', text)
        if account_match:
            party_info['account'] = account_match.group(1).strip()
            
        # Extract Address
        address_match = re.search(r'Address:?(.*?)(?=\n\w+:|$)', text, re.DOTALL)
        if address_match:
            party_info['address'] = address_match.group(1).strip()
            
        return party_info

    async def publish_transaction(self, transaction: Dict):
        """Publish transaction to Kafka topic"""
        try:
            # Determine risk level and topic
            risk_level = self._assess_initial_risk(transaction)
            topic = f"transactions.{risk_level}"
            
            # Serialize transaction data
            message = json.dumps(transaction)
            
            # Publish to Kafka
            self.producer.produce(
                topic,
                key=transaction['transaction_id'],
                value=message,
                callback=self._delivery_callback
            )
            
            # Ensure message is sent
            self.producer.flush()
            
            logger.info(f"Published transaction {transaction['transaction_id']} to topic {topic}")
            
        except Exception as e:
            logger.error(f"Error publishing transaction: {str(e)}")
            raise

    def _assess_initial_risk(self, transaction: Dict) -> str:
        """
        Perform initial risk assessment to determine Kafka topic.
        Returns: 'high_risk', 'medium_risk', or 'low_risk'
        """
        risk_indicators = 0
        
        # Check for high-risk jurisdictions
        high_risk_countries = {'BVI', 'CAYMAN', 'PANAMA', 'UAE'}
        sender_address = transaction.get('sender', {}).get('address', '').upper()
        receiver_address = transaction.get('receiver', {}).get('address', '').upper()
        
        for country in high_risk_countries:
            if country in sender_address or country in receiver_address:
                risk_indicators += 2
                
        # Check transaction amount
        amount = transaction.get('amount', {}).get('value', 0)
        if amount >= 1000000:
            risk_indicators += 2
        elif amount >= 100000:
            risk_indicators += 1
            
        # Check for suspicious keywords in notes
        suspicious_terms = {'urgent', 'missing', 'linked', 'intermediary'}
        notes = transaction.get('additional_notes', '').lower()
        if any(term in notes for term in suspicious_terms):
            risk_indicators += 1
            
        # Determine risk level
        if risk_indicators >= 3:
            return 'high_risk'
        elif risk_indicators >= 1:
            return 'medium_risk'
        return 'low_risk'

    def _delivery_callback(self, err, msg):
        """Callback for Kafka message delivery"""
        if err:
            logger.error(f'Message delivery failed: {str(err)}')
        else:
            logger.info(f'Message delivered to {msg.topic()} [{msg.partition()}]')

    async def consume_transactions(self, topics: List[str], callback: Callable, max_messages: int = 100) -> List[Dict]:
        """
        Consume a batch of transactions from specified topics
        Returns: List of processed transactions
        """
        processed_transactions = []
        consumer = None
        
        try:
            consumer = Consumer(self.consumer_config)
            consumer.subscribe(topics)
            
            message_count = 0
            while message_count < max_messages:
                msg = consumer.poll(1.0)  # 1 second timeout
                
                if msg is None:
                    # No more messages available
                    break
                    
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        # End of partition event
                        continue
                    else:
                        logger.error(f'Error while consuming: {msg.error()}')
                        break
                else:
                    try:
                        transaction = json.loads(msg.value())
                        processed_transaction = await callback(transaction)
                        if processed_transaction:
                            processed_transactions.append(processed_transaction)
                            message_count += 1
                    except Exception as e:
                        logger.error(f'Error processing message: {str(e)}')
                        continue
            
            return processed_transactions
            
        except Exception as e:
            logger.error(f'Error in consumer: {str(e)}')
            raise
        finally:
            if consumer:
                consumer.close()