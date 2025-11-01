import os, logging, dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
from patient_tool import find_patient_by_name, find_patient_by_id
from logging_config import configure_logging
from rag import retrieve, answer_with_llm, rag_confidence
from web_search import web_search

# Load environment variables from .env file
dotenv.load_dotenv()

# Configure project-wide logging setup
configure_logging()
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Allow cross-origin requests (for Streamlit frontend)

# -----------------------------
# Receptionist Agent API
# -----------------------------
@app.route("/receptionist", methods=["POST"])
def receptionist():
    """
    Handles patient identification by name or ID.
    Fetches patient record and returns discharge summary.
    """
    payload = request.get_json() or {}
    message = payload.get("message", "").strip()
    patient_name = payload.get("patient_name") or payload.get("message")
    logger.info("Receptionist received message: %s", message)

    # Validate input
    if not patient_name or len(patient_name.strip()) < 2:
        return jsonify({
            "role": "receptionist",
            "text": "Hello! Please tell me your full name or patient ID to find your discharge summary."
        })

    # --- Search by Patient ID (e.g., P001) ---
    candidate = patient_name.strip()
    if candidate.upper().startswith("P") and candidate[1:].isdigit():
        pid = candidate.upper()
        p = find_patient_by_id(pid)
        if not p:
            return jsonify({
                "role": "receptionist",
                "text": f"No patient found with ID {pid}. Please check your ID or provide full name."
            })

        # Build patient summary response
        text = (
            f"Found patient: {p['patient_name']} (ID: {p['patient_id']}). "
            f"Primary diagnosis: {p['primary_diagnosis']}. "
            f"Discharged on {p['discharge_date']}. "
            f"Follow-up: {p.get('follow_up')}"
        )
        return jsonify({"role": "receptionist", "text": text, "patient": p})

    # --- Search by Patient Name ---
    matches = find_patient_by_name(patient_name)
    if len(matches) == 0:
        return jsonify({
            "role": "receptionist",
            "text": "No patient found matching that name. Please check spelling or provide patient ID."
        })
    if len(matches) > 1:
        options = [{"patient_id": m["patient_id"], "patient_name": m["patient_name"]} for m in matches]
        return jsonify({
            "role": "receptionist",
            "text": "Multiple matches found. Please reply with patient ID to select one.",
            "matches": options
        })

    # Single match found
    p = matches[0]
    text = (
        f"Found patient: {p['patient_name']} (ID: {p['patient_id']}). "
        f"Primary diagnosis: {p['primary_diagnosis']}. "
        f"Discharged on {p['discharge_date']}."
    )
    return jsonify({"role": "receptionist", "text": text, "patient": p})

# -----------------------------
# Clinical Agent API
# -----------------------------
@app.route("/clinical", methods=["POST"])
def clinical():
    """
    Handles clinical questions from the patient.
    Performs retrieval using RAG and generates an answer.
    """
    payload = request.get_json() or {}
    patient_id = payload.get("patient_id")
    question = payload.get("question") or payload.get("message") or ""

    # Validate inputs
    if not patient_id:
        return jsonify({"error": "patient_id required"}), 400
    patient = find_patient_by_id(patient_id)
    if not patient:
        return jsonify({"error": "patient not found"}), 404

    logger.info("Clinical: patient=%s question=%s", patient_id, question)

    # Retrieve top relevant chunks using embeddings
    contexts = retrieve(question, top_k=3)
    top_score = rag_confidence(contexts)

    # Trigger web search if RAG confidence is low
    web_results = []
    used_web = False
    if top_score < 0.14:
        logger.info("Low RAG confidence (%.4f). Triggering web search.", top_score)
        web_results = web_search(question, max_results=3)
        used_web = bool(web_results)

    # Generate final answer using LLM (if key available) or fallback text
    answer = answer_with_llm(
        patient_summary=f"Name: {patient['patient_name']}. "
                        f"Primary diagnosis: {patient.get('primary_diagnosis')}. "
                        f"Discharge instructions: {patient.get('discharge_instructions')}",
        question=question,
        contexts=contexts,
        web_results=web_results
    )

    # Build JSON-serializable source list
    sources = []
    for c in contexts:
        src = {
            "id": int(c.get("id")),
            "snippet": c.get("document", "")[:400],
            "score": float(c.get("score", 0.0))
        }
        sources.append(src)

    # Append web results if used
    if used_web:
        for w in web_results:
            sources.append({
                "id": None,
                "snippet": w.get("snippet"),
                "url": w.get("url"),
                "title": w.get("title"),
                "source": "web"
            })

    # Utility to convert NumPy types for safe JSON serialization
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

    payload = {
        "role": "clinical",
        "text": answer,
        "sources": make_serializable(sources)
    }

    logger.info(
        "Clinical answered patient=%s, sources=%s, used_web=%s",
        patient_id, [s.get("id") for s in sources], used_web
    )
    return jsonify(payload)

# -----------------------------
# Utility Endpoints
# -----------------------------
@app.route("/health", methods=["GET"])
def health():
    """Simple health check endpoint."""
    return jsonify({"status": "ok"})


@app.route("/config", methods=["GET"])
def config():
    """Return configuration info for frontend (like OpenAI status)."""
    openai_enabled = bool(os.getenv("OPENAI_API_KEY"))
    model = os.getenv("MODEL_NAME", "")
    return jsonify({"openai_configured": openai_enabled, "model": model})


# -----------------------------
# App Runner
# -----------------------------
if __name__ == "__main__":
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    port = int(os.getenv("FLASK_PORT", 5000))
    # Run in debug mode for local development
    app.run(host=host, port=port, debug=True)
