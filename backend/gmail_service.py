import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import base64
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

# Gmail API scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify'
]

class GmailService:
    """
    Gmail API service for reading, sending, and managing emails
    """
    
    def __init__(self):
        self.service = None
        self.credentials = None
        
    def authenticate(self, credentials_path: str = None, token_path: str = None) -> bool:
        """
        Authenticate with Gmail API using OAuth2
        
        Args:
            credentials_path: Path to credentials.json file
            token_path: Path to token.json file for stored credentials
            
        Returns:
            bool: True if authentication successful
        """
        try:
            creds = None
            token_file = token_path or 'token.json'
            
            # Load existing token if available
            if os.path.exists(token_file):
                creds = Credentials.from_authorized_user_file(token_file, SCOPES)
            
            # If no valid credentials, get new ones
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not credentials_path:
                        credentials_path = os.getenv('GMAIL_CREDENTIALS_PATH', 'credentials.json')
                    
                    if not os.path.exists(credentials_path):
                        logger.error(f"Gmail credentials file not found: {credentials_path}")
                        return False
                    
                    flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
                    creds = flow.run_local_server(port=0)
                
                # Save credentials for next run
                with open(token_file, 'w') as token:
                    token.write(creds.to_json())
            
            self.credentials = creds
            self.service = build('gmail', 'v1', credentials=creds)
            logger.info("Gmail API authentication successful")
            return True
            
        except Exception as e:
            logger.error(f"Gmail authentication failed: {e}")
            return False
    
    def get_inbox_messages(self, max_results: int = 10, query: str = None) -> Dict[str, Any]:
        """
        Get messages from Gmail inbox
        
        Args:
            max_results: Maximum number of messages to retrieve
            query: Gmail search query (optional)
            
        Returns:
            Dict containing messages and metadata
        """
        try:
            if not self.service:
                return {"success": False, "error": "Gmail service not authenticated"}
            
            # Get message list
            results = self.service.users().messages().list(
                userId='me',
                maxResults=max_results,
                q=query or 'in:inbox'
            ).execute()
            
            messages = results.get('messages', [])
            
            if not messages:
                return {
                    "success": True,
                    "messages": [],
                    "count": 0,
                    "message": "No messages found in inbox"
                }
            
            # Get detailed message information
            detailed_messages = []
            for msg in messages:
                try:
                    message_detail = self.service.users().messages().get(
                        userId='me',
                        id=msg['id'],
                        format='full'
                    ).execute()
                    
                    # Extract message details
                    headers = message_detail['payload'].get('headers', [])
                    subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                    sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
                    date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown Date')
                    
                    # Extract message body
                    body = self._extract_message_body(message_detail['payload'])
                    
                    # Check if message is unread
                    is_unread = 'UNREAD' in message_detail.get('labelIds', [])
                    
                    detailed_messages.append({
                        "id": msg['id'],
                        "subject": subject,
                        "sender": sender,
                        "date": date,
                        "body_preview": body[:200] + "..." if len(body) > 200 else body,
                        "is_unread": is_unread,
                        "thread_id": message_detail.get('threadId')
                    })
                    
                except Exception as e:
                    logger.warning(f"Failed to get details for message {msg['id']}: {e}")
                    continue
            
            return {
                "success": True,
                "messages": detailed_messages,
                "count": len(detailed_messages),
                "total_in_inbox": results.get('resultSizeEstimate', 0),
                "message": f"Retrieved {len(detailed_messages)} messages from inbox"
            }
            
        except HttpError as e:
            logger.error(f"Gmail API error: {e}")
            return {
                "success": False,
                "error": f"Gmail API error: {str(e)}",
                "messages": []
            }
        except Exception as e:
            logger.error(f"Unexpected error getting inbox: {e}")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "messages": []
            }
    
    def get_unread_count(self) -> Dict[str, Any]:
        """
        Get count of unread messages
        
        Returns:
            Dict containing unread count and status
        """
        try:
            if not self.service:
                return {"success": False, "error": "Gmail service not authenticated"}
            
            # Get unread messages count
            results = self.service.users().messages().list(
                userId='me',
                q='is:unread in:inbox'
            ).execute()
            
            unread_count = results.get('resultSizeEstimate', 0)
            
            return {
                "success": True,
                "unread_count": unread_count,
                "message": f"You have {unread_count} unread messages"
            }
            
        except Exception as e:
            logger.error(f"Error getting unread count: {e}")
            return {
                "success": False,
                "error": str(e),
                "unread_count": 0
            }
    
    def send_email(self, to: str, subject: str, body: str, cc: str = None, bcc: str = None) -> Dict[str, Any]:
        """
        Send an email via Gmail API
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body
            cc: CC recipients (optional)
            bcc: BCC recipients (optional)
            
        Returns:
            Dict containing send status and message ID
        """
        try:
            if not self.service:
                return {"success": False, "error": "Gmail service not authenticated"}
            
            # Create message
            message = MIMEMultipart()
            message['to'] = to
            message['subject'] = subject
            
            if cc:
                message['cc'] = cc
            if bcc:
                message['bcc'] = bcc
            
            # Add body
            message.attach(MIMEText(body, 'plain'))
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            # Send message
            send_result = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            return {
                "success": True,
                "message_id": send_result['id'],
                "message": f"Email sent successfully to {to}"
            }
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def mark_as_read(self, message_ids: List[str]) -> Dict[str, Any]:
        """
        Mark messages as read
        
        Args:
            message_ids: List of message IDs to mark as read
            
        Returns:
            Dict containing operation status
        """
        try:
            if not self.service:
                return {"success": False, "error": "Gmail service not authenticated"}
            
            if not message_ids:
                return {"success": True, "message": "No messages to mark as read"}
            
            # Remove UNREAD label from messages
            self.service.users().messages().batchModify(
                userId='me',
                body={
                    'ids': message_ids,
                    'removeLabelIds': ['UNREAD']
                }
            ).execute()
            
            return {
                "success": True,
                "message": f"Marked {len(message_ids)} messages as read"
            }
            
        except Exception as e:
            logger.error(f"Error marking messages as read: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def search_emails(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """
        Search emails using Gmail search syntax
        
        Args:
            query: Gmail search query
            max_results: Maximum number of results
            
        Returns:
            Dict containing search results
        """
        try:
            if not self.service:
                return {"success": False, "error": "Gmail service not authenticated"}
            
            # Perform search
            results = self.service.users().messages().list(
                userId='me',
                maxResults=max_results,
                q=query
            ).execute()
            
            messages = results.get('messages', [])
            
            if not messages:
                return {
                    "success": True,
                    "messages": [],
                    "count": 0,
                    "message": f"No messages found for query: {query}"
                }
            
            # Get message details
            detailed_messages = []
            for msg in messages:
                try:
                    message_detail = self.service.users().messages().get(
                        userId='me',
                        id=msg['id'],
                        format='full'
                    ).execute()
                    
                    headers = message_detail['payload'].get('headers', [])
                    subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                    sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
                    date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown Date')
                    
                    body = self._extract_message_body(message_detail['payload'])
                    
                    detailed_messages.append({
                        "id": msg['id'],
                        "subject": subject,
                        "sender": sender,
                        "date": date,
                        "body_preview": body[:200] + "..." if len(body) > 200 else body
                    })
                    
                except Exception as e:
                    logger.warning(f"Failed to get details for search result {msg['id']}: {e}")
                    continue
            
            return {
                "success": True,
                "messages": detailed_messages,
                "count": len(detailed_messages),
                "query": query,
                "message": f"Found {len(detailed_messages)} messages for query: {query}"
            }
            
        except Exception as e:
            logger.error(f"Error searching emails: {e}")
            return {
                "success": False,
                "error": str(e),
                "messages": []
            }
    
    def _extract_message_body(self, payload: Dict) -> str:
        """
        Extract message body from Gmail API payload
        
        Args:
            payload: Gmail message payload
            
        Returns:
            str: Extracted message body
        """
        try:
            body = ""
            
            if 'parts' in payload:
                # Multipart message
                for part in payload['parts']:
                    if part['mimeType'] == 'text/plain':
                        if 'data' in part['body']:
                            body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                            break
                    elif part['mimeType'] == 'text/html' and not body:
                        if 'data' in part['body']:
                            body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
            else:
                # Single part message
                if payload['mimeType'] == 'text/plain' or payload['mimeType'] == 'text/html':
                    if 'data' in payload['body']:
                        body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
            
            return body.strip()
            
        except Exception as e:
            logger.warning(f"Failed to extract message body: {e}")
            return "Could not extract message body"
    
    def get_user_profile(self) -> Dict[str, Any]:
        """
        Get Gmail user profile information
        
        Returns:
            Dict containing user profile data
        """
        try:
            if not self.service:
                return {"success": False, "error": "Gmail service not authenticated"}
            
            profile = self.service.users().getProfile(userId='me').execute()
            
            return {
                "success": True,
                "email_address": profile.get('emailAddress'),
                "messages_total": profile.get('messagesTotal'),
                "threads_total": profile.get('threadsTotal'),
                "history_id": profile.get('historyId')
            }
            
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            return {
                "success": False,
                "error": str(e)
            }

# Global Gmail service instance
gmail_service = GmailService()