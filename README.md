# Post-Discharge Nephrology Assistant — GenAI Intern Assignment (POC)

## Overview

This project implements a two-agent clinical assistant system:

- **Receptionist Agent:** Identifies the patient, fetches discharge details, and routes queries.
- **Clinical Agent:** Answers follow-up questions using **Retrieval-Augmented Generation (RAG)** on a nephrology reference PDF and, if needed, performs a web search fallback for external knowledge.

The system demonstrates the following pipeline:
1. **PDF Ingestion** 
2. **Vector Embedding Storage**
3. **Semantic Retrieval**
4. **LLM-based Answer Generation** 
The entire process is locally reproducible, allowing for efficient clinical assistance.

---

## Key Point: OpenAI API is Optional

- If you set your `OPENAI_API_KEY` in `.env`, the backend uses GPT-3.5 (or the model set under `MODEL_NAME`) for fluent answer generation.
- If no API key is set, the system will still function by retrieving top relevant text excerpts from the knowledge base.

---

## Setup Instructions

### 1. Prerequisites

- Python 3.10+
- The reference file:  
  `data/reference/comprehensive-clinical-nephrology.pdf`

### 2. Environment Setup

```bash
# Step 1: Create a virtual environment
python -m venv .venv

# Step 2: Activate the virtual environment
# For Windows:
.venv\Scripts\activate
# For Mac/Linux:
source .venv/bin/activate

# Step 3: Install dependencies
pip install -r requirements.txt

```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
Create a .env file (copy from .env.example) and update:
```bash

OPENAI_API_KEY=
MODEL_NAME=gpt-3.5-turbo
CHROMA_PERSIST_DIR=data/chroma
REFERENCE_PDF_PATH=data/reference/comprehensive-clinical-nephrology.pdf
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
BACKEND_URL=http://localhost:5000

```
---

## Running the Project
### 1. Ingest the Reference PDF
```bash
python scripts/ingest_reference.py
```

### 2. Start the Backend
```bash
python backend/app.py
```

### 3. Start the Frontend
```bash
streamlit run frontend/app.py
```
Access it at http://localhost:8501

---
## How It Works

1. **Patient enters name or ID Receptionist retrieves discharge info.**
2. **Patient asks clinical question Clinical agent retrieves info from RAG.**
3. **If confidence is low → performs web search.**
4. **Returns answers with citations and logs interaction.**

---
## Project Structure
```bash
genai-intern/
├── backend/
├── frontend/
├── data/
├── scripts/
├── logs/
├── .env.example
├── README.md
└── requirements.txt
```

---
## Features
- **25+ dummy patient records**
- **Receptionist & Clinical agents**
- **RAG-based knowledge retrieval**
- **Web search fallback**
- **Logging system**
- **Streamlit web interface**
- **JSON-based data retrieval**
- **Optional OpenAI integration**

---
## Disclaimer
This AI assistant is developed for educational and research purposes only.  
It does not provide medical advice. Always consult qualified healthcare professionals for diagnosis or treatment.
