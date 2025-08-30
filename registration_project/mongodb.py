"""
MongoDB configuration for Django project using mongoengine
"""
import os
from mongoengine import connect, disconnect
from django.conf import settings

def connect_to_mongodb():
    """Connect to MongoDB using the URI from settings"""
    try:
        # Disconnect any existing connections
        disconnect()
        
        # Connect to MongoDB
        connect(
            db='registration_project',
            host=settings.MONGODB_URI,
            alias='default'
        )
        print("Successfully connected to MongoDB")
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")

def disconnect_from_mongodb():
    """Disconnect from MongoDB"""
    try:
        disconnect()
        print("Disconnected from MongoDB")
    except Exception as e:
        print(f"Error disconnecting from MongoDB: {e}")
