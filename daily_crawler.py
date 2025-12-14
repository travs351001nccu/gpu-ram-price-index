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


def generate_price_change_summary():
    """Generate summary of price changes compared to yesterday"""
    import psycopg2
    from db_config import config
    
    summary = {
        'new_products': [],
        'price_increases': [],
        'price_decreases': [],
        'discontinued': [],
        'total_products': 0,
        'summary_text': ''
    }
    
    try:
        conn = psycopg2.connect(**config.get_psycopg2_params())
        cur = conn.cursor()
        
        # Get new products (first_seen = today)
        cur.execute("""
            SELECT p.product_name, dp.price, p.category
            FROM products p
            JOIN daily_prices dp ON p.product_id = dp.product_id
            WHERE p.first_seen = CURRENT_DATE AND dp.date = CURRENT_DATE
            ORDER BY p.category, dp.price DESC
            LIMIT 10
        """)
        summary['new_products'] = [
            {'name': row[0], 'price': float(row[1]), 'category': row[2]}
            for row in cur.fetchall()
        ]
        
        # Get price changes (compare today vs previous available date)
        cur.execute("""
            WITH today AS (
                SELECT product_id, price::numeric FROM daily_prices WHERE date = CURRENT_DATE
            ),
            prev_date AS (
                SELECT MAX(date) as prev_date FROM daily_prices WHERE date < CURRENT_DATE
            ),
            previous AS (
                SELECT dp.product_id, dp.price::numeric as price
                FROM daily_prices dp, prev_date pd
                WHERE dp.date = pd.prev_date
            )
            SELECT 
                p.product_name,
                prev.price as old_price,
                t.price as new_price,
                ((t.price - prev.price) / prev.price * 100) as change_pct,
                p.category
            FROM today t
            JOIN previous prev ON t.product_id = prev.product_id
            JOIN products p ON t.product_id = p.product_id
            WHERE ABS(t.price - prev.price) / prev.price > 0.005  -- 0.5% threshold
            ORDER BY change_pct DESC
        """)
        
        for row in cur.fetchall():
            change_data = {
                'name': row[0],
                'old_price': float(row[1]),
                'new_price': float(row[2]),
                'change_pct': float(row[3]),
                'category': row[4]
            }
            if row[3] > 0:
                summary['price_increases'].append(change_data)
            else:
                summary['price_decreases'].append(change_data)
        
        # Get discontinued (seen yesterday, not today)
        cur.execute("""
            SELECT p.product_name, dp.price, p.category
            FROM products p
            JOIN daily_prices dp ON p.product_id = dp.product_id
            WHERE dp.date = CURRENT_DATE - INTERVAL '1 day'
            AND p.product_id NOT IN (
                SELECT product_id FROM daily_prices WHERE date = CURRENT_DATE
            )
            LIMIT 10
        """)
        summary['discontinued'] = [
            {'name': row[0], 'last_price': float(row[1]), 'category': row[2]}
            for row in cur.fetchall()
        ]
        
        # Get total count
        cur.execute("SELECT COUNT(*) FROM daily_prices WHERE date = CURRENT_DATE")
        summary['total_products'] = cur.fetchone()[0]
        
        cur.close()
        conn.close()
        
        # Generate summary text
        lines = []
        lines.append("=" * 60)
        lines.append(f"📊 DAILY PRICE CHANGE SUMMARY - {datetime.now().strftime('%Y-%m-%d')}")
        lines.append("=" * 60)
        
        if summary['new_products']:
            lines.append(f"\n🆕 NEW PRODUCTS ({len(summary['new_products'])}):")
            for p in summary['new_products'][:5]:
                lines.append(f"  • {p['name'][:40]} - ${int(p['price']):,} ({p['category']})")
        
        if summary['price_increases']:
            lines.append(f"\n📈 PRICE INCREASES ({len(summary['price_increases'])}):")
            for p in summary['price_increases'][:5]:
                lines.append(f"  • {p['name'][:30]}: ${int(p['old_price']):,} → ${int(p['new_price']):,} (+{p['change_pct']:.1f}%)")
        
        if summary['price_decreases']:
            lines.append(f"\n📉 PRICE DECREASES ({len(summary['price_decreases'])}):")
            for p in sorted(summary['price_decreases'], key=lambda x: x['change_pct'])[:5]:
                lines.append(f"  • {p['name'][:30]}: ${int(p['old_price']):,} → ${int(p['new_price']):,} ({p['change_pct']:.1f}%)")
        
        if summary['discontinued']:
            lines.append(f"\n❌ DISCONTINUED ({len(summary['discontinued'])}):")
            for p in summary['discontinued'][:3]:
                lines.append(f"  • {p['name'][:40]} (not seen today)")
        
        lines.append(f"\n📊 MARKET SUMMARY:")
        lines.append(f"  • Total products: {summary['total_products']}")
        lines.append(f"  • Price increases: {len(summary['price_increases'])} | Decreases: {len(summary['price_decreases'])}")
        lines.append("=" * 60)
        
        summary['summary_text'] = '\n'.join(lines)
        
    except Exception as e:
        logger.warning(f"Could not generate price change summary: {e}")
        summary['summary_text'] = f"Could not generate summary: {e}"
    
    return summary

