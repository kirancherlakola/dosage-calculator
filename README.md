# Medication Dosage Calculator

A web-based medication dosage calculator that fetches real drug information from the FDA's openFDA API and provides personalized dosage calculations based on patient age and weight.

## Features

- **FDA Drug Search**: Search FDA-approved medications using the openFDA API
- **Real Drug Labels**: View official FDA drug labeling including indications, warnings, and dosage information
- **Personalized Dosing**: Calculate weight-based dosages for common medications
- **Pediatric Support**: Age-appropriate dosing with pediatric warnings
- **No Database Required**: Uses live FDA API data (no manual data maintenance)

## Tech Stack

- **Backend**: Python FastAPI
- **Frontend**: Pure HTML/CSS/JavaScript (no frameworks)
- **Data Source**: [openFDA Drug Label API](https://open.fda.gov/apis/drug/label/)
- **Package Manager**: uv

## Quick Start

### Prerequisites

- Python 3.9+
- [uv](https://github.com/astral-sh/uv) package manager

### Installation

```bash
# Clone the repository
git clone https://github.com/kirancherlakola/dosage-calculator.git
cd dosage-calculator

# Install dependencies
uv sync

# Run the server
uv run uvicorn main:app --reload --port 8000
```

Open http://localhost:8000 in your browser.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web interface |
| `/api/fda/search?q={name}` | GET | Search FDA drugs by name |
| `/api/fda/drug/{id}` | GET | Get drug details by FDA ID |
| `/api/fda/drug-by-name?name={name}` | GET | Get drug by brand/generic name |

## Supported Medications for Dosage Calculation

Weight-based dosing calculations are available for:

| Medication | Dose (mg/kg) | Frequency | Max Daily |
|------------|--------------|-----------|-----------|
| Acetaminophen | 15 | every 4-6 hours | 75 mg/kg (max 4000mg) |
| Ibuprofen | 10 | every 6-8 hours | 40 mg/kg (max 1200mg) |
| Amoxicillin | 25 | every 8 hours | 100 mg/kg (max 3000mg) |
| Diphenhydramine | 1.25 | every 6 hours | 5 mg/kg (max 300mg) |
| Azithromycin | 10 | once daily | 500mg |

## Data Sources

- [openFDA](https://open.fda.gov/) - Official FDA drug labeling data
- [RxNorm](https://www.nlm.nih.gov/research/umls/rxnorm/) - Drug nomenclature (reference)
- Pediatric dosing based on standard medical guidelines

## Disclaimer

This calculator is for **educational purposes only**. Always consult a healthcare professional before taking any medication. Dosage recommendations may vary based on individual health conditions, other medications, and specific circumstances.

## License

MIT
