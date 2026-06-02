# Gmail Account Verification Setup Guide

## Overview
This system now verifies that Gmail accounts **actually exist** using Google People API, preventing dummy/fake emails like "abcdefgh@gmail.com" from being accepted.

## 🔐 Two-Layer Validation

### Layer 1: Format Validation (Client & Server)
- ✅ Must be @gmail.com domain
- ✅ Valid email format
- ✅ No typos (gmal.com → gmail.com)
- ✅ Valid Gmail username patterns

### Layer 2: Existence Verification (Server)
- ✅ **NEW**: Verifies Gmail account actually exists
- ✅ Uses Google People API
- ✅ Checks if account is real and active
- ✅ Prevents dummy emails like "abcdefgh@gmail.com"

## 🚀 Setup Instructions

### Step 1: Update Google OAuth Scopes

You need to add the **Google People API** scope to your OAuth configuration.

#### 1.1 Update Your `.env` File

Add the People API scope to your `GOOGLE_API_SCOPES`:

```env
GOOGLE_API_SCOPES=https://www.googleapis.com/auth/calendar,https://www.googleapis.com/auth/calendar.events,https://www.googleapis.com/auth/userinfo.email,https://www.googleapis.com/auth/userinfo.profile,https://www.googleapis.com/auth/contacts.other.readonly
```

**Important**: The `contacts.other.readonly` scope is required for Gmail verification.

#### 1.2 Update Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project
3. Navigate to **APIs & Services** → **Enabled APIs & services**
4. Click **+ ENABLE APIS AND SERVICES**
5. Search for **"People API"**
6. Click **Enable**

#### 1.3 Update OAuth Consent Screen

1. Go to **APIs & Services** → **OAuth consent screen**
2. Click **Edit App**
3. In **Scopes** section, add:
   - `https://www.googleapis.com/auth/contacts.other.readonly`
4. Save changes

### Step 2: Restart Backend Server

After updating the `.env` file:

```bash
# Stop current server (Ctrl+C)
# Then restart
uvicorn app.main:app --reload
```

### Step 3: Re-authenticate Users

**IMPORTANT**: Existing users must log out and log back in to grant the new permission.

1. Users should log out of the application
2. Clear browser cookies/cache
3. Log in again
4. They will see a new permission request for "See your contacts"
5. Click **Allow**

## 🧪 Testing

### Test Case 1: Valid Gmail Account
```
Input: "realuser@gmail.com" (actual Gmail account)
Expected: ✅ Accepted
```

### Test Case 2: Dummy Gmail Account
```
Input: "abcdefgh@gmail.com" (doesn't exist)
Expected: ❌ Rejected with "Gmail account 'abcdefgh@gmail.com' could not be verified"
```

### Test Case 3: Non-Gmail Account
```
Input: "user@yahoo.com"
Expected: ❌ Rejected with "Only Gmail addresses (@gmail.com) are allowed"
```

### Test Case 4: Invalid Format
```
Input: "abcdef"
Expected: ❌ Rejected with "Invalid email format"
```

## 📋 How It Works

### Backend Flow

1. **User enters email** → Frontend validates format
2. **User clicks "Find Optimal Meeting Slots"** → Frontend validates all emails
3. **Request sent to backend** → Server validates format again
4. **Server verifies Gmail exists** → Uses Google People API
5. **If all valid** → Proceeds to find meeting slots
6. **If any invalid** → Returns 400 error with details

### API Verification Process

```python
# In app/api/meetings.py
@router.post("/suggest")
async def suggest_meeting_slots(...):
    # Step 1: Format validation
    is_valid, error_msg, invalid_emails = validate_email_list(participants)
    
    # Step 2: Gmail existence verification (NEW)
    accounts_valid, verify_error, invalid_accounts = verify_gmail_accounts(
        participants, 
        access_token
    )
```

## 🔍 Google People API Details

### What It Does
- Searches for the email in Google's directory
- Checks if the account exists and is accessible
- Returns verification status

