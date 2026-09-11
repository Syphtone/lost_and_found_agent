# Lost & Found AI

A complete AI-powered lost-and-found assistant with a modern React frontend and FastAPI + LangGraph backend.

## 🚀 Quick Start

### Prerequisites
- Node.js `v18+` or `v24+`
- npm `v9+`
- Python `3.8+`
- pip

### Frontend Setup

```bash
npm install
npm run dev
```

The frontend will be running at: **`http://localhost:5173`**

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env to add your API keys if needed
python main.py
```

The backend will be running at: **`http://localhost:8000`**

---

## 🎨 Features

### Frontend
- **Context-Aware Mock Matches**: Displays relevant potential matches based on user's item category (wallet, phone, keys, water bottle, headphones, etc.)
- **Dynamic Pickup Details**: Pickup Claim Details modal shows actual verified item information with unique pickup locations
- **Interactive AI Chat Experience**: Full conversation flow with typing indicators and auto-scrolling
- **Visual Agent Stage Pipeline**: Real-time progress tracking (new → searching → matches_shown → verification_required → verified → completed)
- **Zero-Knowledge Match Cards**: Displays safe public item details while preserving secret verification features
- **Verification & Claim Cards**: Generates pickup request IDs (PK-xxxxx) or escalation IDs (ESC-xxxx)
- **Dual Mode (Mock / Live API)**: Switch between offline mock engine and real backend endpoints
- **Session Management**: One completed claim per session with session-ended state
- **Start New Session**: Ability to reset state and start a new lost-item report
- **Exact Candidate Selection**: When user identifies a specific candidate from the list, it is selected without re-showing the full candidate list
- **State Machine**: Explicit workflow states prevent repeated searches and stale data reuse

### Backend
- **FastAPI**: RESTful API with CORS support
- **LangGraph**: State machine workflow for agent orchestration
- **Confidence Calculation**: Transparent Python-based scoring with configurable weights
- **Ownership Verification**: Secure feature comparison without exposing private verification data
- **Langfuse Integration**: Observability and tracing (optional, requires credentials)
- **Local JSON Data**: Simple item database for MVP

---

## 🏗️ Architecture

```
USER
 ↓
FRONTEND (React)
 ↓
FASTAPI (Python)
 ↓
LANGGRAPH (Agent Workflow)
 ↓
SEARCH / CONFIDENCE / VERIFICATION
 ↓
ACTION / ESCALATION
 ↓
FASTAPI
 ↓
FRONTEND

LANGGRAPH
 ↓
LANGFUSE (Optional Tracing)
```

---

## 📁 Project Structure

```
lost-and-found-ai/
├── src/
│   ├── components/
│   │   ├── Header.tsx
│   │   ├── ProgressIndicator.tsx
│   │   ├── ChatWindow.tsx
│   │   ├── MessageBubble.tsx
│   │   ├── MatchCard.tsx
│   │   ├── VerificationCard.tsx
│   │   ├── PickupCard.tsx
│   │   ├── ResultCard.tsx
│   │   ├── QuickPrompts.tsx
│   │   ├── SuggestionChips.tsx
│   │   ├── TypingIndicator.tsx
│   │   └── SessionEnded.tsx
│   ├── services/
│   │   └── api.ts
│   ├── data/
│   │   └── mockResponses.ts
│   ├── types/
│   │   └── chat.ts
│   ├── App.tsx
│   ├── App.css
│   ├── index.css
│   └── main.tsx
├── public/
│   ├── favicon.svg
│   └── icons.svg
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── .env.example
│   ├── agent/
│   │   ├── state.py
│   │   ├── nodes.py
│   │   └── graph.py
│   ├── tools/
│   │   ├── search_items.py
│   │   └── db_search_items.py
│   ├── confidence/
│   │   └── confidence.py
│   ├── observability/
│   │   └── tracer.py
│   ├── data/
│   │   ├── items.json
│   │   ├── schema.sql
│   │   └── seed.sql
│   └── tests/
├── package.json
├── package-lock.json
├── vite.config.ts
├── tsconfig.json
├── tsconfig.app.json
├── tsconfig.node.json
├── index.html
├── .gitignore
├── .oxlintrc.json
├── test_backend.py
└── README.md
```

---

## 🔌 Backend API

### POST /chat

**Request:**
```json
{
  "message": "I lost my wallet near the library",
  "conversation_id": "session-12345"
}
```

**Response:**
```json
{
  "conversation_id": "session-12345",
  "response": "I found a potential match. Can you describe a distinctive feature of your item?",
  "stage": "verification_required",
  "match": {
    "id": "item004",
    "category": "wallet",
    "brand": "Fossil",
    "color": "brown",
    "location": "library"
  },
  "confidence_level": "HIGH",
  "confidence_score": 1.0,
  "pickup": null,
  "pickup_request_id": null,
  "escalation_id": null
}
```

### GET /items

Returns list of found items (sanitized, without verification features).

### GET /health

Health check endpoint.

---

## 🧠 LangGraph Workflow

The agent follows this state machine:

1. **INTAKE**: Extract item details (category, brand, color, location, time) using LLM or rule-based extraction
2. **SEARCH**: Query item database for candidate matches
3. **CONFIDENCE**: Calculate confidence score using weighted formula:
   - Similarity: 40%
   - Location match: 20%
   - Time match: 15%
   - Category match: 15%
   - Brand match: 10%
4. **ROUTE BY CONFIDENCE**:
   - HIGH (≥0.85) → Verification
   - MEDIUM (0.60-0.84) → Ask for more information
   - LOW (<0.60) → Escalate
5. **VERIFY**: Compare user's distinctive feature with protected verification feature
6. **ACTION**: Return verified pickup details or escalation to staff

---

## 🔐 Security

- Private verification features are never exposed to the frontend
- Langfuse sanitizes sensitive data before tracing
- CORS configured for frontend-backend communication
- No passwords or API keys hardcoded in source

---

## 🧪 Testing

### Frontend Test Scenarios

#### Wallet Flow
```
"I lost my wallet"
→ Shows 3 wallet candidates (Brown Leather Wallet, Black Card Holder, Blue Wallet)
→ "blue wallet"
→ Blue Wallet selected (no re-listing)
→ Verification feature provided
→ Blue Wallet verified
→ Blue Wallet pickup details shown
```

#### Phone Flow
```
"I lost my phone"
→ Shows phone candidates
→ "black iPhone"
→ Black iPhone selected
→ Verification
→ Black iPhone pickup details
```

#### Smart Watch Flow
```
"I lost my watch"
→ Shows watch candidates
→ "black smart watch"
→ Black Smart Watch selected
→ Verification
→ Black Smart Watch pickup details
```

#### Session Completion
```
Complete one claim
→ "I lost my phone"
→ Expected: Session ended message (no new search)
→ Click "Start New Session"
→ All previous state cleared
→ New lost-item report works correctly
```

### Backend Test
```bash
python test_backend.py
```

---

## 🔧 Environment Variables

Backend `.env`:
```
GOOGLE_API_KEY=your_gemini_api_key_here
HOST=0.0.0.0
PORT=8000
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
LANGFUSE_HOST=https://cloud.langfuse.com
```

---

## 📊 Langfuse Observability

Optional Langfuse integration for tracing LangGraph workflow execution. Add credentials to `.env` to enable.

The trace shows:
- Input message
- Extracted item information
- Workflow node execution
- Search results
- Confidence calculation
- Verification result
- Final stage and response
