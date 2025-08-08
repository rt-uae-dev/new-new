#!/usr/bin/env python3
"""
Test script for email parser integration with sender information.
"""

import sys
import os
import json
import tempfile
import shutil
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from email_parser import extract_person_name_from_email, extract_sender_info, save_email_body

def test_email_parser_integration():
    """Test the complete email parser integration with sender information."""
    
    # Mock email message for testing
    class MockMessage:
        def __init__(self, from_field, subject="Test Subject"):
            self.from_field = from_field
            self.subject = subject
        
        def get(self, field, default=''):
            if field == 'From':
                return self.from_field
            elif field == 'Subject':
                return self.subject
            return default
        
        def is_multipart(self):
            return False
        
        def get_payload(self, decode=True):
            return b"Test email body content"
    
    print("🧪 Testing email parser integration...")
    print("-" * 50)
    
    # Test cases
    test_cases = [
        ('"Hasan Altelly" <hasan.altelly@gmail.com>', 'Test Subject 1'),
        ('John Doe <john.doe@company.com>', 'Test Subject 2'),
        ('mary.jane@example.org', 'Test Subject 3'),
        ('"First Middle Last" <first.middle.last@domain.co.uk>', 'Test Subject 4'),
    ]
    
    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        original_download_dir = os.getenv("DOWNLOAD_DIR", "data/raw/downloads")
        
        # Temporarily set download directory
        os.environ["DOWNLOAD_DIR"] = temp_dir
        
        for from_field, subject in test_cases:
            print(f"\n📧 Testing: {from_field}")
            print(f"   Subject: {subject}")
            
            # Create mock message
            msg = MockMessage(from_field, subject)
            
            # Test sender info extraction
            sender_info = extract_sender_info(msg)
            print(f"   ✅ Sender Info: {sender_info}")
            
            # Test save_email_body function
            try:
                body_path, saved_sender_info = save_email_body(msg, "test_subject")
                print(f"   ✅ Email body saved: {body_path}")
                print(f"   ✅ Sender info saved: {saved_sender_info}")
                
                # Verify files were created
                if os.path.exists(body_path):
                    print(f"   ✅ Email body file exists")
                else:
                    print(f"   ❌ Email body file missing")
                
                sender_file = os.path.join(temp_dir, "test_subject", "sender_info.json")
                if os.path.exists(sender_file):
                    print(f"   ✅ Sender info file exists")
                    # Read and verify content
                    with open(sender_file, 'r', encoding='utf-8') as f:
                        saved_data = json.load(f)
                    print(f"   ✅ Sender info content: {saved_data}")
                else:
                    print(f"   ❌ Sender info file missing")
                    
            except Exception as e:
                print(f"   ❌ Error saving email: {e}")
        
        # Restore original download directory
        os.environ["DOWNLOAD_DIR"] = original_download_dir
    
    print("\n" + "=" * 50)
    print("✅ Email parser integration test completed!")

if __name__ == "__main__":
    test_email_parser_integration()
