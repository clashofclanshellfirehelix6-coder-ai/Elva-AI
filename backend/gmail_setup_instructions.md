# Gmail API Setup Instructions for Elva AI

This guide will help you set up Gmail API integration so users can check their inbox, send emails, and manage Gmail through Elva AI.

## 📋 Prerequisites

- Google account with Gmail access
- Google Cloud Console access
- Python environment with required dependencies

## 🚀 Step-by-Step Setup

### 1. Google Cloud Console Setup

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com/
   - Sign in with your Google account

2. **Create or Select Project**
   - Create a new project or select existing one
   - Note the project ID for reference

3. **Enable Gmail API**
   - Go to "APIs & Services" > "Library"
   - Search for "Gmail API"
   - Click "Enable"

### 2. Create OAuth 2.0 Credentials

1. **Go to Credentials**
   - Navigate to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"

2. **Configure OAuth Consent Screen** (if first time)
   - Choose "External" for user type
   - Fill in required fields:
     - App name: "Elva AI Gmail Integration"
     - User support email: your email
     - Developer contact: your email
   - Add scopes:
     - `https://www.googleapis.com/auth/gmail.readonly`
     - `https://www.googleapis.com/auth/gmail.send`
     - `https://www.googleapis.com/auth/gmail.modify`

3. **Create OAuth Client ID**
   - Application type: "Desktop application"
   - Name: "Elva AI Gmail Client"
   - Click "Create"

4. **Download Credentials**
   - Download the JSON file
   - Rename it to `credentials.json`
   - Place it in your backend directory: `backend/credentials.json`

### 3. Environment Configuration

1. **Update .env file**
   ```bash
   # Add to your backend/.env file
   GMAIL_CREDENTIALS_PATH=credentials.json
   GMAIL_TOKEN_PATH=token.json
   ```

2. **Install Dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

### 4. First-Time Authentication

1. **Run Authentication Script**
   ```python
   # Create a test script: backend/test_gmail_auth.py
   from gmail_service import gmail_service
   
   # This will open browser for OAuth flow
   success = gmail_service.authenticate()
   if success:
       print("✅ Gmail authentication successful!")
       profile = gmail_service.get_user_profile()
       print(f"Connected to: {profile.get('email_address')}")
   else:
       print("❌ Gmail authentication failed")
   ```

2. **Run the Script**
   ```bash
   cd backend
   python test_gmail_auth.py
   ```

3. **Complete OAuth Flow**
   - Browser will open automatically
   - Sign in to your Google account
   - Grant permissions to Elva AI
   - You'll see "The authentication flow has completed"
   - `token.json` file will be created automatically

### 5. Test Integration

1. **Test Basic Functionality**
   ```python
   # Test script: backend/test_gmail_integration.py
   from gmail_service import gmail_service
   
   # Authenticate
   if gmail_service.authenticate():
       # Test inbox check
       result = gmail_service.get_inbox_messages(max_results=5)
       print(f"Inbox check: {result['success']}")
       print(f"Messages found: {result['count']}")
       
       # Test unread count
       unread = gmail_service.get_unread_count()
       print(f"Unread emails: {unread['unread_count']}")
   ```

2. **Test with Elva AI**
   - Start the backend server
   - Use the frontend to ask: "Check my Gmail inbox"
   - Should return formatted email list

## 🔧 Configuration Options

### Custom Paths
```bash
# If you want to store credentials elsewhere
GMAIL_CREDENTIALS_PATH=/path/to/your/credentials.json
GMAIL_TOKEN_PATH=/path/to/your/token.json
```

### Gmail API Scopes
The integration uses these scopes:
- `gmail.readonly` - Read emails and labels
- `gmail.send` - Send emails
- `gmail.modify` - Mark emails as read/unread

## 🛠️ Troubleshooting

### Common Issues

1. **"Credentials file not found"**
   - Ensure `credentials.json` is in the correct path
   - Check `GMAIL_CREDENTIALS_PATH` in `.env`

2. **"Authentication failed"**
   - Delete `token.json` and re-authenticate
   - Check OAuth consent screen configuration
   - Ensure Gmail API is enabled

3. **"Insufficient permissions"**
   - Verify OAuth scopes in Google Cloud Console
   - Re-run authentication flow

4. **"Quota exceeded"**
   - Gmail API has daily quotas
   - Check usage in Google Cloud Console
   - Consider requesting quota increase

### Debug Mode
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🔒 Security Notes

- **Credentials Security**: Never commit `credentials.json` or `token.json` to version control
- **Token Refresh**: Tokens are automatically refreshed
- **Scope Limitation**: Only request necessary permissions
- **User Consent**: Users must explicitly grant permissions

## 📊 Usage Examples

Once set up, users can interact with Gmail naturally:

```
User: "Check my Gmail inbox"
Elva: 📧 Gmail Inbox (5 messages)
• **Project Update** from john@company.com 🔴
• **Meeting Reminder** from calendar@company.com

User: "How many unread emails do I have?"
Elva: 📬 Unread Emails: 3 messages

User: "Search for emails from Sarah"
Elva: 🔍 Found 2 emails from Sarah...
```

## ✅ Verification Checklist

- [ ] Google Cloud project created
- [ ] Gmail API enabled
- [ ] OAuth credentials downloaded as `credentials.json`
- [ ] Environment variables configured
- [ ] Dependencies installed
- [ ] First-time authentication completed
- [ ] `token.json` file created
- [ ] Test scripts run successfully
- [ ] Elva AI responds to Gmail queries

## 🆘 Support

If you encounter issues:
1. Check the logs for detailed error messages
2. Verify all setup steps were completed
3. Test with the provided test scripts
4. Check Google Cloud Console for API quotas and errors

The Gmail integration should now be fully functional with Elva AI!