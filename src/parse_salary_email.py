#!/usr/bin/env python3
"""
Email Text Salary Parser
Extracts salary details and employment terms from email body text
"""

import re
import os
import json
import google.generativeai as genai
from typing import Dict, Any

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️ python-dotenv not installed, using system environment variables")

def extract_salary_with_gemini(email_text: str) -> Dict[str, Any]:
    """
    Use Gemini AI to extract salary information from email text.
    This handles any format - structured tables, separate lines, inline, etc.
    """
    
    if not email_text or not email_text.strip():
        return {}
    
    try:
        # Configure Gemini
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("⚠️ GEMINI_API_KEY not set, falling back to regex extraction")
            return {}
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        prompt = f"""
Analyze this email text and extract ALL salary information. Look for both CASH ALLOWANCES and PROVIDED BENEFITS.

Email Text:
{email_text}

Extract and return ONLY a JSON object with this structure:

{{
  "Basic_Salary": "X,XXX.XX AED" or null,
  "Allowances": {{
    "Housing": "X,XXX.XX AED" or null,
    "Transportation": "X,XXX.XX AED" or null,
    "Food_Allowance": "X,XXX.XX AED" or null,
    "Mobile_Allowance": "X,XXX.XX AED" or null,
    "Internet_Allowance": "X,XXX.XX AED" or null,
    "Travel_Allowance": "X,XXX.XX AED" or null,
    "Accommodation": "X,XXX.XX AED" or null
  }},
  "Benefits": {{
    "Accommodation_Provided": "Provided" or "Provided (Shared)" or "No" or null,
    "Transportation_Provided": "Provided" or "Provided (Bus)" or "No" or null,
    "Food_Provided": "Provided" or "Provided (Cafeteria)" or "No" or null,
    "Medical_Insurance": "Provided" or "No" or null,
    "Visa_Sponsorship": "Provided" or "No" or null,
    "Flight_Tickets": "Annual" or "Biannual" or "Provided" or "No" or null,
    "Uniform_Provided": "Provided" or "No" or null
  }},
  "Employment_Terms": {{
    "Working_Hours": "X hours per day" or null,
    "Annual_Leave": "X days" or null,
    "Probation_Period": "X months" or null,
    "Notice_Period": "X months" or null,
    "Contract_Duration": "X years" or null
  }},
  "Total_Monthly_Package": "X,XXX.XX AED" or null
}}

IMPORTANT RULES:
1. For CASH allowances (Housing: 2,000.00 AED) - put in "Allowances" section
2. For PROVIDED benefits (Accommodation: Provided) - put in "Benefits" section  
3. If you see "Basic Housing Transport Total" followed by numbers, match them in order
4. Always include "AED" for monetary amounts
5. Remove null fields from the final JSON
6. If Total is provided, use it. If not, I'll calculate it from the components.

Return ONLY the JSON, no explanation.
"""

        # Generate response
        response = model.generate_content(prompt)
        content = response.text.strip()
        
        # Clean up response
        if content.startswith("```json"):
            content = content.replace("```json", "").replace("```", "").strip()
        elif content.startswith("```"):
            content = content.replace("```", "").strip()
        
        # Parse JSON
        salary_data = json.loads(content)
        
        # Remove null values
        cleaned_data = {}
        for key, value in salary_data.items():
            if value is not None:
                if isinstance(value, dict):
                    # Clean nested dictionaries
                    cleaned_nested = {k: v for k, v in value.items() if v is not None}
                    if cleaned_nested:
                        cleaned_data[key] = cleaned_nested
                else:
                    cleaned_data[key] = value
        
        # Calculate total if not provided
        if "Total_Monthly_Package" not in cleaned_data:
            total_amount = 0
            components = []
            
            # Add basic salary
            if "Basic_Salary" in cleaned_data:
                basic_value = cleaned_data["Basic_Salary"].replace(" AED", "").replace(",", "")
                try:
                    total_amount += float(basic_value)
                    components.append(f"Basic: {basic_value}")
                except ValueError:
                    pass
            
            # Add allowances (only cash allowances, not provided benefits)
            if "Allowances" in cleaned_data:
                for name, value in cleaned_data["Allowances"].items():
                    clean_value = value.replace(" AED", "").replace(",", "")
                    try:
                        total_amount += float(clean_value)
                        components.append(f"{name}: {clean_value}")
                    except ValueError:
                        pass
            
            # Add calculated total if we have components
            if total_amount > 0:
                cleaned_data["Calculated_Total_Monthly_Package"] = f"{total_amount:,.2f} AED"
                cleaned_data["Calculation_Breakdown"] = components
        
        print(f"✅ Gemini extracted salary data successfully")
        return cleaned_data
        
    except json.JSONDecodeError as e:
        print(f"❌ Gemini salary extraction JSON error: {e}")
        return {}
    except Exception as e:
        print(f"❌ Gemini salary extraction error: {e}")
        return {}


