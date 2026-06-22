# Phase 2: Web Scraping Guide 🔍

Congratulations! You now have a functional web scraping engine for finding running shoe deals.

## What's New in Phase 2

✅ **Base Scraper Class** - Reusable scraping framework
✅ **The Last Hunt Scraper** - First retailer implementation  
✅ **Scraper Manager** - Orchestrates scraping and database storage
✅ **Scraping API** - Endpoints to trigger scraping operations
✅ **Price Recording** - Automatic price history tracking
✅ **Deal Detection** - Auto-creates deals when prices drop below target

## Setup Instructions

### 1. Install New Dependencies

```bash
# Make sure virtual environment is activated
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows

# Install updated requirements
pip install -r requirements.txt

# Install Playwright browsers (one-time setup)
playwright install
```

This downloads Chrome/Firefox browsers for Playwright to use.

### 2. Restart Your Server

```bash
# Stop the current server (Ctrl+C)
# Then restart
python run.py
```

## Testing the Scraper

### Method 1: Test Endpoint (No Database)

This is a quick test that doesn't save anything to the database:

```bash
# Test The Last Hunt scraper
curl "http://localhost:8000/api/scrape/test/the-last-hunt?brand=Nike&model=Vaporfly"
```

Or visit in browser:
http://localhost:8000/api/scrape/test/the-last-hunt?brand=Nike&model=Vaporfly

### Method 2: Scrape a Single Shoe (Saves to Database)

```bash
# Scrape shoe ID 1 across all retailers
curl -X POST http://localhost:8000/api/scrape/shoe/1

# Scrape shoe ID 1 only from retailer ID 1 (The Last Hunt)
curl -X POST http://localhost:8000/api/scrape/shoe/1 \
  -H "Content-Type: application/json" \
  -d '{"retailer_ids": [1]}'
```

### Method 3: Use Swagger UI (Easiest!)

1. Go to http://localhost:8000/docs
2. Find the **scraping** section
3. Try these endpoints:
   - `GET /api/scrape/test/the-last-hunt` - Quick test
   - `POST /api/scrape/shoe/{shoe_id}` - Scrape one shoe
   - `POST /api/scrape/all` - Scrape all shoes (be patient!)

## Understanding the Scraping Flow

```
1. You trigger scrape via API
   ↓
2. ScraperManager gets shoe + retailers from DB
   ↓
3. For each retailer:
   - Use appropriate scraper (TheLastHuntScraper)
   - Search for products matching brand/model
   - Get detailed product info (price, sizes, stock)
   ↓
4. For each product found:
   - Record price in price_records table
   - If price ≤ target_price → Create deal in deals table
   ↓
5. Return results to you
```

## API Endpoints

### Test Scraper (No DB)
```
GET /api/scrape/test/the-last-hunt?brand=Nike&model=Vaporfly
```
Quick test to see if scraper works without saving data.

### Scrape Single Shoe
```
POST /api/scrape/shoe/{shoe_id}
Body (optional): {"retailer_ids": [1, 2, 3]}
```
Scrape specific shoe across all or selected retailers.

### Scrape All Shoes
```
POST /api/scrape/all
Body (optional): {"retailer_ids": [1]}
```
⚠️ This can take several minutes!

### Scrape Specific Retailer
```
POST /api/scrape/retailer/{retailer_id}
Body (optional): {"shoe_ids": [1, 2, 3]}
```
Scrape one retailer for all or selected shoes.

## Expected Results

### Successful Scrape Response
```json
{
  "success": true,
  "message": "Scraping completed for shoe ID 1",
  "results": {
    "shoe": "Nike ZoomX Vaporfly Next% 3",
    "size": "10.5",
    "retailers_scraped": 1,
    "products_found": 3,
    "prices_recorded": 3,
    "deals_found": 1,
    "errors": []
  },
  "scraped_at": "2024-02-21T10:30:00"
}
```

### What Gets Stored

**Price Records** (price_records table):
- Product URL
- Current price
- Original price (if on sale)
- In stock status
- Size availability
- Timestamp

**Deals** (deals table - only if price ≤ target):
- Current price
- Target price
- Savings amount and percentage
- Product URL
- Active status

## Viewing Scrape Results

### Check Price Records
```bash
# Via API
curl http://localhost:8000/api/shoes/1/prices

# Via database viewer
# Open shoe_deals.db in DB Browser
# Look at price_records table
```

### Check Deals Found
```bash
# Via API
curl http://localhost:8000/api/deals

# Or visit Swagger UI
http://localhost:8000/docs
# GET /api/deals endpoint
```

