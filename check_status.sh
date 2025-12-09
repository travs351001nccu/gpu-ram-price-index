#!/bin/bash
# Monitoring Script for Daily Crawler
# Shows execution status and recent logs

echo "======================================================================"
echo " GPU Price Index - Crawler Status"
echo "======================================================================"
echo ""

# Check if cron job is installed
echo " Cron Job Status:"
if crontab -l 2>/dev/null | grep -q "daily_crawler.py"; then
    echo "    Cron job is installed (runs daily at 2:00 AM)"
    echo ""
    echo "   Schedule:"
    crontab -l | grep "daily_crawler.py"
else
    echo "    Cron job NOT installed"
    echo "   Run: crontab cron_setup.txt"
fi

echo ""
echo "======================================================================"
echo " Recent Logs (Last 5 days):"
echo "======================================================================"

cd "$(dirname "$0")"

if [ -d "logs" ]; then
    ls -lht logs/*.log 2>/dev/null | head -5 || echo "   No log files found"
else
    echo "   Logs directory not found"
fi

echo ""
echo "======================================================================"
echo "  Database Status:"
echo "======================================================================"

# Check PostgreSQL
if pgrep -x "postgres" > /dev/null; then
    echo "    PostgreSQL is running"
else
    echo "    PostgreSQL is NOT running"
    echo "   Start with: brew services start postgresql@15"
fi

# Check database
psql -U traviscua -d price_index -c "SELECT 
    (SELECT COUNT(*) FROM products) as products,
    (SELECT COUNT(*) FROM daily_prices) as prices,
    (SELECT COUNT(*) FROM daily_index) as indices,
    (SELECT MAX(date) FROM daily_index) as latest_date;" 2>/dev/null || echo "     Cannot connect to database"

echo ""
echo "======================================================================"
echo " Latest Market Index:"
echo "======================================================================"

psql -U traviscua -d price_index -c "
SELECT 
    category as \"類別\",
    generation as \"世代\",
    avg_price as \"平均價格\",
    min_price as \"最低\",
    max_price as \"最高\",
    product_count as \"商品數\",
    volatility as \"波動率%\"
FROM daily_index 
WHERE date = (SELECT MAX(date) FROM daily_index)
ORDER BY category, avg_price DESC
LIMIT 10;" 2>/dev/null

echo ""
echo "======================================================================"
echo " Useful Commands:"
echo "======================================================================"
echo "   View latest log:     tail -f logs/crawler_\$(date +%Y%m%d).log"
echo "   Run crawler now:     python3 daily_crawler.py"
echo "   Query data:          python3 query_data.py"
echo "   Check cron:          crontab -l"
echo "   Remove cron:         crontab -r"
echo "======================================================================"
