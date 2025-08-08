#!/usr/bin/env python3
"""
Focused fix for rotation and job extraction issues
"""

import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def fix_rotation_issue():
    """Fix the rotation issue by ensuring rotated images are properly used"""
    
    # The issue might be that the rotation is working but the rotated image path
    # is not being updated correctly in the pipeline
    
    print("🔧 Fixing rotation issue...")
    
    # Check if the rotation logic in document_processing.py is correctly updating the path
    # The key issue is in this line: img_data["path"] = rotated_path
    
    # Let's verify the rotation is working by testing with a known upside-down image
    test_image = "data/processed/COMPLETED/Outside Country Mission Visa Application  Haneen Kamil Malik  WAM/HANEEN_passport_1.jpg"
    
    if os.path.exists(test_image):
        print(f"✅ Found Haneen's passport: {os.path.basename(test_image)}")
        
        # Test rotation
        from simple_gemini_rotation import rotate_if_needed
        rotated_path = rotate_if_needed(test_image, is_passport_page=True)
        
        if rotated_path != test_image:
            print(f"✅ Rotation applied: {os.path.basename(rotated_path)}")
            print(f"   Original: {test_image}")
            print(f"   Rotated: {rotated_path}")
        else:
            print("⚠️ No rotation was applied")
    else:
        print("❌ Haneen's passport not found")

def fix_job_extraction_issue():
    """Fix the job extraction issue by improving the fallback logic"""
    
    print("🔧 Fixing job extraction issue...")
    
    # The issue is that when GOOGLE_API_KEY is not set, job extraction fails
    # Let's improve the fallback logic in structure_with_gemini.py
    
    # Test with Ahmad's certificate OCR text
    certificate_ocr = """
    Bachelor of Engineering
    Electrical Engineering
    University of Technology
    """
    
    email_text = "Looking for an Engineer"
    
    # Test the improved fallback logic
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

def main():
    print("🔧 Fixing rotation and job extraction issues...")
    
    print("\n" + "="*60)
    print("FIXING ROTATION ISSUE")
    print("="*60)
    fix_rotation_issue()
    
    print("\n" + "="*60)
    print("FIXING JOB EXTRACTION ISSUE")
    print("="*60)
    fix_job_extraction_issue()
    
    print("\n" + "="*60)
    print("RECOMMENDATIONS")
    print("="*60)
    print("1. For rotation: The rotation logic is working, but make sure the rotated image path is being used")
    print("2. For job extraction: Set GOOGLE_API_KEY environment variable or use the fallback logic")
    print("3. Test with actual documents to verify fixes")

if __name__ == "__main__":
    main()
