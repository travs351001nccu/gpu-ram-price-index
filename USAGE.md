# Usage Guide

## Quick Reference

### Running the Crawler

**Manual execution:**
```bash
python3 daily_crawler.py
```

**Check status:**
```bash
# View today's log
cat logs/crawler_$(date +%Y%m%d).log

# Check cron schedule
crontab -l

# Verify power schedule
pmset -g sched
```

### Querying Data

**View collected data:**
```bash
python3 query_data.py
```

**Database queries:**
```python
from db_config import get_db_connection

conn = get_db_connection()
cur = conn.cursor()

# Get latest prices
cur.execute("""
    SELECT category, generation, avg_price, product_count
    FROM daily_index
    WHERE date = CURRENT_DATE
    ORDER BY category, avg_price DESC
""")

results = cur.fetchall()
for row in results:
    print(row)
```

### Dashboard

**Start dashboard:**
```bash
python3 dashboard.py
```

**Access:**
- Local: http://localhost:5001
- Network: http://[your-ip]:5001

**Stop dashboard:**
```bash
pkill -f dashboard.py
```

## Automation

### Cron Job

The crawler runs automatically at 2:00 AM daily via cron.

**View cron configuration:**
```bash
crontab -l
```

**Modify schedule:**
```bash
crontab -e
```

**Check execution:**
```bash
# View cron mail for errors
tail /var/mail/$USER

# Check logs
ls -lh logs/
```

### Power Schedule

macOS wakes at 1:55 AM and sleeps at 3:00 AM daily.

**Verify schedule:**
```bash
pmset -g sched
```

**Modify schedule:**
```bash
# Wake time
sudo pmset repeat wake MTWRFSU 01:55:00

# Sleep time
sudo pmset repeat sleep MTWRFSU 03:00:00
```

## Data Export

### Export to CSV

```python
import pandas as pd
from db_config import get_db_connection

conn = get_db_connection()

# Export daily index
df = pd.read_sql("SELECT * FROM daily_index ORDER BY date, category", conn)
df.to_csv('price_index.csv', index=False)

# Export price details
df = pd.read_sql("""
    SELECT p.category, p.generation, p.product_name, dp.date, dp.price
    FROM products p
    JOIN daily_prices dp ON p.product_id = dp.product_id
    ORDER BY dp.date, p.category
""", conn)
df.to_csv('price_details.csv', index=False)
```

### Export for Analysis

```python
# Get data for correlation analysis
df = pd.read_sql("""
    SELECT 
        date,
        category,
        generation,
        avg_price,
        product_count,
        volatility
    FROM daily_index
    WHERE date >= CURRENT_DATE - INTERVAL '30 days'
    ORDER BY date, category, generation
""", conn)

# Save for analysis
df.to_csv('analysis_data.csv', index=False)
```

## Troubleshooting

### Crawler Issues

**Check logs:**
```bash
cat logs/crawler_$(date +%Y%m%d).log
```

**Test manually:**
```bash
python3 daily_crawler.py
```

**Verify database connection:**
```bash
python3 -c "from db_config import get_db_connection; conn = get_db_connection(); print('Connected')"
```

### Dashboard Issues

**Check if running:**
```bash
lsof -i :5001
```

**View errors:**
```bash
python3 dashboard.py
```

**Restart:**
```bash
pkill -f dashboard.py
python3 dashboard.py
```

### Database Issues

**Check connection:**
```bash
psql -d price_index -c "SELECT COUNT(*) FROM daily_index"
```

**View tables:**
```bash
psql -d price_index -c "\dt"
```

**Check recent data:**
```bash
psql -d price_index -c "SELECT date, COUNT(*) FROM daily_index GROUP BY date ORDER BY date DESC LIMIT 7"
```

## Maintenance

### Log Rotation

Logs are stored in `logs/crawler_YYYYMMDD.log` format.

**Clean old logs:**
```bash
# Keep last 60 days
find logs -name "crawler_*.log" -mtime +60 -delete
```

### Database Maintenance

**Vacuum database:**
```bash
psql -d price_index -c "VACUUM ANALYZE"
```

**Check database size:**
```bash
psql -d price_index -c "SELECT pg_size_pretty(pg_database_size('price_index'))"
```

## Email Notifications

Emails are sent after each crawler run.

**Test email:**
```python
from email_notifier import send_email_notification, create_success_email

body = create_success_email(500, 4.2)
send_email_notification('Test Email', body, 'your@email.com')
```

**Configure:**
Set environment variables in `~/.zshrc`:
```bash
export GMAIL_ADDRESS="your@gmail.com"
export GMAIL_APP_PASSWORD="your-app-password"
export NOTIFICATION_EMAIL="recipient@gmail.com"
```

## Performance

### Expected Metrics

- Execution time: 4-6 seconds
- Products collected: 400-600 per run
- Database size: ~50MB per month
- Memory usage: <100MB

### Monitoring

**Check execution time:**
```bash
grep "completed successfully" logs/crawler_$(date +%Y%m%d).log
```

**Check product count:**
```bash
grep "Saved.*products" logs/crawler_$(date +%Y%m%d).log
```

**Database growth:**
```bash
psql -d price_index -c "SELECT COUNT(*) FROM daily_prices"
```
