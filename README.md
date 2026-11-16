# MediSync AI — Integrated Hospital Intelligence Platform

> **Full-stack monorepo**: FastAPI backend + Next.js 14 frontend with real-time WebSocket queue, multi-modal AI pipeline, EWS, and LLM-powered patient reports.

---

## 📁 Project Structure

```
medisync-ai/
├── spec.md                          # System specification document
├── docker-compose.yml               # PostgreSQL + Redis + MinIO + Backend
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/
│   │   └── env.py
│   └── app/
│       ├── main.py                  # FastAPI entry point
│       ├── core/
│       │   ├── config.py            # Pydantic settings (env vars)
│       │   ├── database.py          # Async SQLAlchemy engine + session
│       │   ├── security.py          # JWT + bcrypt helpers
│       │   └── redis_client.py      # Async Redis connection
│       ├── models/
│       │   └── models.py            # All SQLAlchemy ORM models
│       ├── schemas/
│       │   └── schemas.py           # All Pydantic request/response schemas
│       ├── api/
│       │   ├── deps.py              # FastAPI dependencies (auth, RBAC)
│       │   └── routes/
│       │       ├── auth.py          # /api/auth — register, login
│       │       ├── admin.py         # /api/admin — doctors, patients, stats
│       │       ├── doctor.py        # /api/doctor — encounters, AI, reports
│       │       ├── patient.py       # /api/patient — queue, encounters, reports
│       │       └── queue.py         # /api/queue — REST + WebSocket
│       ├── services/
│       │   ├── queue_service.py     # WS connection manager + queue helpers
│       │   ├── ews_service.py       # Rule-based Early Warning System
│       │   └── llm_report_service.py# LLM patient report generation
│       ├── ai_pipeline/
│       │   ├── tabular_predictor.py # XGBoost vital-signs risk classifier
│       │   ├── nlp_extractor.py     # HuggingFace / keyword symptom extractor
│       │   └── vision_analyzer.py  # PyTorch medical image analysis
│       └── scripts/
│           └── seed_demo.py         # Creates demo users (admin/doctor/patient)
│
└── frontend/
    ├── package.json
    ├── next.config.ts
    ├── tsconfig.json
    ├── tailwind.config.js
    └── src/
        ├── app/
        │   ├── layout.tsx
        │   ├── page.tsx             # → redirects to /login
        │   ├── globals.css
        │   ├── login/page.tsx       # Login page (all roles)
        │   ├── admin/
        │   │   ├── page.tsx         # Admin dashboard
        │   │   └── queues/page.tsx  # Queue monitor
        │   ├── doctor/
        │   │   ├── page.tsx         # Doctor dashboard + AI
        │   │   └── reports/page.tsx # Report review & approval
        │   └── patient/
        │       └── page.tsx         # Patient portal
        ├── components/
        │   ├── ui/
        │   │   ├── index.tsx        # StatCard, Badge, EWSBadge, etc.
        │   │   └── Sidebar.tsx      # Role-aware sidebar
        │   ├── queue-board/
        │   │   └── QueueBoard.tsx   # Live queue with WS updates
        │   └── ai-insights/
        │       └── AIInsightsPanel.tsx # Multi-modal AI results
        ├── lib/
        │   ├── api.ts               # Axios client + all API functions
        │   ├── websocket.ts         # QueueWebSocket class
        │   └── auth.ts              # JWT decode / token helpers
        └── types/
            └── index.ts             # TypeScript type definitions
```

---

## 🚀 Quick Start

### 1. Start Infrastructure (Docker)

```bash
# From project root
docker-compose up -d postgres redis minio
```

### 2. Backend Setup

```bash
cd backend

# Copy env file
cp .env.example .env
# Edit .env with your values

# Install dependencies (Python 3.11+)
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Seed demo users
python -m app.scripts.seed_demo

# Start API server
uvicorn app.main:app --reload --port 8000
```

API docs available at: **http://localhost:8000/docs**

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies (Node.js 18+)
npm install

# Start dev server
npm run dev
```

App available at: **http://localhost:3000**

---

## 🔑 Demo Credentials

| Role    | Email              | Password   |
|---------|--------------------|------------|
| Admin   | admin@demo.com     | demo1234   |
| Doctor  | doctor@demo.com    | demo1234   |
| Patient | patient@demo.com   | demo1234   |

---

## 🗄️ Database Schema

| Table               | Description |
|---------------------|-------------|
| `users`             | Auth + RBAC (admin / doctor / patient) |
| `patients`          | Patient profiles with NIK and medical history |
| `doctors`           | Doctor specialization and availability |
| `queues`            | Real-time queue entries per poli |
| `medical_encounters`| Examination sessions with vitals and complaint text |
| `ai_predictions`    | Per-modality inference results (tabular / NLP / vision) |
| `treatment_plans`   | Doctor-authored diagnosis, prescriptions, EWS level |
| `clinical_reports`  | LLM-generated patient-friendly reports (draft → approved) |

---

## 🤖 AI Pipeline

| Module                  | Model            | Input            | Output |
|-------------------------|------------------|------------------|--------|
| `tabular_predictor.py`  | XGBoost (or heuristic) | Vital signs JSON | Risk label + confidence |
| `nlp_extractor.py`      | HuggingFace zero-shot | Complaint text   | Symptoms + candidate diagnoses |
| `vision_analyzer.py`    | PyTorch CNN      | Medical image (MinIO key) | Radiological finding |
| `llm_report_service.py` | GPT-3.5 / local  | Clinical notes   | Patient-friendly Markdown report |

> **Demo mode**: If no trained model files are present, all AI modules return deterministic simulation results — no GPU or external API required.

---

## ⚡ WebSocket API

Connect to the queue channel for a specific poli:

```
ws://localhost:8000/api/queue/ws/{poli_name}
```

Messages received are JSON-encoded `Queue` objects pushed on every status change.
Send `ping` → receive `pong` for keepalive.

---

## 🔐 Authentication

All protected endpoints require:

```
Authorization: Bearer <JWT_TOKEN>
```

Obtain a token via `POST /api/auth/login` (OAuth2 form format).

---

## 🐳 Full Docker Compose

To run everything including the backend:

```bash
cd backend
cp .env.example .env
docker-compose up --build
```
