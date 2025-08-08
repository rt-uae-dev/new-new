#!/usr/bin/env python3
"""
Email Body Analyzer using Gemini AI
Analyzes email body text to determine which MOHRE service is needed
"""

import os
import json
import google.generativeai as genai

# Configure Google Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def analyze_email_for_mohre_service(email_body: str, email_subject: str = "") -> dict:
    """
    Analyze email body and subject to determine which MOHRE service is needed
    
    Args:
        email_body: The email body text
        email_subject: The email subject line
        
    Returns:
        dict: Analysis results including service type, confidence, and reasoning
    """
    
    prompt = f"""
You are an expert MOHRE (Ministry of Human Resources and Emiratisation) service classifier.
Analyze the provided email body and subject to determine which specific MOHRE service is being requested.

MOHRE Services Categories:
1. **Work Permit Services**
   - New Work Permit Application
   - Work Permit Renewal
   - Work Permit Cancellation
   - Work Permit Transfer
   - Work Permit Amendment

2. **Residence Visa Services**
   - New Residence Visa Application
   - Residence Visa Renewal
   - Residence Visa Cancellation
   - Residence Visa Transfer
   - Residence Visa Amendment

3. **Labor Card Services**
   - New Labor Card Application
   - Labor Card Renewal
   - Labor Card Cancellation
   - Labor Card Transfer

4. **Document Attestation Services**
   - Educational Certificate Attestation
   - Professional Certificate Attestation
   - Experience Certificate Attestation
   - Commercial Document Attestation

5. **Employee Information Services**
   - Employee Registration
   - Employee Information Update
   - Employee Status Change

6. **Contract Services**
   - Employment Contract Registration
   - Contract Amendment
   - Contract Cancellation

7. **General Inquiries**
   - Service Information Request
   - Status Check Request
   - General Consultation

Email Subject: {email_subject}

Email Body:
{email_body}

Please analyze the content and provide:
1. **Primary Service Category**: The main MOHRE service category
2. **Specific Service**: The exact service being requested
3. **Confidence Level**: High/Medium/Low based on clarity of information
4. **Key Indicators**: What specific words/phrases indicate this service
5. **Additional Context**: Any relevant details about the request
6. **Priority Level**: Urgent/Normal based on language and context
7. **Required Documents**: What documents are likely needed based on the service

Return your analysis as a JSON object with these fields:
- "service_category"
- "specific_service" 
- "confidence_level"
- "key_indicators"
- "additional_context"
- "priority_level"
- "required_documents"
- "reasoning"

Focus on identifying the most specific service possible based on the content.
"""

    try:
        # Generate response using Google Generative AI (Gemini 2.5 Flash)
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        content = response.text

        if not content or not content.strip():
            print("⚠️ Gemini returned empty response for email analysis.")
            return {
                "service_category": "Unknown",
                "specific_service": "Unknown",
                "confidence_level": "Low",
                "key_indicators": [],
                "additional_context": "No analysis available",
                "priority_level": "Normal",
                "required_documents": [],
                "reasoning": "Failed to analyze email content"
            }

        # Remove markdown wrapping if present
        if isinstance(content, str):
            if content.strip().startswith("```json"):
                content = content.strip().replace("```json", "").replace("```", "").strip()
            elif content.strip().startswith("```"):
                content = content.strip().replace("```", "").strip()
            
            # Parse the JSON response
            analysis_result = json.loads(content)
        else:
            # If content is already a dictionary, use it directly
            analysis_result = content
        
        print(f"✅ Email analysis completed: {analysis_result.get('specific_service', 'Unknown')}")
        return analysis_result
        
    except json.JSONDecodeError as e:
        print(f"❌ Gemini JSON parsing failed for email analysis: {e}")
        print(f"Raw response: {content}")
        return {
            "service_category": "Unknown",
            "specific_service": "Unknown", 
            "confidence_level": "Low",
            "key_indicators": [],
            "additional_context": "JSON parsing failed",
            "priority_level": "Normal",
            "required_documents": [],
            "reasoning": f"Failed to parse analysis: {str(e)}"
        }
    except Exception as e:
        print(f"❌ Gemini API call failed for email analysis: {e}")
        return {
            "service_category": "Unknown",
            "specific_service": "Unknown",
            "confidence_level": "Low", 
            "key_indicators": [],
            "additional_context": "API call failed",
            "priority_level": "Normal",
            "required_documents": [],
            "reasoning": f"API error: {str(e)}"
        }

