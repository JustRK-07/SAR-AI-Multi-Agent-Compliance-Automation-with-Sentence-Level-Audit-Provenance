# Backend Architecture - FastAPI + Multi-Agent Pipeline

## High-Level Backend Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    FASTAPI BACKEND ARCHITECTURE                                     │
├─────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                     │
│                                         INCOMING REQUESTS                                           │
│                                               │                                                     │
│                                               ▼                                                     │
│  ┌───────────────────────────────────────────────────────────────────────────────────────────────┐  │
│  │                                    FASTAPI APPLICATION                                        │  │
│  │                                       (app/main.py)                                           │  │
│  │                                                                                               │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────────────────────┐ │  │
│  │  │                                   MIDDLEWARE LAYER                                       │ │  │
│  │  │                                                                                          │ │  │
│  │  │   ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐                  │ │  │
│  │  │   │   CORS           │    │   Error          │    │   Request        │                  │ │  │
│  │  │   │   Middleware     │    │   Handler        │    │   Logging        │                  │ │  │
│  │  │   │                  │    │                  │    │                  │                  │ │  │
│  │  │   │ Origins:         │    │ HTTPException    │    │ Access logs      │                  │ │  │
│  │  │   │ - localhost:5173 │    │ handler          │    │ Request timing   │                  │ │  │
│  │  │   │ - localhost:3000 │    │                  │    │                  │                  │ │  │
│  │  │   └──────────────────┘    └──────────────────┘    └──────────────────┘                  │ │  │
│  │  │                                                                                          │ │  │
│  │  └─────────────────────────────────────────────────────────────────────────────────────────┘ │  │
│  │                                              │                                                │  │
│  │                                              ▼                                                │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────────────────────┐ │  │
│  │  │                                    ROUTER LAYER                                          │ │  │
│  │  │                                  (app/routers/)                                          │ │  │
│  │  │                                                                                          │ │  │
│  │  │   ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐      │ │  │
│  │  │   │   alerts    │ │    sar      │ │   audit     │ │transactions │ │  websocket  │      │ │  │
│  │  │   │   router    │ │   router    │ │   router    │ │   router    │ │   router    │      │ │  │
│  │  │   │             │ │             │ │             │ │             │ │             │      │ │  │
│  │  │   │ /api/alerts │ │ /api/sar    │ │ /api/audit  │ │/api/transac │ │ /ws/sar     │      │ │  │
│  │  │   │             │ │             │ │             │ │             │ │             │      │ │  │
│  │  │   │ GET  /      │ │ POST /gen   │ │ GET /evid   │ │ GET  /      │ │ WS /{task}  │      │ │  │
│  │  │   │ GET  /{id}  │ │ GET  /{id}  │ │ GET /trail  │ │ GET /graph  │ │             │      │ │  │
│  │  │   │ PATCH/stat  │ │ PATCH/{id}  │ │             │ │             │ │             │      │ │  │
│  │  │   │             │ │ POST /sub   │ │             │ │             │ │             │      │ │  │
│  │  │   └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘      │ │  │
│  │  │                                                                                          │ │  │
│  │  └─────────────────────────────────────────────────────────────────────────────────────────┘ │  │
│  │                                              │                                                │  │
│  └──────────────────────────────────────────────┼────────────────────────────────────────────────┘  │
│                                                 │                                                   │
│                                                 ▼                                                   │
│  ┌───────────────────────────────────────────────────────────────────────────────────────────────┐  │
│  │                                     SERVICE LAYER                                             │  │
│  │                                    (app/services/)                                            │  │
│  │                                                                                               │  │
│  │   ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐ │  │
│  │   │                   │  │                   │  │                   │  │                   │ │  │
│  │   │  SARGenerator     │  │  AuditTrail       │  │  FactChecker      │  │  PDFGenerator     │ │  │
│  │   │  Service          │  │  Service          │  │  Service          │  │  Service          │ │  │
│  │   │                   │  │                   │  │                   │  │                   │ │  │
│  │   │  - Orchestrates   │  │  - Log queries    │  │  - Extract claims │  │  - Generate PDF   │ │  │
│  │   │    agent pipeline │  │  - Log LLM calls  │  │  - Verify facts   │  │  - Include audit  │ │  │
│  │   │  - Manages state  │  │  - Track evidence │  │  - Score confid.  │  │  - Format report  │ │  │
│  │   │  - Progress CB    │  │  - Link sentences │  │                   │  │                   │ │  │
│  │   │                   │  │                   │  │                   │  │                   │ │  │
│  │   └─────────┬─────────┘  └───────────────────┘  └───────────────────┘  └───────────────────┘ │  │
│  │             │                                                                                 │  │
│  └─────────────┼─────────────────────────────────────────────────────────────────────────────────┘  │
│                │                                                                                    │
│                ▼                                                                                    │
│  ┌───────────────────────────────────────────────────────────────────────────────────────────────┐  │
│  │                                      AGENT LAYER                                              │  │
│  │                                     (app/agents/)                                             │  │
│  │                                                                                               │  │
│  │                        ┌─────────────────────────────────────────┐                           │  │
│  │                        │     MULTI-AGENT PIPELINE (LangGraph)    │                           │  │
│  │                        │                                         │                           │  │
│  │   ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐                   │  │
│  │   │ Agent 1 │───►│ Agent 2 │───►│ Agent 3 │───►│ Agent 4 │───►│ Agent 5 │                   │  │
│  │   │  Data   │    │Complian-│    │Narrative│    │  Fact   │    │ Editor  │                   │  │
│  │   │ Analyst │    │   ce    │    │ Writer  │    │ Checker │    │         │                   │  │
│  │   └────┬────┘    └────┬────┘    └────┬────┘    └────┬────┘    └────┬────┘                   │  │
│  │        │              │              │              │              │                         │  │
│  │        ▼              ▼              ▼              ▼              ▼                         │  │
│  │   facts_json     typology      narrative      verified       final_sar                      │  │
│  │                                                                                               │  │
│  │                        └─────────────────────────────────────────┘                           │  │
│  │                                                                                               │  │
│  └───────────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                 │                                                   │
│                    ┌────────────────────────────┼────────────────────────────┐                     │
│                    │                            │                            │                     │
│                    ▼                            ▼                            ▼                     │
│  ┌──────────────────────────┐  ┌──────────────────────────┐  ┌──────────────────────────┐         │
│  │                          │  │                          │  │                          │         │
│  │      DATABASE LAYER      │  │    KNOWLEDGE BASE        │  │       LLM LAYER          │         │
│  │       (app/db/)          │  │  (app/knowledge_base/)   │  │      (via Ollama)        │         │
│  │                          │  │                          │  │                          │         │
│  │  ┌────────────────────┐  │  │  ┌────────────────────┐  │  │  ┌────────────────────┐  │         │
│  │  │    SQLAlchemy      │  │  │  │     ChromaDB       │  │  │  │   Ollama Client    │  │         │
│  │  │    (ORM)           │  │  │  │  (Vector Store)    │  │  │  │                    │  │         │
│  │  └────────────────────┘  │  │  └────────────────────┘  │  │  │  Model: Llama 3.1  │  │         │
│  │                          │  │                          │  │  │  Port: 11434       │  │         │
│  │  ┌────────────────────┐  │  │  ┌────────────────────┐  │  │  └────────────────────┘  │         │
│  │  │  PostgreSQL/SQLite │  │  │  │   Embeddings       │  │  │                          │         │
│  │  │  (Database)        │  │  │  │  (MiniLM-L6-v2)    │  │  │                          │         │
│  │  └────────────────────┘  │  │  └────────────────────┘  │  │                          │         │
│  │                          │  │                          │  │                          │         │
│  └──────────────────────────┘  └──────────────────────────┘  └──────────────────────────┘         │
│                                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Directory Structure Detail

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   BACKEND DIRECTORY STRUCTURE                                       │
├─────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                     │
│  backend/                                                                                           │
│  │                                                                                                  │
│  ├── app/                                                                                           │
│  │   │                                                                                              │
│  │   ├── __init__.py                    # Package initialization                                    │
│  │   ├── main.py                        # FastAPI application entry point                           │
│  │   ├── config.py                      # Configuration management (Pydantic Settings)              │
│  │   │                                                                                              │
│  │   ├── routers/                       # API ENDPOINTS                                             │
│  │   │   ├── __init__.py                                                                            │
│  │   │   ├── alerts.py                  # Alert CRUD operations                                     │
│  │   │   │   ├── GET  /api/alerts                   List alerts with filters                       │
│  │   │   │   ├── GET  /api/alerts/{id}              Get single alert                               │
│  │   │   │   └── PATCH /api/alerts/{id}/status      Update alert status                            │
│  │   │   │                                                                                          │
│  │   │   ├── sar.py                     # SAR generation & management                               │
│  │   │   │   ├── POST /api/sar/generate             Start SAR generation                           │
│  │   │   │   ├── GET  /api/sar/task/{task_id}       Get generation status                          │
│  │   │   │   ├── GET  /api/sar/{sar_id}             Get SAR by ID                                  │
│  │   │   │   ├── GET  /api/sar/by-alert/{alert_id}  Get SAR by alert                               │
│  │   │   │   ├── PATCH /api/sar/{sar_id}            Update SAR (edit)                              │
│  │   │   │   ├── POST /api/sar/{sar_id}/submit      Submit for filing                              │
│  │   │   │   └── GET  /api/sar/{sar_id}/export      Export as PDF                                  │
│  │   │   │                                                                                          │
│  │   │   ├── audit.py                   # Audit trail endpoints                                     │
│  │   │   │   ├── GET /api/audit/sar/{id}/evidence/{idx}   Sentence evidence                        │
│  │   │   │   └── GET /api/audit/sar/{id}                  Full audit trail                         │
│  │   │   │                                                                                          │
│  │   │   ├── transactions.py            # Transaction data endpoints                                │
│  │   │   │   ├── GET /api/transactions              List transactions                              │
│  │   │   │   └── GET /api/transactions/graph/{id}   Graph data for React Flow                      │
│  │   │   │                                                                                          │
│  │   │   └── websocket.py               # Real-time updates                                         │
│  │   │       └── WS /ws/sar/{task_id}               Generation progress                            │
│  │   │                                                                                              │
│  │   ├── services/                      # BUSINESS LOGIC                                            │
│  │   │   ├── __init__.py                                                                            │
│  │   │   ├── sar_generator.py           # Orchestrates multi-agent pipeline                         │
│  │   │   ├── audit_trail.py             # Audit logging and retrieval                               │
│  │   │   ├── fact_checker.py            # Claim extraction and verification                         │
│  │   │   └── pdf_generator.py           # PDF report generation                                     │
│  │   │                                                                                              │
│  │   ├── agents/                        # AI AGENTS                                                 │
│  │   │   ├── __init__.py                                                                            │
│  │   │   ├── data_analyst.py            # Agent 1: SQL queries, fact extraction                     │
│  │   │   ├── compliance.py              # Agent 2: Typology classification                          │
│  │   │   ├── writer.py                  # Agent 3: Narrative generation                             │
│  │   │   ├── fact_checker.py            # Agent 4: Claim verification                               │
│  │   │   └── editor.py                  # Agent 5: Grammar and style                                │
│  │   │                                                                                              │
│  │   ├── models/                        # PYDANTIC MODELS (API schemas)                             │
│  │   │   ├── __init__.py                                                                            │
│  │   │   ├── alert.py                   # Alert, AlertStatus, AlertResponse                         │
│  │   │   ├── sar.py                     # SAR, SARStatus, SARResponse                               │
│  │   │   ├── transaction.py             # Transaction, GraphNode, GraphEdge                         │
│  │   │   └── audit.py                   # AuditEntry, AuditEvidence                                 │
│  │   │                                                                                              │
│  │   ├── db/                            # DATABASE LAYER                                            │
│  │   │   ├── __init__.py                                                                            │
│  │   │   ├── database.py                # SQLAlchemy engine, session                                │
│  │   │   ├── models.py                  # ORM models (tables)                                       │
│  │   │   └── crud.py                    # Create, Read, Update, Delete operations                   │
│  │   │                                                                                              │
│  │   └── knowledge_base/                # RAG COMPONENTS                                            │
│  │       ├── __init__.py                                                                            │
│  │       ├── vector_store.py            # ChromaDB operations                                       │
│  │       └── embeddings.py              # Sentence transformers                                     │
│  │                                                                                                  │
│  ├── data/                              # Runtime data (SQLite, ChromaDB)                           │
│  │   ├── sar_dev.db                     # Development SQLite database                               │
│  │   └── chroma_db/                     # Vector store persistence                                  │
│  │                                                                                                  │
│  ├── requirements.txt                   # Python dependencies                                       │
│  ├── seed_data.py                       # Sample data generator                                     │
│  ├── Dockerfile                         # Container build instructions                              │
│  └── .env                               # Environment variables (local)                             │
│                                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Multi-Agent Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                  MULTI-AGENT PIPELINE DETAIL                                        │
├─────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                     │
│  INPUT: alert_id                                                                                    │
│         │                                                                                           │
│         ▼                                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │                                                                                             │   │
│  │   AGENT 1: DATA ANALYST                                                    Progress: 0-20% │   │
│  │   ════════════════════                                                                     │   │
│  │                                                                                             │   │
│  │   File: app/agents/data_analyst.py                                                         │   │
│  │                                                                                             │   │
│  │   ┌───────────────────────────────────────────────────────────────────────────────────┐   │   │
│  │   │                                                                                   │   │   │
│  │   │   INPUTS:                                                                         │   │   │
│  │   │   ├── alert_id                                                                    │   │   │
│  │   │   └── Database connection                                                         │   │   │
│  │   │                                                                                   │   │   │
│  │   │   TOOLS:                                                                          │   │   │
│  │   │   ├── execute_sql()          Execute queries against transaction data            │   │   │
│  │   │   ├── aggregate_stats()      Calculate counts, sums, averages                    │   │   │
│  │   │   └── analyze_patterns()     Detect structuring, layering, etc.                  │   │   │
│  │   │                                                                                   │   │   │
│  │   │   QUERIES EXECUTED:                                                               │   │   │
│  │   │   ├── SELECT COUNT(*), SUM(amount) FROM transactions...                          │   │   │
│  │   │   ├── SELECT MIN(date), MAX(date) FROM transactions...                           │   │   │
│  │   │   ├── SELECT DISTINCT source_account FROM transactions...                        │   │   │
│  │   │   └── SELECT * FROM customers WHERE id = {customer_id}                           │   │   │
│  │   │                                                                                   │   │   │
│  │   │   OUTPUT: facts_json                                                              │   │   │
│  │   │   ┌─────────────────────────────────────────────────────────────────────────┐   │   │   │
│  │   │   │ {                                                                       │   │   │   │
│  │   │   │   "transaction_count": 47,                                              │   │   │   │
│  │   │   │   "total_amount": 5000000,                                              │   │   │   │
│  │   │   │   "unique_sources": 47,                                                 │   │   │   │
│  │   │   │   "date_range": ["2026-01-05", "2026-01-12"],                           │   │   │   │
│  │   │   │   "customer": { "name": "Rajesh Kumar", "pan": "ABCDE1234F" },         │   │   │   │
│  │   │   │   "patterns": ["Structuring", "Multiple unique sources"],              │   │   │   │
│  │   │   │   "queries": [{ "query": "SELECT...", "results": [...] }]              │   │   │   │
│  │   │   │ }                                                                       │   │   │   │
│  │   │   └─────────────────────────────────────────────────────────────────────────┘   │   │   │
│  │   │                                                                                   │   │   │
│  │   └───────────────────────────────────────────────────────────────────────────────────┘   │   │
│  │                                                                                             │   │
│  └─────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                              │                                                      │
│                                              ▼                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │                                                                                             │   │
│  │   AGENT 2: COMPLIANCE SPECIALIST                                          Progress: 20-40% │   │
│  │   ══════════════════════════════                                                           │   │
│  │                                                                                             │   │
│  │   File: app/agents/compliance.py                                                           │   │
│  │                                                                                             │   │
│  │   ┌───────────────────────────────────────────────────────────────────────────────────┐   │   │
│  │   │                                                                                   │   │   │
│  │   │   INPUTS:                                                                         │   │   │
│  │   │   └── facts_json (from Agent 1)                                                   │   │   │
│  │   │                                                                                   │   │   │
│  │   │   KNOWLEDGE BASE:                                                                 │   │   │
│  │   │   ├── FinCEN SAR Activity Codes (31a, 31z, 42, etc.)                             │   │   │
│  │   │   ├── FATF 40 Recommendations                                                    │   │   │
│  │   │   └── Pattern indicators database                                                 │   │   │
│  │   │                                                                                   │   │   │
│  │   │   CLASSIFICATION LOGIC:                                                           │   │   │
│  │   │   ┌─────────────────────────────────────────────────────────────────────────┐   │   │   │
│  │   │   │  Pattern                           → Typology         → FinCEN Code    │   │   │   │
│  │   │   │  ─────────────────────────────────────────────────────────────────────│   │   │   │
│  │   │   │  Multiple txns < threshold         → Structuring      → 31a           │   │   │   │
│  │   │   │  Rapid movement + offshore         → Layering         → 31z           │   │   │   │
│  │   │   │  Multiple sources → consolidate    → Collection Acct  → 31z           │   │   │   │
│  │   │   │  Trade document discrepancies      → Trade-Based ML   → 35f           │   │   │   │
│  │   │   └─────────────────────────────────────────────────────────────────────────┘   │   │   │
│  │   │                                                                                   │   │   │
│  │   │   OUTPUT: typology_result                                                         │   │   │
│  │   │   ┌─────────────────────────────────────────────────────────────────────────┐   │   │   │
│  │   │   │ {                                                                       │   │   │   │
│  │   │   │   "typology": "Structuring",                                            │   │   │   │
│  │   │   │   "fincen_code": "31a",                                                 │   │   │   │
│  │   │   │   "confidence": 0.94,                                                   │   │   │   │
│  │   │   │   "indicators": ["Multiple transactions below threshold", ...],        │   │   │   │
│  │   │   │   "reasoning": "Alert scenario: Structuring. Detected patterns:..."    │   │   │   │
│  │   │   │ }                                                                       │   │   │   │
│  │   │   └─────────────────────────────────────────────────────────────────────────┘   │   │   │
│  │   │                                                                                   │   │   │
│  │   └───────────────────────────────────────────────────────────────────────────────────┘   │   │
│  │                                                                                             │   │
│  └─────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                              │                                                      │
│                                              ▼                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │                                                                                             │   │
│  │   AGENT 3: NARRATIVE WRITER                                               Progress: 40-70% │   │
│  │   ═════════════════════════                                                                │   │
│  │                                                                                             │   │
│  │   File: app/agents/writer.py                                                               │   │
│  │                                                                                             │   │
│  │   ┌───────────────────────────────────────────────────────────────────────────────────┐   │   │
│  │   │                                                                                   │   │   │
│  │   │   INPUTS:                                                                         │   │   │
│  │   │   ├── facts_json (from Agent 1)                                                   │   │   │
│  │   │   └── typology_result (from Agent 2)                                              │   │   │
│  │   │                                                                                   │   │   │
│  │   │   CONSTITUTIONAL AI PRINCIPLES:                                                   │   │   │
│  │   │   ┌─────────────────────────────────────────────────────────────────────────┐   │   │   │
│  │   │   │  ✓ Only state facts supported by transaction data                       │   │   │   │
│  │   │   │  ✓ Do not speculate about customer intent                               │   │   │   │
│  │   │   │  ✓ Use formal regulatory language                                       │   │   │   │
│  │   │   │  ✓ Include specific dates, amounts, account numbers                     │   │   │   │
│  │   │   │  ✓ Cite FinCEN activity codes where applicable                          │   │   │   │
│  │   │   └─────────────────────────────────────────────────────────────────────────┘   │   │   │
│  │   │                                                                                   │   │   │
│  │   │   NARRATIVE SECTIONS:                                                             │   │   │
│  │   │   1. Subject Identification  → Customer name, PAN, account                        │   │   │
│  │   │   2. Activity Summary        → Transaction count, total amount, period            │   │   │
│  │   │   3. Transaction Details     → Amount ranges, types, destinations                 │   │   │
│  │   │   4. Pattern Analysis        → Typology, indicators, FinCEN code                  │   │   │
│  │   │   5. Conclusion              → Regulatory citation                                │   │   │
│  │   │                                                                                   │   │   │
│  │   │   OUTPUT: draft_narrative (5 paragraphs)                                          │   │   │
│  │   │                                                                                   │   │   │
│  │   └───────────────────────────────────────────────────────────────────────────────────┘   │   │
│  │                                                                                             │   │
│  └─────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                              │                                                      │
│                                              ▼                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │                                                                                             │   │
│  │   AGENT 4: FACT CHECKER                                                   Progress: 70-90% │   │
│  │   ═════════════════════                                                                    │   │
│  │                                                                                             │   │
│  │   File: app/agents/fact_checker.py                                                         │   │
│  │                                                                                             │   │
│  │   ┌───────────────────────────────────────────────────────────────────────────────────┐   │   │
│  │   │                                                                                   │   │   │
│  │   │   INPUTS:                                                                         │   │   │
│  │   │   ├── draft_narrative (from Agent 3)                                              │   │   │
│  │   │   └── facts_json (from Agent 1)                                                   │   │   │
│  │   │                                                                                   │   │   │
│  │   │   CLAIM EXTRACTION (using regex/NLP):                                             │   │   │
│  │   │   ├── Numbers: "47 transactions", "₹50,00,000"                                   │   │   │
│  │   │   ├── Dates: "January 5-12, 2026"                                                │   │   │
│  │   │   ├── Account refs: "account #****6789"                                          │   │   │
│  │   │   └── FinCEN codes: "31a", "31z"                                                 │   │   │
│  │   │                                                                                   │   │   │
│  │   │   VERIFICATION PROCESS:                                                           │   │   │
│  │   │   ┌─────────────────────────────────────────────────────────────────────────┐   │   │   │
│  │   │   │ Claim                    │ Expected    │ Actual      │ Status          │   │   │   │
│  │   │   │─────────────────────────────────────────────────────────────────────────│   │   │   │
│  │   │   │ "47 separate deposits"   │ 47          │ 47          │ ✓ VERIFIED      │   │   │   │
│  │   │   │ "₹50,00,000"             │ 5000000     │ 5000000     │ ✓ VERIFIED      │   │   │   │
│  │   │   │ "January 5-12, 2026"     │ date_range  │ matches     │ ✓ VERIFIED      │   │   │   │
│  │   │   │ "FinCEN Code 31a"        │ 31a         │ 31a         │ ✓ VERIFIED      │   │   │   │
│  │   │   └─────────────────────────────────────────────────────────────────────────┘   │   │   │
│  │   │                                                                                   │   │   │
│  │   │   OUTPUT: verification_result                                                     │   │   │
│  │   │   ┌─────────────────────────────────────────────────────────────────────────┐   │   │   │
│  │   │   │ {                                                                       │   │   │   │
│  │   │   │   "verified_narrative": "...",                                          │   │   │   │
│  │   │   │   "confidence": 0.998,                                                  │   │   │   │
│  │   │   │   "claims_verified": 23,                                                │   │   │   │
│  │   │   │   "claims_total": 23,                                                   │   │   │   │
│  │   │   │   "sentence_verifications": { 0: {...}, 1: {...}, ... }                │   │   │   │
│  │   │   │ }                                                                       │   │   │   │
│  │   │   └─────────────────────────────────────────────────────────────────────────┘   │   │   │
│  │   │                                                                                   │   │   │
│  │   └───────────────────────────────────────────────────────────────────────────────────┘   │   │
│  │                                                                                             │   │
│  └─────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                              │                                                      │
│                                              ▼                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │                                                                                             │   │
│  │   AGENT 5: EDITOR                                                        Progress: 90-100% │   │
│  │   ═══════════════                                                                          │   │
│  │                                                                                             │   │
│  │   File: app/agents/editor.py                                                               │   │
│  │                                                                                             │   │
│  │   ┌───────────────────────────────────────────────────────────────────────────────────┐   │   │
│  │   │                                                                                   │   │   │
│  │   │   INPUTS:                                                                         │   │   │
│  │   │   └── verified_narrative (from Agent 4)                                           │   │   │
│  │   │                                                                                   │   │   │
│  │   │   CHECKS PERFORMED:                                                               │   │   │
│  │   │   ├── Grammar check         → Fix contractions, punctuation                       │   │   │
│  │   │   ├── Style check           → Remove informal words, ensure formal tone           │   │   │
│  │   │   ├── Completeness check    → Verify all required sections present                │   │   │
│  │   │   └── Format cleanup        → Normalize spacing, paragraphs                       │   │   │
│  │   │                                                                                   │   │   │
│  │   │   STYLE RULES:                                                                    │   │   │
│  │   │   ┌─────────────────────────────────────────────────────────────────────────┐   │   │   │
│  │   │   │  Informal        →  Formal                                              │   │   │   │
│  │   │   │  "don't"         →  "do not"                                            │   │   │   │
│  │   │   │  "got"           →  "received"                                          │   │   │   │
│  │   │   │  "lots of"       →  "numerous"                                          │   │   │   │
│  │   │   │  "basically"     →  [removed]                                           │   │   │   │
│  │   │   └─────────────────────────────────────────────────────────────────────────┘   │   │   │
│  │   │                                                                                   │   │   │
│  │   │   OUTPUT: final_sar_narrative                                                     │   │   │
│  │   │                                                                                   │   │   │
│  │   └───────────────────────────────────────────────────────────────────────────────────┘   │   │
│  │                                                                                             │   │
│  └─────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                              │                                                      │
│                                              ▼                                                      │
│  OUTPUT: Complete SAR with audit trail                                                             │
│                                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Database Schema

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                      DATABASE SCHEMA                                                │
├─────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                     │
│                                                                                                     │
│    ┌─────────────────────┐         ┌─────────────────────┐         ┌─────────────────────┐         │
│    │     CUSTOMERS       │         │       ALERTS        │         │        SARS         │         │
│    ├─────────────────────┤         ├─────────────────────┤         ├─────────────────────┤         │
│    │ id           PK     │◄────┐   │ id           PK     │◄────┐   │ id           PK     │         │
│    │ name                │     │   │ trigger_date        │     │   │ alert_id     FK     │────┐    │
│    │ dob                 │     │   │ scenario            │     │   │ narrative          │    │    │
│    │ pan                 │     │   │ risk_score          │     │   │ typology           │    │    │
│    │ address             │     └───│ customer_id  FK     │     │   │ fincen_code        │    │    │
│    │ occupation          │         │ status              │     │   │ status             │    │    │
│    │ income_source       │         │ assigned_to         │     │   │ confidence_score   │    │    │
│    │ account_number      │         │ created_at          │     │   │ sentence_count     │    │    │
│    │ account_type        │         │ updated_at          │     │   │ created_by         │    │    │
│    │ account_open_date   │         └─────────────────────┘     │   │ approved_by        │    │    │
│    │ created_at          │                    │                │   │ approved_at        │    │    │
│    └─────────────────────┘                    │                │   │ filing_id          │    │    │
│              │                                │                │   │ submitted_at       │    │    │
│              │                                │                │   │ created_at         │    │    │
│              │                                │                │   │ updated_at         │    │    │
│              │                                │                │   └─────────────────────┘    │    │
│              │                                │                │              │               │    │
│              │                                ▼                │              │               │    │
│              │         ┌─────────────────────────────────┐    │              │               │    │
│              │         │        TRANSACTIONS             │    │              │               │    │
│              │         ├─────────────────────────────────┤    │              │               │    │
│              │         │ id                   PK         │    │              │               │    │
│              └────────►│ alert_id             FK         │────┘              │               │    │
│                        │ customer_id          FK         │                   │               │    │
│                        │ date                            │                   │               │    │
│                        │ amount                          │                   │               │    │
│                        │ type                            │                   ▼               │    │
│                        │ direction                       │    ┌─────────────────────┐       │    │
│                        │ source_account                  │    │    AUDIT_LOGS       │       │    │
│                        │ destination_account             │    ├─────────────────────┤       │    │
│                        │ source_location                 │    │ id           PK     │       │    │
│                        │ destination_location            │    │ sar_id       FK     │◄──────┘    │
│                        │ description                     │    │ sentence_index      │            │
│                        │ is_suspicious                   │    │ entry_type          │            │
│                        │ created_at                      │    │ data         JSON   │            │
│                        └─────────────────────────────────┘    │ confidence          │            │
│                                                               │ timestamp           │            │
│                                                               └─────────────────────┘            │
│                                                                                                   │
│                                                                                                   │
│    RELATIONSHIPS:                                                                                 │
│    ═══════════════                                                                                │
│    Customers 1:N Alerts         (A customer can have multiple alerts)                            │
│    Customers 1:N Transactions   (A customer can have multiple transactions)                      │
│    Alerts 1:N Transactions      (An alert has multiple flagged transactions)                     │
│    Alerts 1:N SARs              (An alert can have multiple SAR versions)                        │
│    SARs 1:N Audit_Logs          (A SAR has multiple audit log entries)                           │
│                                                                                                   │
│                                                                                                   │
└───────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## API Request/Response Flow

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                               API REQUEST/RESPONSE FLOW                                             │
├─────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                     │
│  EXAMPLE: POST /api/sar/generate                                                                    │
│  ═══════════════════════════════                                                                    │
│                                                                                                     │
│     Client                Router               Service               Agents                DB       │
│       │                     │                    │                     │                   │        │
│       │  POST /generate     │                    │                     │                   │        │
│       │  {alert_id: "X"}    │                    │                     │                   │        │
│       │────────────────────►│                    │                     │                   │        │
│       │                     │                    │                     │                   │        │
│       │                     │  validate alert    │                     │                   │        │
│       │                     │───────────────────►│                     │                   │        │
│       │                     │                    │  get_alert_by_id    │                   │        │
│       │                     │                    │─────────────────────────────────────────►│        │
│       │                     │                    │◄─────────────────────────────────────────│        │
│       │                     │◄───────────────────│                     │                   │        │
│       │                     │                    │                     │                   │        │
│       │                     │  start background  │                     │                   │        │
│       │                     │  task              │                     │                   │        │
│       │                     │───────────────────►│                     │                   │        │
│       │                     │                    │                     │                   │        │
│       │  {task_id, sar_id,  │                    │  ┌─────────────────────────────────────┐│        │
│       │   status: process}  │                    │  │  BACKGROUND TASK                   ││        │
│       │◄────────────────────│                    │  │                                    ││        │
│       │                     │                    │  │  Agent 1: extract_facts()          ││        │
│       │                     │                    │  │         │                          ││        │
│       │                     │                    │  │         ▼                          ││        │
│       │  WS /ws/sar/{task}  │                    │  │  Agent 2: classify_typology()      ││        │
│       │════════════════════►│                    │  │         │                          ││        │
│       │                     │                    │  │         ▼                          ││        │
│       │  progress: 20%      │                    │  │  Agent 3: generate_narrative()     ││        │
│       │◄════════════════════│                    │  │         │                          ││        │
│       │                     │                    │  │         ▼                          ││        │
│       │  progress: 40%      │                    │  │  Agent 4: verify_narrative()       ││        │
│       │◄════════════════════│                    │  │         │                          ││        │
│       │                     │                    │  │         ▼                          ││        │
│       │  progress: 70%      │                    │  │  Agent 5: polish_narrative()       ││        │
│       │◄════════════════════│                    │  │         │                          ││        │
│       │                     │                    │  │         ▼                          ││        │
│       │  progress: 100%     │                    │  │  create_sar() ─────────────────────────────►│
│       │  status: complete   │                    │  │  create_audit_logs() ──────────────────────►│
│       │◄════════════════════│                    │  │                                    ││        │
│       │                     │                    │  └─────────────────────────────────────┘│        │
│       │                     │                    │                     │                   │        │
│       │  GET /sar/{id}      │                    │                     │                   │        │
│       │────────────────────►│                    │                     │                   │        │
│       │                     │  get_sar_by_id     │                     │                   │        │
│       │                     │───────────────────►│                     │                   │        │
│       │                     │                    │─────────────────────────────────────────►│        │
│       │                     │                    │◄─────────────────────────────────────────│        │
│       │  {sar_data}         │◄───────────────────│                     │                   │        │
│       │◄────────────────────│                    │                     │                   │        │
│       │                     │                    │                     │                   │        │
│                                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

**Document Version:** 1.0
**Last Updated:** February 2026
