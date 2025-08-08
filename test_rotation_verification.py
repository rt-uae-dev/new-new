#!/usr/bin/env python3
"""
Test script to verify rotation was successful
"""

import os
import sys
sys.path.append('src')

def test_rotation_verification():
    """Verify that the rotation was successful"""
    
    print("🧪 Verifying Rotation Success")
    print("=" * 50)
    
    # Haneen's passport file
    haneen_passport_path = "data/processed/COMPLETED/Outside Country Mission Visa Application  Haneen Kamil Malik  WAM/HANEEN_passport_1.jpg"
    
    if os.path.exists(haneen_passport_path):
        print(f"📄 Found Haneen's passport: {haneen_passport_path}")
        
        # Test both detection methods
        from simple_gemini_rotation import ask_gemini_if_needs_rotation, simple_text_orientation_detection
        
        print("🔍 Testing Gemini detection...")
        gemini_result = ask_gemini_if_needs_rotation(haneen_passport_path, is_passport_page=True)
        
        print("🔍 Testing fallback detection...")
        fallback_result = simple_text_orientation_detection(haneen_passport_path)
        
        print(f"\n📊 Results:")
        print(f"   Gemini says: {gemini_result['rotation_needed']} (angle: {gemini_result['rotation_angle']})")
        print(f"   Fallback says: {fallback_result['rotation_needed']} (angle: {fallback_result['rotation_angle']})")
        
        if not gemini_result['rotation_needed'] and not fallback_result['rotation_needed']:
            print("✅ SUCCESS: Both methods confirm the passport is now correctly oriented!")
            print("✅ The manual rotation we applied earlier was successful!")
        else:
            print("❌ FAILED: One or both methods still detect rotation needed")
            
        # Check file modification time to confirm it was changed
        import time
        file_time = os.path.getmtime(haneen_passport_path)
        file_time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(file_time))
        print(f"\n📅 File last modified: {file_time_str}")
        
    else:
        print(f"❌ Haneen's passport not found: {haneen_passport_path}")

if __name__ == "__main__":
    test_rotation_verification()
