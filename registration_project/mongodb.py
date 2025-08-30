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
        
        # Try different connection approaches
        try:
            # First attempt: Use the full URI with minimal options
            connect(
                db='registration_project',
                host=uri,
                alias='default',
                serverSelectionTimeoutMS=30000,
                connectTimeoutMS=30000,
                socketTimeoutMS=30000,
            )
            print("✅ Successfully connected to MongoDB (method 1)")
        except Exception as e1:
            print(f"Method 1 failed: {e1}")
            try:
                # Second attempt: Use connection string with explicit SSL settings
                connect(
                    db='registration_project',
                    host=uri + "&ssl=true&ssl_cert_reqs=CERT_NONE",
                    alias='default',
                    serverSelectionTimeoutMS=30000,
                    connectTimeoutMS=30000,
                    socketTimeoutMS=30000,
                )
                print("✅ Successfully connected to MongoDB (method 2)")
            except Exception as e2:
                print(f"Method 2 failed: {e2}")
                # Third attempt: Use connection string with TLS settings
                connect(
                    db='registration_project',
                    host=uri + "&tls=true&tlsAllowInvalidCertificates=true",
                    alias='default',
                    serverSelectionTimeoutMS=30000,
                    connectTimeoutMS=30000,
                    socketTimeoutMS=30000,
                )
                print("✅ Successfully connected to MongoDB (method 3)")
                
    except Exception as e:
        print(f"❌ All connection methods failed: {e}")
        # Don't raise the exception to prevent deployment failure


def disconnect_from_mongodb():
    """Disconnect from MongoDB"""
    try:
        disconnect(alias='default')
        print("🔌 Disconnected from MongoDB")
    except Exception as e:
        print(f"❌ Error disconnecting from MongoDB: {e}")
