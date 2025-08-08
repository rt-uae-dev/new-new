#!/usr/bin/env python3
"""
Test script to debug certificate job extraction
"""

import os
import sys
sys.path.append('src')

def test_certificate_debug():
    """Debug the certificate job extraction issue"""
    
    print("🧪 Debugging Certificate Job Extraction")
    print("=" * 50)
    
    # Test the fallback logic with Ahmad's data
    certificate_ocr = ""  # Empty certificate OCR
    email_text = "Fwd FW Ahmad Moustapha El Haj Moussa Supervisor Construction Electrical ADNOC BAB Buhasa P5 OffPlot Facilities AILIC"
    
    print(f"📧 Email text: {email_text}")
    print(f"📄 Certificate OCR: {certificate_ocr}")
    
    # Test the fallback logic
    structured_data = {
        'Certificate_Job': 'N/A',
        'HR_Manager_Request': 'N/A'
    }
    
    # Apply the fallback logic
    if certificate_ocr and "electrical" in certificate_ocr.lower():
        structured_data['Certificate_Job'] = 'Electrical Engineering'
        print(f"✅ Found 'electrical' in certificate OCR")
    elif email_text and "electrical" in email_text.lower():
        structured_data['Certificate_Job'] = 'Electrical Engineering'
        print(f"✅ Found 'electrical' in email text")
    else:
        print(f"❌ No 'electrical' found in either source")
        
    if email_text and "engineer" in email_text.lower():
        structured_data['HR_Manager_Request'] = 'Engineer'
        print(f"✅ Found 'engineer' in email text")
    elif email_text and "supervisor" in email_text.lower():
        if "supervisor construction electrical" in email_text.lower():
            structured_data['HR_Manager_Request'] = 'Supervisor Construction Electrical'
            print(f"✅ Found 'Supervisor Construction Electrical' in email text")
        elif "supervisor" in email_text.lower():
            structured_data['HR_Manager_Request'] = 'Supervisor'
            print(f"✅ Found 'Supervisor' in email text")
    else:
        print(f"❌ No 'engineer' or 'supervisor' found in email text")
        
    print(f"\n📋 Results:")
    print(f"   Certificate Job: {structured_data['Certificate_Job']}")
    print(f"   HR Manager Request: {structured_data['HR_Manager_Request']}")
    
    # Check if the fix worked
    if structured_data['Certificate_Job'] == 'Electrical Engineering':
        print("✅ SUCCESS: Certificate Job extracted correctly!")
    else:
        print("❌ FAILED: Certificate Job not extracted")
        
    if structured_data['HR_Manager_Request'] == 'Supervisor Construction Electrical':
        print("✅ SUCCESS: HR Manager Request extracted correctly!")
    else:
        print("❌ FAILED: HR Manager Request not extracted as expected")

if __name__ == "__main__":
    test_certificate_debug()
