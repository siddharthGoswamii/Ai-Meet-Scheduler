"""
Email validation utility with STRICT Gmail-only validation for serious meetings
"""
import re
from typing import Tuple
import logging

logger = logging.getLogger(__name__)

# STRICT: Only Gmail addresses are allowed for serious meetings
ALLOWED_DOMAIN = 'gmail.com'

# Common typos for Gmail domain
GMAIL_TYPOS = {
    'gmal.com': 'gmail.com',
    'gmial.com': 'gmail.com',
    'gmaill.com': 'gmail.com',
    'gmil.com': 'gmail.com',
    'gmai.com': 'gmail.com',
    'gmailcom': 'gmail.com',
    'gmail.co': 'gmail.com',
    'gmail.cm': 'gmail.com',
}


def validate_email_format(email: str) -> Tuple[bool, str]:
    """
    Validate email format using regex - STRICT Gmail only
    
    Args:
        email: Email address to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Basic email regex pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(pattern, email):
        return False, "Invalid email format"
    
    return True, ""


def check_gmail_typo(domain: str) -> Tuple[bool, str]:
    """
    Check if domain is a common Gmail typo
    
    Args:
        domain: Email domain to check
        
    Returns:
        Tuple of (is_typo, suggested_domain)
    """
    domain_lower = domain.lower()
    
    if domain_lower in GMAIL_TYPOS:
        return True, GMAIL_TYPOS[domain_lower]
    
    return False, ""


def validate_email(email: str) -> Tuple[bool, str]:
    """
    STRICT Gmail-only email validation for serious meetings
    
    Args:
        email: Email address to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Step 1: Validate format
    is_valid_format, format_error = validate_email_format(email)
    if not is_valid_format:
        return False, format_error
    
    # Extract domain
    try:
        local_part, domain = email.rsplit('@', 1)
    except ValueError:
        return False, "Invalid email format"
    
    domain_lower = domain.lower()
    
    # Step 2: Check for Gmail typos
    is_typo, suggested_domain = check_gmail_typo(domain_lower)
    if is_typo:
        return False, f"Did you mean '{local_part}@{suggested_domain}'? Please use a valid Gmail address."
    
    # Step 3: STRICT - Only Gmail addresses allowed
    if domain_lower != ALLOWED_DOMAIN:
        return False, f"Only Gmail addresses (@gmail.com) are allowed for serious meetings. '{email}' is not a valid Gmail address."
    
    # Step 4: Validate local part (username)
    if not local_part or len(local_part) < 1:
        return False, "Email username cannot be empty"
    
    # Check for invalid characters in local part
    if '..' in local_part or local_part.startswith('.') or local_part.endswith('.'):
        return False, "Invalid Gmail address format"
    
    return True, ""


def validate_email_list(emails: list) -> Tuple[bool, str, list]:
    """
    Validate a list of email addresses
    
    Args:
        emails: List of email addresses to validate
        
    Returns:
        Tuple of (all_valid, error_message, invalid_emails)
    """
    invalid_emails = []
    
    for email in emails:
        is_valid, error_msg = validate_email(email)
        if not is_valid:
            invalid_emails.append({
                'email': email,
                'error': error_msg
            })
    
    if invalid_emails:
        error_details = "; ".join([f"{item['email']}: {item['error']}" for item in invalid_emails])
        return False, f"Invalid email(s) found: {error_details}", invalid_emails
    
    return True, "", []

# Made with Bob
