#!/usr/bin/env python3
"""
Main pipeline for MOHRE document processing.
New workflow:
1. Read email body.txt from email folder
2. Convert PDF to JPG
3. Classify through classifier.pt (ResNet)
4. If certificate exists, ensure certificate_attestation page is classified
5. Copy attestation_certificate page and compress first
6. Run YOLO to crop the label out of certificate_attestation page
7. Run OCR for all documents
"""

import os
import subprocess
import platform
from datetime import datetime
from email_parser import fetch_and_store_emails, safe_copy_file, safe_remove_directory
from pdf_converter import convert_pdf_to_jpg
from resnet18_classifier import classify_image_resnet
from yolo_crop_ocr_pipeline import run_yolo_crop, run_enhanced_ocr
from structure_with_gemini import structure_with_gemini
from output_saving_utils import save_outputs, log_processed_file
from image_utils import compress_image_to_jpg
from google_vision_orientation_detector import rotate_if_needed
from parse_salary_docx import parse_salary_docx

# Import email analyzer
try:
    from email_analyzer import analyze_email_for_mohre_service, get_mohre_service_url
except ImportError:
    print("⚠️ Email analyzer not available, skipping MOHRE service analysis")
    def analyze_email_for_mohre_service(email_body: str, email_subject: str = "") -> dict:
        return {
            "service_category": "Unknown",
            "specific_service": "Unknown",
            "confidence_level": "Low",
            "key_indicators": [],
            "additional_context": "Email analyzer not available",
            "priority_level": "Normal",
            "required_documents": [],
            "reasoning": "Email analyzer module not found"
        }
    def get_mohre_service_url(service_category: str, specific_service: str) -> str:
        return "https://www.mohre.gov.ae/en/services.aspx"

# === CONFIG === (env-overridable)
INPUT_DIR = os.getenv("INPUT_DIR", "data/raw/downloads")
NEW_INPUT_DIR = os.getenv("NEW_DOWNLOAD_DIR", "data/raw/new_downloads")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "data/processed/COMPLETED")
TEMP_DIR = os.getenv("TEMP_DIR", "data/temp")
LOG_FILE = os.getenv("LOG_FILE", "logs/process_log.txt")


def normalize_subject(subject_name: str) -> str:
    """
    Normalize subject/folder names to improve matching across cycles:
    - Lowercase
    - Strip whitespace
    - Remove common reply/forward prefixes (re:, fw:, fwd: repeated)
    - Collapse multiple spaces
    """
    if not subject_name:
        return ""
    name = subject_name.strip().lower()
    # Remove repeating prefixes like "fwd:", "fw:", "re:" at the start
    prefixes = ("fwd:", "fw:", "re:")
    changed = True
    while changed:
        changed = False
        for p in prefixes:
            if name.startswith(p):
                name = name[len(p):].lstrip()
                changed = True
    # Also handle plain words without colon at the start
    prefixes_plain = ("fwd ", "fw ", "re ")
    changed = True
    while changed:
        changed = False
        for p in prefixes_plain:
            if name.startswith(p):
                name = name[len(p):].lstrip()
                changed = True
    # Collapse multiple spaces
    name = " ".join(name.split())
    return name


def open_file_explorer(directory_path: str):
    """
    Open file explorer to the specified directory.
    Works on Windows, macOS, and Linux.
    """
    try:
        if platform.system() == "Windows":
            # Windows
            subprocess.run(["explorer", directory_path], check=True)
        elif platform.system() == "Darwin":
            # macOS
            subprocess.run(["open", directory_path], check=True)
        else:
            # Linux
            subprocess.run(["xdg-open", directory_path], check=True)
        
        print(f"📂 Opened file explorer to: {directory_path}")
    except Exception as e:
        print(f"⚠️ Could not open file explorer: {e}")
        print(f"📂 Please manually navigate to: {os.path.abspath(directory_path)}")

def convert_pdf_to_jpg(pdf_path, temp_dir):
    """Convert PDF to JPG images"""
    try:
        from pdf2image import convert_from_path
        images = convert_from_path(pdf_path)
        image_paths = []
        
        for i, image in enumerate(images):
            jpg_path = os.path.join(temp_dir, f"{os.path.splitext(os.path.basename(pdf_path))[0]}_page{i+1}.jpg")
            image.save(jpg_path, "JPEG")
            image_paths.append(jpg_path)
            
        return image_paths
    except Exception as e:
        print(f"❌ Error converting PDF {pdf_path}: {e}")
        return []

