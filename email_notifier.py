#!/usr/bin/env python3
"""
Email notification system for crawler
Sends email when crawler completes
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os


def send_email_notification(subject, body, to_email, from_email=None, password=None):
    """
    Send email notification using Gmail SMTP
    
    Args:
        subject: Email subject
        body: Email body (can be HTML)
        to_email: Recipient email address
        from_email: Sender Gmail address (optional, reads from env)
        password: Gmail app password (optional, reads from env)
    """
    # Get credentials from environment variables if not provided
    from_email = from_email or os.getenv('GMAIL_ADDRESS')
    password = password or os.getenv('GMAIL_APP_PASSWORD')
    
    if not from_email or not password:
        print("❌ Email credentials not configured")
        print("Set GMAIL_ADDRESS and GMAIL_APP_PASSWORD environment variables")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = from_email
        msg['To'] = to_email
        
        # Add body
        html_part = MIMEText(body, 'html')
        msg.attach(html_part)
        
        # Send via Gmail SMTP
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(from_email, password)
            server.send_message(msg)
        
        print(f"✅ Email sent to {to_email}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False


def create_success_email(product_count, elapsed_time, date=None):
    """Create HTML email for successful crawler run"""
    date = date or datetime.now().strftime('%Y-%m-%d')
    
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f5f5f5;">
        <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 10px; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <h1 style="color: #10b981; margin-bottom: 20px;">✅ Crawler Success</h1>
            
            <div style="background-color: #f0fdf4; border-left: 4px solid #10b981; padding: 15px; margin: 20px 0;">
                <h2 style="margin: 0 0 10px 0; color: #065f46;">Run Summary</h2>
                <p style="margin: 5px 0;"><strong>Date:</strong> {date}</p>
                <p style="margin: 5px 0;"><strong>Products Collected:</strong> {product_count}</p>
                <p style="margin: 5px 0;"><strong>Execution Time:</strong> {elapsed_time:.1f} seconds</p>
            </div>
            
            <div style="margin: 20px 0;">
                <h3 style="color: #374151;">What's Next?</h3>
                <ul style="color: #6b7280;">
                    <li>View data on dashboard: <a href="http://localhost:5001">http://localhost:5001</a></li>
                    <li>Check logs for details</li>
                    <li>Data automatically saved to database</li>
                </ul>
            </div>
            
            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb; color: #9ca3af; font-size: 12px;">
                <p>This is an automated message from your GPU/RAM Price Index Crawler</p>
                <p>Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        </div>
    </body>
    </html>
    """
    return html


def create_failure_email(error_message, date=None):
    """Create HTML email for failed crawler run"""
    date = date or datetime.now().strftime('%Y-%m-%d')
    
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f5f5f5;">
        <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 10px; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <h1 style="color: #ef4444; margin-bottom: 20px;">❌ Crawler Failed</h1>
            
            <div style="background-color: #fef2f2; border-left: 4px solid #ef4444; padding: 15px; margin: 20px 0;">
                <h2 style="margin: 0 0 10px 0; color: #991b1b;">Error Details</h2>
                <p style="margin: 5px 0;"><strong>Date:</strong> {date}</p>
                <p style="margin: 5px 0;"><strong>Error:</strong> {error_message}</p>
            </div>
            
            <div style="margin: 20px 0;">
                <h3 style="color: #374151;">Troubleshooting Steps:</h3>
                <ol style="color: #6b7280;">
                    <li>Check the log file for detailed error trace</li>
                    <li>Verify database connection</li>
                    <li>Try running manually: <code>python3 daily_crawler.py</code></li>
                    <li>Check internet connection</li>
                </ol>
            </div>
            
            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb; color: #9ca3af; font-size: 12px;">
                <p>This is an automated message from your GPU/RAM Price Index Crawler</p>
                <p>Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        </div>
    </body>
    </html>
    """
    return html


if __name__ == "__main__":
    # Test email
    print("Testing email notification...")
    print("\nYou need to set up:")
    print("1. GMAIL_ADDRESS environment variable")
    print("2. GMAIL_APP_PASSWORD environment variable")
    print("\nSee EMAIL_SETUP_GUIDE.md for instructions")