### Limitations
- Requires user's OAuth token (user must be logged in)
- May not find accounts if privacy settings are strict
- Gracefully handles API errors (allows through on timeout/errors)

### Error Handling
The system is designed to be **user-friendly**:
- ✅ If API is unavailable → Allows email through (doesn't block users)
- ✅ If permissions insufficient → Allows email through
- ❌ If account definitely doesn't exist → Rejects email
- ❌ If format is invalid → Rejects email

## 🛠️ Troubleshooting

### Issue: "Insufficient permissions" error

**Solution**: User needs to re-authenticate with new scopes
1. Log out
2. Clear cookies
3. Log in again
4. Grant "See your contacts" permission

### Issue: All emails being rejected

**Check**:
1. Is People API enabled in Google Cloud Console?
2. Is the scope added to `.env` file?
3. Did you restart the backend server?
4. Did users re-authenticate?

### Issue: Dummy emails still being accepted

**Check**:
1. Is the frontend code updated? (Restart dev server)
2. Clear browser cache (Ctrl+Shift+R)
3. Check browser console for errors
4. Verify backend logs show "Verifying Gmail accounts..."

### Issue: Real Gmail accounts being rejected

**Possible causes**:
1. Account has strict privacy settings
2. Account is new (not indexed yet)
3. API rate limit reached

**Solution**: Check backend logs for specific error messages

## 📊 Monitoring

### Backend Logs

Look for these log messages:

```
INFO: Verifying 2 Gmail accounts exist...
INFO: Gmail account verified: user@gmail.com
INFO: All 2 Gmail accounts verified successfully
```

Or errors:

```
WARNING: Gmail account not found or not accessible: abcdefgh@gmail.com
ERROR: Google People API error for abcdefgh@gmail.com: ...
```

### Success Indicators

✅ Valid emails are accepted  
✅ Dummy emails are rejected  
✅ Clear error messages shown  
✅ No false positives (real accounts rejected)  
✅ No false negatives (fake accounts accepted)  

## 🔄 Rollback Plan

If Gmail verification causes issues, you can temporarily disable it:

### Option 1: Comment Out Verification

In `app/api/meetings.py`, comment out the verification step:

```python
# Step 2: Verify Gmail accounts actually exist using Google People API
# if participants:
#     logger.info(f"Verifying {len(participants)} Gmail accounts exist...")
#     accounts_valid, verify_error, invalid_accounts = verify_gmail_accounts(
#         participants, 
#         access_token
#     )
#     if not accounts_valid:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=verify_error
#         )
#     logger.info(f"All {len(participants)} Gmail accounts verified successfully")
```

### Option 2: Modify Error Handling

Make verification non-blocking by catching exceptions:

```python
try:
    accounts_valid, verify_error, invalid_accounts = verify_gmail_accounts(
        participants, access_token
    )
    if not accounts_valid:
        logger.warning(f"Gmail verification failed: {verify_error}")
        # Don't raise exception, just log warning
except Exception as e:
    logger.error(f"Gmail verification error: {e}")
    # Continue without verification
```

## 📚 Additional Resources

- [Google People API Documentation](https://developers.google.com/people)
- [OAuth 2.0 Scopes](https://developers.google.com/identity/protocols/oauth2/scopes)
- [Google Cloud Console](https://console.cloud.google.com/)

## ✅ Deployment Checklist

Before deploying to production:

- [ ] People API enabled in Google Cloud Console
- [ ] OAuth consent screen updated with new scope
- [ ] `.env` file updated with new scope
- [ ] Backend server restarted
- [ ] Frontend rebuilt and deployed
- [ ] Test with real Gmail accounts
- [ ] Test with dummy Gmail accounts
- [ ] Test error handling
- [ ] Monitor logs for issues
- [ ] Inform users they need to re-authenticate

---

**Status**: ✅ Implementation Complete  
**Last Updated**: 2026-06-02  
**Feature**: Gmail Account Existence Verification