# lost_and_found_agent
Agentic AI - powered Lost and Found Assistant

An agentic AI system that reunites people with lost items by understanding
natural-language reports, semantically searching existing lost/found records,
scoring match confidence, and escalating ambiguous cases to a human.

\---

## Problem Statement

Lost \& found handling is manual and lossy. A person reports *"I lost a black
Sony headphone near the library yesterday"* in free text, while records are
stored with inconsistent wording, categories, and locations. Keyword search
misses obvious matches (`headphone` vs `earphones`, `library` vs `study hall`),
and a human has to eyeball every report. This does not scale, and confident-but-
wrong matches erode trust.

## Proposed Solution

An **agentic pipeline** that:

1. **Understands** the free-text report and extracts structured fields
(item type, color, brand, location, date, description).
2. **Retrieves** candidate records using **semantic similarity** over
embeddings stored in **PostgreSQL + pgvector** (RAG).
3. **Matches** candidates against the report and produces human-readable
**evidence** for each.
4. **Scores confidence** explicitly and applies a **guardrail**:

   * high confidence → return the match,
   * low / ambiguous → **flag and escalate** to a human.
5. Emits **observability** at every step: node execution, retrieval hits,
MCP calls, confidence, and the routing decision.

The agent *actually* calls tools and runs retrieval — nothing is faked.

## Architecture Overview

```
             HTTP request
                  │
             ┌────▼────┐
             │ FastAPI │              (API layer)
             └────┬────┘
                  │
          ┌───────▼────────┐
          │   LangGraph    │          (agent orchestration)
          │                │
          │  Intake        │  parse report → structured query
          │    ↓           │
          │  Retrieval     │  semantic search via MCP → pgvector
          │    ↓           │
          │  Matching      │  compare candidates, build evidence
          │    ↓           │
          │  Safety /      │  compute confidence score
          │  Confidence    │
          │    ↓           │
          │  Router        │  return match  |  escalate
          └───────┬────────┘
                  │
             ┌────▼────┐
             │  MCP    │              (FastMCP tool server)
             │  tools  │
             └────┬────┘
                  │
          ┌───────▼────────┐
          │ Service layer  │          (business logic + embeddings)
          └───────┬────────┘
                  │
        ┌─────────▼──────────┐
        │ PostgreSQL +       │        (storage + vector search)
        │ pgvector           │
        └────────────────────┘
```

## Technology Stack

|Layer|Technology|
|-|-|
|API|FastAPI|
|Agent workflow|LangGraph|
|Tool protocol|FastMCP (MCP tool server)|
|Storage|PostgreSQL|
|Vector search|pgvector|
|Embeddings|Local sentence-transformers model (e.g. `all-MiniLM-L6-v2`)|
|LLM|Local Unsloth-served model (OpenAI-compatible interface)|
|Language|Python|
|VCS|Git|

Secrets (API keys, DB URL) are supplied via **environment variables** only —
never hard-coded. A `.env.example` will document required variables; `.env` is
git-ignored.

### Model separation (two independent abstractions)

The **LLM** and the **embedding model** are deliberately separate concerns,
each behind its own interface so either can be swapped without touching
LangGraph, MCP, the database, or the RAG logic:

|Concern|Interface|Backend|Used for|
|-|-|-|-|
|**LLM**|`app/llm.py`|Local **Unsloth**-supported model|Conversation, intent understanding, agent reasoning, reasoning over retrieved evidence, final response generation|
|**Embeddings**|`app/embeddings.py`|Local **sentence-transformers** model|Encoding reports into vectors for pgvector RAG|

The rest of the codebase depends only on these interfaces (e.g. `generate()`
and `embed()`), never on a concrete model. Changing the LLM or embedding model
is a one-file change with no ripple into the agent, tools, or storage layers.

## Agent Workflow (LangGraph)

State flows through a directed graph of nodes; each node updates a shared
`AgentState`.

|Node|Responsibility|
|-|-|
|**Intake**|Parse the raw report into a structured query (type, color, brand, location, date).|
|**Retrieval**|Call the `find\_potential\_matches` / `search\_items` MCP tools to fetch semantically similar records from pgvector.|
|**Matching**|Score each candidate against the query and generate evidence explaining *why* it matches.|
|**Safety/Confidence**|Combine similarity + field agreement into a single **confidence score** with an explicit decision.|
|**Router**|If confidence ≥ threshold → return match; else → **flag / escalate**.|

## MCP Role

A **FastMCP** server exposes the system's capabilities as first-class tools the
agent invokes over the Model Context Protocol. This decouples the agent's
reasoning from the data/service layer and makes tool calls explicit and
observable. Planned tools (minimum):

* `create\_lost\_report`  — persist a new lost-item report (+ embedding).
* `create\_found\_report` — persist a new found-item report (+ embedding).
* `search\_items`        — semantic search across reports.
* `find\_potential\_matches` — retrieve best candidate matches for a report.
* `get\_item`            — fetch a single report by id.

## RAG Role

Retrieval-Augmented Generation grounds the agent in real records instead of
letting the LLM hallucinate matches:

