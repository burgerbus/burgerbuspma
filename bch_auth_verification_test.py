#!/usr/bin/env python3
"""
Comprehensive BCH Authentication System Verification Test
Tests all specific requirements from the review request
"""

import requests
import json
import jwt
from datetime import datetime, timedelta

class BCHAuthVerificationTester:
    def __init__(self):
        self.base_url = "https://bbc-rewards-hub.preview.emergentagent.com"
        self.session = requests.Session()
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "details": details
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
    
    def test_challenge_endpoint_requirements(self):
        """Test POST /api/auth/challenge requirements"""
        print("\n=== Testing Challenge Endpoint Requirements ===")
        
        try:
            challenge_data = {"app_name": "Bitcoin Ben's Burger Bus Club"}
            response = self.session.post(f"{self.base_url}/api/auth/challenge", json=challenge_data)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ["challenge_id", "message", "expires_at"]
                if all(field in data for field in required_fields):
                    self.log_test("Challenge Structure", True, "Returns challenge_id, message, expires_at")
                else:
                    missing = [f for f in required_fields if f not in data]
                    self.log_test("Challenge Structure", False, f"Missing fields: {missing}")
                
                # Check message content
                message = data["message"]
                if ("Bitcoin Ben's Burger Bus Club" in message and 
                    "Time:" in message and 
                    "Nonce:" in message):
                    self.log_test("Message Content", True, "Message includes app name, timestamp, and nonce")
                else:
                    self.log_test("Message Content", False, f"Invalid message format: {message}")
                
                # Check expiration (should be 5 minutes)
                try:
                    expires_at = datetime.fromisoformat(data["expires_at"])
                    now = datetime.utcnow()
                    time_diff = (expires_at - now).total_seconds()
                    if 250 <= time_diff <= 350:  # Around 5 minutes (300 seconds)
                        self.log_test("Challenge Expiration", True, f"Expires in {time_diff:.0f} seconds (5 minutes)")
                    else:
                        self.log_test("Challenge Expiration", False, f"Expires in {time_diff:.0f} seconds, expected ~300")
                except Exception as e:
                    self.log_test("Challenge Expiration", False, f"Error parsing expires_at: {str(e)}")
                
                # Store for verification tests
                self.challenge_id = data["challenge_id"]
                self.challenge_message = data["message"]
                
            else:
                self.log_test("Challenge Endpoint", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Challenge Endpoint", False, f"Error: {str(e)}")
    
    def test_verify_endpoint_requirements(self):
        """Test POST /api/auth/verify requirements"""
        print("\n=== Testing Verify Endpoint Requirements ===")
        
        if not hasattr(self, 'challenge_id'):
            self.log_test("Verify Endpoint", False, "No challenge available for testing")
            return
        
        try:
            verify_data = {
                "challenge_id": self.challenge_id,
                "bch_address": "bitcoincash:qr6m7j9njldwwzlg9v7v53unlr4jkmx6eylep8ekg2",
                "signature": "valid_signature_longer_than_10_chars_for_testing",
                "message": self.challenge_message
            }
            response = self.session.post(f"{self.base_url}/api/auth/verify", json=verify_data)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check JWT token response
                if "access_token" in data and "token_type" in data and "expires_in" in data:
                    self.log_test("JWT Token Response", True, "Returns access_token, token_type, expires_in")
                    
                    # Store token for protected endpoint tests
                    self.access_token = data["access_token"]
                    
                    # Verify token format
                    token_parts = data["access_token"].split('.')
                    if len(token_parts) == 3:
                        self.log_test("JWT Format", True, "JWT has 3 parts (header.payload.signature)")
                    else:
                        self.log_test("JWT Format", False, f"JWT has {len(token_parts)} parts, expected 3")
                    
                    # Check token expiration (30 minutes = 1800 seconds)
                    if data["expires_in"] == 1800:
                        self.log_test("JWT Expiration", True, "Token expires in 30 minutes (1800 seconds)")
                    else:
                        self.log_test("JWT Expiration", False, f"Token expires in {data['expires_in']} seconds, expected 1800")
                    
                else:
                    self.log_test("JWT Token Response", False, "Missing required JWT response fields")
            else:
                self.log_test("Verify Endpoint", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Verify Endpoint", False, f"Error: {str(e)}")
    
    def test_jwt_token_claims(self):
        """Test JWT token claims requirements"""
        print("\n=== Testing JWT Token Claims ===")
        
        if not hasattr(self, 'access_token'):
            self.log_test("JWT Claims", False, "No access token available for testing")
            return
        
        try:
            # Decode JWT without verification for testing
            decoded = jwt.decode(self.access_token, options={'verify_signature': False})
            
            # Check BCH address in 'sub' claim
            expected_address = "bitcoincash:qr6m7j9njldwwzlg9v7v53unlr4jkmx6eylep8ekg2"
            if decoded.get('sub') == expected_address:
                self.log_test("BCH Address Claim", True, "BCH address correctly stored in 'sub' claim")
            else:
                self.log_test("BCH Address Claim", False, f"Expected {expected_address}, got {decoded.get('sub')}")
            
            # Check expiration claim
            if 'exp' in decoded:
                exp_time = datetime.fromtimestamp(decoded['exp'])
                now = datetime.utcnow()
                time_diff = (exp_time - now).total_seconds()
                if 1700 <= time_diff <= 1900:  # Around 30 minutes
                    self.log_test("JWT Expiration Claim", True, f"Token expires in {time_diff:.0f} seconds")
                else:
                    self.log_test("JWT Expiration Claim", False, f"Token expires in {time_diff:.0f} seconds, expected ~1800")
            else:
                self.log_test("JWT Expiration Claim", False, "No 'exp' claim in JWT")
            
        except Exception as e:
            self.log_test("JWT Claims", False, f"Error decoding JWT: {str(e)}")
    
    def test_protected_endpoints(self):
        """Test that protected endpoints work with new JWT tokens"""
        print("\n=== Testing Protected Endpoints ===")
        
        if not hasattr(self, 'access_token'):
            self.log_test("Protected Endpoints", False, "No access token available for testing")
            return
        
        auth_headers = {"Authorization": f"Bearer {self.access_token}"}
        
        # Test key protected endpoints
        endpoints = [
            ("/api/profile", "GET"),
            ("/api/membership/register", "POST")
        ]
        
        for endpoint, method in endpoints:
            try:
                if method == "POST":
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
                    response = self.session.get(f"{self.base_url}{endpoint}", headers=auth_headers)
                
                if response.status_code in [200, 201]:
                    self.log_test(f"Protected Endpoint {endpoint}", True, f"Successfully accessed with BCH JWT")
                else:
                    self.log_test(f"Protected Endpoint {endpoint}", False, f"Access failed: {response.status_code}")
            except Exception as e:
                self.log_test(f"Protected Endpoint {endpoint}", False, f"Error: {str(e)}")
    
    def test_error_scenarios(self):
        """Test error handling scenarios"""
        print("\n=== Testing Error Scenarios ===")
        
        # Test invalid challenge_id
        try:
            verify_data = {
                "challenge_id": "invalid_challenge_id",
                "bch_address": "bitcoincash:qr6m7j9njldwwzlg9v7v53unlr4jkmx6eylep8ekg2",
                "signature": "valid_signature_longer_than_10_chars",
                "message": "Some message"
            }
            response = self.session.post(f"{self.base_url}/api/auth/verify", json=verify_data)
            
            if response.status_code == 400:
                data = response.json()
                if "Invalid or expired challenge" in data.get("detail", ""):
                    self.log_test("Invalid Challenge ID", True, "Properly rejects invalid challenge_id")
                else:
                    self.log_test("Invalid Challenge ID", False, f"Unexpected error: {data.get('detail')}")
            else:
                self.log_test("Invalid Challenge ID", False, f"Expected 400, got {response.status_code}")
        except Exception as e:
            self.log_test("Invalid Challenge ID", False, f"Error: {str(e)}")
        
        # Test invalid signature
        if hasattr(self, 'challenge_id') and hasattr(self, 'challenge_message'):
            try:
                verify_data = {
                    "challenge_id": self.challenge_id,
                    "bch_address": "bitcoincash:qr6m7j9njldwwzlg9v7v53unlr4jkmx6eylep8ekg2",
                    "signature": "short",  # Invalid signature
                    "message": self.challenge_message
                }
                response = self.session.post(f"{self.base_url}/api/auth/verify", json=verify_data)
                
                if response.status_code == 401:
                    data = response.json()
                    if "Invalid signature" in data.get("detail", ""):
                        self.log_test("Invalid Signature", True, "Properly rejects invalid signature")
                    else:
                        self.log_test("Invalid Signature", False, f"Unexpected error: {data.get('detail')}")
                else:
                    self.log_test("Invalid Signature", False, f"Expected 401, got {response.status_code}")
            except Exception as e:
                self.log_test("Invalid Signature", False, f"Error: {str(e)}")
    
    def run_verification_tests(self):
        """Run all BCH authentication verification tests"""
        print("🚀 BCH Authentication System Verification Test")
        print("=" * 60)
        
        self.test_challenge_endpoint_requirements()
        self.test_verify_endpoint_requirements()
        self.test_jwt_token_claims()
        self.test_protected_endpoints()
        self.test_error_scenarios()
        
        # Generate summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print("\n" + "=" * 60)
        print("📊 VERIFICATION SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n🔍 FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  ❌ {result['test']}: {result['details']}")
        
        return passed_tests == total_tests

if __name__ == "__main__":
    tester = BCHAuthVerificationTester()
    success = tester.run_verification_tests()
    
    if success:
        print("\n🎉 ALL BCH AUTHENTICATION REQUIREMENTS VERIFIED!")
    else:
        print("\n⚠️  Some requirements need attention.")