def get_mohre_service_url(service_category: str, specific_service: str) -> str:
    """
    Get the relevant MOHRE website URL for the identified service
    
    Args:
        service_category: The main service category
        specific_service: The specific service
        
    Returns:
        str: The relevant MOHRE website URL
    """
    
    # Base MOHRE URLs
    mohre_base_url = "https://www.mohre.gov.ae"
    
    # Service-specific URL mappings
    service_urls = {
        "Work Permit Services": {
            "New Work Permit Application": f"{mohre_base_url}/en/services/work-permit/new-application.aspx",
            "Work Permit Renewal": f"{mohre_base_url}/en/services/work-permit/renewal.aspx",
            "Work Permit Cancellation": f"{mohre_base_url}/en/services/work-permit/cancellation.aspx",
            "Work Permit Transfer": f"{mohre_base_url}/en/services/work-permit/transfer.aspx",
            "Work Permit Amendment": f"{mohre_base_url}/en/services/work-permit/amendment.aspx"
        },
        "Residence Visa Services": {
            "New Residence Visa Application": f"{mohre_base_url}/en/services/residence-visa/new-application.aspx",
            "Residence Visa Renewal": f"{mohre_base_url}/en/services/residence-visa/renewal.aspx",
            "Residence Visa Cancellation": f"{mohre_base_url}/en/services/residence-visa/cancellation.aspx",
            "Residence Visa Transfer": f"{mohre_base_url}/en/services/residence-visa/transfer.aspx",
            "Residence Visa Amendment": f"{mohre_base_url}/en/services/residence-visa/amendment.aspx"
        },
        "Labor Card Services": {
            "New Labor Card Application": f"{mohre_base_url}/en/services/labor-card/new-application.aspx",
            "Labor Card Renewal": f"{mohre_base_url}/en/services/labor-card/renewal.aspx",
            "Labor Card Cancellation": f"{mohre_base_url}/en/services/labor-card/cancellation.aspx",
            "Labor Card Transfer": f"{mohre_base_url}/en/services/labor-card/transfer.aspx"
        },
        "Document Attestation Services": {
            "Educational Certificate Attestation": f"{mohre_base_url}/en/services/attestation/educational.aspx",
            "Professional Certificate Attestation": f"{mohre_base_url}/en/services/attestation/professional.aspx",
            "Experience Certificate Attestation": f"{mohre_base_url}/en/services/attestation/experience.aspx",
            "Commercial Document Attestation": f"{mohre_base_url}/en/services/attestation/commercial.aspx"
        },
        "Employee Information Services": {
            "Employee Registration": f"{mohre_base_url}/en/services/employee/registration.aspx",
            "Employee Information Update": f"{mohre_base_url}/en/services/employee/update.aspx",
            "Employee Status Change": f"{mohre_base_url}/en/services/employee/status-change.aspx"
        },
        "Contract Services": {
            "Employment Contract Registration": f"{mohre_base_url}/en/services/contract/registration.aspx",
            "Contract Amendment": f"{mohre_base_url}/en/services/contract/amendment.aspx",
            "Contract Cancellation": f"{mohre_base_url}/en/services/contract/cancellation.aspx"
        },
        "General Inquiries": {
            "Service Information Request": f"{mohre_base_url}/en/contact-us.aspx",
            "Status Check Request": f"{mohre_base_url}/en/services/status-check.aspx",
            "General Consultation": f"{mohre_base_url}/en/contact-us.aspx"
        }
    }
    
    # Try to find the specific URL
    if service_category in service_urls:
        if specific_service in service_urls[service_category]:
            return service_urls[service_category][specific_service]
        else:
            # Return the category page if specific service not found
            return f"{mohre_base_url}/en/services/{service_category.lower().replace(' ', '-')}.aspx"
    
    # Default to main services page
    return f"{mohre_base_url}/en/services.aspx"
