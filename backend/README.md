# Anton 🏃‍♂️

A personal web application to track and find deals on specific running shoes from trusted Canadian retailers.

## Features

- ✅ Track specific running shoes (brand, model, size)
- ✅ Monitor trusted Canadian retailers
- ✅ Price history tracking
- ✅ Automatic deal detection
- ✅ RESTful API with FastAPI
- ✅ SQLite database (upgradable to PostgreSQL)
- ✅ Web scraping engine with The Last Hunt
- ✅ Manual scraping triggers via API
- 🚧 React frontend (coming next)
- 🚧 Automated scheduling (coming next)

## Tech Stack

**Backend:**
- Python 3.11+
- FastAPI
- SQLAlchemy
- SQLite
- Playwright/BeautifulSoup4

**Frontend (upcoming):**
- React
- Vite
- Tailwind CSS
- React Query

## Project Structure

```
anton/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI application
│   │   ├── database.py          # Database configuration
│   │   ├── models/              # Database models & schemas
│   │   │   ├── __init__.py
│   │   │   ├── models.py        # SQLAlchemy models
│   │   │   └── schemas.py       # Pydantic schemas
│   │   ├── routers/             # API endpoints
│   │   │   ├── __init__.py
│   │   │   ├── shoes.py         # Shoe CRUD operations
│   │   │   ├── retailers.py     # Retailer CRUD operations
│   │   │   ├── deals.py         # Deal viewing
│   │   │   └── dashboard.py     # Dashboard stats
│   │   └── scrapers/            # Web scraping logic (coming)
│   ├── seed_data.py             # Database seeding script
│   ├── requirements.txt         # Python dependencies
│   └── .env.example             # Environment variables template
└── frontend/                    # React frontend (coming)
```

## Setup Instructions

### Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- Git

### Backend Setup

1. **Clone/Navigate to the project:**
```bash
cd anton/backend
```

2. **Create a virtual environment:**
```bash
# Create virtual environment
python -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables:**
```bash
# Copy the example env file
cp .env.example .env

# Edit .env if needed (defaults should work for local development)
```

5. **Initialize database with seed data:**
```bash
python seed_data.py
```

This will:
- Create the SQLite database
- Add 7 Canadian retailers
- Add 12 running shoes to track

6. **Run the development server:**
```bash
# From the backend directory (make sure you're in backend/, not backend/app/)
python run.py

# Or using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs (Swagger UI)
- Alternative Docs: http://localhost:8000/redoc

## API Endpoints

### Shoes

- `GET /api/shoes` - List all shoes
- `GET /api/shoes/{id}` - Get specific shoe
- `POST /api/shoes` - Add new shoe
- `PUT /api/shoes/{id}` - Update shoe
- `DELETE /api/shoes/{id}` - Delete shoe
- `GET /api/shoes/{id}/prices` - Get price history

### Retailers

- `GET /api/retailers` - List all retailers
- `GET /api/retailers/{id}` - Get specific retailer
- `POST /api/retailers` - Add new retailer
- `PUT /api/retailers/{id}` - Update retailer
- `DELETE /api/retailers/{id}` - Delete retailer

### Deals

- `GET /api/deals` - List all deals
- `GET /api/deals/{id}` - Get specific deal
- `GET /api/deals/shoe/{shoe_id}` - Deals for specific shoe
- `GET /api/deals/retailer/{retailer_id}` - Deals from specific retailer
- `PUT /api/deals/{id}/deactivate` - Mark deal as inactive

### Dashboard

- `GET /api/dashboard/stats` - Dashboard statistics
- `GET /api/dashboard/recent-deals` - Recent deals
- `GET /api/dashboard/best-deals` - Best deals by savings

### Scraping (NEW!)

- `POST /api/scrape/shoe/{id}` - Scrape specific shoe
- `POST /api/scrape/all` - Scrape all active shoes
- `POST /api/scrape/retailer/{id}` - Scrape specific retailer
- `GET /api/scrape/test/the-last-hunt` - Test scraper without DB

## Testing the API

### Using the Swagger UI

1. Navigate to http://localhost:8000/docs
2. Try out any endpoint directly in the browser
3. See request/response examples

### Using curl

```bash
# Get all shoes
curl http://localhost:8000/api/shoes

# Add a new shoe
curl -X POST http://localhost:8000/api/shoes \
  -H "Content-Type: application/json" \
  -d '{
    "brand": "Adidas",
    "model": "Adizero Takumi Sen 10",
    "size": "11",
    "target_price": 180.0,
    "notes": "Racing flat",
    "is_active": true
  }'

# Get dashboard stats
curl http://localhost:8000/api/dashboard/stats
```

## Database Schema

### Tables

**shoes**
- id, brand, model, size, target_price, notes, is_active
- created_at, updated_at

**retailers**
- id, name, base_url, is_active, scraping_enabled
- scraper_config, last_scraped_at, created_at, updated_at

**price_records**
- id, shoe_id, retailer_id, product_url, price
- original_price, in_stock, size_available, scraped_at

**deals**
- id, shoe_id, retailer_id, current_price, target_price
- savings_amount, savings_percent, product_url
- in_stock, is_active, detected_at, expires_at

## Seeded Data

### Retailers (7)
- The Last Hunt
- JD Sports Canada
- Altitude Sports
- Sport Experts
- MEC
- Running Room
- Sport Chek

### Shoes (12)
- Adidas: Adizero Adios Pro 3, Boston 12, SL
- Asics: Metaspeed Sky+, Magic Speed 3
- Puma: Deviate Nitro 2, Velocity Nitro 3
- Nike: Vaporfly Next% 3, Alphafly 3, Zoom Fly 5
- Mizuno: Wave Rebellion Pro, Wave Rider 27

All shoes are size 10.5 by default (you can add more sizes)

## Next Steps

### Phase 2: Web Scraping ✅ COMPLETE
- [x] Build base scraper class
- [x] Implement The Last Hunt scraper
- [x] Test with real product pages
- [x] Add error handling and logging
- [x] API endpoints for manual scraping

See **PHASE2_SCRAPING_GUIDE.md** for detailed scraping documentation!

### Phase 3: Frontend (Next)
- [ ] Set up React with Vite
- [ ] Create dashboard view
- [ ] Create deals list view
- [ ] Add shoe/retailer management

### Phase 4: Automation
- [ ] Add APScheduler for periodic scraping
- [ ] Implement deal detection logic
- [ ] Add email notifications (optional)

## Common Commands

```bash
# Activate virtual environment
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Run the server (from backend directory)
python run.py

# Reset database (careful!)
rm shoe_deals.db
python seed_data.py

# Install new package
pip install package-name
pip freeze > requirements.txt
```

## Troubleshooting

### Database Issues
If you see database errors, try:
```bash
rm shoe_deals.db  # Delete the database
python seed_data.py  # Recreate it
```

### Port Already in Use
If port 8000 is busy:
```bash
# Change the port in .env
API_PORT=8001

# Or specify it when running
uvicorn app.main:app --reload --port 8001
```

### Module Not Found
Make sure you're in the virtual environment:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

## Contributing

This is a personal project, but feel free to fork and customize for your own use!

## License

MIT License - feel free to use for personal projects

## Questions?

Check the API documentation at http://localhost:8000/docs or open an issue.

Happy shoe hunting! 🏃‍♂️👟
