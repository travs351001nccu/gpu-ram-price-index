#!/usr/bin/env python3
"""
PChome 24h Crawler - Fetches GPU/RAM prices from PChome search API
"""

import requests
import json
import time
import re
from datetime import datetime
from pathlib import Path


# PChome search keywords for each generation
PCHOME_SEARCH_KEYWORDS = {
    'GPU': {
        # RTX 50 Series
        'NVIDIA_RTX_5090': ['RTX5090', 'RTX 5090'],
        'NVIDIA_RTX_5080': ['RTX5080', 'RTX 5080'],
        'NVIDIA_RTX_5070_Ti': ['RTX5070Ti', 'RTX 5070 Ti'],
        'NVIDIA_RTX_5070': ['RTX5070', 'RTX 5070'],
        'NVIDIA_RTX_5060_Ti': ['RTX5060Ti', 'RTX 5060 Ti'],
        'NVIDIA_RTX_5060': ['RTX5060', 'RTX 5060'],
    },
    'RAM': {
        'DDR5': ['DDR5 記憶體', 'DDR5 桌上型'],
        'DDR4': ['DDR4 記憶體', 'DDR4 桌上型'],
    }
}

# Exclusion keywords (laptops, PCs, etc.)
EXCLUDE_KEYWORDS = [
    '筆電', '筆記', 'NB', 'Laptop', 'Notebook',
    '整機', '主機', '桌機', 'PC', '電競機',
    '背包', '滑鼠', '鍵盤', '螢幕', '電源供應器',
    'SO-DIMM', 'SODIMM', '筆記型'
]


def search_pchome(keyword, max_pages=2):
    """
    Search PChome using their public API
    
    Args:
        keyword: Search term
        max_pages: Maximum pages to fetch (20 products per page)
    
    Returns:
        List of product dicts
    """
    base_url = "https://ecshweb.pchome.com.tw/search/v3.3/all/results"
    products = []
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'application/json',
    }
    
    for page in range(1, max_pages + 1):
        try:
            params = {
                'q': keyword,
                'page': page,
                'sort': 'sale/dc'  # Sort by sales
            }
            
            response = requests.get(base_url, params=params, headers=headers, timeout=10)
            
            if response.status_code != 200:
                print(f"  Warning: PChome returned status {response.status_code}")
                break
            
            data = response.json()
            
            if 'prods' not in data or not data['prods']:
                break
            
            for prod in data['prods']:
                # Skip non-PChome items (marketplace)
                if not prod.get('isPChome', 0):
                    continue
                
                products.append({
                    'pchome_id': prod.get('Id', ''),
                    'name': prod.get('name', ''),
                    'price': prod.get('price', 0),
                    'original_price': prod.get('originPrice', 0),
                })
            
            # Rate limiting
            time.sleep(0.3)
            
        except Exception as e:
            print(f"  Error fetching page {page}: {e}")
            break
    
    return products


def should_exclude(product_name):
    """Check if product should be excluded"""
    name_lower = product_name.lower()
    for kw in EXCLUDE_KEYWORDS:
        if kw.lower() in name_lower:
            return True
    return False


def classify_pchome_product(product_name, category, generation):
    """
    Classify a PChome product to verify it matches the generation
    Returns True if product matches the generation
    """
    name_lower = product_name.lower()
    
    # For GPU, verify the model number matches
    if category == 'GPU':
        keywords = PCHOME_SEARCH_KEYWORDS['GPU'].get(generation, [])
        for kw in keywords:
            if kw.lower().replace(' ', '') in name_lower.replace(' ', ''):
                return True
        return False
    
    # For RAM, verify DDR type
    if category == 'RAM':
        if generation == 'DDR5' and 'ddr5' in name_lower:
            return True
        if generation == 'DDR4' and 'ddr4' in name_lower and 'ddr5' not in name_lower:
            return True
        return False
    
    return False


