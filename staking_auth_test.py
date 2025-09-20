#!/usr/bin/env python3
"""
Test the fixed staking authentication
"""

import requests
import json

def test_staking_auth_fix():
    base_url = "https://bbc-rewards-hub.preview.emergentagent.com"
    session = requests.Session()
    
    print("🔧 Testing Fixed Staking Authentication")
    print("=" * 50)
    
    # Get BCH authentication token
    challenge_response = session.post(f"{base_url}/api/auth/challenge", 
                                    json={"app_name": "Bitcoin Ben's Burger Bus Club"})
    
    if challenge_response.status_code == 200:
        challenge_data = challenge_response.json()
        print(f"✅ Challenge generated: {challenge_data['challenge_id'][:8]}...")
        
        # Verify signature and get JWT token
        verify_data = {
            "challenge_id": challenge_data["challenge_id"],
            "bch_address": "bitcoincash:qr6m7j9njldwwzlg9v7v53unlr4jkmx6eylep8ekg2",
            "signature": "valid_signature_longer_than_10_chars_for_testing",
            "message": challenge_data["message"]
        }
        
        verify_response = session.post(f"{base_url}/api/auth/verify", json=verify_data)
        
        if verify_response.status_code == 200:
            token_data = verify_response.json()
            jwt_token = token_data["access_token"]
            print(f"✅ JWT token obtained")
            
            auth_headers = {"Authorization": f"Bearer {jwt_token}"}
            
            # Test 1: Wallet address update
            print("\n--- Testing Wallet Address Update ---")
            wallet_update_data = {"wallet_address": "7K8DVxtNJGnMtUY1CQJT5jcs8sFGSZTDiG7kowvFpECh"}
            wallet_response = session.post(f"{base_url}/api/profile/update-wallet", 
                                         json=wallet_update_data, headers=auth_headers)
            
            if wallet_response.status_code == 200:
                print("✅ Wallet address update successful")
            else:
                print(f"❌ Wallet address update failed: {wallet_response.status_code}")
                if wallet_response.status_code != 404:
                    print(f"   Response: {wallet_response.text}")
            
            # Test 2: My stakes retrieval
            print("\n--- Testing My Stakes Retrieval ---")
            stakes_response = session.get(f"{base_url}/api/staking/my-stakes", headers=auth_headers)
            
            if stakes_response.status_code == 200:
                stakes_data = stakes_response.json()
                print(f"✅ Stakes retrieval successful: {len(stakes_data.get('stakes', []))} stakes found")
                print(f"   Summary: {stakes_data.get('summary', {})}")
            else:
                print(f"❌ Stakes retrieval failed: {stakes_response.status_code}")
                if stakes_response.status_code != 404:
                    print(f"   Response: {stakes_response.text}")
            
            # Test 3: Stake creation
            print("\n--- Testing Stake Creation ---")
            stake_data = {
                "wallet_address": "7K8DVxtNJGnMtUY1CQJT5jcs8sFGSZTDiG7kowvFpECh",
                "amount_sol": 2.0,
                "validator_vote_account": "7K8DVxtNJGnMtUY1CQJT5jcs8sFGSZTDiG7kowvFpECh"
            }
            stake_response = session.post(f"{base_url}/api/staking/create-stake", 
                                        json=stake_data, headers=auth_headers)
            
            if stake_response.status_code == 200:
                stake_result = stake_response.json()
                print(f"✅ Stake creation successful")
                print(f"   Stake Account: {stake_result.get('stake_account', {}).get('id', 'N/A')}")
                print(f"   Status: {stake_result.get('stake_account', {}).get('status', 'N/A')}")
            else:
                print(f"❌ Stake creation failed: {stake_response.status_code}")
                if stake_response.status_code != 404:
                    print(f"   Response: {stake_response.text}")
            
            # Test 4: Minimum stake amount validation
            print("\n--- Testing Minimum Stake Amount Validation ---")
            small_stake_data = {
                "wallet_address": "7K8DVxtNJGnMtUY1CQJT5jcs8sFGSZTDiG7kowvFpECh",
                "amount_sol": 0.5  # Below minimum
            }
            small_stake_response = session.post(f"{base_url}/api/staking/create-stake", 
                                              json=small_stake_data, headers=auth_headers)
            
            if small_stake_response.status_code == 400:
                error_data = small_stake_response.json()
                if "Minimum stake amount" in error_data.get("detail", ""):
                    print("✅ Minimum stake amount validation working")
                else:
                    print(f"❌ Unexpected error: {error_data.get('detail')}")
            else:
                print(f"❌ Minimum stake validation failed: {small_stake_response.status_code}")
            
            # Test 5: Invalid wallet address validation
            print("\n--- Testing Invalid Wallet Address Validation ---")
            invalid_stake_data = {
                "wallet_address": "invalid_wallet_address",
                "amount_sol": 2.0
            }
            invalid_response = session.post(f"{base_url}/api/staking/create-stake", 
                                          json=invalid_stake_data, headers=auth_headers)
            
            if invalid_response.status_code == 400:
                error_data = invalid_response.json()
                if "Invalid wallet address" in error_data.get("detail", ""):
                    print("✅ Wallet address validation working")
                else:
                    print(f"❌ Unexpected error: {error_data.get('detail')}")
            else:
                print(f"❌ Wallet address validation failed: {invalid_response.status_code}")
        else:
            print(f"❌ JWT token verification failed: {verify_response.status_code}")
    else:
        print(f"❌ Challenge generation failed: {challenge_response.status_code}")

if __name__ == "__main__":
    test_staking_auth_fix()