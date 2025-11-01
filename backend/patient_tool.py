import os, json, logging

logger = logging.getLogger(__name__)

# Path to the directory containing dummy patient JSON files
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "patients")

# -----------------------------
# Utility: List all available patients
# -----------------------------
def list_patients():
    """
    Loads all patient JSON files from the data/patients directory.
    Returns a list of patient records (as dictionaries).
    """
    res = []
    if not os.path.exists(DATA_DIR):
        return res

    # Iterate through all .json files and load patient data
    for fn in sorted(os.listdir(DATA_DIR)):
        if fn.endswith(".json"):
            with open(os.path.join(DATA_DIR, fn)) as f:
                res.append(json.load(f))
    return res


# -----------------------------
# Search: Find patient(s) by name
# -----------------------------
def find_patient_by_name(name):
    """
    Performs a case-insensitive name search in the patient dataset.
    Returns a list of matching patient records.
    """
    name = (name or "").strip().lower()
    matches = []

    for p in list_patients():
        if name in p.get("patient_name", "").lower():
            matches.append(p)

    logger.info(f"find_patient_by_name name={name} found={len(matches)}")
    return matches


# -----------------------------
# Search: Find patient by ID
# -----------------------------
def find_patient_by_id(pid):
    """
    Searches for a patient using their unique patient ID (e.g., P001).
    Returns the matching patient record, or None if not found.
    """
    for p in list_patients():
        if p.get("patient_id") == pid:
            return p
    return None
