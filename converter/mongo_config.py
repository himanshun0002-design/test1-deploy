import os
from django.conf import settings
from pymongo import MongoClient
import mongoengine
import logging

logger = logging.getLogger(__name__)

def connect_mongodb():
    """Initialize MongoDB connection for MongoEngine"""
    try:
        # Connect to MongoDB using MongoEngine
        mongoengine.connect(
            db=settings.MONGODB_DB_NAME,
            host=settings.MONGODB_URI,
            alias='default'
        )
        logger.info("MongoDB connection established successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        return False

def get_mongodb_client():
    """Get MongoDB client instance"""
    try:
        client = MongoClient(settings.MONGODB_URI)
        # Test connection
        client.admin.command('ping')
        logger.info("MongoDB client connection successful")
        return client
    except Exception as e:
        logger.error(f"Failed to create MongoDB client: {e}")
        return None

def init_mongodb_collections():
    """Initialize MongoDB collections and indexes"""
    try:
        client = get_mongodb_client()
        if not client:
            return False
        
        db = client[settings.MONGODB_DB_NAME]
        
        # Create collections if they don't exist
        collections = ['video_conversions', 'files_mapping']
        for collection_name in collections:
            if collection_name not in db.list_collection_names():
                db.create_collection(collection_name)
                logger.info(f"Created collection: {collection_name}")
        
        # Create indexes
        video_conversions = db.video_conversions
        video_conversions.create_index("user_id")
        video_conversions.create_index("status")
        video_conversions.create_index("created_at")
        video_conversions.create_index([("user_id", 1), ("created_at", -1)])
        
        files_mapping = db.files_mapping
        files_mapping.create_index("filename", unique=True)
        files_mapping.create_index("file_id")
        
        logger.info("MongoDB collections and indexes initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize MongoDB collections: {e}")
        return False

def check_mongodb_health():
    """Check MongoDB connection health"""
    try:
        client = get_mongodb_client()
        if not client:
            return False
        
        # Test basic operations
        db = client[settings.MONGODB_DB_NAME]
        result = db.command('ping')
        
        if result.get('ok') == 1:
            logger.info("MongoDB health check passed")
            return True
        else:
            logger.error("MongoDB health check failed")
            return False
            
    except Exception as e:
        logger.error(f"MongoDB health check error: {e}")
        return False
