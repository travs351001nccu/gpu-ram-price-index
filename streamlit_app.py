import streamlit as st
import pandas as pd
import psycopg2
import os
from datetime import datetime, timedelta
from db_config import config

# Page config
st.set_page_config(
    page_title="Price Index Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #1e293b;
        border-radius: 10px;
        padding: 20px;
        color: white;
    }
    .stDataFrame {
        font-family: 'Inter', sans-serif;
    }
</style>
""", unsafe_allow_html=True)

# Database Connection
def get_connection():
    # Streamlit Cloud handles secrets via st.secrets or env vars
    # We try to use the db_config which looks at OS env vars
    try:
        if config.database_url:
            return psycopg2.connect(config.database_url)
        return psycopg2.connect(**config.get_psycopg2_params())
    except Exception as e:
        st.error(f"Failed to connect to database: {e}")
        return None

def load_data(query, params=None):
    conn = get_connection()
    if conn:
        try:
            df = pd.read_sql(query, conn, params=params)
            return df
        except Exception as e:
            st.error(f"Query failed: {e}")
            return pd.DataFrame()
        finally:
            conn.close()
    return pd.DataFrame()

# Title
st.title("📊 GPU & RAM Price Index")
st.markdown("Real-time pricing data from Taiwan market (Coolpc / PChome)")

# Stats Row
col1, col2, col3, col4 = st.columns(4)

stats_query = """
    SELECT 
        (SELECT SUM(product_count) FROM daily_index) as total,
        (SELECT SUM(product_count) FROM daily_index WHERE date = CURRENT_DATE) as today,
        (SELECT COUNT(DISTINCT generation) FROM daily_index) as unique_gens,
        (SELECT MIN(date) FROM daily_index) as start_date
"""
stats = load_data(stats_query)

if not stats.empty:
    with col1:
        total = stats.iloc[0]['total']
        st.metric("Total Records", f"{int(total if total else 0):,}")
    with col2:
        today = stats.iloc[0]['today']
        st.metric("Collected Today", f"{int(today if today else 0):,}")
    with col3:
        unique = stats.iloc[0]['unique_gens']
        st.metric("Tracked Products", f"{int(unique if unique else 0)}")
    with col4:
        start_date = stats.iloc[0]['start_date']
        st.metric("Data Since", start_date.strftime('%Y-%m-%d') if start_date else "-")

# 7-Day Price Changes
st.subheader("📉 7-Day Price Changes")
weekly_changes_query = """
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
        dd.source,
        dd.prev_price as old_price,
        dd.price as new_price,
        ((dd.price - dd.prev_price) / dd.prev_price * 100) as change_pct
    FROM daily_data dd
    JOIN products p ON dd.product_id = p.product_id
    WHERE dd.prev_price IS NOT NULL
    AND ABS(dd.price - dd.prev_price) / dd.prev_price > 0.005
    ORDER BY change_pct DESC
"""
changes = load_data(weekly_changes_query)

if not changes.empty:
    col_inc, col_dec = st.columns(2)
    
    increases = changes[changes['change_pct'] > 0]
    decreases = changes[changes['change_pct'] < 0]
    
    with col_inc:
        st.markdown("### 📈 Increases")
        if not increases.empty:
            # Format for display
            display_inc = increases.copy()
            display_inc['Price'] = display_inc.apply(lambda x: f"${x['old_price']:,.0f} → ${x['new_price']:,.0f}", axis=1)
            display_inc['Change'] = display_inc['change_pct'].apply(lambda x: f"+{x:.1f}%")
            st.dataframe(
                display_inc[['source', 'product_name', 'Price', 'Change']],
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("No price increases detected.")

    with col_dec:
        st.markdown("### 📉 Decreases")
        if not decreases.empty:
            display_dec = decreases.copy()
            display_dec['Price'] = display_dec.apply(lambda x: f"${x['old_price']:,.0f} → ${x['new_price']:,.0f}", axis=1)
            display_dec['Change'] = display_dec['change_pct'].apply(lambda x: f"{x:.1f}%")
            st.dataframe(
                display_dec[['source', 'product_name', 'Price', 'Change']],
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("No price decreases detected.")
else:
    st.info("No significant price changes in the last 7 days.")

# Latest Prices
st.subheader("🏷️ Latest Prices")
latest_query = """
    SELECT 
        category as "Category",
        generation as "Generation",
        avg_price as "Avg Price",
        min_price as "Min Price",
        max_price as "Max Price",
        product_count as "Count"
    FROM daily_index
    WHERE date = (SELECT MAX(date) FROM daily_index)
    ORDER BY category, avg_price DESC
"""
latest = load_data(latest_query)
if not latest.empty:
    st.dataframe(
        latest.style.format({
            "Avg Price": "NT${:,.0f}",
            "Min Price": "NT${:,.0f}",
            "Max Price": "NT${:,.0f}"
        }),
        hide_index=True,
        use_container_width=True
    )

# Footer
st.markdown("---")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
