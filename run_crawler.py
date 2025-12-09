"""
Consumer Electronics Price Index - Main Crawler
Simplified all-in-one version for daily execution
Author: Travis Cua
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import re
import json
from pathlib import Path
import psycopg2
from psycopg2.extras import Json
from db_config import config

def load_taxonomy():
    """Load product taxonomy"""
    with open('product_taxonomy.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def fetch_coolpc_data():
    """Fetch data from Coolpc"""
    url = "https://www.coolpc.com.tw/evaluate.php"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    print(" Fetching data from Coolpc...")
    res = requests.get(url, headers=headers, timeout=30)
    res.encoding = 'big5'
    soup = BeautifulSoup(res.text, 'html.parser')
    
    all_products = []
    for select in soup.find_all('select'):
        for group in select.find_all('optgroup'):
            category = group.get('label', '')
            for opt in group.find_all('option'):
                raw_text = opt.text.strip()
                if not raw_text or raw_text.startswith("---"):
                    continue
                
                price_match = re.search(r'\$\s*(\d+)', raw_text)
                if price_match:
                    all_products.append({
                        '原始分類': category,
                        '商品名稱': raw_text.split('$')[0].strip().rstrip(','),
                        '價格': int(price_match.group(1)),
                        '完整資訊': raw_text
                    })
    
    print(f" Fetched {len(all_products):,} products")
    return pd.DataFrame(all_products)

def classify_products(df, taxonomy):
    """Classify products using taxonomy"""
    print("  Classifying products...")
    
    classified = []
    global_exclusions = [kw.lower() for kw in taxonomy.get('global_exclusions', {}).get('keywords', [])]
    
    for _, row in df.iterrows():
        product_lower = row['商品名稱'].lower()
        
        # Global exclusions
        if any(ex in product_lower for ex in global_exclusions):
            continue
        
        # Match categories
        for cat_name, cat_config in taxonomy['categories'].items():
            if not any(kw in row['原始分類'].lower() for kw in cat_config.get('category_keywords', [])):
                continue
            
            if any(ex.lower() in product_lower for ex in cat_config.get('exclude_keywords', [])):
                continue
            
            # Match generations
            for gen_name, gen_config in cat_config.get('generations', {}).items():
                matched = False
                
                if 'models' in gen_config:
                    if any(model.lower() in product_lower for model in gen_config['models']):
                        matched = True
                
                if 'capacities' in gen_config:
                    for capacity, keywords in gen_config['capacities'].items():
                        if any(kw.lower() in product_lower for kw in keywords):
                            matched = True
                            break
                
                if matched:
                    price_range = gen_config.get('price_range', [0, 999999])
                    if price_range[0] <= row['價格'] <= price_range[1]:
                        classified.append({
                            '類別': cat_name,
                            '世代': gen_name,
                            '商品名稱': row['商品名稱'],
                            '價格': row['價格'],
                            '原始分類': row['原始分類'],
                            '完整資訊': row['完整資訊']
                        })
                    break
            break
    
    print(f" Classified {len(classified):,} products")
    return pd.DataFrame(classified)

def save_to_database(df):
    """Save to PostgreSQL"""
    try:
        conn = psycopg2.connect(**config.get_psycopg2_params())
        cursor = conn.cursor()
        today = datetime.now().date()
        new_products = 0
        
        print(" Saving to database...")
        
        for _, row in df.iterrows():
            brand = row['商品名稱'].split()[0] if row['商品名稱'] else None
            
            # Insert/update product
            cursor.execute("""
                INSERT INTO products (category, generation, product_name, brand, first_seen, last_seen)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (product_name, generation) 
                DO UPDATE SET last_seen = EXCLUDED.last_seen, is_active = TRUE
                RETURNING product_id
            """, (row['類別'], row['世代'], row['商品名稱'], brand, today, today))
            
            product_id = cursor.fetchone()[0]
            
            # Insert price
            cursor.execute("""
                INSERT INTO daily_prices (date, product_id, price, raw_info)
                VALUES (%s, %s, %s, %s)
ON CONFLICT (date, product_id) DO UPDATE SET price = EXCLUDED.price
            """, (today, product_id, row['價格'], Json({'完整資訊': row['完整資訊']})))
            
            new_products += 1
        
        # Generate index
        cursor.execute("""
            INSERT INTO daily_index (date, category, generation, avg_price, min_price, max_price, median_price, std_price, product_count, volatility)
            SELECT 
                %s, category, generation,
                AVG(price)::numeric(10,2), MIN(price), MAX(price), 
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price)::numeric(10,2),
                STDDEV(price)::numeric(10,2), COUNT(*),
                (STDDEV(price) / AVG(price) * 100)::numeric(5,2)
            FROM (
                SELECT p.category, p.generation, dp.price
                FROM products p
                JOIN daily_prices dp ON p.product_id = dp.product_id
                WHERE dp.date = %s
            ) sub
            GROUP BY category, generation
            ON CONFLICT (date, category, generation) DO UPDATE 
            SET avg_price = EXCLUDED.avg_price, min_price = EXCLUDED.min_price
        """, (today, today))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f" Saved {new_products} products to database")
        return True
        
    except Exception as e:
        print(f" Database error: {e}")
        return False

def main():
    """Main execution"""
    print("=" * 60)
    print(" Consumer Electronics Price Index Crawler")
    print("=" * 60)
    
    # Load taxonomy
    taxonomy = load_taxonomy()
    
    # Fetch data
    raw_df = fetch_coolpc_data()
    if raw_df.empty:
        print(" No data fetched")
        return
    
    # Classify
    classified_df = classify_products(raw_df, taxonomy)
    if classified_df.empty:
        print("  No products matched taxonomy")
        return
    
    # Save to database
    save_to_database(classified_df)
    
    # Display summary
    summary = classified_df.groupby(['類別', '世代']).agg({'價格': ['mean', 'min', 'max', 'count']}).round(0)
    summary.columns = ['平均價格', '最低價格', '最高價格', '商品數']
    
    print("\n Today's Market Index:")
    print(summary.to_string())
    
    print("\n Crawler completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    main()
