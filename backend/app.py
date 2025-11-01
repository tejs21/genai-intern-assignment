import os, logging, dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
from patient_tool import find_patient_by_name, find_patient_by_id
from logging_config import configure_logging
from rag import retrieve, answer_with_llm, rag_confidence
from web_search import web_search

dotenv.load_dotenv()
configure_logging()
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

@app.route("/receptionist", methods=["POST"])
def receptionist():
    payload = request.get_json() or {}
    message = payload.get("message","").strip()
    patient_name = payload.get("patient_name") or payload.get("message")
    logger.info("Receptionist received message: %s", message)

    if not patient_name or len(patient_name.strip())<2:
        return jsonify({"role":"receptionist","text":"Hello! Please tell me your full name or patient ID to find your discharge summary."})

    candidate = patient_name.strip()
    if candidate.upper().startswith("P") and candidate[1:].isdigit():
        pid = candidate.upper()
        p = find_patient_by_id(pid)
        if not p:
            return jsonify({"role":"receptionist","text":f"No patient found with ID {pid}. Please check your ID or provide full name."})
        text = f"Found patient: {p['patient_name']} (ID: {p['patient_id']}). Primary diagnosis: {p['primary_diagnosis']}. Discharged on {p['discharge_date']}. Follow-up: {p.get('follow_up')}"
        return jsonify({"role":"receptionist","text":text,"patient":p})

    matches = find_patient_by_name(patient_name)
    if len(matches) == 0:
        return jsonify({"role":"receptionist","text":"No patient found matching that name. Please check spelling or provide patient ID."})
    if len(matches) > 1:
        options = [{"patient_id":m["patient_id"], "patient_name":m["patient_name"]} for m in matches]
        return jsonify({"role":"receptionist","text":"Multiple matches found. Please reply with patient ID to select one.", "matches": options})
    p = matches[0]
    text = f"Found patient: {p['patient_name']} (ID: {p['patient_id']}). Primary diagnosis: {p['primary_diagnosis']}. Discharged on {p['discharge_date']}."
    return jsonify({"role":"receptionist","text":text,"patient":p})

@app.route("/clinical", methods=["POST"])
def clinical():
    payload = request.get_json() or {}
    patient_id = payload.get("patient_id")
    question = payload.get("question") or payload.get("message") or ""
    if not patient_id:
        return jsonify({"error":"patient_id required"}), 400
    patient = find_patient_by_id(patient_id)
    if not patient:
        return jsonify({"error":"patient not found"}), 404

    logger.info("Clinical: patient=%s question=%s", patient_id, question)
    contexts = retrieve(question, top_k=3)
    top_score = rag_confidence(contexts)
    web_results = []
    used_web = False
    if top_score < 0.14:
        logger.info("Low RAG confidence (%.4f). Triggering web search.", top_score)
        web_results = web_search(question, max_results=3)
        used_web = True if web_results else False

    answer = answer_with_llm(
        patient_summary=f"Name: {patient['patient_name']}. Primary diagnosis: {patient.get('primary_diagnosis')}. Discharge instructions: {patient.get('discharge_instructions')}",
        question=question,
        contexts=contexts,
        web_results=web_results
    )

    sources = []
    for c in contexts:
        src = {"id": int(c.get("id")), "snippet": c.get("document","")[:400], "score": float(c.get("score", 0.0))}
        sources.append(src)
    if used_web:
        for w in web_results:
            sources.append({"id": None, "snippet": w.get("snippet"), "url": w.get("url"), "title": w.get("title"), "source": "web"})

    def make_serializable(obj):
        import numpy as np
        if isinstance(obj, (np.integer,)):
            return int(obj)
        elif isinstance(obj, (np.floating,)):
            return float(obj)
        elif isinstance(obj, (np.ndarray,)):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [make_serializable(i) for i in obj]
        else:
            return obj

    payload = {"role":"clinical", "text": answer, "sources": make_serializable(sources)}
    logger.info("Clinical answered patient=%s, sources=%s, used_web=%s", patient_id, [s.get("id") for s in sources], used_web)
    return jsonify(payload)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status":"ok"})

@app.route("/config", methods=["GET"])
def config():
    openai_enabled = bool(os.getenv("OPENAI_API_KEY"))
    model = os.getenv("MODEL_NAME", "")
    return jsonify({"openai_configured": openai_enabled, "model": model})

if __name__ == "__main__":
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    port = int(os.getenv("FLASK_PORT", 5000))
    app.run(host=host, port=port, debug=True)
