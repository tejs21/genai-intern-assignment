"""
scripts/generate_dummy_patients.py
----------------------------------
Utility script to generate 30 dummy post-discharge patient reports.

Each patient record is saved as a JSON file under `data/patients/`.
Used by the Receptionist Agent for patient identification and retrieval.
"""

import json
import os
import random
import datetime

# Ensure output directory exists
os.makedirs("data/patients", exist_ok=True)

# Sample data pools
names = [
    "John Smith", "Rohit Kumar", "Anita Sharma", "Priya Patel", "Arjun Rao",
    "Fatima Khan", "Liu Wei", "Carlos Diaz", "Maria Silva", "Asha Nair"
]
diagnoses = [
    "Chronic Kidney Disease Stage 3",
    "Acute Kidney Injury",
    "Nephrotic Syndrome",
    "Hypertensive Nephrosclerosis"
]
medications_list = [
    ["Lisinopril 10mg daily", "Furosemide 20mg daily"],
    ["Amlodipine 5mg daily"],
    ["Prednisone 20mg daily"]
]

# Generate 30 dummy patient reports
for i in range(1, 31):
    patient_data = {
        "patient_id": f"P{i:03d}",
        "patient_name": f"{random.choice(names)} {i}",
        "discharge_date": (
            datetime.date(2024, 1, 1) +
            datetime.timedelta(days=random.randint(0, 700))
        ).isoformat(),
        "primary_diagnosis": random.choice(diagnoses),
        "medications": random.choice(medications_list),
        "dietary_restrictions": "Low sodium, fluid restriction 1.5L/day",
        "follow_up": "Nephrology clinic in 2 weeks",
        "warning_signs": "Swelling, shortness of breath, decreased urine output",
        "discharge_instructions": "Monitor blood pressure daily; weigh yourself daily."
    }

    # Write JSON file for each patient
    file_path = f"data/patients/{patient_data['patient_id']}.json"
    with open(file_path, "w") as f:
        json.dump(patient_data, f, indent=2)

print(f"Generated {len(os.listdir('data/patients'))} dummy patient files in data/patients/")