def extract_structured_salary_table(text: str) -> Dict[str, Any]:
    """
    Extract salary information from structured table format where labels and values are separated.
    
    Example format:
    Basic
    Housing
    Transport
    Total
    3,963.60
    1,981.80
    660.60
    6,606.00
    """
    try:
        # Look for the pattern: salary labels followed by numeric values
        # First, find all salary-related keywords
        salary_keywords = ['basic', 'housing', 'transport', 'total', 'accommodation', 'travel', 'overtime', 'allowance']
        
        # Split text into words and find salary sections
        words = text.split()
        
        # Find positions of salary keywords
        salary_positions = []
        for i, word in enumerate(words):
            clean_word = re.sub(r'[^\w]', '', word.lower())
            if clean_word in salary_keywords:
                salary_positions.append((i, clean_word))
        
        if len(salary_positions) < 2:  # Need at least 2 salary components
            return {}
        
        # Look for numeric values after the salary keywords
        # Find all numeric values (with commas and decimals)
        numeric_pattern = r'\d{1,3}(?:,\d{3})*(?:\.\d{2})?'
        numeric_matches = []
        
        for i, word in enumerate(words):
            if re.match(numeric_pattern, word):
                numeric_matches.append((i, word))
        
        if len(numeric_matches) < len(salary_positions):
            return {}
        
        # Try to match keywords with values
        # Assume values come after keywords in order
        extracted_data = {}
        
        # Look for specific patterns
        basic_match = re.search(r'basic\s+.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', text)
        housing_match = re.search(r'housing\s+.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', text)
        transport_match = re.search(r'transport\s+.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', text)
        total_match = re.search(r'total\s+.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', text)
        
        # Look for structured salary format where labels and values are on separate lines
        # Pattern 1: Basic\n16,200.00\nAccommodation\n8,100.00\nTransportation\n2,700.00
        lines = text.split('\n')
        salary_components = {}
        
        for i, line in enumerate(lines):
            line = line.strip().lower()
            # Check if this line contains a salary component keyword
            if line in ['basic', 'accommodation', 'transportation', 'transport', 'housing', 'total']:
                # Look for the next line with a number
                for j in range(i+1, min(i+4, len(lines))):  # Check next 3 lines
                    next_line = lines[j].strip()
                    # Look for numeric value (with commas and decimals)
                    if re.match(r'^\d{1,3}(?:,\d{3})*(?:\.\d{2})?$', next_line):
                        # Map component names
                        component_name = line.title()
                        if line == 'transport':
                            component_name = 'Transportation'
                        elif line == 'basic':
                            component_name = 'Basic'
                        elif line == 'accommodation':
                            component_name = 'Accommodation'
                        
                        salary_components[component_name] = f"{next_line} AED"
                        break
        
        # Try pattern for structured table format (Haneen's format)
        # Basic Housing Transport Total followed by numbers in separate lines
        structured_pattern = r'basic\s+housing\s+transport\s+total\s+([\d,]+\.?\d*)\s+([\d,]+\.?\d*)\s+([\d,]+\.?\d*)\s+([\d,]+\.?\d*)'
        structured_match = re.search(structured_pattern, text)
        
        if structured_match:
            salary_components.update({
                "Basic": f"{structured_match.group(1)} AED",
                "Housing": f"{structured_match.group(2)} AED", 
                "Transport": f"{structured_match.group(3)} AED",
                "Total": f"{structured_match.group(4)} AED"
            })
        else:
            # Try to find the pattern where labels are on separate lines from values
            # Look for: Basic\nHousing\nTransport\nTotal\n3,963.60\n1,981.80\n660.60\n6,606.00
            lines = text.split()
            keywords_found = []
            numbers_found = []
            
            # Find salary keywords and their positions
            for i, word in enumerate(lines):
                if word.lower() in ['basic', 'housing', 'transport', 'total']:
                    keywords_found.append((i, word.lower()))
            
            # Find numeric values and their positions  
            for i, word in enumerate(lines):
                if re.match(r'^\d{1,3}(?:,\d{3})*(?:\.\d{2})?$', word):
                    numbers_found.append((i, word))
            
            # If we have 4 keywords and 4 numbers, try to match them
            if len(keywords_found) >= 3 and len(numbers_found) >= 3:
                # Check if keywords come before numbers (structured format)
                last_keyword_pos = max(pos for pos, _ in keywords_found)
                first_number_pos = min(pos for pos, _ in numbers_found)
                
                if last_keyword_pos < first_number_pos and len(keywords_found) == len(numbers_found):
                    # Match keywords with numbers in order
                    for i, (_, keyword) in enumerate(keywords_found):
                        if i < len(numbers_found):
                            _, number = numbers_found[i]
                            component_name = keyword.title()
                            if keyword == 'transport':
                                component_name = 'Transport'
                            elif keyword == 'housing':
                                component_name = 'Housing'
                            salary_components[component_name] = f"{number} AED"
        
        # Also try to extract employment terms from the email
        employment_terms = extract_employment_terms_from_text(text)
        
        if salary_components:
            extracted_data = salary_components
        
        if not extracted_data:
            return {}
            
        # Build structured salary data
        salary_data = {}
        
        # Add basic salary
        if "Basic" in extracted_data:
            salary_data["Basic_Salary"] = extracted_data["Basic"]
            
        # Add allowances
        allowances = {}
        for key in ["Housing", "Transport", "Travel", "Accommodation"]:
            if key in extracted_data:
                allowances[key + " Allowance"] = extracted_data[key]
        
        if allowances:
            salary_data["Allowances"] = allowances
            
        # Add total
        if "Total" in extracted_data:
            salary_data["Total_Monthly_Package"] = extracted_data["Total"]
            
        # Add employment terms if found
        if employment_terms:
            salary_data["Employment_Terms"] = employment_terms
            
        return salary_data
        
    except Exception as e:
        print(f"❌ Error extracting structured salary table: {e}")
        return {}

