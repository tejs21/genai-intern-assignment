import os, pickle, fitz
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import numpy as np

REF_PATH = "data/reference/comprehensive-clinical-nephrology.pdf"
OUT_PATH = "data/reference_embeddings.pkl"

os.makedirs("data", exist_ok=True)
model = SentenceTransformer("all-MiniLM-L6-v2")

def chunk_text(text, size=900, overlap=200):
    chunks, start = [], 0
    while start < len(text):
        chunk = text[start:start + size]
        if len(chunk.strip()) > 50:
            chunks.append(chunk.strip())
        start += size - overlap
    return chunks

print(f"Opening {REF_PATH} ...")
doc = fitz.open(REF_PATH)
print(f"Total pages: {len(doc)}")

BATCH_SIZE = 20
all_chunks, all_embeddings = [], []

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
    print(f"Processed pages {i+1}-{min(i+BATCH_SIZE, len(doc))} ({len(chunks)} chunks)")

doc.close()

all_embeddings = np.vstack(all_embeddings)
pickle.dump({"chunks": all_chunks, "embeddings": all_embeddings}, open(OUT_PATH, "wb"))

print(f"\nSaved embeddings to {OUT_PATH}")
print(f"Total chunks: {len(all_chunks)} | Embeddings shape: {all_embeddings.shape}")
