#!/usr/bin/env python3
"""
Test script to force 180° rotation on Haneen's passport based on user description
"""

import os
import sys
sys.path.append('src')

def test_force_passport_rotation():
    """Force 180° rotation on the passport"""
    
    print("🧪 Testing Force 180° Rotation on Haneen's Passport")
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
            
            # Force 180° rotation based on user description
            import cv2
            print("\n🔄 Force applying 180° rotation (user says photo is upside down)...")
            image = cv2.imread(test_image_path)
            rotated_image = cv2.rotate(image, cv2.ROTATE_180)
            
            # Save rotated image
            rotated_path = test_image_path.replace('.jpg', '_forced_180.jpg')
            cv2.imwrite(rotated_path, rotated_image)
            print(f"📄 Saved force-rotated image: {rotated_path}")
            
            # Test the rotation detection on force-rotated image
            from simple_gemini_rotation import ask_gemini_if_needs_rotation
            
            print("🔍 Testing rotation detection on force-rotated passport...")
            rotated_result = ask_gemini_if_needs_rotation(rotated_path, is_passport_page=True)
            
            print(f"📊 Force-Rotated Results:")
            print(f"   Rotation needed: {rotated_result['rotation_needed']}")
            print(f"   Rotation angle: {rotated_result['rotation_angle']}")
            print(f"   Reason: {rotated_result['reason']}")
            
            # Analysis
            print(f"\n📋 Analysis:")
            if not rotated_result['rotation_needed']:
                print("✅ SUCCESS: Force-rotated passport correctly detected as properly oriented!")
                print("✅ The 180° rotation fixed the upside-down personal photo")
            else:
                print("❌ Force-rotated passport still detected as needing rotation")
                print(f"   Additional rotation needed: {rotated_result['rotation_angle']}°")
                
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
    test_force_passport_rotation()
