#!/usr/bin/env python3
"""
Test script to manually apply 180° rotation to Haneen's passport
"""

import os
import sys
sys.path.append('src')

def test_manual_passport_rotation():
    """Manually apply 180° rotation to the passport"""
    
    print("🧪 Testing Manual 180° Rotation on Haneen's Passport")
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
            
            # Test the rotation detection on original
            from simple_gemini_rotation import ask_gemini_if_needs_rotation
            
            print("🔍 Testing rotation detection on original passport...")
            original_result = ask_gemini_if_needs_rotation(test_image_path, is_passport_page=True)
            
            print(f"📊 Original Results:")
            print(f"   Rotation needed: {original_result['rotation_needed']}")
            print(f"   Rotation angle: {original_result['rotation_angle']}")
            print(f"   Reason: {original_result['reason']}")
            
            # Now manually apply 180° rotation
            import cv2
            print("\n🔄 Manually applying 180° rotation...")
            image = cv2.imread(test_image_path)
            rotated_image = cv2.rotate(image, cv2.ROTATE_180)
            
            # Save rotated image
            rotated_path = test_image_path.replace('.jpg', '_rotated_180.jpg')
            cv2.imwrite(rotated_path, rotated_image)
            print(f"📄 Saved rotated image: {rotated_path}")
            
            # Test the rotation detection on rotated image
            print("🔍 Testing rotation detection on rotated passport...")
            rotated_result = ask_gemini_if_needs_rotation(rotated_path, is_passport_page=True)
            
            print(f"📊 Rotated Results:")
            print(f"   Rotation needed: {rotated_result['rotation_needed']}")
            print(f"   Rotation angle: {rotated_result['rotation_angle']}")
            print(f"   Reason: {rotated_result['reason']}")
            
            # Analysis
            print(f"\n📋 Analysis:")
            if original_result['rotation_needed']:
                print("✅ Original passport correctly detected as needing rotation")
            else:
                print("❌ Original passport incorrectly detected as not needing rotation")
                
            if rotated_result['rotation_needed']:
                print("✅ Rotated passport correctly detected as needing rotation")
            else:
                print("❌ Rotated passport incorrectly detected as not needing rotation")
                
            # Clean up temp files
            try:
                os.remove(test_image_path)
                os.remove(rotated_path)
                print("🧹 Cleaned up temp files")
            except:
                pass
                
        else:
            print("❌ Failed to convert PDF to image")
    else:
        print(f"❌ Original passport not found: {original_passport_path}")

if __name__ == "__main__":
    test_manual_passport_rotation()
