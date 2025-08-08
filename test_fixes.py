#!/usr/bin/env python3
"""
Test script to verify rotation and compression fixes
"""

import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_rotation_fix():
    """Test that rotation now replaces the original file instead of creating duplicates"""
    
    print("🧪 Testing rotation fix...")
    
    # Test with a sample image from the processed folder
    test_image = "data/processed/COMPLETED/Fwd FW Ahmad Moustapha El Haj Moussa Supervisor Construction Electrical ADNOC BAB Buhasa P5 OffPlot Facilities AILIC/Electrical Engineering Certificate BAU_page2_attestation_label.jpg"
    
    if not os.path.exists(test_image):
        print(f"❌ Test image not found: {test_image}")
        return
    
    print(f"✅ Found test image: {os.path.basename(test_image)}")
    
    # Get original file size
    original_size = os.path.getsize(test_image)
    print(f"📏 Original file size: {original_size / 1024:.1f} KB")
    
    try:
        from simple_gemini_rotation import rotate_if_needed
        
        # Test rotation
        print(f"🔄 Testing rotation...")
        rotated_path = rotate_if_needed(test_image, is_passport_page=True)
        
        # Check if the path is the same (should be, since we're replacing the original)
        if rotated_path == test_image:
            print(f"✅ Rotation fix working: Original file replaced (no duplicate created)")
        else:
            print(f"⚠️ Rotation fix issue: New file created at {rotated_path}")
        
        # Check file size after rotation
        new_size = os.path.getsize(test_image)
        print(f"📏 File size after rotation: {new_size / 1024:.1f} KB")
        
    except Exception as e:
        print(f"❌ Error testing rotation: {e}")
        import traceback
        traceback.print_exc()

def test_compression_fix():
    """Test that compression now gets files below 110KB"""
    
    print("\n🧪 Testing compression fix...")
    
    # Test with a sample image
    test_image = "data/processed/COMPLETED/Fwd FW Ahmad Moustapha El Haj Moussa Supervisor Construction Electrical ADNOC BAB Buhasa P5 OffPlot Facilities AILIC/Electrical Engineering Certificate BAU_page2_attestation_label.jpg"
    
    if not os.path.exists(test_image):
        print(f"❌ Test image not found: {test_image}")
        return
    
    print(f"✅ Found test image: {os.path.basename(test_image)}")
    
    # Get original file size
    original_size = os.path.getsize(test_image)
    print(f"📏 Original file size: {original_size / 1024:.1f} KB")
    
    try:
        from image_utils import compress_image_to_jpg
        
        # Create a test output path
        test_output = "test_compressed.jpg"
        
        # Test compression
        print(f"🗜️ Testing compression to 110KB...")
        compressed_path = compress_image_to_jpg(test_image, test_output, max_kb=110)
        
        # Check compressed file size
        compressed_size = os.path.getsize(compressed_path)
        print(f"📏 Compressed file size: {compressed_size / 1024:.1f} KB")
        
        if compressed_size <= 110 * 1024:
            print(f"✅ Compression fix working: File compressed to {compressed_size / 1024:.1f} KB (under 110KB)")
        else:
            print(f"⚠️ Compression fix issue: File still {compressed_size / 1024:.1f} KB (over 110KB)")
        
        # Clean up test file
        if os.path.exists(test_output):
            os.remove(test_output)
            print(f"🧹 Cleaned up test file: {test_output}")
        
    except Exception as e:
        print(f"❌ Error testing compression: {e}")
        import traceback
        traceback.print_exc()

def test_job_extraction_fix():
    """Test that job extraction works with fallback logic"""
    
    print("\n🧪 Testing job extraction fix...")
    
    try:
        from structure_with_gemini import structure_with_gemini
        
        # Test with sample data
        certificate_ocr = """
        Bachelor of Engineering
        Electrical Engineering
        University of Technology
        """
        
        email_text = "Looking for an Engineer"
        
        print(f"📝 Testing with certificate OCR: {certificate_ocr.strip()}")
        print(f"📧 Testing with email text: {email_text}")
        
        result = structure_with_gemini(
            passport_ocr_1="",
            passport_ocr_2="",
            emirates_id_ocr="",
            emirates_id_2_ocr="",
            employee_info="",
            certificate_ocr=certificate_ocr,
            salary_data={},
            email_text=email_text,
            resnet_label="certificate",
            google_metadata={},
            sender_info={}
        )
        
        if isinstance(result, tuple):
            structured_data, gemini_response = result
        else:
            structured_data = result
            gemini_response = ""
        
        print(f"✅ Job extraction test completed:")
        print(f"   Certificate Job: {structured_data.get('Certificate_Job', 'NOT FOUND')}")
        print(f"   HR Manager Request: {structured_data.get('HR_Manager_Request', 'NOT FOUND')}")
        print(f"   Previous Job: {structured_data.get('Previous_Job', 'NOT FOUND')}")
        
    except Exception as e:
        print(f"❌ Error testing job extraction: {e}")
        import traceback
        traceback.print_exc()

def main():
    print("🔧 Testing rotation and compression fixes...")
    
    test_rotation_fix()
    test_compression_fix()
    test_job_extraction_fix()
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print("✅ All tests completed. Check the output above for results.")

if __name__ == "__main__":
    main()
