# Dashboard Documentation

## Overview

The web dashboard provides real-time visualization of collected price data with interactive charts and statistics.

## Starting the Dashboard

```bash
python3 dashboard.py
```

The dashboard will be available at:
- Local access: http://localhost:5001
- Network access: http://[your-ip]:5001

## Features

### Statistics Overview

Four key metrics displayed at the top:
- **Total Records**: Cumulative product count across all days
- **Today's Collection**: Products collected in the current day
- **Unique Products**: Number of distinct product types tracked
- **Data Range**: Date span of collected data

### Price Table

Real-time price data showing:
- Product category (GPU/RAM)
- Generation/model
- Average price
- Minimum price
- Maximum price
- Product count

Data is color-coded by category for easy identification.

### Price Trends Chart

Interactive line chart displaying:
- 7-day price history
- Multiple product lines
- Hover tooltips with exact prices
- Automatic updates every 5 minutes

### Crawler Logs

Recent execution history showing:
- Run date
- Success/failure status
- Product count collected

## API Endpoints

The dashboard exposes REST API endpoints for programmatic access:

### GET /api/stats

Returns overall statistics:
```json
{
  "total_records": 874,
  "today_records": 164,
  "unique_products": 9,
  "start_date": "2025-12-09",
  "end_date": "2025-12-10"
}
```

### GET /api/latest

Returns latest price data:
```json
[
  {
    "category": "GPU",
    "generation": "NVIDIA_RTX_5090",
    "avg_price": 99102.25,
    "min_price": 92888.0,
    "max_price": 103990.0,
    "count": 16,
    "last_updated": "2025-12-10 00:00:00"
  }
]
```

### GET /api/historical/<days>

Returns historical price trends:
```bash
# Get 7-day history
curl http://localhost:5001/api/historical/7
```

### GET /api/logs

Returns recent crawler execution logs:
```json
[
  {
    "date": "2025-12-10",
    "success": true,
    "product_count": 506,
    "file": "crawler_20251210.log"
  }
]
```

## Configuration

### Port Configuration

Default port is 5001. To change:

Edit `dashboard.py`:
```python
app.run(debug=True, host='0.0.0.0', port=5001)
```

### Auto-Refresh

Dashboard auto-refreshes every 5 minutes. To modify:

Edit `templates/dashboard.html`:
```javascript
// Change refresh interval (in milliseconds)
setInterval(loadData, 5 * 60 * 1000);  // 5 minutes
```

## Accessing from Other Devices

The dashboard runs on all network interfaces (0.0.0.0), allowing access from:

**Same computer:**
```
http://localhost:5001
```

**Other devices on same network:**
```
http://[your-mac-ip]:5001
```

**Find your IP:**
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

## Running in Background

To keep dashboard running continuously:

```bash
# Start in background
nohup python3 dashboard.py > dashboard.log 2>&1 &

# Check if running
ps aux | grep dashboard.py

# Stop
pkill -f dashboard.py
```

## Troubleshooting

### Port Already in Use

If port 5001 is occupied:

```bash
# Find process using port
lsof -i :5001

# Kill process
kill -9 [PID]

# Or use different port
python3 dashboard.py --port 5002
```

### No Data Showing

Check database connection:
```bash
python3 -c "from db_config import get_db_connection; conn = get_db_connection(); print('OK')"
```

Verify data exists:
```bash
python3 query_data.py
```

### Dashboard Not Loading

Check Flask is running:
```bash
curl http://localhost:5001
```

View error logs:
```bash
python3 dashboard.py
# Check terminal output for errors
```

## Performance

### Expected Load Times

- Initial page load: <1 second
- API responses: <200ms
- Chart rendering: <500ms

### Browser Compatibility

Tested on:
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

### Mobile Support

Dashboard is responsive and works on:
- iOS Safari
- Android Chrome
- Tablets

## Security Notes

**Development Mode:**
The dashboard runs in Flask development mode. For production deployment:

1. Disable debug mode
2. Use production WSGI server (gunicorn, uWSGI)
3. Add authentication if exposing publicly
4. Use HTTPS

**Network Access:**
Dashboard is accessible on local network. Ensure firewall rules are appropriate for your security requirements.

## Customization

### Styling

CSS is located in `static/dashboard.css`. Modify for custom themes.

### Chart Configuration

Chart.js configuration in `templates/dashboard.html`:
```javascript
// Modify chart options
trendChart = new Chart(ctx, {
    type: 'line',
    data: { datasets },
    options: {
        // Customize here
    }
});
```

### Adding Features

Dashboard uses Flask framework. Add new routes in `dashboard.py`:
```python
@app.route('/api/custom')
def custom_endpoint():
    # Your code here
    return jsonify(data)
```

## Monitoring

### Check Dashboard Status

```bash
# Test API
curl http://localhost:5001/api/stats | python3 -m json.tool

# Check response time
time curl -s http://localhost:5001/api/latest > /dev/null
```

### Log Monitoring

Dashboard logs to stdout. Redirect to file:
```bash
python3 dashboard.py > dashboard.log 2>&1
```

## Stopping the Dashboard

**Graceful shutdown:**
```bash
# If running in terminal
Press Ctrl+C

# If running in background
pkill -f dashboard.py
```

**Force stop:**
```bash
pkill -9 -f dashboard.py
```
