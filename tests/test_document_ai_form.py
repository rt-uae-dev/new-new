#!/usr/bin/env python3
"""
Test Document AI OCR on a form document to show raw output
"""

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Expect credentials in environment; do not hard-code in tests.
# Required env vars at runtime:
#   GOOGLE_API_KEY
#   GOOGLE_CLOUD_PROJECT_ID
#   DOCUMENT_AI_PROCESSOR_ID
#   GOOGLE_APPLICATION_CREDENTIALS

from document_ai_processor import DOCUMENT_AI_PROCESSOR

def test_document_ai_form():
    """Test Document AI on a form document and show raw OCR output"""
    
    # Test with an employee information form
    form_path = "data/dataset/employee_info_form/Employee_Information_Form_page_1_1.jpg"
    
    if not os.path.exists(form_path):
        print(f"❌ Form not found: {form_path}")
        return
    
    print(f"🔍 Testing Document AI on form: {os.path.basename(form_path)}")
    print("=" * 80)
    
    try:
        # Process with Document AI
        result = DOCUMENT_AI_PROCESSOR.process_document(form_path)
        
        if "error" in result:
            print(f"❌ Document AI Error: {result['error']}")
            return
        
        # Show raw OCR text
        print("📄 RAW DOCUMENT AI OCR TEXT:")
        print("-" * 40)
        raw_text = result.get('full_text', '')
        print(raw_text)
        print("-" * 40)
        
        # Show extracted fields
        print("\n📋 EXTRACTED FIELDS:")
        print("-" * 40)
        extracted_fields = result.get('extracted_fields', {})
        for field_name, field_value in extracted_fields.items():
            print(f"• {field_name}: {field_value}")
        
        # Show confidence
        print(f"\n🎯 Confidence: {result.get('confidence', 0.0):.2f}")
        
        # Show document type
        document_type = DOCUMENT_AI_PROCESSOR.get_document_type(raw_text)
        print(f"📋 Document Type: {document_type}")
        
        # Check for critical numbers
        print("\n🔍 CRITICAL NUMBERS CHECK:")
        print("-" * 40)
        has_uid = any('uid' in field_name.lower() for field_name in extracted_fields.keys())
        has_identity = any('identity' in field_name.lower() for field_name in extracted_fields.keys())
        has_file = any('file' in field_name.lower() for field_name in extracted_fields.keys())
        
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
        
        print("\n" + "=" * 80)
        print("✅ Document AI test completed")
        
    except Exception as e:
        print(f"❌ Error during Document AI test: {e}")

if __name__ == "__main__":
    test_document_ai_form()
