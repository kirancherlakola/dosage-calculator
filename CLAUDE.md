# CLAUDE.md

This file provides guidance for Claude Code when working on this project.

## Project Overview

A medication dosage calculator web application that:
1. Searches the FDA's openFDA API for drug information
2. Displays official FDA drug labeling (dosage, warnings, indications)
3. Calculates personalized dosages based on patient age and weight

## Tech Stack

- **Backend**: FastAPI (Python)
- **Frontend**: Pure HTML/CSS/JavaScript embedded in `main.py`
- **External API**: openFDA Drug Label API (`https://api.fda.gov/drug/label.json`)
- **Package Manager**: uv (not pip)

## Project Structure

```
dosage-calculator/
├── main.py           # FastAPI app + embedded HTML frontend
├── database.py       # SQLite schema (legacy, not currently used)
├── pyproject.toml    # uv dependencies
├── README.md         # Project documentation
└── CLAUDE.md         # This file
```

## Key Commands

```bash
# Install dependencies
uv sync

# Run development server
uv run uvicorn main:app --reload --port 8000

# Add new dependency
uv add <package-name>
```

## Architecture Notes

### Backend (`main.py`)

- Uses `httpx` for async HTTP requests to openFDA
- Three main API endpoints:
  - `/api/fda/search` - Search drugs by name
  - `/api/fda/drug/{id}` - Get drug by FDA document ID
  - `/api/fda/drug-by-name` - Get drug by brand/generic name
- HTML frontend is embedded as a string in `serve_frontend()`

### Frontend (embedded in `main.py`)

- Single-page application with vanilla JavaScript
- Debounced search with dropdown results
- Patient parameters (age/weight) for dosage calculation
- Weight-based dosing guidelines stored in `dosingGuidelines` object

### openFDA API

- Base URL: `https://api.fda.gov/drug/label.json`
- No API key required
- Search fields: `openfda.brand_name`, `openfda.generic_name`
- Key response fields: `dosage_and_administration`, `warnings`, `indications_and_usage`

## Common Tasks

### Adding a new medication to dosing guidelines

Edit the `dosingGuidelines` object in the JavaScript section of `main.py`:

```javascript
const dosingGuidelines = {
    'DRUG_NAME': {
        dosePerKg: 10,           // mg/kg per dose
        maxSingleDose: 500,      // max single dose in mg
        maxDailyDose: 40,        // max mg/kg/day
        unit: 'mg',
        frequency: 'every 8 hours',
        maxDailyTotal: 2000      // absolute max daily in mg
    },
};
```

### Adding a new API endpoint

Add async function in `main.py` using the pattern:

```python
@app.get("/api/endpoint")
async def endpoint_name(param: str = Query(...)):
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url)
        # process response
```

## Testing

```bash
# Test FDA search
curl "http://localhost:8000/api/fda/search?q=tylenol"

# Test drug lookup
curl "http://localhost:8000/api/fda/drug-by-name?name=tylenol"
```

## Deployment Notes

- No database required (uses live FDA API)
- Single file deployment (`main.py` contains everything)
- Requires outbound HTTPS access to `api.fda.gov`