1. On write, each report's text is embedded (via `app/embeddings.py`, a local
sentence-transformers model) and stored in a `pgvector` column.
2. On query, the report is embedded with the **same** embedding model and
compared via cosine distance (`<=>`) to retrieve the top-k nearest records.
3. Retrieved records become the evidence base for the **LLM** (`app/llm.py`) to
reason over during matching and confidence scoring.

> Embeddings and the LLM are independent: the embedding model defines the vector
> space for retrieval; the Unsloth LLM never produces embeddings and the
> embedding model never generates text.

## Confidence / Guardrail Concept

Every candidate produces an explicit **confidence score** derived from:

* **Semantic similarity** (pgvector distance → similarity).
* **Structured field agreement** (item type, color, brand, location, date).

Decision policy:

* `confidence ≥ HIGH\_THRESHOLD` → **return match** with evidence.
* `LOW\_THRESHOLD ≤ confidence < HIGH\_THRESHOLD` → **ambiguous → escalate**.
* `confidence < LOW\_THRESHOLD` → **no confident match → escalate / no-match**.

Escalated cases are flagged in the response so a human can review — the system
never asserts a match it cannot justify.

## Planned Directory Structure

```
hackathon-agenticai/
├── README.md
├── .env.example              # required env vars (no secrets)
├── .gitignore
├── requirements.txt
├── app/
│   ├── main.py               # FastAPI entrypoint
│   ├── config.py             # env-based settings
│   ├── db.py                 # PostgreSQL + pgvector connection
│   ├── llm.py                # LLM interface (local Unsloth model)
│   ├── embeddings.py         # embedding interface (local sentence-transformers)
│   ├── services/
│   │   └── items.py          # report CRUD + vector search
│   ├── mcp/
│   │   └── server.py         # FastMCP tool server
│   └── agent/
│       ├── state.py          # AgentState schema
│       ├── nodes.py          # intake/retrieval/matching/safety/router
│       ├── graph.py          # LangGraph wiring
│       └── observability.py  # step logging / traces
├── sql/
│   └── schema.sql            # tables + pgvector index
└── eval/
    └── dataset.json          # small evaluation set (added later)
```

## Setup \& Run

Prerequisites (already satisfied in the reference environment):

* **PostgreSQL 16 with the `pgvector` extension available.**
* **Ollama** running locally with a model pulled (`llama3.1:latest` is used by
default). Verify with `ollama list`.
* The embedding model `all-MiniLM-L6-v2` in the local Hugging Face cache
(loaded fully offline; no download at runtime).

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env        # adjust DATABASE\_URL / LLM\_MODEL if needed

# 3. Create the database (once) and apply the schema
#    (schema.sql enables pgvector and creates the items table + indexes)
python - <<'PY'
import psycopg
from app.config import settings

admin = psycopg.connect("postgresql://postgres:postgres@localhost:5432/postgres", autocommit=True)
if admin.execute("SELECT 1 FROM pg\_database WHERE datname='lostfound'").fetchone() is None:
    admin.execute("CREATE DATABASE lostfound")

conn = psycopg.connect(settings.database\_url, autocommit=True)
conn.execute(open("sql/schema.sql", encoding="utf-8").read())
print("database ready, schema applied")
PY

# 4. Seed a demo corpus of found reports
python -m scripts.seed --reset

# 5. Run the API
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Demo requests (in another terminal):

```bash
# Health
curl http://127.0.0.1:8000/health

# Lost report -> full agent run (decision, confidence, evidence, trace)
curl -X POST http://127.0.0.1:8000/report/lost \\
  -H "Content-Type: application/json" \\
  -d '{"raw\_text":"I lost a black Sony headphone near the library yesterday"}'

# Register a found report
curl -X POST http://127.0.0.1:8000/report/found \\
  -H "Content-Type: application/json" \\
  -d '{"raw\_text":"Found a black Sony headphone by the library","item\_type":"headphones","color":"black","brand":"Sony","location":"library"}'
```

Run the evaluation suite (requires the corpus to be seeded):

```bash
python -m eval.run\_eval
```

### Verified status

The full stack has been exercised end-to-end in the reference environment:

* pgvector cosine retrieval returns correct candidates from real embeddings.
* The LangGraph pipeline runs `intake → retrieval (MCP) → matching → safety → respond`.
* The MCP `find\_potential\_matches` tool is invoked in-process (real tool use).
* Evaluation: **6/6 decision accuracy** across matched / escalated / no\_match cases,
with confidence scores cleanly separated around the 0.75 / 0.45 thresholds.

## MVP Demo Scenario

1. Seed a few **found** reports (e.g. *"Found black Sony over-ear headphones by
the library entrance"*).
2. Submit a **lost** report:
`POST /report/lost` → *"I lost a black Sony headphone near the library yesterday."*
3. The agent runs: **Intake → Retrieval (pgvector) → Matching → Confidence → Router**.
4. Response returns the matched found-report, the **evidence**, a
**confidence score**, and the **routing decision** (`matched`).
5. Submit an ambiguous report (*"I lost some black electronics somewhere"*) →
low confidence → **escalated / flagged** in the response.
6. Observability output shows each node, the retrieval hits, MCP calls, the
score, and the final decision — demonstrating a real, inspectable agent run.

```
