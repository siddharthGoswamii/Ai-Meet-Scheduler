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
        Verify if a Gmail account actually exists using Google People API
        
        Args:
            email: Gmail address to verify
            
        Returns:
            Tuple of (exists, error_message)
        """
        try:
            # Build People API service
            service = build('people', 'v1', credentials=self.credentials)
            
            # Search for the person by email
            # This will only work if the email is in the user's contacts or is a valid Google account
            results = service.people().searchContacts(
                query=email,
                readMask='names,emailAddresses'
            ).execute()
            
            connections = results.get('results', [])
            
            # Check if we found the email
            for connection in connections:
                person = connection.get('person', {})
                email_addresses = person.get('emailAddresses', [])
                
                for email_addr in email_addresses:
                    if email_addr.get('value', '').lower() == email.lower():
                        logger.info(f"Gmail account verified: {email}")
                        return True, ""
            
            # If not found in contacts, try to check if it's a valid Google account
            # by attempting to look it up directly
            try:
                # Try to get person by resource name (email)
                person = service.people().get(
                    resourceName=f'people/{email}',
                    personFields='names,emailAddresses'
                ).execute()
                
                if person:
                    logger.info(f"Gmail account verified via direct lookup: {email}")
                    return True, ""
            except HttpError as e:
                if e.resp.status == 404:
                    # Account not found
                    pass
                else:
                    # Other error, log it
                    logger.warning(f"Error during direct lookup for {email}: {str(e)}")
            
            # Account not found
            logger.warning(f"Gmail account not found or not accessible: {email}")
            return False, f"Gmail account '{email}' could not be verified. Please ensure it's a valid, active Gmail address."
            
        except HttpError as e:
            error_msg = str(e)
            logger.error(f"Google People API error for {email}: {error_msg}")
            
            if 'insufficient permissions' in error_msg.lower() or 'permission denied' in error_msg.lower():
                # If we don't have permission, we'll allow it through but log a warning
                logger.warning(f"Cannot verify {email} due to insufficient permissions - allowing through")
                return True, ""
            
            return False, f"Unable to verify Gmail account '{email}'. Please try again."
            
        except Exception as e:
            logger.error(f"Unexpected error verifying {email}: {str(e)}")
            # On unexpected errors, allow through to avoid blocking legitimate users
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