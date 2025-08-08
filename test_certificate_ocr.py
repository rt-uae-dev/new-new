#!/usr/bin/env python3
"""
Test script to check certificate OCR text for Ahmad
"""

import os
import sys
sys.path.append('src')

def test_certificate_ocr():
    """Test the certificate OCR text to see what was extracted"""
    
    print("🧪 Testing Certificate OCR Text for Ahmad")
    print("=" * 50)
    
    # Check the certificate JSON file
    certificate_json_path = "data/processed/COMPLETED/Fwd FW Ahmad Moustapha El Haj Moussa Supervisor Construction Electrical ADNOC BAB Buhasa P5 OffPlot Facilities AILIC/Ahmad_certificate.json"
    
    if os.path.exists(certificate_json_path):
        print(f"📄 Found certificate JSON: {certificate_json_path}")
        
        # Read the JSON file
        import json
        with open(certificate_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"🔍 Certificate Job: {data.get('Certificate_Job', 'NOT FOUND')}")
        print(f"🔍 HR Manager Request: {data.get('HR_Manager_Request', 'NOT FOUND')}")
        print(f"🔍 Employee Info Job: {data.get('Employee_Info_Job', 'NOT FOUND')}")
        
        # Check if there's raw OCR text available
        print("\n🔍 Checking for raw OCR text...")
        
        # Look for OCR text in the processed data
        if 'ocr_text' in data:
            print(f"📝 Raw OCR text found: {data['ocr_text'][:500]}...")
        else:
            print("❌ No raw OCR text found in JSON")
            
        # Check if there are extracted fields
        if 'extracted_fields' in data:
            print(f"📋 Extracted fields: {data['extracted_fields']}")
        else:
            print("❌ No extracted fields found")
            
    else:
        print(f"❌ Certificate JSON not found: {certificate_json_path}")
    
    # Also check the comprehensive text file
    comprehensive_path = "data/processed/COMPLETED/Fwd FW Ahmad Moustapha El Haj Moussa Supervisor Construction Electrical ADNOC BAB Buhasa P5 OffPlot Facilities AILIC/Ahmad_COMPLETE_DETAILS.txt"
    
    if os.path.exists(comprehensive_path):
        print(f"\n📄 Found comprehensive text: {comprehensive_path}")
        
        with open(comprehensive_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Look for certificate job in the text
        if "Certificate Job:" in content:
            lines = content.split('\n')
            for line in lines:
                if "Certificate Job:" in line:
                    print(f"🔍 {line.strip()}")
                    break
        else:
            print("❌ Certificate Job not found in comprehensive text")
            
        # Look for any mention of electrical
        if "electrical" in content.lower():
            print("✅ Found 'electrical' in comprehensive text")
            # Find the line with electrical
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if "electrical" in line.lower():
                    print(f"🔍 Line {i+1}: {line.strip()}")
        else:
            print("❌ No 'electrical' found in comprehensive text")
    else:
        print(f"❌ Comprehensive text not found: {comprehensive_path}")

if __name__ == "__main__":
    test_certificate_ocr()
