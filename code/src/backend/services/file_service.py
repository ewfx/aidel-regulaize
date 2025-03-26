from app.models.file import FileMetadata
from typing import List, Optional, Dict
import logging
from datetime import datetime
import json
import pandas as pd
import aiofiles
import os
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

class FileService:
    def __init__(self):
        self.collection_name = "files"
        self.upload_dir = Path("uploads")
        self.upload_dir.mkdir(exist_ok=True)

    async def process_file(self, content: bytes, metadata: FileMetadata, db: AsyncIOMotorDatabase) -> None:
        """
        Process and store uploaded file content.
        """
        try:
            # Import PipelineService here to avoid circular import
            from app.services.pipeline_service import PipelineService
            pipeline_service = PipelineService()

            # Save file content
            file_path = self.upload_dir / f"{metadata.id}.{metadata.format.lower()}"
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(content)

            # Store metadata in MongoDB
            await self.create_file_metadata(metadata, db)

            # Process file based on format
            try:
                processed_data = None
                if metadata.format == "JSON":
                    data = json.loads(content)
                    processed_data = await self._process_json_data(data, metadata.id, db)
                elif metadata.format == "CSV":
                    data = pd.read_csv(file_path).to_dict('records')
                    processed_data = await self._process_csv_data(data, metadata.id, db)
                elif metadata.format == "EXCEL":
                    data = pd.read_excel(file_path).to_dict('records')
                    processed_data = await self._process_excel_data(data, metadata.id, db)
                elif metadata.format == "TXT":
                    text_content = content.decode('utf-8')
                    processed_data = await self._process_text_data(text_content, metadata.id, db)

                if processed_data:
                    # Start pipeline processing
                    await pipeline_service.process_file(metadata.id, db)
                    
                    # Update status to processing
                    metadata_dict = metadata.dict()
                    metadata_dict["status"] = "PROCESSING"
                    await self.update_metadata(metadata_dict, db)
                else:
                    # If no data was processed, mark as failed
                    metadata_dict = metadata.dict()
                    metadata_dict["status"] = "FAILED"
                    await self.update_metadata(metadata_dict, db)
                
            except Exception as e:
                logger.error(f"Error processing file {metadata.id}: {str(e)}")
                metadata_dict = metadata.dict()
                metadata_dict["status"] = "FAILED"
                await self.update_metadata(metadata_dict, db)
                raise

        except Exception as e:
            logger.error(f"Error handling file {metadata.id}: {str(e)}")
            metadata_dict = metadata.dict()
            metadata_dict["status"] = "FAILED"
            await self.update_metadata(metadata_dict, db)
            raise

    async def create_file_metadata(self, metadata: FileMetadata, db: AsyncIOMotorDatabase) -> None:
        """Create new file metadata in MongoDB"""
        try:
            await db[self.collection_name].insert_one(metadata.dict())
            logger.info(f"Created metadata for file {metadata.id}")
        except Exception as e:
            logger.error(f"Error creating file metadata: {str(e)}")
            raise

    async def update_metadata(self, metadata: Dict, db: AsyncIOMotorDatabase) -> None:
        """Update file metadata in MongoDB"""
        try:
            metadata["updatedAt"] = datetime.utcnow()
            await db[self.collection_name].update_one(
                {"id": metadata["id"]},
                {"$set": metadata}
            )
            logger.info(f"Updated metadata for file {metadata['id']}")
        except Exception as e:
            logger.error(f"Error updating metadata for file {metadata['id']}: {str(e)}")
            raise

    async def list_files(self, db: AsyncIOMotorDatabase, skip: int = 0, limit: int = 100) -> List[FileMetadata]:
        """List all uploaded files with pagination"""
        try:
            cursor = db[self.collection_name].find().skip(skip).limit(limit)
            files = await cursor.to_list(length=limit)
            return [FileMetadata(**file) for file in files]
        except Exception as e:
            logger.error(f"Error listing files: {str(e)}")
            raise

    async def get_file(self, file_id: str, db: AsyncIOMotorDatabase) -> Optional[FileMetadata]:
        """Get file metadata by ID"""
        try:
            file = await db[self.collection_name].find_one({"id": file_id})
            return FileMetadata(**file) if file else None
        except Exception as e:
            logger.error(f"Error getting file {file_id}: {str(e)}")
            raise

    async def delete_file(self, file_id: str, db: AsyncIOMotorDatabase) -> bool:
        """Delete file and its metadata"""
        try:
            # Delete from MongoDB
            result = await db[self.collection_name].delete_one({"id": file_id})
            
            # Delete physical file if it exists
            file_path = self.upload_dir / f"{file_id}.*"
            for f in Path().glob(str(file_path)):
                f.unlink()
            
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting file {file_id}: {str(e)}")
            raise

    async def _process_json_data(self, data: dict, file_id: str, db: AsyncIOMotorDatabase) -> bool:
        """Process JSON data"""
        try:
            if isinstance(data, list):
                await db[self.collection_name].update_one(
                    {"id": file_id},
                    {"$set": {"processed_records": len(data)}}
                )
                return True
            elif isinstance(data, dict):
                await db[self.collection_name].update_one(
                    {"id": file_id},
                    {"$set": {"processed_records": 1}}
                )
                return True
            return False
        except Exception as e:
            logger.error(f"Error processing JSON data: {str(e)}")
            raise

    async def _process_csv_data(self, data: List[dict], file_id: str, db: AsyncIOMotorDatabase) -> bool:
        """Process CSV data"""
        try:
            await db[self.collection_name].update_one(
                {"id": file_id},
                {"$set": {"processed_records": len(data)}}
            )
            return True
        except Exception as e:
            logger.error(f"Error processing CSV data: {str(e)}")
            raise

    async def _process_excel_data(self, data: List[dict], file_id: str, db: AsyncIOMotorDatabase) -> bool:
        """Process Excel data"""
        try:
            await db[self.collection_name].update_one(
                {"id": file_id},
                {"$set": {"processed_records": len(data)}}
            )
            return True
        except Exception as e:
            logger.error(f"Error processing Excel data: {str(e)}")
            raise

    async def _process_text_data(self, content: str, file_id: str, db: AsyncIOMotorDatabase) -> bool:
        """Process text data"""
        try:
            # Split into lines and count non-empty lines
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            await db[self.collection_name].update_one(
                {"id": file_id},
                {"$set": {"processed_records": len(lines)}}
            )
            return True
        except Exception as e:
            logger.error(f"Error processing text data: {str(e)}")
            raise