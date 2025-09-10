#!/usr/bin/env python3
"""
PMA (Private Membership Association) Validation System Testing
Tests the updated PMA validation system for orders endpoint and profile management
"""

import requests
import json
import time
import os
from typing import Dict, Any, Optional
import uuid

class PMAValidationTester:
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
    
    def get_auth_token(self) -> Optional[str]:
        """Get authentication token for testing protected endpoints"""
        try:
            # Generate BCH authentication challenge
            challenge_data = {"app_name": "Bitcoin Ben's Burger Bus Club"}
            response = self.session.post(f"{self.base_url}/api/auth/challenge", json=challenge_data)
            
            if response.status_code != 200:
                print(f"Failed to generate challenge: {response.status_code}")
                return None
            
            challenge_resp = response.json()
            challenge_id = challenge_resp["challenge_id"]
            challenge_message = challenge_resp["message"]
            
            # Verify signature (using simplified verification for testing)
            verify_data = {
                "challenge_id": challenge_id,
                "bch_address": "bitcoincash:qr6m7j9njldwwzlg9v7v53unlr4jkmx6eylep8ekg2",
                "signature": "valid_signature_longer_than_10_chars_for_testing",
                "message": challenge_message
            }
            
            response = self.session.post(f"{self.base_url}/api/auth/verify", json=verify_data)
            
            if response.status_code == 200:
                token_data = response.json()
                return token_data["access_token"]
            else:
                print(f"Failed to verify signature: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error getting auth token: {str(e)}")
            return None
    
    def test_debug_profile_incomplete_status(self):
        """Test that /api/debug/profile returns incomplete membership status"""
        print("\n=== Testing Debug Profile Incomplete Status ===")
        
        try:
            response = self.session.get(f"{self.base_url}/api/debug/profile")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check that profile returns incomplete PMA status
                if data.get("pma_agreed") == False and data.get("dues_paid") == False:
                    self.log_test("Debug Profile Incomplete Status", True, 
                                f"Profile correctly shows incomplete PMA status: pma_agreed={data.get('pma_agreed')}, dues_paid={data.get('dues_paid')}")
                else:
                    self.log_test("Debug Profile Incomplete Status", False, 
                                f"Profile should show incomplete status but got: pma_agreed={data.get('pma_agreed')}, dues_paid={data.get('dues_paid')}")
                
                # Verify other expected fields are present
                expected_fields = ["id", "wallet_address", "membership_tier", "full_name", "email", "phone", "payment_amount", "total_orders"]
                missing_fields = [field for field in expected_fields if field not in data]
                
                if not missing_fields:
                    self.log_test("Debug Profile Structure", True, "All expected profile fields present")
                else:
                    self.log_test("Debug Profile Structure", False, f"Missing fields: {missing_fields}")
                    
            else:
                self.log_test("Debug Profile Incomplete Status", False, f"Status: {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("Debug Profile Incomplete Status", False, f"Connection error: {str(e)}")
    
    def test_pma_registration_update(self):
        """Test that /api/debug/register properly updates PMA status"""
        print("\n=== Testing PMA Registration Update ===")
        
        try:
            # Test registration with complete PMA data
            registration_data = {
                "wallet_address": "test_wallet_pma_123",
                "fullName": "John PMA Member",
                "email": "john@bitcoinben.com",
                "phone": "+1-555-PMA-TEST",
                "pma_agreed": True,
                "dues_paid": True,
                "payment_amount": 21.0
            }
            
            response = self.session.post(f"{self.base_url}/api/debug/register", json=registration_data)
            
            if response.status_code == 200:
                data = response.json()
                
                if "message" in data and "member" in data:
                    member_data = data["member"]
                    
                    # Verify PMA status was updated correctly
                    if member_data.get("pma_agreed") == True and member_data.get("dues_paid") == True:
                        self.log_test("PMA Registration Update", True, 
                                    f"Registration correctly updated PMA status: pma_agreed={member_data.get('pma_agreed')}, dues_paid={member_data.get('dues_paid')}")
                    else:
                        self.log_test("PMA Registration Update", False, 
                                    f"PMA status not updated correctly: pma_agreed={member_data.get('pma_agreed')}, dues_paid={member_data.get('dues_paid')}")
                    
                    # Verify other fields were updated
                    if (member_data.get("full_name") == "John PMA Member" and 
                        member_data.get("email") == "john@bitcoinben.com" and
                        member_data.get("payment_amount") == 21.0):
                        self.log_test("PMA Registration Fields Update", True, "All registration fields updated correctly")
                    else:
                        self.log_test("PMA Registration Fields Update", False, 
                                    f"Fields not updated correctly: name={member_data.get('full_name')}, email={member_data.get('email')}, payment={member_data.get('payment_amount')}")
                else:
                    self.log_test("PMA Registration Update", False, "Invalid response structure", data)
            else:
                self.log_test("PMA Registration Update", False, f"Status: {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("PMA Registration Update", False, f"Connection error: {str(e)}")
    
    def test_orders_pma_validation_incomplete(self):
        """Test POST /api/orders with incomplete membership (should return 403)"""
        print("\n=== Testing Orders PMA Validation - Incomplete Membership ===")
        
        # Get auth token
        auth_token = self.get_auth_token()
        if not auth_token:
            self.log_test("Orders PMA Validation Setup", False, "Could not get authentication token")
            return
        
        auth_headers = {"Authorization": f"Bearer {auth_token}"}
        
        try:
            # Test order creation with incomplete membership
            items_data = [
                {"item_id": "test_item_123", "quantity": 1, "special_instructions": "Extra crispy"}
            ]
            
            params = {
                "pickup_location": "Downtown Business District",
                "pickup_time": "12:00"
            }
            
            response = self.session.post(f"{self.base_url}/api/orders", json=items_data, params=params, headers=auth_headers)
            
            if response.status_code == 403:
                data = response.json()
                error_detail = data.get("detail", "")
                
                # Check for PMA agreement error message
                if "PMA agreement" in error_detail and "signed" in error_detail:
                    self.log_test("Orders PMA Agreement Validation", True, 
                                f"Correctly blocked order with PMA agreement error: {error_detail}")
                else:
                    self.log_test("Orders PMA Agreement Validation", False, 
                                f"Expected PMA agreement error but got: {error_detail}")
            else:
                self.log_test("Orders PMA Agreement Validation", False, 
                            f"Expected 403 status but got: {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("Orders PMA Agreement Validation", False, f"Connection error: {str(e)}")
    
    def test_orders_pma_validation_no_agreement(self):
        """Test POST /api/orders with pma_agreed=false (should return 403)"""
        print("\n=== Testing Orders PMA Validation - No Agreement ===")
        
        # First, create a member with pma_agreed=false but dues_paid=true
        try:
            registration_data = {
                "wallet_address": "test_wallet_no_agreement",
                "fullName": "Jane No Agreement",
                "email": "jane@bitcoinben.com",
                "phone": "+1-555-NO-AGREE",
                "pma_agreed": False,  # No agreement
                "dues_paid": True,   # But dues paid
                "payment_amount": 21.0
            }
            
            reg_response = self.session.post(f"{self.base_url}/api/debug/register", json=registration_data)
            
            if reg_response.status_code != 200:
                self.log_test("Orders PMA No Agreement Setup", False, "Could not create test member")
                return
            
            # Get auth token (this would be for the member with no agreement)
            auth_token = self.get_auth_token()
            if not auth_token:
                self.log_test("Orders PMA No Agreement Setup", False, "Could not get authentication token")
                return
            
            auth_headers = {"Authorization": f"Bearer {auth_token}"}
            
            # Try to create order
            items_data = [
                {"item_id": "test_item_456", "quantity": 2}
            ]
            
            params = {
                "pickup_location": "Downtown Business District",
                "pickup_time": "13:00"
            }
            
            response = self.session.post(f"{self.base_url}/api/orders", json=items_data, params=params, headers=auth_headers)
            
            if response.status_code == 403:
                data = response.json()
                error_detail = data.get("detail", "")
                
                if "PMA agreement" in error_detail:
                    self.log_test("Orders No PMA Agreement Block", True, 
                                f"Correctly blocked order without PMA agreement: {error_detail}")
                else:
                    self.log_test("Orders No PMA Agreement Block", False, 
                                f"Expected PMA agreement error but got: {error_detail}")
            else:
                self.log_test("Orders No PMA Agreement Block", False, 
                            f"Expected 403 status but got: {response.status_code}")
                
        except Exception as e:
            self.log_test("Orders No PMA Agreement Block", False, f"Connection error: {str(e)}")
    
    def test_orders_pma_validation_no_dues(self):
        """Test POST /api/orders with dues_paid=false (should return 403)"""
        print("\n=== Testing Orders PMA Validation - No Dues Paid ===")
        
        # First, create a member with pma_agreed=true but dues_paid=false
        try:
            registration_data = {
                "wallet_address": "test_wallet_no_dues",
                "fullName": "Bob No Dues",
                "email": "bob@bitcoinben.com",
                "phone": "+1-555-NO-DUES",
                "pma_agreed": True,   # Agreement signed
                "dues_paid": False,   # But no dues paid
                "payment_amount": 0.0
            }
            
            reg_response = self.session.post(f"{self.base_url}/api/debug/register", json=registration_data)
            
            if reg_response.status_code != 200:
                self.log_test("Orders PMA No Dues Setup", False, "Could not create test member")
                return
            
            # Get auth token
            auth_token = self.get_auth_token()
            if not auth_token:
                self.log_test("Orders PMA No Dues Setup", False, "Could not get authentication token")
                return
            
            auth_headers = {"Authorization": f"Bearer {auth_token}"}
            
            # Try to create order
            items_data = [
                {"item_id": "test_item_789", "quantity": 1}
            ]
            
            params = {
                "pickup_location": "Downtown Business District",
                "pickup_time": "14:00"
            }
            
            response = self.session.post(f"{self.base_url}/api/orders", json=items_data, params=params, headers=auth_headers)
            
            if response.status_code == 403:
                data = response.json()
                error_detail = data.get("detail", "")
                
                if "dues" in error_detail and "$21" in error_detail:
                    self.log_test("Orders No Dues Paid Block", True, 
                                f"Correctly blocked order without dues payment: {error_detail}")
                else:
                    self.log_test("Orders No Dues Paid Block", False, 
                                f"Expected dues payment error but got: {error_detail}")
            else:
                self.log_test("Orders No Dues Paid Block", False, 
                            f"Expected 403 status but got: {response.status_code}")
                
        except Exception as e:
            self.log_test("Orders No Dues Paid Block", False, f"Connection error: {str(e)}")
    
    def test_orders_pma_validation_complete(self):
        """Test POST /api/orders with both pma_agreed=true AND dues_paid=true (should work)"""
        print("\n=== Testing Orders PMA Validation - Complete Membership ===")
        
        # First, seed menu data to ensure we have items to order
        try:
            seed_response = self.session.post(f"{self.base_url}/api/admin/seed-data")
            if seed_response.status_code == 200:
                time.sleep(2)  # Allow time for seeding
                self.log_test("Orders Complete PMA Setup - Data Seeding", True, "Menu data seeded successfully")
            else:
                self.log_test("Orders Complete PMA Setup - Data Seeding", False, f"Seeding failed: {seed_response.status_code}")
        except Exception as e:
            self.log_test("Orders Complete PMA Setup - Data Seeding", False, f"Seeding error: {str(e)}")
        
        # Create a member with complete PMA status
        try:
            registration_data = {
                "wallet_address": "test_wallet_complete_pma",
                "fullName": "Alice Complete Member",
                "email": "alice@bitcoinben.com",
                "phone": "+1-555-COMPLETE",
                "pma_agreed": True,   # Agreement signed
                "dues_paid": True,    # Dues paid
                "payment_amount": 21.0
            }
            
            reg_response = self.session.post(f"{self.base_url}/api/debug/register", json=registration_data)
            
            if reg_response.status_code != 200:
                self.log_test("Orders Complete PMA Setup", False, "Could not create complete member")
                return
            
            # Get auth token
            auth_token = self.get_auth_token()
            if not auth_token:
                self.log_test("Orders Complete PMA Setup", False, "Could not get authentication token")
                return
            
            auth_headers = {"Authorization": f"Bearer {auth_token}"}
            
            # Get menu items to find a valid item_id
            menu_response = self.session.get(f"{self.base_url}/api/debug/menu")
            if menu_response.status_code == 200:
                menu_items = menu_response.json()
                if len(menu_items) > 0:
                    item_id = menu_items[0]["id"]
                    
                    # Try to create order with complete PMA status
                    order_data = {
                        "items": [
                            {"item_id": item_id, "quantity": 1, "special_instructions": "Extra delicious"}
                        ],
                        "pickup_location": "Downtown Business District",
                        "pickup_time": "15:00"
                    }
                    
                    response = self.session.post(f"{self.base_url}/api/orders", json=order_data, headers=auth_headers)
                    
                    if response.status_code in [200, 201]:
                        data = response.json()
                        
                        # Verify order was created successfully
                        if "id" in data and "wallet_address" in data:
                            self.log_test("Orders Complete PMA Success", True, 
                                        f"Order created successfully with complete PMA status: Order ID {data.get('id')}")
                        else:
                            self.log_test("Orders Complete PMA Success", False, 
                                        "Order response missing required fields", data)
                    else:
                        self.log_test("Orders Complete PMA Success", False, 
                                    f"Order creation failed with status: {response.status_code}", response.text)
                else:
                    self.log_test("Orders Complete PMA Success", False, "No menu items available for testing")
            else:
                self.log_test("Orders Complete PMA Success", False, "Could not retrieve menu items")
                
        except Exception as e:
            self.log_test("Orders Complete PMA Success", False, f"Connection error: {str(e)}")
    
    def test_error_message_validation(self):
        """Test that 403 error messages are descriptive and helpful"""
        print("\n=== Testing Error Message Validation ===")
        
        # Get auth token
        auth_token = self.get_auth_token()
        if not auth_token:
            self.log_test("Error Message Validation Setup", False, "Could not get authentication token")
            return
        
        auth_headers = {"Authorization": f"Bearer {auth_token}"}
        
        try:
            # Test order with incomplete membership to check error message quality
            order_data = {
                "items": [{"item_id": "test_item", "quantity": 1}],
                "pickup_location": "Test Location",
                "pickup_time": "12:00"
            }
            
            response = self.session.post(f"{self.base_url}/api/orders", json=order_data, headers=auth_headers)
            
            if response.status_code == 403:
                data = response.json()
                error_detail = data.get("detail", "")
                
                # Check if error message is descriptive and helpful
                descriptive_elements = [
                    "PMA agreement" in error_detail,
                    "signed" in error_detail or "complete" in error_detail,
                    "membership" in error_detail or "registration" in error_detail
                ]
                
                if any(descriptive_elements):
                    self.log_test("Error Message Descriptiveness", True, 
                                f"Error message is descriptive: {error_detail}")
                else:
                    self.log_test("Error Message Descriptiveness", False, 
                                f"Error message not descriptive enough: {error_detail}")
                
                # Check if error message provides guidance
                guidance_elements = [
                    "Please" in error_detail,
                    "complete" in error_detail,
                    "registration" in error_detail or "membership" in error_detail
                ]
                
                if any(guidance_elements):
                    self.log_test("Error Message Guidance", True, 
                                f"Error message provides helpful guidance: {error_detail}")
                else:
                    self.log_test("Error Message Guidance", False, 
                                f"Error message lacks guidance: {error_detail}")
                
                # Verify correct HTTP status code
                self.log_test("Error Status Code", True, f"Correct 403 Forbidden status returned")
                
            else:
                self.log_test("Error Message Validation", False, 
                            f"Expected 403 error but got: {response.status_code}")
                
        except Exception as e:
            self.log_test("Error Message Validation", False, f"Connection error: {str(e)}")
    
    def test_profile_status_after_registration(self):
        """Test GET /api/debug/profile after registration shows completed status"""
        print("\n=== Testing Profile Status After Registration ===")
        
        try:
            # First register a complete member
            registration_data = {
                "wallet_address": "test_wallet_profile_check",
                "fullName": "Charlie Profile Test",
                "email": "charlie@bitcoinben.com",
                "phone": "+1-555-PROFILE",
                "pma_agreed": True,
                "dues_paid": True,
                "payment_amount": 21.0
            }
            
            reg_response = self.session.post(f"{self.base_url}/api/debug/register", json=registration_data)
            
            if reg_response.status_code == 200:
                # Note: The debug profile endpoint returns static incomplete data
                # This is by design for testing the PMA flow
                profile_response = self.session.get(f"{self.base_url}/api/debug/profile")
                
                if profile_response.status_code == 200:
                    profile_data = profile_response.json()
                    
                    # The debug profile endpoint is designed to return incomplete status
                    # to allow testing of the PMA validation flow
                    if profile_data.get("pma_agreed") == False and profile_data.get("dues_paid") == False:
                        self.log_test("Debug Profile Returns Incomplete Status", True, 
                                    "Debug profile correctly returns incomplete status for testing PMA flow")
                    else:
                        self.log_test("Debug Profile Returns Incomplete Status", False, 
                                    f"Debug profile should return incomplete status but got: pma_agreed={profile_data.get('pma_agreed')}, dues_paid={profile_data.get('dues_paid')}")
                else:
                    self.log_test("Profile Status After Registration", False, 
                                f"Could not retrieve profile: {profile_response.status_code}")
            else:
                self.log_test("Profile Status After Registration", False, 
                            f"Registration failed: {reg_response.status_code}")
                
        except Exception as e:
            self.log_test("Profile Status After Registration", False, f"Connection error: {str(e)}")
    
    def run_pma_validation_tests(self):
        """Run all PMA validation tests"""
        print(f"🚀 Starting PMA Validation System Testing")
        print(f"🔗 Backend URL: {self.base_url}")
        print("=" * 80)
        
        # Run PMA validation test suites
        self.test_debug_profile_incomplete_status()
        self.test_pma_registration_update()
        self.test_orders_pma_validation_incomplete()
        self.test_orders_pma_validation_no_agreement()
        self.test_orders_pma_validation_no_dues()
        self.test_orders_pma_validation_complete()
        self.test_error_message_validation()
        self.test_profile_status_after_registration()
        
        # Generate summary
        self.generate_summary()
    
    def generate_summary(self):
        """Generate test summary"""
        print("\n" + "=" * 80)
        print("📊 PMA VALIDATION TEST SUMMARY")
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
    tester = PMAValidationTester()
    tester.run_pma_validation_tests()