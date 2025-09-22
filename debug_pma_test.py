#!/usr/bin/env python3
"""
Debug PMA Validation - Check what member profile is being used
"""

import requests
import json

def get_backend_url():
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

def get_auth_token():
    """Get authentication token"""
    base_url = get_backend_url()
    session = requests.Session()
    
    try:
        # Generate BCH authentication challenge
        challenge_data = {"app_name": "Bitcoin Ben's Burger Bus Club"}
        response = session.post(f"{base_url}/api/auth/challenge", json=challenge_data)
        
        if response.status_code != 200:
            print(f"Failed to generate challenge: {response.status_code}")
            return None, None
        
        challenge_resp = response.json()
        challenge_id = challenge_resp["challenge_id"]
        challenge_message = challenge_resp["message"]
        
        # Verify signature
        verify_data = {
            "challenge_id": challenge_id,
            "bch_address": "bitcoincash:qr6m7j9njldwwzlg9v7v53unlr4jkmx6eylep8ekg2",
            "signature": "valid_signature_longer_than_10_chars_for_testing",
            "message": challenge_message
        }
        
        response = session.post(f"{base_url}/api/auth/verify", json=verify_data)
        
        if response.status_code == 200:
            token_data = response.json()
            return token_data["access_token"], session
        else:
            print(f"Failed to verify signature: {response.status_code}")
            return None, None
            
    except Exception as e:
        print(f"Error getting auth token: {str(e)}")
        return None, None

def main():
    base_url = get_backend_url()
    print(f"Testing PMA validation with backend: {base_url}")
    
    # Get auth token
    auth_token, session = get_auth_token()
    if not auth_token:
        print("❌ Could not get authentication token")
        return
    
    print("✅ Got authentication token")
    
    # Check member profile
    auth_headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        profile_response = session.get(f"{base_url}/api/profile", headers=auth_headers)
        if profile_response.status_code == 200:
            profile_data = profile_response.json()
            print(f"📋 Member Profile:")
            print(f"   Wallet Address: {profile_data.get('wallet_address')}")
            print(f"   PMA Agreed: {profile_data.get('pma_agreed')}")
            print(f"   Dues Paid: {profile_data.get('dues_paid')}")
            print(f"   Payment Amount: {profile_data.get('payment_amount')}")
            print(f"   Full Name: {profile_data.get('full_name')}")
            print(f"   Email: {profile_data.get('email')}")
        else:
            print(f"❌ Could not get profile: {profile_response.status_code}")
            return
    except Exception as e:
        print(f"❌ Error getting profile: {str(e)}")
        return
    
    # Now try to create an order
    print(f"\n🛒 Testing order creation...")
    
    try:
        items_data = [{"item_id": "test_item", "quantity": 1}]
        params = {
            "pickup_location": "Test Location",
            "pickup_time": "12:00"
        }
        
        order_response = session.post(f"{base_url}/api/orders", json=items_data, params=params, headers=auth_headers)
        
        print(f"📦 Order Response:")
        print(f"   Status Code: {order_response.status_code}")
        
        if order_response.status_code == 403:
            error_data = order_response.json()
            print(f"   Error Detail: {error_data.get('detail')}")
            print("✅ PMA validation working correctly - order blocked")
        elif order_response.status_code == 200:
            order_data = order_response.json()
            print(f"   Order ID: {order_data.get('id')}")
            print("❌ PMA validation NOT working - order allowed when it should be blocked")
        else:
            print(f"   Response: {order_response.text}")
            print(f"❓ Unexpected response code: {order_response.status_code}")
            
    except Exception as e:
        print(f"❌ Error creating order: {str(e)}")

if __name__ == "__main__":
    main()