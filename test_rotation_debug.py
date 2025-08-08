#!/usr/bin/env python3
"""
Debug script to test rotation logic with Haneen's passport
"""

import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_rotation():
    """Test rotation with Haneen's passport image"""
    
    # Test with Haneen's actual passport file
    test_image = "data/processed/COMPLETED/Outside Country Mission Visa Application  Haneen Kamil Malik  WAM/HANEEN_passport_1.jpg"
    
    if not os.path.exists(test_image):
        print(f"❌ Test image not found: {test_image}")
        return
    
    print(f"🧪 Testing rotation with Haneen's passport: {os.path.basename(test_image)}")
    
    try:
        from simple_gemini_rotation import ask_gemini_if_needs_rotation, rotate_if_needed
        
        # First, just ask Gemini what it thinks
        print("\n🔍 Step 1: Asking Gemini if rotation is needed...")
        result = ask_gemini_if_needs_rotation(test_image, is_passport_page=True)
        print(f"Result: {result}")
        
        # Then try the full rotation
        print("\n🔄 Step 2: Trying full rotation...")
        rotated_path = rotate_if_needed(test_image, is_passport_page=True)
        print(f"Final result path: {rotated_path}")
        
        if rotated_path != test_image:
            print(f"✅ Rotation was applied: {os.path.basename(rotated_path)}")
        else:
            print(f"⏭️ No rotation was needed")
            
    except Exception as e:
        print(f"❌ Error testing rotation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_rotation()
