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
            success = 'completed successfully' in content
            
            # Extract product count
            product_count = 0
            for line in content.split('\n'):
                if 'Saved' in line and 'products to database' in line:
                    try:
                        product_count = int(line.split()[1])
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
