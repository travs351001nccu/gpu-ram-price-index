#!/usr/bin/env python3
"""
Automated Daily Crawler with Logging
Runs automatically every day at 2:00 AM
"""

import sys
import logging
from datetime import datetime
from pathlib import Path

# Setup logging
log_dir = Path(__file__).parent / 'logs'
log_dir.mkdir(exist_ok=True)

log_file = log_dir / f'crawler_{datetime.now().strftime("%Y%m%d")}.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def send_notification(title, message):
    """Send email notification"""
    import os
    
    # Print to terminal for immediate feedback
    print("\n" + "=" * 60)
    print(f"🔔 NOTIFICATION: {title}")
    print(f"   {message}")
    print("=" * 60 + "\n")
    
    # Try to send email
    try:
        from email_notifier import send_email_notification, create_success_email, create_failure_email
        
        to_email = os.getenv('NOTIFICATION_EMAIL', 'cjtravispaysub@gmail.com')
        
        # Parse message to get product count and time
        if "Collected" in message and "products" in message:
            # Success email
            parts = message.split()
            product_count = int(parts[1]) if len(parts) > 1 else 0
            time_str = parts[-1].replace('s', '')
            elapsed = float(time_str) if time_str.replace('.', '').isdigit() else 0
            
            body = create_success_email(product_count, elapsed)
            subject = f"✅ Crawler Success - {datetime.now().strftime('%b %d, %Y')}"
        else:
            # Failure email
            body = create_failure_email(message)
            subject = f"❌ Crawler Failed - {datetime.now().strftime('%b %d, %Y')}"
        
        if send_email_notification(subject, body, to_email):
            logger.info(f"Email sent to {to_email}")
        else:
            logger.warning("Email not configured - check EMAIL_SETUP_GUIDE.md")
            
    except Exception as e:
        logger.warning(f"Could not send email: {e}")
        logger.info("Email notifications not configured - see EMAIL_SETUP_GUIDE.md")

def main():
    """Main execution with error handling"""
    start_time = datetime.now()
    logger.info("=" * 60)
    logger.info("Starting daily crawler")
    logger.info("=" * 60)
    
    try:
        # Import and run the main crawler
        from run_crawler import main as run_main_crawler
        
        # Run crawler normally (don't capture output)
        run_main_crawler()
        
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"Crawler completed successfully in {elapsed:.2f} seconds")
        
        # Get product count from database
        product_count = 0
        try:
            import psycopg2
            from db_config import config
            conn = psycopg2.connect(**config.get_psycopg2_params())
            cur = conn.cursor()
            cur.execute("SELECT SUM(product_count) FROM daily_index WHERE date = CURRENT_DATE")
            result = cur.fetchone()
            product_count = int(result[0]) if result and result[0] else 0
            cur.close()
            conn.close()
        except Exception as e:
            logger.warning(f"Could not get product count: {e}")
        
        # Send success notification
        send_notification(
            "✅ Crawler Success",
            f"Collected {product_count} products in {elapsed:.1f}s"
        )
        
        return 0
        
    except ImportError as e:
        logger.error(f"Import error: {e}")
        logger.error("Make sure run_crawler.py is in the same directory")
        send_notification("❌ Crawler Failed", f"Import error: {str(e)[:40]}")
        return 1
        
    except Exception as e:
        logger.error(f"Crawler failed: {e}")
        logger.exception("Full error trace:")
        send_notification("❌ Crawler Failed", f"Error: {str(e)[:50]}")
        return 1
        
    finally:
        logger.info("=" * 60)
        logger.info(f"Log saved to: {log_file}")
        logger.info("=" * 60)

if __name__ == "__main__":
    sys.exit(main())
