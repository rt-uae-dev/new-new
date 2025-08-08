#!/usr/bin/env python3
"""
Test script to check Haneen's passport rotation issue
"""

import os
import sys
sys.path.append('src')

def test_haneen_rotation():
    """Test Haneen's passport rotation"""
    
    print("🧪 Testing Haneen's Passport Rotation")
    print("=" * 50)
    
    # Check the processed Haneen passport file
    haneen_passport_path = "data/processed/COMPLETED/Outside Country Mission Visa Application  Haneen Kamil Malik  WAM/HANEEN_passport_1.jpg"
    
    if os.path.exists(haneen_passport_path):
        print(f"📄 Found Haneen's passport: {haneen_passport_path}")
        
        # Test the rotation logic on this file
        from simple_gemini_rotation import ask_gemini_if_needs_rotation
        
        print("🔍 Testing Gemini rotation detection...")
        result = ask_gemini_if_needs_rotation(haneen_passport_path, is_passport_page=True)
        
        print(f"📊 Gemini says:")
        print(f"   Rotation needed: {result['rotation_needed']}")
        print(f"   Rotation angle: {result['rotation_angle']}")
        print(f"   Reason: {result['reason']}")
        
        if not result['rotation_needed']:
            print("❌ PROBLEM: Gemini says no rotation needed, but the passport is upside down!")
            print("🔍 This suggests the Gemini prompt might not be working correctly for this specific image")
            
            # Let's also test the fallback text-based detection
            from simple_gemini_rotation import simple_text_orientation_detection
            print("\n🔍 Testing fallback text-based detection...")
            fallback_result = simple_text_orientation_detection(haneen_passport_path)
            
            print(f"📊 Fallback says:")
            print(f"   Rotation needed: {fallback_result['rotation_needed']}")
            print(f"   Rotation angle: {fallback_result['rotation_angle']}")
            print(f"   Reason: {fallback_result['reason']}")
            
            if fallback_result['rotation_needed']:
                print("✅ Fallback detection works! The issue is with Gemini's passport prompt")
            else:
                print("❌ Both Gemini and fallback failed to detect rotation")
        else:
            print("✅ Gemini correctly detected rotation needed")
            
    else:
        print(f"❌ Haneen's passport not found: {haneen_passport_path}")
        
        # Check if there are other Haneen files
        haneen_dir = "data/processed/COMPLETED/Outside Country Mission Visa Application Haneen Kamil Malik WAM"
        if os.path.exists(haneen_dir):
            print(f"📁 Found Haneen directory: {haneen_dir}")
            files = os.listdir(haneen_dir)
            passport_files = [f for f in files if "passport" in f.lower()]
            print(f"📄 Passport files found: {passport_files}")
            
            if passport_files:
                test_file = os.path.join(haneen_dir, passport_files[0])
                print(f"🔍 Testing with: {test_file}")
                
                from simple_gemini_rotation import ask_gemini_if_needs_rotation
                result = ask_gemini_if_needs_rotation(test_file, is_passport_page=True)
                
                print(f"📊 Gemini says:")
                print(f"   Rotation needed: {result['rotation_needed']}")
                print(f"   Rotation angle: {result['rotation_angle']}")
                print(f"   Reason: {result['reason']}")

if __name__ == "__main__":
    test_haneen_rotation()
