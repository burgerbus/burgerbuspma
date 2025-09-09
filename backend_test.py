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
        
        # Test root endpoint
        try:
            response = self.session.get(f"{self.base_url}/api/")
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "TruckMembers" in data["message"]:
                    self.log_test("Root API Endpoint", True, f"Status: {response.status_code}, Message: {data['message']}")
                else:
                    self.log_test("Root API Endpoint", False, f"Unexpected response format", data)
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
        
        # Test public menu endpoint
        try:
            response = self.session.get(f"{self.base_url}/api/menu/public")
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_test("Public Menu Endpoint", True, f"Status: {response.status_code}, Items: {len(data)}")
                    if len(data) > 0:
                        # Validate menu item structure
                        item = data[0]
                        required_fields = ['id', 'name', 'description', 'price', 'member_price', 'category']
                        if all(field in item for field in required_fields):
                            self.log_test("Menu Item Structure", True, "All required fields present")
                        else:
                            missing = [f for f in required_fields if f not in item]
                            self.log_test("Menu Item Structure", False, f"Missing fields: {missing}")
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
            challenge_payload = {"address": test_wallet_address}
            response = self.session.post(f"{self.base_url}/auth/authentication/challenge", json=challenge_payload)
            
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
        
        # Test invalid wallet address
        try:
            invalid_payload = {"address": "invalid_address"}
            response = self.session.post(f"{self.base_url}/auth/authentication/challenge", json=invalid_payload)
            
            if response.status_code in [400, 422]:  # Expected error for invalid address
                self.log_test("Invalid Wallet Address Handling", True, f"Properly rejected invalid address: {response.status_code}")
            else:
                self.log_test("Invalid Wallet Address Handling", False, f"Unexpected status: {response.status_code}")
        except Exception as e:
            self.log_test("Invalid Wallet Address Handling", False, f"Connection error: {str(e)}")
    
    def test_admin_data_seeding(self):
        """Test admin data seeding endpoint"""
        print("\n=== Testing Admin Data Seeding ===")
        
        try:
            response = self.session.post(f"{self.base_url}/api/admin/seed-data")
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "seeded" in data["message"].lower():
                    self.log_test("Admin Data Seeding", True, f"Status: {response.status_code}, Message: {data['message']}")
                    
                    # Verify data was actually seeded by checking public endpoints
                    time.sleep(1)  # Give database time to update
                    
                    # Check if menu items were seeded
                    menu_response = self.session.get(f"{self.base_url}/api/menu/public")
                    if menu_response.status_code == 200:
                        menu_data = menu_response.json()
                        if len(menu_data) > 0:
                            self.log_test("Menu Data Persistence", True, f"Found {len(menu_data)} menu items after seeding")
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
                        
                        # Verify data structure integrity
                        sample_item = menu_data[0]
                        if all(key in sample_item for key in ['id', 'name', 'price', 'member_price']):
                            self.log_test("Database Data Integrity", True, "Menu item structure maintained")
                        else:
                            self.log_test("Database Data Integrity", False, "Menu item structure corrupted")
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
    
    def test_cors_and_security(self):
        """Test CORS headers and security measures"""
        print("\n=== Testing CORS and Security ===")
        
        # Test CORS headers
        try:
            response = self.session.get(f"{self.base_url}/api/")
            headers = response.headers
            
            cors_headers = [
                'access-control-allow-origin',
                'access-control-allow-methods',
                'access-control-allow-headers'
            ]
            
            cors_present = any(header in headers for header in cors_headers)
            if cors_present:
                self.log_test("CORS Headers", True, "CORS headers present in response")
            else:
                self.log_test("CORS Headers", False, "No CORS headers found")
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
            response = self.session.post(f"{self.base_url}/auth/authentication/challenge", 
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
            response = self.session.post(f"{self.base_url}/auth/authentication/challenge", json={})
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
        print(f"🚀 Starting comprehensive backend testing for Food Truck Membership Site")
        print(f"🔗 Backend URL: {self.base_url}")
        print("=" * 80)
        
        # Run all test suites
        self.test_basic_health_check()
        self.test_public_endpoints()
        self.test_wallet_authentication_flow()
        self.test_admin_data_seeding()
        self.test_database_integration()
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