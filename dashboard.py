#!/usr/bin/env python3
"""
Web Dashboard for GPU/RAM Price Index
View collected data in a beautiful web interface
"""

from flask import Flask, render_template, jsonify
import psycopg2
from datetime import datetime, timedelta
import json
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from db_config import get_db_connection

app = Flask(__name__)


def get_latest_data():
    """Get latest price data from database"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    query = """
    SELECT 
        category,
        generation,
        avg_price,
        min_price,
        max_price,
        product_count,
        date as last_updated
    FROM daily_index
    WHERE date = (SELECT MAX(date) FROM daily_index)
    ORDER BY category, avg_price DESC
    """
    
    cur.execute(query)
    results = cur.fetchall()
    
    data = []
    for row in results:
        data.append({
            'category': row[0],
            'generation': row[1],
            'avg_price': float(row[2]),
            'min_price': float(row[3]),
            'max_price': float(row[4]),
            'count': row[5],
            'last_updated': row[6].strftime('%Y-%m-%d %H:%M:%S')
        })
    
    cur.close()
    conn.close()
    
    return data


def get_historical_data(days=7):
    """Get historical price trends"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    query = """
    SELECT 
        date,
        category,
        generation,
        avg_price,
        product_count as count
    FROM daily_index
    WHERE date >= CURRENT_DATE - INTERVAL '%s days'
    ORDER BY date DESC, category, generation
    """
    
    cur.execute(query, (days,))
    results = cur.fetchall()
    
    data = []
    for row in results:
        data.append({
            'date': row[0].strftime('%Y-%m-%d'),
            'category': row[1],
            'generation': row[2],
            'avg_price': float(row[3]),
            'count': row[4]
        })
    
    cur.close()
    conn.close()
    
    return data


def get_stats():
    """Get overall statistics"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Total records (sum of all product counts)
    cur.execute("SELECT SUM(product_count) FROM daily_index")
    total_records = cur.fetchone()[0] or 0
    
    # Records today
    cur.execute("SELECT SUM(product_count) FROM daily_index WHERE date = CURRENT_DATE")
    today_records = cur.fetchone()[0] or 0
    
    # Unique products
    cur.execute("SELECT COUNT(DISTINCT generation) FROM daily_index")
    unique_products = cur.fetchone()[0]
    
    # Date range
    cur.execute("SELECT MIN(date), MAX(date) FROM daily_index")
    date_range = cur.fetchone()
    
    cur.close()
    conn.close()
    
    return {
        'total_records': int(total_records),
        'today_records': int(today_records),
        'unique_products': unique_products,
        'start_date': date_range[0].strftime('%Y-%m-%d') if date_range[0] else 'N/A',
        'end_date': date_range[1].strftime('%Y-%m-%d') if date_range[1] else 'N/A'
    }


def get_recent_logs(limit=10):
    """Get recent log entries"""
    log_dir = Path(__file__).parent / 'logs'
    logs = []
    
    for log_file in sorted(log_dir.glob('crawler_*.log'), reverse=True)[:limit]:
        try:
            with open(log_file, 'r') as f:
                content = f.read()
            
            # Extract key info
            date = log_file.stem.replace('crawler_', '')
            success = 'completed successfully' in content or 'Crawler Success' in content
            
            # Extract product count - try multiple patterns
            product_count = 0
            for line in content.split('\n'):
                # Try "Collected X products" format (from notification)
                if 'Collected' in line and 'products' in line:
                    import re
                    match = re.search(r'Collected (\d+) products', line)
                    if match:
                        product_count = max(product_count, int(match.group(1)))
                # Try "Saved X products" format (old format)
                elif 'Saved' in line and 'products to database' in line:
                    try:
                        parts = line.split()
                        for i, p in enumerate(parts):
                            if p == 'Saved' and i+1 < len(parts):
                                product_count = max(product_count, int(parts[i+1]))
                    except:
                        pass
            
            logs.append({
                'date': f"{date[:4]}-{date[4:6]}-{date[6:8]}",
                'success': success,
                'product_count': product_count,
                'file': log_file.name
            })
        except:
            pass
    
    return logs


