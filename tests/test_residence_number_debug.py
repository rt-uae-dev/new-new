#!/usr/bin/env python3
"""
Test script to debug residence number mapping
"""
import os
import sys
import json

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Set environment variables
# This test does not need real credentials; ensure no hard-coded paths/secrets

def test_residence_number_mapping():
    """Test residence number mapping from Document AI metadata"""
    
    # Sample Document AI metadata from the actual console output
    sample_metadata = {
        'visa_fields': {
            'UID_Number': '9031715',
            'Identity_Number': '784199169031715',
            'Residence_Number': '101/2019/2/179119'
        },
        'emirates_id_2_fields': {
            'UID_Number': '4872435'
        },
        'residence_cancellation_fields': {
            'UID_Number': '2111045',
            'Identity_Number': '784199169031715',
            'Residence_Number': '101/2019/2/179119'
        }
    }
    
    # Test the post-processing function
    from structure_with_gemini import post_process_structured_data
    
    # Sample structured data (what Gemini returns)
    sample_structured_data = {
        'Full Name': 'Ahmad Moustapha Elhaj Moussa',
        'Identity_Number': None,  # This should be updated
        'UID_Number': None  # This should be updated
    }
    
    print("🔍 Testing residence number mapping...")
    print(f"📋 Original structured data: {sample_structured_data}")
    print(f"📋 Document AI metadata: {json.dumps(sample_metadata, indent=2)}")
    
    # Apply post-processing
    result = post_process_structured_data(sample_structured_data, sample_metadata)
    
    print(f"✅ Post-processed result: {result}")
    
    # Check if mapping worked
    if result.get('Identity_Number') == '101/2019/2/179119':
        print("✅ SUCCESS: Residence number correctly mapped to Identity_Number")
    else:
        print("❌ FAILED: Residence number not mapped to Identity_Number")
    
    if result.get('UID_Number') == '4872435':
        print("✅ SUCCESS: UID number correctly mapped")
    else:
        print("❌ FAILED: UID number not mapped")

if __name__ == "__main__":
    test_residence_number_mapping()
