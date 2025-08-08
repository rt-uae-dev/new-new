#!/usr/bin/env python3
"""
Test script to simulate email parser processing of existing email bodies.
"""

import sys
import os
import json
import email
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from email_parser import extract_sender_info, extract_person_name_from_email

def create_mock_email_message(email_body, from_header):
    """
    Create a mock email message object to test sender extraction.
    """
    class MockMessage:
        def __init__(self, body, from_field):
            self.body = body
            self.from_field = from_field
        
        def get(self, field, default=''):
            if field == 'From':
                return self.from_field
            return default
        
        def is_multipart(self):
            return False
        
        def get_payload(self, decode=True):
            return self.body.encode('utf-8')
    
    return MockMessage(email_body, from_header)

def test_email_parser_reprocessing():
    """Test reprocessing existing email bodies with the email parser logic."""
    
    print("🧪 Testing email parser reprocessing of existing email bodies...")
    print("-" * 60)
    
    downloads_dir = "data/raw/downloads"
    
    if not os.path.exists(downloads_dir):
        print(f"❌ Downloads directory not found: {downloads_dir}")
        return
    
    folders = [f for f in os.listdir(downloads_dir) if os.path.isdir(os.path.join(downloads_dir, f))]
    
    for folder in folders:
        print(f"\n🔍 Reprocessing folder: {folder}")
        
        folder_path = os.path.join(downloads_dir, folder)
        email_body_path = os.path.join(folder_path, "email_body.txt")
        
        if os.path.exists(email_body_path):
            with open(email_body_path, "r", encoding="utf-8") as f:
                email_body = f.read()
            
            print(f"   📧 Email body length: {len(email_body)} characters")
            
            # Try to extract sender info from email body content
            # Look for "From:" patterns in the email body
            import re
            from_patterns = [
                r'From:\s*([^<\n]+?)\s*<([^>]+)>',  # "From: Name <email@domain.com>"
                r'From:\s*([^\n]+@[^\n]+)',  # "From: email@domain.com"
            ]
            
            extracted_from = None
            for pattern in from_patterns:
                matches = re.findall(pattern, email_body, re.IGNORECASE)
                if matches:
                    if len(matches[0]) == 2:  # Name and email
                        name = matches[0][0].strip().strip('"')
                        email_addr = matches[0][1].strip()
                        extracted_from = f"{name} <{email_addr}>"
                        break
                    elif len(matches[0]) == 1:  # Just email
                        email_addr = matches[0].strip()
                        extracted_from = email_addr
                        break
            
            if extracted_from:
                print(f"   🔍 Found From header in email body: {extracted_from}")
                
                # Create mock email message
                mock_msg = create_mock_email_message(email_body, extracted_from)
                
                # Extract sender info using the email parser logic
                sender_info = extract_sender_info(mock_msg)
                
                print(f"   👤 Extracted sender info:")
                print(f"      Name: {sender_info['name']}")
                print(f"      Email: {sender_info['email']}")
                print(f"      Person Name: {sender_info['person_name']}")
                
                # Save the sender info
                sender_path = os.path.join(folder_path, "sender_info.json")
                with open(sender_path, "w", encoding="utf-8") as f:
                    json.dump(sender_info, f, ensure_ascii=False, indent=2)
                print(f"   ✅ Saved sender info: {sender_path}")
                
            else:
                print(f"   ⚠️ No From header found in email body")
                print(f"   📝 Using default sender info")
                
                # Use default sender info
                sender_info = {
                    'email': 'Unknown',
                    'name': 'Unknown',
                    'person_name': 'Unknown'
                }
                
                # Save the default sender info
                sender_path = os.path.join(folder_path, "sender_info.json")
                with open(sender_path, "w", encoding="utf-8") as f:
                    json.dump(sender_info, f, ensure_ascii=False, indent=2)
                print(f"   ✅ Saved default sender info: {sender_path}")
        else:
            print(f"   ❌ No email body found")
    
    print("\n" + "=" * 60)
    print("✅ Email parser reprocessing test completed!")

if __name__ == "__main__":
    test_email_parser_reprocessing()
