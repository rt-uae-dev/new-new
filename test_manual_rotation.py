#!/usr/bin/env python3
"""
Test script to manually apply rotation to Haneen's passport
"""

import os
import sys
sys.path.append('src')

def test_manual_rotation():
    """Manually apply rotation to Haneen's passport"""
    
    print("🧪 Testing Manual Rotation for Haneen's Passport")
    print("=" * 50)
    
    # Haneen's passport file
    haneen_passport_path = "data/processed/COMPLETED/Outside Country Mission Visa Application  Haneen Kamil Malik  WAM/HANEEN_passport_1.jpg"
    
    if os.path.exists(haneen_passport_path):
        print(f"📄 Found Haneen's passport: {haneen_passport_path}")
        
        # Test the full rotation function
        from simple_gemini_rotation import rotate_if_needed
        
        print("🔄 Applying rotation using the full function...")
        result_path = rotate_if_needed(haneen_passport_path, is_passport_page=True)
        
        print(f"📊 Result path: {result_path}")
        print(f"📊 Original path: {haneen_passport_path}")
        
        if result_path != haneen_passport_path:
            print("✅ Rotation was applied - file was modified")
        else:
            print("❌ No rotation was applied - file unchanged")
            
        # Test the rotation detection again
        from simple_gemini_rotation import ask_gemini_if_needs_rotation
        print("\n🔍 Testing rotation detection after manual rotation...")
        result = ask_gemini_if_needs_rotation(haneen_passport_path, is_passport_page=True)
        
        print(f"📊 After rotation, Gemini says:")
        print(f"   Rotation needed: {result['rotation_needed']}")
        print(f"   Rotation angle: {result['rotation_angle']}")
        print(f"   Reason: {result['reason']}")
        
        if not result['rotation_needed']:
            print("✅ SUCCESS: Passport is now correctly oriented!")
        else:
            print("❌ FAILED: Passport still needs rotation")
            
    else:
        print(f"❌ Haneen's passport not found: {haneen_passport_path}")

if __name__ == "__main__":
    test_manual_rotation()
