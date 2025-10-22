"""
Email delivery using Resend API
"""

import resend
import logging
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class EmailSender:
    """Handles email delivery using Resend API"""

    def __init__(self, api_key: str, from_email: str):
        """
        Initialize email sender

        Args:
            api_key: Resend API key
            from_email: From email address
        """
        self.api_key = api_key
        self.from_email = from_email
        resend.api_key = api_key

    def send_daily_digest(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send daily digest email

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email content
            text_content: Plain text fallback content

        Returns:
            Resend API response
        """
        try:
            logger.info(f"Sending daily digest to {to_email}")

            # Prepare email parameters
            params = {
                "from": self.from_email,
                "to": [to_email],
                "subject": subject,
                "html": html_content,
            }

            # Add text content if provided
            if text_content:
                params["text"] = text_content

            # Send email
            response = resend.Emails.send(params)

            # Check response
            if response.get("id"):
                logger.info(f"Email sent successfully. ID: {response['id']}")
                return response
            else:
                error_msg = response.get("message", "Unknown error")
                logger.error(f"Failed to send email: {error_msg}")
                raise Exception(f"Email send failed: {error_msg}")

        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            raise

    def send_test_email(self, to_email: str) -> Dict[str, Any]:
        """
        Send a test email to verify configuration

        Args:
            to_email: Recipient email address

        Returns:
            Resend API response
        """
        try:
            logger.info("Sending test email")

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>VibeList Test</title>
                <style>
                    body {{ font-family: monospace; background: #000; color: #0f0; padding: 20px; }}
                    .container {{ max-width: 600px; margin: 0 auto; border: 2px solid #0f0; padding: 20px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>VIBELIST SYSTEM TEST</h1>
                    <p>This is a test email from VibeList.</p>
                    <p>If you're receiving this, your email configuration is working correctly!</p>
                    <p>System Time: {timestamp}</p>
                    <hr>
                    <p><em>VibeList v1.0 - Daily Portfolio Digest</em></p>
                </div>
            </body>
            </html>
            """

            text_content = f"""
VIBELIST SYSTEM TEST

This is a test email from VibeList.

If you're receiving this, your email configuration is working correctly!

System Time: {timestamp}

---
VibeList v1.0 - Daily Portfolio Digest
            """

            return self.send_daily_digest(
                to_email=to_email,
                subject="[TEST] VibeList Email Configuration",
                html_content=html_content,
                text_content=text_content
            )

        except Exception as e:
            logger.error(f"Error sending test email: {str(e)}")
            raise

    def validate_configuration(self) -> bool:
        """
        Validate email configuration

        Returns:
            True if configuration is valid, False otherwise
        """
        try:
            # Basic validation of API key format
            if not self.api_key or len(self.api_key) < 10:
                logger.error("Invalid Resend API key format")
                return False

            # Basic email validation
            if not self.from_email or "@" not in self.from_email:
                logger.error("Invalid from email address")
                return False

            logger.info("Email configuration validation passed")
            return True

        except Exception as e:
            logger.error(f"Error validating email configuration: {str(e)}")
            return False

    def create_digest_subject(self, portfolio_score: float, date: datetime) -> str:
        """
        Create email subject for daily digest

        Args:
            portfolio_score: Overall portfolio score
            date: Digest date

        Returns:
            Formatted email subject
        """
        # Determine sentiment emoji
        if portfolio_score > 0.3:
            emoji = "📈"
        elif portfolio_score < -0.3:
            emoji = "📉"
        else:
            emoji = "📊"

        date_str = date.strftime("%Y-%m-%d")
        score_str = f"{portfolio_score:+.3f}"

        return f"{emoji} VibeList Daily Digest - {date_str} (Score: {score_str})"
