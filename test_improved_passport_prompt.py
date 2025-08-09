#!/usr/bin/env python3
"""
Test the improved passport rotation prompt with Haneen's passport
"""

import os
import sys
from pathlib import Path

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from simple_gemini_rotation import ask_gemini_if_needs_rotation

def test_haneen_passport_with_improved_prompt():
    """Test the improved prompt with Haneen's passport"""
    
    # Look for Haneen's processed passport
    processed_dir = "data/processed/COMPLETED"
    haneen_folder = None
    
    # Find Haneen's folder
    if os.path.exists(processed_dir):
        for folder in os.listdir(processed_dir):
            if "haneen" in folder.lower():
                haneen_folder = os.path.join(processed_dir, folder)
                break
    
    if not haneen_folder or not os.path.exists(haneen_folder):
        print("❌ Haneen's processed folder not found")
        return
    
    print(f"🧪 Testing Improved Passport Rotation Prompt")
    print("=" * 60)
    print(f"📁 Testing with folder: {os.path.basename(haneen_folder)}")
    print()
    
    # Look for passport images
    passport_files = []
    for file in os.listdir(haneen_folder):
        if "passport" in file.lower() and file.endswith('.jpg'):
            passport_files.append(os.path.join(haneen_folder, file))
    
    if not passport_files:
        print("❌ No passport images found in Haneen's folder")
        return
    
    print(f"📄 Found {len(passport_files)} passport file(s):")
    for passport_file in passport_files:
        print(f"   • {os.path.basename(passport_file)}")
    print()
    
    # Test each passport file
    for passport_file in passport_files:
        print(f"🔍 Testing: {os.path.basename(passport_file)}")
        print("-" * 50)
        
        try:
            print("📝 NEW PROMPT:")
            print("   'Is this passport oriented properly? If not, how many degrees clockwise do I need to turn it?'")
            print("   'Answer: 0, 90, 180, or 270'")
            print()
            
            result = ask_gemini_if_needs_rotation(passport_file, is_passport_page=True)
            
            print(f"🤖 Gemini Response:")
            print(f"   Rotation needed: {result['rotation_needed']}")
            print(f"   Rotation angle: {result['rotation_angle']}°")
            print(f"   Reason: {result['reason']}")
            print()
            
            if result['rotation_needed']:
                print(f"🔄 ACTION: Will rotate {result['rotation_angle']}° clockwise")
            else:
                print(f"✅ ACTION: Keep original orientation")
            
        except Exception as e:
            print(f"❌ Error testing {os.path.basename(passport_file)}: {e}")
        
        print()

if __name__ == "__main__":
    test_haneen_passport_with_improved_prompt()
