import imaplib
import email
import os
import time
import shutil
import re
from email.header import decode_header
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

EMAIL = os.getenv("EMAIL_ADDRESS")
PASSWORD = os.getenv("EMAIL_PASSWORD")
IMAP_SERVER = os.getenv("IMAP_SERVER")
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "data/raw/downloads")  # legacy/initial archive
NEW_DOWNLOAD_DIR = os.getenv("NEW_DOWNLOAD_DIR", "data/raw/new_downloads")  # fresh per-cycle inbox
COMPLETED_DIR = os.getenv("COMPLETED_DIR", "data/processed/COMPLETED")

os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(NEW_DOWNLOAD_DIR, exist_ok=True)

def clean_filename(name):
    return "".join(c for c in name if c.isalnum() or c in (" ", ".", "_")).rstrip()

def normalize_subject(subject_name: str) -> str:
    """
    Normalize subject/folder names to improve matching:
    - Lowercase, strip
    - Remove leading reply/forward prefixes (re:, fw:, fwd:) repeatedly
    - Collapse multiple spaces
    """
    if not subject_name:
        return ""
    name = subject_name.strip().lower()
    prefixes = ("fwd:", "fw:", "re:")
    changed = True
    while changed:
        changed = False
        for p in prefixes:
            if name.startswith(p):
                name = name[len(p):].lstrip()
                changed = True
    prefixes_plain = ("fwd ", "fw ", "re ")
    changed = True
    while changed:
        changed = False
        for p in prefixes_plain:
            if name.startswith(p):
                name = name[len(p):].lstrip()
                changed = True
    name = " ".join(name.split())
    return name

def extract_person_name_from_email(email_address):
    """
    Extract person's name from email address.
    Example: hasan.altelly@gmail.com -> Hasan Altelly
    """
    if not email_address:
        return "Unknown"
    
    # Remove domain part
    local_part = email_address.split('@')[0]
    
    # Handle common patterns
    if '.' in local_part:
        # Split by dots and capitalize each part
        name_parts = local_part.split('.')
        name_parts = [part.capitalize() for part in name_parts if part]
        return ' '.join(name_parts)
    elif '_' in local_part:
        # Split by underscores and capitalize each part
        name_parts = local_part.split('_')
        name_parts = [part.capitalize() for part in name_parts if part]
        return ' '.join(name_parts)
    else:
        # Single word - just capitalize
        return local_part.capitalize()

def extract_sender_info(msg):
    """
    Extract sender information from email message.
    Returns a dictionary with sender details.
    """
    sender_info = {
        'email': '',
        'name': '',
        'person_name': 'Unknown'
    }
    
    # Get From field
    from_field = msg.get('From', '')
    if from_field:
        # Parse the From field which might be in format: "Name <email@domain.com>" or just "email@domain.com"
        if '<' in from_field and '>' in from_field:
            # Format: "Name <email@domain.com>"
            name_match = re.search(r'^([^<]+)', from_field)
            email_match = re.search(r'<([^>]+)>', from_field)
            
            if name_match:
                sender_info['name'] = name_match.group(1).strip().strip('"')
            if email_match:
                sender_info['email'] = email_match.group(1).strip()
        else:
            # Format: just "email@domain.com"
            sender_info['email'] = from_field.strip()
    
    # Extract person name from email address
    if sender_info['email']:
        sender_info['person_name'] = extract_person_name_from_email(sender_info['email'])
    
    return sender_info

def download_attachments(msg, subject_folder):
    attachments_saved = []
    for part in msg.walk():
        content_disposition = str(part.get("Content-Disposition"))
        if "attachment" in content_disposition:
            filename = part.get_filename()
            if filename:
                filename = clean_filename(filename)
                folder_path = os.path.join(NEW_DOWNLOAD_DIR, subject_folder)
                os.makedirs(folder_path, exist_ok=True)
                filepath = os.path.join(folder_path, filename)
                with open(filepath, "wb") as f:
                    f.write(part.get_payload(decode=True))
                attachments_saved.append(filepath)
                print(f"📎 Downloaded attachment: {filepath}")
    return attachments_saved

def save_email_body(msg, subject_folder):
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                body += part.get_payload(decode=True).decode(errors="ignore")
    else:
        body = msg.get_payload(decode=True).decode(errors="ignore")

    folder_path = os.path.join(NEW_DOWNLOAD_DIR, subject_folder)
    os.makedirs(folder_path, exist_ok=True)
    
    # Save email body
    body_path = os.path.join(folder_path, "email_body.txt")
    with open(body_path, "w", encoding="utf-8") as f:
        f.write(body)
    print(f"📝 Saved email body: {body_path}")
    
    # Extract and save sender information
    sender_info = extract_sender_info(msg)
    sender_path = os.path.join(folder_path, "sender_info.json")
    with open(sender_path, "w", encoding="utf-8") as f:
        import json
        json.dump(sender_info, f, ensure_ascii=False, indent=2)
    print(f"📧 Saved sender info: {sender_path}")
    print(f"👤 Sender: {sender_info['person_name']} ({sender_info['email']})")
    
    return body_path, sender_info

