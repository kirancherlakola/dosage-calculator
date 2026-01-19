from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional
import httpx
import re

app = FastAPI(title="Medication Dosage Calculator")

# openFDA API base URL
OPENFDA_BASE = "https://api.fda.gov/drug/label.json"


class FDADrugInfo(BaseModel):
    brand_name: str
    generic_name: Optional[str] = None
    manufacturer: Optional[str] = None
    product_type: Optional[str] = None
    route: Optional[str] = None
    active_ingredient: Optional[str] = None
    purpose: Optional[str] = None
    indications: Optional[str] = None
    dosage_and_administration: Optional[str] = None
    warnings: Optional[str] = None
    do_not_use: Optional[str] = None
    ask_doctor: Optional[str] = None
    stop_use: Optional[str] = None
    storage: Optional[str] = None


def clean_text(text: str) -> str:
    """Clean up FDA label text by removing extra whitespace."""
    if not text:
        return ""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)
    # Normalize whitespace
    text = ' '.join(text.split())
    return text.strip()


def extract_first(data: dict, key: str) -> Optional[str]:
    """Extract first item from a list field and clean it."""
    value = data.get(key)
    if value and isinstance(value, list) and len(value) > 0:
        return clean_text(value[0])
    return None


@app.get("/api/fda/search")
async def search_fda_drugs(q: str = Query(..., min_length=2, description="Drug name to search")):
    """Search FDA drug database by name."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            # Search by brand name or generic name
            url = f"{OPENFDA_BASE}?search=(openfda.brand_name:{q}+OR+openfda.generic_name:{q})&limit=20"
            response = await client.get(url)

            if response.status_code == 404:
                return {"results": [], "total": 0}

            response.raise_for_status()
            data = response.json()

            results = []
            seen = set()  # Avoid duplicates

            for item in data.get("results", []):
                openfda = item.get("openfda", {})
                brand_names = openfda.get("brand_name", [])
                generic_names = openfda.get("generic_name", [])
                manufacturers = openfda.get("manufacturer_name", [])

                brand = brand_names[0] if brand_names else None
                generic = generic_names[0] if generic_names else None
                manufacturer = manufacturers[0] if manufacturers else None

                # Create unique key
                key = f"{brand}|{generic}".lower()
                if key in seen:
                    continue
                seen.add(key)

                if brand or generic:
                    results.append({
                        "id": item.get("id"),
                        "brand_name": brand,
                        "generic_name": generic,
                        "manufacturer": manufacturer,
                        "product_type": openfda.get("product_type", [None])[0],
                    })

            return {
                "results": results,
                "total": data.get("meta", {}).get("results", {}).get("total", 0),
                "source": "openFDA"
            }

        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail="FDA API error")
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"FDA API unavailable: {str(e)}")


@app.get("/api/fda/drug/{drug_id}")
async def get_fda_drug(drug_id: str):
    """Get detailed drug information from FDA by ID."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            url = f"{OPENFDA_BASE}?search=id:{drug_id}&limit=1"
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

            results = data.get("results", [])
            if not results:
                raise HTTPException(status_code=404, detail="Drug not found")

            item = results[0]
            openfda = item.get("openfda", {})

            return FDADrugInfo(
                brand_name=openfda.get("brand_name", ["Unknown"])[0],
                generic_name=openfda.get("generic_name", [None])[0],
                manufacturer=openfda.get("manufacturer_name", [None])[0],
                product_type=openfda.get("product_type", [None])[0],
                route=openfda.get("route", [None])[0],
                active_ingredient=extract_first(item, "active_ingredient"),
                purpose=extract_first(item, "purpose"),
                indications=extract_first(item, "indications_and_usage"),
                dosage_and_administration=extract_first(item, "dosage_and_administration"),
                warnings=extract_first(item, "warnings"),
                do_not_use=extract_first(item, "do_not_use"),
                ask_doctor=extract_first(item, "ask_doctor"),
                stop_use=extract_first(item, "stop_use"),
                storage=extract_first(item, "storage_and_handling"),
            )

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise HTTPException(status_code=404, detail="Drug not found")
            raise HTTPException(status_code=e.response.status_code, detail="FDA API error")
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"FDA API unavailable: {str(e)}")


