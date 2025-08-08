import os
import json
import shutil
# Add timestamp or UUID
from datetime import datetime
import os
import json
import shutil
from datetime import datetime
import subprocess
import platform

def open_file_explorer(path: str) -> None:
    """
    Open file explorer to the specified path.
    
    Args:
        path: Directory path to open
    """
    try:
        if platform.system() == "Windows":
            subprocess.run(["explorer", path], check=True)
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["open", path], check=True)
        else:  # Linux
            subprocess.run(["xdg-open", path], check=True)
        print(f"📂 Opened file explorer to: {path}")
    except Exception as e:
        print(f"⚠️ Could not open file explorer: {e}")

def safe_copy_file(src_path: str, dst_path: str) -> bool:
    """
    Safely copy a file with error handling.
    
    Args:
        src_path: Source file path
        dst_path: Destination file path
    
    Returns:
        bool: True if copy was successful, False otherwise
    """
    try:
        # Ensure destination directory exists
        dst_dir = os.path.dirname(dst_path)
        if dst_dir:
            os.makedirs(dst_dir, exist_ok=True)
        
        # Copy the file
        shutil.copy2(src_path, dst_path)
        return True
    except Exception as e:
        print(f"❌ Failed to copy {src_path} to {dst_path}: {e}")
        return False

def save_outputs(jpg_path: str, structured_json: dict, output_dir: str, base_name: str, gemini_response: str = None) -> str:
    """
    Save the final compressed JPG and structured JSON to output directory.
    Returns the full path to the saved JPG.
    """
    os.makedirs(output_dir, exist_ok=True)

    # No timestamp needed - keep base_name as is
    final_jpg_path = os.path.join(output_dir, base_name + ".jpg")
    final_json_path = os.path.join(output_dir, base_name + ".json")

    try:
        shutil.copy2(jpg_path, final_jpg_path)
    except Exception as e:
        raise RuntimeError(f"❌ Failed to copy image: {e}")

    try:
        with open(final_json_path, "w", encoding="utf-8") as f:
            json.dump(structured_json, f, ensure_ascii=False, indent=2)
    except Exception as e:
        raise RuntimeError(f"❌ Failed to write JSON: {e}")

    return final_jpg_path

def log_processed_file(log_file: str, original_file: str, saved_jpg_path: str, label: str):
    """
    Append log entry to a .txt file for processed documents.
    """
    with open(log_file, "a", encoding="utf-8") as log:
        log.write(f"Processed File: {original_file}\n")
        log.write(f"Saved JPG:     {saved_jpg_path}\n")
        log.write(f"Document Type: {label}\n")
        log.write("-" * 40 + "\n")
