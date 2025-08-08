#!/usr/bin/env python3
"""
Test script to analyze email bodies and extract sender information.
"""

import sys
import os
import re
import json
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from email_parser import extract_person_name_from_email

def extract_sender_from_email_body(email_body):
    """
    Try to extract sender information from email body content.
    This is a fallback when we don't have access to email headers.
    """
    sender_info = {
        'email': 'Unknown',
        'name': 'Unknown',
        'person_name': 'Unknown'
    }
    
    # Look for "From:" lines in the email body
    from_patterns = [
        r'From:\s*([^<\n]+?)\s*<([^>]+)>',  # "From: Name <email@domain.com>"
        r'From:\s*([^\n]+@[^\n]+)',  # "From: email@domain.com"
        r'From\s+([^<\n]+?)\s+<([^>]+)>',  # "From Name <email@domain.com>"
    ]
    
    for pattern in from_patterns:
        matches = re.findall(pattern, email_body, re.IGNORECASE)
        if matches:
            if len(matches[0]) == 2:  # Name and email
                name = matches[0][0].strip().strip('"')
                email = matches[0][1].strip()
                sender_info['name'] = name
                sender_info['email'] = email
                sender_info['person_name'] = extract_person_name_from_email(email)
                break
            elif len(matches[0]) == 1:  # Just email
                email = matches[0].strip()
                sender_info['email'] = email
                sender_info['person_name'] = extract_person_name_from_email(email)
                break
    
    return sender_info

def test_email_header_extraction():
    """Test extracting sender information from email bodies."""
    
    print("🧪 Testing email header extraction from email bodies...")
    print("-" * 60)
    
    downloads_dir = "data/raw/downloads"
    
    if not os.path.exists(downloads_dir):
        print(f"❌ Downloads directory not found: {downloads_dir}")
        return
    
    folders = [f for f in os.listdir(downloads_dir) if os.path.isdir(os.path.join(downloads_dir, f))]
    
    for folder in folders:
        print(f"\n🔍 Analyzing folder: {folder}")
        
        folder_path = os.path.join(downloads_dir, folder)
        email_body_path = os.path.join(folder_path, "email_body.txt")
        
        if os.path.exists(email_body_path):
            with open(email_body_path, "r", encoding="utf-8") as f:
                email_body = f.read()
            
            print(f"   📧 Email body length: {len(email_body)} characters")
            
            # Extract sender info from email body
            sender_info = extract_sender_from_email_body(email_body)
            
            print(f"   👤 Extracted sender info:")
            print(f"      Name: {sender_info['name']}")
            print(f"      Email: {sender_info['email']}")
            print(f"      Person Name: {sender_info['person_name']}")
            
            # Show the first few lines of the email to understand the structure
            lines = email_body.split('\n')[:10]
            print(f"   📝 First 10 lines of email:")
            for i, line in enumerate(lines, 1):
                print(f"      {i:2d}: {line}")
            
            # Look for any "From:" patterns in the entire email
            from_lines = re.findall(r'From:.*', email_body, re.IGNORECASE)
            if from_lines:
                print(f"   🔍 Found 'From:' lines in email:")
                for line in from_lines:
                    print(f"      {line.strip()}")
            else:
                print(f"   ⚠️ No 'From:' lines found in email body")
        else:
            print(f"   ❌ No email body found")
    
    print("\n" + "=" * 60)
    print("✅ Email header extraction test completed!")

if __name__ == "__main__":
    test_email_header_extraction()
