#!/usr/bin/env python3
"""
Test script to debug rotation and job extraction issues
"""

import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_rotation():
    """Test rotation with Haneen's passport"""
    
    # Test with Haneen's processed passport file
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

def test_job_extraction():
    """Test job extraction with Ahmad's certificate"""
    
    # Test with Ahmad's certificate
    test_certificate = "data/dataset/certificate/05.1DegreeCertificate_page_1_1_1_1.jpg"
    
    if not os.path.exists(test_certificate):
        print(f"❌ Test certificate not found: {test_certificate}")
        return
    
    print(f"🧪 Testing job extraction with Ahmad's certificate: {os.path.basename(test_certificate)}")
    
    try:
        # Simulate the OCR text that should contain "Electrical Engineering"
        certificate_ocr = """
        Bachelor of Engineering
        Electrical Engineering
        University of Technology
        """
        
        email_text = "Looking for an Engineer"
        
        # Test the Gemini structuring
        from structure_with_gemini import structure_with_gemini
        
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
        
        print(f"Certificate Job: {structured_data.get('Certificate_Job', 'NOT FOUND')}")
        print(f"HR Manager Request: {structured_data.get('HR_Manager_Request', 'NOT FOUND')}")
        print(f"Previous Job: {structured_data.get('Previous_Job', 'NOT FOUND')}")
        
    except Exception as e:
        print(f"❌ Error testing job extraction: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🔍 Testing rotation and job extraction issues...")
    
    print("\n" + "="*60)
    print("TESTING ROTATION")
    print("="*60)
    test_rotation()
    
    print("\n" + "="*60)
    print("TESTING JOB EXTRACTION")
    print("="*60)
    test_job_extraction()
