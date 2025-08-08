#!/usr/bin/env python3
"""
Email Processing Module
Handles email fetching, analysis, and MOHRE service classification
"""

import os
import json
from typing import Dict, Any
from email_analyzer import analyze_email_for_mohre_service

def get_mohre_service_url(service_category: str, specific_service: str) -> str:
    """Generate MOHRE service URL based on service category and specific service."""
    base_url = "https://www.mohre.gov.ae/en/services.aspx"
    
    service_urls = {
        "Work Permit Services": {
            "New Work Permit Application": "https://www.mohre.gov.ae/en/services/work-permit/new-work-permit.aspx",
            "Work Permit Renewal": "https://www.mohre.gov.ae/en/services/work-permit/work-permit-renewal.aspx",
            "Work Permit Cancellation": "https://www.mohre.gov.ae/en/services/work-permit/work-permit-cancellation.aspx"
        },
        "Residence Visa Services": {
            "Residence Visa Application": "https://www.mohre.gov.ae/en/services/residence-visa/residence-visa-application.aspx",
            "Residence Visa Renewal": "https://www.mohre.gov.ae/en/services/residence-visa/residence-visa-renewal.aspx",
            "Residence Visa Cancellation": "https://www.mohre.gov.ae/en/services/residence-visa/residence-visa-cancellation.aspx"
        },
        "Employment Services": {
            "Employment Contract": "https://www.mohre.gov.ae/en/services/employment/employment-contract.aspx",
            "Contract Amendment": "https://www.mohre.gov.ae/en/services/employment/contract-amendment.aspx",
            "Contract Termination": "https://www.mohre.gov.ae/en/services/employment/contract-termination.aspx"
        }
    }
    
    return service_urls.get(service_category, {}).get(specific_service, base_url)

def load_email_data(subject_path: str) -> tuple[str, Dict[str, Any], Dict[str, Any]]:
    """
    Load email body and sender information from a subject folder.
    
    Returns:
        tuple: (email_text, sender_info, mohre_analysis)
    """
    email_text_path = os.path.join(subject_path, "email_body.txt")
    sender_info_path = os.path.join(subject_path, "sender_info.json")
    
    email_text = ""
    sender_info = {
        'email': 'Unknown',
        'name': 'Unknown',
        'person_name': 'Unknown'
    }
    
    # Load email body
    if os.path.exists(email_text_path):
        with open(email_text_path, "r", encoding="utf-8") as f:
            email_text = f.read()
        print(f"📧 Email body loaded: {len(email_text)} characters")
        
        # Analyze email for MOHRE service
        print("🔍 Analyzing email for MOHRE service...")
        try:
            mohre_analysis = analyze_email_for_mohre_service(email_text, os.path.basename(subject_path))
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

    # Load sender info
    if os.path.exists(sender_info_path):
        try:
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

    return email_text, sender_info, mohre_analysis, mohre_service_url
