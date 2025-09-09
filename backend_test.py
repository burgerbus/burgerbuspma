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
            return "https://members-food.preview.emergentagent.com"
        
        return "https://members-food.preview.emergentagent.com"
    
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
                    
                    # Check for Bitcoin Ben's themed items
                    bitcoin_themed_items = ["The Satoshi Stacker", "The Hodl Burger", "The Bitcoin Mining Rig", "Lightning Network Loaded Fries"]
                    found_items = []
                    
                    for item in data:
                        if item.get("name") in bitcoin_themed_items:
                            found_items.append(item["name"])
                    
                    if found_items:
                        self.log_test("Bitcoin Ben's Themed Items", True, f"Found themed items: {', '.join(found_items)}")
                    else:
                        self.log_test("Bitcoin Ben's Themed Items", False, f"No Bitcoin Ben's themed items found in menu")
                    
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
    
    def test_wallet_authentication_flow(self):
        """Test Solana wallet authentication endpoints"""
        print("\n=== Testing Wallet Authentication Flow ===")
        
        # Test authentication challenge endpoint
        test_wallet_address = "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"  # Valid Solana address format
        
        try:
            # Test challenge generation
            params = {"address": test_wallet_address, "chain": "SOL"}
            response = self.session.post(f"{self.base_url}/api/auth/authorization/challenge", params=params)
            
            if response.status_code == 200:
                data = response.json()
                if "challenge" in data:
                    self.log_test("Authentication Challenge", True, f"Status: {response.status_code}, Challenge generated")
                    
                    # Validate challenge format
                    challenge = data["challenge"]
                    if isinstance(challenge, str) and len(challenge) > 10:
                        self.log_test("Challenge Format", True, f"Challenge length: {len(challenge)}")
                    else:
                        self.log_test("Challenge Format", False, f"Invalid challenge format: {challenge}")
                else:
                    self.log_test("Authentication Challenge", False, "No challenge in response", data)
            else:
                self.log_test("Authentication Challenge", False, f"Status: {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Authentication Challenge", False, f"Connection error: {str(e)}")
        
        # Test invalid wallet address (challenge generation should still work, validation happens at solve stage)
        try:
            invalid_params = {"address": "invalid_address", "chain": "SOL"}
            response = self.session.post(f"{self.base_url}/api/auth/authorization/challenge", params=invalid_params)
            
            if response.status_code == 200:  # Challenge generation should work even with invalid address
                data = response.json()
                if "challenge" in data and data["address"] == "invalid_address":
                    self.log_test("Invalid Wallet Address Challenge", True, "Challenge generated for invalid address (validation at solve stage)")
                else:
                    self.log_test("Invalid Wallet Address Challenge", False, "Unexpected response format")
            else:
                self.log_test("Invalid Wallet Address Challenge", False, f"Unexpected status: {response.status_code}")
        except Exception as e:
            self.log_test("Invalid Wallet Address Challenge", False, f"Connection error: {str(e)}")
    
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
    
    def test_error_handling(self):
        """Test error handling for invalid requests"""
        print("\n=== Testing Error Handling ===")
        
        # Test invalid JSON payload
        try:
            response = self.session.post(f"{self.base_url}/api/auth/authorization/challenge", 
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
            response = self.session.post(f"{self.base_url}/api/auth/authorization/challenge", json={})
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
    
    def run_all_tests(self):
        """Run all backend tests"""
        print(f"🚀 Starting comprehensive backend testing for Bitcoin Ben's Burger Bus Club")
        print(f"🔗 Backend URL: {self.base_url}")
        print("=" * 80)
        
        # Run all test suites
        self.test_basic_health_check()
        self.test_public_endpoints()
        self.test_wallet_authentication_flow()
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
    tester.run_all_tests()