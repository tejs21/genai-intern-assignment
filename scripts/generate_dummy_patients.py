import json, os, random, datetime
os.makedirs("data/patients", exist_ok=True)

names = ["John Smith","Rohit Kumar","Anita Sharma","Priya Patel","Arjun Rao","Fatima Khan","Liu Wei","Carlos Diaz","Maria Silva","Asha Nair"]
diagnoses = ["Chronic Kidney Disease Stage 3","Acute Kidney Injury","Nephrotic Syndrome","Hypertensive Nephrosclerosis"]
meds = [["Lisinopril 10mg daily","Furosemide 20mg daily"],["Amlodipine 5mg daily"],["Prednisone 20mg daily"]]

for i in range(1,31):
    p = {
        "patient_id": f"P{i:03d}",
        "patient_name": random.choice(names)+" "+str(i),
        "discharge_date": (datetime.date(2024,1,1) + datetime.timedelta(days=random.randint(0,700))).isoformat(),
        "primary_diagnosis": random.choice(diagnoses),
        "medications": random.choice(meds),
        "dietary_restrictions": "Low sodium, fluid restriction 1.5L/day",
        "follow_up": "Nephrology clinic in 2 weeks",
        "warning_signs": "Swelling, shortness of breath, decreased urine output",
        "discharge_instructions": "Monitor BP daily; weigh yourself daily"
    }
    with open(f"data/patients/{p['patient_id']}.json","w") as f:
        json.dump(p, f, indent=2)
print("Generated patients:", len(os.listdir("data/patients")))
