import os
import uuid
from django.conf import settings
from django.core.files.storage import Storage
from django.core.files.base import ContentFile
from pymongo import MongoClient
from gridfs import GridFS
import logging

logger = logging.getLogger(__name__)

class MongoDBStorage(Storage):
    """Custom storage backend for MongoDB GridFS"""
    
    def __init__(self):
        self.client = MongoClient(settings.MONGODB_URI)
        self.db = self.client[settings.MONGODB_DB_NAME]
        self.fs = GridFS(self.db)
    
    def _open(self, name, mode='rb'):
        """Open a file from GridFS"""
        try:
            file_id = self._get_file_id(name)
            if file_id:
                grid_out = self.fs.get(file_id)
                return ContentFile(grid_out.read())
            return None
        except Exception as e:
            logger.error(f"Error opening file {name}: {e}")
            return None
    
    def _save(self, name, content):
        """Save a file to GridFS"""
        try:
            # Generate unique filename if name is not provided
            if not name:
                ext = os.path.splitext(content.name)[1] if hasattr(content, 'name') else ''
                name = f"uploads/{uuid.uuid4().hex}{ext}"
            
            # Read content
            content.seek(0)
            file_data = content.read()
            
            # Store in GridFS
            file_id = self.fs.put(
                file_data,
                filename=name,
                content_type=getattr(content, 'content_type', 'application/octet-stream')
            )
            
            # Store mapping in files collection
            self.db.files_mapping.insert_one({
                'filename': name,
                'file_id': file_id,
                'content_type': getattr(content, 'content_type', 'application/octet-stream'),
                'size': len(file_data)
            })
            
            logger.info(f"File {name} saved to GridFS with ID: {file_id}")
            return name
            
        except Exception as e:
            logger.error(f"Error saving file {name}: {e}")
            raise
    
    def delete(self, name):
        """Delete a file from GridFS"""
        try:
            file_id = self._get_file_id(name)
            if file_id:
                self.fs.delete(file_id)
                # Remove mapping
                self.db.files_mapping.delete_one({'filename': name})
                logger.info(f"File {name} deleted from GridFS")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting file {name}: {e}")
            return False
    
    def exists(self, name):
        """Check if file exists in GridFS"""
        try:
            return self.db.files_mapping.find_one({'filename': name}) is not None
        except Exception as e:
            logger.error(f"Error checking file existence {name}: {e}")
            return False
    
    def url(self, name):
        """Get URL for file (for GridFS, we'll use a custom endpoint)"""
        return f"/media/gridfs/{name}"
    
    def size(self, name):
        """Get file size"""
        try:
            mapping = self.db.files_mapping.find_one({'filename': name})
            return mapping.get('size', 0) if mapping else 0
        except Exception as e:
            logger.error(f"Error getting file size {name}: {e}")
            return 0
    
    def _get_file_id(self, name):
        """Get GridFS file ID from filename"""
        try:
            mapping = self.db.files_mapping.find_one({'filename': name})
            return mapping.get('file_id') if mapping else None
        except Exception as e:
            logger.error(f"Error getting file ID for {name}: {e}")
            return None
    
    def get_file_content(self, name):
        """Get file content as bytes"""
        try:
            file_id = self._get_file_id(name)
            if file_id:
                grid_out = self.fs.get(file_id)
                return grid_out.read()
            return None
        except Exception as e:
            logger.error(f"Error getting file content for {name}: {e}")
            return None

# Global instance
mongodb_storage = MongoDBStorage()
