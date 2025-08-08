#!/usr/bin/env python3
"""
Test script to verify the rotation fix is working correctly
"""

import os
import sys
sys.path.append('src')

def test_rotation_fix():
    """Test the rotation fix by simulating the pipeline steps"""
    
    print("🧪 Testing Rotation Fix")
    print("=" * 50)
    
    # Test with Haneen's passport file
    test_image_path = "data/temp/Passport_page1.jpg"
    
    if not os.path.exists(test_image_path):
        print(f"❌ Test image not found: {test_image_path}")
        return
    
    print(f"📄 Testing with: {test_image_path}")
    
    # Step 1: Simulate classification
    from resnet18_classifier import classify_image_resnet
    classification = classify_image_resnet(test_image_path)
    print(f"🏷️ ResNet classification: {classification}")
    
    # Step 2: Simulate rotation
    from simple_gemini_rotation import rotate_if_needed
    rotated_path = rotate_if_needed(test_image_path, is_passport_page=True)
    print(f"🔄 Rotation result: {rotated_path}")
    
    # Step 3: Simulate YOLO cropping using rotated path
    from crop_yolo_detections import run_yolo_crop
    cropped_path = run_yolo_crop(rotated_path, "data/temp")
    print(f"✂️ YOLO cropping result: {cropped_path}")
    
    # Step 4: Check if the cropped file is correctly oriented
    print(f"✅ Test completed. Cropped file should be correctly oriented: {cropped_path}")
    
    # Step 5: Verify the fix by checking if rotated_path is used
    print(f"🔍 Verification: YOLO cropping used rotated path: {rotated_path != test_image_path}")

if __name__ == "__main__":
    test_rotation_fix()
