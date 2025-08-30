#!/usr/bin/env python
"""
Test script to verify registration and authentication functionality
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'registration_project.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.test import Client

def test_user_creation():
    """Test user creation functionality"""
    print("Testing user creation...")
    
    # Test 1: Create a user
    try:
        user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        print(f"✅ User created successfully: {user.username}")
        
        # Test 2: Authenticate the user
        auth_user = authenticate(username='testuser', password='testpass123')
        if auth_user:
            print(f"✅ User authenticated successfully: {auth_user.username}")
        else:
            print("❌ User authentication failed")
            
        # Test 3: Check if user exists
        if User.objects.filter(username='testuser').exists():
            print("✅ User exists in database")
        else:
            print("❌ User not found in database")
            
        # Clean up
        user.delete()
        print("✅ Test user cleaned up")
        
    except Exception as e:
        print(f"❌ Error during user creation test: {e}")
        return False
    
    return True

def test_mongodb_connection():
    """Test MongoDB connection"""
    print("\nTesting MongoDB connection...")
    
    try:
        from converter.mongo_config import check_mongodb_health
        if check_mongodb_health():
            print("✅ MongoDB connection successful")
            return True
        else:
            print("❌ MongoDB connection failed")
            return False
    except Exception as e:
        print(f"❌ Error testing MongoDB connection: {e}")
        return False

def test_registration_view():
    """Test registration view"""
    print("\nTesting registration view...")
    
    try:
        client = Client()
        
        # Test registration form
        response = client.get('/register/')
        if response.status_code == 200:
            print("✅ Registration page loads successfully")
        else:
            print(f"❌ Registration page failed to load: {response.status_code}")
            return False
            
        # Test user registration
        response = client.post('/register/', {
            'username': 'testuser2',
            'password1': 'testpass123',
            'password2': 'testpass123'
        })
        
        if response.status_code == 302:  # Redirect after successful registration
            print("✅ User registration successful")
            
            # Check if user was created
            if User.objects.filter(username='testuser2').exists():
                print("✅ User created in database")
                
                # Clean up
                User.objects.filter(username='testuser2').delete()
                print("✅ Test user cleaned up")
                return True
            else:
                print("❌ User not found in database after registration")
                return False
        else:
            print(f"❌ User registration failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing registration view: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Running system tests...\n")
    
    tests = [
        ("User Creation", test_user_creation),
        ("MongoDB Connection", test_mongodb_connection),
        ("Registration View", test_registration_view),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"Running {test_name} test...")
        result = test_func()
        results.append((test_name, result))
        print()
    
    # Summary
    print("📊 Test Results Summary:")
    print("=" * 40)
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print("=" * 40)
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! System is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
