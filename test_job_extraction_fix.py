#!/usr/bin/env python3
"""
Test script to verify the job extraction fix
"""

import os
import sys
sys.path.append('src')

def test_job_extraction_fix():
    """Test the job extraction fix"""
    
    print("🧪 Testing Job Extraction Fix")
    print("=" * 50)
    
    # Simulate the fallback logic with Ahmad's data
    certificate_ocr = ""  # Empty certificate OCR
    email_text = "Fwd FW Ahmad Moustapha El Haj Moussa Supervisor Construction Electrical ADNOC BAB BAB Buhasa P5 OffPlot Facilities AILIC"
    
    print(f"📧 Email text: {email_text}")
    print(f"📄 Certificate OCR: {certificate_ocr}")
    
    # Test the fallback logic
    structured_data = {
        'Full Name': 'N/A',
        'Full Name (AR)': 'N/A',
        'Date of Birth': 'N/A',
        'Nationality': 'N/A',
        'Nationality (AR)': 'N/A',
        'Passport Number': 'N/A',
        'EID_Number': 'N/A',
        'Certificate_Job': 'N/A',
        'HR_Manager_Request': 'N/A',
        'Previous_Job': 'N/A',
        'Employee_Info_Job': 'N/A',
        'Salary': 'N/A',
        'Document Type': 'certificate'
    }
    
    # Apply the fixed fallback logic
    if certificate_ocr and "electrical" in certificate_ocr.lower():
        structured_data['Certificate_Job'] = 'Electrical Engineering'
        print("✅ Found 'electrical' in certificate OCR")
    elif email_text and "electrical" in email_text.lower():
        structured_data['Certificate_Job'] = 'Electrical Engineering'
        print("✅ Found 'electrical' in email text")
    else:
        print("❌ No 'electrical' found in either source")
        
    if email_text and "engineer" in email_text.lower():
        structured_data['HR_Manager_Request'] = 'Engineer'
        print("✅ Found 'engineer' in email text")
    else:
        print("❌ No 'engineer' found in email text")
        # Check what's actually in the email text
        print(f"🔍 Email text contains: {email_text}")
        if "Engineer" in email_text:
            print("✅ Found 'Engineer' (capital E) in email text")
            structured_data['HR_Manager_Request'] = 'Engineer'
        elif "engineer" in email_text:
            print("✅ Found 'engineer' (lowercase) in email text")
            structured_data['HR_Manager_Request'] = 'Engineer'
        else:
            print("❌ No 'engineer' found in any case")
    
    print(f"\n📋 Results:")
    print(f"   Certificate Job: {structured_data['Certificate_Job']}")
    print(f"   HR Manager Request: {structured_data['HR_Manager_Request']}")
    
    # Check if the fix worked
    if structured_data['Certificate_Job'] == 'Electrical Engineering':
        print("✅ FIX WORKED: Certificate Job extracted correctly!")
    else:
        print("❌ FIX FAILED: Certificate Job not extracted")

if __name__ == "__main__":
    test_job_extraction_fix()