def send_notification(title, message, price_changes=None):
    """Send email notification"""
    import os
    
    # Print to terminal for immediate feedback
    print("\n" + "=" * 60)
    print(f"NOTIFICATION: {title}")
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
            # Find the time value (format: X.Xs)
            time_str = None
            for part in parts:
                if part.endswith('s') and part[:-1].replace('.', '').isdigit():
                    time_str = part.replace('s', '')
                    break
            elapsed = float(time_str) if time_str else 0
            
            # Get price summary from database (like dashboard)
            price_summary = []
            weekly_changes = []
            try:
                import psycopg2
                from db_config import config
                conn = psycopg2.connect(**config.get_psycopg2_params())
                cur = conn.cursor()
                
                # Get price summary
                cur.execute("""
                    SELECT 
                        category,
                        generation,
                        AVG(price) as avg_price,
                        MIN(price) as min_price,
                        MAX(price) as max_price,
                        COUNT(*) as count
                    FROM daily_prices dp
                    JOIN products p ON dp.product_id = p.product_id
                    WHERE dp.date = CURRENT_DATE
                    GROUP BY category, generation
                    ORDER BY category, avg_price DESC
                """)
                for row in cur.fetchall():
                    price_summary.append({
                        'category': row[0],
                        'generation': row[1],
                        'avg_price': float(row[2]),
                        'min_price': float(row[3]),
                        'max_price': float(row[4]),
                        'count': row[5]
                    })
                
                # Get 7-day price changes with source and date
                cur.execute("""
                    WITH daily_data AS (
                        SELECT 
                            dp.product_id,
                            dp.date,
                            dp.price::numeric,
                            dp.source,
                            LAG(dp.price::numeric) OVER (PARTITION BY dp.product_id ORDER BY dp.date) as prev_price,
                            LAG(dp.date) OVER (PARTITION BY dp.product_id ORDER BY dp.date) as prev_date
                        FROM daily_prices dp
                        WHERE dp.date >= CURRENT_DATE - INTERVAL '7 days'
                    )
                    SELECT 
                        p.product_name,
                        dd.source,
                        dd.prev_date as from_date,
                        dd.date as to_date,
                        dd.prev_price as old_price,
                        dd.price as new_price,
                        ((dd.price - dd.prev_price) / dd.prev_price * 100) as change_pct
                    FROM daily_data dd
                    JOIN products p ON dd.product_id = p.product_id
                    WHERE dd.prev_price IS NOT NULL
                    AND ABS(dd.price - dd.prev_price) / dd.prev_price > 0.005
                    ORDER BY dd.date DESC, change_pct DESC
                """)
                
                for row in cur.fetchall():
                    weekly_changes.append({
                        'name': row[0],
                        'source': row[1],
                        'from_date': row[2].strftime('%m/%d') if row[2] else '',
                        'to_date': row[3].strftime('%m/%d') if row[3] else '',
                        'old_price': float(row[4]),
                        'new_price': float(row[5]),
                        'change_pct': float(row[6])
                    })
                
                # Get new products (first seen today)
                new_products = []
                cur.execute("""
                    SELECT p.product_name, dp.price, p.category, dp.source
                    FROM products p
                    JOIN daily_prices dp ON p.product_id = dp.product_id
                    WHERE p.first_seen = CURRENT_DATE AND dp.date = CURRENT_DATE
                    ORDER BY p.category, dp.price DESC
                    LIMIT 20
                """)
                for row in cur.fetchall():
                    new_products.append({
                        'name': row[0],
                        'price': float(row[1]),
                        'category': row[2],
                        'source': row[3]
                    })
                
                cur.close()
                conn.close()
            except Exception as e:
                logger.warning(f"Could not get price data: {e}")
                new_products = []
            
            body = create_success_email(product_count, elapsed, price_changes=price_changes, price_summary=price_summary, weekly_changes=weekly_changes, new_products=new_products)
            subject = f"GPU/RAM Price Watch - {datetime.now().strftime('%b %d, %Y')}"
        else:
            # Failure email
            body = create_failure_email(message)
            subject = f"Crawler Failed - {datetime.now().strftime('%b %d, %Y')}"
        
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
        
        # Generate and log price change summary
        logger.info("")
        summary = generate_price_change_summary()
        for line in summary['summary_text'].split('\n'):
            logger.info(line)
        
        # Send success notification with summary info
        summary_info = ""
        if summary['new_products']:
            summary_info += f" | {len(summary['new_products'])} new"
        if summary['price_increases']:
            summary_info += f" | {len(summary['price_increases'])} ↑"
        if summary['price_decreases']:
            summary_info += f" | {len(summary['price_decreases'])} ↓"
        
        send_notification(
            "✅ Crawler Success",
            f"Collected {product_count} products in {elapsed:.1f}s{summary_info}",
            price_changes=summary
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