## How The Last Hunt Scraper Works

### Search Process
1. **Builds search URL** with brand and model
2. **Fetches search results** page
3. **Parses product grid** using CSS selectors
4. **Extracts** product URLs, names, prices

### Product Details
1. **Visits each product page**
2. **Extracts** detailed info:
   - Full product name
   - Current price
   - Original price (if sale)
   - Available sizes
   - Stock status
3. **Returns** structured data

### CSS Selectors Used

The scraper looks for common e-commerce patterns:
- Product items: `.product-item`, `.product-card`, `.grid-item`
- Product links: `a[href*="/products/"]`
- Prices: `.price`, `.product-price`
- Original prices: `.compare-at-price`, `.was-price`
- Sizes: `select[name*="size"] option`

**Note:** These selectors may need adjustment based on actual site structure!

## Troubleshooting

### "No products found"

**Possible causes:**
1. Search query didn't match any products
2. CSS selectors need adjustment for the website
3. Website structure has changed

**Solutions:**
- Try different brand/model combinations
- Use the test endpoint to see raw results
- Check server logs for details

### "Failed to fetch search page"

**Possible causes:**
1. Network connectivity issue
2. Website blocking requests
3. Invalid URL

**Solutions:**
- Check your internet connection
- Try enabling browser mode (use_browser=True)
- Verify the retailer's website is accessible

### "Playwright browser not installed"

**Solution:**
```bash
playwright install
```

### Rate Limiting / Blocked

The scraper includes built-in delays (2-3 seconds between requests).

If you get blocked:
1. Increase delays in `base_scraper.py`
2. Use browser mode instead of requests
3. Scrape during off-peak hours
4. Add more realistic headers

## Customizing the Scraper

### Adjust Rate Limiting

Edit `app/scrapers/base_scraper.py`:
```python
# Increase delay between requests
time.sleep(5)  # Change from 2 to 5 seconds
```

### Enable Browser Mode

For JavaScript-heavy sites, use Playwright:
```python
# In the_last_hunt.py __init__
self.config = {
    "use_browser": True  # Change from False
}
```

### Add Custom Headers

```python
# In base_scraper.py __init__
self.session.headers.update({
    'User-Agent': 'Your custom user agent',
    'Accept-Language': 'en-CA,en;q=0.9'
})
```

## Important Notes

### Legal & Ethical
- ✅ Personal use only
- ✅ Respects rate limits (2-3s delays)
- ✅ Identifies itself with User-Agent
- ❌ Don't scrape excessively
- ❌ Don't republish scraped data

### Performance
- **Single shoe:** ~5-10 seconds per retailer
- **All shoes (12):** ~2-3 minutes per retailer
- **Add delays:** Sites may block rapid requests

### Data Freshness
- Prices are snapshots at scrape time
- Run scraping periodically (we'll automate this in Phase 4)
- Old prices remain in price_records for history

## Next Steps - Adding More Retailers

To add another retailer:

1. **Create scraper file** (copy `the_last_hunt.py`)
2. **Update selectors** for new site structure
3. **Register in ScraperManager**
4. **Test thoroughly**

We'll tackle more retailers as we progress!

## Testing Checklist

Before considering scraping complete:

- [ ] Test endpoint works without errors
- [ ] Products are found for at least one shoe
- [ ] Prices are recorded in database
- [ ] Deals are created when price < target
- [ ] Price history is viewable via API
- [ ] No rate limiting or blocking issues

## Common Test Scenarios

### Scenario 1: Nike Vaporfly
```bash
# Should find products
curl "http://localhost:8000/api/scrape/test/the-last-hunt?brand=Nike&model=Vaporfly"
```

### Scenario 2: Adidas Adizero
```bash
# Should find products
curl "http://localhost:8000/api/scrape/test/the-last-hunt?brand=Adidas&model=Adizero"
```

### Scenario 3: Obscure Model
```bash
# Might not find products
curl "http://localhost:8000/api/scrape/test/the-last-hunt?brand=Nike&model=XYZ123"
```

## What You've Achieved! 🎉

✅ Built a web scraping framework
✅ Implemented first retailer scraper
✅ Automatic price tracking
✅ Automatic deal detection
✅ API to trigger scraping
✅ Database storage of all results

**You now have a working deal finder!** 🏃‍♂️👟

The scraper will:
- Search retailers for your shoes
- Track prices over time
- Alert you to deals automatically
- Store everything in your database

In Phase 3, we'll build a nice frontend to view all this data.
In Phase 4, we'll add automatic scheduling so it runs every few hours.

But right now, you can manually scrape and find deals! Try it out! 🚀
