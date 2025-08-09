#!/usr/bin/env python3
"""
Output Generation Module
Handles saving files, creating text reports, and final compression
"""

import os
import json
from typing import Dict, Any, List
from structure_with_gemini import structure_with_gemini
from output_saving_utils import save_outputs, log_processed_file
from image_utils import compress_image_to_jpg
from parse_salary_docx import parse_salary_docx
from parse_salary_email import parse_salary_email, merge_salary_data

def parse_salary_documents(subject_path: str, email_text: str = "") -> Dict[str, Any]:
    """Parse salary DOCX files and email text."""
    print("💰 Parsing salary information from documents and email...")
    docx_salary_data = {}
    email_salary_data = {}

    # Look for salary DOCX files
    docx_files = [f for f in os.listdir(subject_path) if f.lower().endswith('.docx') and 'salary' in f.lower()]
    
    for docx_file in docx_files:
        try:
            docx_path = os.path.join(subject_path, docx_file)
            parsed_salary = parse_salary_docx(docx_path)
            if parsed_salary:
                docx_salary_data.update(parsed_salary)
                print(f"✅ Parsed salary from DOCX: {docx_file}")
        except Exception as e:
            print(f"❌ Error parsing salary from {docx_file}: {e}")
    
    # Parse salary from email text
    if email_text and email_text.strip():
        try:
            email_salary_data = parse_salary_email(email_text)
            if email_salary_data:
                print("✅ Parsed salary from email text")
                print("📧 Email Salary Details:")
                for key, value in email_salary_data.items():
                    if isinstance(value, dict):
                        print(f"   📋 {key.replace('_', ' ').title()}:")
                        for sub_key, sub_value in value.items():
                            print(f"      • {sub_key}: {sub_value}")
                    else:
                        print(f"   • {key.replace('_', ' ').title()}: {value}")
            else:
                print("⚠️ No salary data found in email text")
        except Exception as e:
            print(f"❌ Error parsing salary from email text: {e}")
    
    # Merge salary data (DOCX takes priority)
    final_salary_data = merge_salary_data(docx_salary_data, email_salary_data)
    
    if final_salary_data:
        print("💰 Final Salary Summary:")
        for key, value in final_salary_data.items():
            if isinstance(value, dict):
                print(f"   📋 {key.replace('_', ' ').title()}:")
                for sub_key, sub_value in value.items():
                    print(f"      • {sub_key}: {sub_value}")
            else:
                print(f"   • {key.replace('_', ' ').title()}: {value}")
    else:
        print("⚠️ No salary information found in documents or email")

    return final_salary_data

def collect_ocr_data(processed_images: List[Dict[str, Any]]) -> tuple[str, str, str, str, str, str, Dict[str, Any]]:
    """Collect OCR data by document type."""
    passport_ocr_1 = ""
    passport_ocr_2 = ""
    emirates_id_ocr = ""
    emirates_id_2_ocr = ""
    employee_info = ""
    certificate_ocr = ""
    google_metadata = {}
    
    for img_data in processed_images:
        ocr_text = img_data.get("ocr_text", "")
        extracted_fields = img_data.get("extracted_fields", {})
        
        if img_data["label"] == "passport_1":
            passport_ocr_1 = ocr_text
            if extracted_fields:
                google_metadata["passport_1_fields"] = extracted_fields
        elif img_data["label"] == "passport_2":
            passport_ocr_2 = ocr_text
            if extracted_fields:
                google_metadata["passport_2_fields"] = extracted_fields
        elif img_data["label"] == "emirates_id":
            emirates_id_ocr = ocr_text
            if extracted_fields:
                google_metadata["emirates_id_fields"] = extracted_fields
        elif img_data["label"] == "emirates_id_2":
            emirates_id_2_ocr = ocr_text
            if extracted_fields:
                google_metadata["emirates_id_2_fields"] = extracted_fields
        elif img_data["label"] == "employee_info_form":
            employee_info = ocr_text
            if extracted_fields:
                google_metadata["employee_info_fields"] = extracted_fields
        elif img_data["label"] in ["certificate", "certificate_attestation", "attestation_label"]:
            certificate_ocr = ocr_text
            if extracted_fields:
                google_metadata["certificate_fields"] = extracted_fields
        elif img_data["label"] == "visa":
            if extracted_fields:
                google_metadata["visa_fields"] = extracted_fields
        elif img_data["label"] == "residence_cancellation":
            if extracted_fields:
                google_metadata["residence_cancellation_fields"] = extracted_fields

    return passport_ocr_1, passport_ocr_2, emirates_id_ocr, emirates_id_2_ocr, employee_info, certificate_ocr, google_metadata

