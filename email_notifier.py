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
from pathlib import Path

# Load .env file if it exists
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ.setdefault(key.strip(), value.strip())


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


def create_success_email(product_count, elapsed_time, date=None, price_changes=None, price_summary=None, weekly_changes=None, new_products=None):
    """Create HTML email for successful crawler run"""
    date = date or datetime.now().strftime('%Y-%m-%d')
    
    # Generate price summary table (like dashboard)
    summary_table_html = ""
    if price_summary:
        summary_table_html = """
            <div style="margin: 20px 0;">
                <h3 style="color: #374151; margin-bottom: 15px;">Price Summary</h3>
                <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                    <thead>
                        <tr style="background-color: #1e293b; color: white;">
                            <th style="padding: 10px; text-align: left;">Category</th>
                            <th style="padding: 10px; text-align: left;">Generation</th>
                            <th style="padding: 10px; text-align: right;">Avg Price</th>
                            <th style="padding: 10px; text-align: right;">Min</th>
                            <th style="padding: 10px; text-align: right;">Max</th>
                            <th style="padding: 10px; text-align: center;">Count</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        for item in price_summary:
            cat_color = "#22c55e" if item['category'] == 'GPU' else "#3b82f6"
            summary_table_html += f"""
                <tr style="border-bottom: 1px solid #e5e7eb;">
                    <td style="padding: 8px;"><span style="background-color: {cat_color}20; color: {cat_color}; padding: 2px 8px; border-radius: 4px; font-size: 12px;">{item['category']}</span></td>
                    <td style="padding: 8px; font-weight: 600;">{item['generation'].replace('_', ' ')}</td>
                    <td style="padding: 8px; text-align: right; color: #4ECDC4; font-weight: 600;">NT$ {int(item['avg_price']):,}</td>
                    <td style="padding: 8px; text-align: right; color: #94a3b8;">NT$ {int(item['min_price']):,}</td>
                    <td style="padding: 8px; text-align: right; color: #94a3b8;">NT$ {int(item['max_price']):,}</td>
                    <td style="padding: 8px; text-align: center;">{item['count']}</td>
                </tr>
            """
        summary_table_html += "</tbody></table></div>"
    
    # Generate weekly price changes section
    changes_html = ""
    if weekly_changes and len(weekly_changes) > 0:
        # Separate increases and decreases
        increases = [c for c in weekly_changes if c['change_pct'] > 0]
        decreases = [c for c in weekly_changes if c['change_pct'] < 0]
        
        changes_html = """
            <div style="margin: 20px 0;">
                <h3 style="color: #374151; margin-bottom: 15px;">7-Day Price Changes</h3>
        """
        
        if increases:
            changes_html += """
                <div style="background-color: #fef3c7; padding: 12px; border-radius: 6px; margin-bottom: 10px;">
                    <strong style="color: #92400e;">Price Increases:</strong>
                    <table style="width: 100%; margin-top: 8px; font-size: 13px;">
            """
            for p in increases[:15]:
                source_color = "#22c55e" if p['source'] == 'Coolpc' else "#3b82f6"
                changes_html += f"""
                    <tr>
                        <td style="padding: 4px 0;"><span style="background-color: {source_color}20; color: {source_color}; padding: 1px 6px; border-radius: 3px; font-size: 11px;">{p['source']}</span></td>
                        <td style="padding: 4px 8px; color: #92400e;">{p['name'][:35]}</td>
                        <td style="padding: 4px 0; color: #94a3b8; font-size: 11px;">{p['from_date']}-{p['to_date']}</td>
                        <td style="padding: 4px 0; text-align: right; color: #b45309;">NT${int(p['old_price']):,} → NT${int(p['new_price']):,}</td>
                        <td style="padding: 4px 0; text-align: right; color: #dc2626; font-weight: 600;">+{p['change_pct']:.1f}%</td>
                    </tr>
                """
            changes_html += "</table></div>"
        
        if decreases:
            changes_html += """
                <div style="background-color: #dbeafe; padding: 12px; border-radius: 6px; margin-bottom: 10px;">
                    <strong style="color: #1e40af;">Price Decreases:</strong>
                    <table style="width: 100%; margin-top: 8px; font-size: 13px;">
            """
            for p in sorted(decreases, key=lambda x: x['change_pct'])[:15]:
                source_color = "#22c55e" if p['source'] == 'Coolpc' else "#3b82f6"
                changes_html += f"""
                    <tr>
                        <td style="padding: 4px 0;"><span style="background-color: {source_color}20; color: {source_color}; padding: 1px 6px; border-radius: 3px; font-size: 11px;">{p['source']}</span></td>
                        <td style="padding: 4px 8px; color: #1e40af;">{p['name'][:35]}</td>
                        <td style="padding: 4px 0; color: #94a3b8; font-size: 11px;">{p['from_date']}-{p['to_date']}</td>
                        <td style="padding: 4px 0; text-align: right; color: #1d4ed8;">NT${int(p['old_price']):,} → NT${int(p['new_price']):,}</td>
                        <td style="padding: 4px 0; text-align: right; color: #16a34a; font-weight: 600;">{p['change_pct']:.1f}%</td>
                    </tr>
                """
            changes_html += "</table></div>"
        
        changes_html += "</div>"
    else:
        changes_html = """
            <div style="background-color: #f0fdf4; padding: 15px; border-radius: 6px; margin: 20px 0; text-align: center;">
                <span style="color: #065f46;">No price changes detected in the past 7 days</span>
            </div>
        """
    
    # Generate new products section
    new_products_html = ""
    if new_products and len(new_products) > 0:
        new_products_html = """
            <div style="margin: 20px 0;">
                <h3 style="color: #374151; margin-bottom: 15px;">New Products Today</h3>
                <table style="width: 100%; font-size: 13px;">
        """
        for p in new_products[:15]:
            source_color = "#22c55e" if p['source'] == 'Coolpc' else "#3b82f6"
            cat_color = "#22c55e" if p['category'] == 'GPU' else "#3b82f6"
            new_products_html += f"""
                <tr style="border-bottom: 1px solid #f3f4f6;">
                    <td style="padding: 6px 0;"><span style="background-color: {source_color}20; color: {source_color}; padding: 1px 6px; border-radius: 3px; font-size: 11px;">{p['source']}</span></td>
                    <td style="padding: 6px 0;"><span style="background-color: {cat_color}20; color: {cat_color}; padding: 1px 6px; border-radius: 3px; font-size: 11px;">{p['category']}</span></td>
                    <td style="padding: 6px 8px; color: #374151;">{p['name'][:40]}</td>
                    <td style="padding: 6px 0; text-align: right; color: #4ECDC4; font-weight: 600;">NT$ {int(p['price']):,}</td>
                </tr>
            """
        new_products_html += "</table></div>"
    
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f5f5f5;">
        <div style="max-width: 750px; margin: 0 auto; background-color: white; border-radius: 10px; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <h1 style="color: #10b981; margin-bottom: 5px;">GPU/RAM Price Watch</h1>
            <p style="color: #94a3b8; margin-top: 0;">Daily Report - {date}</p>
            
            {summary_table_html}
            
            {changes_html}
            
            {new_products_html}
            
            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb; color: #9ca3af; font-size: 12px;">
                <p style="margin: 5px 0;">Products collected: {product_count} | Execution time: {elapsed_time:.1f}s</p>
                <p style="margin: 5px 0;">Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
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
