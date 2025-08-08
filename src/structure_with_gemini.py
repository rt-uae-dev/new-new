import google.generativeai as genai
import os
import json
try:
    from attestation_utils import validate_attestation_numbers
except ImportError:
    # If attestation_utils is not available, create a dummy function
    def validate_attestation_numbers(ocr_text, extracted_numbers):
        return extracted_numbers

# Configure Google Gemini API
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
else:
    print("⚠️ GEMINI_API_KEY not set - job extraction may be limited")

def post_process_structured_data(structured_data: dict, google_metadata: dict) -> dict:
    """
    Post-process structured data to ensure Document AI extracted fields are properly mapped
    """
    if not structured_data or not google_metadata:
        return structured_data
    
    # Check for Residence_Number in Document AI metadata and map to Identity_Number
    for field_type, fields in google_metadata.items():
        if isinstance(fields, dict) and 'Residence_Number' in fields:
            residence_number = fields['Residence_Number']
            current_identity = structured_data.get('Identity_Number')
            if residence_number and (not current_identity or current_identity == 'null' or current_identity is None):
                print(f"🔧 Post-processing: Mapping Residence_Number '{residence_number}' to Identity_Number")
                structured_data['Identity_Number'] = residence_number
                break
    
    # Check for UID_Number in Document AI metadata - prioritize emirates_id_2_fields
    uid_number = None
    # First, try to get UID from emirates_id_2_fields (preferred source)
    if 'emirates_id_2_fields' in google_metadata and isinstance(google_metadata['emirates_id_2_fields'], dict):
        if 'UID_Number' in google_metadata['emirates_id_2_fields']:
            uid_number = google_metadata['emirates_id_2_fields']['UID_Number']
            print(f"🔧 Post-processing: Found UID_Number '{uid_number}' in emirates_id_2_fields")
    
    # If not found in emirates_id_2_fields, look in other fields
    if not uid_number:
        for field_type, fields in google_metadata.items():
            if isinstance(fields, dict) and 'UID_Number' in fields:
                uid_number = fields['UID_Number']
                print(f"🔧 Post-processing: Found UID_Number '{uid_number}' in {field_type}")
                break
    
    # Apply UID mapping if found and needed
    current_uid = structured_data.get('UID_Number')
    if uid_number and (not current_uid or current_uid == 'null' or current_uid is None):
        print(f"🔧 Post-processing: Mapping UID_Number '{uid_number}' to UID_Number")
        structured_data['UID_Number'] = uid_number
    
    # Post-process job fields from Document AI metadata
    # Extract Previous Job from EID fields
    for field_type, fields in google_metadata.items():
        if isinstance(fields, dict) and 'Job Title' in fields:
            job_title = fields['Job Title']
            if job_title and job_title != 'null' and job_title is not None:
                if field_type in ['emirates_id_fields', 'emirates_id_2_fields']:
                    print(f"🔧 Post-processing: Found Previous Job '{job_title}' in {field_type}")
                    structured_data['Previous_Job'] = job_title
                elif field_type == 'employee_info_fields':
                    print(f"🔧 Post-processing: Found Employee Info Job '{job_title}' in {field_type}")
                    structured_data['Employee_Info_Job'] = job_title
                break
    
    return structured_data

