#!/usr/bin/env python3
"""
Excel Export - Export price data to Excel files for VBA practice
"""

import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent))


def get_db_connection():
    """Get database connection"""
    import psycopg2
    from db_config import config
    return psycopg2.connect(**config.get_psycopg2_params())


def export_daily_prices(output_dir='exports'):
    """
    Export today's prices to Excel
    Sheet 1: All products with prices
    """
    conn = get_db_connection()
    
    query = """
        SELECT 
            COALESCE(p.source, 'Coolpc') as "來源",
            p.category as "類別",
            p.generation as "世代",
            p.product_name as "商品名稱",
            p.brand as "品牌",
            dp.price as "價格",
            dp.date as "日期"
        FROM products p
        JOIN daily_prices dp ON p.product_id = dp.product_id
        WHERE dp.date = CURRENT_DATE
        ORDER BY p.source, p.category, p.generation, dp.price DESC
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # Create exports directory
    Path(output_dir).mkdir(exist_ok=True)
    
    # Export to Excel
    filename = f"{output_dir}/daily_prices_{datetime.now().strftime('%Y%m%d')}.xlsx"
    df.to_excel(filename, index=False, sheet_name='今日價格')
    
    print(f"✅ Exported {len(df)} products to {filename}")
    return filename


def export_price_history(days=30, output_dir='exports'):
    """
    Export price history with trends
    Sheet 1: Daily index averages
    Sheet 2: Individual product history
    """
    conn = get_db_connection()
    
    # Query 1: Daily index averages
    query_index = f"""
        SELECT 
            date as "日期",
            category as "類別",
            generation as "世代",
            avg_price as "平均價格",
            min_price as "最低價格",
            max_price as "最高價格",
            product_count as "商品數",
            volatility as "波動率"
        FROM daily_index
        WHERE date >= CURRENT_DATE - INTERVAL '{days} days'
        ORDER BY date DESC, category, generation
    """
    df_index = pd.read_sql_query(query_index, conn)
    
    # Query 2: Price changes by product
    query_changes = """
        WITH today AS (
            SELECT product_id, price as today_price FROM daily_prices WHERE date = CURRENT_DATE
        ),
        yesterday AS (
            SELECT product_id, price as yesterday_price FROM daily_prices WHERE date = CURRENT_DATE - INTERVAL '1 day'
        ),
        week_ago AS (
            SELECT product_id, price as week_ago_price FROM daily_prices WHERE date = CURRENT_DATE - INTERVAL '7 days'
        )
        SELECT 
            COALESCE(p.source, 'Coolpc') as "來源",
            p.category as "類別",
            p.generation as "世代",
            p.product_name as "商品名稱",
            t.today_price as "今日價格",
            y.yesterday_price as "昨日價格",
            w.week_ago_price as "七天前價格",
            CASE WHEN y.yesterday_price > 0 
                THEN ROUND(((t.today_price - y.yesterday_price) / y.yesterday_price * 100)::numeric, 2)
                ELSE 0 END as "日漲跌%",
            CASE WHEN w.week_ago_price > 0 
                THEN ROUND(((t.today_price - w.week_ago_price) / w.week_ago_price * 100)::numeric, 2)
                ELSE 0 END as "週漲跌%"
        FROM products p
        JOIN today t ON p.product_id = t.product_id
        LEFT JOIN yesterday y ON p.product_id = y.product_id
        LEFT JOIN week_ago w ON p.product_id = w.product_id
        ORDER BY p.source, p.category, p.generation, t.today_price DESC
    """
    df_changes = pd.read_sql_query(query_changes, conn)
    
    conn.close()
    
    # Create exports directory
    Path(output_dir).mkdir(exist_ok=True)
    
    # Export to Excel with multiple sheets
    filename = f"{output_dir}/price_history_{datetime.now().strftime('%Y%m%d')}.xlsx"
    
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        df_index.to_excel(writer, index=False, sheet_name='每日指數')
        df_changes.to_excel(writer, index=False, sheet_name='價格變化')
    
    print(f"✅ Exported price history to {filename}")
    print(f"   - 每日指數: {len(df_index)} rows")
    print(f"   - 價格變化: {len(df_changes)} rows")
    
    return filename


def export_cross_source_comparison(output_dir='exports'):
    """
    Export cross-source price comparison (Coolpc vs PChome)
    Find similar products and compare prices
    """
    conn = get_db_connection()
    
    # Get summary by source and generation
    query = """
        SELECT 
            COALESCE(p.source, 'Coolpc') as "來源",
            p.category as "類別",
            p.generation as "世代",
            COUNT(*) as "商品數",
            ROUND(AVG(dp.price)::numeric, 0) as "平均價格",
            MIN(dp.price) as "最低價格",
            MAX(dp.price) as "最高價格"
        FROM products p
        JOIN daily_prices dp ON p.product_id = dp.product_id
        WHERE dp.date = CURRENT_DATE
        GROUP BY p.source, p.category, p.generation
        ORDER BY p.category, p.generation, p.source
    """
    df_summary = pd.read_sql_query(query, conn)
    
    # Pivot to compare sources side by side
    query_pivot = """
        WITH source_prices AS (
            SELECT 
                p.category,
                p.generation,
                COALESCE(p.source, 'Coolpc') as source,
                ROUND(AVG(dp.price)::numeric, 0) as avg_price,
                COUNT(*) as product_count
            FROM products p
            JOIN daily_prices dp ON p.product_id = dp.product_id
            WHERE dp.date = CURRENT_DATE
            GROUP BY p.category, p.generation, p.source
        )
        SELECT 
            c.category as "類別",
            c.generation as "世代",
            c.avg_price as "Coolpc平均",
            p.avg_price as "PChome平均",
            CASE WHEN c.avg_price > 0 AND p.avg_price > 0 
                THEN ROUND(p.avg_price - c.avg_price) 
                ELSE NULL END as "價差",
            CASE WHEN c.avg_price > 0 AND p.avg_price > 0 
                THEN CASE WHEN c.avg_price < p.avg_price THEN 'Coolpc' ELSE 'PChome' END
                ELSE NULL END as "較便宜"
        FROM source_prices c
        FULL JOIN source_prices p ON c.category = p.category AND c.generation = p.generation AND p.source = 'PChome'
        WHERE c.source = 'Coolpc'
        ORDER BY c.category, c.generation
    """
    df_comparison = pd.read_sql_query(query_pivot, conn)
    
    conn.close()
    
    # Create exports directory
    Path(output_dir).mkdir(exist_ok=True)
    
    # Export to Excel with multiple sheets
    filename = f"{output_dir}/cross_source_comparison_{datetime.now().strftime('%Y%m%d')}.xlsx"
    
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        df_summary.to_excel(writer, index=False, sheet_name='各來源統計')
        df_comparison.to_excel(writer, index=False, sheet_name='跨平台比較')
    
    print(f"✅ Exported cross-source comparison to {filename}")
    print(f"   - 各來源統計: {len(df_summary)} rows")
    print(f"   - 跨平台比較: {len(df_comparison)} rows")
    
    return filename


def export_all(output_dir='exports'):
    """Export all reports"""
    print("=" * 60)
    print(" Excel Export - GPU/RAM Price Index")
    print("=" * 60)
    
    files = []
    
    try:
        files.append(export_daily_prices(output_dir))
    except Exception as e:
        print(f"❌ Error exporting daily prices: {e}")
    
    try:
        files.append(export_price_history(output_dir=output_dir))
    except Exception as e:
        print(f"❌ Error exporting price history: {e}")
    
    try:
        files.append(export_cross_source_comparison(output_dir))
    except Exception as e:
        print(f"❌ Error exporting cross-source comparison: {e}")
    
    print("=" * 60)
    print(f"📁 Exported {len(files)} files to {output_dir}/")
    print("=" * 60)
    
    return files


def main():
    """Main entry point"""
    export_all()


if __name__ == "__main__":
    main()
