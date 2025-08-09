#!/usr/bin/env python3
"""
Test script to verify email salary parsing functionality
"""

from src.parse_salary_email import parse_salary_email

# Real email text from the processed folder
sample_email_text = """Hi,



Kindly apply for MISSION VISA for mentioned employee under Dubai office.



Travel Dates:  ASAP



Documents attached:




  1.  Passport & ID

  2.  Photo

  3.  Employee Information Form



Basic

Housing

Transport

Total

3,963.60

1,981.80

660.60

6,606.00




Thanks

Yasser



"""

# Also test with comprehensive email including employment terms
comprehensive_email_text = """
Dear HR Team,

Please process the visa application for John Smith.

Here are the employment details:
- Basic salary: AED 4500 per month
- Housing allowance: AED 1500
- Transport allowance: AED 600
- Total monthly package: AED 6600

Employment Terms:
- Contract duration: 2 years
- Probation period: 3 months
- Working hours: 8 hours per day
- Annual leave: 30 days
- Sick leave: 15 days
- Notice period: 1 month
- Medical insurance: provided by company
- Visa sponsorship: yes
- Accommodation: company provided
- Transportation: company bus provided
- Flight tickets: annual return tickets provided

Please let me know if you need any additional information.

Best regards,
HR Manager
"""

def test_email_salary_parsing():
    print("🧪 Testing email salary parsing...")
    print("=" * 70)
    
    # Test 1: Real email from Haneen case (structured table format)
    print("📧 TEST 1: Real email with structured salary table")
    print("=" * 50)
    print("Email content:")
    print(sample_email_text[:200] + "..." if len(sample_email_text) > 200 else sample_email_text)
    
    result1 = parse_salary_email(sample_email_text)
    
    print("\n💰 Parsed salary data:")
    if result1:
        for key, value in result1.items():
            if isinstance(value, dict):
                print(f"📋 {key.replace('_', ' ').title()}:")
                for sub_key, sub_value in value.items():
                    print(f"   • {sub_key}: {sub_value}")
            else:
                print(f"• {key.replace('_', ' ').title()}: {value}")
    else:
        print("⚠️ No salary data extracted")
    
    print("\n" + "=" * 70)
    
    # Test 2: Comprehensive email with employment terms
    print("📧 TEST 2: Comprehensive email with employment terms")
    print("=" * 50)
    print("Email content:")
    print(comprehensive_email_text[:300] + "..." if len(comprehensive_email_text) > 300 else comprehensive_email_text)
    
    result2 = parse_salary_email(comprehensive_email_text)
    
    print("\n💰 Parsed comprehensive data:")
    if result2:
        for key, value in result2.items():
            if isinstance(value, dict):
                print(f"📋 {key.replace('_', ' ').title()}:")
                for sub_key, sub_value in value.items():
                    print(f"   • {sub_key}: {sub_value}")
            else:
                print(f"• {key.replace('_', ' ').title()}: {value}")
    else:
        print("⚠️ No comprehensive data extracted")
    
    print("\n" + "=" * 70)
    return result1, result2

if __name__ == "__main__":
    test_email_salary_parsing()
