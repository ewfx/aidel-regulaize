import pytest
from httpx import AsyncClient
import json
from datetime import datetime
from app.models.transaction import Transaction, TransactionCreate
from app.services.transaction_service import TransactionService

@pytest.mark.asyncio
async def test_create_transaction(test_app, mongodb_client):
    # Test data
    transaction_data = {
        "raw_data": "Test transaction",
        "sender": {"name": "John Doe", "address": "123 Main St"},
        "receiver": {"name": "Jane Smith", "address": "456 Oak Ave"},
        "amount": {"value": 100000, "currency": "USD"},
        "date": "2024-02-28",
        "additional_notes": "Test transaction notes"
    }

    # Create transaction
    response = test_app.post("/api/transactions", json=transaction_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "transaction_id" in data
    assert "risk_score" in data
    assert "confidence_score" in data
    assert "supporting_evidence" in data
    assert "reason" in data

@pytest.mark.asyncio
async def test_get_transaction(test_app, mongodb_client):
    # Create test transaction
    service = TransactionService()
    transaction = await service.create_transaction(
        test_app.app.mongodb,
        TransactionCreate(
            raw_data="Test transaction",
            sender={"name": "John Doe"},
            receiver={"name": "Jane Smith"},
            amount={"value": 50000, "currency": "USD"}
        )
    )

    # Get transaction
    response = test_app.get(f"/api/transactions/{transaction.id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["transaction_id"] == transaction.id
    assert "risk_score" in data
    assert "confidence_score" in data

@pytest.mark.asyncio
async def test_list_transactions(test_app, mongodb_client):
    # Create multiple test transactions
    service = TransactionService()
    transactions = []
    for i in range(3):
        transaction = await service.create_transaction(
            test_app.app.mongodb,
            TransactionCreate(
                raw_data=f"Test transaction {i}",
                sender={"name": f"Sender {i}"},
                receiver={"name": f"Receiver {i}"},
                amount={"value": 10000 * (i + 1), "currency": "USD"}
            )
        )
        transactions.append(transaction)

    # List transactions
    response = test_app.get("/api/transactions")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) == 3
    assert all("transaction_id" in tx for tx in data)
    assert all("risk_score" in tx for tx in data)

@pytest.mark.asyncio
async def test_high_risk_transaction(test_app, mongodb_client):
    # Test data with high-risk indicators
    transaction_data = {
        "raw_data": "High risk transaction",
        "sender": {"name": "Shell Corp", "address": "Cayman Islands"},
        "receiver": {"name": "Offshore Ltd", "address": "BVI"},
        "amount": {"value": 2000000, "currency": "USD"},
        "date": "2024-02-28",
        "additional_notes": "Urgent transfer through intermediary"
    }

    # Create transaction
    response = test_app.post("/api/transactions", json=transaction_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["risk_score"] > 0.7  # High risk threshold
    assert data["confidence_score"] > 0.8
    assert len(data["supporting_evidence"]) > 0
    assert "high-risk" in data["reason"].lower()

@pytest.mark.asyncio
async def test_transaction_update(test_app, mongodb_client):
    # Create initial transaction
    service = TransactionService()
    transaction = await service.create_transaction(
        test_app.app.mongodb,
        TransactionCreate(
            raw_data="Initial transaction",
            sender={"name": "Initial Sender"},
            receiver={"name": "Initial Receiver"},
            amount={"value": 50000, "currency": "USD"}
        )
    )

    # Update data
    update_data = {
        "amount": {"value": 75000, "currency": "USD"},
        "additional_notes": "Updated transaction notes"
    }

    # Update transaction
    response = test_app.put(
        f"/api/transactions/{transaction.id}",
        json=update_data
    )
    assert response.status_code == 200
    
    data = response.json()
    assert data["transaction_id"] == transaction.id
    assert "risk_score" in data
    assert "confidence_score" in data

@pytest.mark.asyncio
async def test_transaction_deletion(test_app, mongodb_client):
    # Create test transaction
    service = TransactionService()
    transaction = await service.create_transaction(
        test_app.app.mongodb,
        TransactionCreate(
            raw_data="Test transaction",
            sender={"name": "John Doe"},
            receiver={"name": "Jane Smith"},
            amount={"value": 50000, "currency": "USD"}
        )
    )

    # Delete transaction
    response = test_app.delete(f"/api/transactions/{transaction.id}")
    assert response.status_code == 200

    # Verify deletion
    response = test_app.get(f"/api/transactions/{transaction.id}")
    assert response.status_code == 404