#!/usr/bin/env python3
"""
Test script to check UID number extraction from Emirates ID
"""
import os
import sys
import json

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Set environment variables
# Expect credentials in environment; do not hard-code in tests

def test_emirates_id_uid_extraction():
    """Test UID number extraction from Emirates ID"""
    
    from document_ai_processor import DocumentAIProcessor
    
    # Initialize Document AI processor
    processor = DocumentAIProcessor()
    
    # Test with Ahmad's Emirates ID
    emirates_id_path = "data/raw/downloads/Fwd FW Ahmad Moustapha El Haj Moussa Supervisor Construction Electrical ADNOC BAB Buhasa P5 OffPlot Facilities AILIC/Ahmad Emirates ID 2027.pdf"
    
    if not os.path.exists(emirates_id_path):
        print(f"❌ Emirates ID file not found: {emirates_id_path}")
        return
    
    print(f"🔍 Testing UID extraction from: {emirates_id_path}")
    
    try:
        # Process the Emirates ID
        result = processor.process_document(emirates_id_path)
        
        print("📋 Document AI Result:")
        print(json.dumps(result, indent=2))
        
        # Check if UID number was extracted
        if 'emirates_id_fields' in result:
            emirates_fields = result['emirates_id_fields']
            if 'UID_Number' in emirates_fields:
                print(f"✅ SUCCESS: UID Number extracted: {emirates_fields['UID_Number']}")
            else:
                print("❌ FAILED: UID Number not found in emirates_id_fields")
                print(f"Available fields: {list(emirates_fields.keys())}")
        else:
            print("❌ FAILED: emirates_id_fields not found in result")
            print(f"Available keys: {list(result.keys())}")
            
    except Exception as e:
        print(f"❌ Error processing Emirates ID: {e}")

if __name__ == "__main__":
    test_emirates_id_uid_extraction()
