# Tick Sightings Backend - MVP

A simple backend system for managing tick sighting data in the UK.

## Features

✅ Data ingestion from API with cleaning and deduplication  
✅ SQLite database for efficient storage  
✅ REST API with search and filtering  
✅ Statistics and trends endpoints  
✅ Error handling and logging  

## Requirements

Create a `requirements.txt` file with:

```
flask==3.0.0
flask-cors==4.0.0
requests==2.31.0
```

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run data ingestion (first time)
python batch1_ingestion.py

# Start the API server
python batch2_api.py
```

## Project Structure

```
tick-sightings-backend/
├── batch1_ingestion.py      # Data fetching and storage
├── batch2_api.py             # Flask API server
├── requirements.txt          # Python dependencies
├── tick_sightings.db        # SQLite database (auto-created)
└── README.md                 # This file
```

## API Endpoints

### Health Check
```
GET /
```

### Get All Sightings
```
GET /api/sightings?page=1&per_page=100
```

### Search & Filter
```
GET /api/sightings/search?start_date=2024-01-01&end_date=2024-12-31&location=London&species=Ixodes
```

**Parameters:**
- `start_date` - Filter by start date (YYYY-MM-DD)
- `end_date` - Filter by end date (YYYY-MM-DD)
- `location` - Filter by location (partial match)
- `species` - Filter by species name (partial match)

### Region Statistics
```
GET /api/stats/regions
```
Returns count of sightings per location.

### Trends Over Time
```
GET /api/stats/trends?period=monthly
```
**Parameters:**
- `period` - "weekly" or "monthly" (default: monthly)

### Species Statistics
```
GET /api/stats/species
```
Returns count by species type.

## Example Usage

```bash
# Test the API
curl http://localhost:5000/

# Get sightings
curl http://localhost:5000/api/sightings

# Search by location
curl "http://localhost:5000/api/sightings/search?location=London"

# Get region stats
curl http://localhost:5000/api/stats/regions

# Get monthly trends
curl http://localhost:5000/api/stats/trends?period=monthly
```

## Data Processing Strategy

1. **Ingestion**: Fetch data from external API
2. **Cleaning**: Remove duplicates, handle missing fields
3. **Storage**: Store in SQLite with indexed fields
4. **Serving**: Provide filtered and aggregated data via REST API

## Error Handling

- API failures are logged and handled gracefully
- Duplicate entries are automatically skipped
- Missing data fields are filled with defaults
- All endpoints return JSON with success/error status

## Architecture Decisions

### Why SQLite?
- Simple, serverless, no setup required
- Perfect for MVP and moderate data sizes
- Easy to deploy

### Why Flask?
- Lightweight and simple
- Quick to set up and understand
- Good for backend API services

### Data Strategy
- Batch ingestion to avoid overwhelming the API
- Duplicate detection using unique external ID
- Indexes on date and location for faster queries

## Future Improvements (If More Time)

- [ ] Scheduled data updates (cron job)
- [ ] Data validation with Pydantic
- [ ] Authentication and rate limiting
- [ ] PostgreSQL for production
- [ ] Caching layer (Redis)
- [ ] Docker containerization
- [ ] Unit tests
- [ ] API documentation (Swagger/OpenAPI)

## Troubleshooting

**Database not created?**
Run `batch1_ingestion.py` first to create the database.

**API connection error?**
Check if the external API is accessible: https://dev-task.elancoapps.com/

**CORS issues?**
Flask-CORS is enabled for all origins in development.

## Contact

For issues, contact: BECKY.MEARS@network.elancoah.com