def structure_with_gemini(
    passport_ocr_1: str,
    passport_ocr_2: str,
    emirates_id_ocr: str,
    emirates_id_2_ocr: str,
    employee_info: str,
    certificate_ocr: str,
    salary_data: dict,
    email_text: str,
    resnet_label: str,
    google_metadata: dict,
    sender_info: dict = None
) -> dict:
    prompt = f"""
You are an expert MOHRE document structuring assistant.
Use the provided OCR text, email body, classification labels, salary data, and Document AI extracted fields to generate a clean JSON structure.

IMPORTANT: Prioritize Document AI extracted fields over raw OCR text for accuracy.
CRITICAL: If Document AI has extracted specific fields (like passport numbers, issue places, etc.), use those values directly.
CRITICAL: Check the "DOCUMENT AI EXTRACTED FIELDS" section below for all available extracted fields before searching OCR text.
CRITICAL: For Identity Number/File Number, look for "Residence_Number" field in Document AI metadata.
CRITICAL: For U.I.D Number, look for "UID_Number" field in Document AI metadata.
CRITICAL: If "Residence_Number" is found in Document AI metadata, use that value for "Identity_Number" field.
CRITICAL: If "UID_Number" is found in Document AI metadata, use that value for "UID_Number" field.

IMPORTANT: Prioritize data from Emirates ID (EID) and Passport over all other sources for accuracy.

CRITICAL RULE: Passport Issue Place must be the specific place where the passport was issued. Look for fields like "Place of Issue", "Authority", "जारी करने का स्थान", "Oude and Place" in the passport. If no specific issue place is found, then use the issuing country.

Follow these rules:
1. **Full Name**: 
   - FIRST PRIORITY: Document AI extracted "Full Name" field (if available)
   - SECOND PRIORITY: Passport page 1 - look for "Given Name(s)" or "Name" field
   - THIRD PRIORITY: Emirates ID (EID) - look for "Name:" field (only if passport name is incomplete)
   - FOURTH PRIORITY: Employee info form
   - SPECIAL RULE FOR INDIAN PASSPORTS: If nationality is INDIAN and Father's Name is found (from passport page 2 or employee info), append Father's Name to Full Name (e.g., "YOGESHKUMAR ASHOKBHAI SANT" becomes "YOGESHKUMAR ASHOKBHAI SANT ASHOKBHAI BABURAO")
   - For other nationalities, never change the Full Name.
   - Use EID to supplement any missing parts of the name from passport.

2. **Date of Birth**: 
   - FIRST PRIORITY: Document AI extracted "Date of Birth" field (if available)
   - SECOND PRIORITY: Emirates ID (EID) - look for "Date of Birth" or "تاريخ الميلاد"
   - THIRD PRIORITY: Passport page 1 - look for "Date of Birth" field
   - FOURTH PRIORITY: Employee info form
   - Must be in DD/MM/YYYY or DD-MM-YYYY format. If incomplete (like "11/1979"), try to find complete date from other sources.

3. **Nationality**: 
   - FIRST PRIORITY: Document AI extracted "Nationality" field (if available)
   - SECOND PRIORITY: Passport page 1 - look for "Nationality" field
   - THIRD PRIORITY: Emirates ID (EID)
   - FOURTH PRIORITY: Employee info form
   - CRITICAL: Simplify nationality names:
     * "PALESTINIAN" → "PALESTINE"
     * "INDIAN" → "INDIA"
     * "LEBANESE" → "LEBANON"
     * "EGYPTIAN" → "EGYPT"
     * "PAKISTANI" → "PAKISTAN"
     * "BANGLADESHI" → "BANGLADESH"
     * "SRI LANKAN" → "SRI LANKA"
     * "NEPALI" → "NEPAL"
     * "PHILIPPINE" → "PHILIPPINES"
     * "FILIPINO" → "PHILIPPINES"

4. **Passport Number**: 
   - FIRST PRIORITY: Document AI extracted "Passport Number" field (if available)
   - SECOND PRIORITY: Passport page 1 - look for "Passport No" or "رقم الجواز"
   - THIRD PRIORITY: Emirates ID (EID)
   - FOURTH PRIORITY: Employee info form

5. **EID Number (Emirates ID Number)**: 
   - FIRST PRIORITY: Document AI extracted "EID Number" field (if available)
   - SECOND PRIORITY: Emirates ID (EID) - look for "ID Number" or "رقم الهوية" (format: 784-XXXX-XXXXXXX-X)
   - THIRD PRIORITY: Employee info form - look for "EID" or "Emirates ID Number"
   - FOURTH PRIORITY: Any other document with EID/Identity number
   - NOTE: EID numbers always start with "784"
   - IMPORTANT: Only EID numbers start with "784"

6. **EID Issue Date**: 
   - FIRST PRIORITY: Document AI extracted "Issue Date" field from Emirates ID (if available)
   - SECOND PRIORITY: Emirates ID (EID) - look for "Issue Date", "Date of Issue", "تاريخ الإصدار"
   - THIRD PRIORITY: Any document with EID issue date
   - Must be in DD/MM/YYYY or DD-MM-YYYY format

7. **EID Expiry Date**: 
   - FIRST PRIORITY: Document AI extracted "Expiry Date" field from Emirates ID (if available)
   - SECOND PRIORITY: Emirates ID (EID) - look for "Expiry Date", "Date of Expiry", "تاريخ انتهاء الصلاحية"
   - THIRD PRIORITY: Any document with EID expiry date
   - Must be in DD/MM/YYYY or DD-MM-YYYY format

8. **Identity Number/File Number**: 
   - FIRST PRIORITY: Document AI extracted "Identity Number" field (if available)
   - SECOND PRIORITY: Document AI extracted "Residence Number" field (if available) - this is the file number
   - THIRD PRIORITY: Look for numbers in format "XXX/YYYY/Z/ZZZZZZ" (e.g., "101/2019/2/179119", "202/2020/1/123456")
   - FOURTH PRIORITY: Work permit cancellation documents - look for "File No", "Identity No", "رقم الهوية", or similar fields
   - FIFTH PRIORITY: Residence cancellation documents - look for "Identity No", "رقم الهوية", or "File Number"
   - SIXTH PRIORITY: Any document with file numbers in this format
   - SEVENTH PRIORITY: Employee info form or other official documents
   - CRITICAL: Look for patterns like "101/2019/2/179119", "202/2020/1/123456", etc.
   - CRITICAL: Search the ENTIRE OCR text for these patterns, even if Document AI didn't extract them as structured fields
   - CRITICAL: The residence number IS the file number for residence cancellation documents
   - CRITICAL: If Document AI extracted "Residence_Number" field, use that value for "Identity_Number" field
   - CRITICAL: Check the Document AI metadata section below for "Residence_Number" field
   - CRITICAL: The "Residence_Number" field from Document AI should be mapped to "Identity_Number" field in the output
   - This is different from EID number - it's a government file reference

9. **U.I.D Number**: 
   - FIRST PRIORITY: Document AI extracted "UID Number" field (if available)
   - SECOND PRIORITY: Look for numbers in format "XXXXXXX" (e.g., "2188862", "1234567")
   - THIRD PRIORITY: Residence cancellation documents - look for "U.I.D No", "U.I.D", "UID", "Unique Identity Number", or "رقم الهوية الفريد"
   - FOURTH PRIORITY: Work permit cancellation documents - look for "U.I.D", "UID", or "Unique Identity"
   - FIFTH PRIORITY: Any document with U.I.D references
   - SIXTH PRIORITY: Employee info form or other official documents
   - CRITICAL: Look for 7-digit numbers that are NOT EID numbers (EID starts with 784)
   - CRITICAL: Search the ENTIRE OCR text for these patterns, even if Document AI didn't extract them as structured fields
   - CRITICAL: Look for any 7-digit numbers in the raw text that could be UID numbers
   - CRITICAL: Check the Document AI metadata section below for "UID_Number" field
   - EXAMPLES: "2188862", "1234567", "9876543"
   - This is different from EID and Identity numbers

10. **Father's Name**: 
   - FIRST PRIORITY: Document AI extracted "Father's Name" field (if available)
   - SECOND PRIORITY: Passport page 2 - look for "Father" or "Guardian" field
   - THIRD PRIORITY: Employee info form
   - CRITICAL: Must provide Arabic translation in "Father's Name (AR)" field
   - EXAMPLES: 
     * "ASHOKBHAI BABURAD" → "أشوكبهاي بابوراو"
     * "MOUSTAPHA" → "مصطفى"
     * "AHMED" → "أحمد"

11. **Mother's Name**: 
   - FIRST PRIORITY: Document AI extracted "Mother's Name" field (if available)
   - SECOND PRIORITY: Passport page 2 - look for "Mother" field
   - THIRD PRIORITY: Employee info form
   - Must be one word (first found).
   - CRITICAL: Must provide Arabic translation in "Mother's Name (AR)" field
   - EXAMPLES:
     * "PUSHPABEN" → "بوشبابين"
     * "Mona" → "منى"
     * "Fatima" → "فاطمة"

12. **Place of Birth**: 
    - FIRST PRIORITY: Document AI extracted "Place of Birth" field (if available)
    - SECOND PRIORITY: Passport page 1 - look for "Place of Birth" field
    - THIRD PRIORITY: Employee info form
    - FOURTH PRIORITY: Use nationality as fallback
    - CRITICAL: This is where the person was born, NOT where the passport was issued

13. **Passport Issue Place**: 
    - FIRST PRIORITY: Document AI extracted "Passport Issue Place" field (if available)
    - SECOND PRIORITY: Passport page 1 or 2 - look for "Place of Issue", "Authority", "जारी करने का स्थान", "Oude and Place", or similar fields
    - THIRD PRIORITY: Employee info form
    - FOURTH PRIORITY: Extract the issuing country from passport text (look for country names like "Republic of Lebanon", "Republic of India", "Arab Republic of Egypt", etc.)
    - FIFTH PRIORITY: Use passport country code (LBN = Lebanon, IND = India, EGY = Egypt, etc.)
    - SIXTH PRIORITY: Use nationality as fallback
    - CRITICAL: Never use UAE addresses, place of birth, or other location data as passport issue place
    - EXAMPLES: 
      * Lebanese passport with "الجمهورية اللبنانية / Republic of Lebanon" → "LEBANON"
      * Indian passport with "भारत गणराज्य REPUBLIC OF INDIA" → "INDIA"
      * Egyptian passport with "جمهورية مصر العربية / Arab Republic of Egypt" → "EGYPT"
      * Passport with country code "LBN" → "LEBANON"
      * Passport with country code "EGY" → "EGYPT"
      * Passport with country code "IND" → "INDIA"
      * Indian passport with "Oude and Place: DUBAI" → "DUBAI"

14. **Passport Issue Date**: 
    - FIRST PRIORITY: Document AI extracted "Issue Date" field (if available)
    - SECOND PRIORITY: Passport page 1 - look for "Date of Issue", "Issue Date", "Date d'émission", "تاريخ الإصدار", or similar fields
    - THIRD PRIORITY: Passport page 2 - look for issue date fields
    - FOURTH PRIORITY: Employee info form - look for passport issue date
    - Must be in DD/MM/YYYY or DD-MM-YYYY format
    - If found in different format, convert to DD/MM/YYYY

15. **Passport Expiry Date**: 
    - FIRST PRIORITY: Document AI extracted "Expiry Date" field (if available)
    - SECOND PRIORITY: Passport page 1 - look for "Date of Expiry", "Expiry Date", "Date d'expiration", "تاريخ انتهاء الصلاحية", or similar fields
    - THIRD PRIORITY: Passport page 2 - look for expiry date fields
    - FOURTH PRIORITY: Employee info form - look for passport expiry date
    - Must be in DD/MM/YYYY or DD-MM-YYYY format
    - If found in different format, convert to DD/MM/YYYY

16. **Home Phone Number**: 
    - FIRST PRIORITY: Document AI extracted "Phone Number" field (if available)
    - SECOND PRIORITY: Emirates ID (EID) - look for phone numbers in contact information
    - THIRD PRIORITY: Employee info form - look for "Phone", "Mobile", "Contact" fields
    - FOURTH PRIORITY: Passport page 2 - look for contact information
    - FIFTH PRIORITY: Any document with phone numbers
    - CRITICAL RULES:
      * If phone number starts with "+", replace "+" with "00"
      * If phone number starts with "00", keep as is
      * If phone number starts with "971", add "00" prefix
      * If phone number is 9 digits and starts with "5", add "00971" prefix
      * If phone number is 10 digits and starts with "05", replace "05" with "009715"
      * If phone number is 12 digits and starts with "971", add "00" prefix
    - EXAMPLES:
      * "+971501234567" → "00971501234567"
      * "971501234567" → "00971501234567"
      * "501234567" → "00971501234567"
      * "0501234567" → "00971501234567"
      * "00971501234567" → "00971501234567" (keep as is)
    - IMPORTANT: Look for the most recent/current phone number, not old ones

17. **Home Address**: 
    - FIRST PRIORITY: Passport page 2 - look for address section
    - SECOND PRIORITY: Employee info form - look for "Address" field
    - Extract only: Area, City, Province/State
    - Example: "E 108 CHANDRANAGAR COLONY BEHIND SUVARNALAXMI APARTMENTS WAGHODIA ROAD, VADODARA PIN:390019,GUJARAT, INDIA" becomes "VADODARA, GUJARAT"
    - Remove PIN codes, street details, building numbers

16. **UAE Address**: 
    - FIRST PRIORITY: Employee info form - look for "Primary Address In UAE" or address fields
    - SECOND PRIORITY: Look for UAE addresses in any document
    - Extract: Area, City/Emirate (both parts)
    - Example: "Madinat Zayed, Al Yam street, B841 building, F202" becomes "Madinat Zayed, Abu Dhabi"
    - Example: "B841 building, F202, Abu Dhabi" becomes "Abu Dhabi"
    - Example: "Al Ain, Abu Dhabi" becomes "Al Ain, Abu Dhabi"
    - Example: "Dubai Marina, Dubai" becomes "Dubai Marina, Dubai"
    - Remove building numbers, apartment numbers, street details
    - Include both the specific area and the city/emirate when available

17. **Job Information** (extract from multiple sources):
    - **Certificate Job**: 
      * FIRST PRIORITY: Extract from certificate/degree OCR text
      * Look for degree titles like "Bachelor of Engineering", "Master of Science", "Electrical Engineering", "Computer Science", "Mechanical Engineering"
      * Look for field of study or specialization mentioned in the certificate
      * Example: "Bachelor of Engineering in Electrical Engineering" → "Electrical Engineering"
      * Example: "Master of Science in Computer Science" → "Computer Science"
      * If no specific degree/field found, set to null
    - **HR Manager Request**: 
      * FIRST PRIORITY: Extract from email body text
      * SECOND PRIORITY: Extract from email subject line
      * Look for job titles like "Engineer", "Manager", "Supervisor", "Coordinator", "Technician"
      * Look for phrases like "looking for", "need", "require", "seeking"
      * Example: "looking for an Engineer" → "Engineer"
      * Example: "need a Supervisor" → "Supervisor"
      * If no job request found in email, set to null
    - **Previous Job**: 
      * FIRST PRIORITY: Extract from EID OCR (emirates_id_fields or emirates_id_2_fields)
      * Look for "Job Title" field in Document AI extracted fields
      * Example: "Supervisor Construction Electrical" → "Supervisor Construction Electrical"
      * If no job title found in EID, set to null
    - **Employee Info Form Job**: 
      * Extract from employee info form OCR if available
      * Look for "Profession" or "Job Title" fields
      * If no job info found in employee form, set to null
    - Return as separate fields: "Certificate_Job", "HR_Manager_Request", "Previous_Job", "Employee_Info_Job"

18. **Salary Information**:
    - CRITICAL: If salary_data is provided and contains salary information, use ONLY the salary_data values
    - DO NOT extract salary from OCR text or other sources if salary_data is available
    - FIRST PRIORITY: If salary_data has "Total", use that value (e.g., "19170 AED")
    - SECOND PRIORITY: If salary_data has "Total Salary", use that value (e.g., "AED 96,000")
    - THIRD PRIORITY: If salary_data has "Basic", use that value (e.g., "5453 AED")
    - FOURTH PRIORITY: If salary_data has "Basic Salary per Month", use that value
    - FIFTH PRIORITY: If salary_data is a simple number, use it directly
    - If no salary data is available, set to null
    - DO NOT return the entire salary_data dictionary - extract the main salary value only
    - IMPORTANT: Always include "AED" in the salary value if it's not already present
    - CRITICAL: Ignore any salary-like numbers found in OCR text if salary_data is provided
    - ENHANCED: Include detailed salary breakdown and employment terms if available:
      * Basic Salary
      * Housing Allowance
      * Transport Allowance
      * Other Allowances
      * Total Package
      * Probation Period
      * Notice Period
      * Working Hours
      * Contract Duration
      * Annual Leave
      * Sick Leave
      * Insurance Coverage
      * Visa Status
      * Flight Tickets
      * Accommodation Provided
      * Transport Provided

19. **Document Type**: Use ResNet prediction and Google Vision metadata.

20. **Document-Specific Extraction**:
    - **Residence Cancellation Documents**: 
      * Look specifically for UID numbers (7-digit format)
      * Look for Identity numbers (XXX/YYYY/ZZZZZZZ format)
      * Look for cancellation dates and reasons
      * CRITICAL: Search entire OCR text for any 7-digit numbers that could be UID
    - **Work Permit Cancellation Documents**:
      * Look specifically for File numbers (XXX/YYYY/ZZZZZZZ format)
      * Look for cancellation reference numbers
      * Look for cancellation dates and reasons
      * CRITICAL: Search entire OCR text for any 7-digit numbers that could be File numbers
    - **Certificate Attestation Documents**:
      * Look for attestation numbers (10-15 digits)
      * Look for attestation dates and authorities
    - **Employee Information Forms**:
      * Look for all personal details (name, DOB, nationality, etc.)
      * Look for employment details (job title, salary, etc.)

21. **Arabic Translations**: 
    - Translate Full Name, Father's Name, Mother's Name, Place of Birth, and Passport Issue Place to Arabic
    - IMPORTANT: For Indian passports, translate the COMPLETE name (including appended father's name) to Arabic
    - If missing, use nationality as fallback
    - CRITICAL: You MUST provide Arabic translations for these fields:
      * "Full Name (AR)" - Arabic translation of the full name
      * "Father's Name (AR)" - Arabic translation of the father's name
      * "Mother's Name (AR)" - Arabic translation of the mother's name
      * "Nationality (AR)" - Arabic translation of nationality (e.g., "INDIA" → "الهند")
      * "Place of Birth (AR)" - Arabic translation of place of birth
      * "Passport Issue Place (AR)" - Arabic translation of passport issue place
    - EXAMPLES:
      * "HARI DHAS SUDHARSANA DHAS BINDHU DHAS SUDHARSANA DHAS" → "هاري داس سودارسانا داس بيندو داس سودارسانا داس"
      * "ASHOKBHAI BABURAO SANT" → "أشوكبهاي بابوراو سانت"
      * "BINDHU SUDHARSANA DHAS" → "بيندو سودارسانا داس"
      * "INDIA" → "الهند"
      * "PALESTINE" → "فلسطين"
      * "DUBAI" → "دبي"
      * "LEBANON" → "لبنان"
      * "EGYPT" → "مصر"

22. **Attestation** (only if certificate_attestation is detected):
   - ONLY extract from certificate_attestation OCR (same document), never from other documents
   - Look for attestation numbers that are 10-15 digits long (e.g., "201400642961", "20183787892730") - this is Attestation Number 1
   - Look for any 7-digit number (e.g., "2468761") - this is Attestation Number 2
   - NEVER use Emirates ID numbers (they start with 784)
   - NEVER use identity numbers (they have / format like 101/2019/179119)
   - NEVER use receipt numbers or numbers from other document types
   - NEVER use numbers that don't appear in the actual OCR text
   - ONLY use numbers that are clearly attestation numbers from the attestation sticker/certificate
   - CRITICAL: Verify that any extracted number actually appears in the OCR text before using it
   - If both are not found, set them to null

22. **Email Sender Information**:
   - Email_Sender_Name: Use the sender's display name from the email (if available)
   - Email_Sender_Email: Use the sender's email address
   - Email_Sender_Person_Name: Use the extracted person name from the email address (e.g., "hasan.altelly@gmail.com" becomes "Hasan Altelly")

Return output as JSON with these fields:
  "Full Name", "Full Name (AR)", "Father's Name", "Father's Name (AR)", "Mother's Name", "Mother's Name (AR)", "Date of Birth",
  "Nationality", "Nationality (AR)", "Passport Number", "EID_Number", "EID_Issue_Date", "EID_Expiry_Date", "Identity_Number", "UID_Number",
  "Place of Birth", "Place of Birth (AR)", "Passport Issue Place", "Passport Issue Place (AR)",
  "Passport Issue Date", "Passport Expiry Date",
  "Home Phone Number", "Home Address", "UAE Address", "Certificate_Job", "HR_Manager_Request", "Previous_Job", "Employee_Info_Job", "Salary", "Document Type",
  "Attestation Number 1", "Attestation Number 2",
  "Salary_Breakdown", "Employment_Terms",
  "Email_Sender_Name", "Email_Sender_Email", "Email_Sender_Person_Name"

VALIDATION: Before returning, verify that:
- Passport Issue Place is the country that issued the passport (not where person lives/works)
- Place of Birth is where the person was born (not where passport was issued)
- UAE Address is where the person lives in UAE (not passport issue place)
- ALL Arabic translation fields are provided (Full Name (AR), Father's Name (AR), Mother's Name (AR), Nationality (AR), Place of Birth (AR), Passport Issue Place (AR))
- Nationality is simplified (e.g., "PALESTINIAN" → "PALESTINE", "INDIAN" → "INDIA")
- For residence cancellation documents: Check for UID numbers (7-digit format) - search entire OCR text
- For work permit cancellation documents: Check for File numbers (XXX/YYYY/ZZZZZZZ format) - search entire OCR text
- CRITICAL: If UID or File numbers are missing, search the entire OCR text again for any 7-digit numbers that could be these fields
- Phone numbers are properly formatted (should start with "00971" for UAE numbers)

=== PASSPORT PAGE 1 OCR ===
{passport_ocr_1}

=== PASSPORT PAGE 2 OCR ===
{passport_ocr_2}

=== EMIRATES ID FRONT OCR ===
{emirates_id_ocr}

=== EMIRATES ID BACK OCR ===
{emirates_id_2_ocr}

=== EMPLOYEE INFO OCR ===
{employee_info}

=== CERTIFICATE OCR ===
{certificate_ocr}

=== EMAIL TEXT ===
{email_text}

=== SALARY TABLE ===
{json.dumps(salary_data, indent=2)}

=== EMAIL SENDER INFORMATION ===
{json.dumps(sender_info, indent=2) if sender_info else '{}'}

=== RESNET CLASSIFICATION ===
{resnet_label}

=== DOCUMENT AI EXTRACTED FIELDS ===
{json.dumps(google_metadata.get('passport_1_fields', {}), indent=2) if 'passport_1_fields' in google_metadata else '{}'}
{json.dumps(google_metadata.get('passport_2_fields', {}), indent=2) if 'passport_2_fields' in google_metadata else '{}'}
{json.dumps(google_metadata.get('emirates_id_fields', {}), indent=2) if 'emirates_id_fields' in google_metadata else '{}'}
{json.dumps(google_metadata.get('emirates_id_2_fields', {}), indent=2) if 'emirates_id_2_fields' in google_metadata else '{}'}
{json.dumps(google_metadata.get('certificate_fields', {}), indent=2) if 'certificate_fields' in google_metadata else '{}'}
{json.dumps(google_metadata.get('employee_info_fields', {}), indent=2) if 'employee_info_fields' in google_metadata else '{}'}
{json.dumps(google_metadata.get('visa_fields', {}), indent=2) if 'visa_fields' in google_metadata else '{}'}
{json.dumps(google_metadata.get('residence_cancellation_fields', {}), indent=2) if 'residence_cancellation_fields' in google_metadata else '{}'}

=== GOOGLE VISION METADATA ===
{json.dumps(google_metadata, indent=2)}

Return only the structured JSON.
"""

    try:
        # Check if API key is available
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("⚠️ GEMINI_API_KEY not set - using fallback job extraction...")
            # Create a basic structured data with available information
            structured_data = {
                'Full Name': 'N/A',
                'Full Name (AR)': 'N/A',
                'Date of Birth': 'N/A',
                'Nationality': 'N/A',
                'Nationality (AR)': 'N/A',
                'Passport Number': 'N/A',
                'EID_Number': 'N/A',
                'Certificate_Job': 'N/A',
                'HR_Manager_Request': 'N/A',
                'Previous_Job': 'N/A',
                'Employee_Info_Job': 'N/A',
                'Salary': 'N/A',
                'Document Type': resnet_label
            }
            
            # Try to extract basic information from OCR text and email
            if certificate_ocr and "electrical" in certificate_ocr.lower():
                structured_data['Certificate_Job'] = 'Electrical Engineering'
                print(f"✅ Found 'electrical' in certificate OCR: {certificate_ocr[:100]}...")
            elif email_text and "electrical" in email_text.lower():
                structured_data['Certificate_Job'] = 'Electrical Engineering'
                print(f"✅ Found 'electrical' in email text: {email_text[:100]}...")
            else:
                print(f"❌ No 'electrical' found in certificate_ocr or email_text")
                print(f"   Certificate OCR: {certificate_ocr[:100] if certificate_ocr else 'EMPTY'}...")
                print(f"   Email text: {email_text[:100] if email_text else 'EMPTY'}...")
                
            if email_text and "engineer" in email_text.lower():
                structured_data['HR_Manager_Request'] = 'Engineer'
            elif email_text and "supervisor" in email_text.lower():
                # Extract the full job title from email
                if "supervisor construction electrical" in email_text.lower():
                    structured_data['HR_Manager_Request'] = 'Supervisor Construction Electrical'
                elif "supervisor" in email_text.lower():
                    structured_data['HR_Manager_Request'] = 'Supervisor'
                
            return structured_data, "Fallback extraction used - no API key"
        
        # Generate response using Google Generative AI (Gemini 2.5 Flash)
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        content = response.text

        if not content or not content.strip():
            print("⚠️ Gemini returned empty response.")
            return {}

        print("🔍 Gemini RAW RESPONSE:\n", content)  # Debug log
        
        # Store original response for text file
        original_response = content
        
        # Remove markdown wrapping if present
        if isinstance(content, str):
            if content.strip().startswith("```json"):
                content = content.strip().replace("```json", "").replace("```", "").strip()
            elif content.strip().startswith("```"):
                content = content.strip().replace("```", "").strip()
            
            # Parse the JSON response
            structured_data = json.loads(content)
        else:
            # If content is already a dictionary, use it directly
            structured_data = content
        
        # Validate attestation numbers if present
        if "Attestation Number 1" in structured_data or "Attestation Number 2" in structured_data:
            validated_attestation = validate_attestation_numbers(certificate_ocr, structured_data)
            # Update only the attestation numbers, preserve all other data
            structured_data.update(validated_attestation)
        
        # Post-process structured data to ensure Document AI extracted fields are properly mapped
        structured_data = post_process_structured_data(structured_data, google_metadata)

        print("✅ Gemini structured data successfully")
        return structured_data, original_response
        
    except json.JSONDecodeError as e:
        print(f"❌ Gemini JSON parsing failed: {e}")
        print(f"Raw response: {content}")
        return {}, ""
    except Exception as e:
        print(f"❌ Gemini API call failed: {e}")
        return {}, ""


