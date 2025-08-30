"""
MongoDB configuration for Django project using mongoengine
"""
import os
from mongoengine import connect, disconnect
from django.conf import settings


def connect_to_mongodb():
    """Connect to MongoDB using the URI from settings"""
    try:
        # Disconnect any existing connections (avoid duplicate connections)
        disconnect(alias='default')

        connect(
            db='registration_project',   # 👈 You can change this DB name if needed
            host=settings.MONGODB_URI,
            alias='default'
        )
        print("✅ Successfully connected to MongoDB")
    except Exception as e:
        print(f"❌ Error connecting to MongoDB: {e}")


def disconnect_from_mongodb():
    """Disconnect from MongoDB"""
    try:
        disconnect(alias='default')
        print("🔌 Disconnected from MongoDB")
    except Exception as e:
        print(f"❌ Error disconnecting from MongoDB: {e}")
