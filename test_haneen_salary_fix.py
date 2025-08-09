#!/usr/bin/env python3
"""
Test and fix Haneen's salary extraction issue
"""

import os
import sys

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from parse_salary_email import parse_salary_email

def test_haneen_salary_format():
    """Test Haneen's specific salary format"""
    
    # Recreate Haneen's email format
    haneen_email = """Hi,

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
Yasser"""
    
    print("🧪 Testing Haneen's Salary Format")
    print("=" * 60)
    print("📧 Email format:")
    print("Basic")
    print("Housing") 
    print("Transport")
    print("Total")
    print("3,963.60")
    print("1,981.80")
    print("660.60")
    print("6,606.00")
    print()
    
    print("💰 Expected extraction:")
    print("   • Basic Salary: 3,963.60 AED")
    print("   • Housing Allowance: 1,981.80 AED")
    print("   • Transport Allowance: 660.60 AED")
    print("   • Total: 6,606.00 AED")
    print()
    
    print("🔍 Actual extraction:")
    try:
        salary_data = parse_salary_email(haneen_email)
        
        if salary_data:
            for key, value in salary_data.items():
                if isinstance(value, dict):
                    print(f"   📋 {key.replace('_', ' ').title()}:")
                    for sub_key, sub_value in value.items():
                        print(f"      • {sub_key}: {sub_value}")
                else:
                    print(f"   • {key.replace('_', ' ').title()}: {value}")
        else:
            print("   ❌ No salary data extracted")
            
        # Check if we got the correct total
        if salary_data and "Total_Monthly_Package" in salary_data:
            extracted_total = salary_data["Total_Monthly_Package"]
            if "6,606.00" in extracted_total:
                print("\n✅ SUCCESS: Extracted correct total (6,606.00 AED)")
            else:
                print(f"\n❌ WRONG: Expected 6,606.00 AED, got {extracted_total}")
        else:
            print("\n❌ MISSING: No total package found")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_haneen_salary_format()
