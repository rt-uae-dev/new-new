#!/usr/bin/env python3
"""
MOHRE Document Processing Pipeline - Refactored Version
Main orchestration module using modular components
"""

import os
import sys
import time
import signal
from typing import Set

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded environment variables from .env file")
except ImportError:
    print("⚠️ python-dotenv not installed, using system environment variables")
except Exception as e:
    print(f"⚠️ Error loading .env file: {e}")

# Import modular components
from email_processing import load_email_data
from document_processing import (
    convert_pdfs_to_images, classify_images, handle_certificate_attestation_pairing,
    rotate_images_if_needed, process_attestation_pages, run_yolo_cropping, run_ocr_processing
)
from output_generation import (
    parse_salary_documents, collect_ocr_data, run_gemini_structuring,
    create_comprehensive_text_file, save_individual_files, compress_final_files,
    extract_first_name
)
from folder_management import (
    get_completed_folders, should_skip_folder, check_existing_completion,
    create_summary_for_empty_folder, archive_processed_folder, get_folders_to_process
)
from email_parser import fetch_and_store_emails
from output_saving_utils import open_file_explorer

# Environment variables
NEW_DOWNLOAD_DIR = os.getenv("NEW_DOWNLOAD_DIR", "data/raw/new_downloads")
INPUT_DIR = os.getenv("INPUT_DIR", "data/raw/downloads")
NEW_INPUT_DIR = os.getenv("NEW_INPUT_DIR", "data/raw/new_downloads")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "data/processed/COMPLETED")
TEMP_DIR = os.getenv("TEMP_DIR", "data/temp")
LOG_FILE = os.getenv("LOG_FILE", "logs/processing.log")

# Global flag for graceful shutdown
running = True

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    global running
    print("\n🛑 Received interrupt signal. Stopping gracefully...")
    running = False

def process_single_folder(subject_path: str, subject_folder: str, download_dir: str, 
                         current_subject_folder: str, temp_dir: str, output_dir: str, 
                         log_file: str) -> bool:
    """
    Process a single folder through the complete pipeline.
    
    Returns:
        bool: True if processing was successful, False otherwise
    """
    try:
        print(f"\n🔍 Processing folder: {subject_folder}")
        
        # === STEP 1: Load email data ===
        email_text, sender_info, mohre_analysis, mohre_service_url = load_email_data(subject_path)
        
        # === STEP 2: Convert PDFs to images ===
        all_image_paths = convert_pdfs_to_images(subject_path, temp_dir)
        
        if not all_image_paths:
            print(f"⚠️ No images found in {subject_folder}")
            create_summary_for_empty_folder(subject_path, subject_folder, output_dir, 
                                          sender_info, mohre_analysis, mohre_service_url)
            return True
        
        # === STEP 3: Parse salary documents ===
        salary_data = parse_salary_documents(subject_path)
        
        # === STEP 4: Classify images ===
        classified_images = classify_images(all_image_paths)
        
        # === STEP 5: Handle certificate/attestation pairing ===
        handle_certificate_attestation_pairing(classified_images)
        
        # === STEP 6: Rotate images if needed ===
        rotate_images_if_needed(classified_images)
        
        # === STEP 7: Process attestation pages ===
        process_attestation_pages(classified_images, temp_dir, output_dir, current_subject_folder)
        
        # === STEP 8: Run YOLO cropping ===
        run_yolo_cropping(classified_images, temp_dir)
        
        # === STEP 9: Run OCR processing ===
        processed_images = run_ocr_processing(classified_images)
        
        if not processed_images:
            print(f"⚠️ No processed images for {current_subject_folder}. Skipping folder.")
            return False
        
        # === STEP 10: Collect OCR data ===
        ocr_data = collect_ocr_data(processed_images)
        
        # === STEP 11: Run Gemini structuring ===
        final_structured, gemini_response = run_gemini_structuring(
            current_subject_folder, ocr_data, salary_data, email_text, 
            processed_images, ocr_data[6], sender_info
        )
        
        # === STEP 12: Extract first name ===
        first_name, full_name = extract_first_name(final_structured)
        
        # === STEP 13: Create output directory ===
        subject_output_dir = os.path.join(output_dir, current_subject_folder)
        os.makedirs(subject_output_dir, exist_ok=True)
        
        # === STEP 14: Create comprehensive text file ===
        create_comprehensive_text_file(
            subject_output_dir, first_name, full_name, final_structured, 
            sender_info, subject_folder, mohre_analysis, mohre_service_url, salary_data,
            processed_images, email_text
        )
        
        # === STEP 15: Save individual files ===
        save_individual_files(processed_images, final_structured, subject_output_dir, 
                            first_name, gemini_response, log_file)
        
        # === STEP 16: Compress final files ===
        compress_final_files(processed_images, subject_output_dir, first_name)
        
        return True
        
    except Exception as e:
        print(f"❌ Error processing folder {subject_folder}: {e}")
        return False

def main():
    """Main processing loop."""
    global running
    
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"📁 Output directory ensured: {OUTPUT_DIR}")
    
    cycle_count = 0
    
    while running:
        cycle_count += 1
        print(f"\n🔄 CYCLE #{cycle_count} - {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        try:
            # === STEP 1: Fetch emails ===
            print("📧 Fetching emails...")
            fetch_and_store_emails()
            
            # === STEP 2: Get completed folders ===
            completed_normalized, completed_exact = get_completed_folders(OUTPUT_DIR)
            
            # === STEP 3: Get folders to process ===
            download_dirs = [NEW_DOWNLOAD_DIR]  # Only process from new_downloads
            folders_to_process = get_folders_to_process(download_dirs)
            
            processed_folders: Set[str] = set()
            
            # === STEP 4: Process each folder ===
            for download_dir, subject_folder in folders_to_process:
                if not running:  # Check if user wants to stop
                    break
                    
                if subject_folder in processed_folders:
                    print(f"⏭️ Skipping already processed folder: {subject_folder}")
                    continue

                # Check if folder should be skipped
                if should_skip_folder(subject_folder, download_dir, NEW_INPUT_DIR, 
                                    completed_normalized, completed_exact):
                    processed_folders.add(subject_folder)
                    continue
                
                # Check existing completion
                if check_existing_completion(subject_folder, OUTPUT_DIR):
                    processed_folders.add(subject_folder)
                    continue
                
                subject_path = os.path.join(download_dir, subject_folder)
                if not os.path.isdir(subject_path):
                    continue

                # Ensure we consistently save outputs under the actual folder being processed
                current_subject_folder = os.path.basename(subject_path)
                
                # Process the folder
                success = process_single_folder(
                    subject_path, subject_folder, download_dir, current_subject_folder,
                    TEMP_DIR, OUTPUT_DIR, LOG_FILE
                )
                
                if success:
                    processed_folders.add(current_subject_folder)
                    print(f"📂 Done with folder: {current_subject_folder}\n{'-'*40}")
                    
                    # Archive processed folder
                    archive_processed_folder(subject_path, current_subject_folder, 
                                           download_dir, NEW_INPUT_DIR, INPUT_DIR)
            
            # === STEP 5: Final summary ===
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
                
                # Only open file explorer if documents were actually processed
                print(f"\n📂 Opening file explorer to view processed documents...")
                absolute_output_dir = os.path.abspath(OUTPUT_DIR)
                open_file_explorer(absolute_output_dir)
            else:
                print("="*60)
                print("⏭️ No documents processed in this cycle.")
            
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
