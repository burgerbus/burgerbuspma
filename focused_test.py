#!/usr/bin/env python3
"""
Focused test for the issues found in the backend testing
"""

import requests
import json
import time

def test_focused_issues():
    base_url = "https://bbc-rewards-hub.preview.emergentagent.com"
    session = requests.Session()
    
    print("=== Testing Fixed Issues ===")
    
    # Test 1: BCH Authentication and Profile Access
    print("\n1. Testing BCH Authentication and Profile Access")
    
    # Generate challenge
    challenge_response = session.post(f"{base_url}/api/auth/challenge", 
                                    json={"app_name": "Bitcoin Ben's Burger Bus Club"})
    
    if challenge_response.status_code == 200:
        challenge_data = challenge_response.json()
        print(f"✅ Challenge generated: {challenge_data['challenge_id']}")
        
        # Verify signature and get token
        verify_data = {
            "challenge_id": challenge_data["challenge_id"],
            "bch_address": "bitcoincash:qr6m7j9njldwwzlg9v7v53unlr4jkmx6eylep8ekg2",
            "signature": "valid_signature_longer_than_10_chars_for_testing",
            "message": challenge_data["message"]
        }
        
        verify_response = session.post(f"{base_url}/api/auth/verify", json=verify_data)
        
        if verify_response.status_code == 200:
            token_data = verify_response.json()
            access_token = token_data["access_token"]
            print(f"✅ JWT token obtained")
            
            # Test profile access with token
            auth_headers = {"Authorization": f"Bearer {access_token}"}
            profile_response = session.get(f"{base_url}/api/profile", headers=auth_headers)
            
            if profile_response.status_code == 200:
                profile_data = profile_response.json()
                print(f"✅ Profile access successful: {profile_data.get('wallet_address', 'N/A')}")
            else:
                print(f"❌ Profile access failed: {profile_response.status_code}")
        else:
            print(f"❌ Token verification failed: {verify_response.status_code}")
    else:
        print(f"❌ Challenge generation failed: {challenge_response.status_code}")
    
    # Test 2: Payment System
    print("\n2. Testing Payment System")
    
    # Create payment
    payment_response = session.post(f"{base_url}/api/payments/create-membership-payment", 
                                  json={"user_address": "bitcoincash:qtest123"})
    
    if payment_response.status_code == 200:
        payment_data = payment_response.json()
        payment_id = payment_data["payment_id"]
        print(f"✅ Payment created: {payment_id}")
        
        # Test payment status
        status_response = session.get(f"{base_url}/api/payments/status/{payment_id}")
        
        if status_response.status_code == 200:
            status_data = status_response.json()
            print(f"✅ Payment status retrieved: {status_data['status']}")
            print(f"   Amount USD: ${status_data.get('amount_usd', 'N/A')}")
            print(f"   Amount BCH: {status_data.get('amount_bch', 'N/A')}")
        else:
            print(f"❌ Payment status failed: {status_response.status_code}")
        
        # Test admin pending payments
        pending_response = session.get(f"{base_url}/api/admin/pending-payments")
        
        if pending_response.status_code == 200:
            pending_data = pending_response.json()
            print(f"✅ Admin pending payments: {pending_data['count']} payments")
        else:
            print(f"❌ Admin pending payments failed: {pending_response.status_code}")
    else:
        print(f"❌ Payment creation failed: {payment_response.status_code}")

if __name__ == "__main__":
    test_focused_issues()