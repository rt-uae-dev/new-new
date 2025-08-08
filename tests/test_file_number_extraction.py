#!/usr/bin/env python3
"""
Test script to debug file number extraction
"""
import os
import sys
import json

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Set environment variables
# Expect credentials in environment; do not hard-code in tests

def test_file_number_extraction():
    """Test file number extraction from Document AI metadata"""
    
    # Sample Document AI metadata from the actual run
    sample_metadata = {
        'visa_fields': {
            'UID_Number': '9031715',
            'Identity_Number': '784199169031715',
            'Residence_Number': '101/2019/2/179119',  # This should be the file number
            'EID_Number': '784199169031715',
            'Passport Number': 'PR0283298',
            'Job Title': 'صاحب العم',
            'Employer': 'شركه المنصورى لخدمات الانتاج ذ م م',
            'Passport Issue Place': 'Accompanied by',
            'Dates Found': ['16/04/2025', '15/04/2027']
        },
        'residence_cancellation_fields': {
            'UID_Number': '2111045',
            'Identity_Number': '784199169031715',
            'Residence_Number': '101/2019/2/179119',  # This should be the file number
            'EID_Number': '784199169031715',
            'Passport Number': 'PR0283298',
            'Full Name': 'AHMAD MOUSTAPHA ELHAJ MC',
            'Job Title': 'Information Clerk',
            'Employer': 'ALMANSOORI PRODUCTION',
            'Passport Issue Place': 'ABU DHABI',
            'Dates Found': ['19/08/2025', '22/07/2025']
        },
        'emirates_id_2_fields': {
            'UID_Number': '4872435',  # This should be the UID number
            'Identity_Number': '784199169031715',
            'EID_Number': '784199169031715',
            'Job Title': 'كاتب المعلومات',
            'Employer': 'Almansoori Production Services Company - Llo',
            'Attestation Number 2': '4872435',
            'Attestation Number 1': '199169031715',
            'Has Official Stamp': 'No',
            'Emirates ID Number': '78419916903171'
        }
    }
    
    print("🔍 Testing File Number Extraction")
    print("=" * 50)
    
    # Check if Residence_Number exists in visa fields
    if 'visa_fields' in sample_metadata and 'Residence_Number' in sample_metadata['visa_fields']:
        residence_number = sample_metadata['visa_fields']['Residence_Number']
        print(f"✅ Found Residence_Number in visa_fields: {residence_number}")
        print(f"   This should be used as Identity_Number/File Number")
    else:
        print("❌ Residence_Number not found in visa_fields")
    
    # Check if Residence_Number exists in residence_cancellation fields
    if 'residence_cancellation_fields' in sample_metadata and 'Residence_Number' in sample_metadata['residence_cancellation_fields']:
        residence_number = sample_metadata['residence_cancellation_fields']['Residence_Number']
        print(f"✅ Found Residence_Number in residence_cancellation_fields: {residence_number}")
        print(f"   This should be used as Identity_Number/File Number")
    else:
        print("❌ Residence_Number not found in residence_cancellation_fields")
    
    # Check if UID_Number exists in emirates_id_2 fields
    if 'emirates_id_2_fields' in sample_metadata and 'UID_Number' in sample_metadata['emirates_id_2_fields']:
        uid_number = sample_metadata['emirates_id_2_fields']['UID_Number']
        print(f"✅ Found UID_Number in emirates_id_2_fields: {uid_number}")
        print(f"   This should be used as U.I.D Number")
    else:
        print("❌ UID_Number not found in emirates_id_2_fields")
    
    print("\n🔍 Expected Results:")
    print(f"   Identity_Number/File Number: 101/2019/2/179119")
    print(f"   U.I.D Number: 4872435")
    
    print("\n🔍 Testing Gemini prompt logic:")
    print("   The Gemini prompt should:")
    print("   1. Look for Document AI extracted 'Residence_Number' field")
    print("   2. Use that value for 'Identity_Number' field")
    print("   3. Look for Document AI extracted 'UID_Number' field")
    print("   4. Use that value for 'UID_Number' field")

if __name__ == "__main__":
    test_file_number_extraction()
