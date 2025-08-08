#!/usr/bin/env python3
"""
Test script for folder processing check functionality.
"""

import sys
import os
import tempfile
import shutil
import json
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_folder_processing_check():
    """Test the folder processing check logic."""
    
    print("🧪 Testing folder processing check...")
    print("-" * 50)
    
    # Create temporary directories for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test structure
        downloads_dir = os.path.join(temp_dir, "downloads")
        completed_dir = os.path.join(temp_dir, "completed")
        
        os.makedirs(downloads_dir, exist_ok=True)
        os.makedirs(completed_dir, exist_ok=True)
        
        # Test case 1: New folder (should be processed)
        new_folder = os.path.join(downloads_dir, "new_folder")
        os.makedirs(new_folder, exist_ok=True)
        
        # Test case 2: Completed folder with master text file (should be skipped)
        completed_folder = os.path.join(completed_dir, "completed_folder")
        os.makedirs(completed_folder, exist_ok=True)
        master_text_file = os.path.join(completed_folder, "John_COMPLETE_DETAILS.txt")
        with open(master_text_file, 'w') as f:
            f.write("Test complete details")
        
        # Test case 3: Incomplete folder in completed directory (should be reprocessed)
        incomplete_folder = os.path.join(completed_dir, "incomplete_folder")
        os.makedirs(incomplete_folder, exist_ok=True)
        # Create some files but no master text file
        with open(os.path.join(incomplete_folder, "some_file.txt"), 'w') as f:
            f.write("Some content")
        
        # Test case 4: Folder in downloads that matches completed folder name
        downloads_completed_folder = os.path.join(downloads_dir, "completed_folder")
        os.makedirs(downloads_completed_folder, exist_ok=True)
        with open(os.path.join(downloads_completed_folder, "email_body.txt"), 'w') as f:
            f.write("Test email body")
        
        # Test case 5: Folder in downloads that matches incomplete folder name
        downloads_incomplete_folder = os.path.join(downloads_dir, "incomplete_folder")
        os.makedirs(downloads_incomplete_folder, exist_ok=True)
        with open(os.path.join(downloads_incomplete_folder, "email_body.txt"), 'w') as f:
            f.write("Test email body")
        
        print("📁 Test directory structure created:")
        print(f"   Downloads: {downloads_dir}")
        print(f"   Completed: {completed_dir}")
        
        # Simulate the folder processing check logic
        processed_folders = set()
        
        def should_process_folder(folder_name):
            """Simulate the folder processing check logic."""
            # Check if already processed in this session
            if folder_name in processed_folders:
                print(f"   ⏭️ {folder_name}: Already processed in this session")
                return False
            
            # Check if folder exists in completed directory
            completed_folder_path = os.path.join(completed_dir, folder_name)
            if os.path.exists(completed_folder_path):
                # Check if the master text file exists (indicating complete processing)
                master_text_files = [f for f in os.listdir(completed_folder_path) if f.endswith('_COMPLETE_DETAILS.txt')]
                if master_text_files:
                    print(f"   ⏭️ {folder_name}: Already processed (found {len(master_text_files)} complete detail files)")
                    processed_folders.add(folder_name)
                    return False
                else:
                    print(f"   ⚠️ {folder_name}: Found incomplete folder, will reprocess")
                    # Remove the incomplete folder to allow reprocessing
                    try:
                        shutil.rmtree(completed_folder_path)
                        print(f"   🗑️ Removed incomplete folder: {completed_folder_path}")
                        return True
                    except Exception as e:
                        print(f"   ❌ Could not remove incomplete folder: {e}")
                        return False
            
            print(f"   ✅ {folder_name}: New folder, will process")
            return True
        
        # Test each folder
        test_folders = ["new_folder", "completed_folder", "incomplete_folder"]
        
        print("\n🔍 Testing folder processing decisions:")
        for folder in test_folders:
            should_process = should_process_folder(folder)
            status = "✅ WILL PROCESS" if should_process else "⏭️ WILL SKIP"
            print(f"   {status}: {folder}")
        
        # Verify the incomplete folder was removed
        if not os.path.exists(incomplete_folder):
            print(f"   ✅ Incomplete folder was successfully removed")
        else:
            print(f"   ❌ Incomplete folder still exists")
        
        print("\n" + "=" * 50)
        print("✅ Folder processing check test completed!")

if __name__ == "__main__":
    test_folder_processing_check()

