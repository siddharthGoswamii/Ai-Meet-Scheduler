"""
Test script for email validation
"""
import sys
import io

# Set UTF-8 encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app.utils.email_validator import validate_email

# Test cases
test_emails = [
    # Valid emails
    ("user@gmail.com", True, "Valid Gmail"),
    ("test@yahoo.com", True, "Valid Yahoo"),
    ("admin@outlook.com", True, "Valid Outlook"),
    
    # Invalid - fake emails
    ("abcdef@gmail.com", True, "Fake Gmail (should pass format but domain exists)"),
    
    # Invalid - typos
    ("user@gmal.com", False, "Typo: gmal.com instead of gmail.com"),
    ("test@gmial.com", False, "Typo: gmial.com instead of gmail.com"),
    ("admin@yaho.com", False, "Typo: yaho.com instead of yahoo.com"),
    ("user@hotmial.com", False, "Typo: hotmial.com instead of hotmail.com"),
    
    # Invalid - non-existent domains
    ("user@thisisafakedomain12345.com", False, "Non-existent domain"),
    ("test@invaliddomain999.net", False, "Invalid domain"),
    
    # Invalid format
    ("notanemail", False, "Invalid format - no @"),
    ("@gmail.com", False, "Invalid format - no local part"),
    ("user@", False, "Invalid format - no domain"),
]

print("=" * 80)
print("EMAIL VALIDATION TEST RESULTS")
print("=" * 80)

for email, expected_valid, description in test_emails:
    is_valid, error_msg = validate_email(email)
    status = "✓ PASS" if is_valid == expected_valid else "✗ FAIL"
    
    print(f"\n{status} | {description}")
    print(f"  Email: {email}")
    print(f"  Expected: {'Valid' if expected_valid else 'Invalid'}")
    print(f"  Result: {'Valid' if is_valid else 'Invalid'}")
    if error_msg:
        print(f"  Error: {error_msg}")

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)

# Made with Bob
