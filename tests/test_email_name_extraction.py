#!/usr/bin/env python3
"""
Test script for email name extraction functionality.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from email_parser import extract_person_name_from_email, extract_sender_info

def test_email_name_extraction():
    """Test the email name extraction function with various email formats."""
    
    test_cases = [
        ("hasan.altelly@gmail.com", "Hasan Altelly"),
        ("john.doe@company.com", "John Doe"),
        ("mary_jane@example.org", "Mary Jane"),
        ("singleword@test.com", "Singleword"),
        ("first.middle.last@domain.co.uk", "First Middle Last"),
        ("user123@test.com", "User123"),
        ("", "Unknown"),
        (None, "Unknown"),
    ]
    
    print("🧪 Testing email name extraction...")
    print("-" * 50)
    
    for email_address, expected_name in test_cases:
        result = extract_person_name_from_email(email_address)
        status = "✅" if result == expected_name else "❌"
        print(f"{status} {email_address} -> {result} (expected: {expected_name})")
    
    print("\n" + "=" * 50)
    print("✅ Email name extraction test completed!")

def test_sender_info_extraction():
    """Test the sender info extraction function."""
    
    # Mock email message for testing
    class MockMessage:
        def __init__(self, from_field):
            self.from_field = from_field
        
        def get(self, field, default=''):
            if field == 'From':
                return self.from_field
            return default
    
    test_cases = [
        ('"Hasan Altelly" <hasan.altelly@gmail.com>', 'Hasan Altelly', 'hasan.altelly@gmail.com'),
        ('John Doe <john.doe@company.com>', 'John Doe', 'john.doe@company.com'),
        ('mary.jane@example.org', '', 'mary.jane@example.org'),
        ('"First Middle Last" <first.middle.last@domain.co.uk>', 'First Middle Last', 'first.middle.last@domain.co.uk'),
    ]
    
    print("\n🧪 Testing sender info extraction...")
    print("-" * 50)
    
    for from_field, expected_name, expected_email in test_cases:
        msg = MockMessage(from_field)
        result = extract_sender_info(msg)
        
        name_correct = result['name'] == expected_name
        email_correct = result['email'] == expected_email
        person_name_correct = result['person_name'] == extract_person_name_from_email(expected_email)
        
        status = "✅" if name_correct and email_correct and person_name_correct else "❌"
        print(f"{status} From: {from_field}")
        print(f"   Name: {result['name']} (expected: {expected_name})")
        print(f"   Email: {result['email']} (expected: {expected_email})")
        print(f"   Person Name: {result['person_name']}")
        print()
    
    print("=" * 50)
    print("✅ Sender info extraction test completed!")

if __name__ == "__main__":
    test_email_name_extraction()
    test_sender_info_extraction()
