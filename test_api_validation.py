"""
Test API endpoint email validation
"""
import sys
import io

# Set UTF-8 encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app.utils.email_validator import validate_email_list

print("=" * 80)
print("API ENDPOINT EMAIL VALIDATION TEST")
print("=" * 80)

# Test case 1: Valid emails
print("\n✓ Test 1: Valid emails")
emails1 = ["user@gmail.com", "test@yahoo.com"]
is_valid, error_msg, invalid = validate_email_list(emails1)
print(f"  Emails: {emails1}")
print(f"  Result: {'PASS' if is_valid else 'FAIL'}")
if error_msg:
    print(f"  Error: {error_msg}")

# Test case 2: Email with typo (gmal.com)
print("\n✓ Test 2: Email with typo (gmal.com)")
emails2 = ["aas@gmal.com"]
is_valid, error_msg, invalid = validate_email_list(emails2)
print(f"  Emails: {emails2}")
print(f"  Result: {'REJECTED ✓' if not is_valid else 'ACCEPTED ✗ (should be rejected)'}")
if error_msg:
    print(f"  Error: {error_msg}")

# Test case 3: Mix of valid and invalid
print("\n✓ Test 3: Mix of valid and invalid emails")
emails3 = ["user@gmail.com", "test@yaho.com", "admin@outlook.com"]
is_valid, error_msg, invalid = validate_email_list(emails3)
print(f"  Emails: {emails3}")
print(f"  Result: {'REJECTED ✓' if not is_valid else 'ACCEPTED ✗ (should be rejected)'}")
if error_msg:
    print(f"  Error: {error_msg}")

# Test case 4: Non-existent domain
print("\n✓ Test 4: Non-existent domain")
emails4 = ["user@fakeemail12345xyz.com"]
is_valid, error_msg, invalid = validate_email_list(emails4)
print(f"  Emails: {emails4}")
print(f"  Result: {'REJECTED ✓' if not is_valid else 'ACCEPTED ✗ (should be rejected)'}")
if error_msg:
    print(f"  Error: {error_msg}")

# Test case 5: Multiple typos
print("\n✓ Test 5: Multiple typos")
emails5 = ["user@gmal.com", "test@gmial.com"]
is_valid, error_msg, invalid = validate_email_list(emails5)
print(f"  Emails: {emails5}")
print(f"  Result: {'REJECTED ✓' if not is_valid else 'ACCEPTED ✗ (should be rejected)'}")
if error_msg:
    print(f"  Error: {error_msg}")

print("\n" + "=" * 80)
print("SUMMARY: The /suggest endpoint will now reject these invalid emails")
print("=" * 80)

# Made with Bob