@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')


@app.route('/api/latest')
def api_latest():
    """API endpoint for latest data"""
    return jsonify(get_latest_data())


@app.route('/api/historical/<int:days>')
def api_historical(days):
    """API endpoint for historical data"""
    return jsonify(get_historical_data(days))


@app.route('/api/stats')
def api_stats():
    """API endpoint for statistics"""
    return jsonify(get_stats())


@app.route('/api/logs')
def api_logs():
    """API endpoint for recent logs"""
    return jsonify(get_recent_logs())


@app.route('/api/products/<generation>')
def api_products(generation):
    """Get all products for a generation with today vs yesterday price"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Get products with today's and yesterday's prices
    query = """
    WITH today_prices AS (
        SELECT p.product_id, p.product_name, p.brand, dp.price as today_price, COALESCE(p.source, 'Coolpc') as source
        FROM products p
        JOIN daily_prices dp ON p.product_id = dp.product_id
        WHERE p.generation = %s AND dp.date = CURRENT_DATE
    ),
    yesterday_prices AS (
        SELECT p.product_id, dp.price as yesterday_price
        FROM products p
        JOIN daily_prices dp ON p.product_id = dp.product_id
        WHERE p.generation = %s AND dp.date = CURRENT_DATE - INTERVAL '1 day'
    )
    SELECT 
        t.product_id,
        t.product_name,
        t.brand,
        t.today_price,
        COALESCE(y.yesterday_price, t.today_price) as yesterday_price,
        t.source
    FROM today_prices t
    LEFT JOIN yesterday_prices y ON t.product_id = y.product_id
    ORDER BY t.source, t.today_price DESC
    """
    
    cur.execute(query, (generation, generation))
    results = cur.fetchall()
    
    products = []
    for row in results:
        today_price = float(row[3])
        yesterday_price = float(row[4])
        change = 0
        if yesterday_price > 0:
            change = ((today_price - yesterday_price) / yesterday_price) * 100
        
        products.append({
            'product_id': row[0],
            'product_name': row[1],
            'brand': row[2],
            'today_price': today_price,
            'yesterday_price': yesterday_price,
            'change_percent': round(change, 2),
            'source': row[5]
        })
    
    cur.close()
    conn.close()
    
    return jsonify(products)


@app.route('/api/product/<int:product_id>/history')
def api_product_history(product_id):
    """Get price history for a specific product"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Get product info
    cur.execute("""
        SELECT product_name, brand, category, generation, first_seen
        FROM products
        WHERE product_id = %s
    """, (product_id,))
    
    product_info = cur.fetchone()
    if not product_info:
        return jsonify({'error': 'Product not found'}), 404
    
    # Get price history (last 30 days)
    cur.execute("""
        SELECT date, price
        FROM daily_prices
        WHERE product_id = %s
        ORDER BY date DESC
        LIMIT 30
    """, (product_id,))
    
    history = cur.fetchall()
    
    # Calculate stats
    prices = [float(h[1]) for h in history]
    
    cur.close()
    conn.close()
    
    return jsonify({
        'product_id': product_id,
        'product_name': product_info[0],
        'brand': product_info[1],
        'category': product_info[2],
        'generation': product_info[3],
        'first_seen': product_info[4].strftime('%Y-%m-%d') if product_info[4] else None,
        'history': [
            {'date': h[0].strftime('%Y-%m-%d'), 'price': float(h[1])}
            for h in reversed(history)
        ],
        'stats': {
            'min_price': min(prices) if prices else 0,
            'max_price': max(prices) if prices else 0,
            'current_price': prices[0] if prices else 0,
            'days_tracked': len(prices)
        }
    })


