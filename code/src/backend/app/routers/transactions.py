from fastapi import APIRouter, HTTPException, Request
from typing import List, Optional
from app.models.transaction import Transaction, TransactionCreate, TransactionUpdate, TransactionResponse
from app.services.transaction_service import TransactionService
from app.services.kafka_service import KafkaService
from app.core.config import settings

router = APIRouter()
transaction_service = TransactionService()
kafka_service = KafkaService()

@router.get("/statistics", response_model=dict)
async def get_transaction_statistics(request: Request):
    """Get transaction statistics"""
    try:
        if not hasattr(request, 'app') or not hasattr(request.app, 'mongodb'):
            raise HTTPException(status_code=500, detail="Database connection not available")
        return await transaction_service.get_transaction_statistics(request.app.mongodb)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("", response_model=List[TransactionResponse])
async def list_transactions(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    risk_threshold: Optional[float] = None,
    file_id: Optional[str] = None
):
    """List transactions with optional filters"""
    try:
        if not hasattr(request, 'app') or not hasattr(request.app, 'mongodb'):
            raise HTTPException(status_code=500, detail="Database connection not available")
        transactions = await transaction_service.list_transactions(
            request.app.mongodb,
            skip=skip,
            limit=limit,
            status=status,
            risk_threshold=risk_threshold,
            file_id=file_id
        )
        return transactions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(transaction_id: str, request: Request):
    """Get transaction by ID"""
    try:
        if not hasattr(request, 'app') or not hasattr(request.app, 'mongodb'):
            raise HTTPException(status_code=500, detail="Database connection not available")
        transaction = await transaction_service.get_transaction(request.app.mongodb, transaction_id)
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        return transaction
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("", response_model=TransactionResponse)
async def create_transaction(transaction_data: TransactionCreate, request: Request):
    """Create a new transaction"""
    try:
        if not hasattr(request, 'app') or not hasattr(request.app, 'mongodb'):
            raise HTTPException(status_code=500, detail="Database connection not available")
        transaction = await transaction_service.create_transaction(request.app.mongodb, transaction_data)
        return transaction
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(transaction_id: str, update_data: TransactionUpdate, request: Request):
    """Update transaction"""
    try:
        if not hasattr(request, 'app') or not hasattr(request.app, 'mongodb'):
            raise HTTPException(status_code=500, detail="Database connection not available")
        transaction = await transaction_service.update_transaction(
            request.app.mongodb,
            transaction_id,
            update_data
        )
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        return transaction
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{transaction_id}")
async def delete_transaction(transaction_id: str, request: Request):
    """Delete transaction"""
    try:
        if not hasattr(request, 'app') or not hasattr(request.app, 'mongodb'):
            raise HTTPException(status_code=500, detail="Database connection not available")
        success = await transaction_service.delete_transaction(request.app.mongodb, transaction_id)
        if not success:
            raise HTTPException(status_code=404, detail="Transaction not found")
        return {"message": "Transaction deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/process-blocks", response_model=List[dict])
async def process_transaction_blocks(content: str):
    """Process transaction blocks and publish to Kafka topics"""
    try:
        transactions = kafka_service.parse_transaction_blocks(content)
        for transaction in transactions:
            await kafka_service.publish_transaction(transaction)
        return transactions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))