# SAR NARRATIVE GENERATOR - SYSTEM ARCHITECTURE

## High-Level Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                                     │
│                           SAR NARRATIVE GENERATOR WITH AUDIT TRAIL                                  │
│                                                                                                     │
│  ┌───────────────────────────────────────────────────────────────────────────────────────────────┐  │
│  │                                    REACT FRONTEND (Port 5173)                                 │  │
│  │                                                                                               │  │
│  │   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                  │  │
│  │   │  Dashboard  │    │   Alerts    │    │     SAR     │    │   History   │                  │  │
│  │   │    Page     │    │    Queue    │    │  Workspace  │    │    View     │                  │  │
│  │   └─────────────┘    └─────────────┘    └──────┬──────┘    └─────────────┘                  │  │
│  │                                                │                                             │  │
│  │                           ┌────────────────────┼────────────────────┐                        │  │
│  │                           │                    │                    │                        │  │
│  │                    ┌──────▼──────┐      ┌──────▼──────┐      ┌──────▼──────┐                │  │
│  │                    │  Narrative  │      │   Audit     │      │ Transaction │                │  │
│  │                    │   Panel     │◄────►│   Trail     │      │    Graph    │                │  │
│  │                    │ (Clickable) │      │   Panel     │      │ (ReactFlow) │                │  │
│  │                    └─────────────┘      └─────────────┘      └─────────────┘                │  │
│  │                                                                                               │  │
│  │   ┌─────────────────────────────────────────────────────────────────────────────────────┐   │  │
│  │   │                         STATE MANAGEMENT (TanStack Query)                            │   │  │
│  │   │    useAlerts()  │  useSARGeneration()  │  useAuditTrail()  │  useTransactions()     │   │  │
│  │   └─────────────────────────────────────────────────────────────────────────────────────┘   │  │
│  └───────────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                              │                                                      │
│                                              │ REST API + WebSocket                                 │
│                                              ▼                                                      │
│  ┌───────────────────────────────────────────────────────────────────────────────────────────────┐  │
│  │                                  FASTAPI BACKEND (Port 8000)                                  │  │
│  │                                                                                               │  │
│  │   ┌─────────────────────────────────────────────────────────────────────────────────────┐   │  │
│  │   │                                   API LAYER                                          │   │  │
│  │   │                                                                                      │   │  │
│  │   │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌────────────┐│   │  │
│  │   │  │ /api/alerts  │ │  /api/sar    │ │ /api/audit   │ │/api/transact │ │ /ws/sar    ││   │  │
│  │   │  │              │ │  /generate   │ │  /evidence   │ │  /graph      │ │ (WebSocket)││   │  │
│  │   │  │  GET list    │ │  POST create │ │  GET trail   │ │  GET nodes   │ │  Progress  ││   │  │
│  │   │  │  GET by id   │ │  PATCH edit  │ │  GET by idx  │ │  GET edges   │ │  Updates   ││   │  │
│  │   │  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘ └────────────┘│   │  │
│  │   └─────────────────────────────────────────────────────────────────────────────────────┘   │  │
│  │                                              │                                               │  │
│  │   ┌──────────────────────────────────────────┴──────────────────────────────────────────┐   │  │
│  │   │                              SERVICE LAYER                                           │   │  │
│  │   │                                                                                      │   │  │
│  │   │   ┌────────────────┐   ┌────────────────┐   ┌────────────────┐   ┌────────────────┐ │   │  │
│  │   │   │ SARGenerator   │   │  AuditTrail    │   │  FactChecker   │   │  PDFExporter   │ │   │  │
│  │   │   │    Service     │   │    Service     │   │    Service     │   │    Service     │ │   │  │
│  │   │   └───────┬────────┘   └────────────────┘   └────────────────┘   └────────────────┘ │   │  │
│  │   └───────────┼──────────────────────────────────────────────────────────────────────────┘   │  │
│  │               │                                                                              │  │
│  │               ▼                                                                              │  │
│  │   ┌─────────────────────────────────────────────────────────────────────────────────────┐   │  │
│  │   │                     MULTI-AGENT PIPELINE (LangGraph)                                 │   │  │
│  │   │                                                                                      │   │  │
│  │   │   ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐          │   │  │
│  │   │   │ AGENT 1 │    │ AGENT 2 │    │ AGENT 3 │    │ AGENT 4 │    │ AGENT 5 │          │   │  │
│  │   │   │  Data   │───►│Complian-│───►│Narrative│───►│  Fact   │───►│ Editor  │          │   │  │
│  │   │   │ Analyst │    │   ce    │    │ Writer  │    │ Checker │    │         │          │   │  │
│  │   │   └────┬────┘    └────┬────┘    └────┬────┘    └────┬────┘    └────┬────┘          │   │  │
│  │   │        │              │              │              │              │               │   │  │
│  │   │        │              │              │              │              │               │   │  │
│  │   │   ┌────▼────┐    ┌────▼────┐    ┌────▼────┐    ┌────▼────┐    ┌────▼────┐          │   │  │
│  │   │   │  SQL    │    │Typology │    │   RAG   │    │  Claim  │    │ Grammar │          │   │  │
│  │   │   │ Queries │    │ Classify│    │ + LLM   │    │ Verify  │    │  Check  │          │   │  │
│  │   │   └─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘          │   │  │
│  │   │                                                                                      │   │  │
│  │   │   Output: facts_json → typology → draft_narrative → verified_narrative → final_sar  │   │  │
│  │   └─────────────────────────────────────────────────────────────────────────────────────┘   │  │
│  │                                              │                                               │  │
│  └──────────────────────────────────────────────┼───────────────────────────────────────────────┘  │
│                                                 │                                                   │
│                    ┌────────────────────────────┼────────────────────────────┐                     │
│                    │                            │                            │                     │
│                    ▼                            ▼                            ▼                     │
│  ┌──────────────────────────┐  ┌──────────────────────────┐  ┌──────────────────────────┐         │
│  │                          │  │                          │  │                          │         │
│  │      POSTGRESQL          │  │       CHROMADB           │  │        OLLAMA            │         │
│  │      (Port 5432)         │  │    (Vector Store)        │  │     (Port 11434)         │         │
│  │                          │  │                          │  │                          │         │
│  │  ┌────────────────────┐  │  │  ┌────────────────────┐  │  │  ┌────────────────────┐  │         │
│  │  │     alerts         │  │  │  │  FinCEN Typologies │  │  │  │   Llama 3.1 8B     │  │         │
│  │  │     customers      │  │  │  │  (31 categories)   │  │  │  │   (Local LLM)      │  │         │
│  │  │     transactions   │  │  │  ├────────────────────┤  │  │  │                    │  │         │
│  │  │     cases          │  │  │  │  FATF Guidelines   │  │  │  │   - Narrative Gen  │  │         │
│  │  │     sar_reports    │  │  │  │  (40 Recommends)   │  │  │  │   - Fact Checking  │  │         │
│  │  │     audit_logs     │  │  │  ├────────────────────┤  │  │  │   - Classification │  │         │
│  │  └────────────────────┘  │  │  │  Historical SARs   │  │  │  └────────────────────┘  │         │
│  │                          │  │  │  (500+ approved)   │  │  │                          │         │
│  │  Stores:                 │  │  └────────────────────┘  │  │  Constitutional AI:      │         │
│  │  - Transaction data      │  │                          │  │  - No speculation        │         │
│  │  - Customer KYC          │  │  Embedding Model:        │  │  - Formal language       │         │
│  │  - Audit trail entries   │  │  all-MiniLM-L6-v2        │  │  - Fact-grounded only    │         │
│  │  - SAR versions          │  │                          │  │                          │         │
│  └──────────────────────────┘  └──────────────────────────┘  └──────────────────────────┘         │
│                                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                        DATA FLOW                                                    │
├─────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                     │
│   ┌──────────────┐                                                                                  │
│   │   ANALYST    │                                                                                  │
│   │    (User)    │                                                                                  │
│   └──────┬───────┘                                                                                  │
│          │                                                                                          │
│          │ 1. Select Alert                                                                          │
│          ▼                                                                                          │
│   ┌──────────────┐      2. Fetch Alert Data       ┌──────────────┐                                 │
│   │    React     │ ──────────────────────────────►│   FastAPI    │                                 │
│   │   Frontend   │                                │   Backend    │                                 │
│   └──────────────┘                                └──────┬───────┘                                 │
│          │                                               │                                          │
│          │ 3. Click "Generate SAR"                       │ 4. Query Database                       │
│          │                                               ▼                                          │
│          │                                        ┌──────────────┐                                 │
│          │                                        │  PostgreSQL  │                                 │
│          │                                        │  - Alerts    │                                 │
│          │                                        │  - Customers │                                 │
│          │                                        │  - Txns      │                                 │
│          │                                        └──────┬───────┘                                 │
│          │                                               │                                          │
│          │                                               │ 5. Return Facts                         │
│          │                                               ▼                                          │
│          │    ┌─────────────────────────────────────────────────────────────────────────────┐      │
│          │    │                        MULTI-AGENT PIPELINE                                  │      │
│          │    │                                                                              │      │
│          │    │  facts_json ──► Agent 1 ──► Agent 2 ──► Agent 3 ──► Agent 4 ──► Agent 5    │      │
│          │    │                  │           │           │           │           │          │      │
│          │    │                  │           │           │           │           │          │      │
│          │    │                  ▼           ▼           ▼           ▼           ▼          │      │
│          │    │               ┌─────┐    ┌─────┐    ┌─────────┐  ┌─────┐    ┌─────┐        │      │
│          │    │               │ SQL │    │ RAG │    │ Ollama  │  │Verify│   │Polish│        │      │
│          │    │               │Query│    │Fetch│    │  LLM    │  │Claims│   │Grammar│       │      │
│          │    │               └──┬──┘    └──┬──┘    └────┬────┘  └──┬──┘    └──┬──┘        │      │
│          │    │                  │          │            │          │          │            │      │
│          │    │                  ▼          ▼            │          │          │            │      │
│          │    │            PostgreSQL   ChromaDB         │          │          │            │      │
│          │    │                                          │          │          │            │      │
│          │    └──────────────────────────────────────────┼──────────┼──────────┼────────────┘      │
│          │                                               │          │          │                    │
│          │    6. WebSocket Progress Updates              │          │          │                    │
│          │◄──────────────────────────────────────────────┘          │          │                    │
│          │                                                          │          │                    │
│          │    7. Final SAR + Audit Trail                            │          │                    │
│          │◄─────────────────────────────────────────────────────────┴──────────┘                    │
│          │                                                                                          │
│          ▼                                                                                          │
│   ┌──────────────┐                                                                                  │
│   │  Split View  │                                                                                  │
│   │              │                                                                                  │
│   │ ┌──────────┐ │      8. Click Sentence           ┌──────────────┐                               │
│   │ │Narrative │ │ ────────────────────────────────►│   FastAPI    │                               │
│   │ │  Panel   │ │                                  │  /evidence   │                               │
│   │ └──────────┘ │                                  └──────┬───────┘                               │
│   │ ┌──────────┐ │      9. Return Evidence                 │                                       │
│   │ │  Audit   │ │◄────────────────────────────────────────┘                                       │
│   │ │  Trail   │ │                                                                                  │
│   │ └──────────┘ │                                                                                  │
│   └──────────────┘                                                                                  │
│          │                                                                                          │
│          │ 10. Approve & Submit                                                                     │
│          ▼                                                                                          │
│   ┌──────────────┐                                                                                  │
│   │  PDF Export  │ ──────► Regulatory Filing (FinCEN)                                              │
│   │ + Audit Pkg  │                                                                                  │
│   └──────────────┘                                                                                  │
│                                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Multi-Agent Pipeline Detail

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              MULTI-AGENT PIPELINE (LangGraph)                                       │
├─────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                     │
│  INPUT                                                                                              │
│  ─────                                                                                              │
│  alert_id: "ALT_001"                                                                                │
│  customer: "Rajesh Kumar"                                                                           │
│  transactions: [47 records]                                                                         │
│                                                                                                     │
│         │                                                                                           │
│         ▼                                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │  AGENT 1: DATA ANALYST                                                                       │   │
│  │  ═══════════════════════                                                                     │   │
│  │                                                                                              │   │
│  │  Tools: execute_sql(), aggregate_stats()                                                     │   │
│  │                                                                                              │   │
│  │  Actions:                                                                                    │   │
│  │  ├─ SELECT COUNT(*), SUM(amount) FROM transactions WHERE alert_id = 'ALT_001'               │   │
│  │  ├─ SELECT MIN(date), MAX(date) FROM transactions WHERE alert_id = 'ALT_001'                │   │
│  │  └─ SELECT DISTINCT source_account FROM transactions WHERE alert_id = 'ALT_001'             │   │
│  │                                                                                              │   │
│  │  Output: facts_json = {                                                                      │   │
│  │    "txn_count": 47,                                                                          │   │
│  │    "total_amount": 5000000,                                                                  │   │
│  │    "date_range": ["2026-01-05", "2026-01-12"],                                               │   │
│  │    "unique_sources": 47,                                                                     │   │
│  │    "avg_amount": 106382                                                                      │   │
│  │  }                                                                                           │   │
│  │                                                                                              │   │
│  │  Audit Log: ✓ Query text, results, timestamp                                                 │   │
│  └──────────────────────────────────────────────────────────────────────────────────────────────┘   │
│         │                                                                                           │
│         ▼                                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │  AGENT 2: COMPLIANCE SPECIALIST                                                              │   │
│  │  ══════════════════════════════                                                              │   │
│  │                                                                                              │   │
│  │  Tools: classify_typology(), retrieve_fincen_code(), search_regulations()                    │   │
│  │                                                                                              │   │
│  │  Actions:                                                                                    │   │
│  │  ├─ Analyze pattern: 47 deposits from unique sources in 7 days                              │   │
│  │  ├─ Match to typology: STRUCTURING (multiple small deposits)                                │   │
│  │  └─ Retrieve FinCEN code: 31a - Structuring                                                 │   │
│  │                                                                                              │   │
│  │  RAG Query: "What are indicators of structuring activity?"                                   │   │
│  │  Retrieved: "Structuring involves breaking transactions into smaller amounts..."             │   │
│  │                                                                                              │   │
│  │  Output: {                                                                                   │   │
│  │    "typology": "Structuring",                                                                │   │
│  │    "fincen_code": "31a",                                                                     │   │
│  │    "confidence": 0.94,                                                                       │   │
│  │    "indicators": ["multiple_sources", "rapid_timeframe", "similar_amounts"]                 │   │
│  │  }                                                                                           │   │
│  │                                                                                              │   │
│  │  Audit Log: ✓ Classification reasoning, retrieved docs, confidence                          │   │
│  └──────────────────────────────────────────────────────────────────────────────────────────────┘   │
│         │                                                                                           │
│         ▼                                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │  AGENT 3: NARRATIVE WRITER (Llama 3.1 via Ollama)                                           │   │
│  │  ════════════════════════════════════════════════                                            │   │
│  │                                                                                              │   │
│  │  Tools: retrieve_sar_examples(), generate_paragraph()                                        │   │
│  │                                                                                              │   │
│  │  Constitutional AI Principles:                                                               │   │
│  │  ├─ ✓ Only state facts supported by data                                                    │   │
│  │  ├─ ✓ No speculation about intent                                                           │   │
│  │  ├─ ✓ Use formal regulatory language                                                        │   │
│  │  └─ ✓ Include specific dates, amounts, codes                                                │   │
│  │                                                                                              │   │
│  │  RAG: Retrieve 3 similar historical SARs as examples                                         │   │
│  │                                                                                              │   │
│  │  Output: draft_narrative = """                                                               │   │
│  │    Review of account activity for Rajesh Kumar (PAN: ABCDE1234F),                           │   │
│  │    savings account #123456789, revealed suspicious transaction patterns                      │   │
│  │    during the period January 5-12, 2026.                                                    │   │
│  │                                                                                              │   │
│  │    The subject received 47 separate deposits totaling ₹50,00,000...                         │   │
│  │  """                                                                                         │   │
│  │                                                                                              │   │
│  │  Audit Log: ✓ Full prompt, response, temperature, retrieved examples                        │   │
│  └──────────────────────────────────────────────────────────────────────────────────────────────┘   │
│         │                                                                                           │
│         ▼                                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │  AGENT 4: FACT CHECKER                                                                       │   │
│  │  ═════════════════════                                                                       │   │
│  │                                                                                              │   │
│  │  Tools: extract_claims(), verify_claim()                                                     │   │
│  │                                                                                              │   │
│  │  Process:                                                                                    │   │
│  │  ┌────────────────────────────────────────────────────────────────────────────────────────┐ │   │
│  │  │ Sentence                              │ Claim           │ Verification    │ Result    │ │   │
│  │  ├────────────────────────────────────────────────────────────────────────────────────────┤ │   │
│  │  │ "received 47 separate deposits"       │ count = 47      │ SQL: COUNT(*)   │ ✓ PASS    │ │   │
│  │  │ "totaling ₹50,00,000"                 │ sum = 5000000   │ SQL: SUM(amt)   │ ✓ PASS    │ │   │
│  │  │ "January 5-12, 2026"                  │ date range      │ SQL: MIN/MAX    │ ✓ PASS    │ │   │
│  │  │ "from 47 distinct accounts"           │ unique = 47     │ SQL: DISTINCT   │ ✓ PASS    │ │   │
│  │  └────────────────────────────────────────────────────────────────────────────────────────┘ │   │
│  │                                                                                              │   │
│  │  Output: verified_narrative (same as draft, all claims passed)                               │   │
│  │  Confidence: 100% (all 23 claims verified)                                                   │   │
│  │                                                                                              │   │
│  │  Audit Log: ✓ Each claim, verification query, result, confidence score                      │   │
│  └──────────────────────────────────────────────────────────────────────────────────────────────┘   │
│         │                                                                                           │
│         ▼                                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │  AGENT 5: EDITOR                                                                             │   │
│  │  ═══════════════                                                                             │   │
│  │                                                                                              │   │
│  │  Tools: grammar_check(), style_check(), completeness_check()                                 │   │
│  │                                                                                              │   │
│  │  Checks:                                                                                     │   │
│  │  ├─ ✓ Grammar: No errors                                                                    │   │
│  │  ├─ ✓ Style: Formal regulatory tone                                                         │   │
│  │  ├─ ✓ Completeness: All required sections present                                           │   │
│  │  │   □ Subject identification                                                               │   │
│  │  │   □ Time period                                                                          │   │
│  │  │   □ Transaction summary                                                                  │   │
│  │  │   □ Suspicious indicators                                                                │   │
│  │  │   □ Typology classification                                                              │   │
│  │  └─ ✓ FinCEN code cited                                                                     │   │
│  │                                                                                              │   │
│  │  Output: final_sar_narrative (polished, ready for review)                                    │   │
│  │                                                                                              │   │
│  │  Audit Log: ✓ Edits made, style violations fixed, final quality score                       │   │
│  └──────────────────────────────────────────────────────────────────────────────────────────────┘   │
│         │                                                                                           │
│         ▼                                                                                           │
│  OUTPUT                                                                                             │
│  ══════                                                                                             │
│  {                                                                                                  │
│    "sar_id": "SAR_2026_00123",                                                                      │
│    "narrative": "Review of account activity for Rajesh Kumar...",                                   │
│    "typology": "Structuring",                                                                       │
│    "fincen_code": "31a",                                                                            │
│    "confidence": 0.998,                                                                             │
│    "audit_trail": [                                                                                 │
│      { "sentence_idx": 0, "evidence": {...}, "confidence": 1.0 },                                  │
│      { "sentence_idx": 1, "evidence": {...}, "confidence": 1.0 },                                  │
│      ...                                                                                            │
│    ]                                                                                                │
│  }                                                                                                  │
│                                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Transaction Flow Graph (React Flow)

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              TRANSACTION FLOW VISUALIZATION                                         │
├─────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                     │
│   ┌──────────────────────────────────────────────────────────────────────────────────────────┐     │
│   │                                                                              [+] [-] [⟲] │     │
│   │                                                                                          │     │
│   │     ┌─────────────┐                                                                      │     │
│   │     │  Account A  │                                                                      │     │
│   │     │   Mumbai    │────────────────────┐                                                 │     │
│   │     │   ₹98,000   │                    │                                                 │     │
│   │     └─────────────┘                    │                                                 │     │
│   │                                        │                                                 │     │
│   │     ┌─────────────┐                    │      ₹98K                                       │     │
│   │     │  Account B  │                    │                                                 │     │
│   │     │   Delhi     │────────────────────┼──────────────┐                                  │     │
│   │     │   ₹95,000   │         ₹95K       │              │                                  │     │
│   │     └─────────────┘                    │              │                                  │     │
│   │                                        │              ▼                                  │     │
│   │     ┌─────────────┐                    │    ╔═══════════════════╗        ┌────────────┐ │     │
│   │     │  Account C  │                    └───►║     SUBJECT       ║        │  OFFSHORE  │ │     │
│   │     │   Chennai   │─────────────────────────║   Rajesh Kumar    ║═══════►│  Cayman    │ │     │
│   │     │   ₹92,000   │         ₹92K           ║   Account ****6789 ║  ₹48.5L│  Islands   │ │     │
│   │     └─────────────┘                    ┌───►║   Mumbai          ║        │   🔴       │ │     │
│   │                                        │    ╚═══════════════════╝        └────────────┘ │     │
│   │     ┌─────────────┐                    │              ▲                                  │     │
│   │     │  Account D  │                    │              │                                  │     │
│   │     │   Pune      │────────────────────┘              │                                  │     │
│   │     │   ₹97,000   │         ₹97K                      │                                  │     │
│   │     └─────────────┘                                   │                                  │     │
│   │           .                                           │                                  │     │
│   │           .                                           │                                  │     │
│   │           .                                           │                                  │     │
│   │     ┌─────────────┐                                   │                                  │     │
│   │     │ Account 47  │───────────────────────────────────┘                                  │     │
│   │     │  Bangalore  │         ₹1,05,000                                                    │     │
│   │     │  ₹1,05,000  │                                                                      │     │
│   │     └─────────────┘                                                                      │     │
│   │                                                                                          │     │
│   │  ┌────────────────────────────────────────────────────────────────────────────────────┐ │     │
│   │  │  LEGEND                                                                            │ │     │
│   │  │  ═══════                                                                           │ │     │
│   │  │  ╔═══╗ Subject Account (under investigation)                                       │ │     │
│   │  │  ┌───┐ Source/Destination Account                                                  │ │     │
│   │  │   🔴  High-Risk Jurisdiction                                                       │ │     │
│   │  │  ═══► Large transfer (>₹10L)                                                       │ │     │
│   │  │  ───► Standard transfer                                                            │ │     │
│   │  └────────────────────────────────────────────────────────────────────────────────────┘ │     │
│   │                                                                                          │     │
│   │  [MiniMap]                                                                               │     │
│   │  ┌──────┐                                                                                │     │
│   │  │ •••  │                                                                                │     │
│   │  │  •   │                                                                                │     │
│   │  └──────┘                                                                                │     │
│   └──────────────────────────────────────────────────────────────────────────────────────────┘     │
│                                                                                                     │
│   PATTERN DETECTED: 47 inbound transfers from unique sources → 1 large outbound to offshore       │
│   TYPOLOGY: Layering / Collection Account                                                          │
│                                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Audit Trail Structure

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    AUDIT TRAIL SCHEMA                                               │
├─────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                     │
│  SAR Narrative Sentence:                                                                            │
│  "The subject received 47 separate deposits totaling ₹50,00,000 from 47 distinct accounts"         │
│                                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │  AUDIT ENTRY                                                                                 │   │
│  ├─────────────────────────────────────────────────────────────────────────────────────────────┤   │
│  │                                                                                              │   │
│  │  sentence_index: 1                                                                           │   │
│  │  sentence_text: "The subject received 47 separate deposits totaling ₹50,00,000..."          │   │
│  │                                                                                              │   │
│  │  ┌────────────────────────────────────────────────────────────────────────────────────────┐ │   │
│  │  │  DATA SOURCES                                                                          │ │   │
│  │  ├────────────────────────────────────────────────────────────────────────────────────────┤ │   │
│  │  │  table: "transactions"                                                                 │ │   │
│  │  │  database: "sar_db"                                                                    │ │   │
│  │  │  query_timestamp: "2026-02-15T10:23:45Z"                                               │ │   │
│  │  └────────────────────────────────────────────────────────────────────────────────────────┘ │   │
│  │                                                                                              │   │
│  │  ┌────────────────────────────────────────────────────────────────────────────────────────┐ │   │
│  │  │  SQL QUERIES EXECUTED                                                                  │ │   │
│  │  ├────────────────────────────────────────────────────────────────────────────────────────┤ │   │
│  │  │                                                                                        │ │   │
│  │  │  Query 1: Transaction Count                                                            │ │   │
│  │  │  ┌──────────────────────────────────────────────────────────────────────────────────┐ │ │   │
│  │  │  │ SELECT COUNT(*) as txn_count                                                     │ │ │   │
│  │  │  │ FROM transactions                                                                │ │ │   │
│  │  │  │ WHERE alert_id = 'ALT_001'                                                       │ │ │   │
│  │  │  │   AND direction = 'INBOUND';                                                     │ │ │   │
│  │  │  └──────────────────────────────────────────────────────────────────────────────────┘ │ │   │
│  │  │  Result: { "txn_count": 47 }                                                           │ │   │
│  │  │                                                                                        │ │   │
│  │  │  Query 2: Total Amount                                                                 │ │   │
│  │  │  ┌──────────────────────────────────────────────────────────────────────────────────┐ │ │   │
│  │  │  │ SELECT SUM(amount) as total_amount                                               │ │ │   │
│  │  │  │ FROM transactions                                                                │ │ │   │
│  │  │  │ WHERE alert_id = 'ALT_001'                                                       │ │ │   │
│  │  │  │   AND direction = 'INBOUND';                                                     │ │ │   │
│  │  │  └──────────────────────────────────────────────────────────────────────────────────┘ │ │   │
│  │  │  Result: { "total_amount": 5000000 }                                                   │ │   │
│  │  │                                                                                        │ │   │
│  │  │  Query 3: Unique Sources                                                               │ │   │
│  │  │  ┌──────────────────────────────────────────────────────────────────────────────────┐ │ │   │
│  │  │  │ SELECT COUNT(DISTINCT source_account) as unique_sources                          │ │ │   │
│  │  │  │ FROM transactions                                                                │ │ │   │
│  │  │  │ WHERE alert_id = 'ALT_001';                                                      │ │ │   │
│  │  │  └──────────────────────────────────────────────────────────────────────────────────┘ │ │   │
│  │  │  Result: { "unique_sources": 47 }                                                      │ │   │
│  │  │                                                                                        │ │   │
│  │  └────────────────────────────────────────────────────────────────────────────────────────┘ │   │
│  │                                                                                              │   │
│  │  ┌────────────────────────────────────────────────────────────────────────────────────────┐ │   │
│  │  │  CLAIM VERIFICATION                                                                    │ │   │
│  │  ├────────────────────────────────────────────────────────────────────────────────────────┤ │   │
│  │  │                                                                                        │ │   │
│  │  │  ┌─────────────────────────┬──────────────┬──────────────┬────────────┬─────────────┐│ │   │
│  │  │  │ Claim                   │ Expected     │ Actual       │ Match      │ Confidence  ││ │   │
│  │  │  ├─────────────────────────┼──────────────┼──────────────┼────────────┼─────────────┤│ │   │
│  │  │  │ "47 separate deposits"  │ 47           │ 47           │ ✓ EXACT    │ 100%        ││ │   │
│  │  │  │ "₹50,00,000"            │ 5000000      │ 5000000      │ ✓ EXACT    │ 100%        ││ │   │
│  │  │  │ "47 distinct accounts"  │ 47           │ 47           │ ✓ EXACT    │ 100%        ││ │   │
│  │  │  └─────────────────────────┴──────────────┴──────────────┴────────────┴─────────────┘│ │   │
│  │  │                                                                                        │ │   │
│  │  │  Overall Confidence: 100%                                                              │ │   │
│  │  │  Verification Status: ✅ ALL CLAIMS VERIFIED                                           │ │   │
│  │  │                                                                                        │ │   │
│  │  └────────────────────────────────────────────────────────────────────────────────────────┘ │   │
│  │                                                                                              │   │
│  │  ┌────────────────────────────────────────────────────────────────────────────────────────┐ │   │
│  │  │  LLM GENERATION LOG                                                                    │ │   │
│  │  ├────────────────────────────────────────────────────────────────────────────────────────┤ │   │
│  │  │                                                                                        │ │   │
│  │  │  model: "llama-3.1-8b"                                                                 │ │   │
│  │  │  temperature: 0.3                                                                      │ │   │
│  │  │  timestamp: "2026-02-15T10:23:48Z"                                                     │ │   │
│  │  │                                                                                        │ │   │
│  │  │  prompt: """                                                                           │ │   │
│  │  │    Generate a formal SAR sentence describing inbound transactions.                    │ │   │
│  │  │    Facts: txn_count=47, total=5000000, unique_sources=47                              │ │   │
│  │  │    Style: Formal, regulatory, specific numbers                                        │ │   │
│  │  │  """                                                                                   │ │   │
│  │  │                                                                                        │ │   │
│  │  │  response: "The subject received 47 separate deposits totaling ₹50,00,000             │ │   │
│  │  │            from 47 distinct accounts during the review period."                       │ │   │
│  │  │                                                                                        │ │   │
│  │  │  tokens_used: { prompt: 89, completion: 24, total: 113 }                              │ │   │
│  │  │                                                                                        │ │   │
│  │  └────────────────────────────────────────────────────────────────────────────────────────┘ │   │
│  │                                                                                              │   │
│  │  ┌────────────────────────────────────────────────────────────────────────────────────────┐ │   │
│  │  │  REASONING TRACE                                                                       │ │   │
│  │  ├────────────────────────────────────────────────────────────────────────────────────────┤ │   │
│  │  │                                                                                        │ │   │
│  │  │  Why this language was chosen:                                                         │ │   │
│  │  │  1. "received" - Neutral verb, doesn't imply intent                                   │ │   │
│  │  │  2. "47 separate deposits" - Exact count from database                                │ │   │
│  │  │  3. "₹50,00,000" - Indian format, exact sum from query                                │ │   │
│  │  │  4. "47 distinct accounts" - Highlights unique sources (red flag)                     │ │   │
│  │  │                                                                                        │ │   │
│  │  │  Constitutional AI checks passed:                                                      │ │   │
│  │  │  ✓ No speculation (removed "appears to be laundering")                                │ │   │
│  │  │  ✓ All facts verified against database                                                │ │   │
│  │  │  ✓ Formal regulatory tone maintained                                                  │ │   │
│  │  │                                                                                        │ │   │
│  │  └────────────────────────────────────────────────────────────────────────────────────────┘ │   │
│  │                                                                                              │   │
│  └─────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Technology Stack Summary

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    TECHNOLOGY STACK                                                 │
├─────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                     │
│   FRONTEND                          BACKEND                           DATA & AI                    │
│   ════════                          ═══════                           ═════════                    │
│                                                                                                     │
│   ┌─────────────────┐              ┌─────────────────┐              ┌─────────────────┐            │
│   │                 │              │                 │              │                 │            │
│   │  React 18       │              │  FastAPI        │              │  PostgreSQL     │            │
│   │  TypeScript     │◄────────────►│  Python 3.11    │◄────────────►│  (Relational)   │            │
│   │  Vite           │   REST API   │  Pydantic       │   SQLAlchemy │                 │            │
│   │                 │   WebSocket  │  Uvicorn        │              │                 │            │
│   └─────────────────┘              └─────────────────┘              └─────────────────┘            │
│           │                                │                                │                      │
│           │                                │                                │                      │
│   ┌─────────────────┐              ┌─────────────────┐              ┌─────────────────┐            │
│   │                 │              │                 │              │                 │            │
│   │  TailwindCSS    │              │  LangChain      │              │  ChromaDB       │            │
│   │  shadcn/ui      │              │  LangGraph      │◄────────────►│  (Vector Store) │            │
│   │  Radix UI       │              │  (Agents)       │   Embeddings │                 │            │
│   │                 │              │                 │              │                 │            │
│   └─────────────────┘              └─────────────────┘              └─────────────────┘            │
│           │                                │                                │                      │
│           │                                │                                │                      │
│   ┌─────────────────┐              ┌─────────────────┐              ┌─────────────────┐            │
│   │                 │              │                 │              │                 │            │
│   │  TanStack Query │              │  spaCy          │              │  Ollama         │            │
│   │  (State Mgmt)   │              │  (NER)          │◄────────────►│  Llama 3.1      │            │
│   │                 │              │                 │   LLM Calls  │  (Local LLM)    │            │
│   │                 │              │                 │              │                 │            │
│   └─────────────────┘              └─────────────────┘              └─────────────────┘            │
│           │                                │                                                       │
│           │                                │                                                       │
│   ┌─────────────────┐              ┌─────────────────┐                                             │
│   │                 │              │                 │                                             │
│   │  React Flow     │              │  NetworkX       │                                             │
│   │  (Graph Viz)    │              │  (Graph Algo)   │                                             │
│   │                 │              │                 │                                             │
│   │                 │              │                 │                                             │
│   └─────────────────┘              └─────────────────┘                                             │
│                                                                                                     │
│                                                                                                     │
│   DEVELOPMENT TOOLS                 DEPLOYMENT                                                     │
│   ═════════════════                 ══════════                                                     │
│                                                                                                     │
│   ┌─────────────────┐              ┌─────────────────┐                                             │
│   │  ESLint         │              │  Docker         │                                             │
│   │  Prettier       │              │  Docker Compose │                                             │
│   │  TypeScript     │              │  Nginx          │                                             │
│   │  Git            │              │  (Optional)     │                                             │
│   └─────────────────┘              └─────────────────┘                                             │
│                                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Project Directory Structure

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    PROJECT STRUCTURE                                                │
├─────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                     │
│  sar-narrative-generator/                                                                           │
│  │                                                                                                  │
│  ├── frontend/                          # React Application                                         │
│  │   ├── src/                                                                                       │
│  │   │   ├── components/                                                                            │
│  │   │   │   ├── layout/                # Sidebar, Header, Layout                                   │
│  │   │   │   ├── alerts/                # AlertList, AlertCard, AlertFilters                        │
│  │   │   │   ├── sar/                   # NarrativePanel, AuditTrailPanel, SAREditor               │
│  │   │   │   ├── transactions/          # TransactionTable, TransactionGraph                        │
│  │   │   │   ├── audit/                 # AuditLog, QueryViewer, ConfidenceBar                     │
│  │   │   │   └── common/                # Button, Card, Modal, DataTable                           │
│  │   │   ├── pages/                     # Dashboard, Alerts, SARWorkspace, History                 │
│  │   │   ├── hooks/                     # useAlerts, useSARGeneration, useAuditTrail               │
│  │   │   ├── services/                  # api.ts, alertService, sarService                         │
│  │   │   ├── types/                     # TypeScript type definitions                              │
│  │   │   └── utils/                     # formatters, constants                                    │
│  │   ├── package.json                                                                               │
│  │   ├── vite.config.ts                                                                             │
│  │   └── tailwind.config.js                                                                         │
│  │                                                                                                  │
│  ├── backend/                           # FastAPI Application                                       │
│  │   ├── app/                                                                                       │
│  │   │   ├── routers/                   # alerts.py, sar.py, audit.py, transactions.py             │
│  │   │   ├── services/                  # sar_generator.py, audit_trail.py, fact_checker.py        │
│  │   │   ├── agents/                    # data_analyst.py, compliance.py, writer.py, etc.          │
│  │   │   ├── models/                    # Pydantic models                                          │
│  │   │   ├── db/                        # database.py, models.py, crud.py                          │
│  │   │   └── knowledge_base/            # vector_store.py, embeddings.py                           │
│  │   ├── requirements.txt                                                                           │
│  │   └── Dockerfile                                                                                 │
│  │                                                                                                  │
│  ├── data/                              # Sample Data                                               │
│  │   ├── scenarios/                     # 50 SAR test scenarios                                     │
│  │   ├── regulatory/                    # FinCEN typologies, FATF guidelines                        │
│  │   └── historical_sars/               # 100+ approved SAR examples                                │
│  │                                                                                                  │
│  ├── docker-compose.yml                 # Full stack deployment                                     │
│  ├── README.md                          # Project documentation                                     │
│  └── ARCHITECTURE_DIAGRAM.md            # This file                                                 │
│                                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## API Endpoints Summary

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                      API ENDPOINTS                                                  │
├─────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                     │
│  ALERTS                                                                                             │
│  ══════                                                                                             │
│  GET    /api/alerts                    List all alerts (with filters)                              │
│  GET    /api/alerts/{alert_id}         Get alert details                                           │
│  PATCH  /api/alerts/{alert_id}         Update alert status                                         │
│                                                                                                     │
│  SAR GENERATION                                                                                     │
│  ══════════════                                                                                     │
│  POST   /api/sar/generate              Start SAR generation (returns task_id)                      │
│  GET    /api/sar/{sar_id}              Get SAR with narrative                                      │
│  PATCH  /api/sar/{sar_id}              Update narrative (analyst edits)                            │
│  POST   /api/sar/{sar_id}/submit       Approve and submit to regulator                             │
│  GET    /api/sar/{sar_id}/export       Export as PDF with audit package                            │
│                                                                                                     │
│  AUDIT TRAIL                                                                                        │
│  ═══════════                                                                                        │
│  GET    /api/sar/{sar_id}/evidence/{sentence_idx}    Get evidence for sentence                     │
│  GET    /api/sar/{sar_id}/audit                       Get full audit trail                         │
│                                                                                                     │
│  TRANSACTIONS                                                                                       │
│  ════════════                                                                                       │
│  GET    /api/transactions              List transactions for alert                                 │
│  GET    /api/transactions/graph/{alert_id}    Get graph data for React Flow                        │
│                                                                                                     │
│  WEBSOCKET                                                                                          │
│  ═════════                                                                                          │
│  WS     /ws/sar/{task_id}              Real-time generation progress                               │
│                                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

**Document Version:** 1.0
**Last Updated:** February 2026
**Project:** SAR Narrative Generator with Audit Trail
**Hackathon:** Barclays Hack-O-Hire 2026
