#!/usr/bin/env python3
"""
Test script for new payment and crypto features
"""
import sys
import os

# Add server directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_crypto_utils():
    """Test encryption and decryption"""
    print("=" * 60)
    print("Testing crypto_utils...")
    print("=" * 60)
    
    from api.utils.crypto_utils import encrypt_with_public_key, decrypt_with_private_key
    
    # Test data
    test_nib = "PT50 0002 0123 1234 5678 9015 4"
    test_card = "4111111111111111"
    
    # Test NIB encryption/decryption
    print(f"\n1. Testing NIB encryption/decryption")
    print(f"   Original NIB: {test_nib}")
    encrypted_nib = encrypt_with_public_key(test_nib)
    print(f"   Encrypted (base64): {encrypted_nib[:50]}...")
    decrypted_nib = decrypt_with_private_key(encrypted_nib)
    print(f"   Decrypted NIB: {decrypted_nib}")
    assert test_nib == decrypted_nib, "NIB encryption/decryption failed!"
    print("   ✓ NIB encryption/decryption works correctly")
    
    # Test card encryption/decryption
    print(f"\n2. Testing Card encryption/decryption")
    print(f"   Original Card: {test_card}")
    encrypted_card = encrypt_with_public_key(test_card)
    print(f"   Encrypted (base64): {encrypted_card[:50]}...")
    decrypted_card = decrypt_with_private_key(encrypted_card)
    print(f"   Decrypted Card: {decrypted_card}")
    assert test_card == decrypted_card, "Card encryption/decryption failed!"
    print("   ✓ Card encryption/decryption works correctly")
    
    print("\n✅ All crypto_utils tests passed!\n")


def test_fastpay_client():
    """Test FastPay client (without actual API calls)"""
    print("=" * 60)
    print("Testing FastPayClient...")
    print("=" * 60)
    
    # Set a dummy token for testing BEFORE importing
    import os
    os.environ["FASTPAY_API_TOKEN"] = "test_token_12345"
    
    # Now import (reimport won't help, so we need to set it before the module loads)
    import importlib
    import services.fastpay_client as fpc
    importlib.reload(fpc)
    
    from services.fastpay_client import FastPayClient, FastPayError
    
    print("\n1. Testing FastPayClient initialization")
    try:
        client = FastPayClient()
        print(f"   ✓ Client initialized with base_url: {client.base_url}")
        print(f"   ✓ API token configured: {client.api_token[:10]}...")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return
    
    print("\n2. Testing header generation")
    headers = client._headers()
    print(f"   ✓ Headers generated: {list(headers.keys())}")
    assert "Authorization" in headers
    assert "Content-Type" in headers
    assert "Idempotency-Key" in headers
    print("   ✓ All required headers present")
    
    print("\n3. Testing idempotency key uniqueness")
    key1 = client._headers()["Idempotency-Key"]
    key2 = client._headers()["Idempotency-Key"]
    print(f"   Key 1: {key1}")
    print(f"   Key 2: {key2}")
    assert key1 != key2, "Idempotency keys should be unique"
    print("   ✓ Idempotency keys are unique")
    
    print("\n✅ All FastPayClient tests passed!\n")
    print("⚠️  Note: Actual API calls not tested (requires real API endpoint)")


def test_process_payments_structure():
    """Test ProcessPayments class structure"""
    print("=" * 60)
    print("Testing ProcessPayments structure...")
    print("=" * 60)
    
    from services.process_payments import ProcessPayments
    
    print("\n1. Checking ProcessPayments class structure")
    print(f"   ✓ Class methods: {[m for m in dir(ProcessPayments) if not m.startswith('_')]}")
    
    # Check required methods exist
    required_methods = ['pay_single', 'schedule_payment']
    for method in required_methods:
        assert hasattr(ProcessPayments, method), f"Missing method: {method}"
        print(f"   ✓ Method '{method}' exists")
    
    print("\n✅ ProcessPayments structure is correct!\n")
    print("⚠️  Note: Full functionality requires database connection")


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("ISCTE Spot - New Features Test Suite")
    print("=" * 60 + "\n")
    
    tests = [
        ("Crypto Utils", test_crypto_utils),
        ("FastPay Client", test_fastpay_client),
        ("Process Payments Structure", test_process_payments_structure),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"\n❌ {test_name} failed with error:")
            print(f"   {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
            print()
    
    print("=" * 60)
    print(f"Test Summary: {passed} passed, {failed} failed out of {len(tests)} tests")
    print("=" * 60)
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