def fetch_pchome_data():
    """
    Fetch all GPU/RAM products from PChome
    
    Returns:
        DataFrame with classified products
    """
    import pandas as pd
    
    all_products = []
    
    print(" 🛒 Fetching data from PChome 24h...")
    
    # Fetch GPU products
    for generation, keywords in PCHOME_SEARCH_KEYWORDS['GPU'].items():
        for keyword in keywords[:1]:  # Use first keyword only to avoid duplicates
            print(f"   Searching: {keyword}...")
            products = search_pchome(keyword, max_pages=2)
            
            for prod in products:
                if should_exclude(prod['name']):
                    continue
                
                if not classify_pchome_product(prod['name'], 'GPU', generation):
                    continue
                
                # Verify price is in reasonable range
                if prod['price'] < 5000 or prod['price'] > 200000:
                    continue
                
                all_products.append({
                    '類別': 'GPU',
                    '世代': generation,
                    '商品名稱': prod['name'],
                    '價格': prod['price'],
                    '原始價格': prod['original_price'],
                    'PChome_ID': prod['pchome_id'],
                    '來源': 'PChome'
                })
    
    # Fetch RAM products
    for generation, keywords in PCHOME_SEARCH_KEYWORDS['RAM'].items():
        for keyword in keywords[:1]:
            print(f"   Searching: {keyword}...")
            products = search_pchome(keyword, max_pages=2)
            
            for prod in products:
                if should_exclude(prod['name']):
                    continue
                
                if not classify_pchome_product(prod['name'], 'RAM', generation):
                    continue
                
                # Verify price is in reasonable range for RAM
                if prod['price'] < 500 or prod['price'] > 50000:
                    continue
                
                all_products.append({
                    '類別': 'RAM',
                    '世代': generation,
                    '商品名稱': prod['name'],
                    '價格': prod['price'],
                    '原始價格': prod['original_price'],
                    'PChome_ID': prod['pchome_id'],
                    '來源': 'PChome'
                })
    
    # Remove duplicates by name
    seen_names = set()
    unique_products = []
    for prod in all_products:
        name_key = prod['商品名稱'][:50]  # Use first 50 chars as key
        if name_key not in seen_names:
            seen_names.add(name_key)
            unique_products.append(prod)
    
    print(f" ✅ Fetched {len(unique_products)} products from PChome")
    
    return pd.DataFrame(unique_products)


def save_pchome_to_database(df):
    """Save PChome products to database"""
    import psycopg2
    from psycopg2.extras import Json
    
    # Import db_config from parent
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from db_config import config
    
    if df.empty:
        print("  No PChome data to save")
        return False
    
    try:
        conn = psycopg2.connect(**config.get_psycopg2_params())
        cursor = conn.cursor()
        today = datetime.now().date()
        saved_count = 0
        
        print("  Saving PChome data to database...")
        
        for _, row in df.iterrows():
            brand = row['商品名稱'].split()[0] if row['商品名稱'] else None
            
            # Insert/update product with source
            cursor.execute("""
                INSERT INTO products (category, generation, product_name, brand, first_seen, last_seen, source)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (product_name, generation) 
                DO UPDATE SET last_seen = EXCLUDED.last_seen, is_active = TRUE, source = EXCLUDED.source
                RETURNING product_id
            """, (row['類別'], row['世代'], row['商品名稱'], brand, today, today, 'PChome'))
            
            product_id = cursor.fetchone()[0]
            
            # Insert price with source
            cursor.execute("""
                INSERT INTO daily_prices (date, product_id, price, source, raw_info)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (date, product_id) DO UPDATE SET price = EXCLUDED.price, source = EXCLUDED.source
            """, (today, product_id, row['價格'], 'PChome', Json({'pchome_id': row.get('PChome_ID', '')})))
            
            saved_count += 1
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"  ✅ Saved {saved_count} PChome products to database")
        return True
        
    except Exception as e:
        print(f"  ❌ Database error: {e}")
        return False


def main():
    """Test PChome crawler"""
    print("=" * 60)
    print(" PChome 24h Crawler - Test Run")
    print("=" * 60)
    
    df = fetch_pchome_data()
    
    if not df.empty:
        print("\n Sample data:")
        print(df.head(10).to_string(index=False))
        
        print(f"\n Summary:")
        summary = df.groupby(['類別', '世代']).agg({'價格': ['count', 'mean', 'min', 'max']}).round(0)
        print(summary)
    
    print("=" * 60)


if __name__ == "__main__":
    main()
