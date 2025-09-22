#!/usr/bin/env python3
"""
Authentication Fix Testing for Bitcoin Ben's Burger Bus Club
Tests JWT secret key verification, authentication flow, and protected endpoints
"""

import requests
import json
import os
import time
from typing import Dict, Any, Optional

class AuthFixTester:
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
    
    def test_jwt_secret_verification(self):
        """Test that JWT secret key is properly loaded and working"""
        print("\n=== Testing JWT Secret Key Verification ===")
        
        # Check if backend .env has the FASTAPI_WALLETAUTH_SECRET
        try:
            with open('/app/backend/.env', 'r') as f:
                env_content = f.read()
                if 'FASTAPI_WALLETAUTH_SECRET=' in env_content:
                    # Extract the secret value
                    for line in env_content.split('\n'):
                        if line.startswith('FASTAPI_WALLETAUTH_SECRET='):
                            secret_value = line.split('=', 1)[1].strip().strip('"')
                            if secret_value and len(secret_value) > 10:
                                self.log_test("JWT Secret Environment Variable", True, f"Secret key loaded (length: {len(secret_value)})")
                            else:
                                self.log_test("JWT Secret Environment Variable", False, "Secret key is empty or too short")
                            break
                    else:
                        self.log_test("JWT Secret Environment Variable", False, "Secret key line found but could not parse value")
                else:
                    self.log_test("JWT Secret Environment Variable", False, "FASTAPI_WALLETAUTH_SECRET not found in backend .env")
        except Exception as e:
            self.log_test("JWT Secret Environment Variable", False, f"Error reading backend .env: {str(e)}")
    
    def test_authentication_challenge_endpoint(self):
        """Test POST /api/auth/authorization/challenge"""
        print("\n=== Testing Authentication Challenge Endpoint ===")
        
        test_wallet_address = "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"  # Valid Solana address format
        
        try:
            # Test challenge generation with proper parameters
            params = {"address": test_wallet_address, "chain": "SOL"}
            response = self.session.post(f"{self.base_url}/api/auth/authorization/challenge", params=params)
            
            if response.status_code == 200:
                data = response.json()
                if "challenge" in data and "address" in data:
                    challenge = data["challenge"]
                    if isinstance(challenge, str) and len(challenge) > 20:
                        self.log_test("Challenge Generation", True, f"Valid challenge generated (length: {len(challenge)})")
                        
                        # Verify challenge format (should be a message to sign)
                        if "Bitcoin Ben's Burger Bus Club" in challenge:
                            self.log_test("Challenge App Name", True, "Challenge contains correct app name")
                        else:
                            self.log_test("Challenge App Name", False, f"Challenge missing app name: {challenge[:100]}...")
                        
                        # Verify address is returned correctly
                        if data["address"] == test_wallet_address:
                            self.log_test("Challenge Address Echo", True, "Address correctly echoed in response")
                        else:
                            self.log_test("Challenge Address Echo", False, f"Address mismatch: sent {test_wallet_address}, got {data['address']}")
                    else:
                        self.log_test("Challenge Generation", False, f"Invalid challenge format: {challenge}")
                else:
                    self.log_test("Challenge Generation", False, f"Missing required fields in response: {data}")
            else:
                self.log_test("Challenge Generation", False, f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_test("Challenge Generation", False, f"Connection error: {str(e)}")
    
    def test_authentication_solve_endpoint(self):
        """Test POST /api/auth/authorization/solve"""
        print("\n=== Testing Authentication Solve Endpoint ===")
        
        # First get a challenge
        test_wallet_address = "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
        
        try:
            # Get challenge first
            params = {"address": test_wallet_address, "chain": "SOL"}
            challenge_response = self.session.post(f"{self.base_url}/api/auth/authorization/challenge", params=params)
            
            if challenge_response.status_code == 200:
                challenge_data = challenge_response.json()
                challenge = challenge_data.get("challenge")
                
                if challenge:
                    # Test solve endpoint with invalid signature (should fail gracefully)
                    solve_data = {
                        "address": test_wallet_address,
                        "chain": "SOL",
                        "signature": "invalid_signature_for_testing"
                    }
                    
                    solve_response = self.session.post(f"{self.base_url}/api/auth/authorization/solve", json=solve_data)
                    
                    # Should return an error but not crash (400 or 401)
                    if solve_response.status_code in [400, 401, 422]:
                        self.log_test("Solve Endpoint Error Handling", True, f"Properly handles invalid signature: {solve_response.status_code}")
                        
                        # Check if response contains error details
                        try:
                            error_data = solve_response.json()
                            if "detail" in error_data:
                                self.log_test("Solve Error Response Format", True, f"Proper error format: {error_data['detail']}")
                            else:
                                self.log_test("Solve Error Response Format", False, "Missing error details in response")
                        except:
                            self.log_test("Solve Error Response Format", False, "Invalid JSON in error response")
                    else:
                        self.log_test("Solve Endpoint Error Handling", False, f"Unexpected status: {solve_response.status_code}, Response: {solve_response.text}")
                else:
                    self.log_test("Solve Endpoint Error Handling", False, "Could not get challenge for solve test")
            else:
                self.log_test("Solve Endpoint Error Handling", False, "Could not get challenge for solve test")
        except Exception as e:
            self.log_test("Solve Endpoint Error Handling", False, f"Connection error: {str(e)}")
    
    def test_protected_endpoints_without_auth(self):
        """Test protected endpoints without authentication"""
        print("\n=== Testing Protected Endpoints Without Authentication ===")
        
        protected_endpoints = [
            ("/api/profile", "GET"),
            ("/api/membership/register", "POST")
        ]
        
        for endpoint, method in protected_endpoints:
            try:
                if method == "GET":
                    response = self.session.get(f"{self.base_url}{endpoint}")
                elif method == "POST":
                    # Test with sample data for registration
                    sample_data = {
                        "fullName": "Test User",
                        "email": "test@example.com",
                        "phone": "+1-555-0123",
                        "pma_agreed": True,
                        "dues_paid": True,
                        "payment_amount": 50.0
                    }
                    response = self.session.post(f"{self.base_url}{endpoint}", json=sample_data)
                
                # Should return 401 or 403, NOT 500
                if response.status_code in [401, 403]:
                    self.log_test(f"Protected Endpoint Auth Check ({endpoint})", True, f"Properly requires authentication: {response.status_code}")
                elif response.status_code == 422:
                    # Check if it's auth-related validation error
                    try:
                        error_data = response.json()
                        error_detail = str(error_data.get("detail", "")).lower()
                        if "authorization" in error_detail or "token" in error_detail or "auth" in error_detail:
                            self.log_test(f"Protected Endpoint Auth Check ({endpoint})", True, f"Auth validation error (expected): {response.status_code}")
                        else:
                            self.log_test(f"Protected Endpoint Auth Check ({endpoint})", False, f"Non-auth validation error: {error_data}")
                    except:
                        self.log_test(f"Protected Endpoint Auth Check ({endpoint})", True, f"Validation error (likely auth-related): {response.status_code}")
                elif response.status_code == 500:
                    self.log_test(f"Protected Endpoint Auth Check ({endpoint})", False, f"Server error instead of auth error: {response.status_code}")
                else:
                    self.log_test(f"Protected Endpoint Auth Check ({endpoint})", False, f"Unexpected status: {response.status_code}")
            except Exception as e:
                self.log_test(f"Protected Endpoint Auth Check ({endpoint})", False, f"Connection error: {str(e)}")
    
    def test_registration_flow_simulation(self):
        """Simulate complete registration flow (without actual wallet signature)"""
        print("\n=== Testing Registration Flow Simulation ===")
        
        test_wallet_address = "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
        
        try:
            # Step 1: Get authentication challenge
            params = {"address": test_wallet_address, "chain": "SOL"}
            challenge_response = self.session.post(f"{self.base_url}/api/auth/authorization/challenge", params=params)
            
            if challenge_response.status_code == 200:
                challenge_data = challenge_response.json()
                self.log_test("Registration Flow - Challenge", True, f"Challenge obtained successfully")
                
                # Step 2: Attempt to register without valid signature (should fail with proper error)
                registration_data = {
                    "fullName": "Bitcoin Ben Member",
                    "email": "member@bitcoinben.com",
                    "phone": "+1-555-BITCOIN",
                    "pma_agreed": True,
                    "dues_paid": True,
                    "payment_amount": 100.0
                }
                
                register_response = self.session.post(f"{self.base_url}/api/membership/register", json=registration_data)
                
                # Should fail with auth error, not server error
                if register_response.status_code in [401, 403]:
                    self.log_test("Registration Flow - Auth Required", True, f"Registration properly requires authentication: {register_response.status_code}")
                elif register_response.status_code == 422:
                    try:
                        error_data = register_response.json()
                        error_detail = str(error_data.get("detail", "")).lower()
                        if "authorization" in error_detail or "token" in error_detail:
                            self.log_test("Registration Flow - Auth Required", True, f"Registration auth validation working: {register_response.status_code}")
                        else:
                            self.log_test("Registration Flow - Auth Required", False, f"Unexpected validation error: {error_data}")
                    except:
                        self.log_test("Registration Flow - Auth Required", True, f"Registration validation (likely auth): {register_response.status_code}")
                elif register_response.status_code == 500:
                    self.log_test("Registration Flow - Auth Required", False, f"Server error in registration (should be auth error): {register_response.status_code}")
                else:
                    self.log_test("Registration Flow - Auth Required", False, f"Unexpected registration response: {register_response.status_code}")
            else:
                self.log_test("Registration Flow - Challenge", False, f"Could not get challenge: {challenge_response.status_code}")
        except Exception as e:
            self.log_test("Registration Flow - Challenge", False, f"Registration flow error: {str(e)}")
    
    def test_jwt_token_validation_behavior(self):
        """Test JWT token validation behavior"""
        print("\n=== Testing JWT Token Validation Behavior ===")
        
        # Test with invalid JWT token
        try:
            headers = {"Authorization": "Bearer invalid_jwt_token"}
            response = self.session.get(f"{self.base_url}/api/profile", headers=headers)
            
            # Should return 401 or 403, not 500
            if response.status_code in [401, 403]:
                self.log_test("Invalid JWT Token Handling", True, f"Invalid JWT properly rejected: {response.status_code}")
            elif response.status_code == 422:
                try:
                    error_data = response.json()
                    self.log_test("Invalid JWT Token Handling", True, f"JWT validation error (expected): {error_data}")
                except:
                    self.log_test("Invalid JWT Token Handling", True, f"JWT validation error: {response.status_code}")
            elif response.status_code == 500:
                self.log_test("Invalid JWT Token Handling", False, f"Server error with invalid JWT (should be auth error): {response.status_code}")
            else:
                self.log_test("Invalid JWT Token Handling", False, f"Unexpected response to invalid JWT: {response.status_code}")
        except Exception as e:
            self.log_test("Invalid JWT Token Handling", False, f"Error testing invalid JWT: {str(e)}")
        
        # Test with malformed Authorization header
        try:
            headers = {"Authorization": "InvalidFormat"}
            response = self.session.get(f"{self.base_url}/api/profile", headers=headers)
            
            if response.status_code in [401, 403, 422]:
                self.log_test("Malformed Auth Header Handling", True, f"Malformed auth header properly handled: {response.status_code}")
            elif response.status_code == 500:
                self.log_test("Malformed Auth Header Handling", False, f"Server error with malformed auth header: {response.status_code}")
            else:
                self.log_test("Malformed Auth Header Handling", False, f"Unexpected response to malformed auth: {response.status_code}")
        except Exception as e:
            self.log_test("Malformed Auth Header Handling", False, f"Error testing malformed auth header: {str(e)}")
    
    def run_auth_fix_tests(self):
        """Run all authentication fix tests"""
        print(f"🔐 Starting Authentication Fix Testing for Bitcoin Ben's Burger Bus Club")
        print(f"🔗 Backend URL: {self.base_url}")
        print("=" * 80)
        
        # Run authentication-focused tests
        self.test_jwt_secret_verification()
        self.test_authentication_challenge_endpoint()
        self.test_authentication_solve_endpoint()
        self.test_protected_endpoints_without_auth()
        self.test_registration_flow_simulation()
        self.test_jwt_token_validation_behavior()
        
        # Generate summary
        self.generate_summary()
    
    def generate_summary(self):
        """Generate test summary"""
        print("\n" + "=" * 80)
        print("📊 AUTHENTICATION FIX TEST SUMMARY")
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
    tester = AuthFixTester()
    tester.run_auth_fix_tests()