def fetch_and_store_emails(unseen_only=True, since_today=True):
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL, PASSWORD)
        mail.select("inbox")
    except Exception as e:
        print(f"❌ Failed to connect to email server: {e}")
        print("✅ Continuing without email processing...")
        return

    criteria = []
    if unseen_only:
        criteria.append("UNSEEN")
    if since_today:
        # Use a more reliable date format for 2025
        today = datetime.now().strftime("%d-%b-%Y")
        print(f"📅 Today's date: {today}")
        criteria.append(f'SINCE "{today}"')
    search_criteria = "(" + " ".join(criteria) + ")" if criteria else "ALL"

    print(f"📬 Searching emails with criteria: {search_criteria}")
    status, messages = mail.search(None, search_criteria)
    if status != "OK":
        print("❌ Failed to search emails.")
        mail.logout()
        return

    email_ids = messages[0].split()
    print(f"🔍 Found {len(email_ids)} email(s) matching criteria.")
    
    # If no emails found with current criteria, try without date restriction but still UNSEEN only
    if len(email_ids) == 0 and since_today and unseen_only:
        print("🔄 No unseen emails found with date restriction, trying without date filter but UNSEEN only...")
        search_criteria = "UNSEEN"
        print(f"📬 Searching emails with criteria: {search_criteria}")
        status, messages = mail.search(None, search_criteria)
        if status == "OK":
            email_ids = messages[0].split()
            print(f"🔍 Found {len(email_ids)} unseen email(s) without date restriction.")
    
    # If still no emails found, don't process any emails (don't fall back to ALL)
    if len(email_ids) == 0:
        print("✅ No unseen emails found. Skipping email processing.")
        try:
            mail.logout()
        except:
            pass
        return

    # Build normalized map of existing download subject folders to merge replies/forwards
    existing_downloads = {}
    try:
        if os.path.isdir(DOWNLOAD_DIR):
            for folder in os.listdir(DOWNLOAD_DIR):
                folder_path = os.path.join(DOWNLOAD_DIR, folder)
                if os.path.isdir(folder_path):
                    existing_downloads.setdefault(normalize_subject(folder), folder)
    except Exception as e:
        print(f"⚠️ Could not scan downloads directory: {e}")

    for eid in email_ids:
        _, msg_data = mail.fetch(eid, "(RFC822)")
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding or "utf-8", errors="ignore")
                requested_folder = clean_filename(subject) or "NoSubject"
                normalized_subject = normalize_subject(requested_folder)
                # Merge into existing folder if normalized match exists
                subject_folder = existing_downloads.get(normalized_subject, requested_folder)

                print(f"\n📥 Processing email: {subject} → folder: {subject_folder}")

                save_email_body(msg, subject_folder)
                download_attachments(msg, subject_folder)
                mail.store(eid, '+FLAGS', '\\Seen')

    try:
        mail.logout()
    except:
        pass
    print("✅ Finished checking inbox.\n")

def cleanup_old_files(days_old=60):
    now = time.time()
    cutoff = now - (days_old * 86400)
    for folder in os.listdir(DOWNLOAD_DIR):
        folder_path = os.path.join(DOWNLOAD_DIR, folder)
        if os.path.isdir(folder_path):
            folder_time = os.path.getmtime(folder_path)
            if folder_time < cutoff:
                try:
                    shutil.rmtree(folder_path)
                    print(f"🗑️ Deleted old folder: {folder_path}")
                except Exception as e:
                    print(f"⚠️ Could not delete old folder {folder_path}: {e}")

def safe_copy_file(src_path, dst_path):
    """
    Safely copy a file with error handling.
    Returns True if successful, False otherwise.
    """
    try:
        shutil.copy2(src_path, dst_path)
        return True
    except Exception as e:
        print(f"⚠️ Could not copy {src_path} to {dst_path}: {e}")
        return False

def safe_remove_directory(dir_path):
    """
    Safely remove a directory with error handling.
    Returns True if successful, False otherwise.
    """
    try:
        shutil.rmtree(dir_path)
        return True
    except Exception as e:
        print(f"⚠️ Could not remove directory {dir_path}: {e}")
        return False

# Optional: Continuous runner if run directly
if __name__ == "__main__":
    while True:
        print(f"\n🔄 Checking inbox at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        fetch_and_store_emails()
        cleanup_old_files(days_old=60)
        print("⏳ Sleeping for 5 minutes...\n")
        time.sleep(5 * 60)