def main():
    import time
    import signal
    import sys
    
    # Global flag to control the continuous loop
    running = True
    
    def signal_handler(sig, frame):
        nonlocal running
        print("\n\n🛑 Ctrl+C detected. Stopping continuous processing...")
        running = False
    
    # Set up signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    print("🚀 Starting MOHRE Document Processing Service")
    print("📋 Press Ctrl+C to stop the service")
    print("⏰ Service will check for new emails every 3 minutes")
    print("="*60)
    
    cycle_count = 0
    
    while running:
        cycle_count += 1
        print(f"\n🔄 CYCLE #{cycle_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        try:
            # === STEP 0: Ensure output directory exists ===
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            print(f"📁 Output directory ensured: {OUTPUT_DIR}")
            
            # === STEP 1: Fetch emails ===
            print("📧 Fetching emails...")
            fetch_and_store_emails()

            # === STEP 2: Process each subject folder ===
            # Build sets of completed subjects to avoid reprocessing
            completed_normalized = set()
            completed_exact = set()
            if os.path.isdir(OUTPUT_DIR):
                for completed_folder in os.listdir(OUTPUT_DIR):
                    completed_path = os.path.join(OUTPUT_DIR, completed_folder)
                    if not os.path.isdir(completed_path):
                        continue
                    completed_exact.add(completed_folder)
                    completed_normalized.add(normalize_subject(completed_folder))

            # Process ONLY NEW inbox to avoid reprocessing archived downloads in this run
            download_dirs = [NEW_INPUT_DIR]
            processed_folders = set()

            for download_dir in download_dirs:
                if not os.path.exists(download_dir):
                    print(f"⚠️ Download directory not found: {download_dir}")
                    continue
                    
                print(f"📁 Processing from: {download_dir}")
                folders_to_process = os.listdir(download_dir)
                print(f"📂 Found {len(folders_to_process)} folders in {download_dir}")
                
                for subject_folder in folders_to_process:
                    if not running:  # Check if user wants to stop
                        break
                        
                    if subject_folder in processed_folders:
                        print(f"⏭️ Skipping already processed folder: {subject_folder}")
                        continue

                    # Skip if subject already exists in COMPLETED (normalized or exact)
                    # BUT: always process items in NEW_INPUT_DIR to allow re-processing/replies
                    normalized = normalize_subject(subject_folder)
                    if os.path.abspath(download_dir) != os.path.abspath(NEW_INPUT_DIR):
                        if normalized in completed_normalized or subject_folder in completed_exact:
                            print(f"⏭️ Skipping folder (already completed): {subject_folder}")
                            processed_folders.add(subject_folder)
                            continue
                    
                    # Check if folder already exists in completed directory (exact name match)
                    completed_folder_path = os.path.join(OUTPUT_DIR, subject_folder)
                    if os.path.exists(completed_folder_path):
                        # Check if the master text file exists (indicating complete processing)
                        master_text_files = [f for f in os.listdir(completed_folder_path) if f.endswith('_COMPLETE_DETAILS.txt')]
                        if master_text_files:
                            print(f"⏭️ Skipping folder already processed (found {len(master_text_files)} complete detail files): {subject_folder}")
                            processed_folders.add(subject_folder)
                            continue
                        else:
                            # Treat as complete to avoid reprocessing loops
                            print(f"⏭️ Skipping folder (exists in COMPLETED but no txt yet): {subject_folder}")
                            processed_folders.add(subject_folder)
                            continue
                    
                    subject_path = os.path.join(download_dir, subject_folder)
                    if not os.path.isdir(subject_path):
                        continue

                    print(f"\n🔍 Processing folder: {subject_folder}")
                    
                    # === STEP 2.1: Read email body.txt and sender info ===
                    email_text_path = os.path.join(subject_path, "email_body.txt")
                    sender_info_path = os.path.join(subject_path, "sender_info.json")
                    
                    email_text = ""
                    sender_info = {
                        'email': 'Unknown',
                        'name': 'Unknown',
                        'person_name': 'Unknown'
                    }
                    
                    if os.path.exists(email_text_path):
                        with open(email_text_path, "r", encoding="utf-8") as f:
                            email_text = f.read()
                        print(f"📧 Email body loaded: {len(email_text)} characters")
                        
                        # === STEP 2.1.5: Analyze email for MOHRE service ===
                        print("🔍 Analyzing email for MOHRE service...")
                        try:
                            mohre_analysis = analyze_email_for_mohre_service(email_text, subject_folder)
                            mohre_service_url = get_mohre_service_url(
                                mohre_analysis.get('service_category', 'Unknown'),
                                mohre_analysis.get('specific_service', 'Unknown')
                            )
                            print(f"✅ MOHRE Service Analysis: {mohre_analysis.get('specific_service', 'Unknown')}")
                            print(f"   Category: {mohre_analysis.get('service_category', 'Unknown')}")
                            print(f"   Confidence: {mohre_analysis.get('confidence_level', 'Low')}")
                            print(f"   Priority: {mohre_analysis.get('priority_level', 'Normal')}")
                        except Exception as e:
                            print(f"❌ Error analyzing email for MOHRE service: {e}")
                            mohre_analysis = {
                                "service_category": "Unknown",
                                "specific_service": "Unknown",
                                "confidence_level": "Low",
                                "key_indicators": [],
                                "additional_context": "Analysis failed",
                                "priority_level": "Normal",
                                "required_documents": [],
                                "reasoning": f"Analysis error: {str(e)}"
                            }
                            mohre_service_url = "https://www.mohre.gov.ae/en/services.aspx"
                    else:
                        mohre_analysis = {
                            "service_category": "Unknown",
                            "specific_service": "Unknown",
                            "confidence_level": "Low",
                            "key_indicators": [],
                            "additional_context": "No email body found",
                            "priority_level": "Normal",
                            "required_documents": [],
                            "reasoning": "No email body available for analysis"
                        }
                        mohre_service_url = "https://www.mohre.gov.ae/en/services.aspx"

                    # Ensure we consistently save outputs under the actual folder being processed
                    # This prevents mixing outputs if loop scoping ever changes
                    current_subject_folder = os.path.basename(subject_path)

                    # === STEP 2.1.6: Load sender info ===
                    if os.path.exists(sender_info_path):
                        try:
                            import json
                            with open(sender_info_path, "r", encoding="utf-8") as f:
                                sender_info = json.load(f)
                            print(f"👤 Sender info loaded: {sender_info['person_name']} ({sender_info['email']})")
                        except Exception as e:
                            print(f"⚠️ Error loading sender info: {e}")
                            sender_info = {
                                'email': 'Unknown',
                                'name': 'Unknown',
                                'person_name': 'Unknown'
                            }
                    else:
                        print(f"⚠️ No sender_info.json found, using default values")
                        sender_info = {
                            'email': 'Unknown',
                            'name': 'Unknown',
                            'person_name': 'Unknown'
                        }

                    # === STEP 2.2: Convert PDFs to JPGs ===
                    print("🔄 Converting PDFs to JPGs...")
                    all_image_paths = []
                    for filename in os.listdir(subject_path):
                        file_path = os.path.join(subject_path, filename)
                        if filename.lower().endswith(".pdf"):
                            print(f"📄 Converting: {filename}")
                            jpg_paths = convert_pdf_to_jpg(file_path, TEMP_DIR)
                            all_image_paths.extend(jpg_paths)
                        elif filename.lower().endswith((".jpg", ".jpeg", ".png")):
                            # Copy existing images to temp without compression (for best OCR quality)
                            temp_path = os.path.join(TEMP_DIR, filename)
                            if safe_copy_file(file_path, temp_path):
                                all_image_paths.append(temp_path)
                                print(f"📷 Copied image: {filename}")
                            else:
                                print(f"⚠️ Failed to copy image: {filename}")

                    if not all_image_paths:
                        print(f"⚠️ No images found in {subject_folder}")
                        # Still produce a summary-only COMPLETE_DETAILS.txt so we don't reprocess next cycle
                        subject_output_dir = os.path.join(OUTPUT_DIR, current_subject_folder)
                        os.makedirs(subject_output_dir, exist_ok=True)
                        summary_file = os.path.join(subject_output_dir, "Summary_COMPLETE_DETAILS.txt")
                        with open(summary_file, "w", encoding="utf-8") as f:
                            f.write("=" * 80 + "\n")
                            f.write(f"SUMMARY FOR: {subject_folder}\n")
                            f.write("=" * 80 + "\n\n")
                            f.write("📧 EMAIL SENDER INFORMATION\n")
                            f.write("-" * 40 + "\n")
                            f.write(f"Sender Name: {sender_info.get('name', 'N/A')}\n")
                            f.write(f"Sender Email: {sender_info.get('email', 'N/A')}\n")
                            f.write(f"Email Subject: {subject_folder}\n\n")
                            f.write("🏛️ MOHRE SERVICE ANALYSIS\n")
                            f.write("-" * 40 + "\n")
                            f.write(f"Service Category: {mohre_analysis.get('service_category', 'N/A')}\n")
                            f.write(f"Specific Service: {mohre_analysis.get('specific_service', 'N/A')}\n")
                            f.write(f"Confidence Level: {mohre_analysis.get('confidence_level', 'N/A')}\n")
                            f.write(f"Priority Level: {mohre_analysis.get('priority_level', 'N/A')}\n")
                            f.write(f"MOHRE Service URL: {get_mohre_service_url(mohre_analysis.get('service_category',''), mohre_analysis.get('specific_service',''))}\n")
                            additional = mohre_analysis.get('additional_context', '')
                            if additional:
                                f.write(f"Additional Context: {additional}\n")
                        print(f"📄 Created summary details file: {summary_file}")
                        processed_folders.add(subject_folder)
                        continue

                    # === STEP 2.3: Parse salary DOCX files ===
                    print("💰 Parsing salary DOCX files...")
                    salary_data = {}
            
                    # Look for salary DOCX files
                    docx_files = [f for f in os.listdir(subject_path) if f.lower().endswith('.docx') and 'salary' in f.lower()]
                    
                    for docx_file in docx_files:
                        try:
                            docx_path = os.path.join(subject_path, docx_file)
                            parsed_salary = parse_salary_docx(docx_path)
                            if parsed_salary:
                                salary_data.update(parsed_salary)
                                print(f"✅ Parsed salary from: {docx_file}")
                                
                                # Display salary breakdown
                                print("💰 Salary Breakdown:")
                                for key, value in parsed_salary.items():
                                    if key == "Employment_Terms":
                                        print(f"   📋 Employment Terms:")
                                        for term_key, term_value in value.items():
                                            print(f"      • {term_key.replace('_', ' ').title()}: {term_value}")
                                    else:
                                        print(f"   • {key.replace('_', ' ').title()}: {value}")
                            else:
                                print(f"⚠️ No salary data found in: {docx_file}")
                        except Exception as e:
                            print(f"❌ Error parsing salary from {docx_file}: {e}")

                    # === STEP 2.4: Classify all images with ResNet ===
                    print("🏷️ Classifying images with ResNet...")
                    classified_images = []
                    for img_path in all_image_paths:
                        try:
                            resnet_label = classify_image_resnet(img_path)
                            classified_images.append({
                                "path": img_path,
                                "label": resnet_label,
                                "filename": os.path.basename(img_path)
                            })
                            print(f"✅ {os.path.basename(img_path)} → {resnet_label}")
                        except Exception as e:
                            print(f"❌ Error classifying {os.path.basename(img_path)}: {e}")

                    # === STEP 2.5: Ensure certificate + attestation pairing ===
                    has_certificate = any(img["label"] == "certificate" for img in classified_images)
                    has_attestation = any(img["label"] in ["certificate_attestation", "attestation_label"] for img in classified_images)
                    
                    if has_certificate and not has_attestation:
                        print("⚠️ Certificate found but no attestation page. Looking for misclassified attestation...")
                        for img_data in classified_images:
                            if img_data["label"] in ["emirates_id", "emirates_id_2", "unknown"]:
                                # Reclassify as attestation_label for further processing
                                img_data["label"] = "attestation_label"
                                print(f"🔄 Reclassified {img_data['filename']} as attestation_label")

                    # === STEP 2.6: Rotate images if needed using Gemini 2.5 Flash (only specific document types) ===
                    print("🔄 Using Gemini 2.5 Flash to check and rotate images if needed...")
                    
                    # Only check rotation for specific document types after classification
                    rotation_check_types = ["passport_1", "passport_2", "personal_photo", "certificate"]
                    
                    for img_data in classified_images:
                        try:
                            # Only check rotation for specific document types
                            if img_data["label"] in rotation_check_types:
                                print(f"🔍 Checking rotation for {img_data['filename']} ({img_data['label']})...")
                                rotated_path = rotate_if_needed(img_data["path"])
                                if rotated_path != img_data["path"]:
                                    img_data["path"] = rotated_path
                                    print(f"✅ Gemini 2.5 Flash rotated {img_data['filename']} ({img_data['label']})")
                                else:
                                    print(f"✅ No rotation needed for {img_data['filename']} ({img_data['label']})")
                            else:
                                print(f"⏭️ Skipping rotation check for {img_data['filename']} ({img_data['label']}) - not in rotation check list")
                        except Exception as e:
                            print(f"⚠️ Error rotating {img_data['filename']}: {e}")

                    # === STEP 2.7: If ResNet detects attestation page, compress and copy to finished folder first ===
                    print("📋 Checking for attestation pages detected by ResNet...")
                    attestation_images = [img for img in classified_images if img["label"] in ["certificate_attestation", "attestation_label"]]
                    
                    for attestation_img in attestation_images:
                        try:
                            # Compress attestation page first
                            compressed_path = compress_image_to_jpg(
                                attestation_img["path"],
                                os.path.join(TEMP_DIR, f"{os.path.splitext(os.path.basename(attestation_img['path']))[0]}_compressed.jpg")
                            )
                            attestation_img["compressed_path"] = compressed_path
                            print(f"✅ Compressed attestation page: {os.path.basename(attestation_img['path'])}")
                            
                            # Copy to finished folder immediately
                            finished_folder = os.path.join(OUTPUT_DIR, current_subject_folder)
                            os.makedirs(finished_folder, exist_ok=True)
                            finished_path = os.path.join(finished_folder, f"{os.path.splitext(os.path.basename(attestation_img['path']))[0]}_attestation_label.jpg")
                            if safe_copy_file(compressed_path, finished_path):
                                attestation_img["finished_path"] = finished_path
                                print(f"✅ Copied attestation page to finished folder: {os.path.basename(finished_path)}")
                            else:
                                print(f"⚠️ Failed to copy attestation page to finished folder")
                        except Exception as e:
                            print(f"❌ Error processing attestation {attestation_img['filename']}: {e}")

                    # === STEP 2.8: Run YOLO cropping for ALL documents ===
                    print("✂️ Running YOLO cropping for ALL documents...")
                    for img_data in classified_images:
                        try:
                            # Use the path that was already processed (either compressed or original)
                            # All images should already be compressed from the initial processing
                            input_path = img_data["path"]
                            
                            # Run YOLO cropping for ALL documents
                            cropped_path = run_yolo_crop(input_path, TEMP_DIR)
                            img_data["cropped_path"] = cropped_path
                            print(f"✅ YOLO cropped {img_data['label']}: {os.path.basename(cropped_path)}")
                            
                        except Exception as e:
                            print(f"❌ Error cropping {img_data['filename']}: {e}")

                    # === STEP 2.9: Run OCR for all documents using cropped versions ===
                    print("📝 Running OCR for all documents using cropped versions...")
                    processed_images = []
                    
                    for img_data in classified_images:
                        try:
                            # Use cropped path for OCR (all documents)
                            ocr_path = img_data["cropped_path"]

                            # Run OCR
                            vision_data = run_enhanced_ocr(ocr_path)
                            img_data["ocr_text"] = vision_data.get("ocr_text", "")
                            img_data["extracted_fields"] = vision_data.get("extracted_fields", {})
                            img_data["document_type"] = vision_data.get("document_type", "unknown")
                            img_data["confidence"] = vision_data.get("confidence", 0.0)
                            
                            processed_images.append(img_data)
                            print(f"✅ OCR completed: {img_data['filename']} ({img_data['label']})")
                            
                        except Exception as e:
                            print(f"❌ Error processing {img_data['filename']}: {e}")
                            # Still add to processed_images even if OCR fails, with empty data
                            img_data["ocr_text"] = ""
                            img_data["extracted_fields"] = {}
                            img_data["document_type"] = "unknown"
                            img_data["confidence"] = 0.0
                            processed_images.append(img_data)
                            print(f"⚠️ Added {img_data['filename']} to processed list despite OCR error")

                    if not processed_images:
                        if classified_images:
                            print(f"⚠️ OCR failed for all images in {current_subject_folder}, but proceeding with empty OCR data")
                            # Use classified_images as processed_images with empty OCR data
                            for img_data in classified_images:
                                img_data["ocr_text"] = ""
                                img_data["extracted_fields"] = {}
                                img_data["document_type"] = "unknown"
                                img_data["confidence"] = 0.0
                            processed_images = classified_images
                        else:
                            print(f"⚠️ No processed images for {current_subject_folder}. Skipping folder.")
                            continue

                    # === STEP 3: Comprehensive Gemini structuring ===
                    print(f"🧠 Running comprehensive Gemini structuring for {current_subject_folder}...")
                    
                    # Collect OCR data by document type
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

                    result = structure_with_gemini(
                        passport_ocr_1=passport_ocr_1,
                        passport_ocr_2=passport_ocr_2,
                        emirates_id_ocr=emirates_id_ocr,
                        emirates_id_2_ocr=emirates_id_2_ocr,
                        employee_info=employee_info,
                        certificate_ocr=certificate_ocr,
                        salary_data=salary_data,  # Use the parsed salary data
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

                    # === STEP 4: Save everything ===
                    subject_output_dir = os.path.join(OUTPUT_DIR, current_subject_folder)
                    os.makedirs(subject_output_dir, exist_ok=True)

                    # Create comprehensive master text file
                    first_name = "Unknown"
            
                    # Handle both string and dictionary cases for final_structured
                    if isinstance(final_structured, str):
                        try:
                            import json
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
                        f.write(f"Job Title: {final_structured.get('Job Title', 'N/A')}\n")
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
                        
                        # MOHRE Service Analysis Section
                        f.write("🏛️ MOHRE SERVICE ANALYSIS\n")
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

                    # Save individual files
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
                        log_processed_file(LOG_FILE, img_data["filename"], final_path, img_data["label"])

                    # === STEP 5: Final compression of all saved files ===
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

                    processed_folders.add(current_subject_folder)
                    print(f"📂 Done with folder: {current_subject_folder}\n{'-'*40}")

                    # If this came from NEW_INPUT_DIR, archive it into INPUT_DIR for manual review
                    try:
                        if os.path.abspath(download_dir) == os.path.abspath(NEW_INPUT_DIR):
                            src = subject_path
                            dst = os.path.join(INPUT_DIR, current_subject_folder)
                            # Move folder; if exists, append a suffix
                            import shutil
                            if os.path.exists(dst):
                                base = dst
                                i = 1
                                while os.path.exists(f"{base}_{i}"):
                                    i += 1
                                dst = f"{base}_{i}"
                            shutil.move(src, dst)
                            print(f"📦 Archived processed folder to: {dst}")
                    except Exception as e:
                        print(f"⚠️ Could not archive folder {current_subject_folder}: {e}")

                    # === FINAL SUMMARY ===
                    print("\n" + "="*60)
                    print("📊 PROCESSING SUMMARY")
                    print("="*60)
                    print(f"✅ Successfully processed folders: {len(processed_folders)}")
                    if processed_folders:
                        print("📂 Processed folders:")
                        for folder in sorted(processed_folders):
                            print(f"   • {folder}")
                    print("="*60)
                    print("✅ All documents processed.")
                    
                    # Open file explorer to the COMPLETED directory
                    print(f"\n📂 Opening file explorer to view processed documents...")
                    absolute_output_dir = os.path.abspath(OUTPUT_DIR)
                    open_file_explorer(absolute_output_dir)
                    
        except Exception as e:
            print(f"❌ Error in processing cycle: {e}")
            print("🔄 Continuing to next cycle...")
        
        # Wait 3 minutes before next cycle (unless user wants to stop)
        if running:
            print(f"\n⏰ Waiting 3 minutes before next cycle...")
            print("📋 Press Ctrl+C to stop the service")
            
            total = 180
            while total > 0 and running:
                mins = total // 60
                secs = total % 60
                print(f"⏱️ {mins:02d}:{secs:02d} remaining...", end="\r", flush=True)
                time.sleep(1)
                total -= 1
            print("")
    
    print("\n🛑 Service stopped by user.")
    print("👋 Thank you for using MOHRE Document Processing Service!")

if __name__ == "__main__":
    main()