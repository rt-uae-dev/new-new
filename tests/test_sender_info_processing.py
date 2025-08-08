#!/usr/bin/env python3
"""
Test script to process sender information from existing folders.
"""

import sys
import os
import json
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from email_parser import extract_person_name_from_email, extract_sender_info

def test_sender_info_processing():
    """Test processing sender information from existing folders."""
    
    print("🧪 Testing sender info processing from existing folders...")
    print("-" * 60)
    
    # Check existing folders in downloads
    downloads_dir = "data/raw/downloads"
    completed_dir = "data/processed/COMPLETED"
    
    if not os.path.exists(downloads_dir):
        print(f"❌ Downloads directory not found: {downloads_dir}")
        return
    
    folders = [f for f in os.listdir(downloads_dir) if os.path.isdir(os.path.join(downloads_dir, f))]
    
    print(f"📁 Found {len(folders)} folders in downloads directory:")
    
    for folder in folders:
        print(f"\n🔍 Processing folder: {folder}")
        
        folder_path = os.path.join(downloads_dir, folder)
        email_body_path = os.path.join(folder_path, "email_body.txt")
        sender_info_path = os.path.join(folder_path, "sender_info.json")
        
        # Check if email body exists
        if os.path.exists(email_body_path):
            print(f"   ✅ Email body found: {email_body_path}")
            
            # Read email body
            with open(email_body_path, "r", encoding="utf-8") as f:
                email_body = f.read()
            print(f"   📧 Email body length: {len(email_body)} characters")
            
            # Check if sender info exists
            if os.path.exists(sender_info_path):
                print(f"   ✅ Sender info found: {sender_info_path}")
                try:
                    with open(sender_info_path, "r", encoding="utf-8") as f:
                        sender_info = json.load(f)
                    print(f"   👤 Sender: {sender_info.get('person_name', 'Unknown')} ({sender_info.get('email', 'Unknown')})")
                except Exception as e:
                    print(f"   ❌ Error reading sender info: {e}")
            else:
                print(f"   ⚠️ No sender_info.json found, would use default values")
                sender_info = {
                    'email': 'Unknown',
                    'name': 'Unknown',
                    'person_name': 'Unknown'
                }
        else:
            print(f"   ❌ No email body found")
            sender_info = {
                'email': 'Unknown',
                'name': 'Unknown',
                'person_name': 'Unknown'
            }
        
        # Check if folder is already in completed directory
        completed_folder_path = os.path.join(completed_dir, folder)
        if os.path.exists(completed_folder_path):
            print(f"   📂 Folder exists in completed directory")
            
            # Check for complete details file
            complete_files = [f for f in os.listdir(completed_folder_path) if f.endswith('_COMPLETE_DETAILS.txt')]
            if complete_files:
                print(f"   ✅ Found {len(complete_files)} complete detail files")
                
                # Read the complete details file to see current sender info
                complete_file_path = os.path.join(completed_folder_path, complete_files[0])
                try:
                    with open(complete_file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    # Check if sender info is already in the file
                    if "EMAIL SENDER INFORMATION" in content:
                        print(f"   📧 Sender information already present in complete details file")
                    else:
                        print(f"   ⚠️ Sender information missing from complete details file")
                        
                        # Show what would be added
                        print(f"   📝 Would add sender info:")
                        print(f"      Sender Name: {sender_info.get('name', 'Unknown')}")
                        print(f"      Sender Email: {sender_info.get('email', 'Unknown')}")
                        print(f"      Extracted Person Name: {sender_info.get('person_name', 'Unknown')}")
                except Exception as e:
                    print(f"   ❌ Error reading complete details file: {e}")
            else:
                print(f"   ⚠️ No complete detail files found")
        else:
            print(f"   📂 Folder not yet in completed directory")
    
    print("\n" + "=" * 60)
    print("✅ Sender info processing test completed!")

if __name__ == "__main__":
    test_sender_info_processing()

