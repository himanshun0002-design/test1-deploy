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

        # Parse the MongoDB URI to extract components
        uri = settings.MONGODB_URI
        
        # Optimized connection with faster timeouts and SSL handling
        connect(
            db='registration_project',
            host=uri,
            alias='default',
            serverSelectionTimeoutMS=10000,  # Reduced from 30s to 10s
            connectTimeoutMS=10000,          # Reduced from 30s to 10s
            socketTimeoutMS=10000,           # Reduced from 30s to 10s
            maxPoolSize=5,                   # Reduced pool size
            minPoolSize=1,
            maxIdleTimeMS=30000,             # Close idle connections faster
            retryWrites=True,
            w='majority',
            ssl=True,
            ssl_cert_reqs='CERT_NONE',      # Don't require SSL certificate verification
            tlsAllowInvalidCertificates=True,  # Allow invalid certificates
            tlsAllowInvalidHostnames=True,     # Allow invalid hostnames
        )
        print("✅ Successfully connected to MongoDB")
                
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        # Don't raise the exception to prevent deployment failure


def disconnect_from_mongodb():
    """Disconnect from MongoDB"""
    try:
        disconnect(alias='default')
        print("🔌 Disconnected from MongoDB")
    except Exception as e:
        print(f"❌ Error disconnecting from MongoDB: {e}")
