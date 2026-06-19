import os
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.api_python_client import discovery
from config import GMAIL_CREDENTIALS_PATH, GMAIL_TOKEN_PATH, GMAIL_USER_EMAIL, GMAIL_QUERY

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.send']

class GmailClient:
    def __init__(self):
        self.service = self._authenticate()
    
    def _authenticate(self):
        creds = None
        
        # Load existing token
        if os.path.exists(GMAIL_TOKEN_PATH):
            creds = Credentials.from_authorized_user_file(GMAIL_TOKEN_PATH, SCOPES)
        
        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(GMAIL_CREDENTIALS_PATH, SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save token for next run
            with open(GMAIL_TOKEN_PATH, 'w') as token:
                token.write(creds.to_json())
        
        return discovery.build('gmail', 'v1', credentials=creds)
    
    def get_unread_emails(self):
        """Fetch unread emails matching the query"""
        try:
            results = self.service.users().messages().list(
                userId='me',
                q=f'is:unread {GMAIL_QUERY}',
                maxResults=10
            ).execute()
            
            messages = results.get('messages', [])
            return [self._get_message_details(msg['id']) for msg in messages]
        
        except Exception as e:
            print(f"Error fetching emails: {e}")
            return []
    
    def _get_message_details(self, message_id):
        """Get full message details including attachments"""
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            headers = message['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), '')
            
            # Extract body
            body = self._extract_body(message['payload'])
            
            # Extract attachments
            attachments = self._extract_attachments(message['payload'])
            
            return {
                'id': message_id,
                'subject': subject,
                'sender': sender,
                'body': body,
                'attachments': attachments
            }
        
        except Exception as e:
            print(f"Error getting message details: {e}")
            return None
    
    def _extract_body(self, payload):
        """Extract email body text"""
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    if 'data' in part['body']:
                        return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
        elif 'body' in payload:
            if 'data' in payload['body']:
                return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
        return ''
    
    def _extract_attachments(self, payload):
        """Extract attachment file IDs and filenames"""
        attachments = []
        if 'parts' in payload:
            for part in payload['parts']:
                if part['filename']:
                    attachments.append({
                        'filename': part['filename'],
                        'mimeType': part['mimeType'],
                        'attachmentId': part['body'].get('attachmentId')
                    })
        return attachments
    
    def download_attachment(self, message_id, attachment_id, filename):
        """Download attachment and save to file"""
        try:
            attachment = self.service.users().messages().attachments().get(
                userId='me',
                messageId=message_id,
                id=attachment_id
            ).execute()
            
            file_data = base64.urlsafe_b64decode(attachment['data'])
            os.makedirs('downloads', exist_ok=True)
            filepath = os.path.join('downloads', filename)
            
            with open(filepath, 'wb') as f:
                f.write(file_data)
            
            return filepath
        
        except Exception as e:
            print(f"Error downloading attachment: {e}")
            return None
    
    def send_email(self, recipient, subject, body, attachments=None):
        """Send email with optional attachments"""
        try:
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            from email.mime.base import MIMEBase
            from email import encoders
            
            message = MIMEMultipart()
            message['to'] = recipient
            message['subject'] = subject
            
            message.attach(MIMEText(body, 'html'))
            
            if attachments:
                for filepath in attachments:
                    with open(filepath, 'rb') as attachment:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(attachment.read())
                    
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', f'attachment; filename= {os.path.basename(filepath)}')
                    message.attach(part)
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            send_message = {'raw': raw_message}
            
            self.service.users().messages().send(userId='me', body=send_message).execute()
            print(f"Email sent to {recipient}")
        
        except Exception as e:
            print(f"Error sending email: {e}")
    
    def mark_as_read(self, message_id):
        """Mark message as read"""
        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
        except Exception as e:
            print(f"Error marking message as read: {e}")
