#!/usr/bin/env python3
"""
Proper PMA Validation Testing - Test with fresh addresses and controlled scenarios
"""

import requests
import json
import uuid

def get_backend_url():
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

def get_auth_token_for_address(bch_address):
    """Get authentication token for a specific BCH address"""
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
            "bch_address": bch_address,
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

def test_scenario(scenario_name, bch_address, expected_pma_agreed, expected_dues_paid, expected_order_status):
    """Test a specific PMA validation scenario"""
    base_url = get_backend_url()
    print(f"\n=== {scenario_name} ===")
    print(f"BCH Address: {bch_address}")
    print(f"Expected PMA Agreed: {expected_pma_agreed}")
    print(f"Expected Dues Paid: {expected_dues_paid}")
    print(f"Expected Order Status: {expected_order_status}")
    
    # Get auth token for this address
    auth_token, session = get_auth_token_for_address(bch_address)
    if not auth_token:
        print("❌ Could not get authentication token")
        return False
    
    auth_headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Check member profile
    try:
        profile_response = session.get(f"{base_url}/api/profile", headers=auth_headers)
        if profile_response.status_code == 200:
            profile_data = profile_response.json()
            actual_pma_agreed = profile_data.get('pma_agreed')
            actual_dues_paid = profile_data.get('dues_paid')
            
            print(f"📋 Actual Profile Status:")
            print(f"   PMA Agreed: {actual_pma_agreed}")
            print(f"   Dues Paid: {actual_dues_paid}")
            
            # Verify profile matches expectations
            profile_correct = (actual_pma_agreed == expected_pma_agreed and 
                             actual_dues_paid == expected_dues_paid)
            
            if not profile_correct:
                print(f"⚠️  Profile doesn't match expected values")
        else:
            print(f"❌ Could not get profile: {profile_response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error getting profile: {str(e)}")
        return False
    
    # Test order creation
    try:
        items_data = [{"item_id": "test_item", "quantity": 1}]
        params = {
            "pickup_location": "Test Location",
            "pickup_time": "12:00"
        }
        
        order_response = session.post(f"{base_url}/api/orders", json=items_data, params=params, headers=auth_headers)
        actual_order_status = order_response.status_code
        
        print(f"🛒 Order Test Result:")
        print(f"   Status Code: {actual_order_status}")
        
        if actual_order_status == expected_order_status:
            if actual_order_status == 403:
                error_data = order_response.json()
                error_detail = error_data.get('detail', '')
                print(f"   Error Detail: {error_detail}")
                print("✅ PMA validation working correctly - order blocked as expected")
                
                # Check error message quality
                if "PMA agreement" in error_detail or "dues" in error_detail:
                    print("✅ Error message is descriptive")
                else:
                    print("⚠️  Error message could be more descriptive")
                    
            elif actual_order_status == 200:
                order_data = order_response.json()
                print(f"   Order ID: {order_data.get('id')}")
                print("✅ Order allowed as expected (complete PMA status)")
            
            return True
        else:
            print(f"❌ Expected status {expected_order_status}, got {actual_order_status}")
            if order_response.status_code == 403:
                error_data = order_response.json()
                print(f"   Error Detail: {error_data.get('detail')}")
            elif order_response.status_code == 200:
                order_data = order_response.json()
                print(f"   Order ID: {order_data.get('id')}")
            else:
                print(f"   Response: {order_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error creating order: {str(e)}")
        return False

def main():
    base_url = get_backend_url()
    print(f"🚀 Testing PMA Validation System")
    print(f"🔗 Backend URL: {base_url}")
    print("=" * 80)
    
    # Test scenarios with fresh BCH addresses
    test_results = []
    
    # Scenario 1: Fresh address (should have incomplete PMA status)
    fresh_address = f"bitcoincash:qr6m7j9njldwwzlg9v7v53unlr4jkmx6eylep{uuid.uuid4().hex[:8]}"
    result1 = test_scenario(
        "Fresh Address - Incomplete PMA Status",
        fresh_address,
        expected_pma_agreed=False,
        expected_dues_paid=False,
        expected_order_status=403
    )
    test_results.append(("Fresh Address Test", result1))
    
    # Scenario 2: Register a member with PMA agreed but no dues paid
    session = requests.Session()
    partial_address = f"bitcoincash:qr6m7j9njldwwzlg9v7v53unlr4jkmx6eylep{uuid.uuid4().hex[:8]}"
    
    try:
        registration_data = {
            "wallet_address": partial_address,
            "fullName": "Partial PMA Member",
            "email": "partial@bitcoinben.com",
            "phone": "+1-555-PARTIAL",
            "pma_agreed": True,   # Agreement signed
            "dues_paid": False,   # But no dues paid
            "payment_amount": 0.0
        }
        
        reg_response = session.post(f"{base_url}/api/debug/register", json=registration_data)
        if reg_response.status_code == 200:
            print(f"✅ Created partial PMA member: {partial_address}")
        else:
            print(f"❌ Failed to create partial PMA member: {reg_response.status_code}")
    except Exception as e:
        print(f"❌ Error creating partial PMA member: {str(e)}")
    
    result2 = test_scenario(
        "PMA Agreed but No Dues Paid",
        partial_address,
        expected_pma_agreed=True,
        expected_dues_paid=False,
        expected_order_status=403
    )
    test_results.append(("Partial PMA Test", result2))
    
    # Scenario 3: Register a member with complete PMA status
    complete_address = f"bitcoincash:qr6m7j9njldwwzlg9v7v53unlr4jkmx6eylep{uuid.uuid4().hex[:8]}"
    
    try:
        registration_data = {
            "wallet_address": complete_address,
            "fullName": "Complete PMA Member",
            "email": "complete@bitcoinben.com",
            "phone": "+1-555-COMPLETE",
            "pma_agreed": True,   # Agreement signed
            "dues_paid": True,    # Dues paid
            "payment_amount": 21.0
        }
        
        reg_response = session.post(f"{base_url}/api/debug/register", json=registration_data)
        if reg_response.status_code == 200:
            print(f"✅ Created complete PMA member: {complete_address}")
        else:
            print(f"❌ Failed to create complete PMA member: {reg_response.status_code}")
    except Exception as e:
        print(f"❌ Error creating complete PMA member: {str(e)}")
    
    # First seed menu data to ensure we have items
    try:
        seed_response = session.post(f"{base_url}/api/admin/seed-data")
        if seed_response.status_code == 200:
            print("✅ Menu data seeded for complete PMA test")
    except Exception as e:
        print(f"⚠️  Could not seed menu data: {str(e)}")
    
    result3 = test_scenario(
        "Complete PMA Status",
        complete_address,
        expected_pma_agreed=True,
        expected_dues_paid=True,
        expected_order_status=200
    )
    test_results.append(("Complete PMA Test", result3))
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 PMA VALIDATION TEST SUMMARY")
    print("=" * 80)
    
    total_tests = len(test_results)
    passed_tests = sum(1 for _, result in test_results if result)
    failed_tests = total_tests - passed_tests
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests} ✅")
    print(f"Failed: {failed_tests} ❌")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if failed_tests > 0:
        print("\n🔍 FAILED TESTS:")
        for test_name, result in test_results:
            if not result:
                print(f"  ❌ {test_name}")
    
    print("\n✅ PASSED TESTS:")
    for test_name, result in test_results:
        if result:
            print(f"  ✅ {test_name}")

if __name__ == "__main__":
    main()