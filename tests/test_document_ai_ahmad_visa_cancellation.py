#!/usr/bin/env python3
"""
Test Document AI OCR on Ahmad's visa cancellation document to show raw output
"""

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Set environment variables for Document AI (same as main pipeline)
# Expect credentials in environment; do not hard-code in tests

from document_ai_processor import DOCUMENT_AI_PROCESSOR

def test_document_ai_ahmad_visa_cancellation():
    """Test Document AI on Ahmad's visa cancellation document and show raw OCR output"""
    
    # Test with Ahmad's visa cancellation document
    doc_path = "data/temp/visa cancellation Ahmad_page1.jpg"
    
    if not os.path.exists(doc_path):
        print(f"❌ Document not found: {doc_path}")
        return
    
    print(f"🔍 Testing Document AI on Ahmad's visa cancellation: {os.path.basename(doc_path)}")
    print("=" * 80)
    
    try:
        # Process with Document AI
        result = DOCUMENT_AI_PROCESSOR.process_document(doc_path)
        
        if "error" in result:
            print(f"❌ Document AI Error: {result['error']}")
            return
        
        # Show raw OCR text
        print("📄 RAW DOCUMENT AI OCR TEXT:")
        print("-" * 40)
        raw_text = result.get('full_text', '')
        print(raw_text)
        print("-" * 40)
        
        # Show document type
        document_type = DOCUMENT_AI_PROCESSOR.get_document_type(raw_text)
        print(f"📋 Document Type: {document_type}")
        
        # Test field extraction directly
        print("\n🔍 TESTING FIELD EXTRACTION DIRECTLY:")
        print("-" * 40)
        extracted_fields = DOCUMENT_AI_PROCESSOR.extract_specific_fields(raw_text)
        print(f"Extracted fields count: {len(extracted_fields)}")
        for field_name, field_value in extracted_fields.items():
            print(f"• {field_name}: {field_value}")
        
        # Test field extraction by document type
        print("\n🔍 TESTING FIELD EXTRACTION BY DOCUMENT TYPE:")
        print("-" * 40)
        extracted_fields_by_type = DOCUMENT_AI_PROCESSOR.extract_fields_by_document_type(raw_text)
        print(f"Extracted fields by type count: {len(extracted_fields_by_type)}")
        for field_name, field_value in extracted_fields_by_type.items():
            print(f"• {field_name}: {field_value}")
        
        # Show confidence
        print(f"\n🎯 Confidence: {result.get('confidence', 0.0):.2f}")
        
        # Check for critical numbers
        print("\n🔍 CRITICAL NUMBERS CHECK:")
        print("-" * 40)
        has_uid = any('uid' in field_name.lower() for field_name in extracted_fields_by_type.keys())
        has_identity = any('identity' in field_name.lower() for field_name in extracted_fields_by_type.keys())
        has_file = any('file' in field_name.lower() for field_name in extracted_fields_by_type.keys())
        
        print(f"• UID Number found: {has_uid}")
        print(f"• Identity Number found: {has_identity}")
        print(f"• File Number found: {has_file}")
        
        # Check raw text for patterns
        text_lower = raw_text.lower()
        uid_patterns = ['uid', 'رقم الهوية الفريد', 'unified identity']
        file_patterns = ['file no', 'رقم الملف', 'identity no', 'رقم الهوية']
        
        uid_in_text = any(pattern in text_lower for pattern in uid_patterns)
        file_in_text = any(pattern in text_lower for pattern in file_patterns)
        
        print(f"• UID patterns in raw text: {uid_in_text}")
        print(f"• File patterns in raw text: {file_in_text}")
        
        # Check for specific numbers in the text
        print("\n🔍 SPECIFIC NUMBERS IN TEXT:")
        print("-" * 40)
        import re
        
        # Look for 7-digit numbers (potential UID numbers)
        uid_numbers = re.findall(r'\b\d{7}\b', raw_text)
        print(f"• 7-digit numbers found: {uid_numbers}")
        
        # Look for file number patterns (XXX/YYYY/ZZZZZZZ)
        file_numbers = re.findall(r'\b\d{3}/\d{4}/\d{7}\b', raw_text)
        print(f"• File number patterns found: {file_numbers}")
        
        # Look for any numbers that might be important
        all_numbers = re.findall(r'\b\d{6,15}\b', raw_text)
        print(f"• All 6-15 digit numbers found: {all_numbers[:10]}...")  # Show first 10
        
        print("\n" + "=" * 80)
        print("✅ Document AI test completed")
        
    except Exception as e:
        print(f"❌ Error during Document AI test: {e}")

if __name__ == "__main__":
    test_document_ai_ahmad_visa_cancellation()
