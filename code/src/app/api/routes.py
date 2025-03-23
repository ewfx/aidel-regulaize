from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.models.transaction import TransactionRequest, TransactionResponse
from app.services.transaction_processor import TransactionProcessor
from app.core.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.post("/transactions/process", 
             response_model=TransactionResponse,
             summary="Process transaction and assess risk",
             response_description="Detailed risk analysis for the transaction")
async def process_transaction(
    transaction: TransactionRequest,
    background_tasks: BackgroundTasks
):
    try:
        processor = TransactionProcessor()
        result = await processor.process(transaction)
        
        # Add audit logging to background tasks
        background_tasks.add_task(
            processor.log_transaction,
            transaction.transactionID,
            result
        )
        
        return result
    except Exception as e:
        logger.error(f"Error processing transaction: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to process transaction"
        )