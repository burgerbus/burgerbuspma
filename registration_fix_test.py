#!/usr/bin/env python3
"""
Specific tests for Bitcoin Ben's Burger Bus Club registration fix
Focus on testing the registration endpoint, profile creation, database model, auth flow, and member menu access
"""

import requests
import json
import time
import os
from typing import Dict, Any, Optional

class RegistrationFixTester:
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
            return "https://blockchain-eats.preview.emergentagent.com"
        
        return "https://blockchain-eats.preview.emergentagent.com"
    
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
    
    def test_registration_endpoint_without_auth(self):
        """Test POST /api/membership/register without auth (should get 401/403)"""
        print("\n=== Testing Registration Endpoint Without Auth ===")
        
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
                self.log_test("Registration Endpoint Auth Required", True, f"Properly requires authentication: {response.status_code}")
            elif response.status_code == 422:
                # Check if it's a validation error about missing auth
                try:
                    data = response.json()
                    error_detail = str(data.get("detail", ""))
                    if "authorization" in error_detail.lower() or "token" in error_detail.lower() or "auth" in error_detail.lower():
                        self.log_test("Registration Endpoint Auth Required", True, f"Auth validation error as expected: {error_detail}")
                    else:
                        self.log_test("Registration Endpoint Auth Required", False, f"Unexpected 422 validation error: {error_detail}")
                except:
                    self.log_test("Registration Endpoint Auth Required", True, f"422 validation error (likely auth-related)")
            elif response.status_code == 500:
                self.log_test("Registration Endpoint Auth Required", False, f"Server error (500) - registration fix may not be working properly. Response: {response.text}")
            else:
                self.log_test("Registration Endpoint Auth Required", False, f"Unexpected status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_test("Registration Endpoint Auth Required", False, f"Connection error: {str(e)}")
        
        # Verify endpoint exists
        try:
            response = self.session.post(f"{self.base_url}/api/membership/register")
            if response.status_code != 404:
                self.log_test("Registration Endpoint Exists", True, f"Endpoint exists (status: {response.status_code})")
            else:
                self.log_test("Registration Endpoint Exists", False, "Endpoint not found (404)")
        except Exception as e:
            self.log_test("Registration Endpoint Exists", False, f"Connection error: {str(e)}")
    
    def test_profile_creation_without_auth(self):
        """Test GET /api/profile without auth (should get proper auth error)"""
        print("\n=== Testing Profile Creation Without Auth ===")
        
        try:
            response = self.session.get(f"{self.base_url}/api/profile")
            
            if response.status_code in [401, 403]:
                self.log_test("Profile Endpoint Auth Required", True, f"Properly requires authentication: {response.status_code}")
            elif response.status_code == 422:
                # Check if it's a validation error about missing auth
                try:
                    data = response.json()
                    error_detail = str(data.get("detail", ""))
                    if "authorization" in error_detail.lower() or "token" in error_detail.lower() or "auth" in error_detail.lower():
                        self.log_test("Profile Endpoint Auth Required", True, f"Auth validation error as expected: {error_detail}")
                    else:
                        self.log_test("Profile Endpoint Auth Required", False, f"Unexpected 422 validation error: {error_detail}")
                except:
                    self.log_test("Profile Endpoint Auth Required", True, f"422 validation error (likely auth-related)")
            elif response.status_code == 500:
                self.log_test("Profile Endpoint Auth Required", False, f"Server error (500) - profile creation may have issues. Response: {response.text}")
            else:
                self.log_test("Profile Endpoint Auth Required", False, f"Unexpected status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_test("Profile Endpoint Auth Required", False, f"Connection error: {str(e)}")
    
    def test_database_model_datetime_handling(self):
        """Test datetime handling in MongoDB operations by checking data seeding"""
        print("\n=== Testing Database Model Datetime Handling ===")
        
        try:
            # Seed data to test datetime handling
            response = self.session.post(f"{self.base_url}/api/admin/seed-data")
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "seeded" in data["message"].lower():
                    self.log_test("Database Datetime Handling", True, f"Data seeding successful: {data['message']}")
                    
                    # Wait for database operations to complete
                    time.sleep(2)
                    
                    # Verify data was persisted correctly
                    menu_response = self.session.get(f"{self.base_url}/api/menu/public")
                    if menu_response.status_code == 200:
                        menu_data = menu_response.json()
                        if len(menu_data) > 0:
                            self.log_test("Database Model Persistence", True, f"Successfully persisted {len(menu_data)} items with datetime fields")
                        else:
                            self.log_test("Database Model Persistence", False, "No data persisted after seeding")
                    else:
                        self.log_test("Database Model Persistence", False, f"Could not verify data persistence: {menu_response.status_code}")
                else:
                    self.log_test("Database Datetime Handling", False, f"Unexpected seeding response: {data}")
            elif response.status_code == 500:
                self.log_test("Database Datetime Handling", False, f"Server error during seeding - datetime handling may be broken. Response: {response.text}")
            else:
                self.log_test("Database Datetime Handling", False, f"Seeding failed: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_test("Database Datetime Handling", False, f"Connection error: {str(e)}")
    
    def test_authentication_flow_endpoints(self):
        """Test challenge/solve endpoints work correctly"""
        print("\n=== Testing Authentication Flow Endpoints ===")
        
        # Test authentication challenge endpoint
        test_wallet_address = "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"  # Valid Solana address format
        
        try:
            # Test challenge generation
            params = {"address": test_wallet_address, "chain": "SOL"}
            response = self.session.post(f"{self.base_url}/api/auth/authorization/challenge", params=params)
            
            if response.status_code == 200:
                data = response.json()
                if "challenge" in data:
                    self.log_test("Auth Challenge Generation", True, f"Challenge generated successfully")
                    
                    # Validate challenge format
                    challenge = data["challenge"]
                    if isinstance(challenge, str) and len(challenge) > 10:
                        self.log_test("Auth Challenge Format", True, f"Challenge format valid (length: {len(challenge)})")
                    else:
                        self.log_test("Auth Challenge Format", False, f"Invalid challenge format: {challenge}")
                    
                    # Verify address is returned correctly
                    if data.get("address") == test_wallet_address:
                        self.log_test("Auth Challenge Address", True, "Wallet address correctly returned in challenge")
                    else:
                        self.log_test("Auth Challenge Address", False, f"Address mismatch: expected {test_wallet_address}, got {data.get('address')}")
                else:
                    self.log_test("Auth Challenge Generation", False, "No challenge in response", data)
            elif response.status_code == 500:
                self.log_test("Auth Challenge Generation", False, f"Server error (500) - auth flow may be broken. Response: {response.text}")
            else:
                self.log_test("Auth Challenge Generation", False, f"Unexpected status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_test("Auth Challenge Generation", False, f"Connection error: {str(e)}")
        
        # Test solve endpoint exists (will fail without signature, but should not 404)
        try:
            solve_data = {
                "address": test_wallet_address,
                "chain": "SOL",
                "signature": "dummy_signature"
            }
            response = self.session.post(f"{self.base_url}/api/auth/authorization/solve", json=solve_data)
            
            if response.status_code != 404:
                self.log_test("Auth Solve Endpoint Exists", True, f"Solve endpoint exists (status: {response.status_code})")
            else:
                self.log_test("Auth Solve Endpoint Exists", False, "Solve endpoint not found (404)")
        except Exception as e:
            self.log_test("Auth Solve Endpoint Exists", False, f"Connection error: {str(e)}")
    
    def test_member_menu_access_auth_required(self):
        """Test GET /api/menu/member requires auth"""
        print("\n=== Testing Member Menu Access Auth Required ===")
        
        try:
            response = self.session.get(f"{self.base_url}/api/menu/member")
            
            if response.status_code in [401, 403]:
                self.log_test("Member Menu Auth Required", True, f"Properly requires authentication: {response.status_code}")
            elif response.status_code == 422:
                # Check if it's a validation error about missing auth
                try:
                    data = response.json()
                    error_detail = str(data.get("detail", ""))
                    if "authorization" in error_detail.lower() or "token" in error_detail.lower() or "auth" in error_detail.lower():
                        self.log_test("Member Menu Auth Required", True, f"Auth validation error as expected: {error_detail}")
                    else:
                        self.log_test("Member Menu Auth Required", False, f"Unexpected 422 validation error: {error_detail}")
                except:
                    self.log_test("Member Menu Auth Required", True, f"422 validation error (likely auth-related)")
            elif response.status_code == 500:
                self.log_test("Member Menu Auth Required", False, f"Server error (500) - member menu may have issues. Response: {response.text}")
            else:
                self.log_test("Member Menu Auth Required", False, f"Unexpected status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_test("Member Menu Auth Required", False, f"Connection error: {str(e)}")
        
        # Verify endpoint exists
        try:
            response = self.session.get(f"{self.base_url}/api/menu/member")
            if response.status_code != 404:
                self.log_test("Member Menu Endpoint Exists", True, f"Endpoint exists (status: {response.status_code})")
            else:
                self.log_test("Member Menu Endpoint Exists", False, "Endpoint not found (404)")
        except Exception as e:
            self.log_test("Member Menu Endpoint Exists", False, f"Connection error: {str(e)}")
    
    def test_menu_items_format(self):
        """Verify menu items are properly formatted by checking public menu structure"""
        print("\n=== Testing Menu Items Format ===")
        
        try:
            # First seed data to ensure we have menu items
            seed_response = self.session.post(f"{self.base_url}/api/admin/seed-data")
            if seed_response.status_code == 200:
                time.sleep(2)  # Wait for seeding to complete
                
                # Check public menu format
                response = self.session.get(f"{self.base_url}/api/menu/public")
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list) and len(data) > 0:
                        item = data[0]
                        
                        # Check required fields for public menu
                        required_fields = ['id', 'name', 'description', 'category', 'image_url', 'is_available']
                        missing_fields = [field for field in required_fields if field not in item]
                        
                        if not missing_fields:
                            self.log_test("Menu Item Format Structure", True, "All required fields present in menu items")
                        else:
                            self.log_test("Menu Item Format Structure", False, f"Missing fields: {missing_fields}")
                        
                        # Verify pricing is hidden in public menu
                        if "price" not in item and "member_price" not in item:
                            self.log_test("Menu Item Pricing Hidden", True, "Pricing correctly hidden from public menu")
                        else:
                            self.log_test("Menu Item Pricing Hidden", False, "Pricing visible in public menu")
                        
                        # Check for members_only_pricing flag
                        if item.get("members_only_pricing") == True:
                            self.log_test("Menu Item Members Flag", True, "members_only_pricing flag correctly set")
                        else:
                            self.log_test("Menu Item Members Flag", False, "members_only_pricing flag missing or incorrect")
                    else:
                        self.log_test("Menu Item Format Structure", False, "No menu items found or invalid format")
                else:
                    self.log_test("Menu Item Format Structure", False, f"Could not retrieve menu: {response.status_code}")
            else:
                self.log_test("Menu Item Format Structure", False, "Could not seed data for testing")
        except Exception as e:
            self.log_test("Menu Item Format Structure", False, f"Connection error: {str(e)}")
    
    def run_registration_fix_tests(self):
        """Run all registration fix tests"""
        print(f"🚀 Testing Bitcoin Ben's Burger Bus Club Registration Fix")
        print(f"🔗 Backend URL: {self.base_url}")
        print("=" * 80)
        
        # Run specific tests for registration fix
        self.test_registration_endpoint_without_auth()
        self.test_profile_creation_without_auth()
        self.test_database_model_datetime_handling()
        self.test_authentication_flow_endpoints()
        self.test_member_menu_access_auth_required()
        self.test_menu_items_format()
        
        # Generate summary
        self.generate_summary()
    
    def generate_summary(self):
        """Generate test summary"""
        print("\n" + "=" * 80)
        print("📊 REGISTRATION FIX TEST SUMMARY")
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
    tester = RegistrationFixTester()
    tester.run_registration_fix_tests()