def extract_employment_terms_from_text(email_text: str) -> Dict[str, str]:
    """
    Extract employment terms from email text.
    """
    try:
        text = email_text.lower()
        employment_terms = {}
        
        # Employment terms patterns
        patterns = {
            "Contract_Duration": [
                r"contract\s*(?:duration|period|length)\s*:?\s*(\d+\s*(?:years?|months?|yrs?))",
                r"(\d+\s*(?:years?|months?|yrs?))\s*contract",
                r"contract\s*(?:for|of)\s*(\d+\s*(?:years?|months?|yrs?))"
            ],
            "Probation_Period": [
                r"probation\s*period\s*:?\s*(\d+\s*(?:months?|days?|weeks?))",
                r"probationary\s*period\s*:?\s*(\d+\s*(?:months?|days?|weeks?))",
                r"(\d+\s*(?:months?|days?|weeks?))\s*probation"
            ],
            "Working_Hours": [
                r"working\s*hours?\s*:?\s*(\d+\s*(?:hours?|hrs?)\s*(?:per\s*day|daily)?)",
                r"work\s*hours?\s*:?\s*(\d+\s*(?:hours?|hrs?)\s*(?:per\s*day|daily)?)",
                r"(\d+\s*(?:hours?|hrs?)\s*(?:per\s*day|daily))\s*work",
                r"(\d+\s*(?:hours?|hrs?))\s*(?:per\s*day|daily)"
            ],
            "Annual_Leave": [
                r"annual\s*leave\s*:?\s*(\d+\s*days?)",
                r"vacation\s*days?\s*:?\s*(\d+\s*days?)",
                r"(\d+\s*days?)\s*annual\s*leave",
                r"(\d+\s*days?)\s*vacation"
            ],
            "Sick_Leave": [
                r"sick\s*leave\s*:?\s*(\d+\s*days?)",
                r"medical\s*leave\s*:?\s*(\d+\s*days?)",
                r"(\d+\s*days?)\s*sick\s*leave"
            ],
            "Work_Days": [
                r"work\s*days?\s*:?\s*(\d+\s*days?\s*per\s*week)",
                r"working\s*days?\s*:?\s*(\d+\s*days?\s*per\s*week)",
                r"(\d+\s*days?\s*per\s*week)\s*work"
            ],
            "Notice_Period": [
                r"notice\s*period\s*:?\s*(\d+\s*(?:months?|days?|weeks?))",
                r"resignation\s*notice\s*:?\s*(\d+\s*(?:months?|days?|weeks?))",
                r"(\d+\s*(?:months?|days?|weeks?))\s*notice"
            ],
            "Overtime_Rate": [
                r"overtime\s*rate\s*:?\s*(\d+(?:\.\d+)?\s*(?:times?|x|multiplier))",
                r"overtime\s*pay\s*:?\s*(\d+(?:\.\d+)?\s*(?:times?|x|multiplier))"
            ],
            "Medical_Insurance": [
                r"medical\s*insurance\s*:?\s*(provided|included|yes|no|covered|company\s*provides?)",
                r"health\s*insurance\s*:?\s*(provided|included|yes|no|covered|company\s*provides?)",
                r"insurance\s*:?\s*(provided|included|yes|no|covered|company\s*provides?)"
            ],
            "Visa_Sponsorship": [
                r"visa\s*(?:sponsorship|status)\s*:?\s*(provided|included|yes|no|sponsored|company\s*provides?)",
                r"work\s*visa\s*:?\s*(provided|included|yes|no|sponsored|company\s*provides?)"
            ],
            "Accommodation": [
                r"accommodation\s*:?\s*(provided|included|yes|no|shared|single|company\s*provides?)",
                r"housing\s*:?\s*(provided|included|yes|no|shared|single|company\s*provides?)",
                r"residence\s*:?\s*(provided|included|yes|no|shared|single|company\s*provides?)"
            ],
            "Transportation": [
                r"transport\s*(?:to\s*work)?\s*:?\s*(provided|included|yes|no|shared|private|company\s*provides?|bus)",
                r"transportation\s*:?\s*(provided|included|yes|no|shared|private|company\s*provides?)"
            ],
            "Flight_Tickets": [
                r"flight\s*tickets?\s*:?\s*(provided|included|yes|no|annual|biannual|yearly|company\s*provides?)",
                r"air\s*tickets?\s*:?\s*(provided|included|yes|no|annual|biannual|yearly|company\s*provides?)",
                r"return\s*tickets?\s*:?\s*(provided|included|yes|no|annual|biannual|yearly|company\s*provides?)"
            ],
            "Gratuity": [
                r"gratuity\s*:?\s*(\d+(?:\.\d+)?\s*(?:months?|days?|salary))",
                r"end\s*of\s*service\s*:?\s*(\d+(?:\.\d+)?\s*(?:months?|days?|salary))"
            ],
            "Bonus": [
                r"(?:annual\s*)?bonus\s*:?\s*([\d,]+\.?\d*\s*(?:aed|months?|%|percent))",
                r"performance\s*bonus\s*:?\s*([\d,]+\.?\d*\s*(?:aed|months?|%|percent))"
            ]
        }
        
        # Extract each employment term
        for term, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, text)
                if match:
                    value = match.group(1).strip()
                    
                    # Standardize boolean values
                    if term in ["Medical_Insurance", "Visa_Sponsorship", "Accommodation", "Transportation", "Flight_Tickets"]:
                        if any(word in value.lower() for word in ["yes", "provided", "included", "covered", "company"]):
                            employment_terms[term.replace('_', ' ').title()] = "Yes"
                        elif "no" in value.lower():
                            employment_terms[term.replace('_', ' ').title()] = "No"
                        else:
                            employment_terms[term.replace('_', ' ').title()] = value.title()
                    else:
                        employment_terms[term.replace('_', ' ').title()] = value
                    break  # Take first match for each term
        
        return employment_terms
        
    except Exception as e:
        print(f"❌ Error extracting employment terms: {e}")
        return {}

