#!/usr/bin/env python3
"""
Folder Management Module
Handles folder management including subject normalization, completion checking, and archiving
"""

import os
import re
import shutil
from typing import Set, List

def normalize_subject(subject_name: str) -> str:
    """
    Normalize subject name by removing common prefixes and suffixes.
    This helps match related emails (replies, forwards) to the same folder.
    """
    # Remove common email prefixes
    prefixes_to_remove = [
        r'^re:\s*',
        r'^fw:\s*', 
        r'^fwd:\s*',
        r'^fwd\s*',
        r'^forward:\s*',
        r'^forward\s*',
        r'^reply:\s*',
        r'^reply\s*'
    ]
    
    normalized = subject_name.lower().strip()
    
    # Remove prefixes
    for prefix in prefixes_to_remove:
        normalized = re.sub(prefix, '', normalized, flags=re.IGNORECASE)
    
    # Remove extra whitespace
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    return normalized

def get_completed_folders(output_dir: str) -> tuple[Set[str], Set[str]]:
    """
    Get sets of completed folder names (both normalized and exact).
    
    Returns:
        tuple: (completed_normalized, completed_exact)
    """
    completed_normalized = set()
    completed_exact = set()
    
    if not os.path.exists(output_dir):
        return completed_normalized, completed_exact
    
    for folder_name in os.listdir(output_dir):
        folder_path = os.path.join(output_dir, folder_name)
        if os.path.isdir(folder_path):
            # Check if folder contains a complete details file
            complete_files = [f for f in os.listdir(folder_path) if f.endswith('_COMPLETE_DETAILS.txt')]
            if complete_files:
                completed_exact.add(folder_name)
                completed_normalized.add(normalize_subject(folder_name))
    
    return completed_normalized, completed_exact

def should_skip_folder(subject_folder: str, download_dir: str, new_input_dir: str, 
                      completed_normalized: Set[str], completed_exact: Set[str]) -> bool:
    """
    Determine if a folder should be skipped based on completion status.
    
    Returns:
        bool: True if folder should be skipped, False otherwise
    """
    normalized = normalize_subject(subject_folder)
    
    # Skip if subject already exists in COMPLETED (normalized or exact)
    # BUT: always process items in NEW_INPUT_DIR to allow re-processing/replies
    if os.path.abspath(download_dir) != os.path.abspath(new_input_dir):
        if normalized in completed_normalized or subject_folder in completed_exact:
            print(f"⏭️ Skipping folder (already completed): {subject_folder}")
            return True
    
    return False

def check_existing_completion(subject_folder: str, output_dir: str) -> bool:
    """
    Check if folder already exists in completed directory with complete processing.
    
    Returns:
        bool: True if folder should be skipped, False otherwise
    """
    completed_folder_path = os.path.join(output_dir, subject_folder)
    if os.path.exists(completed_folder_path):
        # Check if the master text file exists (indicating complete processing)
        master_text_files = [f for f in os.listdir(completed_folder_path) if f.endswith('_COMPLETE_DETAILS.txt')]
        if master_text_files:
            print(f"⏭️ Skipping folder already processed (found {len(master_text_files)} complete detail files): {subject_folder}")
            return True
        else:
            # Treat as complete to avoid reprocessing loops
            print(f"⏭️ Skipping folder (exists in COMPLETED but no txt yet): {subject_folder}")
            return True
    
    return False

def create_summary_for_empty_folder(subject_path: str, subject_folder: str, output_dir: str, 
                                  sender_info: dict, mohre_analysis: dict, mohre_service_url: str) -> None:
    """Create a summary file for folders with no images or PDFs."""
    subject_output_dir = os.path.join(output_dir, subject_folder)
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
        f.write(f"MOHRE Service URL: {mohre_service_url}\n")
        additional = mohre_analysis.get('additional_context', '')
        if additional:
            f.write(f"Additional Context: {additional}\n")
    
    print(f"📄 Created summary details file: {summary_file}")

def archive_processed_folder(subject_path: str, current_subject_folder: str, download_dir: str, 
                           new_input_dir: str, input_dir: str) -> None:
    """Archive processed folder to appropriate location."""
    try:
        if os.path.abspath(download_dir) == os.path.abspath(new_input_dir):
            src = subject_path
            dst = os.path.join(input_dir, current_subject_folder)
            # Move folder; if exists, append a suffix
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

def get_folders_to_process(download_dirs: List[str]) -> List[tuple[str, str]]:
    """
    Get list of folders to process from download directories.
    
    Returns:
        List[tuple]: List of (download_dir, folder_name) tuples
    """
    folders_to_process = []
    
    for download_dir in download_dirs:
        if not os.path.exists(download_dir):
            print(f"⚠️ Download directory not found: {download_dir}")
            continue
            
        print(f"📁 Processing from: {download_dir}")
        folder_names = os.listdir(download_dir)
        print(f"📂 Found {len(folder_names)} folders in {download_dir}")
        
        for folder_name in folder_names:
            folders_to_process.append((download_dir, folder_name))
    
    return folders_to_process
