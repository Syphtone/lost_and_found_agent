# Lost & Found AI - Backup MVP Backend

A lightweight, reliable, and modular **FastAPI + LangGraph** backend MVP for the **Lost & Found AI** hackathon system.

---

## 🏗️ Architecture Overview

```text
                  +-------------------+
                  |  React Frontend   |
                  +---------+---------+
                            |  POST /chat
                            v
                  +-------------------+
                  |  FastAPI Server   |
                  +---------+---------+
                            |
                            v
                  +-------------------+
                  |  LangGraph Agent  |
                  +---------+---------+
                            |
         +------------------+------------------+
         |                  |                  |
         v                  v                  v
  +--------------+   +--------------+   +--------------+
  | INTAKE Node  |   | SEARCH Tool  |   | CONFIDENCE   |
  | (LLM Extract)|   | (items.json) |   | (Py Formula) |
  +--------------+   +--------------+   +--------------+
                            |
          +-----------------+-----------------+
          |                 |                 |
          v                 v                 v
       [ HIGH ]          [ MEDIUM ]        [ LOW ]
          |                 |                 |
          v                 v                 v
   +--------------+  +--------------+  +--------------+
   | VERIFY Node  |  | ASK MORE     |  | ESCALATE     |
   | (Feature Check) | (Need Info)  |  | (Staff Review)|
   +--------------+  +--------------+  +--------------+
```

---

## 🛠️ Setup Instructions

### 1. Create a Virtual Environment

```bash
cd backend
python -m venv venv
```

Activate the virtual environment:
- **Windows (PowerShell)**: `.\venv\Scripts\Activate.ps1`
- **Windows (CMD)**: `.\venv\Scripts\activate.bat`
- **macOS / Linux**: `source venv/bin/activate`

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure `.env`

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Set your `GOOGLE_API_KEY` (Gemini API key) if available:
```env
GOOGLE_API_KEY=your_gemini_api_key_here
HOST=0.0.0.0
PORT=8000
```
*(Note: If no API key is set, the system automatically falls back to an offline rule/keyword extractor).*

---

## 🚀 Running the Server

Start the FastAPI server using `uvicorn`:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The server will run on `http://localhost:8000`. You can test API docs at `http://localhost:8000/docs`.

---

## 🧪 Testing

Run unit & integration tests using `pytest`:

```bash
pytest tests/test_backend.py -v
```

---

## 📡 API Endpoint & Examples

### `POST /chat`

#### Request
```json
{
  "conversation_id": "conv_12345",
  "message": "I lost my black Sony headphones near the library."
}
```

#### Response (Potential Match / High Confidence)
```json
{
  "conversation_id": "conv_12345",
  "response": "I found a potential match. Can you describe a distinctive feature of your item?",
  "stage": "verification_required",
  "match": {
    "id": "item001",
    "category": "headphones",
    "brand": "Sony",
    "color": "black",
    "location": "library",
    "found_time": "16:20",
    "description": "Black Sony wireless noise-canceling headphones with carrying case"
  },
  "confidence_level": "HIGH",
  "confidence_score": 0.95,
  "pickup": null
}
```

#### Verification Turn Request
```json
{
  "conversation_id": "conv_12345",
  "message": "There is a small scratch on the left earcup."
}
```

#### Response (Verified)
```json
{
  "conversation_id": "conv_12345",
  "response": "Your item has been successfully verified. A pickup request has been created.",
  "stage": "verified",
  "match": {
    "id": "item001",
    "category": "headphones",
    "brand": "Sony",
    "color": "black",
    "location": "library"
  },
  "confidence_level": "HIGH",
  "pickup": {
    "location": "Library Security Desk",
    "status": "Ready for pickup",
    "item_id": "item001"
  },
  "pickup_request_id": "PK-89241A"
}
```

---

## 🐘 PostgreSQL + pgvector Setup (RAG Upgrade)

To upgrade from local JSON search to PostgreSQL with `pgvector` vector similarity search:

### 1. Run PostgreSQL with pgvector (Docker)

```bash
docker run -d \
  --name pgvector-lost-found \
  -e POSTGRES_DB=lost_found_db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 \
  ankane/pgvector
```

### 2. Initialize Database Schema & Seed Data

```bash
# Apply SQL Schema
psql -h localhost -U postgres -d lost_found_db -f data/schema.sql

# Seed Sample Items
psql -h localhost -U postgres -d lost_found_db -f data/seed.sql
```

### 3. Configure `.env`

Add `DATABASE_URL` to your `backend/.env`:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/lost_found_db
```

### 4. Modular Database Code
- Schema: [data/schema.sql](file:///C:/Users/TUF/.gemini/antigravity/scratch/lost-and-found-ai/backend/data/schema.sql)
- Seed: [data/seed.sql](file:///C:/Users/TUF/.gemini/antigravity/scratch/lost-and-found-ai/backend/data/seed.sql)
- PostgreSQL Search Tool: [tools/db_search_items.py](file:///C:/Users/TUF/.gemini/antigravity/scratch/lost-and-found-ai/backend/tools/db_search_items.py)

---

## 🔍 Langfuse Tracing & Observability

The backend includes native **Langfuse** integration to trace and visualize full LangGraph workflow executions in real-time.

```text
Trace: Lost & Found Request
├── Node: INTAKE (Structured entity extraction)
├── Node: SEARCH (Database query & candidate matching)
├── Node: CONFIDENCE (Transparent scoring calculation)
├── Node: VERIFY / ASK_MORE / ESCALATE (Decision routing)
└── Final Action (Response output & stage update)
```

### 1. Configure Langfuse Keys in `.env`

```env
LANGFUSE_PUBLIC_KEY=pk-lf-your_public_key
LANGFUSE_SECRET_KEY=sk-lf-your_secret_key
LANGFUSE_HOST=https://cloud.langfuse.com
```

*(If these keys are left empty, the system automatically runs in fallback mode without crashing).*

### 2. Security & Data Protection
- Protected item attributes like `verification_feature` are automatically sanitized and stripped before trace payloads are recorded in Langfuse.