@app.get("/api/fda/drug-by-name")
async def get_fda_drug_by_name(name: str = Query(..., min_length=2)):
    """Get drug information by brand or generic name."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            # Search for the exact drug name
            url = f'{OPENFDA_BASE}?search=openfda.brand_name:"{name}"&limit=1'
            response = await client.get(url)

            # Try generic name if brand name not found
            if response.status_code == 404:
                url = f'{OPENFDA_BASE}?search=openfda.generic_name:"{name}"&limit=1'
                response = await client.get(url)

            if response.status_code == 404:
                raise HTTPException(status_code=404, detail=f"Drug '{name}' not found in FDA database")

            response.raise_for_status()
            data = response.json()

            results = data.get("results", [])
            if not results:
                raise HTTPException(status_code=404, detail=f"Drug '{name}' not found")

            item = results[0]
            openfda = item.get("openfda", {})

            return {
                "id": item.get("id"),
                "brand_name": openfda.get("brand_name", ["Unknown"])[0],
                "generic_name": openfda.get("generic_name", [None])[0],
                "manufacturer": openfda.get("manufacturer_name", [None])[0],
                "product_type": openfda.get("product_type", [None])[0],
                "route": openfda.get("route", [None])[0],
                "active_ingredient": extract_first(item, "active_ingredient"),
                "purpose": extract_first(item, "purpose"),
                "indications": extract_first(item, "indications_and_usage"),
                "dosage_and_administration": extract_first(item, "dosage_and_administration"),
                "warnings": extract_first(item, "warnings"),
                "do_not_use": extract_first(item, "do_not_use"),
                "ask_doctor": extract_first(item, "ask_doctor"),
                "stop_use": extract_first(item, "stop_use"),
                "storage": extract_first(item, "storage_and_handling"),
                "source": "openFDA",
                "disclaimer": "This information is from FDA drug labeling. Always consult a healthcare professional."
            }

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise HTTPException(status_code=404, detail=f"Drug '{name}' not found")
            raise HTTPException(status_code=e.response.status_code, detail="FDA API error")
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"FDA API unavailable: {str(e)}")


# Serve HTML frontend
@app.get("/", response_class=HTMLResponse)
def serve_frontend():
    """Serve the main HTML page."""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Medication Dosage Calculator - FDA Data</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
        }
        header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        header h1 {
            font-size: 2.2rem;
            margin-bottom: 10px;
        }
        header p {
            opacity: 0.9;
        }
        .badge {
            display: inline-block;
            background: rgba(255,255,255,0.2);
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            margin-top: 10px;
        }
        .card {
            background: white;
            border-radius: 16px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            margin-bottom: 20px;
        }
        .form-group {
            margin-bottom: 20px;
            position: relative;
        }
        label {
            display: block;
            font-weight: 600;
            margin-bottom: 8px;
            color: #333;
        }
        input[type="text"], input[type="number"] {
            width: 100%;
            padding: 14px 16px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        input:focus {
            outline: none;
            border-color: #2a5298;
        }
        .search-results {
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            background: white;
            border: 2px solid #e0e0e0;
            border-top: none;
            border-radius: 0 0 8px 8px;
            max-height: 300px;
            overflow-y: auto;
            z-index: 100;
            display: none;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        .search-results.show {
            display: block;
        }
        .search-result-item {
            padding: 12px 16px;
            cursor: pointer;
            border-bottom: 1px solid #eee;
        }
        .search-result-item:hover {
            background: #f5f7fa;
        }
        .search-result-item .brand {
            font-weight: 600;
            color: #333;
        }
        .search-result-item .generic {
            font-size: 13px;
            color: #666;
        }
        .search-result-item .manufacturer {
            font-size: 12px;
            color: #999;
        }
        button {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 18px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(30, 60, 114, 0.4);
        }
        button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        #drugInfo {
            display: none;
        }
        .info-section {
            margin-bottom: 20px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 12px;
            border-left: 4px solid #2a5298;
        }
        .info-section h3 {
            color: #1e3c72;
            margin-bottom: 12px;
            font-size: 1.1rem;
        }
        .info-section p {
            color: #444;
            line-height: 1.6;
            font-size: 14px;
        }
        .warning-section {
            background: #fff8e6;
            border-left-color: #f5a623;
        }
        .warning-section h3 {
            color: #b8860b;
        }
        .dosage-section {
            background: #e8f5e9;
            border-left-color: #4caf50;
        }
        .dosage-section h3 {
            color: #2e7d32;
        }
        .disclaimer {
            background: #ffebee;
            border: 1px solid #ef9a9a;
            border-radius: 8px;
            padding: 15px;
            margin-top: 20px;
        }
        .disclaimer h4 {
            color: #c62828;
            margin-bottom: 8px;
        }
        .disclaimer p {
            color: #c62828;
            font-size: 13px;
        }
        .loading {
            text-align: center;
            padding: 20px;
            color: #666;
        }
        .spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 2px solid #e0e0e0;
            border-top-color: #2a5298;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-right: 10px;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        .source-badge {
            display: inline-block;
            background: #2a5298;
            color: white;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 11px;
            margin-left: 10px;
            vertical-align: middle;
        }
        .drug-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #e0e0e0;
        }
        .drug-header h2 {
            color: #1e3c72;
        }
        .drug-header .meta {
            font-size: 14px;
            color: #666;
        }
        .error {
            background: #ffebee;
            color: #c62828;
            padding: 15px;
            border-radius: 8px;
            margin-top: 15px;
        }
        .row {
            display: flex;
            gap: 20px;
        }
        .row .form-group {
            flex: 1;
        }
        .patient-params {
            margin-top: 20px;
            padding: 20px;
            background: #f0f4f8;
            border-radius: 12px;
            border: 2px solid #d0d8e0;
        }
        .calculated-dosage {
            margin-top: 20px;
            padding: 20px;
            background: #e3f2fd;
            border-radius: 12px;
            border-left: 4px solid #1976d2;
        }
        .calculated-dosage h3 {
            color: #1565c0;
            margin-bottom: 15px;
        }
        .dose-result {
            background: white;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 10px;
        }
        .dose-result .dose-label {
            font-weight: 600;
            color: #333;
        }
        .dose-result .dose-value {
            font-size: 1.3em;
            color: #1565c0;
            font-weight: bold;
        }
        .dose-result .dose-note {
            font-size: 13px;
            color: #666;
            margin-top: 5px;
        }
        .age-warning {
            background: #fff3e0;
            border: 1px solid #ffb74d;
            border-radius: 8px;
            padding: 12px;
            margin-top: 10px;
            color: #e65100;
            font-size: 14px;
        }
        @media (max-width: 600px) {
            .row {
                flex-direction: column;
                gap: 0;
            }
            header h1 {
                font-size: 1.6rem;
            }
            .card {
                padding: 20px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Medication Dosage Information</h1>
            <p>Search FDA-approved drug labeling data</p>
            <span class="badge">Powered by openFDA API</span>
        </header>

        <div class="card">
            <div class="form-group">
                <label for="drugSearch">Search for a Medication</label>
                <input type="text" id="drugSearch" placeholder="Type drug name (e.g., Tylenol, Ibuprofen, Amoxicillin)..." autocomplete="off">
                <div id="searchResults" class="search-results"></div>
            </div>

            <div id="patientParams" class="patient-params" style="display: none;">
                <h3 style="margin-bottom: 15px; color: #1e3c72;">Patient Information</h3>
                <div class="row">
                    <div class="form-group">
                        <label for="patientAge">Age (years)</label>
                        <input type="number" id="patientAge" min="0" max="120" step="0.5" placeholder="e.g., 8">
                    </div>
                    <div class="form-group">
                        <label for="patientWeight">Weight (kg)</label>
                        <input type="number" id="patientWeight" min="1" max="300" step="0.1" placeholder="e.g., 25">
                    </div>
                </div>
                <button type="button" id="calculateBtn" onclick="calculateDosage()">Calculate Personalized Dosage</button>
            </div>

            <div id="calculatedDosage" class="calculated-dosage" style="display: none;"></div>

            <div class="disclaimer">
                <h4>Important Disclaimer</h4>
                <p>This information comes directly from FDA drug labeling (openFDA). It is for educational purposes only. Always consult a healthcare professional before taking any medication. Dosage recommendations may vary based on individual health conditions.</p>
            </div>
        </div>

        <div id="drugInfo" class="card">
            <div id="drugContent"></div>
        </div>
    </div>

    <script>
        const searchInput = document.getElementById('drugSearch');
        const searchResults = document.getElementById('searchResults');
        const drugInfo = document.getElementById('drugInfo');
        const drugContent = document.getElementById('drugContent');
        const patientParams = document.getElementById('patientParams');
        const calculatedDosage = document.getElementById('calculatedDosage');

        let searchTimeout = null;
        let selectedDrugId = null;
        let currentDrug = null;

        // Common weight-based dosing guidelines (mg/kg)
        const dosingGuidelines = {
            'ACETAMINOPHEN': { dosePerKg: 15, maxSingleDose: 1000, maxDailyDose: 75, unit: 'mg', frequency: 'every 4-6 hours', maxDailyTotal: 4000 },
            'IBUPROFEN': { dosePerKg: 10, maxSingleDose: 400, maxDailyDose: 40, unit: 'mg', frequency: 'every 6-8 hours', maxDailyTotal: 1200 },
            'AMOXICILLIN': { dosePerKg: 25, maxSingleDose: 500, maxDailyDose: 100, unit: 'mg', frequency: 'every 8 hours', maxDailyTotal: 3000 },
            'DIPHENHYDRAMINE': { dosePerKg: 1.25, maxSingleDose: 50, maxDailyDose: 5, unit: 'mg', frequency: 'every 6 hours', maxDailyTotal: 300 },
            'CETIRIZINE': { dosePerKg: null, fixedPediatric: 5, fixedAdult: 10, unit: 'mg', frequency: 'once daily', ageThreshold: 6 },
            'AZITHROMYCIN': { dosePerKg: 10, maxSingleDose: 500, maxDailyDose: 10, unit: 'mg', frequency: 'once daily', maxDailyTotal: 500 },
        };

        // Debounced search
        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.trim();

            if (searchTimeout) clearTimeout(searchTimeout);

            if (query.length < 2) {
                searchResults.classList.remove('show');
                return;
            }

            searchTimeout = setTimeout(() => searchDrugs(query), 300);
        });

        // Close search results on outside click
        document.addEventListener('click', (e) => {
            if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
                searchResults.classList.remove('show');
            }
        });

        async function searchDrugs(query) {
            searchResults.innerHTML = '<div class="loading"><span class="spinner"></span>Searching FDA database...</div>';
            searchResults.classList.add('show');

            try {
                const response = await fetch(`/api/fda/search?q=${encodeURIComponent(query)}`);
                const data = await response.json();

                if (data.results.length === 0) {
                    searchResults.innerHTML = '<div class="search-result-item">No medications found. Try a different name.</div>';
                    return;
                }

                searchResults.innerHTML = data.results.map(drug => `
                    <div class="search-result-item" data-id="${drug.id}">
                        <div class="brand">${drug.brand_name || 'Unknown Brand'}</div>
                        ${drug.generic_name ? `<div class="generic">${drug.generic_name}</div>` : ''}
                        ${drug.manufacturer ? `<div class="manufacturer">${drug.manufacturer}</div>` : ''}
                    </div>
                `).join('');

                // Add click handlers
                searchResults.querySelectorAll('.search-result-item').forEach(item => {
                    item.addEventListener('click', () => {
                        selectedDrugId = item.dataset.id;
                        searchInput.value = item.querySelector('.brand').textContent;
                        searchResults.classList.remove('show');
                        loadDrugInfo(selectedDrugId);
                    });
                });

            } catch (error) {
                searchResults.innerHTML = `<div class="search-result-item">Error searching: ${error.message}</div>`;
            }
        }

        async function loadDrugInfo(drugId) {
            drugContent.innerHTML = '<div class="loading"><span class="spinner"></span>Loading drug information from FDA...</div>';
            drugInfo.style.display = 'block';
            calculatedDosage.style.display = 'none';

            try {
                const response = await fetch(`/api/fda/drug/${drugId}`);
                if (!response.ok) throw new Error('Drug information not available');

                const drug = await response.json();
                currentDrug = drug;
                displayDrugInfo(drug);

                // Show patient parameters section
                patientParams.style.display = 'block';

            } catch (error) {
                drugContent.innerHTML = `<div class="error">${error.message}</div>`;
                patientParams.style.display = 'none';
            }
        }

        function calculateDosage() {
            const age = parseFloat(document.getElementById('patientAge').value);
            const weight = parseFloat(document.getElementById('patientWeight').value);

            if (!currentDrug) {
                alert('Please select a medication first');
                return;
            }

            if (isNaN(age) && isNaN(weight)) {
                alert('Please enter at least age or weight');
                return;
            }

            // Find matching guideline
            const genericName = (currentDrug.generic_name || '').toUpperCase();
            let guideline = null;

            for (const [drug, guide] of Object.entries(dosingGuidelines)) {
                if (genericName.includes(drug)) {
                    guideline = guide;
                    break;
                }
            }

            let html = '<h3>Personalized Dosage Calculation</h3>';

            if (guideline && !isNaN(weight) && weight > 0) {
                let calculatedDose;
                let maxSingle;
                let notes = [];

                if (guideline.dosePerKg) {
                    calculatedDose = guideline.dosePerKg * weight;
                    maxSingle = guideline.maxSingleDose;

                    // Apply max single dose limit
                    if (calculatedDose > maxSingle) {
                        notes.push(`Adjusted from ${calculatedDose.toFixed(1)} ${guideline.unit} to max single dose`);
                        calculatedDose = maxSingle;
                    }

                    const maxDaily = guideline.maxDailyDose * weight;
                    const maxDailyAdjusted = Math.min(maxDaily, guideline.maxDailyTotal);

                    html += `
                        <div class="dose-result">
                            <div class="dose-label">Recommended Single Dose</div>
                            <div class="dose-value">${calculatedDose.toFixed(1)} ${guideline.unit}</div>
                            <div class="dose-note">Based on ${guideline.dosePerKg} ${guideline.unit}/kg × ${weight} kg</div>
                        </div>
                        <div class="dose-result">
                            <div class="dose-label">Frequency</div>
                            <div class="dose-value">${guideline.frequency}</div>
                        </div>
                        <div class="dose-result">
                            <div class="dose-label">Maximum Daily Dose</div>
                            <div class="dose-value">${maxDailyAdjusted.toFixed(0)} ${guideline.unit}/day</div>
                            <div class="dose-note">Based on ${guideline.maxDailyDose} ${guideline.unit}/kg/day (max ${guideline.maxDailyTotal} ${guideline.unit})</div>
                        </div>
                    `;
                } else if (guideline.fixedPediatric && guideline.fixedAdult) {
                    // Fixed dose medications like cetirizine
                    const dose = (!isNaN(age) && age < guideline.ageThreshold) ? guideline.fixedPediatric : guideline.fixedAdult;
                    html += `
                        <div class="dose-result">
                            <div class="dose-label">Recommended Dose</div>
                            <div class="dose-value">${dose} ${guideline.unit}</div>
                            <div class="dose-note">${!isNaN(age) && age < guideline.ageThreshold ? 'Pediatric dose (under ' + guideline.ageThreshold + ' years)' : 'Adult dose'}</div>
                        </div>
                        <div class="dose-result">
                            <div class="dose-label">Frequency</div>
                            <div class="dose-value">${guideline.frequency}</div>
                        </div>
                    `;
                }

                if (notes.length > 0) {
                    html += `<div class="dose-note">${notes.join('. ')}</div>`;
                }
            } else {
                html += `
                    <div class="dose-result">
                        <div class="dose-note">Weight-based dosing calculation not available for this medication. Please refer to the FDA dosage information above.</div>
                    </div>
                `;
            }

            // Age-specific warnings
            if (!isNaN(age)) {
                if (age < 2) {
                    html += `<div class="age-warning"><strong>Warning:</strong> For children under 2 years, always consult a healthcare provider before administering any medication.</div>`;
                } else if (age < 12) {
                    html += `<div class="age-warning"><strong>Note:</strong> Pediatric dosing shown. Always verify with the FDA label information and consult a healthcare provider.</div>`;
                }
            }

            calculatedDosage.innerHTML = html;
            calculatedDosage.style.display = 'block';
            calculatedDosage.scrollIntoView({ behavior: 'smooth' });
        }

        function displayDrugInfo(drug) {
            let html = `
                <div class="drug-header">
                    <div>
                        <h2>${drug.brand_name}<span class="source-badge">FDA Data</span></h2>
                        ${drug.generic_name ? `<div class="meta"><strong>Generic:</strong> ${drug.generic_name}</div>` : ''}
                        ${drug.manufacturer ? `<div class="meta"><strong>Manufacturer:</strong> ${drug.manufacturer}</div>` : ''}
                        ${drug.route ? `<div class="meta"><strong>Route:</strong> ${drug.route}</div>` : ''}
                    </div>
                </div>
            `;

            if (drug.active_ingredient) {
                html += `
                    <div class="info-section">
                        <h3>Active Ingredient</h3>
                        <p>${drug.active_ingredient}</p>
                    </div>
                `;
            }

            if (drug.purpose) {
                html += `
                    <div class="info-section">
                        <h3>Purpose</h3>
                        <p>${drug.purpose}</p>
                    </div>
                `;
            }

            if (drug.indications) {
                html += `
                    <div class="info-section">
                        <h3>Uses / Indications</h3>
                        <p>${drug.indications}</p>
                    </div>
                `;
            }

            if (drug.dosage_and_administration) {
                html += `
                    <div class="info-section dosage-section">
                        <h3>Dosage & Administration</h3>
                        <p>${drug.dosage_and_administration}</p>
                    </div>
                `;
            }

            if (drug.warnings) {
                html += `
                    <div class="info-section warning-section">
                        <h3>Warnings</h3>
                        <p>${drug.warnings}</p>
                    </div>
                `;
            }

            if (drug.do_not_use) {
                html += `
                    <div class="info-section warning-section">
                        <h3>Do Not Use</h3>
                        <p>${drug.do_not_use}</p>
                    </div>
                `;
            }

            if (drug.ask_doctor) {
                html += `
                    <div class="info-section">
                        <h3>Ask a Doctor Before Use</h3>
                        <p>${drug.ask_doctor}</p>
                    </div>
                `;
            }

            if (drug.stop_use) {
                html += `
                    <div class="info-section warning-section">
                        <h3>Stop Use And Ask a Doctor If</h3>
                        <p>${drug.stop_use}</p>
                    </div>
                `;
            }

            if (drug.storage) {
                html += `
                    <div class="info-section">
                        <h3>Storage</h3>
                        <p>${drug.storage}</p>
                    </div>
                `;
            }

            drugContent.innerHTML = html;
            drugInfo.scrollIntoView({ behavior: 'smooth' });
        }
    </script>
</body>
</html>
"""


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