def structure_document_with_gemini(label: str, ocr_text: str, email_text: str, salary_data: dict) -> dict:
    """
    Structure individual document using Gemini API.
    """
    if not ocr_text.strip():
        print("⚠️ Skipping Gemini — OCR text is empty.")
        return {}

    prompt = f"""
You are an expert MOHRE document structuring assistant.
Analyze the provided OCR text and extract relevant information based on the document type.

Document Type: {label}
OCR Text: {ocr_text}
Email Text: {email_text}
Salary Data: {json.dumps(salary_data, indent=2)}

Extract all relevant fields based on the document type and return as JSON.
For each field, provide the most accurate value found in the OCR text.
If a field is not found, set it to null.

IMPORTANT: For names, provide both English and Arabic versions:
- "Full Name" and "Full Name (AR)" - Arabic translation of the full name
- "Father's Name" and "Father's Name (AR)" - Arabic translation of the father's name  
- "Mother's Name" and "Mother's Name (AR)" - Arabic translation of the mother's name

For locations and nationalities, provide both English and Arabic versions:
- "Nationality" and "Nationality (AR)" - Arabic translation of nationality
- "Place of Birth" and "Place of Birth (AR)" - Arabic translation of place of birth
- "Passport Issue Place" and "Passport Issue Place (AR)" - Arabic translation of passport issue place

Return only valid JSON without any markdown formatting.
"""

    try:
        # Use Gemini 2.5 Flash for individual document structuring
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        content = response.text.strip()
        
        # Remove markdown wrapping if present
        if isinstance(content, str):
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()
            elif content.startswith("```"):
                content = content.replace("```", "").strip()
            
            structured_data = json.loads(content)
        else:
            # If content is already a dictionary, use it directly
            structured_data = content
        print(f"✅ Gemini structured {label} document successfully")
        return structured_data
        
    except json.JSONDecodeError as e:
        print(f"❌ Gemini JSON parsing failed for {label}: {e}")
        return {}
    except Exception as e:
        print(f"❌ Gemini API call failed for {label}: {e}")
        return {}


def merge_structured_documents(structured_docs):
    """
    Merge multiple structured documents into a single comprehensive record.
    """
    if not structured_docs:
        return {}
    
    merged = {}
    
    for doc in structured_docs:
        if not doc:
            continue
            
        for key, value in doc.items():
            if value and (key not in merged or not merged[key]):
                merged[key] = value
    
    return merged 