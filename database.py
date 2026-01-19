import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "medications.db"


def get_connection():
    """Get a database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize the database schema."""
    conn = get_connection()
    cursor = conn.cursor()

    # Medications table - stores basic drug info
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS medications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            generic_name TEXT,
            drug_class TEXT,
            description TEXT,
            warnings TEXT
        )
    """)

    # Dosage forms table - tablets, liquid, etc.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dosage_forms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            medication_id INTEGER NOT NULL,
            form TEXT NOT NULL,
            strength TEXT NOT NULL,
            strength_unit TEXT NOT NULL,
            FOREIGN KEY (medication_id) REFERENCES medications(id)
        )
    """)

    # Dosage guidelines table - age/weight based dosing
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dosage_guidelines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            medication_id INTEGER NOT NULL,
            indication TEXT NOT NULL,
            age_group TEXT,
            min_age_years REAL,
            max_age_years REAL,
            min_weight_kg REAL,
            max_weight_kg REAL,
            dose_per_kg REAL,
            dose_unit TEXT,
            min_dose REAL,
            max_dose REAL,
            frequency TEXT,
            max_daily_dose REAL,
            route TEXT,
            notes TEXT,
            FOREIGN KEY (medication_id) REFERENCES medications(id)
        )
    """)

    conn.commit()
    conn.close()


def seed_data():
    """Seed the database with common medication data."""
    conn = get_connection()
    cursor = conn.cursor()

    # Check if data already exists
    cursor.execute("SELECT COUNT(*) FROM medications")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return

    # Common medications with dosage info based on standard guidelines
    medications = [
        {
            "name": "Acetaminophen (Tylenol)",
            "generic_name": "Acetaminophen",
            "drug_class": "Analgesic/Antipyretic",
            "description": "Pain reliever and fever reducer",
            "warnings": "Do not exceed 4000mg/day in adults. Avoid in liver disease."
        },
        {
            "name": "Ibuprofen (Advil/Motrin)",
            "generic_name": "Ibuprofen",
            "drug_class": "NSAID",
            "description": "Pain reliever, fever reducer, anti-inflammatory",
            "warnings": "Take with food. Avoid in kidney disease, GI bleeding, or aspirin allergy."
        },
        {
            "name": "Amoxicillin",
            "generic_name": "Amoxicillin",
            "drug_class": "Antibiotic (Penicillin)",
            "description": "Antibiotic for bacterial infections",
            "warnings": "Check for penicillin allergy. Complete full course."
        },
        {
            "name": "Diphenhydramine (Benadryl)",
            "generic_name": "Diphenhydramine",
            "drug_class": "Antihistamine",
            "description": "Allergy relief, sleep aid",
            "warnings": "Causes drowsiness. Not for children under 2 without doctor advice."
        },
        {
            "name": "Cetirizine (Zyrtec)",
            "generic_name": "Cetirizine",
            "drug_class": "Antihistamine",
            "description": "Non-drowsy allergy relief",
            "warnings": "May cause mild drowsiness in some people."
        },
        {
            "name": "Omeprazole (Prilosec)",
            "generic_name": "Omeprazole",
            "drug_class": "Proton Pump Inhibitor",
            "description": "Reduces stomach acid for heartburn/GERD",
            "warnings": "Not for immediate heartburn relief. Long-term use requires monitoring."
        },
        {
            "name": "Metformin",
            "generic_name": "Metformin",
            "drug_class": "Antidiabetic",
            "description": "Blood sugar control for Type 2 diabetes",
            "warnings": "Take with meals. Monitor kidney function. Risk of lactic acidosis."
        },
        {
            "name": "Lisinopril",
            "generic_name": "Lisinopril",
            "drug_class": "ACE Inhibitor",
            "description": "Blood pressure medication",
            "warnings": "May cause dry cough. Avoid in pregnancy. Monitor potassium levels."
        },
    ]

    for med in medications:
        cursor.execute("""
            INSERT INTO medications (name, generic_name, drug_class, description, warnings)
            VALUES (?, ?, ?, ?, ?)
        """, (med["name"], med["generic_name"], med["drug_class"],
              med["description"], med["warnings"]))

    # Get medication IDs
    cursor.execute("SELECT id, name FROM medications")
    med_ids = {row["name"]: row["id"] for row in cursor.fetchall()}

    # Dosage forms
    forms = [
        # Acetaminophen
        (med_ids["Acetaminophen (Tylenol)"], "Tablet", "325", "mg"),
        (med_ids["Acetaminophen (Tylenol)"], "Tablet", "500", "mg"),
        (med_ids["Acetaminophen (Tylenol)"], "Liquid", "160", "mg/5mL"),
        # Ibuprofen
        (med_ids["Ibuprofen (Advil/Motrin)"], "Tablet", "200", "mg"),
        (med_ids["Ibuprofen (Advil/Motrin)"], "Tablet", "400", "mg"),
        (med_ids["Ibuprofen (Advil/Motrin)"], "Liquid", "100", "mg/5mL"),
        # Amoxicillin
        (med_ids["Amoxicillin"], "Capsule", "250", "mg"),
        (med_ids["Amoxicillin"], "Capsule", "500", "mg"),
        (med_ids["Amoxicillin"], "Liquid", "250", "mg/5mL"),
        # Diphenhydramine
        (med_ids["Diphenhydramine (Benadryl)"], "Tablet", "25", "mg"),
        (med_ids["Diphenhydramine (Benadryl)"], "Liquid", "12.5", "mg/5mL"),
        # Cetirizine
        (med_ids["Cetirizine (Zyrtec)"], "Tablet", "10", "mg"),
        (med_ids["Cetirizine (Zyrtec)"], "Liquid", "5", "mg/5mL"),
        # Omeprazole
        (med_ids["Omeprazole (Prilosec)"], "Capsule", "20", "mg"),
        (med_ids["Omeprazole (Prilosec)"], "Capsule", "40", "mg"),
        # Metformin
        (med_ids["Metformin"], "Tablet", "500", "mg"),
        (med_ids["Metformin"], "Tablet", "850", "mg"),
        (med_ids["Metformin"], "Tablet", "1000", "mg"),
        # Lisinopril
        (med_ids["Lisinopril"], "Tablet", "5", "mg"),
        (med_ids["Lisinopril"], "Tablet", "10", "mg"),
        (med_ids["Lisinopril"], "Tablet", "20", "mg"),
    ]

    for form in forms:
        cursor.execute("""
            INSERT INTO dosage_forms (medication_id, form, strength, strength_unit)
            VALUES (?, ?, ?, ?)
        """, form)

    # Dosage guidelines (based on standard medical references)
    guidelines = [
        # Acetaminophen - Adults
        (med_ids["Acetaminophen (Tylenol)"], "Pain/Fever", "Adult", 18, 999,
         None, None, None, "mg", 325, 1000, "Every 4-6 hours", 4000, "Oral",
         "Do not exceed 4000mg in 24 hours"),
        # Acetaminophen - Children (weight-based)
        (med_ids["Acetaminophen (Tylenol)"], "Pain/Fever", "Pediatric", 2, 12,
         10, 50, 15, "mg/kg", 160, 500, "Every 4-6 hours", 75, "Oral",
         "Max 75mg/kg/day, not to exceed 4000mg"),
        # Ibuprofen - Adults
        (med_ids["Ibuprofen (Advil/Motrin)"], "Pain/Fever/Inflammation", "Adult", 18, 999,
         None, None, None, "mg", 200, 400, "Every 4-6 hours", 1200, "Oral",
         "Take with food. Max 1200mg/day OTC, 3200mg/day Rx"),
        # Ibuprofen - Children
        (med_ids["Ibuprofen (Advil/Motrin)"], "Pain/Fever", "Pediatric", 0.5, 12,
         5, 40, 10, "mg/kg", 50, 400, "Every 6-8 hours", 40, "Oral",
         "Max 40mg/kg/day"),
        # Amoxicillin - Adults
        (med_ids["Amoxicillin"], "Bacterial Infection", "Adult", 18, 999,
         None, None, None, "mg", 250, 500, "Every 8 hours", 3000, "Oral",
         "Complete full course of antibiotics"),
        # Amoxicillin - Children
        (med_ids["Amoxicillin"], "Bacterial Infection", "Pediatric", 0, 12,
         3, 40, 25, "mg/kg", 125, 500, "Every 8 hours", 100, "Oral",
         "Standard dose 25-50mg/kg/day divided q8h"),
        # Diphenhydramine - Adults
        (med_ids["Diphenhydramine (Benadryl)"], "Allergy/Sleep", "Adult", 12, 999,
         None, None, None, "mg", 25, 50, "Every 4-6 hours", 300, "Oral",
         "Causes drowsiness"),
        # Diphenhydramine - Children
        (med_ids["Diphenhydramine (Benadryl)"], "Allergy", "Pediatric", 6, 12,
         20, 40, 1.25, "mg/kg", 12.5, 25, "Every 4-6 hours", 150, "Oral",
         "Not recommended under 6 years without doctor advice"),
        # Cetirizine - Adults
        (med_ids["Cetirizine (Zyrtec)"], "Allergy", "Adult", 12, 999,
         None, None, None, "mg", 10, 10, "Once daily", 10, "Oral",
         "May take 5mg if drowsy"),
        # Cetirizine - Children
        (med_ids["Cetirizine (Zyrtec)"], "Allergy", "Pediatric", 2, 6,
         10, 25, None, "mg", 2.5, 5, "Once daily", 5, "Oral",
         "2.5mg for ages 2-5"),
        # Omeprazole - Adults
        (med_ids["Omeprazole (Prilosec)"], "GERD/Heartburn", "Adult", 18, 999,
         None, None, None, "mg", 20, 40, "Once daily", 40, "Oral",
         "Take 30-60 minutes before meal"),
        # Metformin - Adults
        (med_ids["Metformin"], "Type 2 Diabetes", "Adult", 18, 999,
         None, None, None, "mg", 500, 1000, "Twice daily with meals", 2550, "Oral",
         "Start low, titrate slowly. Max 2550mg/day"),
        # Lisinopril - Adults
        (med_ids["Lisinopril"], "Hypertension", "Adult", 18, 999,
         None, None, None, "mg", 5, 10, "Once daily", 80, "Oral",
         "Start 5-10mg, titrate as needed. Max 80mg/day"),
    ]

    for g in guidelines:
        cursor.execute("""
            INSERT INTO dosage_guidelines
            (medication_id, indication, age_group, min_age_years, max_age_years,
             min_weight_kg, max_weight_kg, dose_per_kg, dose_unit, min_dose, max_dose,
             frequency, max_daily_dose, route, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, g)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    seed_data()
    print("Database initialized and seeded successfully!")
