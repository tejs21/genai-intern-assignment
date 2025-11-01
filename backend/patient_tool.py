import os, json, logging

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "patients")

def list_patients():
    res = []
    if not os.path.exists(DATA_DIR):
        return res
    for fn in sorted(os.listdir(DATA_DIR)):
        if fn.endswith(".json"):
            with open(os.path.join(DATA_DIR, fn)) as f:
                res.append(json.load(f))
    return res

def find_patient_by_name(name):
    name = (name or "").strip().lower()
    matches = []
    for p in list_patients():
        if name in p.get("patient_name", "").lower():
            matches.append(p)
    logger.info(f"find_patient_by_name name={name} found={len(matches)}")
    return matches

def find_patient_by_id(pid):
    for p in list_patients():
        if p.get("patient_id") == pid:
            return p
    return None
