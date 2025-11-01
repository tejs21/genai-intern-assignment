"""
Reference Ingestion Script
--------------------------
This script processes the nephrology reference PDF, splits it into text chunks,
and generates vector embeddings for Retrieval-Augmented Generation (RAG).

Output:
    - data/reference_embeddings.pkl
      (contains {'chunks': [...], 'embeddings': [...]})

Usage:
    python scripts/ingest_reference.py
"""

import os
import pickle
import fitz  # PyMuPDF for PDF parsing
import numpy as np
from tqdm import tqdm
from sentence_transformers import SentenceTransformer

# -------------------------------------------------------
# Paths and Model Setup
# -------------------------------------------------------
REF_PATH = "data/reference/comprehensive-clinical-nephrology.pdf"
OUT_PATH = "data/reference_embeddings.pkl"
os.makedirs("data", exist_ok=True)

# Load embedding model (lightweight and fast)
model = SentenceTransformer("all-MiniLM-L6-v2")

# -------------------------------------------------------
# Helper Function — Chunking Large Text
# -------------------------------------------------------
def chunk_text(text, size=900, overlap=200):
    """
    Split large text into overlapping chunks for semantic retrieval.
    Args:
        text (str): Full input text.
        size (int): Maximum characters per chunk.
        overlap (int): Number of overlapping characters between chunks.
    Returns:
        List[str]: Text chunks ready for embedding.
    """
    chunks, start = [], 0
    while start < len(text):
        chunk = text[start:start + size]
        if len(chunk.strip()) > 50:  # Skip very short or empty fragments
            chunks.append(chunk.strip())
        start += size - overlap
    return chunks

# -------------------------------------------------------
# PDF Reading and Chunk Embedding
# -------------------------------------------------------
print(f"Opening reference PDF: {REF_PATH}")
doc = fitz.open(REF_PATH)
print(f"Total pages found: {len(doc)}")

BATCH_SIZE = 20
all_chunks, all_embeddings = [], []

# Process PDF in batches for efficiency
for i in range(0, len(doc), BATCH_SIZE):
    batch_text = ""
    for j in range(i, min(i + BATCH_SIZE, len(doc))):
        page = doc.load_page(j)
        batch_text += page.get_text("text") + "\n"

    chunks = chunk_text(batch_text)
    if not chunks:
        continue

    embeddings = model.encode(chunks, show_progress_bar=False)
    all_chunks.extend(chunks)
    all_embeddings.append(embeddings)
    print(f"Processed pages {i+1}-{min(i+BATCH_SIZE, len(doc))} | {len(chunks)} chunks")

doc.close()

# -------------------------------------------------------
# Save Processed Embeddings
# -------------------------------------------------------
all_embeddings = np.vstack(all_embeddings)
pickle.dump({"chunks": all_chunks, "embeddings": all_embeddings}, open(OUT_PATH, "wb"))

print(f"\nEmbeddings saved to: {OUT_PATH}")
print(f"Total chunks: {len(all_chunks)} | Embedding matrix shape: {all_embeddings.shape}")