def run_gemini_structuring(current_subject_folder: str, ocr_data: tuple, salary_data: Dict[str, Any], 
                          email_text: str, processed_images: List[Dict[str, Any]], 
                          google_metadata: Dict[str, Any], sender_info: Dict[str, Any]) -> tuple[Dict[str, Any], str]:
    """Run comprehensive Gemini structuring."""
    print(f"🧠 Running comprehensive Gemini structuring for {current_subject_folder}...")
    
    passport_ocr_1, passport_ocr_2, emirates_id_ocr, emirates_id_2_ocr, employee_info, certificate_ocr, _ = ocr_data
    
    result = structure_with_gemini(
        passport_ocr_1=passport_ocr_1,
        passport_ocr_2=passport_ocr_2,
        emirates_id_ocr=emirates_id_ocr,
        emirates_id_2_ocr=emirates_id_2_ocr,
        employee_info=employee_info,
        certificate_ocr=certificate_ocr,
        salary_data=salary_data,
        email_text=email_text,
        resnet_label=", ".join([img["label"] for img in processed_images]),
        google_metadata=google_metadata,
        sender_info=sender_info
    )

    # Handle the tuple return from structure_with_gemini
    if isinstance(result, tuple):
        final_structured, gemini_response = result
    else:
        final_structured = result
        gemini_response = ""
    
    # Add sender information to the structured data if not already present
    if sender_info and isinstance(final_structured, dict):
        final_structured['Email_Sender_Name'] = sender_info.get('name', 'N/A')
        final_structured['Email_Sender_Email'] = sender_info.get('email', 'N/A')
        final_structured['Email_Sender_Person_Name'] = sender_info.get('person_name', 'N/A')

    return final_structured, gemini_response

