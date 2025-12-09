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

def main():
    """Main execution with error handling"""
    start_time = datetime.now()
    logger.info("=" * 60)
    logger.info("Starting daily crawler")
    logger.info("=" * 60)
    
    try:
        # Import and run the main crawler
        from run_crawler import main as run_main_crawler
        
        run_main_crawler()
        
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"Crawler completed successfully in {elapsed:.2f} seconds")
        return 0
        
    except ImportError as e:
        logger.error(f"Import error: {e}")
        logger.error("Make sure run_crawler.py is in the same directory")
        return 1
        
    except Exception as e:
        logger.error(f"Crawler failed: {e}")
        logger.exception("Full error trace:")
        return 1
        
    finally:
        logger.info("=" * 60)
        logger.info(f"Log saved to: {log_file}")
        logger.info("=" * 60)

if __name__ == "__main__":
    sys.exit(main())
