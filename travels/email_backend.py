"""
Custom Django Email Backend using Brevo HTTP API
Uses HTTP/HTTPS instead of SMTP - works on DigitalOcean (no port blocking)
"""
import requests
import json
import logging
import os
from django.core.mail.backends.base import BaseEmailBackend
from django.conf import settings

logger = logging.getLogger('django.core.mail')


class BrevoAPIEmailBackend(BaseEmailBackend):
    """
    Brevo (Sendinblue) HTTP API Email Backend
    Uses Brevo's REST API instead of SMTP - works on DigitalOcean
    """
    
    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.api_key = getattr(settings, 'BREVO_SMTP_KEY', '') or os.environ.get('BREVO_SMTP_KEY', '')
        self.api_url = 'https://api.brevo.com/v3/smtp/email'
        self.from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@safarzonetravels.com')
        self.from_name = getattr(settings, 'DEFAULT_FROM_EMAIL_NAME', 'Safar Zone Travels')
    
    def send_messages(self, email_messages):
        """
        Send one or more EmailMessage objects and return the number of emails sent.
        """
        if not email_messages:
            return 0
        
        if not self.api_key:
            logger.error("Brevo API key not configured")
            if not self.fail_silently:
                raise ValueError("Brevo API key not configured")
            return 0
        
        num_sent = 0
        for message in email_messages:
            try:
                # Prepare Brevo API payload
                payload = {
                    'sender': {
                        'name': self.from_name,
                        'email': self.from_email
                    },
                    'to': [{'email': email} for email in message.to],
                    'subject': message.subject,
                }
                
                # Add HTML and text content
                html_content = None
                text_content = None
                
                # Check for HTML content in alternatives
                if hasattr(message, 'alternatives') and message.alternatives:
                    for content, mimetype in message.alternatives:
                        if mimetype == 'text/html':
                            html_content = content
                        elif mimetype == 'text/plain':
                            text_content = content
                
                # If no HTML in alternatives, check body
                if not html_content and not text_content:
                    # Assume body is HTML if it contains HTML tags
                    if '<html' in message.body.lower() or '<body' in message.body.lower() or '<div' in message.body.lower():
                        html_content = message.body
                    else:
                        text_content = message.body
                elif not html_content:
                    text_content = message.body
                else:
                    # HTML found in alternatives, use body as text fallback
                    text_content = message.body if message.body else None
                
                if html_content:
                    payload['htmlContent'] = html_content
                if text_content:
                    payload['textContent'] = text_content
                
                # Add CC and BCC if present
                if message.cc:
                    payload['cc'] = [{'email': email} for email in message.cc]
                if message.bcc:
                    payload['bcc'] = [{'email': email} for email in message.bcc]
                
                # Add reply-to if present
                if message.reply_to:
                    payload['replyTo'] = {'email': message.reply_to[0]}
                
                # Add attachments if present
                if message.attachments:
                    payload['attachment'] = []
                    for attachment in message.attachments:
                        import base64
                        if len(attachment) == 3:
                            filename, content, mimetype = attachment
                            payload['attachment'].append({
                                'name': filename,
                                'content': base64.b64encode(content).decode('utf-8')
                            })
                
                # Send via Brevo API
                headers = {
                    'accept': 'application/json',
                    'api-key': self.api_key,
                    'content-type': 'application/json'
                }
                
                logger.info(f"Sending email via Brevo API to {', '.join(message.to)}")
                response = requests.post(
                    self.api_url,
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 201:
                    logger.info(f"✓ Email sent successfully via Brevo API to {', '.join(message.to)}")
                    num_sent += 1
                else:
                    error_msg = f"Brevo API error: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    if not self.fail_silently:
                        raise Exception(error_msg)
                    
            except requests.exceptions.RequestException as e:
                error_msg = f"Brevo API request failed: {str(e)}"
                logger.error(error_msg)
                if not self.fail_silently:
                    raise Exception(error_msg)
            except Exception as e:
                error_msg = f"Error sending email via Brevo API: {str(e)}"
                logger.error(error_msg)
                if not self.fail_silently:
                    raise
        
        return num_sent