def create_comprehensive_text_file(subject_output_dir: str, first_name: str, full_name: str, 
                                 final_structured: Dict[str, Any], sender_info: Dict[str, Any], 
                                 subject_folder: str, mohre_analysis: Dict[str, Any], 
                                 mohre_service_url: str, salary_data: Dict[str, Any],
                                 processed_images: List[Dict[str, Any]], email_text: str) -> str:
    """Create comprehensive master text file."""
    master_text_file = os.path.join(subject_output_dir, f"{first_name}_COMPLETE_DETAILS.txt")
    
    with open(master_text_file, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write(f"COMPLETE DOCUMENT DETAILS FOR: {full_name}\n")
        f.write("=" * 80 + "\n\n")
        
        # Email Sender Information Section
        f.write("📧 EMAIL SENDER INFORMATION\n")
        f.write("-" * 40 + "\n")
        f.write(f"Sender Name: {sender_info.get('name', 'N/A')}\n")
        f.write(f"Sender Email: {sender_info.get('email', 'N/A')}\n")
        f.write(f"Email Subject: {subject_folder}\n\n")
        
        # Personal Information Section
        f.write("📋 PERSONAL INFORMATION\n")
        f.write("-" * 40 + "\n")
        f.write(f"Full Name: {final_structured.get('Full Name', 'N/A')}\n")
        f.write(f"Full Name (AR): {final_structured.get('Full Name (AR)', 'N/A')}\n")
        f.write("Father's Name: " + str(final_structured.get("Father's Name", 'N/A')) + "\n")
        f.write("Father's Name (AR): " + str(final_structured.get("Father's Name (AR)", 'N/A')) + "\n")
        f.write("Mother's Name: " + str(final_structured.get("Mother's Name", 'N/A')) + "\n")
        f.write("Mother's Name (AR): " + str(final_structured.get("Mother's Name (AR)", 'N/A')) + "\n")
        f.write(f"Date of Birth: {final_structured.get('Date of Birth', 'N/A')}\n")
        f.write(f"Nationality: {final_structured.get('Nationality', 'N/A')}\n")
        f.write(f"Nationality (AR): {final_structured.get('Nationality (AR)', 'N/A')}\n")
        f.write(f"Place of Birth: {final_structured.get('Place of Birth', 'N/A')}\n")
        f.write(f"Place of Birth (AR): {final_structured.get('Place of Birth (AR)', 'N/A')}\n\n")
        
        # Document Information Section
        f.write("📄 DOCUMENT INFORMATION\n")
        f.write("-" * 40 + "\n")
        f.write(f"Passport Number: {final_structured.get('Passport Number', 'N/A')}\n")
        f.write(f"EID Number: {final_structured.get('EID_Number', 'N/A')}\n")
        f.write(f"EID Issue Date: {final_structured.get('EID_Issue_Date', 'N/A')}\n")
        f.write(f"EID Expiry Date: {final_structured.get('EID_Expiry_Date', 'N/A')}\n")
        f.write(f"Identity Number/File Number: {final_structured.get('Identity_Number', 'N/A')}\n")
        f.write(f"U.I.D Number: {final_structured.get('UID_Number', 'N/A')}\n")
        f.write(f"Passport Issue Place: {final_structured.get('Passport Issue Place', 'N/A')}\n")
        f.write(f"Passport Issue Place (AR): {final_structured.get('Passport Issue Place (AR)', 'N/A')}\n")
        f.write(f"Passport Issue Date: {final_structured.get('Passport Issue Date', 'N/A')}\n")
        f.write(f"Passport Expiry Date: {final_structured.get('Passport Expiry Date', 'N/A')}\n\n")
        
        # Contact Information Section
        f.write("📞 CONTACT INFORMATION\n")
        f.write("-" * 40 + "\n")
        f.write(f"Home Phone Number: {final_structured.get('Home Phone Number', 'N/A')}\n")
        f.write(f"Home Address: {final_structured.get('Home Address', 'N/A')}\n")
        f.write(f"UAE Address: {final_structured.get('UAE Address', 'N/A')}\n\n")
        
        # Professional Information Section
        f.write("💼 PROFESSIONAL INFORMATION\n")
        f.write("-" * 40 + "\n")
        f.write(f"Certificate Job: {final_structured.get('Certificate_Job', 'N/A')}\n")
        f.write(f"HR Manager Request: {final_structured.get('HR_Manager_Request', 'N/A')}\n")
        f.write(f"Previous Job (EID): {final_structured.get('Previous_Job', 'N/A')}\n")
        f.write(f"Employee Info Form Job: {final_structured.get('Employee_Info_Job', 'N/A')}\n")
        f.write(f"Salary: {final_structured.get('Salary', 'N/A')}\n\n")
        
        # Enhanced Salary Information Section
        if salary_data:
            f.write("💰 DETAILED SALARY BREAKDOWN\n")
            f.write("-" * 40 + "\n")
            for key, value in salary_data.items():
                if key == "Employment_Terms":
                    f.write("📋 Employment Terms:\n")
                    for term_key, term_value in value.items():
                        f.write(f"   • {term_key.replace('_', ' ').title()}: {term_value}\n")
                else:
                    f.write(f"• {key.replace('_', ' ').title()}: {value}\n")
            f.write("\n")
        
        # Attestation Information Section
        f.write("🏛️ ATTESTATION INFORMATION\n")
        f.write("-" * 40 + "\n")
        f.write(f"Attestation Number 1: {final_structured.get('Attestation Number 1', 'N/A')}\n")
        f.write(f"Attestation Number 2: {final_structured.get('Attestation Number 2', 'N/A')}\n\n")
        
        # Simple Service Analysis Section
        f.write("🔍 SERVICE NEEDED\n")
        f.write("-" * 40 + "\n")
        service_needed = analyze_service_needed(processed_images, email_text, subject_folder)
        f.write(f"{service_needed}\n\n")
        
        # MOHRE Service Analysis Section (Detailed)
        f.write("🏛️ DETAILED MOHRE SERVICE ANALYSIS\n")
        f.write("-" * 40 + "\n")
        f.write(f"Service Category: {mohre_analysis.get('service_category', 'N/A')}\n")
        f.write(f"Specific Service: {mohre_analysis.get('specific_service', 'N/A')}\n")
        f.write(f"Confidence Level: {mohre_analysis.get('confidence_level', 'N/A')}\n")
        f.write(f"Priority Level: {mohre_analysis.get('priority_level', 'N/A')}\n")
        f.write(f"MOHRE Service URL: {mohre_service_url}\n")
        f.write(f"Additional Context: {mohre_analysis.get('additional_context', 'N/A')}\n")
        f.write(f"Reasoning: {mohre_analysis.get('reasoning', 'N/A')}\n")
        
        # Key Indicators
        key_indicators = mohre_analysis.get('key_indicators', [])
        if key_indicators:
            f.write(f"Key Indicators: {', '.join(key_indicators)}\n")
        else:
            f.write("Key Indicators: None identified\n")
        
        # Required Documents
        required_docs = mohre_analysis.get('required_documents', [])
        if required_docs:
            f.write("Required Documents:\n")
            for doc in required_docs:
                f.write(f"   • {doc}\n")
        else:
            f.write("Required Documents: Not specified\n")
        f.write("\n")
    
    print(f"📄 Created comprehensive details file: {master_text_file}")
    return master_text_file

def save_individual_files(processed_images: List[Dict[str, Any]], final_structured: Dict[str, Any], 
                         subject_output_dir: str, first_name: str, gemini_response: str, log_file: str) -> None:
    """Save individual files."""
    for img_data in processed_images:
        # Create descriptive filename based on document type and extracted first name
        doc_type = img_data["label"]
        
        # Create descriptive name using first name
        if doc_type == "passport_1":
            base = f"{first_name}_passport_1"
        elif doc_type == "passport_2":
            base = f"{first_name}_passport_2"
        elif doc_type == "emirates_id":
            base = f"{first_name}_emirates_id"
        elif doc_type == "emirates_id_2":
            base = f"{first_name}_emirates_id_2"
        elif doc_type == "personal_photo":
            base = f"{first_name}_personal_photo"
        elif doc_type == "certificate":
            base = f"{first_name}_certificate"
        elif doc_type == "certificate_attestation":
            base = f"{first_name}_certificate_attestation"
        elif doc_type == "attestation_label":
            base = f"{first_name}_attestation_label"
        elif doc_type == "residence_cancellation":
            base = f"{first_name}_residence_cancellation"
        else:
            base = f"{first_name}_{doc_type}"
        
        # Use the appropriate path for saving
        if img_data["label"] in ["certificate_attestation", "attestation_label"] and "finished_path" in img_data:
            # For attestation pages, use the already saved finished path
            save_path = img_data["finished_path"]
        elif "cropped_path" in img_data:
            save_path = img_data["cropped_path"]
        elif "compressed_path" in img_data:
            save_path = img_data["compressed_path"]
        else:
            save_path = img_data["path"]
        
        final_path = save_outputs(save_path, final_structured, subject_output_dir, base, gemini_response)
        log_processed_file(log_file, img_data["filename"], final_path, img_data["label"])

def compress_final_files(processed_images: List[Dict[str, Any]], subject_output_dir: str, first_name: str) -> None:
    """Compress all saved files to under 110KB."""
    print("🗜️ Compressing all saved files to under 110KB...")
    for img_data in processed_images:
        try:
            # Find the saved file path
            doc_type = img_data["label"]
            if doc_type == "passport_1":
                base = f"{first_name}_passport_1"
            elif doc_type == "passport_2":
                base = f"{first_name}_passport_2"
            elif doc_type == "emirates_id":
                base = f"{first_name}_emirates_id"
            elif doc_type == "emirates_id_2":
                base = f"{first_name}_emirates_id_2"
            elif doc_type == "personal_photo":
                base = f"{first_name}_personal_photo"
            elif doc_type == "certificate":
                base = f"{first_name}_certificate"
            elif doc_type == "certificate_attestation":
                base = f"{first_name}_certificate_attestation"
            elif doc_type == "attestation_label":
                base = f"{first_name}_attestation_label"
            elif doc_type == "residence_cancellation":
                base = f"{first_name}_residence_cancellation"
            else:
                base = f"{first_name}_{doc_type}"
            
            # Look for the saved file
            saved_file = os.path.join(subject_output_dir, f"{base}.jpg")
            if os.path.exists(saved_file):
                # Compress the saved file
                compressed_path = compress_image_to_jpg(saved_file, saved_file)
                print(f"✅ Final compression: {os.path.basename(saved_file)}")
        except Exception as e:
            print(f"⚠️ Error in final compression for {img_data['filename']}: {e}")

def analyze_service_needed(processed_images: List[Dict[str, Any]], email_text: str, subject_folder: str) -> str:
    """
    Analyze documents and provide a simple, one-sentence description of what service is needed.
    
    Args:
        processed_images: List of processed image data
        email_text: Email body text
        subject_folder: Email subject/folder name
        
    Returns:
        str: One-sentence description of service needed
    """
    # Get document types present
    document_types = [img["label"] for img in processed_images]
    
    # Check for specific document combinations
    has_job_offer = any("job_offer" in label for label in document_types)
    has_contract = any("contract" in label for label in document_types)
    has_certificate = any("certificate" in label for label in document_types)
    has_attestation = any("attestation" in label for label in document_types)
    has_visa = any("visa" in label for label in document_types)
    has_residence_cancellation = any("residence_cancellation" in label for label in document_types)
    has_work_permit_cancellation = any("work_permit_cancellation" in label for label in document_types)
    has_emirates_id = any("emirates_id" in label for label in document_types)
    has_passport = any("passport" in label for label in document_types)
    
    # Analyze email text for keywords
    email_lower = email_text.lower() if email_text else ""
    subject_lower = subject_folder.lower() if subject_folder else ""
    
    # Check for specific service requests in email
    if "new job offer" in email_lower or "new labour contract" in email_lower:
        if has_job_offer and has_contract:
            return "Please send me new job offer and labour contract - Step 1 (job offer + contract) in MOHRE."
        elif has_job_offer:
            return "Please send me new job offer - Step 1 (job offer) in MOHRE."
        elif has_contract:
            return "Please send me new labour contract - Step 1 (contract) in MOHRE."
    
    if "attestation" in email_lower or "attest" in email_lower:
        if has_certificate and has_attestation:
            return "Certificate attestation service needed - attestation of educational documents."
        elif has_certificate:
            return "Certificate attestation service needed - attestation of educational documents."
    
    if "visa" in email_lower and "cancellation" in email_lower:
        if has_residence_cancellation:
            return "Residence visa cancellation service needed."
        elif has_work_permit_cancellation:
            return "Work permit cancellation service needed."
    
    if "visa" in email_lower and "renewal" in email_lower:
        return "Visa renewal service needed."
    
    if "new visa" in email_lower or "apply visa" in email_lower:
        return "New visa application service needed."
    
    # Document-based analysis
    if has_job_offer and has_contract:
        return "Step 1 MOHRE service needed - job offer and labour contract processing."
    
    if has_certificate and has_attestation:
        return "Certificate attestation service needed - educational document attestation."
    
    if has_residence_cancellation:
        return "Residence visa cancellation service needed."
    
    if has_work_permit_cancellation:
        return "Work permit cancellation service needed."
    
    if has_visa and has_passport and has_emirates_id:
        return "Visa application service needed - complete document set provided."
    
    if has_certificate:
        return "Certificate processing service needed - educational document verification."
    
    if has_passport and has_emirates_id:
        return "Document verification service needed - passport and Emirates ID provided."
    
    # Default fallback
    return "Document processing service needed - please review documents for specific requirements."

def extract_first_name(final_structured: Dict[str, Any]) -> tuple[str, str]:
    """Extract first name from structured data."""
    # Handle both string and dictionary cases for final_structured
    if isinstance(final_structured, str):
        try:
            final_structured = json.loads(final_structured)
            mother_name = final_structured.get('Mother\'s Name', 'NOT FOUND')
            print(f"🔍 Debug - Successfully parsed JSON, mother's name: {mother_name}")
        except Exception as e:
            print(f"⚠️ Could not parse final_structured as JSON: {e}")
            print(f"⚠️ Raw final_structured: {final_structured[:200]}...")
            final_structured = {}
    else:
        mother_name = final_structured.get('Mother\'s Name', 'NOT FOUND')
        print(f"🔍 Debug - final_structured is already dict, mother's name: {mother_name}")
    
    full_name = final_structured.get("Full Name", "")
    print(f"🔍 Debug - Full Name extracted: '{full_name}'")
    
    if full_name:
        first_name = full_name.split()[0] if full_name else "Unknown"
        print(f"🔍 Debug - First Name extracted: '{first_name}'")
    else:
        print(f"⚠️ No full name found in structured data")
        first_name = "Unknown"
    
    return first_name, full_name