@app.route('/api/comparison')
def api_comparison():
    """Get cross-source price comparison"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    query = """
    WITH source_prices AS (
        SELECT 
            p.category,
            p.generation,
            COALESCE(p.source, 'Coolpc') as source,
            ROUND(AVG(dp.price)::numeric, 0) as avg_price,
            MIN(dp.price) as min_price,
            COUNT(*) as product_count
        FROM products p
        JOIN daily_prices dp ON p.product_id = dp.product_id
        WHERE dp.date = CURRENT_DATE
        GROUP BY p.category, p.generation, p.source
    ),
    all_generations AS (
        SELECT DISTINCT category, generation FROM source_prices
    )
    SELECT 
        ag.category,
        ag.generation,
        c.avg_price as coolpc_avg,
        c.min_price as coolpc_min,
        COALESCE(c.product_count, 0) as coolpc_count,
        p.avg_price as pchome_avg,
        p.min_price as pchome_min,
        COALESCE(p.product_count, 0) as pchome_count,
        CASE 
            WHEN c.avg_price > 0 AND p.avg_price > 0 
            THEN ROUND(p.avg_price - c.avg_price) 
            ELSE NULL 
        END as price_diff,
        CASE 
            WHEN c.min_price IS NOT NULL AND p.min_price IS NOT NULL
            THEN CASE WHEN c.min_price < p.min_price THEN 'Coolpc' ELSE 'PChome' END
            WHEN c.min_price IS NOT NULL THEN 'Coolpc'
            WHEN p.min_price IS NOT NULL THEN 'PChome'
            ELSE NULL
        END as cheaper
    FROM all_generations ag
    LEFT JOIN source_prices c ON ag.category = c.category AND ag.generation = c.generation AND c.source = 'Coolpc'
    LEFT JOIN source_prices p ON ag.category = p.category AND ag.generation = p.generation AND p.source = 'PChome'
    WHERE c.avg_price IS NOT NULL OR p.avg_price IS NOT NULL
    ORDER BY ag.category, ag.generation
    """
    
    cur.execute(query)
    results = cur.fetchall()
    
    comparison = []
    for row in results:
        comparison.append({
            'category': row[0],
            'generation': row[1],
            'coolpc': {
                'avg': float(row[2]) if row[2] else None,
                'min': float(row[3]) if row[3] else None,
                'count': row[4] if row[4] else 0
            },
            'pchome': {
                'avg': float(row[5]) if row[5] else None,
                'min': float(row[6]) if row[6] else None,
                'count': row[7] if row[7] else 0
            },
            'price_diff': float(row[8]) if row[8] else None,
            'cheaper': row[9]
        })
    
    cur.close()
    conn.close()
    
    return jsonify(comparison)


@app.route('/api/weekly-changes')
def api_weekly_changes():
    """Get 7-day price changes for all products"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    query = """
    WITH daily_data AS (
        SELECT 
            dp.product_id,
            dp.date,
            dp.price::numeric,
            COALESCE(dp.source, 'Coolpc') as source,
            LAG(dp.price::numeric) OVER (PARTITION BY dp.product_id ORDER BY dp.date) as prev_price,
            LAG(dp.date) OVER (PARTITION BY dp.product_id ORDER BY dp.date) as prev_date
        FROM daily_prices dp
        WHERE dp.date >= CURRENT_DATE - INTERVAL '7 days'
    )
    SELECT 
        p.product_name,
        p.category,
        p.generation,
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
    """
    
    cur.execute(query)
    results = cur.fetchall()
    
    changes = []
    for row in results:
        changes.append({
            'product_name': row[0],
            'category': row[1],
            'generation': row[2],
            'source': row[3],
            'from_date': row[4].strftime('%m/%d') if row[4] else '',
            'to_date': row[5].strftime('%m/%d') if row[5] else '',
            'old_price': float(row[6]),
            'new_price': float(row[7]),
            'change_pct': float(row[8])
        })
    
    cur.close()
    conn.close()
    
    return jsonify(changes)


if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    templates_dir = Path(__file__).parent / 'templates'
    templates_dir.mkdir(exist_ok=True)
    
    print("=" * 60)
    print("GPU/RAM Price Index Dashboard")
    print("=" * 60)
    print("Starting server at: http://localhost:5001")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5001)
