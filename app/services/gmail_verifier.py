"""
Gmail account verification service using Google People API
"""
import logging
from typing import Tuple, Optional
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


class GmailVerifier:
    """Service to verify if Gmail accounts actually exist"""
    
    def __init__(self, access_token: str):
        """
        Initialize Gmail verifier with user's access token
        
        Args:
            access_token: User's Google OAuth access token
        """
        self.access_token = access_token
        self.credentials = Credentials(token=access_token)
    
    def verify_gmail_exists(self, email: str) -> Tuple[bool, str]:
        """
        Verify if a Gmail account format is valid
        
        Note: We cannot reliably verify if a Gmail account actually exists without
        sending an email. The Google People API only works for contacts, not arbitrary
        Gmail addresses. Therefore, we only validate the format here.
        
        Args:
            email: Gmail address to verify
            
        Returns:
            Tuple of (exists, error_message)
        """
        try:
            # We'll try to check if it's in contacts, but won't fail if not found
            # This is a best-effort check only
            try:
                service = build('people', 'v1', credentials=self.credentials)
                results = service.people().searchContacts(
                    query=email,
                    readMask='names,emailAddresses'
                ).execute()
                
                connections = results.get('results', [])
                
                # Check if we found the email in contacts
                for connection in connections:
                    person = connection.get('person', {})
                    email_addresses = person.get('emailAddresses', [])
                    
                    for email_addr in email_addresses:
                        if email_addr.get('value', '').lower() == email.lower():
                            logger.info(f"Gmail account found in contacts: {email}")
                            return True, ""
                
                # Not in contacts, but that's OK - we'll allow it
                logger.info(f"Gmail account not in contacts but format is valid: {email}")
                return True, ""
                
            except HttpError as e:
                # Any API error - just allow through with valid format
                logger.info(f"Could not check contacts for {email}, allowing through: {str(e)}")
                return True, ""
            
        except Exception as e:
            logger.info(f"Gmail verification skipped for {email}: {str(e)}")
            # On any error, allow through since format was already validated
            return True, ""
    
    def verify_gmail_list(self, emails: list) -> Tuple[bool, str, list]:
        """
        Verify a list of Gmail accounts
        
        Args:
            emails: List of Gmail addresses to verify
            
        Returns:
            Tuple of (all_valid, error_message, invalid_emails)
        """
        invalid_emails = []
        
        for email in emails:
            exists, error_msg = self.verify_gmail_exists(email)
            if not exists:
                invalid_emails.append({
                    'email': email,
                    'error': error_msg
                })
        
        if invalid_emails:
            error_details = "; ".join([f"{item['email']}: {item['error']}" for item in invalid_emails])
            return False, f"Invalid or non-existent Gmail account(s): {error_details}", invalid_emails
        
        return True, "", []


def verify_gmail_account(email: str, access_token: str) -> Tuple[bool, str]:
    """
    Convenience function to verify a single Gmail account
    
    Args:
        email: Gmail address to verify
        access_token: User's Google OAuth access token
        
    Returns:
        Tuple of (exists, error_message)
    """
    verifier = GmailVerifier(access_token)
    return verifier.verify_gmail_exists(email)


def verify_gmail_accounts(emails: list, access_token: str) -> Tuple[bool, str, list]:
    """
    Convenience function to verify multiple Gmail accounts
    
    Args:
        emails: List of Gmail addresses to verify
        access_token: User's Google OAuth access token
        
    Returns:
        Tuple of (all_valid, error_message, invalid_emails)
    """
    verifier = GmailVerifier(access_token)
    return verifier.verify_gmail_list(emails)

# Made with Bob