# GPU/RAM Price Index - Usage Guide

## Quick Start

### View Current Prices
```bash
python3 query_data.py
```
Shows latest price index for all GPU/RAM categories.

### Run Crawler Manually
```bash
python3 daily_crawler.py
```
Fetches today's prices from coolpc.com.tw and saves to database.

### Check System Status
```bash
./check_status.sh
```
Shows database stats, recent logs, and latest market index.

---

## Automation Setup

### Install Daily Cron Job (runs at 2:00 AM)
```bash
crontab cron_setup.txt
```

### Verify Cron Job
```bash
crontab -l
```

### Remove Cron Job
```bash
crontab -r
```

---

## Database Info

**Database Name**: `price_index`  
**Tables**:
- `products` - Product catalog
- `daily_prices` - Time-series pricing data
- `daily_index` - Aggregated market indices
- `data_quality_log` - Validation tracking

### Direct Database Access
```bash
psql price_index
```

### Backup Database
```bash
pg_dump price_index > backup_$(date +%Y%m%d).sql
```

---

## Files

- `run_crawler.py` - Main scraper (fetch, classify, save)
- `daily_crawler.py` - Automated wrapper with logging
- `db_config.py` - Database configuration
- `query_data.py` - Data query helper
- `product_taxonomy.json` - Classification rules (32 GPU + RAM)
- `cron_setup.txt` - Cron job configuration
- `check_status.sh` - Monitoring script
- `logs/` - Execution logs

---

## Troubleshooting

### PostgreSQL not running
```bash
brew services start postgresql@15
```

### Check recent logs
```bash
tail -f logs/crawler_$(date +%Y%m%d).log
```

### Test database connection
```bash
python3 -c "from db_config import config; import psycopg2; conn = psycopg2.connect(**config.get_psycopg2_params()); print('Connected'); conn.close()"
```

---

**Project**: Consumer Electronics Price Index  
**Data Source**: coolpc.com.tw  
**Target**: 30-day price collection (6,000+ records)