def parse_salary_email(email_text: str) -> Dict[str, Any]:
    """
    Parse salary details and employment terms from email body text.
    Uses Gemini AI first, then falls back to regex patterns if needed.
    
    Args:
        email_text: The email body text to parse
        
    Returns:
        dict: Extracted salary and employment data
    """
    if not email_text or not email_text.strip():
        return {}
    
    try:
        print(f"🔍 Parsing salary from email text: {len(email_text)} characters")
        
        # Try Gemini extraction first
        gemini_result = extract_salary_with_gemini(email_text)
        if gemini_result:
            print("✅ Using Gemini extraction results")
            return gemini_result
        
        print("⚠️ Gemini extraction failed or unavailable, falling back to regex patterns")
        
        # Fallback to existing regex-based extraction
        # First try to extract from separate lines format (like the Balakrishnan email)
        # Use original text to preserve line breaks
        lines = email_text.split('\n')
        line_based_salary = {}
        
        # Check for structured table format (Haneen's format) first
        salary_keywords = []
        salary_numbers = []
        
        for i, line in enumerate(lines):
            line_clean = line.strip().lower()
            if line_clean in ['basic', 'housing', 'transport', 'total']:
                salary_keywords.append((i, line_clean))
            elif re.match(r'^\d{1,3}(?:,\d{3})*(?:\.\d{2})?$', line.strip()):
                salary_numbers.append((i, line.strip()))
        
        # If we have keywords followed by numbers (structured table format)
        if len(salary_keywords) >= 3 and len(salary_numbers) >= 3:
            # Check if all keywords come before all numbers
            last_keyword_line = max(pos for pos, _ in salary_keywords)
            first_number_line = min(pos for pos, _ in salary_numbers)
            
            if last_keyword_line < first_number_line and len(salary_keywords) == len(salary_numbers):
                print(f"🔍 Detected structured table format: {len(salary_keywords)} keywords, {len(salary_numbers)} numbers")
                # Match keywords with numbers in order
                for i, (_, keyword) in enumerate(salary_keywords):
                    if i < len(salary_numbers):
                        _, number = salary_numbers[i]
                        component_name = keyword.title()
                        if keyword == 'transport':
                            component_name = 'Transport'
                        elif keyword == 'housing':
                            component_name = 'Housing'
                        line_based_salary[component_name] = f"{number} AED"
                        print(f"   Matched {keyword} -> {number}")
        
        # If structured table didn't work, try adjacent line format (Balakrishnan style)
        if not line_based_salary:
            for i, line in enumerate(lines):
                line_clean = line.strip().lower()
                if line_clean in ['basic', 'accommodation', 'transportation', 'transport', 'housing', 'total']:
                    # Look for numeric value in next few lines
                    for j in range(i+1, min(i+4, len(lines))):
                        next_line = lines[j].strip()
                        if re.match(r'^\d{1,3}(?:,\d{3})*(?:\.\d{2})?$', next_line):
                            component_name = line_clean.title()
                            if line_clean in ['transport', 'transportation']:
                                component_name = 'Transportation'
                            line_based_salary[component_name] = f"{next_line} AED"
                            break
        
        # Initialize extracted_data
        extracted_data = {}
        
        # If we found salary data in separate lines format, use it
        if line_based_salary:
            extracted_data = line_based_salary
        else:
            # Clean and normalize text for pattern matching
            text = email_text.lower().replace("\n", " ").replace("\r", " ").replace("\t", " ")
            text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with single space
            
            # Try structured table format
            structured_salary = extract_structured_salary_table(text)
            if structured_salary:
                return structured_salary
            # Enhanced patterns for salary and employment terms (inline format)
            patterns = {
                # Salary Components - More flexible patterns
                "Basic": r"basic\s*salary\s*:?\s*(?:aed\s*)?(\d[\d,]*\.?\d*)",
                "Basic_Monthly": r"basic\s*(?:salary\s*)?(?:per\s*month|monthly)\s*:?\s*(?:aed\s*)?(\d[\d,]*\.?\d*)",
                "Housing": r"housing\s*(?:allowance)?\s*:?\s*(?:aed\s*)?(\d[\d,]*\.?\d*)",
                "Transport": r"transport\s*(?:allowance)?\s*:?\s*(?:aed\s*)?(\d[\d,]*\.?\d*)",
                "Transportation": r"transportation\s*(?:allowance)?\s*:?\s*(?:aed\s*)?(\d[\d,]*\.?\d*)",
                "Travel": r"travel\s*(?:allowance)?\s*:?\s*(?:aed\s*)?(\d[\d,]*\.?\d*)",
                "Accommodation": r"accommodation\s*(?:allowance)?\s*:?\s*(?:aed\s*)?(\d[\d,]*\.?\d*)",
                "Plane": r"plane\s*(?:ticket|allowance)?\s*:?\s*(?:aed\s*)?(\d[\d,]*\.?\d*)",
                "Overtime": r"overtime\s*(?:\+\s*premium\s*)?(?:allowance)?\s*:?\s*(?:aed\s*)?(\d[\d,]*\.?\d*)",
                "Site_Allowance": r"site\s*allowance\s*:?\s*(?:aed\s*)?(\d[\d,]*\.?\d*)",
                "Total": r"total\s*(?:monthly\s*)?(?:package|salary)\s*:?\s*(?:aed\s*)?(\d[\d,]*\.?\d*)",
                "Monthly_Package": r"monthly\s*package\s*:?\s*(?:aed\s*)?(\d[\d,]*\.?\d*)",
                "Gross_Salary": r"gross\s*salary\s*:?\s*(?:aed\s*)?(\d[\d,]*\.?\d*)",
                "Net_Salary": r"net\s*salary\s*:?\s*(?:aed\s*)?(\d[\d,]*\.?\d*)",
                
                # Employment Terms
                "Probation_Period": r"probation\s*period\s*:?\s*(\d+\s*(?:months?|days?|weeks?))",
                "Notice_Period": r"notice\s*period\s*:?\s*(\d+\s*(?:months?|days?|weeks?))",
                "Working_Hours": r"(?:working\s*hours?|hours?\s*of\s*work|work\s*hours?)\s*:?\s*(\d+(?:\s*-\s*\d+)?\s*(?:hours?|hrs?|h)(?:\s*per\s*day)?)",
                "Contract_Duration": r"contract\s*(?:duration|period)\s*:?\s*(\d+\s*(?:months?|years?))",
                "Contract_Type": r"contract\s*type\s*:?\s*(permanent|temporary|fixed|unlimited)",
                "Annual_Leave": r"annual\s*leave\s*:?\s*(\d+\s*(?:days?|weeks?))",
                "Sick_Leave": r"sick\s*leave\s*:?\s*(\d+\s*(?:days?|weeks?))",
                "Work_Days": r"work\s*days?\s*(?:per\s*week)?\s*:?\s*(\d+\s*(?:days?)?(?:\s*per\s*week)?)",
                "Overtime_Rate": r"overtime\s*rate\s*:?\s*(\d+(?:\.\d+)?\s*(?:times?|x|multiplier))",
                "Gratuity": r"gratuity\s*:?\s*(\d+(?:\.\d+)?\s*(?:months?|days?|salary))",
                
                # Benefits and Amenities (when provided vs. cash allowance)
                "Insurance": r"(?:health\s*|medical\s*)?insurance\s*:?\s*(provided|included|yes|no|covered|company\s*provides?|free)",
                "Medical_Insurance": r"medical\s*(?:insurance|coverage)\s*:?\s*(provided|included|yes|no|covered|company\s*provides?|free)",
                "Visa_Status": r"visa\s*(?:sponsorship|status|support)?\s*:?\s*(provided|included|yes|no|sponsored|company\s*provides?)",
                "Flight_Ticket": r"(?:flight\s*ticket|air\s*ticket|return\s*ticket|annual\s*ticket)\s*:?\s*(provided|included|yes|no|annual|biannual|yearly|company\s*provides?|free)",
                "Accommodation_Provided": r"accommodation\s*(?:is\s*)?:?\s*(provided|included|yes|no|shared|single|company\s*provides?|free|furnished|unfurnished)",
                "Transport_Provided": r"transport(?:ation)?\s*(?:to\s*work|is\s*)?:?\s*(provided|included|yes|no|shared|private|company\s*provides?|bus|free|pickup)",
                "Food_Provided": r"(?:food|meals?|lunch|dinner|breakfast)\s*(?:is\s*)?:?\s*(provided|included|yes|no|company\s*provides?|free|cafeteria)",
                "Uniform_Provided": r"uniform\s*(?:is\s*)?:?\s*(provided|included|yes|no|company\s*provides?|free)",
                "Tools_Provided": r"(?:tools?|equipment)\s*(?:are\s*|is\s*)?:?\s*(provided|included|yes|no|company\s*provides?|free)",
                "Food_Allowance": r"food\s*(?:allowance|meals?)\s*:?\s*(?:(?:aed\s*)?(\d[\d,]*\.?\d*)|provided|included|yes|no)",
                "Mobile_Allowance": r"mobile\s*(?:phone\s*)?allowance\s*:?\s*(?:aed\s*)?(\d[\d,]*\.?\d*)",
                "Internet_Allowance": r"internet\s*allowance\s*:?\s*(?:aed\s*)?(\d[\d,]*\.?\d*)",
                
                # Job Details
                "Job_Title": r"(?:position|job\s*title|role)\s*:?\s*([a-zA-Z\s]+(?:engineer|manager|supervisor|coordinator|technician|specialist|analyst|assistant|officer))",
                "Department": r"department\s*:?\s*([a-zA-Z\s]+)",
                "Location": r"(?:work\s*location|location)\s*:?\s*([a-zA-Z\s,]+)",
                "Start_Date": r"(?:start\s*date|joining\s*date|commencement)\s*:?\s*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})",
                
                # Additional Benefits
                "Bonus": r"(?:annual\s*)?bonus\s*:?\s*(?:aed\s*)?(\d[\d,]*\.?\d*)",
                "Commission": r"commission\s*:?\s*(?:aed\s*)?(\d[\d,]*\.?\d*)",
                "Incentive": r"incentive\s*:?\s*(?:aed\s*)?(\d[\d,]*\.?\d*)",
            }

            # Extract all values using patterns (fallback method)
            for key, pattern in patterns.items():
                matches = re.findall(pattern, text)
                if matches:
                    # Take the first match
                    value = matches[0].strip()
                    
                    # Clean up the value
                    if key in ["Insurance", "Medical_Insurance", "Visa_Status", "Flight_Ticket", 
                              "Accommodation_Provided", "Transport_Provided", "Food_Provided", 
                              "Uniform_Provided", "Tools_Provided"]:
                        # For boolean/status fields, standardize the text
                        if any(word in value.lower() for word in ["yes", "provided", "included", "covered", "company", "free"]):
                            extracted_data[key] = "Provided"
                        elif "no" in value.lower():
                            extracted_data[key] = "No"
                        elif any(word in value.lower() for word in ["shared", "single", "furnished", "unfurnished", "private", "bus", "pickup", "cafeteria"]):
                            extracted_data[key] = f"Provided ({value.title()})"
                        else:
                            extracted_data[key] = value.title()
                    elif key in ["Contract_Type"]:
                        extracted_data[key] = value.title()
                    else:
                        # For numeric fields, add AED if it's a salary component and doesn't have it
                        if key in ["Basic", "Basic_Monthly", "Housing", "Transport", "Travel", "Accommodation", 
                                 "Plane", "Overtime", "Site_Allowance", "Total", "Monthly_Package", 
                                 "Gross_Salary", "Net_Salary", "Food_Allowance", "Mobile_Allowance", 
                                 "Internet_Allowance", "Bonus", "Commission", "Incentive"]:
                            # Remove commas and clean the number
                            clean_value = re.sub(r'[,\s]', '', value)
                            if clean_value.replace('.', '').isdigit():
                                extracted_data[key] = f"{clean_value} AED"
                            else:
                                extracted_data[key] = value
                        else:
                            extracted_data[key] = value

        if not extracted_data:
            return {}

        # Build final salary data structure
        salary_data = {}
        
        # Add basic salary information
        if "Basic" in extracted_data:
            salary_data["Basic_Salary"] = extracted_data["Basic"]
        elif "Basic_Monthly" in extracted_data:
            salary_data["Basic_Salary"] = extracted_data["Basic_Monthly"]
            
        # Add allowances
        allowances = {}
        for key in ["Housing", "Transport", "Transportation", "Travel", "Accommodation", "Plane", 
                   "Food_Allowance", "Mobile_Allowance", "Internet_Allowance"]:
            if key in extracted_data:
                allowances[key.replace('_', ' ').title()] = extracted_data[key]
        
        if allowances:
            salary_data["Allowances"] = allowances
            
        # Add overtime and special allowances
        special_allowances = {}
        for key in ["Overtime", "Site_Allowance", "Bonus", "Commission", "Incentive"]:
            if key in extracted_data:
                special_allowances[key.replace('_', ' ').title()] = extracted_data[key]
                
        if special_allowances:
            salary_data["Special_Allowances"] = special_allowances
            
        # Add total package
        if "Total" in extracted_data:
            salary_data["Total_Monthly_Package"] = extracted_data["Total"]
        elif "Monthly_Package" in extracted_data:
            salary_data["Total_Monthly_Package"] = extracted_data["Monthly_Package"]
        elif "Gross_Salary" in extracted_data:
            salary_data["Gross_Salary"] = extracted_data["Gross_Salary"]
        elif "Net_Salary" in extracted_data:
            salary_data["Net_Salary"] = extracted_data["Net_Salary"]
        else:
            # Calculate total if not provided by summing all salary components
            total_amount = 0
            salary_components = []
            
            # Sum basic salary
            if "Basic_Salary" in salary_data:
                basic_value = salary_data["Basic_Salary"].replace(" AED", "").replace(",", "")
                try:
                    total_amount += float(basic_value)
                    salary_components.append(f"Basic: {basic_value}")
                except ValueError:
                    pass
            
            # Sum allowances
            if "Allowances" in salary_data:
                for allowance_name, allowance_value in salary_data["Allowances"].items():
                    clean_value = allowance_value.replace(" AED", "").replace(",", "")
                    try:
                        total_amount += float(clean_value)
                        salary_components.append(f"{allowance_name}: {clean_value}")
                    except ValueError:
                        pass
            
            # Sum special allowances
            if "Special_Allowances" in salary_data:
                for special_name, special_value in salary_data["Special_Allowances"].items():
                    clean_value = special_value.replace(" AED", "").replace(",", "")
                    try:
                        total_amount += float(clean_value)
                        salary_components.append(f"{special_name}: {clean_value}")
                    except ValueError:
                        pass
            
            # Add calculated total if we have components
            if total_amount > 0:
                salary_data["Calculated_Total_Monthly_Package"] = f"{total_amount:,.2f} AED"
                salary_data["Calculation_Breakdown"] = salary_components
            
        # Add employment terms
        employment_terms = {}
        for key in ["Probation_Period", "Notice_Period", "Working_Hours", "Contract_Duration",
                   "Contract_Type", "Annual_Leave", "Sick_Leave", "Work_Days", "Overtime_Rate", "Gratuity"]:
            if key in extracted_data:
                employment_terms[key.replace('_', ' ').title()] = extracted_data[key]
                
        if employment_terms:
            salary_data["Employment_Terms"] = employment_terms
            
        # Add benefits
        benefits = {}
        for key in ["Insurance", "Medical_Insurance", "Visa_Status", "Flight_Ticket", 
                   "Accommodation_Provided", "Transport_Provided", "Food_Provided",
                   "Uniform_Provided", "Tools_Provided"]:
            if key in extracted_data:
                benefits[key.replace('_', ' ').title()] = extracted_data[key]
                
        if benefits:
            salary_data["Benefits"] = benefits
            
        # Add job information
        job_info = {}
        for key in ["Job_Title", "Department", "Location", "Start_Date"]:
            if key in extracted_data:
                job_info[key.replace('_', ' ').title()] = extracted_data[key]
                
        if job_info:
            salary_data["Job_Information"] = job_info

        # Extract employment terms from the full email text
        employment_terms = extract_employment_terms_from_text(email_text)
        if employment_terms:
            salary_data["Employment_Terms"] = employment_terms

        return salary_data
        
    except Exception as e:
        print(f"❌ Error parsing salary from email text: {e}")
        return {}

def merge_salary_data(docx_salary: Dict[str, Any], email_salary: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge salary data from DOCX files and email text, prioritizing DOCX data.
    
    Args:
        docx_salary: Salary data extracted from DOCX files
        email_salary: Salary data extracted from email text
        
    Returns:
        dict: Merged salary data
    """
    if not docx_salary and not email_salary:
        return {}
    
    if not docx_salary:
        return email_salary
    
    if not email_salary:
        return docx_salary
    
    # Merge both, with DOCX taking priority
    merged = email_salary.copy()
    
    # Override with DOCX data where available
    for key, value in docx_salary.items():
        if value:  # Only override if DOCX has a non-empty value
            merged[key] = value
    
    return merged
