"""
Test script for Gmail-only email validation
"""
import sys
import io
from app.utils.email_validator import validate_email, validate_email_list

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_valid_gmail():
    """Test valid Gmail addresses"""
    valid_emails = [
        "user@gmail.com",
        "test.user@gmail.com",
        "user123@gmail.com",
        "user_name@gmail.com",
        "user+tag@gmail.com",
    ]
    
    print("Testing VALID Gmail addresses:")
    for email in valid_emails:
        is_valid, error = validate_email(email)
        status = "[PASS]" if is_valid else "[FAIL]"
        print(f"  {status}: {email}")
        if not is_valid:
            print(f"    Error: {error}")
    print()

def test_invalid_non_gmail():
    """Test non-Gmail addresses (should be rejected)"""
    invalid_emails = [
        "user@yahoo.com",
        "user@outlook.com",
        "user@hotmail.com",
        "user@company.com",
        "abcdef",  # The problematic case from the user
        "test@test.com",
    ]
    
    print("Testing INVALID non-Gmail addresses (should be REJECTED):")
    for email in invalid_emails:
        is_valid, error = validate_email(email)
        status = "[PASS - Rejected]" if not is_valid else "[FAIL - Accepted]"
        print(f"  {status}: {email}")
        if not is_valid:
            print(f"    Error: {error}")
    print()

def test_gmail_typos():
    """Test common Gmail typos"""
    typo_emails = [
        "user@gmal.com",
        "user@gmial.com",
        "user@gmaill.com",
        "user@gmil.com",
        "user@gmai.com",
    ]
    
    print("Testing Gmail TYPOS (should be REJECTED with suggestions):")
    for email in typo_emails:
        is_valid, error = validate_email(email)
        status = "[PASS - Rejected]" if not is_valid else "[FAIL - Accepted]"
        print(f"  {status}: {email}")
        if not is_valid:
            print(f"    Error: {error}")
    print()

def test_invalid_format():
    """Test invalid email formats"""
    invalid_formats = [
        "notanemail",
        "@gmail.com",
        "user@",
        "user..name@gmail.com",
        ".user@gmail.com",
        "user.@gmail.com",
    ]
    
    print("Testing INVALID email formats:")
    for email in invalid_formats:
        is_valid, error = validate_email(email)
        status = "[PASS - Rejected]" if not is_valid else "[FAIL - Accepted]"
        print(f"  {status}: {email}")
        if not is_valid:
            print(f"    Error: {error}")
    print()

def test_email_list():
    """Test email list validation"""
    print("Testing EMAIL LIST validation:")
    
    # Valid list
    valid_list = ["user1@gmail.com", "user2@gmail.com"]
    is_valid, error, invalid = validate_email_list(valid_list)
    print(f"  Valid list: {is_valid} - {valid_list}")
    
    # Mixed list (should fail)
    mixed_list = ["user1@gmail.com", "user2@yahoo.com", "abcdef"]
    is_valid, error, invalid = validate_email_list(mixed_list)
    print(f"  Mixed list: {is_valid} - {mixed_list}")
    if not is_valid:
        print(f"    Error: {error}")
    print()

if __name__ == "__main__":
    print("=" * 70)
    print("GMAIL-ONLY EMAIL VALIDATION TEST")
    print("=" * 70)
    print()
    
    test_valid_gmail()
    test_invalid_non_gmail()
    test_gmail_typos()
    test_invalid_format()
    test_email_list()
    
    print("=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)

# Made with Bob
