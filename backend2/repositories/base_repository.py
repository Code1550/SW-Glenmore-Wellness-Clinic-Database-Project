# backend/repositories/base_repository.py
"""Base repository with common CRUD operations for all repositories"""

from typing import Optional, List, Dict, Any, Type, TypeVar, Generic
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase
from pymongo import ReturnDocument
from bson import ObjectId
import logging

from ..models.base import MongoBaseModel

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=MongoBaseModel)


class BaseRepository(Generic[T]):
    """Base repository class with common CRUD operations"""
    
    def __init__(self, database: AsyncIOMotorDatabase, collection_name: str, model_class: Type[T]):
        """
        Initialize base repository
        
        Args:
            database: MongoDB database instance
            collection_name: Name of the collection
            model_class: Pydantic model class for the collection
        """
        self.database = database
        self.collection: AsyncIOMotorCollection = database[collection_name]
        self.collection_name = collection_name
        self.model_class = model_class
        self.counters_collection = database["counters_primary_key_collection"]
    
    async def get_next_sequence(self, sequence_name: Optional[str] = None) -> int:
        """
        Get next auto-increment ID for the collection
        
        Args:
            sequence_name: Optional custom sequence name, defaults to collection name
        
        Returns:
            Next sequence number
        """
        seq_name = sequence_name or self.collection_name
        counter = await self.counters_collection.find_one_and_update(
            {"_id": seq_name},
            {"$inc": {"sequence_value": 1}},
            upsert=True,
            return_document=ReturnDocument.AFTER
        )
        return counter["sequence_value"]
    
    async def create(self, document: Dict[str, Any], auto_id_field: Optional[str] = None) -> T:
        """
        Create a new document
        
        Args:
            document: Document data to insert
            auto_id_field: Field name for auto-increment ID (e.g., 'patient_id')
        
        Returns:
            Created document as model instance
        """
        try:
            # Add auto-increment ID if specified
            if auto_id_field and auto_id_field not in document:
                next_id = await self.get_next_sequence()
                document[auto_id_field] = f"{self.collection_name.upper()[:3]}{str(next_id).zfill(3)}"
            
            # Add timestamps
            now = datetime.utcnow()
            document["created_at"] = document.get("created_at", now)
            document["updated_at"] = document.get("updated_at", now)
            
            # Insert document
            result = await self.collection.insert_one(document)
            document["_id"] = result.inserted_id
            
            return self.model_class(**document)
        except Exception as e:
            logger.error(f"Error creating document in {self.collection_name}: {str(e)}")
            raise
    
    async def find_by_id(self, document_id: str, id_field: str = "_id") -> Optional[T]:
        """
        Find document by ID
        
        Args:
            document_id: Document ID to search for
            id_field: Field name to search (default: _id, could be patient_id, etc.)
        
        Returns:
            Document as model instance or None
        """
        try:
            query = {}
            if id_field == "_id":
                query = {"_id": ObjectId(document_id) if ObjectId.is_valid(document_id) else document_id}
            else:
                query = {id_field: document_id}
            
            document = await self.collection.find_one(query)
            return self.model_class(**document) if document else None
        except Exception as e:
            logger.error(f"Error finding document by ID in {self.collection_name}: {str(e)}")
            return None
    
    async def find_one(self, filter_dict: Dict[str, Any]) -> Optional[T]:
        """
        Find single document by filter
        
        Args:
            filter_dict: MongoDB filter query
        
        Returns:
            Document as model instance or None
        """
        try:
            document = await self.collection.find_one(filter_dict)
            return self.model_class(**document) if document else None
        except Exception as e:
            logger.error(f"Error finding document in {self.collection_name}: {str(e)}")
            return None
    
    async def find_many(
        self,
        filter_dict: Dict[str, Any] = None,
        skip: int = 0,
        limit: int = 100,
        sort: Optional[List[tuple]] = None
    ) -> List[T]:
        """
        Find multiple documents
        
        Args:
            filter_dict: MongoDB filter query
            skip: Number of documents to skip
            limit: Maximum number of documents to return
            sort: List of (field, direction) tuples for sorting
        
        Returns:
            List of documents as model instances
        """
        try:
            filter_dict = filter_dict or {}
            cursor = self.collection.find(filter_dict)
            
            if sort:
                cursor = cursor.sort(sort)
            
            cursor = cursor.skip(skip).limit(limit)
            
            documents = await cursor.to_list(length=limit)
            return [self.model_class(**doc) for doc in documents]
        except Exception as e:
            logger.error(f"Error finding documents in {self.collection_name}: {str(e)}")
            return []
    
    async def update_by_id(
        self,
        document_id: str,
        update_dict: Dict[str, Any],
        id_field: str = "_id"
    ) -> Optional[T]:
        """
        Update document by ID
        
        Args:
            document_id: Document ID to update
            update_dict: Fields to update
            id_field: Field name to search (default: _id)
        
        Returns:
            Updated document as model instance or None
        """
        try:
            # Add updated timestamp
            update_dict["updated_at"] = datetime.utcnow()
            
            query = {}
            if id_field == "_id":
                query = {"_id": ObjectId(document_id) if ObjectId.is_valid(document_id) else document_id}
            else:
                query = {id_field: document_id}
            
            document = await self.collection.find_one_and_update(
                query,
                {"$set": update_dict},
                return_document=ReturnDocument.AFTER
            )
            
            return self.model_class(**document) if document else None
        except Exception as e:
            logger.error(f"Error updating document in {self.collection_name}: {str(e)}")
            return None
    
    async def update_one(self, filter_dict: Dict[str, Any], update_dict: Dict[str, Any]) -> Optional[T]:
        """
        Update single document by filter
        
        Args:
            filter_dict: MongoDB filter query
            update_dict: Fields to update
        
        Returns:
            Updated document as model instance or None
        """
        try:
            # Add updated timestamp
            update_dict["updated_at"] = datetime.utcnow()
            
            document = await self.collection.find_one_and_update(
                filter_dict,
                {"$set": update_dict},
                return_document=ReturnDocument.AFTER
            )
            
            return self.model_class(**document) if document else None
        except Exception as e:
            logger.error(f"Error updating document in {self.collection_name}: {str(e)}")
            return None
    
    async def update_many(self, filter_dict: Dict[str, Any], update_dict: Dict[str, Any]) -> int:
        """
        Update multiple documents
        
        Args:
            filter_dict: MongoDB filter query
            update_dict: Fields to update
        
        Returns:
            Number of documents updated
        """
        try:
            # Add updated timestamp
            update_dict["updated_at"] = datetime.utcnow()
            
            result = await self.collection.update_many(
                filter_dict,
                {"$set": update_dict}
            )
            
            return result.modified_count
        except Exception as e:
            logger.error(f"Error updating documents in {self.collection_name}: {str(e)}")
            return 0
    
    async def delete_by_id(self, document_id: str, id_field: str = "_id") -> bool:
        """
        Delete document by ID
        
        Args:
            document_id: Document ID to delete
            id_field: Field name to search (default: _id)
        
        Returns:
            True if deleted, False otherwise
        """
        try:
            query = {}
            if id_field == "_id":
                query = {"_id": ObjectId(document_id) if ObjectId.is_valid(document_id) else document_id}
            else:
                query = {id_field: document_id}
            
            result = await self.collection.delete_one(query)
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting document in {self.collection_name}: {str(e)}")
            return False
    
    async def delete_one(self, filter_dict: Dict[str, Any]) -> bool:
        """
        Delete single document by filter
        
        Args:
            filter_dict: MongoDB filter query
        
        Returns:
            True if deleted, False otherwise
        """
        try:
            result = await self.collection.delete_one(filter_dict)
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting document in {self.collection_name}: {str(e)}")
            return False
    
    async def delete_many(self, filter_dict: Dict[str, Any]) -> int:
        """
        Delete multiple documents
        
        Args:
            filter_dict: MongoDB filter query
        
        Returns:
            Number of documents deleted
        """
        try:
            result = await self.collection.delete_many(filter_dict)
            return result.deleted_count
        except Exception as e:
            logger.error(f"Error deleting documents in {self.collection_name}: {str(e)}")
            return 0
    
    async def count(self, filter_dict: Dict[str, Any] = None) -> int:
        """
        Count documents
        
        Args:
            filter_dict: MongoDB filter query
        
        Returns:
            Number of documents matching filter
        """
        try:
            filter_dict = filter_dict or {}
            return await self.collection.count_documents(filter_dict)
        except Exception as e:
            logger.error(f"Error counting documents in {self.collection_name}: {str(e)}")
            return 0
    
    async def exists(self, filter_dict: Dict[str, Any]) -> bool:
        """
        Check if document exists
        
        Args:
            filter_dict: MongoDB filter query
        
        Returns:
            True if exists, False otherwise
        """
        try:
            count = await self.collection.count_documents(filter_dict, limit=1)
            return count > 0
        except Exception as e:
            logger.error(f"Error checking existence in {self.collection_name}: {str(e)}")
            return False
    
    async def aggregate(self, pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Run aggregation pipeline
        
        Args:
            pipeline: MongoDB aggregation pipeline
        
        Returns:
            List of aggregation results
        """
        try:
            cursor = self.collection.aggregate(pipeline)
            return await cursor.to_list(length=None)
        except Exception as e:
            logger.error(f"Error running aggregation in {self.collection_name}: {str(e)}")
            return []
    
    async def bulk_create(self, documents: List[Dict[str, Any]]) -> List[T]:
        """
        Create multiple documents
        
        Args:
            documents: List of documents to insert
        
        Returns:
            List of created documents as model instances
        """
        try:
            now = datetime.utcnow()
            for doc in documents:
                doc["created_at"] = doc.get("created_at", now)
                doc["updated_at"] = doc.get("updated_at", now)
            
            result = await self.collection.insert_many(documents)
            
            # Fetch and return created documents
            created_docs = await self.collection.find(
                {"_id": {"$in": result.inserted_ids}}
            ).to_list(length=None)
            
            return [self.model_class(**doc) for doc in created_docs]
        except Exception as e:
            logger.error(f"Error bulk creating documents in {self.collection_name}: {str(e)}")
            return []
    
    async def find_with_text_search(self, search_text: str, limit: int = 100) -> List[T]:
        """
        Perform text search (requires text index on collection)
        
        Args:
            search_text: Text to search for
            limit: Maximum number of results
        
        Returns:
            List of matching documents
        """
        try:
            cursor = self.collection.find(
                {"$text": {"$search": search_text}},
                {"score": {"$meta": "textScore"}}
            ).sort([("score", {"$meta": "textScore"})]).limit(limit)
            
            documents = await cursor.to_list(length=limit)
            return [self.model_class(**doc) for doc in documents]
        except Exception as e:
            logger.error(f"Error performing text search in {self.collection_name}: {str(e)}")
            return []
# End of backend/repositories/base_repository.py