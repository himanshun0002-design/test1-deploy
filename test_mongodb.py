#!/usr/bin/env python3
"""
Test script to verify MongoDB connection
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'registration_project.settings')
django.setup()

# Test MongoDB connection
try:
    from registration_project.mongodb import connect_to_mongodb
    connect_to_mongodb()
    print("✅ MongoDB connection test successful!")
except Exception as e:
    print(f"❌ MongoDB connection test failed: {e}")
    sys.exit(1)
