# 🚀 AI Router — Full-Stack Application

An intelligent AI router that automatically selects between **Local LLM** (Gemma 3 via Ollama) and **Cloud LLM** (Llama 3.1 via Fireworks AI) using a fine-tuned DistilBERT multi-task router model.

---

## 🏗 Architecture

```
User Query
    │
    ▼
FastAPI Backend  (port 8000)
    │
    ▼
MultiTaskRouter (DistilBERT)
    ├── route_logits     → LOCAL | CLOUD
    ├── intent_logits    → 62 intent classes
    └── complexity_pred  → [0, 1] sigmoid
    │
    ├── LOCAL → Gemma 3 via Ollama (localhost:11434)
    └── CLOUD → Llama 3.1 via Fireworks AI
    │
    ▼
Next.js Frontend (port 3000)
    ├── Left:   Conversation history sidebar
    ├── Center: Chat interface with metadata cards
    └── Right:  Live statistics dashboard
```

---

## 📁 Project Structure

```
project/
├── backend/
│   ├── app.py               ← FastAPI app (CORS, middleware, all routes)
│   ├── initialize_model.py  ← MultiTaskRouter singleton loader
│   ├── predictor.py         ← Predictor class (3-head model outputs)
│   ├── gemma.py             ← Gemma via Ollama
│   ├── fireworks.py         ← Fireworks AI cloud service
│   ├── .env                 ← API keys (copy and fill in)
│   └── requirements.txt
│
├── frontend/
│   ├── app/
│   │   ├── layout.tsx       ← Root layout
│   │   ├── page.tsx         ← Main 3-panel page
│   │   └── globals.css      ← Design system
│   ├── components/
│   │   ├── Sidebar.tsx      ← Conversation history
│   │   ├── ChatMessage.tsx  ← Message cards with metadata
│   │   ├── InputBar.tsx     ← Query input
│   │   ├── StatusIndicator.tsx
│   │   ├── StatsDashboard.tsx ← Live stats + pie chart
│   │   ├── RouteBadge.tsx   ← LOCAL/CLOUD badge
│   │   ├── ConfidenceBar.tsx← Animated confidence bar
│   │   └── LoadingSpinner.tsx
│   ├── services/api.ts      ← Axios client
│   └── types/chat.ts        ← TypeScript interfaces
│
└── router_model/            ← Pre-trained MultiTaskRouter weights
    ├── model.safetensors
    ├── config.json
    ├── tokenizer.json
    ├── route_encoder.joblib
    └── intent_encoder.joblib
```

---

## ⚡ Quick Start

### Prerequisites

| Tool | Purpose | Install |
|------|---------|---------|
| Python 3.11 | Backend runtime | [python.org](https://python.org) |
| Node.js 20+ | Frontend runtime | [nodejs.org](https://nodejs.org) |
| Ollama | Local Gemma LLM | [ollama.com](https://ollama.com) |

---

### 1. Backend Setup

```bash
# Activate virtual environment
.venv\Scripts\activate          # Windows
source .venv/bin/activate        # Linux/macOS

# Install dependencies
pip install -r backend/requirements.txt

# (Optional) Set your Fireworks API key
# Edit backend/.env and set FIREWORKS_API_KEY=your_key_here

# Start the backend
cd backend
uvicorn app:app --reload
```

Backend runs at: **http://localhost:8000**  
Swagger docs at: **http://localhost:8000/api/docs**

---

### 2. Local LLM — Ollama (Optional but recommended for LOCAL route)

```bash
# Install Ollama from https://ollama.com/download
# Then pull and run Gemma 3:
ollama pull gemma3
ollama serve
```

If Ollama is not running, LOCAL-routed queries will return an informative error message (the app won't crash).

---

### 3. Frontend Setup

```bash
# Install Node.js from https://nodejs.org/ first
cd frontend
npm install
npm run dev
```

Frontend runs at: **http://localhost:3000**

---

## 🌐 API Reference

### `POST /predict` — Full prediction + LLM answer
```json
Request:  { "query": "Install nginx on Ubuntu" }
Response: {
  "route":       "LOCAL",
  "confidence":  0.97,
  "intent":      "linux_install",
  "complexity":  0.17,
  "answer":      "sudo apt install nginx",
  "latency_ms":  1423.5
}
```

### `POST /route` — Routing decision only (no LLM)
```json
Request:  { "query": "Write a complex ML pipeline" }
Response: {
  "route":       "CLOUD",
  "confidence":  0.92,
  "intent":      "code_generation",
  "complexity":  0.81,
  "latency_ms":  45.2
}
```

### `GET /health` — Server status
### `GET /api/docs` — Swagger UI

---

## 🎨 Frontend Features

| Feature | Description |
|---------|-------------|
| 💬 Chat interface | ChatGPT-style conversation with history |
| 🏷 Route badges | 🟢 LOCAL (green) · 🔵 CLOUD (blue) |
| 📊 Confidence bar | Animated: green >90% · yellow >70% · red <70% |
| 🎯 Intent badge | Shows detected intent (linux_install, code_generation, etc.) |
| ⚡ Complexity score | Sigmoid complexity from the model's regression head |
| ⏱ Response time | Full end-to-end latency including LLM generation |
| 📈 Live stats | Right panel: total/LOCAL/CLOUD counts + pie chart |
| 💰 Cost efficiency | Tracks how many queries were handled locally |

---

## 🧠 Model Details

- **Architecture**: MultiTaskRouter (DistilBERT + 3 task heads)
- **Route head**: 2-class classification (CLOUD=0, LOCAL=1)
- **Intent head**: 62-class classification
- **Complexity head**: Sigmoid regression [0, 1]
- **Inference**: Single forward pass returns all 3 outputs

---

## 🏆 AMD Developer Hackathon — ACT II

Built by **Anish Siwakoti** and **Sabin Siwakoti**
