"""
Query Helper - View database data
"""

import psycopg2
import pandas as pd
from db_config import config

def query_latest_index():
    """Get latest price index"""
    conn = psycopg2.connect(**config.get_psycopg2_params())
    
    query = """
        SELECT category, generation, avg_price, min_price, max_price, product_count, volatility
        FROM daily_index
        WHERE date = (SELECT MAX(date) FROM daily_index)
        ORDER BY category, generation
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    return df

def query_price_history(generation, days=30):
    """Get price history for a generation"""
    conn = psycopg2.connect(**config.get_psycopg2_params())
    
    query = """
        SELECT date, avg_price, min_price, max_price, product_count
        FROM daily_index
        WHERE generation = %s
        ORDER by date DESC
        LIMIT %s
    """
    
    df = pd.read_sql_query(query, conn, params=(generation, days))
    conn.close()
    
    return df

def main():
    """Display latest data"""
    print("=" * 60)
    print(" Latest Price Index")
    print("=" * 60)
    
    latest = query_latest_index()
    print(latest.to_string(index=False))
    
    print("\n" + "=" * 60)
    print(" Query Example: RTX 5090 History")
    print("=" * 60)
    
    history = query_price_history('NVIDIA_RTX_5090', days=10)
    if not history.empty:
        print(history.to_string(index=False))
    else:
        print("No data yet (need more days)")

if __name__ == "__main__":
    main()
