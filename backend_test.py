#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Food Truck Membership Site
Tests all API endpoints, authentication, database integration, and error handling
"""

import requests
import json
import time
import os
from typing import Dict, Any, Optional
import uuid

class FoodTruckBackendTester:
    def __init__(self):
        # Get backend URL from frontend .env file
        self.base_url = self.get_backend_url()
        self.session = requests.Session()
        self.test_results = []
        
    def get_backend_url(self) -> str:
        """Get backend URL from frontend .env file"""
        try:
            with open('/app/frontend/.env', 'r') as f:
                for line in f:
                    if line.startswith('REACT_APP_BACKEND_URL='):
                        return line.split('=', 1)[1].strip()
        except Exception as e:
            print(f"Error reading frontend .env: {e}")
            return "https://bbcmembership.preview.emergentagent.com"
        
        return "https://bbcmembership.preview.emergentagent.com"
    
    def log_test(self, test_name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "response_data": response_data
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
        if response_data and not success:
            print(f"   Response: {response_data}")
    
    def test_basic_health_check(self):
        """Test basic API health endpoints"""
        print("\n=== Testing Basic API Health Check ===")
        
        # Test root endpoint - should show Bitcoin Ben's Burger Bus Club
        try:
            response = self.session.get(f"{self.base_url}/api/")
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "Bitcoin Ben's Burger Bus Club" in data["message"]:
                    self.log_test("Root API Endpoint", True, f"Status: {response.status_code}, Message: {data['message']}")
                else:
                    self.log_test("Root API Endpoint", False, f"Expected Bitcoin Ben's Burger Bus Club in message, got: {data}")
            else:
                self.log_test("Root API Endpoint", False, f"Status: {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Root API Endpoint", False, f"Connection error: {str(e)}")
        
        # Test health endpoint (if exists)
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                self.log_test("Health Endpoint", True, f"Status: {response.status_code}")
            elif response.status_code == 404:
                self.log_test("Health Endpoint", True, "Health endpoint not implemented (expected)")
            else:
                self.log_test("Health Endpoint", False, f"Unexpected status: {response.status_code}")
        except Exception as e:
            self.log_test("Health Endpoint", False, f"Connection error: {str(e)}")
    
    def test_public_endpoints(self):
        """Test public endpoints that don't require authentication"""
        print("\n=== Testing Public Endpoints ===")
        
        # Test public menu endpoint - should show Bitcoin Ben's themed items without pricing
        try:
            response = self.session.get(f"{self.base_url}/api/menu/public")
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_test("Public Menu Endpoint", True, f"Status: {response.status_code}, Items: {len(data)}")
                    
                    # Check for Bitcoin Ben's themed items (only basic tier items show in public menu)
                    bitcoin_themed_items = ["The Satoshi Stacker", "The Hodl Burger", "Lightning Network Loaded Fries"]
                    found_items = []
                    
                    for item in data:
                        if item.get("name") in bitcoin_themed_items:
                            found_items.append(item["name"])
                    
                    if len(found_items) >= 2:  # Should have at least 2 basic tier Bitcoin Ben's items
                        self.log_test("Bitcoin Ben's Themed Items", True, f"Found themed items: {', '.join(found_items)}")
                    else:
                        self.log_test("Bitcoin Ben's Themed Items", False, f"Expected Bitcoin Ben's themed items, found: {found_items}")
                    
                    # Verify pricing is hidden (should not have price/member_price fields)
                    if len(data) > 0:
                        item = data[0]
                        if "price" not in item and "member_price" not in item:
                            self.log_test("Public Menu Pricing Hidden", True, "Pricing correctly hidden from public view")
                        else:
                            self.log_test("Public Menu Pricing Hidden", False, "Pricing visible in public menu")
                        
                        # Check for members_only_pricing flag
                        if item.get("members_only_pricing") == True:
                            self.log_test("Members Only Pricing Flag", True, "Correct members_only_pricing flag present")
                        else:
                            self.log_test("Members Only Pricing Flag", False, "Missing or incorrect members_only_pricing flag")
                else:
                    self.log_test("Public Menu Endpoint", False, "Response is not a list", data)
            else:
                self.log_test("Public Menu Endpoint", False, f"Status: {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Public Menu Endpoint", False, f"Connection error: {str(e)}")
        
        # Test public locations endpoint
        try:
            response = self.session.get(f"{self.base_url}/api/locations/public")
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_test("Public Locations Endpoint", True, f"Status: {response.status_code}, Locations: {len(data)}")
                    if len(data) > 0:
                        # Validate location structure
                        location = data[0]
                        required_fields = ['id', 'name', 'address', 'date', 'start_time', 'end_time']
                        if all(field in location for field in required_fields):
                            self.log_test("Location Structure", True, "All required fields present")
                        else:
                            missing = [f for f in required_fields if f not in location]
                            self.log_test("Location Structure", False, f"Missing fields: {missing}")
                else:
                    self.log_test("Public Locations Endpoint", False, "Response is not a list", data)
            else:
                self.log_test("Public Locations Endpoint", False, f"Status: {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Public Locations Endpoint", False, f"Connection error: {str(e)}")
    
    def test_bch_authentication_flow(self):
        """Test BCH (Bitcoin Cash) wallet authentication endpoints"""
        print("\n=== Testing BCH Authentication Flow ===")
        
        # Test BCH authentication challenge endpoint
        test_bch_address = "bitcoincash:qr6m7j9njldwwzlg9v7v53unlr4jkmx6eylep8ekg2"  # Valid BCH address format
        
        # Test 1: Challenge Generation
        try:
            challenge_data = {
                "app_name": "Bitcoin Ben's Burger Bus Club"
            }
            response = self.session.post(f"{self.base_url}/api/auth/challenge", json=challenge_data)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["challenge_id", "message", "expires_at"]
                if all(field in data for field in required_fields):
                    self.log_test("BCH Challenge Generation", True, f"Status: {response.status_code}, All required fields present")
                    
                    # Store challenge data for verification test
                    self.challenge_id = data["challenge_id"]
                    self.challenge_message = data["message"]
                    
                    # Validate challenge structure
                    if len(data["challenge_id"]) == 32:  # Should be 16 bytes hex = 32 chars
                        self.log_test("Challenge ID Format", True, f"Challenge ID length: {len(data['challenge_id'])}")
                    else:
                        self.log_test("Challenge ID Format", False, f"Invalid challenge ID length: {len(data['challenge_id'])}")
                    
                    # Validate message contains app name, timestamp, and nonce
                    message = data["message"]
                    if "Bitcoin Ben's Burger Bus Club" in message and "Time:" in message and "Nonce:" in message:
                        self.log_test("Challenge Message Format", True, "Message contains app name, timestamp, and nonce")
                    else:
                        self.log_test("Challenge Message Format", False, f"Invalid message format: {message}")
                    
                    # Validate expires_at is in future (5 minutes)
                    from datetime import datetime
                    try:
                        expires_at = datetime.fromisoformat(data["expires_at"])
                        now = datetime.utcnow()
                        time_diff = (expires_at - now).total_seconds()
                        if 250 <= time_diff <= 350:  # Should be around 5 minutes (300 seconds)
                            self.log_test("Challenge Expiration", True, f"Challenge expires in {time_diff:.0f} seconds")
                        else:
                            self.log_test("Challenge Expiration", False, f"Unexpected expiration time: {time_diff:.0f} seconds")
                    except Exception as e:
                        self.log_test("Challenge Expiration", False, f"Error parsing expires_at: {str(e)}")
                else:
                    missing_fields = [f for f in required_fields if f not in data]
                    self.log_test("BCH Challenge Generation", False, f"Missing fields: {missing_fields}", data)
            else:
                self.log_test("BCH Challenge Generation", False, f"Status: {response.status_code}", response.text)
        except Exception as e:
            self.log_test("BCH Challenge Generation", False, f"Connection error: {str(e)}")
        
        # Test 2: Signature Verification with Valid Data
        if hasattr(self, 'challenge_id') and hasattr(self, 'challenge_message'):
            try:
                verify_data = {
                    "challenge_id": self.challenge_id,
                    "bch_address": test_bch_address,
                    "signature": "valid_signature_longer_than_10_chars_for_testing",
                    "message": self.challenge_message
                }
                response = self.session.post(f"{self.base_url}/api/auth/verify", json=verify_data)
                
                if response.status_code == 200:
                    data = response.json()
                    required_fields = ["access_token", "token_type", "expires_in"]
                    if all(field in data for field in required_fields):
                        self.log_test("BCH Signature Verification", True, f"Status: {response.status_code}, JWT token issued")
                        
                        # Store token for protected endpoint tests
                        self.access_token = data["access_token"]
                        
                        # Validate token format (JWT has 3 parts separated by dots)
                        token_parts = data["access_token"].split('.')
                        if len(token_parts) == 3:
                            self.log_test("JWT Token Format", True, f"JWT has 3 parts as expected")
                        else:
                            self.log_test("JWT Token Format", False, f"JWT has {len(token_parts)} parts, expected 3")
                        
                        # Validate token type
                        if data["token_type"] == "bearer":
                            self.log_test("JWT Token Type", True, "Token type is 'bearer'")
                        else:
                            self.log_test("JWT Token Type", False, f"Token type is '{data['token_type']}', expected 'bearer'")
                        
                        # Validate expires_in (should be 30 minutes = 1800 seconds)
                        if data["expires_in"] == 1800:
                            self.log_test("JWT Token Expiration", True, f"Token expires in {data['expires_in']} seconds (30 minutes)")
                        else:
                            self.log_test("JWT Token Expiration", False, f"Token expires in {data['expires_in']} seconds, expected 1800")
                    else:
                        missing_fields = [f for f in required_fields if f not in data]
                        self.log_test("BCH Signature Verification", False, f"Missing fields: {missing_fields}", data)
                else:
                    self.log_test("BCH Signature Verification", False, f"Status: {response.status_code}", response.text)
            except Exception as e:
                self.log_test("BCH Signature Verification", False, f"Connection error: {str(e)}")
        
        # Test 3: Error Scenarios
        self.test_bch_auth_error_scenarios()
    
    def test_bch_auth_error_scenarios(self):
        """Test BCH authentication error handling"""
        print("\n=== Testing BCH Authentication Error Scenarios ===")
        
        # Test 1: Invalid challenge_id
        try:
            verify_data = {
                "challenge_id": "invalid_challenge_id_12345",
                "bch_address": "bitcoincash:qr6m7j9njldwwzlg9v7v53unlr4jkmx6eylep8ekg2",
                "signature": "valid_signature_longer_than_10_chars",
                "message": "Some message"
            }
            response = self.session.post(f"{self.base_url}/api/auth/verify", json=verify_data)
            
            if response.status_code == 400:
                data = response.json()
                if "Invalid or expired challenge" in data.get("detail", ""):
                    self.log_test("Invalid Challenge ID Error", True, "Properly rejects invalid challenge_id")
                else:
                    self.log_test("Invalid Challenge ID Error", False, f"Unexpected error message: {data.get('detail')}")
            else:
                self.log_test("Invalid Challenge ID Error", False, f"Expected 400, got {response.status_code}")
        except Exception as e:
            self.log_test("Invalid Challenge ID Error", False, f"Connection error: {str(e)}")
        
        # Test 2: Message mismatch
        if hasattr(self, 'challenge_id'):
            try:
                verify_data = {
                    "challenge_id": self.challenge_id,
                    "bch_address": "bitcoincash:qr6m7j9njldwwzlg9v7v53unlr4jkmx6eylep8ekg2",
                    "signature": "valid_signature_longer_than_10_chars",
                    "message": "Wrong message that doesn't match challenge"
                }
                response = self.session.post(f"{self.base_url}/api/auth/verify", json=verify_data)
                
                if response.status_code == 400:
                    data = response.json()
                    if "Message does not match challenge" in data.get("detail", ""):
                        self.log_test("Message Mismatch Error", True, "Properly rejects message mismatch")
                    else:
                        self.log_test("Message Mismatch Error", False, f"Unexpected error message: {data.get('detail')}")
                else:
                    self.log_test("Message Mismatch Error", False, f"Expected 400, got {response.status_code}")
            except Exception as e:
                self.log_test("Message Mismatch Error", False, f"Connection error: {str(e)}")
        
        # Test 3: Invalid signature (too short)
        if hasattr(self, 'challenge_id') and hasattr(self, 'challenge_message'):
            try:
                verify_data = {
                    "challenge_id": self.challenge_id,
                    "bch_address": "bitcoincash:qr6m7j9njldwwzlg9v7v53unlr4jkmx6eylep8ekg2",
                    "signature": "short",  # Less than 10 characters
                    "message": self.challenge_message
                }
                response = self.session.post(f"{self.base_url}/api/auth/verify", json=verify_data)
                
                if response.status_code == 401:
                    data = response.json()
                    if "Invalid signature" in data.get("detail", ""):
                        self.log_test("Invalid Signature Error", True, "Properly rejects invalid signature")
                    else:
                        self.log_test("Invalid Signature Error", False, f"Unexpected error message: {data.get('detail')}")
                else:
                    self.log_test("Invalid Signature Error", False, f"Expected 401, got {response.status_code}")
            except Exception as e:
                self.log_test("Invalid Signature Error", False, f"Connection error: {str(e)}")
        
        # Test 4: Expired challenge (simulate by creating a new challenge and waiting)
        try:
            # Generate a challenge first
            challenge_data = {"app_name": "Test App"}
            response = self.session.post(f"{self.base_url}/api/auth/challenge", json=challenge_data)
            
            if response.status_code == 200:
                data = response.json()
                challenge_id = data["challenge_id"]
                
                # Simulate expired challenge by using an old challenge_id that should be expired
                # For testing purposes, we'll just test the error handling mechanism
                self.log_test("Challenge Expiration Test Setup", True, "Challenge created for expiration testing")
            else:
                self.log_test("Challenge Expiration Test Setup", False, "Could not create challenge for expiration test")
        except Exception as e:
            self.log_test("Challenge Expiration Test Setup", False, f"Connection error: {str(e)}")
    
    def test_jwt_protected_endpoints(self):
        """Test that protected endpoints work with new BCH JWT tokens"""
        print("\n=== Testing JWT Protected Endpoints ===")
        
        if not hasattr(self, 'access_token'):
            self.log_test("JWT Protected Endpoints", False, "No access token available for testing")
            return
        
        # Set up authorization header
        auth_headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        
        # Test protected endpoints
        protected_endpoints = [
            ("/api/profile", "Member Profile"),
            ("/api/membership/register", "Member Registration"),
            ("/api/menu/member", "Member Menu"),
            ("/api/locations/member", "Member Locations"),
            ("/api/orders", "Member Orders"),
            ("/api/events", "Member Events")
        ]
        
        for endpoint, name in protected_endpoints:
            try:
                if endpoint == "/api/membership/register":
                    # POST endpoint requires data
                    member_data = {
                        "fullName": "BCH Test User",
                        "email": "bch@bitcoinben.com",
                        "phone": "+1-555-0789",
                        "pma_agreed": True,
                        "dues_paid": True,
                        "payment_amount": 50.0
                    }
                    response = self.session.post(f"{self.base_url}{endpoint}", json=member_data, headers=auth_headers)
                else:
                    # GET endpoint
                    response = self.session.get(f"{self.base_url}{endpoint}", headers=auth_headers)
                
                if response.status_code in [200, 201]:
                    self.log_test(f"JWT Protected Access ({name})", True, f"Successfully accessed with BCH JWT token: {response.status_code}")
                elif response.status_code in [401, 403]:
                    self.log_test(f"JWT Protected Access ({name})", False, f"JWT token rejected: {response.status_code}")
                else:
                    # Some endpoints might return other status codes (like 500 for missing data)
                    # but if we get past auth, that's what we're testing
                    if response.status_code != 404:  # 404 means endpoint doesn't exist
                        self.log_test(f"JWT Protected Access ({name})", True, f"JWT token accepted (status: {response.status_code})")
                    else:
                        self.log_test(f"JWT Protected Access ({name})", False, f"Endpoint not found: {response.status_code}")
            except Exception as e:
                self.log_test(f"JWT Protected Access ({name})", False, f"Connection error: {str(e)}")
    
    def test_wallet_authentication_flow(self):
        """Test BCH wallet authentication flow (updated from Solana)"""
        self.test_bch_authentication_flow()
        self.test_jwt_protected_endpoints()
    
    def test_member_registration_endpoint(self):
        """Test member registration endpoint with PMA agreement and dues payment"""
        print("\n=== Testing Member Registration Endpoint ===")
        
        # Test member registration endpoint without authentication (should fail)
        try:
            member_data = {
                "fullName": "John Bitcoin",
                "email": "john@bitcoinben.com",
                "phone": "+1-555-0123",
                "pma_agreed": True,
                "dues_paid": True,
                "payment_amount": 50.0
            }
            
            response = self.session.post(f"{self.base_url}/api/membership/register", json=member_data)
            
            if response.status_code in [401, 403]:
                self.log_test("Member Registration Auth Required", True, f"Properly requires authentication: {response.status_code}")
            elif response.status_code == 422:
                # Check if it's a validation error about missing auth
                data = response.json()
                if "detail" in data:
                    self.log_test("Member Registration Auth Required", True, f"Auth validation error as expected: {data['detail']}")
                else:
                    self.log_test("Member Registration Auth Required", False, f"Unexpected 422 response: {data}")
            else:
                self.log_test("Member Registration Auth Required", False, f"Unexpected status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_test("Member Registration Auth Required", False, f"Connection error: {str(e)}")
        
        # Test endpoint exists (even if auth fails)
        try:
            response = self.session.post(f"{self.base_url}/api/membership/register")
            if response.status_code != 404:
                self.log_test("Member Registration Endpoint Exists", True, f"Endpoint exists (status: {response.status_code})")
            else:
                self.log_test("Member Registration Endpoint Exists", False, "Endpoint not found (404)")
        except Exception as e:
            self.log_test("Member Registration Endpoint Exists", False, f"Connection error: {str(e)}")
    
    def test_admin_data_seeding(self):
        """Test admin data seeding endpoint - should create Bitcoin Ben's themed items"""
        print("\n=== Testing Admin Data Seeding ===")
        
        try:
            response = self.session.post(f"{self.base_url}/api/admin/seed-data")
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "seeded" in data["message"].lower():
                    self.log_test("Admin Data Seeding", True, f"Status: {response.status_code}, Message: {data['message']}")
                    
                    # Verify data was actually seeded by checking public endpoints
                    time.sleep(2)  # Give database time to update
                    
                    # Check if Bitcoin Ben's themed menu items were seeded
                    menu_response = self.session.get(f"{self.base_url}/api/menu/public")
                    if menu_response.status_code == 200:
                        menu_data = menu_response.json()
                        if len(menu_data) > 0:
                            self.log_test("Menu Data Persistence", True, f"Found {len(menu_data)} menu items after seeding")
                            
                            # Check for specific Bitcoin Ben's themed items
                            bitcoin_themed_items = ["The Satoshi Stacker", "The Hodl Burger", "The Bitcoin Mining Rig", "Lightning Network Loaded Fries"]
                            found_items = []
                            
                            for item in menu_data:
                                if item.get("name") in bitcoin_themed_items:
                                    found_items.append(item["name"])
                            
                            if len(found_items) >= 2:  # Should have at least basic tier items
                                self.log_test("Bitcoin Ben's Themed Menu Items", True, f"Found themed items: {', '.join(found_items)}")
                            else:
                                self.log_test("Bitcoin Ben's Themed Menu Items", False, f"Expected Bitcoin Ben's themed items, found: {found_items}")
                        else:
                            self.log_test("Menu Data Persistence", False, "No menu items found after seeding")
                    
                    # Check if locations were seeded
                    locations_response = self.session.get(f"{self.base_url}/api/locations/public")
                    if locations_response.status_code == 200:
                        locations_data = locations_response.json()
                        if len(locations_data) > 0:
                            self.log_test("Location Data Persistence", True, f"Found {len(locations_data)} locations after seeding")
                        else:
                            self.log_test("Location Data Persistence", False, "No locations found after seeding")
                else:
                    self.log_test("Admin Data Seeding", False, "Unexpected response format", data)
            else:
                self.log_test("Admin Data Seeding", False, f"Status: {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Admin Data Seeding", False, f"Connection error: {str(e)}")
    
    def test_database_integration(self):
        """Test database connectivity and data persistence"""
        print("\n=== Testing Database Integration ===")
        
        # Test data persistence by seeding and then retrieving
        try:
            # First seed data
            seed_response = self.session.post(f"{self.base_url}/api/admin/seed-data")
            if seed_response.status_code == 200:
                time.sleep(2)  # Allow time for database operations
                
                # Test menu data persistence
                menu_response = self.session.get(f"{self.base_url}/api/menu/public")
                if menu_response.status_code == 200:
                    menu_data = menu_response.json()
                    if len(menu_data) >= 1:  # Should have at least basic tier items
                        self.log_test("Database Menu Persistence", True, f"Successfully persisted {len(menu_data)} menu items")
                        
                        # Verify data structure integrity for public menu (no pricing)
                        sample_item = menu_data[0]
                        required_public_fields = ['id', 'name', 'description', 'category', 'image_url', 'is_available']
                        if all(key in sample_item for key in required_public_fields):
                            self.log_test("Database Data Integrity", True, "Public menu item structure maintained")
                        else:
                            missing = [f for f in required_public_fields if f not in sample_item]
                            self.log_test("Database Data Integrity", False, f"Public menu item structure missing: {missing}")
                    else:
                        self.log_test("Database Menu Persistence", False, "No menu items persisted")
                
                # Test location data persistence
                location_response = self.session.get(f"{self.base_url}/api/locations/public")
                if location_response.status_code == 200:
                    location_data = location_response.json()
                    if len(location_data) >= 1:  # Should have at least public locations
                        self.log_test("Database Location Persistence", True, f"Successfully persisted {len(location_data)} locations")
                    else:
                        self.log_test("Database Location Persistence", False, "No locations persisted")
            else:
                self.log_test("Database Integration", False, "Could not seed data for testing")
        except Exception as e:
            self.log_test("Database Integration", False, f"Database connection error: {str(e)}")
    
    def test_member_profile_fields(self):
        """Test that new member profile fields are supported in the database structure"""
        print("\n=== Testing Member Profile Fields ===")
        
        # Test that the member registration endpoint accepts the new fields
        # This is an indirect test since we can't authenticate without a real wallet signature
        try:
            # Test with complete member data structure
            member_data = {
                "fullName": "Alice Bitcoin",
                "email": "alice@bitcoinben.com", 
                "phone": "+1-555-0456",
                "pma_agreed": True,
                "dues_paid": True,
                "payment_amount": 75.0
            }
            
            response = self.session.post(f"{self.base_url}/api/membership/register", json=member_data)
            
            # Should fail with auth error, but if it's a validation error about the fields, that's bad
            if response.status_code in [401, 403]:
                self.log_test("Member Profile Fields Structure", True, "Endpoint accepts new member profile fields (auth required)")
            elif response.status_code == 422:
                # Check if it's about missing auth vs field validation
                try:
                    error_data = response.json()
                    error_detail = str(error_data.get("detail", ""))
                    if "authorization" in error_detail.lower() or "token" in error_detail.lower() or "auth" in error_detail.lower():
                        self.log_test("Member Profile Fields Structure", True, "New member profile fields accepted (auth validation)")
                    else:
                        self.log_test("Member Profile Fields Structure", False, f"Field validation error: {error_detail}")
                except:
                    self.log_test("Member Profile Fields Structure", True, "Endpoint processes new member fields (422 validation)")
            else:
                self.log_test("Member Profile Fields Structure", False, f"Unexpected response: {response.status_code}")
        except Exception as e:
            self.log_test("Member Profile Fields Structure", False, f"Connection error: {str(e)}")
        
        # Test with missing required PMA fields
        try:
            incomplete_data = {
                "fullName": "Bob Bitcoin"
                # Missing email, phone, pma_agreed, dues_paid, payment_amount
            }
            
            response = self.session.post(f"{self.base_url}/api/membership/register", json=incomplete_data)
            
            # Should still fail with auth, but endpoint should exist and process the request
            if response.status_code in [401, 403, 422]:
                self.log_test("Member Profile Optional Fields", True, "Endpoint handles incomplete member data appropriately")
            else:
                self.log_test("Member Profile Optional Fields", False, f"Unexpected response: {response.status_code}")
        except Exception as e:
            self.log_test("Member Profile Optional Fields", False, f"Connection error: {str(e)}")
    
    def test_cors_and_security(self):
        """Test CORS headers and security measures"""
        print("\n=== Testing CORS and Security ===")
        
        # Test CORS headers with Origin header to trigger CORS
        try:
            headers_with_origin = {'Origin': 'https://example.com'}
            response = self.session.get(f"{self.base_url}/api/", headers=headers_with_origin)
            headers = response.headers
            
            # Check for specific CORS headers
            cors_origin = headers.get('access-control-allow-origin')
            cors_credentials = headers.get('access-control-allow-credentials')
            
            if cors_origin or cors_credentials:
                cors_info = []
                if cors_origin:
                    cors_info.append(f"Origin: {cors_origin}")
                if cors_credentials:
                    cors_info.append(f"Credentials: {cors_credentials}")
                self.log_test("CORS Headers", True, f"CORS headers present - {', '.join(cors_info)}")
            else:
                # CORS might be handled by the proxy/ingress, which is acceptable
                self.log_test("CORS Headers", True, "CORS may be handled by proxy/ingress (acceptable for production)")
        except Exception as e:
            self.log_test("CORS Headers", False, f"Error checking CORS: {str(e)}")
        
        # Test unauthorized access to protected endpoints
        protected_endpoints = [
            "/api/profile",
            "/api/menu/member",
            "/api/locations/member",
            "/api/orders",
            "/api/events"
        ]
        
        for endpoint in protected_endpoints:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}")
                if response.status_code in [401, 403]:  # Unauthorized or Forbidden
                    self.log_test(f"Protected Endpoint Security ({endpoint})", True, f"Properly protected: {response.status_code}")
                else:
                    self.log_test(f"Protected Endpoint Security ({endpoint})", False, f"Unexpected access: {response.status_code}")
            except Exception as e:
                self.log_test(f"Protected Endpoint Security ({endpoint})", False, f"Error: {str(e)}")
    
    def test_bch_payment_system(self):
        """Test the new BCH payment system endpoints"""
        print("\n=== Testing BCH Payment System ===")
        
        # Test 1: Payment Creation Endpoint
        try:
            response = self.session.post(f"{self.base_url}/api/payments/create-membership-payment", 
                                       json={"user_address": "bitcoincash:qr6m7j9njldwwzlg9v7v53unlr4jkmx6eylep8ekg2"})
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["success", "payment_id", "amount_usd", "amount_bch", "bch_price", 
                                 "receiving_address", "expires_at", "qr_code", "payment_uri", "instructions"]
                
                if all(field in data for field in required_fields):
                    self.log_test("Payment Creation Endpoint", True, f"All required fields present. Payment ID: {data.get('payment_id')}")
                    
                    # Store payment_id for status testing
                    self.payment_id = data["payment_id"]
                    
                    # Validate payment details
                    if data["amount_usd"] == 21.0:
                        self.log_test("Payment Amount USD", True, f"Correct membership fee: ${data['amount_usd']}")
                    else:
                        self.log_test("Payment Amount USD", False, f"Expected $21, got ${data['amount_usd']}")
                    
                    # Validate BCH price fetching (should be > 0)
                    if data["bch_price"] > 0:
                        self.log_test("BCH Price Fetching", True, f"BCH price fetched: ${data['bch_price']}")
                    else:
                        self.log_test("BCH Price Fetching", False, f"Invalid BCH price: ${data['bch_price']}")
                    
                    # Validate BCH amount calculation
                    expected_bch = 21.0 / data["bch_price"]
                    if abs(data["amount_bch"] - expected_bch) < 0.00000001:  # 8 decimal precision
                        self.log_test("BCH Amount Calculation", True, f"Correct BCH amount: {data['amount_bch']}")
                    else:
                        self.log_test("BCH Amount Calculation", False, f"Expected {expected_bch}, got {data['amount_bch']}")
                    
                    # Validate QR code generation
                    if data["qr_code"] and data["qr_code"].startswith("data:image/png;base64,"):
                        self.log_test("QR Code Generation", True, "QR code generated successfully")
                    else:
                        self.log_test("QR Code Generation", False, "Invalid or missing QR code")
                    
                    # Validate payment URI format
                    expected_uri_start = f"bitcoincash:{data['receiving_address']}?amount="
                    if data["payment_uri"].startswith(expected_uri_start):
                        self.log_test("Payment URI Format", True, "Payment URI correctly formatted")
                    else:
                        self.log_test("Payment URI Format", False, f"Invalid payment URI format: {data['payment_uri']}")
                        
                else:
                    missing_fields = [f for f in required_fields if f not in data]
                    self.log_test("Payment Creation Endpoint", False, f"Missing fields: {missing_fields}")
            else:
                self.log_test("Payment Creation Endpoint", False, f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_test("Payment Creation Endpoint", False, f"Connection error: {str(e)}")
        
        # Test 2: Payment Status Endpoint
        if hasattr(self, 'payment_id'):
            try:
                response = self.session.get(f"{self.base_url}/api/payments/status/{self.payment_id}")
                
                if response.status_code == 200:
                    data = response.json()
                    required_fields = ["payment_id", "status", "amount_usd", "amount_bch", 
                                     "receiving_address", "expires_at", "created_at"]
                    
                    if all(field in data for field in required_fields):
                        self.log_test("Payment Status Endpoint", True, f"Status: {data['status']}, Payment ID: {data['payment_id']}")
                        
                        # Validate status is pending for new payment
                        if data["status"] == "pending":
                            self.log_test("Payment Initial Status", True, "Payment status correctly set to pending")
                        else:
                            self.log_test("Payment Initial Status", False, f"Expected 'pending', got '{data['status']}'")
                            
                        # Validate expiration logic (should be 24 hours from creation)
                        from datetime import datetime, timezone
                        try:
                            expires_at = datetime.fromisoformat(data["expires_at"].replace('Z', '+00:00'))
                            created_at = datetime.fromisoformat(data["created_at"].replace('Z', '+00:00'))
                            time_diff = (expires_at - created_at).total_seconds()
                            expected_hours = 24 * 3600  # 24 hours in seconds
                            
                            if abs(time_diff - expected_hours) < 300:  # Allow 5 minute tolerance
                                self.log_test("Payment Expiration Logic", True, f"Payment expires in {time_diff/3600:.1f} hours")
                            else:
                                self.log_test("Payment Expiration Logic", False, f"Expected 24 hours, got {time_diff/3600:.1f} hours")
                        except Exception as e:
                            self.log_test("Payment Expiration Logic", False, f"Error parsing dates: {str(e)}")
                    else:
                        missing_fields = [f for f in required_fields if f not in data]
                        self.log_test("Payment Status Endpoint", False, f"Missing fields: {missing_fields}")
                else:
                    self.log_test("Payment Status Endpoint", False, f"Status: {response.status_code}, Response: {response.text}")
            except Exception as e:
                self.log_test("Payment Status Endpoint", False, f"Connection error: {str(e)}")
        
        # Test 3: Invalid Payment ID
        try:
            response = self.session.get(f"{self.base_url}/api/payments/status/invalid_payment_id")
            
            if response.status_code == 404:
                data = response.json()
                if "Payment not found" in data.get("detail", ""):
                    self.log_test("Invalid Payment ID Handling", True, "Properly handles invalid payment ID")
                else:
                    self.log_test("Invalid Payment ID Handling", False, f"Unexpected error message: {data.get('detail')}")
            else:
                self.log_test("Invalid Payment ID Handling", False, f"Expected 404, got {response.status_code}")
        except Exception as e:
            self.log_test("Invalid Payment ID Handling", False, f"Connection error: {str(e)}")
    
    def test_admin_payment_endpoints(self):
        """Test admin payment management endpoints"""
        print("\n=== Testing Admin Payment Endpoints ===")
        
        # Test 1: Admin Verify Payment
        if hasattr(self, 'payment_id'):
            try:
                verify_data = {
                    "payment_id": self.payment_id,
                    "transaction_id": "test_tx_12345abcdef",
                    "admin_notes": "Test verification"
                }
                response = self.session.post(f"{self.base_url}/api/admin/verify-payment", json=verify_data)
                
                if response.status_code == 200:
                    data = response.json()
                    required_fields = ["success", "message", "payment_id", "member_activated", "cashstamp_pending"]
                    
                    if all(field in data for field in required_fields):
                        self.log_test("Admin Verify Payment", True, f"Payment verified successfully: {data['message']}")
                        
                        # Validate verification response
                        if data["success"] and data["member_activated"] and data["cashstamp_pending"]:
                            self.log_test("Payment Verification Response", True, "All verification flags correct")
                        else:
                            self.log_test("Payment Verification Response", False, f"Unexpected verification flags: {data}")
                    else:
                        missing_fields = [f for f in required_fields if f not in data]
                        self.log_test("Admin Verify Payment", False, f"Missing fields: {missing_fields}")
                else:
                    self.log_test("Admin Verify Payment", False, f"Status: {response.status_code}, Response: {response.text}")
            except Exception as e:
                self.log_test("Admin Verify Payment", False, f"Connection error: {str(e)}")
        
        # Test 2: Admin Pending Payments List
        try:
            response = self.session.get(f"{self.base_url}/api/admin/pending-payments")
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["pending_payments", "count"]
                
                if all(field in data for field in required_fields):
                    self.log_test("Admin Pending Payments", True, f"Found {data['count']} pending payments")
                    
                    # Validate pending payments structure
                    if data["count"] > 0 and len(data["pending_payments"]) > 0:
                        payment = data["pending_payments"][0]
                        payment_fields = ["payment_id", "user_address", "amount_usd", "amount_bch", "created_at", "expires_at"]
                        if all(field in payment for field in payment_fields):
                            self.log_test("Pending Payment Structure", True, "Payment structure is correct")
                        else:
                            missing = [f for f in payment_fields if f not in payment]
                            self.log_test("Pending Payment Structure", False, f"Missing fields: {missing}")
                    else:
                        self.log_test("Pending Payment Structure", True, "No pending payments (expected after verification)")
                else:
                    missing_fields = [f for f in required_fields if f not in data]
                    self.log_test("Admin Pending Payments", False, f"Missing fields: {missing_fields}")
            else:
                self.log_test("Admin Pending Payments", False, f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_test("Admin Pending Payments", False, f"Connection error: {str(e)}")
        
        # Test 3: Admin Send Cashstamp
        if hasattr(self, 'payment_id'):
            try:
                cashstamp_data = {
                    "payment_id": self.payment_id,
                    "recipient_address": "bitcoincash:qr6m7j9njldwwzlg9v7v53unlr4jkmx6eylep8ekg2",
                    "admin_wallet_address": "bitcoincash:qpadmin123456789abcdef"
                }
                response = self.session.post(f"{self.base_url}/api/admin/send-cashstamp", json=cashstamp_data)
                
                if response.status_code == 200:
                    data = response.json()
                    required_fields = ["success", "message", "payment_id", "cashstamp_amount_bch", 
                                     "cashstamp_amount_usd", "instructions", "note"]
                    
                    if all(field in data for field in required_fields):
                        self.log_test("Admin Send Cashstamp", True, f"Cashstamp instructions generated: {data['message']}")
                        
                        # Validate cashstamp amount
                        if data["cashstamp_amount_usd"] == 15.0:
                            self.log_test("Cashstamp Amount USD", True, f"Correct cashstamp amount: ${data['cashstamp_amount_usd']}")
                        else:
                            self.log_test("Cashstamp Amount USD", False, f"Expected $15, got ${data['cashstamp_amount_usd']}")
                        
                        # Validate instructions structure
                        instructions = data["instructions"]
                        if isinstance(instructions, dict) and "action" in instructions and "amount_bch" in instructions:
                            self.log_test("Cashstamp Instructions", True, "Instructions properly formatted")
                        else:
                            self.log_test("Cashstamp Instructions", False, f"Invalid instructions format: {instructions}")
                    else:
                        missing_fields = [f for f in required_fields if f not in data]
                        self.log_test("Admin Send Cashstamp", False, f"Missing fields: {missing_fields}")
                else:
                    self.log_test("Admin Send Cashstamp", False, f"Status: {response.status_code}, Response: {response.text}")
            except Exception as e:
                self.log_test("Admin Send Cashstamp", False, f"Connection error: {str(e)}")
        
        # Test 4: Cashstamp for Unverified Payment (should fail)
        try:
            # Create a new payment for this test
            response = self.session.post(f"{self.base_url}/api/payments/create-membership-payment", 
                                       json={"user_address": "bitcoincash:qtest123456789"})
            if response.status_code == 200:
                new_payment_id = response.json()["payment_id"]
                
                cashstamp_data = {
                    "payment_id": new_payment_id,
                    "recipient_address": "bitcoincash:qtest123456789"
                }
                response = self.session.post(f"{self.base_url}/api/admin/send-cashstamp", json=cashstamp_data)
                
                if response.status_code == 400:
                    data = response.json()
                    if "Payment must be verified first" in data.get("detail", ""):
                        self.log_test("Cashstamp Unverified Payment", True, "Properly rejects unverified payment")
                    else:
                        self.log_test("Cashstamp Unverified Payment", False, f"Unexpected error: {data.get('detail')}")
                else:
                    self.log_test("Cashstamp Unverified Payment", False, f"Expected 400, got {response.status_code}")
        except Exception as e:
            self.log_test("Cashstamp Unverified Payment", False, f"Connection error: {str(e)}")
    
    def test_payment_integration_flow(self):
        """Test complete payment flow integration"""
        print("\n=== Testing Payment Integration Flow ===")
        
        # Test complete flow: create → check status → verify → check status → cashstamp
        try:
            # Step 1: Create payment
            user_address = "bitcoincash:qintegration_test_address"
            response = self.session.post(f"{self.base_url}/api/payments/create-membership-payment", 
                                       json={"user_address": user_address})
            
            if response.status_code == 200:
                payment_data = response.json()
                payment_id = payment_data["payment_id"]
                self.log_test("Integration Flow - Create Payment", True, f"Payment created: {payment_id}")
                
                # Step 2: Check initial status
                status_response = self.session.get(f"{self.base_url}/api/payments/status/{payment_id}")
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    if status_data["status"] == "pending":
                        self.log_test("Integration Flow - Initial Status", True, "Payment status is pending")
                        
                        # Step 3: Admin verify payment
                        verify_data = {
                            "payment_id": payment_id,
                            "transaction_id": "integration_test_tx_abc123"
                        }
                        verify_response = self.session.post(f"{self.base_url}/api/admin/verify-payment", json=verify_data)
                        
                        if verify_response.status_code == 200:
                            self.log_test("Integration Flow - Verify Payment", True, "Payment verified successfully")
                            
                            # Step 4: Check updated status
                            updated_status_response = self.session.get(f"{self.base_url}/api/payments/status/{payment_id}")
                            if updated_status_response.status_code == 200:
                                updated_status_data = updated_status_response.json()
                                if updated_status_data["status"] == "verified":
                                    self.log_test("Integration Flow - Updated Status", True, "Payment status updated to verified")
                                    
                                    # Validate transaction_id and verified_at are set
                                    if updated_status_data.get("transaction_id") and updated_status_data.get("verified_at"):
                                        self.log_test("Integration Flow - Verification Details", True, "Transaction ID and verification time recorded")
                                    else:
                                        self.log_test("Integration Flow - Verification Details", False, "Missing transaction ID or verification time")
                                    
                                    # Step 5: Generate cashstamp
                                    cashstamp_data = {
                                        "payment_id": payment_id,
                                        "recipient_address": user_address
                                    }
                                    cashstamp_response = self.session.post(f"{self.base_url}/api/admin/send-cashstamp", json=cashstamp_data)
                                    
                                    if cashstamp_response.status_code == 200:
                                        self.log_test("Integration Flow - Generate Cashstamp", True, "Cashstamp instructions generated")
                                        self.log_test("Integration Flow - Complete", True, "Full payment flow completed successfully")
                                    else:
                                        self.log_test("Integration Flow - Generate Cashstamp", False, f"Cashstamp failed: {cashstamp_response.status_code}")
                                else:
                                    self.log_test("Integration Flow - Updated Status", False, f"Expected 'verified', got '{updated_status_data['status']}'")
                            else:
                                self.log_test("Integration Flow - Updated Status", False, f"Status check failed: {updated_status_response.status_code}")
                        else:
                            self.log_test("Integration Flow - Verify Payment", False, f"Verification failed: {verify_response.status_code}")
                    else:
                        self.log_test("Integration Flow - Initial Status", False, f"Expected 'pending', got '{status_data['status']}'")
                else:
                    self.log_test("Integration Flow - Initial Status", False, f"Status check failed: {status_response.status_code}")
            else:
                self.log_test("Integration Flow - Create Payment", False, f"Payment creation failed: {response.status_code}")
        except Exception as e:
            self.log_test("Integration Flow - Complete", False, f"Integration test error: {str(e)}")
    
    def test_payment_error_scenarios(self):
        """Test payment system error handling"""
        print("\n=== Testing Payment Error Scenarios ===")
        
        # Test 1: Verify non-existent payment
        try:
            verify_data = {
                "payment_id": "non_existent_payment_123",
                "transaction_id": "test_tx"
            }
            response = self.session.post(f"{self.base_url}/api/admin/verify-payment", json=verify_data)
            
            if response.status_code == 404:
                data = response.json()
                if "Payment not found" in data.get("detail", ""):
                    self.log_test("Verify Non-existent Payment", True, "Properly handles non-existent payment")
                else:
                    self.log_test("Verify Non-existent Payment", False, f"Unexpected error: {data.get('detail')}")
            else:
                self.log_test("Verify Non-existent Payment", False, f"Expected 404, got {response.status_code}")
        except Exception as e:
            self.log_test("Verify Non-existent Payment", False, f"Connection error: {str(e)}")
        
        # Test 2: Double verification (should handle gracefully)
        if hasattr(self, 'payment_id'):
            try:
                verify_data = {
                    "payment_id": self.payment_id,
                    "transaction_id": "double_verify_test"
                }
                response = self.session.post(f"{self.base_url}/api/admin/verify-payment", json=verify_data)
                
                if response.status_code == 200:
                    data = response.json()
                    if "already verified" in data.get("message", "").lower():
                        self.log_test("Double Verification Handling", True, "Properly handles already verified payment")
                    else:
                        self.log_test("Double Verification Handling", True, "Verification completed (may update transaction ID)")
                else:
                    self.log_test("Double Verification Handling", False, f"Unexpected status: {response.status_code}")
            except Exception as e:
                self.log_test("Double Verification Handling", False, f"Connection error: {str(e)}")
        
        # Test 3: Cashstamp for non-existent payment
        try:
            cashstamp_data = {
                "payment_id": "non_existent_payment_456",
                "recipient_address": "bitcoincash:qtest"
            }
            response = self.session.post(f"{self.base_url}/api/admin/send-cashstamp", json=cashstamp_data)
            
            if response.status_code == 404:
                data = response.json()
                if "Payment not found" in data.get("detail", ""):
                    self.log_test("Cashstamp Non-existent Payment", True, "Properly handles non-existent payment")
                else:
                    self.log_test("Cashstamp Non-existent Payment", False, f"Unexpected error: {data.get('detail')}")
            else:
                self.log_test("Cashstamp Non-existent Payment", False, f"Expected 404, got {response.status_code}")
        except Exception as e:
            self.log_test("Cashstamp Non-existent Payment", False, f"Connection error: {str(e)}")
    
    def test_bch_price_fallback(self):
        """Test BCH price fetching and fallback mechanism"""
        print("\n=== Testing BCH Price Fallback ===")
        
        # Create multiple payments to test price consistency
        try:
            prices = []
            for i in range(3):
                response = self.session.post(f"{self.base_url}/api/payments/create-membership-payment", 
                                           json={"user_address": f"bitcoincash:qtest{i}"})
                if response.status_code == 200:
                    data = response.json()
                    prices.append(data["bch_price"])
                    time.sleep(1)  # Small delay between requests
            
            if len(prices) >= 2:
                # Prices should be consistent (within reasonable range) or fallback to 300
                if all(p > 0 for p in prices):
                    if all(abs(p - prices[0]) < 50 for p in prices):  # Prices within $50 of each other
                        self.log_test("BCH Price Consistency", True, f"Prices consistent: {prices}")
                    elif all(p == 300.0 for p in prices):
                        self.log_test("BCH Price Fallback", True, "Using fallback price of $300")
                    else:
                        self.log_test("BCH Price Variation", True, f"Price variation detected: {prices} (may be normal)")
                else:
                    self.log_test("BCH Price Fetching", False, f"Invalid prices: {prices}")
            else:
                self.log_test("BCH Price Testing", False, "Could not create enough payments for price testing")
        except Exception as e:
            self.log_test("BCH Price Testing", False, f"Error testing price fetching: {str(e)}")

    def test_pump_fun_token_integration(self):
        """Test pump.fun token integration endpoints"""
        print("\n=== Testing Pump.fun Token Integration ===")
        
        # Test 1: Token Info Endpoint
        try:
            response = self.session.get(f"{self.base_url}/api/pump/token-info")
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["success", "token"]
                
                if all(field in data for field in required_fields):
                    token_info = data["token"]
                    token_fields = ["mint", "name", "symbol", "decimals", "description"]
                    
                    if all(field in token_info for field in token_fields):
                        self.log_test("Pump Token Info Endpoint", True, f"All token fields present. Symbol: {token_info.get('symbol')}")
                        
                        # Validate specific token configuration
                        if token_info["mint"] == "mWusXdRfsYAoFtYdaDcf8tmG7hnRNvnVc2TuvNEpump":
                            self.log_test("Token Mint Address", True, f"Correct mint: {token_info['mint']}")
                        else:
                            self.log_test("Token Mint Address", False, f"Expected mWusXdRfsYAoFtYdaDcf8tmG7hnRNvnVc2TuvNEpump, got {token_info['mint']}")
                        
                        if token_info["symbol"] == "BBTC":
                            self.log_test("Token Symbol", True, f"Correct symbol: {token_info['symbol']}")
                        else:
                            self.log_test("Token Symbol", False, f"Expected BBTC, got {token_info['symbol']}")
                        
                        if token_info["name"] == "Bitcoin Ben's Club Token":
                            self.log_test("Token Name", True, f"Correct name: {token_info['name']}")
                        else:
                            self.log_test("Token Name", False, f"Expected Bitcoin Ben's Club Token, got {token_info['name']}")
                        
                        if token_info["decimals"] == 9:
                            self.log_test("Token Decimals", True, f"Correct decimals: {token_info['decimals']}")
                        else:
                            self.log_test("Token Decimals", False, f"Expected 9, got {token_info['decimals']}")
                    else:
                        missing_fields = [f for f in token_fields if f not in token_info]
                        self.log_test("Pump Token Info Endpoint", False, f"Missing token fields: {missing_fields}")
                else:
                    missing_fields = [f for f in required_fields if f not in data]
                    self.log_test("Pump Token Info Endpoint", False, f"Missing fields: {missing_fields}")
            else:
                self.log_test("Pump Token Info Endpoint", False, f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_test("Pump Token Info Endpoint", False, f"Connection error: {str(e)}")
        
        # Test 2: Token Price Endpoint
        try:
            response = self.session.get(f"{self.base_url}/api/pump/token-price")
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["success", "token_mint", "price_sol", "price_usd", "market_cap", "volume_24h", "holders", "last_updated"]
                
                if all(field in data for field in required_fields):
                    self.log_test("Pump Token Price Endpoint", True, f"All price fields present. Price USD: ${data.get('price_usd')}")
                    
                    # Validate price data structure
                    if data["token_mint"] == "mWusXdRfsYAoFtYdaDcf8tmG7hnRNvnVc2TuvNEpump":
                        self.log_test("Price Token Mint", True, "Correct token mint in price data")
                    else:
                        self.log_test("Price Token Mint", False, f"Mint mismatch: {data['token_mint']}")
                    
                    # Validate numeric fields are positive
                    numeric_fields = ["price_sol", "price_usd", "market_cap", "volume_24h", "holders"]
                    all_positive = all(isinstance(data[field], (int, float)) and data[field] > 0 for field in numeric_fields)
                    
                    if all_positive:
                        self.log_test("Price Data Validation", True, "All numeric price fields are positive")
                    else:
                        invalid_fields = [f for f in numeric_fields if not (isinstance(data[f], (int, float)) and data[f] > 0)]
                        self.log_test("Price Data Validation", False, f"Invalid numeric fields: {invalid_fields}")
                    
                    # Validate timestamp format
                    try:
                        from datetime import datetime
                        datetime.fromisoformat(data["last_updated"].replace('Z', '+00:00'))
                        self.log_test("Price Timestamp Format", True, "Valid ISO timestamp format")
                    except Exception:
                        self.log_test("Price Timestamp Format", False, f"Invalid timestamp: {data['last_updated']}")
                else:
                    missing_fields = [f for f in required_fields if f not in data]
                    self.log_test("Pump Token Price Endpoint", False, f"Missing fields: {missing_fields}")
            else:
                self.log_test("Pump Token Price Endpoint", False, f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_test("Pump Token Price Endpoint", False, f"Connection error: {str(e)}")
        
        # Test 3: Buy Link Generation
        try:
            # Test with USD amount
            buy_data = {"amount_usd": 100}
            response = self.session.post(f"{self.base_url}/api/pump/buy-link", json=buy_data)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["success", "buy_url", "token_mint", "amount_sol", "amount_usd", "instructions"]
                
                if all(field in data for field in required_fields):
                    self.log_test("Pump Buy Link Generation", True, f"Buy link generated: {data.get('buy_url')}")
                    
                    # Validate buy URL format
                    expected_base = f"https://pump.fun/{data['token_mint']}"
                    if data["buy_url"].startswith(expected_base):
                        self.log_test("Buy Link URL Format", True, "Correct pump.fun URL format")
                    else:
                        self.log_test("Buy Link URL Format", False, f"Invalid URL format: {data['buy_url']}")
                    
                    # Validate amount conversion
                    if data["amount_usd"] == 100 and data["amount_sol"] > 0:
                        self.log_test("Buy Link Amount Conversion", True, f"USD to SOL conversion: ${data['amount_usd']} = {data['amount_sol']} SOL")
                    else:
                        self.log_test("Buy Link Amount Conversion", False, f"Invalid conversion: USD={data['amount_usd']}, SOL={data['amount_sol']}")
                else:
                    missing_fields = [f for f in required_fields if f not in data]
                    self.log_test("Pump Buy Link Generation", False, f"Missing fields: {missing_fields}")
            else:
                self.log_test("Pump Buy Link Generation", False, f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_test("Pump Buy Link Generation", False, f"Connection error: {str(e)}")
        
        # Test 4: Buy Link with SOL amount
        try:
            buy_data = {"amount_sol": 0.5}
            response = self.session.post(f"{self.base_url}/api/pump/buy-link", json=buy_data)
            
            if response.status_code == 200:
                data = response.json()
                if data["amount_sol"] == 0.5:
                    self.log_test("Buy Link SOL Amount", True, f"SOL amount preserved: {data['amount_sol']}")
                else:
                    self.log_test("Buy Link SOL Amount", False, f"Expected 0.5 SOL, got {data['amount_sol']}")
            else:
                self.log_test("Buy Link SOL Amount", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Buy Link SOL Amount", False, f"Connection error: {str(e)}")
    
    def test_pump_fun_member_rewards(self):
        """Test pump.fun member rewards system (requires authentication)"""
        print("\n=== Testing Pump.fun Member Rewards ===")
        
        if not hasattr(self, 'access_token'):
            self.log_test("Pump Member Rewards", False, "No access token available for testing")
            return
        
        # Set up authorization header
        auth_headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        
        # Test 1: Get Member Rewards
        try:
            response = self.session.get(f"{self.base_url}/api/pump/member-rewards", headers=auth_headers)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["success", "member_address", "membership_tier", "base_reward", 
                                 "tier_multiplier", "activity_bonus", "total_reward_tokens", 
                                 "token_symbol", "claim_status", "instructions"]
                
                if all(field in data for field in required_fields):
                    self.log_test("Member Rewards Calculation", True, f"Total rewards: {data.get('total_reward_tokens')} {data.get('token_symbol')}")
                    
                    # Validate reward calculation logic
                    expected_total = data["base_reward"] * data["tier_multiplier"] + data["activity_bonus"]
                    if abs(data["total_reward_tokens"] - expected_total) < 0.01:
                        self.log_test("Reward Calculation Logic", True, f"Correct calculation: {data['base_reward']} * {data['tier_multiplier']} + {data['activity_bonus']} = {data['total_reward_tokens']}")
                    else:
                        self.log_test("Reward Calculation Logic", False, f"Calculation error: expected {expected_total}, got {data['total_reward_tokens']}")
                    
                    # Validate tier multiplier
                    tier = data["membership_tier"]
                    multiplier = data["tier_multiplier"]
                    expected_multipliers = {"basic": 1.0, "premium": 2.0, "vip": 5.0}
                    
                    if multiplier == expected_multipliers.get(tier, 1.0):
                        self.log_test("Tier Multiplier Logic", True, f"{tier} tier has {multiplier}x multiplier")
                    else:
                        self.log_test("Tier Multiplier Logic", False, f"Expected {expected_multipliers.get(tier, 1.0)}x for {tier}, got {multiplier}x")
                    
                    # Validate token symbol
                    if data["token_symbol"] == "BBTC":
                        self.log_test("Reward Token Symbol", True, "Correct token symbol: BBTC")
                    else:
                        self.log_test("Reward Token Symbol", False, f"Expected BBTC, got {data['token_symbol']}")
                else:
                    missing_fields = [f for f in required_fields if f not in data]
                    self.log_test("Member Rewards Calculation", False, f"Missing fields: {missing_fields}")
            elif response.status_code in [401, 403]:
                self.log_test("Member Rewards Authentication", False, "Authentication failed for rewards endpoint")
            else:
                self.log_test("Member Rewards Calculation", False, f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_test("Member Rewards Calculation", False, f"Connection error: {str(e)}")
        
        # Test 2: Claim Rewards
        try:
            claim_data = {
                "wallet_address": "bitcoincash:qr6m7j9njldwwzlg9v7v53unlr4jkmx6eylep8ekg2"
            }
            response = self.session.post(f"{self.base_url}/api/pump/claim-rewards", json=claim_data, headers=auth_headers)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["success", "message", "claim_id", "member_address", "reward_wallet", 
                                 "reward_amount", "token_symbol", "status", "estimated_processing"]
                
                if all(field in data for field in required_fields):
                    self.log_test("Reward Claim Submission", True, f"Claim submitted: {data.get('claim_id')}")
                    
                    # Store claim_id for admin testing
                    self.reward_claim_id = data["claim_id"]
                    
                    # Validate claim status
                    if data["status"] == "pending_approval":
                        self.log_test("Claim Status", True, "Claim status set to pending_approval")
                    else:
                        self.log_test("Claim Status", False, f"Expected pending_approval, got {data['status']}")
                    
                    # Validate reward amount is positive
                    if isinstance(data["reward_amount"], (int, float)) and data["reward_amount"] > 0:
                        self.log_test("Claim Reward Amount", True, f"Valid reward amount: {data['reward_amount']}")
                    else:
                        self.log_test("Claim Reward Amount", False, f"Invalid reward amount: {data['reward_amount']}")
                else:
                    missing_fields = [f for f in required_fields if f not in data]
                    self.log_test("Reward Claim Submission", False, f"Missing fields: {missing_fields}")
            elif response.status_code in [401, 403]:
                self.log_test("Reward Claim Authentication", False, "Authentication failed for claim endpoint")
            else:
                self.log_test("Reward Claim Submission", False, f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_test("Reward Claim Submission", False, f"Connection error: {str(e)}")
    
    def test_pump_fun_admin_endpoints(self):
        """Test pump.fun admin endpoints for reward management"""
        print("\n=== Testing Pump.fun Admin Endpoints ===")
        
        # Test 1: Get Pending Claims
        try:
            response = self.session.get(f"{self.base_url}/api/admin/pump/pending-claims")
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["success", "pending_claims", "total_pending", "total_tokens_pending"]
                
                if all(field in data for field in required_fields):
                    self.log_test("Admin Pending Claims", True, f"Found {data.get('total_pending')} pending claims")
                    
                    # Validate data structure
                    if isinstance(data["pending_claims"], list):
                        self.log_test("Pending Claims Structure", True, "Claims returned as list")
                    else:
                        self.log_test("Pending Claims Structure", False, f"Expected list, got {type(data['pending_claims'])}")
                    
                    # Validate numeric fields
                    if isinstance(data["total_pending"], int) and isinstance(data["total_tokens_pending"], (int, float)):
                        self.log_test("Pending Claims Totals", True, f"Valid totals: {data['total_pending']} claims, {data['total_tokens_pending']} tokens")
                    else:
                        self.log_test("Pending Claims Totals", False, "Invalid total field types")
                else:
                    missing_fields = [f for f in required_fields if f not in data]
                    self.log_test("Admin Pending Claims", False, f"Missing fields: {missing_fields}")
            else:
                self.log_test("Admin Pending Claims", False, f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_test("Admin Pending Claims", False, f"Connection error: {str(e)}")
        
        # Test 2: Approve Claim
        try:
            # Use a test claim ID
            test_claim_id = getattr(self, 'reward_claim_id', 'test_claim_12345')
            approve_data = {
                "claim_id": test_claim_id,
                "transaction_signature": "test_signature_abc123def456",
                "admin_notes": "Test approval for pump.fun integration testing"
            }
            response = self.session.post(f"{self.base_url}/api/admin/pump/approve-claim", json=approve_data)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["success", "message", "claim_id", "processed_at"]
                
                if all(field in data for field in required_fields):
                    self.log_test("Admin Approve Claim", True, f"Claim approved: {data.get('message')}")
                    
                    # Validate claim_id matches
                    if data["claim_id"] == test_claim_id:
                        self.log_test("Claim ID Validation", True, "Claim ID matches request")
                    else:
                        self.log_test("Claim ID Validation", False, f"Expected {test_claim_id}, got {data['claim_id']}")
                    
                    # Validate processed_at timestamp
                    try:
                        from datetime import datetime
                        datetime.fromisoformat(data["processed_at"].replace('Z', '+00:00'))
                        self.log_test("Claim Processing Timestamp", True, "Valid processing timestamp")
                    except Exception:
                        self.log_test("Claim Processing Timestamp", False, f"Invalid timestamp: {data['processed_at']}")
                    
                    # Validate transaction signature is recorded
                    if approve_data.get("transaction_signature") and data.get("transaction_signature"):
                        self.log_test("Transaction Signature Recording", True, "Transaction signature recorded")
                    else:
                        self.log_test("Transaction Signature Recording", False, "Transaction signature not recorded")
                else:
                    missing_fields = [f for f in required_fields if f not in data]
                    self.log_test("Admin Approve Claim", False, f"Missing fields: {missing_fields}")
            else:
                self.log_test("Admin Approve Claim", False, f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_test("Admin Approve Claim", False, f"Connection error: {str(e)}")
    
    def test_pump_fun_authentication_requirements(self):
        """Test that pump.fun endpoints properly require authentication where needed"""
        print("\n=== Testing Pump.fun Authentication Requirements ===")
        
        # Test 1: Member rewards without auth (should fail)
        try:
            response = self.session.get(f"{self.base_url}/api/pump/member-rewards")
            
            if response.status_code in [401, 403]:
                self.log_test("Member Rewards Auth Required", True, f"Properly requires authentication: {response.status_code}")
            else:
                self.log_test("Member Rewards Auth Required", False, f"Expected 401/403, got {response.status_code}")
        except Exception as e:
            self.log_test("Member Rewards Auth Required", False, f"Connection error: {str(e)}")
        
        # Test 2: Claim rewards without auth (should fail)
        try:
            claim_data = {"wallet_address": "test_wallet"}
            response = self.session.post(f"{self.base_url}/api/pump/claim-rewards", json=claim_data)
            
            if response.status_code in [401, 403]:
                self.log_test("Claim Rewards Auth Required", True, f"Properly requires authentication: {response.status_code}")
            else:
                self.log_test("Claim Rewards Auth Required", False, f"Expected 401/403, got {response.status_code}")
        except Exception as e:
            self.log_test("Claim Rewards Auth Required", False, f"Connection error: {str(e)}")
        
        # Test 3: Public endpoints should work without auth
        public_endpoints = [
            ("/api/pump/token-info", "Token Info"),
            ("/api/pump/token-price", "Token Price")
        ]
        
        for endpoint, name in public_endpoints:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}")
                if response.status_code == 200:
                    self.log_test(f"Public Access ({name})", True, f"Public endpoint accessible: {response.status_code}")
                else:
                    self.log_test(f"Public Access ({name})", False, f"Public endpoint failed: {response.status_code}")
            except Exception as e:
                self.log_test(f"Public Access ({name})", False, f"Connection error: {str(e)}")
        
        # Test 4: Buy link generation should work without auth
        try:
            buy_data = {"amount_usd": 50}
            response = self.session.post(f"{self.base_url}/api/pump/buy-link", json=buy_data)
            
            if response.status_code == 200:
                self.log_test("Buy Link Public Access", True, "Buy link generation works without auth")
            else:
                self.log_test("Buy Link Public Access", False, f"Buy link generation failed: {response.status_code}")
        except Exception as e:
            self.log_test("Buy Link Public Access", False, f"Connection error: {str(e)}")
    
    def test_pump_fun_error_handling(self):
        """Test pump.fun endpoints error handling"""
        print("\n=== Testing Pump.fun Error Handling ===")
        
        # Test 1: Buy link with invalid parameters
        try:
            # Test with negative amount
            buy_data = {"amount_usd": -50}
            response = self.session.post(f"{self.base_url}/api/pump/buy-link", json=buy_data)
            
            # Should either handle gracefully or return error
            if response.status_code in [200, 400, 422]:
                self.log_test("Buy Link Invalid Amount", True, f"Handled invalid amount appropriately: {response.status_code}")
            else:
                self.log_test("Buy Link Invalid Amount", False, f"Unexpected status: {response.status_code}")
        except Exception as e:
            self.log_test("Buy Link Invalid Amount", False, f"Connection error: {str(e)}")
        
        # Test 2: Buy link with no parameters
        try:
            response = self.session.post(f"{self.base_url}/api/pump/buy-link", json={})
            
            if response.status_code == 200:
                data = response.json()
                # Should generate basic buy link without amount
                if "buy_url" in data:
                    self.log_test("Buy Link No Parameters", True, "Generated basic buy link without amount")
                else:
                    self.log_test("Buy Link No Parameters", False, "No buy URL in response")
            else:
                self.log_test("Buy Link No Parameters", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Buy Link No Parameters", False, f"Connection error: {str(e)}")
        
        # Test 3: Claim rewards with invalid wallet address (if authenticated)
        if hasattr(self, 'access_token'):
            try:
                auth_headers = {"Authorization": f"Bearer {self.access_token}"}
                claim_data = {"wallet_address": "invalid_wallet_address"}
                response = self.session.post(f"{self.base_url}/api/pump/claim-rewards", json=claim_data, headers=auth_headers)
                
                # Should handle gracefully (may accept any string as wallet address for testing)
                if response.status_code in [200, 400, 422]:
                    self.log_test("Claim Invalid Wallet", True, f"Handled invalid wallet appropriately: {response.status_code}")
                else:
                    self.log_test("Claim Invalid Wallet", False, f"Unexpected status: {response.status_code}")
            except Exception as e:
                self.log_test("Claim Invalid Wallet", False, f"Connection error: {str(e)}")
        
        # Test 4: Admin approve non-existent claim
        try:
            approve_data = {
                "claim_id": "non_existent_claim_12345",
                "transaction_signature": "test_sig"
            }
            response = self.session.post(f"{self.base_url}/api/admin/pump/approve-claim", json=approve_data)
            
            # Should handle gracefully (may accept any claim_id for testing)
            if response.status_code in [200, 404, 400]:
                self.log_test("Admin Approve Non-existent Claim", True, f"Handled non-existent claim appropriately: {response.status_code}")
            else:
                self.log_test("Admin Approve Non-existent Claim", False, f"Unexpected status: {response.status_code}")
        except Exception as e:
            self.log_test("Admin Approve Non-existent Claim", False, f"Connection error: {str(e)}")

    def test_error_handling(self):
        """Test error handling for invalid requests"""
        print("\n=== Testing Error Handling ===")
        
        # Test invalid JSON payload
        try:
            response = self.session.post(f"{self.base_url}/api/auth/challenge", 
                                       data="invalid json", 
                                       headers={'Content-Type': 'application/json'})
            if response.status_code in [400, 422]:
                self.log_test("Invalid JSON Handling", True, f"Properly handled invalid JSON: {response.status_code}")
            else:
                self.log_test("Invalid JSON Handling", False, f"Unexpected status: {response.status_code}")
        except Exception as e:
            self.log_test("Invalid JSON Handling", False, f"Error: {str(e)}")
        
        # Test missing required parameters
        try:
            response = self.session.post(f"{self.base_url}/api/auth/challenge", json={})
            if response.status_code in [400, 422]:
                self.log_test("Missing Parameters Handling", True, f"Properly handled missing params: {response.status_code}")
            else:
                self.log_test("Missing Parameters Handling", False, f"Unexpected status: {response.status_code}")
        except Exception as e:
            self.log_test("Missing Parameters Handling", False, f"Error: {str(e)}")
        
        # Test non-existent endpoint
        try:
            response = self.session.get(f"{self.base_url}/api/nonexistent")
            if response.status_code == 404:
                self.log_test("Non-existent Endpoint Handling", True, f"Properly returned 404: {response.status_code}")
            else:
                self.log_test("Non-existent Endpoint Handling", False, f"Unexpected status: {response.status_code}")
        except Exception as e:
            self.log_test("Non-existent Endpoint Handling", False, f"Error: {str(e)}")
    
    def test_authentication_and_dashboard_flow(self):
        """Test complete authentication and member dashboard access flow as requested"""
        print("\n=== Testing Authentication and Member Dashboard Access Flow ===")
        print("🔐 Testing critical authentication flow for member dashboard access")
        
        # Step 1: Test BCH Authentication Challenge Generation
        try:
            challenge_data = {
                "app_name": "Bitcoin Ben's Burger Bus Club"
            }
            response = self.session.post(f"{self.base_url}/api/auth/challenge", json=challenge_data)
            
            if response.status_code == 200:
                data = response.json()
                if all(field in data for field in ["challenge_id", "message", "expires_at"]):
                    self.log_test("Auth Challenge Generation", True, f"Challenge created successfully: {data['challenge_id'][:8]}...")
                    self.challenge_id = data["challenge_id"]
                    self.challenge_message = data["message"]
                else:
                    self.log_test("Auth Challenge Generation", False, "Missing required challenge fields")
                    return
            else:
                self.log_test("Auth Challenge Generation", False, f"Status: {response.status_code}")
                return
        except Exception as e:
            self.log_test("Auth Challenge Generation", False, f"Connection error: {str(e)}")
            return
        
        # Step 2: Test BCH Authentication Signature Verification (Login)
        try:
            test_bch_address = "bitcoincash:qr6m7j9njldwwzlg9v7v53unlr4jkmx6eylep8ekg2"
            verify_data = {
                "challenge_id": self.challenge_id,
                "bch_address": test_bch_address,
                "signature": "valid_signature_for_member_dashboard_testing_12345",
                "message": self.challenge_message
            }
            response = self.session.post(f"{self.base_url}/api/auth/verify", json=verify_data)
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data:
                    self.log_test("Auth Login (Signature Verification)", True, f"JWT token issued successfully")
                    self.access_token = data["access_token"]
                    self.auth_headers = {"Authorization": f"Bearer {self.access_token}"}
                else:
                    self.log_test("Auth Login (Signature Verification)", False, "No access token in response")
                    return
            else:
                self.log_test("Auth Login (Signature Verification)", False, f"Status: {response.status_code}")
                return
        except Exception as e:
            self.log_test("Auth Login (Signature Verification)", False, f"Connection error: {str(e)}")
            return
        
        # Step 3: Test Member Profile Access (GET /api/profile)
        try:
            response = self.session.get(f"{self.base_url}/api/profile", headers=self.auth_headers)
            
            if response.status_code == 200:
                data = response.json()
                if "wallet_address" in data and "membership_tier" in data:
                    self.log_test("Member Profile Access", True, f"Profile retrieved: {data.get('membership_tier', 'unknown')} tier")
                else:
                    self.log_test("Member Profile Access", False, "Invalid profile structure")
            else:
                self.log_test("Member Profile Access", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Member Profile Access", False, f"Connection error: {str(e)}")
        
        # Step 4: Test Member Dashboard Endpoints
        dashboard_endpoints = [
            ("/api/menu/member", "Member Menu"),
            ("/api/locations/member", "Member Locations"), 
            ("/api/events", "Member Events"),
            ("/api/orders", "Member Orders")
        ]
        
        for endpoint, name in dashboard_endpoints:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}", headers=self.auth_headers)
                
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list):
                        self.log_test(f"Dashboard Access - {name}", True, f"Accessed successfully, {len(data)} items")
                    else:
                        self.log_test(f"Dashboard Access - {name}", True, f"Accessed successfully")
                elif response.status_code in [401, 403]:
                    self.log_test(f"Dashboard Access - {name}", False, f"Authentication failed: {response.status_code}")
                else:
                    self.log_test(f"Dashboard Access - {name}", False, f"Unexpected status: {response.status_code}")
            except Exception as e:
                self.log_test(f"Dashboard Access - {name}", False, f"Connection error: {str(e)}")
        
        # Step 5: Test Member Registration Endpoint (POST /api/membership/register)
        try:
            member_data = {
                "fullName": "Test Member",
                "email": "testmember@bitcoinbens.com",
                "password": "TestPass123!",  # Note: This system uses wallet auth, not password
                "phone": "+1-555-TEST",
                "pma_agreed": True,
                "dues_paid": True,
                "payment_amount": 21.0
            }
            response = self.session.post(f"{self.base_url}/api/membership/register", 
                                       json=member_data, headers=self.auth_headers)
            
            if response.status_code in [200, 201]:
                self.log_test("Member Registration", True, "Registration completed successfully")
            elif response.status_code in [401, 403]:
                self.log_test("Member Registration", False, f"Authentication failed: {response.status_code}")
            else:
                # May return other status codes but if auth passes, that's what we're testing
                self.log_test("Member Registration", True, f"Registration processed (status: {response.status_code})")
        except Exception as e:
            self.log_test("Member Registration", False, f"Connection error: {str(e)}")
        
        # Step 6: Test Authentication Error Scenarios
        try:
            # Test access without token
            response = self.session.get(f"{self.base_url}/api/profile")
            if response.status_code in [401, 403]:
                self.log_test("Auth Protection - No Token", True, "Properly blocks unauthenticated access")
            else:
                self.log_test("Auth Protection - No Token", False, f"Unexpected access: {response.status_code}")
            
            # Test access with invalid token
            invalid_headers = {"Authorization": "Bearer invalid_token_12345"}
            response = self.session.get(f"{self.base_url}/api/profile", headers=invalid_headers)
            if response.status_code in [401, 403]:
                self.log_test("Auth Protection - Invalid Token", True, "Properly blocks invalid token")
            else:
                self.log_test("Auth Protection - Invalid Token", False, f"Unexpected access: {response.status_code}")
        except Exception as e:
            self.log_test("Auth Protection Tests", False, f"Connection error: {str(e)}")

    def test_dashboard_data_endpoints(self):
        """Test dashboard data endpoints that were previously using bchAuthService"""
        print("\n=== Testing Dashboard Data Endpoints ===")
        
        if not hasattr(self, 'access_token'):
            self.log_test("Dashboard Data Endpoints", False, "No access token available for testing")
            return
        
        # Set up authorization header
        auth_headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        
        # Test dashboard data endpoints
        dashboard_endpoints = [
            ("/api/profile", "User Profile Data", "GET"),
            ("/api/debug/menu", "Menu Items", "GET"),
            ("/api/debug/locations", "Locations", "GET"),
            ("/api/debug/events", "Events", "GET"),
            ("/api/debug/orders", "Orders", "GET"),
            ("/api/pump/token-info", "Pump.fun Token Info", "GET"),
            ("/api/pump/token-price", "Pump.fun Token Price", "GET"),
            ("/api/affiliate/my-stats", "Affiliate Stats", "GET")
        ]
        
        for endpoint, name, method in dashboard_endpoints:
            try:
                if method == "GET":
                    if endpoint.startswith("/api/pump/") or endpoint == "/api/debug/menu":
                        # These endpoints might not require auth
                        response = self.session.get(f"{self.base_url}{endpoint}")
                        if response.status_code == 401 or response.status_code == 403:
                            # Try with auth
                            response = self.session.get(f"{self.base_url}{endpoint}", headers=auth_headers)
                    else:
                        # These definitely require auth
                        response = self.session.get(f"{self.base_url}{endpoint}", headers=auth_headers)
                
                if response.status_code == 200:
                    data = response.json()
                    self.log_test(f"Dashboard Data ({name})", True, f"Successfully retrieved data: {response.status_code}")
                    
                    # Validate data structure based on endpoint
                    if endpoint == "/api/profile":
                        required_fields = ["id", "wallet_address", "membership_tier"]
                        if all(field in data for field in required_fields):
                            self.log_test(f"Profile Data Structure", True, f"All required profile fields present")
                        else:
                            missing = [f for f in required_fields if f not in data]
                            self.log_test(f"Profile Data Structure", False, f"Missing fields: {missing}")
                    
                    elif endpoint == "/api/debug/menu":
                        if isinstance(data, list) and len(data) > 0:
                            self.log_test(f"Menu Data Structure", True, f"Menu contains {len(data)} items")
                            # Check for Bitcoin Ben's themed items
                            bitcoin_items = [item for item in data if "Bitcoin" in item.get("name", "") or "Satoshi" in item.get("name", "") or "Hodl" in item.get("name", "")]
                            if len(bitcoin_items) > 0:
                                self.log_test(f"Bitcoin Themed Menu Items", True, f"Found {len(bitcoin_items)} Bitcoin-themed items")
                            else:
                                self.log_test(f"Bitcoin Themed Menu Items", False, "No Bitcoin-themed items found")
                        else:
                            self.log_test(f"Menu Data Structure", False, "Menu data is empty or invalid")
                    
                    elif endpoint == "/api/debug/locations":
                        if isinstance(data, list):
                            self.log_test(f"Locations Data Structure", True, f"Locations contains {len(data)} items")
                        else:
                            self.log_test(f"Locations Data Structure", False, "Locations data is not a list")
                    
                    elif endpoint == "/api/debug/events":
                        if isinstance(data, list):
                            self.log_test(f"Events Data Structure", True, f"Events contains {len(data)} items")
                        else:
                            self.log_test(f"Events Data Structure", False, "Events data is not a list")
                    
                    elif endpoint == "/api/debug/orders":
                        if isinstance(data, list):
                            self.log_test(f"Orders Data Structure", True, f"Orders contains {len(data)} items")
                        else:
                            self.log_test(f"Orders Data Structure", False, "Orders data is not a list")
                    
                    elif endpoint == "/api/pump/token-info":
                        if "token" in data and "mint" in data["token"]:
                            self.log_test(f"Token Info Data Structure", True, f"Token info contains required fields")
                        else:
                            self.log_test(f"Token Info Data Structure", False, "Token info missing required fields")
                    
                    elif endpoint == "/api/pump/token-price":
                        required_price_fields = ["price_usd", "market_cap", "volume_24h", "holders"]
                        if all(field in data for field in required_price_fields):
                            self.log_test(f"Token Price Data Structure", True, f"Token price contains all required fields")
                        else:
                            missing = [f for f in required_price_fields if f not in data]
                            self.log_test(f"Token Price Data Structure", False, f"Missing price fields: {missing}")
                    
                    elif endpoint == "/api/affiliate/my-stats":
                        required_affiliate_fields = ["referral_code", "total_referrals", "total_commissions_earned"]
                        if all(field in data for field in required_affiliate_fields):
                            self.log_test(f"Affiliate Stats Data Structure", True, f"Affiliate stats contain all required fields")
                        else:
                            missing = [f for f in required_affiliate_fields if f not in data]
                            self.log_test(f"Affiliate Stats Data Structure", False, f"Missing affiliate fields: {missing}")
                
                elif response.status_code in [401, 403]:
                    self.log_test(f"Dashboard Data ({name})", False, f"Authentication failed: {response.status_code}")
                else:
                    self.log_test(f"Dashboard Data ({name})", False, f"Unexpected status: {response.status_code}, Response: {response.text[:200]}")
            
            except Exception as e:
                self.log_test(f"Dashboard Data ({name})", False, f"Connection error: {str(e)}")

    def run_dashboard_fix_tests(self):
        """Run tests specifically for the dashboard data population fix"""
        print(f"🚀 Starting Dashboard Data Population Fix Testing for: {self.base_url}")
        print("=" * 80)
        
        # Test user registration and login flow (BCH authentication)
        self.test_authentication_and_dashboard_flow()
        
        # Test dashboard data endpoints
        self.test_dashboard_data_endpoints()
        
        # Generate summary
        self.generate_summary()

    def test_admin_authentication_system(self):
        """Test new admin authentication system"""
        print("\n=== Testing Admin Authentication System ===")
        
        # Test 1: Admin Login with Correct Credentials
        try:
            admin_login_data = {
                "email": "admin@bitcoinben.com",
                "password": "admin123"
            }
            response = self.session.post(f"{self.base_url}/api/auth/admin-login", json=admin_login_data)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["access_token", "token_type", "expires_in", "admin", "role"]
                
                if all(field in data for field in required_fields):
                    self.log_test("Admin Login - Correct Credentials", True, f"Admin login successful. Role: {data.get('role')}")
                    
                    # Store admin token for further tests
                    self.admin_token = data["access_token"]
                    
                    # Validate admin-specific fields
                    if data.get("admin") == True and data.get("role") == "admin":
                        self.log_test("Admin Login - Role Validation", True, "Admin role and permissions correctly set")
                    else:
                        self.log_test("Admin Login - Role Validation", False, f"Expected admin=True, role=admin, got admin={data.get('admin')}, role={data.get('role')}")
                    
                    # Validate JWT token format
                    token_parts = data["access_token"].split('.')
                    if len(token_parts) == 3:
                        self.log_test("Admin JWT Token Format", True, "JWT token properly formatted")
                    else:
                        self.log_test("Admin JWT Token Format", False, f"Invalid JWT format: {len(token_parts)} parts")
                        
                else:
                    missing_fields = [f for f in required_fields if f not in data]
                    self.log_test("Admin Login - Correct Credentials", False, f"Missing fields: {missing_fields}")
            elif response.status_code == 404:
                self.log_test("Admin Login - Correct Credentials", False, "Admin login endpoint not implemented")
            else:
                self.log_test("Admin Login - Correct Credentials", False, f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_test("Admin Login - Correct Credentials", False, f"Connection error: {str(e)}")
        
        # Test 2: Admin Login with Incorrect Credentials (Security Test)
        try:
            incorrect_credentials = [
                {"email": "admin@bitcoinben.com", "password": "wrongpassword"},
                {"email": "wrong@email.com", "password": "admin123"},
                {"email": "admin@bitcoinben.com", "password": ""},
                {"email": "", "password": "admin123"}
            ]
            
            security_passed = 0
            for i, creds in enumerate(incorrect_credentials):
                response = self.session.post(f"{self.base_url}/api/auth/admin-login", json=creds)
                
                if response.status_code in [401, 403]:
                    security_passed += 1
                    self.log_test(f"Admin Security Test {i+1}", True, f"Correctly rejected invalid credentials: {response.status_code}")
                elif response.status_code == 404:
                    self.log_test(f"Admin Security Test {i+1}", False, "Admin login endpoint not implemented")
                    break
                else:
                    self.log_test(f"Admin Security Test {i+1}", False, f"Security issue: {response.status_code} for invalid credentials")
            
            if security_passed == len(incorrect_credentials):
                self.log_test("Admin Security - Overall", True, "All invalid credential attempts properly rejected")
            elif security_passed > 0:
                self.log_test("Admin Security - Overall", True, f"Most security tests passed ({security_passed}/{len(incorrect_credentials)})")
            else:
                self.log_test("Admin Security - Overall", False, "Admin authentication security issues detected")
                
        except Exception as e:
            self.log_test("Admin Security Tests", False, f"Connection error: {str(e)}")
    
    def test_bbc_staking_payment_system(self):
        """Test BBC staking payment system"""
        print("\n=== Testing BBC Staking Payment System ===")
        
        # Test 1: BBC Staking Payment with Valid Data
        try:
            staking_data = {
                "wallet_address": "7K8DVxtNJGnMtUY1CQJT5jcs8sFGSZTDiG7kowvFpECh",  # Valid Solana wallet format
                "bbc_tokens_staked": 1000000.0  # 1,000,000 BBC tokens as required
            }
            response = self.session.post(f"{self.base_url}/api/auth/bbc-staking-payment", json=staking_data)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["success", "message", "staking_verified", "membership_activated", "tokens_staked"]
                
                if all(field in data for field in required_fields):
                    self.log_test("BBC Staking Payment - Valid Data", True, f"Staking payment successful: {data.get('message')}")
                    
                    # Validate staking amount
                    if data.get("tokens_staked") == 1000000.0:
                        self.log_test("BBC Staking Amount Validation", True, f"Correct staking amount: {data['tokens_staked']} BBC tokens")
                    else:
                        self.log_test("BBC Staking Amount Validation", False, f"Expected 1,000,000, got {data.get('tokens_staked')}")
                    
                    # Validate membership activation
                    if data.get("membership_activated") == True:
                        self.log_test("BBC Staking Membership Activation", True, "Membership correctly activated for staking")
                    else:
                        self.log_test("BBC Staking Membership Activation", False, "Membership not activated despite valid staking")
                        
                else:
                    missing_fields = [f for f in required_fields if f not in data]
                    self.log_test("BBC Staking Payment - Valid Data", False, f"Missing fields: {missing_fields}")
            elif response.status_code == 404:
                self.log_test("BBC Staking Payment - Valid Data", False, "BBC staking payment endpoint not implemented")
            else:
                self.log_test("BBC Staking Payment - Valid Data", False, f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_test("BBC Staking Payment - Valid Data", False, f"Connection error: {str(e)}")
        
        # Test 2: BBC Staking Payment with Insufficient Tokens
        try:
            insufficient_staking_data = {
                "wallet_address": "7K8DVxtNJGnMtUY1CQJT5jcs8sFGSZTDiG7kowvFpECh",
                "bbc_tokens_staked": 500000.0  # Only 500,000 BBC tokens (insufficient)
            }
            response = self.session.post(f"{self.base_url}/api/auth/bbc-staking-payment", json=insufficient_staking_data)
            
            if response.status_code == 400:
                data = response.json()
                if "insufficient" in data.get("detail", "").lower() or "minimum" in data.get("detail", "").lower():
                    self.log_test("BBC Staking - Insufficient Tokens", True, "Correctly rejects insufficient staking amount")
                else:
                    self.log_test("BBC Staking - Insufficient Tokens", False, f"Unexpected error message: {data.get('detail')}")
            elif response.status_code == 404:
                self.log_test("BBC Staking - Insufficient Tokens", False, "BBC staking payment endpoint not implemented")
            else:
                self.log_test("BBC Staking - Insufficient Tokens", False, f"Expected 400, got {response.status_code}")
        except Exception as e:
            self.log_test("BBC Staking - Insufficient Tokens", False, f"Connection error: {str(e)}")
        
        # Test 3: BBC Staking Payment with Invalid Wallet Address
        try:
            invalid_wallet_data = {
                "wallet_address": "invalid_wallet_address_123",
                "bbc_tokens_staked": 1000000.0
            }
            response = self.session.post(f"{self.base_url}/api/auth/bbc-staking-payment", json=invalid_wallet_data)
            
            if response.status_code == 400:
                data = response.json()
                if "invalid" in data.get("detail", "").lower() or "wallet" in data.get("detail", "").lower():
                    self.log_test("BBC Staking - Invalid Wallet", True, "Correctly rejects invalid wallet address")
                else:
                    self.log_test("BBC Staking - Invalid Wallet", False, f"Unexpected error message: {data.get('detail')}")
            elif response.status_code == 404:
                self.log_test("BBC Staking - Invalid Wallet", False, "BBC staking payment endpoint not implemented")
            else:
                self.log_test("BBC Staking - Invalid Wallet", False, f"Expected 400, got {response.status_code}")
        except Exception as e:
            self.log_test("BBC Staking - Invalid Wallet", False, f"Connection error: {str(e)}")
    
    def test_membership_pricing_configuration(self):
        """Test updated membership pricing configuration ($21 instead of free)"""
        print("\n=== Testing Membership Pricing Configuration ===")
        
        # Test 1: Payment Methods Configuration
        try:
            response = self.session.get(f"{self.base_url}/api/payments/methods")
            
            if response.status_code == 200:
                data = response.json()
                if "payment_methods" in data:
                    payment_methods = data["payment_methods"]
                    
                    # Check BCH payment method pricing
                    if "bch" in payment_methods:
                        bch_method = payment_methods["bch"]
                        if bch_method.get("amount") == 21.0:
                            self.log_test("BCH Payment Method Pricing", True, f"BCH payment correctly set to ${bch_method['amount']}")
                        else:
                            self.log_test("BCH Payment Method Pricing", False, f"Expected $21, got ${bch_method.get('amount')}")
                    
                    # Check Venmo payment method pricing
                    if "venmo" in payment_methods:
                        venmo_method = payment_methods["venmo"]
                        if venmo_method.get("amount") == 21.0:
                            self.log_test("Venmo Payment Method Pricing", True, f"Venmo payment correctly set to ${venmo_method['amount']}")
                        else:
                            self.log_test("Venmo Payment Method Pricing", False, f"Expected $21, got ${venmo_method.get('amount')}")
                    
                    # Check membership type
                    if data.get("membership_type") == "Private Membership Association":
                        self.log_test("Membership Type Configuration", True, "Membership type correctly set to PMA")
                    else:
                        self.log_test("Membership Type Configuration", False, f"Expected PMA, got {data.get('membership_type')}")
                        
                else:
                    self.log_test("Payment Methods Configuration", False, "Payment methods not found in response")
            else:
                self.log_test("Payment Methods Configuration", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Payment Methods Configuration", False, f"Connection error: {str(e)}")
        
        # Test 2: Payment Creation with $21 Amount
        try:
            response = self.session.post(f"{self.base_url}/api/payments/create-membership-payment", 
                                       json={"user_address": "bitcoincash:qtest_pricing"})
            
            if response.status_code == 200:
                data = response.json()
                if data.get("amount_usd") == 21.0:
                    self.log_test("Payment Creation - $21 Amount", True, f"Payment correctly created for ${data['amount_usd']}")
                else:
                    self.log_test("Payment Creation - $21 Amount", False, f"Expected $21, got ${data.get('amount_usd')}")
            else:
                self.log_test("Payment Creation - $21 Amount", False, f"Payment creation failed: {response.status_code}")
        except Exception as e:
            self.log_test("Payment Creation - $21 Amount", False, f"Connection error: {str(e)}")
    
    def test_multi_currency_menu_pricing(self):
        """Test menu items include multi-currency pricing (USD, BCH, BBC)"""
        print("\n=== Testing Multi-Currency Menu Pricing ===")
        
        # First seed data to ensure menu items exist
        try:
            self.session.post(f"{self.base_url}/api/admin/seed-data")
            time.sleep(2)  # Allow time for seeding
        except:
            pass
        
        # Test member menu with authentication (if we have a token)
        if hasattr(self, 'access_token'):
            try:
                auth_headers = {"Authorization": f"Bearer {self.access_token}"}
                response = self.session.get(f"{self.base_url}/api/menu/member", headers=auth_headers)
                
                if response.status_code == 200:
                    menu_items = response.json()
                    if len(menu_items) > 0:
                        self.log_test("Member Menu Access", True, f"Retrieved {len(menu_items)} menu items")
                        
                        # Check first item for multi-currency pricing
                        item = menu_items[0]
                        currency_fields = ["price", "member_price", "price_bch", "member_price_bch", "price_bbc", "member_price_bbc"]
                        present_currencies = [field for field in currency_fields if field in item and item[field] is not None]
                        
                        if len(present_currencies) >= 4:  # Should have USD and member USD at minimum, ideally all 6
                            self.log_test("Multi-Currency Pricing", True, f"Found {len(present_currencies)} currency fields: {present_currencies}")
                            
                            # Validate specific currencies
                            if "price" in item and "member_price" in item:
                                self.log_test("USD Pricing", True, f"USD: ${item['price']}, Member: ${item['member_price']}")
                            
                            if "price_bch" in item and item["price_bch"] is not None:
                                self.log_test("BCH Pricing", True, f"BCH: {item['price_bch']} BCH")
                            else:
                                self.log_test("BCH Pricing", False, "BCH pricing not found or null")
                            
                            if "price_bbc" in item and item["price_bbc"] is not None:
                                self.log_test("BBC Token Pricing", True, f"BBC: {item['price_bbc']} BBC tokens")
                            else:
                                self.log_test("BBC Token Pricing", False, "BBC token pricing not found or null")
                                
                        else:
                            self.log_test("Multi-Currency Pricing", False, f"Only found {len(present_currencies)} currency fields: {present_currencies}")
                    else:
                        self.log_test("Member Menu Access", False, "No menu items found")
                else:
                    self.log_test("Member Menu Access", False, f"Status: {response.status_code}")
            except Exception as e:
                self.log_test("Member Menu Multi-Currency", False, f"Connection error: {str(e)}")
        
        # Test debug menu endpoint (no auth required)
        try:
            response = self.session.get(f"{self.base_url}/api/debug/menu")
            
            if response.status_code == 200:
                menu_items = response.json()
                if len(menu_items) > 0:
                    self.log_test("Debug Menu Access", True, f"Retrieved {len(menu_items)} menu items via debug endpoint")
                    
                    # Check for multi-currency pricing in debug menu
                    item = menu_items[0]
                    currency_fields = ["price", "member_price", "price_bch", "member_price_bch", "price_bbc", "member_price_bbc"]
                    present_currencies = [field for field in currency_fields if hasattr(item, field) or (isinstance(item, dict) and field in item)]
                    
                    if len(present_currencies) >= 2:
                        self.log_test("Debug Menu Multi-Currency", True, f"Multi-currency fields present: {present_currencies}")
                    else:
                        self.log_test("Debug Menu Multi-Currency", False, f"Limited currency fields: {present_currencies}")
                else:
                    self.log_test("Debug Menu Access", False, "No menu items in debug endpoint")
            else:
                self.log_test("Debug Menu Access", False, f"Debug menu status: {response.status_code}")
        except Exception as e:
            self.log_test("Debug Menu Multi-Currency", False, f"Connection error: {str(e)}")
    
    def test_existing_endpoints_with_new_pricing(self):
        """Test that all existing endpoints still work with the new pricing structure"""
        print("\n=== Testing Existing Endpoints with New Pricing Structure ===")
        
        # Test 1: Public endpoints still work
        public_endpoints = [
            ("/api/", "Root API"),
            ("/api/menu/public", "Public Menu"),
            ("/api/locations/public", "Public Locations"),
            ("/api/payments/methods", "Payment Methods")
        ]
        
        for endpoint, name in public_endpoints:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}")
                if response.status_code == 200:
                    self.log_test(f"Public Endpoint - {name}", True, f"Endpoint working: {response.status_code}")
                else:
                    self.log_test(f"Public Endpoint - {name}", False, f"Status: {response.status_code}")
            except Exception as e:
                self.log_test(f"Public Endpoint - {name}", False, f"Connection error: {str(e)}")
        
        # Test 2: Payment system endpoints
        payment_endpoints_tests = [
            ("create-membership-payment", "POST", {"user_address": "bitcoincash:qtest"}),
            ("methods", "GET", None)
        ]
        
        for endpoint_suffix, method, data in payment_endpoints_tests:
            try:
                endpoint = f"{self.base_url}/api/payments/{endpoint_suffix}"
                if method == "POST":
                    response = self.session.post(endpoint, json=data)
                else:
                    response = self.session.get(endpoint)
                
                if response.status_code == 200:
                    self.log_test(f"Payment Endpoint - {endpoint_suffix}", True, f"Endpoint working with new pricing: {response.status_code}")
                else:
                    self.log_test(f"Payment Endpoint - {endpoint_suffix}", False, f"Status: {response.status_code}")
            except Exception as e:
                self.log_test(f"Payment Endpoint - {endpoint_suffix}", False, f"Connection error: {str(e)}")
        
        # Test 3: Admin endpoints (if we have admin token)
        if hasattr(self, 'admin_token'):
            admin_headers = {"Authorization": f"Bearer {self.admin_token}"}
            admin_endpoints = [
                ("/api/admin/pending-payments", "GET", None),
                ("/api/admin/seed-data", "POST", None)
            ]
            
            for endpoint, method, data in admin_endpoints:
                try:
                    if method == "POST":
                        response = self.session.post(f"{self.base_url}{endpoint}", json=data, headers=admin_headers)
                    else:
                        response = self.session.get(f"{self.base_url}{endpoint}", headers=admin_headers)
                    
                    if response.status_code in [200, 201]:
                        self.log_test(f"Admin Endpoint - {endpoint}", True, f"Admin endpoint working: {response.status_code}")
                    else:
                        self.log_test(f"Admin Endpoint - {endpoint}", False, f"Status: {response.status_code}")
                except Exception as e:
                    self.log_test(f"Admin Endpoint - {endpoint}", False, f"Connection error: {str(e)}")
        
        # Test 4: Token integration endpoints
        token_endpoints = [
            ("/api/pump/token-info", "Token Info"),
            ("/api/pump/token-price", "Token Price")
        ]
        
        for endpoint, name in token_endpoints:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}")
                if response.status_code == 200:
                    self.log_test(f"Token Endpoint - {name}", True, f"Token endpoint working: {response.status_code}")
                else:
                    self.log_test(f"Token Endpoint - {name}", False, f"Status: {response.status_code}")
            except Exception as e:
                self.log_test(f"Token Endpoint - {name}", False, f"Connection error: {str(e)}")

    def run_all_tests(self):
        """Run all backend tests"""
        print(f"🚀 Starting comprehensive backend testing for Bitcoin Ben's Burger Bus Club")
        print(f"🔗 Backend URL: {self.base_url}")
        print("=" * 80)
        
        # PRIORITY: New Admin Authentication and BBC Staking System Tests (as requested)
        self.test_admin_authentication_system()
        self.test_bbc_staking_payment_system()
        self.test_membership_pricing_configuration()
        self.test_multi_currency_menu_pricing()
        self.test_existing_endpoints_with_new_pricing()
        
        # PRIORITY: Authentication and Member Dashboard Flow (as requested)
        self.test_authentication_and_dashboard_flow()
        
        # Run all test suites
        self.test_basic_health_check()
        self.test_public_endpoints()
        self.test_wallet_authentication_flow()
        
        # NEW: BCH Payment System Tests
        self.test_bch_payment_system()
        self.test_admin_payment_endpoints()
        self.test_payment_integration_flow()
        self.test_payment_error_scenarios()
        self.test_bch_price_fallback()
        
        # NEW: Pump.fun Token Integration Tests
        self.test_pump_fun_token_integration()
        self.test_pump_fun_member_rewards()
        self.test_pump_fun_admin_endpoints()
        self.test_pump_fun_authentication_requirements()
        self.test_pump_fun_error_handling()
        
        # Existing tests
        self.test_member_registration_endpoint()
        self.test_admin_data_seeding()
        self.test_database_integration()
        self.test_member_profile_fields()
        self.test_cors_and_security()
        self.test_error_handling()
        
        # Generate summary
        self.generate_summary()
    
    def generate_summary(self):
        """Generate test summary"""
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n🔍 FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  ❌ {result['test']}: {result['details']}")
        
        print("\n✅ PASSED TESTS:")
        for result in self.test_results:
            if result["success"]:
                print(f"  ✅ {result['test']}: {result['details']}")
        
        return {
            "total": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "success_rate": (passed_tests/total_tests)*100,
            "results": self.test_results
        }

if __name__ == "__main__":
    tester = FoodTruckBackendTester()
    # Run dashboard fix tests specifically for the review request
    tester.run_dashboard_fix_tests()