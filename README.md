# GPU & RAM Price Index - Alternative Data Collection

Automated web scraping system for collecting daily GPU and RAM pricing data from Taiwan's consumer electronics market. Built for quantitative analysis and alternative data research.

## Project Overview

**Objective**: Collect 30 days of pricing data to analyze correlation with semiconductor stock prices (TSMC, NVIDIA)

**Data Source**: coolpc.com.tw (Taiwan's leading PC component retailer)

**Collection Period**: December 9, 2025 - January 8, 2026

**Target**: 6,000+ daily price records across 32 GPU models and RAM categories

## Features

- Automated daily web scraping at 2:00 AM
- PostgreSQL time-series database
- Product taxonomy classification (32 GPU models + DDR4/DDR5)
- Data quality validation and deduplication
- Automated logging and monitoring
- Power schedule integration for Mac automation

## Tech Stack

- **Language**: Python 3.9+
- **Web Scraping**: BeautifulSoup4, Requests
- **Database**: PostgreSQL
- **Data Processing**: Pandas
- **Automation**: Cron, macOS pmset
- **Encoding**: Big5 (Taiwan market)

## Project Structure

```
.
├── run_crawler.py          # Main scraper (fetch, classify, save)
├── daily_crawler.py        # Automated wrapper with logging
├── query_data.py           # Data query and analysis
├── db_config.py            # Database configuration
├── product_taxonomy.json   # Classification rules (32 GPU + RAM)
├── cron_setup.txt          # Cron job configuration
├── check_status.sh         # System monitoring script
├── setup_schedule.sh       # Power schedule setup
├── logs/                   # Execution logs
└── USAGE.md               # Quick reference guide
```

## Database Schema

### Tables

**products** - Product catalog
- `product_id`, `category`, `generation`, `product_name`, `brand`
- `first_seen`, `last_seen`, `is_active`

**daily_prices** - Time-series pricing
- `date`, `product_id`, `price`, `raw_info`

**daily_index** - Aggregated market indices
- `date`, `category`, `generation`
- `avg_price`, `min_price`, `max_price`, `median_price`
- `std_price`, `product_count`, `volatility`

**data_quality_log** - Validation tracking
- `date`, `records_fetched`, `records_classified`, `success_rate`

## Installation

### Prerequisites

```bash
# Install Python dependencies
pip install requests beautifulsoup4 pandas psycopg2-binary

# Install PostgreSQL
brew install postgresql@15
brew services start postgresql@15

# Create database
createdb price_index
```

### Database Setup

```sql
-- Run schema creation (see schema.sql)
psql price_index < schema.sql
```

### Configuration

1. Update `db_config.py` with your PostgreSQL credentials
2. Set environment variables (optional):
   ```bash
   export PGUSER=your_username
   export PGPASSWORD=your_password
   ```

## Usage

### Manual Execution

```bash
# Run crawler once
python3 daily_crawler.py

# Query latest data
python3 query_data.py

# Check system status
./check_status.sh
```

### Automated Execution

```bash
# Install cron job (runs daily at 2:00 AM)
crontab cron_setup.txt

# Verify installation
crontab -l

# Set up power schedule (Mac only)
./setup_schedule.sh
```

## Sample Output

```
Today's Market Index:

category generation      avg_price  min_price  max_price  product_count
GPU      NVIDIA_RTX_5090   99102.25      92888     103990             61
GPU      NVIDIA_RTX_5080   43637.24      35888      55990             84
GPU      NVIDIA_RTX_5070   22182.17      19888      25990             96
RAM      DDR5               4514.46       2900       7399             13
```

## Data Collection Progress

| Milestone | Date | Records | Status |
|-----------|------|---------|--------|
| Day 7 | Dec 15, 2025 | ~1,400 | Pending |
| Day 14 | Dec 22, 2025 | ~2,800 | Pending |
| Day 24 | Jan 1, 2026 | ~4,800 | Pending |
| Day 30 | Jan 8, 2026 | ~6,000 | Target |

## Planned Analysis

1. **Price Correlation Analysis**
   - GPU prices vs TSMC/NVIDIA stock prices
   - Information Coefficient (IC) calculation
   - Statistical significance testing

2. **Time Series Analysis**
   - Moving averages (MA7, MA30)
   - Volatility patterns
   - Seasonal trends

3. **Visualization Dashboard**
   - Streamlit web app
   - Real-time price charts
   - Market index tracking

## Key Insights (To Be Updated)

_This section will be populated after 30 days of data collection_

## Challenges & Solutions

**Challenge**: Big5 encoding for Taiwan market  
**Solution**: `res.encoding = 'big5'` in requests

**Challenge**: Product classification accuracy  
**Solution**: JSON-based taxonomy with regex patterns

**Challenge**: Automated execution reliability  
**Solution**: Power schedule + cron + comprehensive logging

## Future Enhancements

- [ ] Add more retailers (PChome, Shopee)
- [ ] Expand to CPU and motherboard pricing
- [ ] Real-time price alerts
- [ ] API endpoint for data access
- [ ] Machine learning price prediction

## Contributing

This is a personal research project, but suggestions are welcome! Feel free to open an issue.

## License

MIT License - See LICENSE file for details

## Author

**Travis Cua**  
Quantitative Research | Alternative Data  
[LinkedIn](#) | [GitHub](#)

## Acknowledgments

- Data source: coolpc.com.tw
- Inspired by alternative data research in quantitative finance
- Built as part of a 90-day quant project series

---

**Project Status**: Active Data Collection (Day 1/30)  
**Last Updated**: December 9, 2025
