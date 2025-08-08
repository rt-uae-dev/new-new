#!/usr/bin/env python3
"""
Test script to check the original Haneen passport before processing
"""

import os
import sys
sys.path.append('src')

def test_original_haneen_passport():
    """Test the original Haneen passport file"""
    
    print("🧪 Testing Original Haneen Passport")
    print("=" * 50)
    
    # Original Haneen passport file
    original_passport_path = "data/raw/downloads/Outside Country Mission Visa Application  Haneen Kamil Malik  WAM/Passport.pdf"
    
    if os.path.exists(original_passport_path):
        print(f"📄 Found original Haneen passport: {original_passport_path}")
        
        # Convert PDF to image first
        from pdf_converter import convert_pdf_to_jpg
        temp_dir = "data/temp"
        os.makedirs(temp_dir, exist_ok=True)
        
        print("🔄 Converting PDF to image...")
        image_paths = convert_pdf_to_jpg(original_passport_path, temp_dir)
        
        if image_paths:
            # Test the first image
            test_image_path = image_paths[0]
            print(f"📄 Testing image: {test_image_path}")
            
            # Test the rotation detection
            from simple_gemini_rotation import ask_gemini_if_needs_rotation
            
            print("🔍 Testing rotation detection on original passport...")
            result = ask_gemini_if_needs_rotation(test_image_path, is_passport_page=True)
            
            print(f"📊 Results:")
            print(f"   Rotation needed: {result['rotation_needed']}")
            print(f"   Rotation angle: {result['rotation_angle']}")
            print(f"   Reason: {result['reason']}")
            
            if result['rotation_needed']:
                print("✅ SUCCESS: Correctly detected that original passport needs rotation!")
                print(f"   Recommended rotation: {result['rotation_angle']}°")
            else:
                print("❌ FAILED: Did not detect rotation needed on original passport")
                
            # Clean up temp file
            try:
                os.remove(test_image_path)
                print("🧹 Cleaned up temp file")
            except:
                pass
                
        else:
            print("❌ Failed to convert PDF to image")
    else:
        print(f"❌ Original passport not found: {original_passport_path}")

if __name__ == "__main__":
    test_original_haneen_passport()
