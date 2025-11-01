import os, pickle, numpy as np, logging
from sentence_transformers import SentenceTransformer
import dotenv
dotenv.load_dotenv()

logger = logging.getLogger(__name__)

OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-3.5-turbo")
REF_EMB_PATH = "data/reference_embeddings.pkl"

logger.info("Loading sentence-transformer model...")
model = SentenceTransformer("all-MiniLM-L6-v2")

if not os.path.exists(REF_EMB_PATH):
    raise FileNotFoundError(f"{REF_EMB_PATH} not found. Run scripts/ingest_reference.py first.")

logger.info("Loading reference embeddings...")
data = pickle.load(open(REF_EMB_PATH, "rb"))
chunks = data["chunks"]
embeddings = np.array(data["embeddings"])

if OPENAI_KEY:
    import openai
    openai.api_key = OPENAI_KEY
    logger.info(f"OpenAI enabled, model={MODEL_NAME}")
else:
    openai = None
    logger.info("OpenAI key not set — using fallback mode.")

def retrieve(query, top_k=3):
    q_emb = model.encode([query])[0]
    sims = np.dot(embeddings, q_emb) / (np.linalg.norm(embeddings, axis=1) * np.linalg.norm(q_emb))
    sims = np.nan_to_num(sims)
    top_idx = np.argsort(sims)[::-1][:top_k]
    results = [{"id": int(i), "document": chunks[int(i)], "score": float(sims[int(i)])} for i in top_idx]
    return results

def rag_confidence(contexts, min_score=0.15):
    """
    Simple heuristic: if the top score is below min_score, consider low confidence.
    Adjust min_score as needed for your data.
    """
    if not contexts:
        return 0.0
    top_score = contexts[0].get("score", 0.0)
    return float(top_score)

def compose_prompt(patient_summary, question, contexts, web_results=None):
    ctx_text = ""
    for i, c in enumerate(contexts, start=1):
        snippet = c.get("document", "")[:1200]
        ctx_text += f"[Source {i} | chunk:{c.get('id')} | score:{c.get('score'):.4f}]\n{snippet}\n\n"
    web_block = ""
    if web_results:
        for i, w in enumerate(web_results, start=1):
            web_block += f"[Web {i}] {w.get('title')} - {w.get('url')}\n{w.get('snippet')}\n\n"

    prompt = f"""
You are a clinical assistant. Answer the question using ONLY the provided reference contexts. If the answer is not in the references, use the web search results (clearly tag them as [Web N]) and indicate that they're web sources. Always include citations.

Patient summary:
{patient_summary}

Question:
{question}

Reference Contexts:
{ctx_text}

Web Search Results:
{web_block}

Answer concisely and include citations. End with: "Disclaimer: This is NOT medical advice. Consult a clinician."
"""
    return prompt

def answer_with_llm(patient_summary, question, contexts, web_results=None):
    prompt = compose_prompt(patient_summary, question, contexts, web_results)
    logger.info("LLM prompt length: %d chars; contexts=%d; web=%d", len(prompt), len(contexts), len(web_results) if web_results else 0)
    if openai:
        try:
            messages = [
                {"role":"system","content":"You are a concise clinical assistant. Use only the provided sources."},
                {"role":"user","content":prompt}
            ]
            resp = openai.ChatCompletion.create(
                model=MODEL_NAME,
                messages=messages,
                max_tokens=500,
                temperature=0.0,
            )
            return resp["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.exception("OpenAI call failed: %s", e)

    out = ""
    if contexts:
        out += "Top reference excerpts:\n\n"
        for i, c in enumerate(contexts, start=1):
            out += f"[Source {i}] (score={c.get('score'):.4f}) {c.get('document')[:400]}...\n\n"
    if web_results:
        out += "Web search results:\n\n"
        for i, w in enumerate(web_results, start=1):
            out += f"[Web {i}] {w.get('title')} - {w.get('url')}\n{w.get('snippet')}\n\n"
    if not contexts and not web_results:
        out = "No information found in references or web search. Recommend follow-up with a clinician.\n\n"
    out += "Disclaimer: This is NOT medical advice. Consult a clinician."
    return out
