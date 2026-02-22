# Frontend Architecture

## React Application Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND (React 18)                            │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                           App.tsx (Router)                            │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │  │
│  │  │  Dashboard  │  │   Alerts    │  │SARWorkspace │  │   History   │  │  │
│  │  │    Page     │  │    Page     │  │    Page     │  │    Page     │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                          Layout Components                          │    │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │    │
│  │  │     Layout       │  │     Sidebar      │  │     Header       │  │    │
│  │  │   (Wrapper)      │  │   (Navigation)   │  │  (User/Actions)  │  │    │
│  │  └──────────────────┘  └──────────────────┘  └──────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                        Feature Components                           │    │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────────┐    │    │
│  │  │ NarrativePanel │  │AuditTrailPanel │  │ TransactionGraph   │    │    │
│  │  │  (SAR Display) │  │  (Evidence)    │  │   (React Flow)     │    │    │
│  │  └────────────────┘  └────────────────┘  └────────────────────┘    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         Common Components                           │    │
│  │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────────┐   │    │
│  │  │  Card  │  │ Button │  │ Modal  │  │ Badge  │  │  Spinner   │   │    │
│  │  └────────┘  └────────┘  └────────┘  └────────┘  └────────────┘   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Component Hierarchy

```
App.tsx
├── QueryClientProvider (TanStack Query)
│   └── BrowserRouter
│       └── Routes
│           ├── /dashboard → Dashboard
│           ├── /alerts → Alerts
│           ├── /sar/:alertId → SARWorkspace
│           └── /history → History

SARWorkspace (Main Feature Page)
├── Layout
│   ├── Sidebar
│   │   └── Navigation Links
│   └── Header
│       └── User Menu
└── Main Content
    ├── Alert Summary Card
    ├── Split View Container
    │   ├── Left Panel (60%)
    │   │   └── NarrativePanel
    │   │       ├── Progress Indicator (during generation)
    │   │       ├── Narrative Text
    │   │       │   └── ClickableSentence (per sentence)
    │   │       └── Action Buttons (Export, Approve)
    │   └── Right Panel (40%)
    │       └── AuditTrailPanel
    │           ├── Selected Sentence Display
    │           └── Evidence Cards
    │               ├── SQL Queries Used
    │               ├── Data Retrieved
    │               └── Sources Referenced
    └── Transaction Graph Section
        └── TransactionGraph (React Flow)
            ├── Account Nodes
            ├── Transaction Edges
            └── Controls (zoom, pan, fit)
```

## State Management Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           STATE MANAGEMENT                                   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    TanStack Query (Server State)                     │   │
│  │                                                                      │   │
│  │   useQuery('alerts')      →  GET /api/alerts                        │   │
│  │   useQuery('alert', id)   →  GET /api/alerts/{id}                   │   │
│  │   useQuery('sar', id)     →  GET /api/sar/{id}                      │   │
│  │   useQuery('evidence')    →  GET /api/audit/sar/{id}/evidence/{idx} │   │
│  │   useQuery('graph')       →  GET /api/transactions/graph/{alertId}  │   │
│  │                                                                      │   │
│  │   useMutation('generate') →  POST /api/sar/generate                 │   │
│  │   useMutation('approve')  →  POST /api/sar/{id}/approve             │   │
│  │   useMutation('export')   →  POST /api/sar/{id}/export              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    React State (UI State)                            │   │
│  │                                                                      │   │
│  │   useState: selectedSentenceIndex                                   │   │
│  │   useState: isGenerating                                            │   │
│  │   useState: generationProgress                                      │   │
│  │   useState: activeTab                                               │   │
│  │   useState: sidebarCollapsed                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    WebSocket State (Real-time)                       │   │
│  │                                                                      │   │
│  │   useWebSocket('/ws/sar/{taskId}')                                  │   │
│  │   ├── onMessage: Update generation progress                         │   │
│  │   ├── onComplete: Invalidate queries, show result                   │   │
│  │   └── onError: Show error notification                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Data Flow Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              DATA FLOW                                        │
│                                                                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐   │
│  │    User     │    │  Component  │    │   Service   │    │   Backend   │   │
│  │   Action    │───▶│   Handler   │───▶│    Layer    │───▶│     API     │   │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘   │
│                                                                    │         │
│                                                                    ▼         │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐   │
│  │     UI      │    │    React    │    │  TanStack   │    │    HTTP     │   │
│  │   Update    │◀───│    State    │◀───│   Query     │◀───│  Response   │   │
│  └─────────────┘    └─────────────┘    │   Cache     │    └─────────────┘   │
│                                        └─────────────┘                       │
└──────────────────────────────────────────────────────────────────────────────┘

Example: Generate SAR Flow
═══════════════════════════

1. User clicks "Generate SAR"
   │
   ▼
2. SARWorkspace.handleGenerate()
   │
   ▼
3. sarService.generateSAR(alertId)
   │
   ▼
4. POST /api/sar/generate
   │
   ▼
5. Backend returns { taskId: "abc123" }
   │
   ▼
6. WebSocket connects to /ws/sar/abc123
   │
   ▼
7. Progress updates arrive via WebSocket
   │  ├── { agent: "data_analyst", status: "running" }
   │  ├── { agent: "data_analyst", status: "complete" }
   │  ├── { agent: "compliance", status: "running" }
   │  └── ... (more updates)
   │
   ▼
8. Final message: { status: "complete", sarId: "xyz789" }
   │
   ▼
9. Invalidate queries, fetch SAR data
   │
   ▼
10. Display narrative with clickable sentences
```

## SAR Workspace Page Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ┌──────┐                     SAR Narrative Generator              [User ▼] │
│ │ LOGO │  Dashboard  Alerts  SAR Workspace  History                        │
├─┴──────┴───────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │ ALERT: ALT-2024-001                              Status: [In Review]  │ │
│  │ Subject: John Smith | Risk Score: 85 | Created: 2024-01-15           │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌──────────────────────────────────┬──────────────────────────────────┐   │
│  │      NARRATIVE PANEL (60%)       │     AUDIT TRAIL PANEL (40%)      │   │
│  │                                  │                                   │   │
│  │  ┌────────────────────────────┐  │  ┌─────────────────────────────┐ │   │
│  │  │ SAR NARRATIVE              │  │  │ EVIDENCE FOR SENTENCE #3    │ │   │
│  │  │                            │  │  │                             │ │   │
│  │  │ [1] Subject John Smith     │  │  │ SQL Query:                  │ │   │
│  │  │ conducted 47 transactions  │  │  │ ┌─────────────────────────┐ │ │   │
│  │  │ totaling $125,000...       │  │  │ │ SELECT COUNT(*)...      │ │ │   │
│  │  │                            │  │  │ └─────────────────────────┘ │ │   │
│  │  │ [2] The activity pattern   │  │  │                             │ │   │
│  │  │ suggests structuring to    │  │  │ Data Retrieved:             │ │   │
│  │  │ avoid CTR thresholds...    │  │  │ ┌─────────────────────────┐ │ │   │
│  │  │                            │  │  │ │ { count: 47,            │ │ │   │
│  │  │ [3] ← SELECTED (highlight) │  │  │ │   total: 125000 }       │ │ │   │
│  │  │ Multiple deposits were     │  │  │ └─────────────────────────┘ │ │   │
│  │  │ made just below $10,000... │  │  │                             │ │   │
│  │  │                            │  │  │ Sources:                    │ │   │
│  │  │ [4] Wire transfers to      │  │  │ • Transaction Table         │ │   │
│  │  │ high-risk jurisdictions... │  │  │ • Account History           │ │   │
│  │  │                            │  │  │ • FinCEN Guidelines §3.2    │ │   │
│  │  └────────────────────────────┘  │  └─────────────────────────────┘ │   │
│  │                                  │                                   │   │
│  │  [Export PDF] [Approve] [Edit]   │  Confidence: 95% ████████████░   │   │
│  └──────────────────────────────────┴──────────────────────────────────┘   │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                      TRANSACTION FLOW GRAPH                           │ │
│  │                                                                       │ │
│  │     ┌─────────┐         $15,000          ┌─────────┐                 │ │
│  │     │ Account │ ─────────────────────▶   │ Shell   │                 │ │
│  │     │  A-001  │                          │ Corp X  │                 │ │
│  │     │ (John)  │                          │ ⚠️      │                 │ │
│  │     └────┬────┘                          └────┬────┘                 │ │
│  │          │                                    │                       │ │
│  │          │ $9,500                             │ $12,000              │ │
│  │          ▼                                    ▼                       │ │
│  │     ┌─────────┐                          ┌─────────┐                 │ │
│  │     │ Account │                          │ Offshore│                 │ │
│  │     │  B-002  │                          │ Bank    │                 │ │
│  │     │         │                          │ ⚠️⚠️    │                 │ │
│  │     └─────────┘                          └─────────┘                 │ │
│  │                                                                       │ │
│  │  Legend: ⬜ Normal  ⚠️ High Risk  🔴 Subject                         │ │
│  │  [Zoom +] [Zoom -] [Fit View] [Download PNG]                         │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

## File Structure

```
frontend/
├── public/
│   └── favicon.ico
├── src/
│   ├── main.tsx                 # App entry point
│   ├── App.tsx                  # Router configuration
│   ├── index.css                # Global styles + Tailwind
│   │
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Layout.tsx       # Main layout wrapper
│   │   │   ├── Sidebar.tsx      # Navigation sidebar
│   │   │   └── Header.tsx       # Top header bar
│   │   │
│   │   ├── common/
│   │   │   ├── Card.tsx         # Reusable card component
│   │   │   ├── Button.tsx       # Button variants
│   │   │   ├── Badge.tsx        # Status badges
│   │   │   ├── Modal.tsx        # Modal dialog
│   │   │   ├── Spinner.tsx      # Loading spinner
│   │   │   └── ProgressBar.tsx  # Progress indicator
│   │   │
│   │   ├── sar/
│   │   │   ├── NarrativePanel.tsx    # SAR narrative display
│   │   │   ├── AuditTrailPanel.tsx   # Evidence viewer
│   │   │   ├── ClickableSentence.tsx # Interactive sentence
│   │   │   ├── EvidenceCard.tsx      # Evidence display
│   │   │   └── GenerationProgress.tsx # Progress during gen
│   │   │
│   │   ├── transactions/
│   │   │   ├── TransactionGraph.tsx  # React Flow graph
│   │   │   ├── AccountNode.tsx       # Custom node component
│   │   │   └── TransactionEdge.tsx   # Custom edge component
│   │   │
│   │   └── alerts/
│   │       ├── AlertCard.tsx         # Alert summary card
│   │       ├── AlertList.tsx         # Alert list view
│   │       └── AlertFilters.tsx      # Filter controls
│   │
│   ├── pages/
│   │   ├── Dashboard.tsx        # Overview dashboard
│   │   ├── Alerts.tsx           # Alerts listing page
│   │   ├── SARWorkspace.tsx     # Main SAR generation page
│   │   └── History.tsx          # Past SAR reports
│   │
│   ├── services/
│   │   ├── api.ts               # Axios instance + config
│   │   ├── alertService.ts      # Alert API calls
│   │   ├── sarService.ts        # SAR API calls
│   │   ├── auditService.ts      # Audit trail API calls
│   │   └── transactionService.ts # Transaction API calls
│   │
│   ├── hooks/
│   │   ├── useAlerts.ts         # Alert data hooks
│   │   ├── useSAR.ts            # SAR data hooks
│   │   ├── useWebSocket.ts      # WebSocket connection hook
│   │   └── useAuditTrail.ts     # Audit trail hooks
│   │
│   ├── types/
│   │   └── index.ts             # TypeScript interfaces
│   │
│   └── utils/
│       ├── cn.ts                # classNames utility
│       └── formatters.ts        # Date, currency formatters
│
├── package.json
├── vite.config.ts
├── tailwind.config.js
├── tsconfig.json
└── Dockerfile
```

## React Flow Graph Configuration

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        TRANSACTION GRAPH SETUP                               │
│                                                                             │
│  Node Types:                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                      │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │   │
│  │  │   SUBJECT   │  │   NORMAL    │  │  HIGH RISK  │                 │   │
│  │  │   Account   │  │   Account   │  │   Account   │                 │   │
│  │  │             │  │             │  │             │                 │   │
│  │  │  🔴 Red     │  │  ⬜ Gray    │  │  🟡 Yellow  │                 │   │
│  │  │   Border    │  │   Border    │  │   Border    │                 │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                 │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Edge Types:                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                      │   │
│  │  ─────────▶  Normal Transaction (gray, thin)                        │   │
│  │  ═════════▶  Large Transaction (blue, thick)                        │   │
│  │  - - - - -▶  Suspicious Transaction (red, dashed)                   │   │
│  │                                                                      │   │
│  │  Edge Labels: Amount + Date                                         │   │
│  │  Animation: Dashed lines animate for suspicious flows               │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Controls:                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  [+] Zoom In    [-] Zoom Out    [⊡] Fit View    [📷] Export PNG     │   │
│  │  [🔍] Search Node    [📊] Toggle Stats    [🎨] Color Legend         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Key TypeScript Interfaces

```typescript
// types/index.ts

interface Alert {
  id: string;
  subject_name: string;
  subject_id: string;
  risk_score: number;
  status: 'pending' | 'in_review' | 'completed';
  created_at: string;
  alert_type: string;
}

interface SAR {
  id: string;
  alert_id: string;
  narrative: string;
  sentences: SentenceWithEvidence[];
  status: 'draft' | 'reviewed' | 'approved' | 'submitted';
  created_at: string;
  typology: TypologyClassification;
}

interface SentenceWithEvidence {
  index: number;
  text: string;
  evidence: Evidence;
  confidence: number;
}

interface Evidence {
  sql_queries: string[];
  data_retrieved: Record<string, any>[];
  sources: string[];
  facts_used: string[];
}

interface TransactionNode {
  id: string;
  type: 'subject' | 'normal' | 'high_risk';
  data: {
    label: string;
    account_id: string;
    account_holder: string;
    risk_indicators: string[];
  };
  position: { x: number; y: number };
}

interface TransactionEdge {
  id: string;
  source: string;
  target: string;
  type: 'normal' | 'large' | 'suspicious';
  data: {
    amount: number;
    date: string;
    transaction_type: string;
  };
}

interface GenerationProgress {
  task_id: string;
  current_agent: string;
  status: 'pending' | 'running' | 'complete' | 'error';
  progress_percent: number;
  message: string;
}
```

## WebSocket Integration

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         WEBSOCKET MESSAGE FLOW                               │
│                                                                             │
│   Frontend                           Backend                                │
│   ════════                           ═══════                                │
│                                                                             │
│   POST /api/sar/generate                                                    │
│   ─────────────────────────▶                                               │
│                              { taskId: "abc123" }                           │
│   ◀─────────────────────────                                               │
│                                                                             │
│   WS /ws/sar/abc123                                                         │
│   ═══════════════════════▶  Connection Established                         │
│                                                                             │
│                              { agent: "data_analyst",                       │
│   ◀═════════════════════════  status: "running",                           │
│                               message: "Extracting facts..." }             │
│                                                                             │
│                              { agent: "data_analyst",                       │
│   ◀═════════════════════════  status: "complete",                          │
│                               progress: 20 }                                │
│                                                                             │
│                              { agent: "compliance",                         │
│   ◀═════════════════════════  status: "running",                           │
│                               message: "Classifying typology..." }         │
│                                                                             │
│                              ... more updates ...                           │
│                                                                             │
│                              { status: "complete",                          │
│   ◀═════════════════════════  sarId: "sar-xyz789",                         │
│                               message: "SAR generated successfully" }      │
│                                                                             │
│   Connection Closed                                                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Styling Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          TAILWIND CSS SETUP                                  │
│                                                                             │
│  tailwind.config.js:                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  colors: {                                                           │   │
│  │    primary: {                                                        │   │
│  │      50: '#eff6ff',   // Light blue                                 │   │
│  │      500: '#3b82f6',  // Main blue                                  │   │
│  │      900: '#1e3a8a',  // Dark blue                                  │   │
│  │    },                                                                │   │
│  │    risk: {                                                           │   │
│  │      low: '#22c55e',     // Green                                   │   │
│  │      medium: '#f59e0b',  // Yellow                                  │   │
│  │      high: '#ef4444',    // Red                                     │   │
│  │    },                                                                │   │
│  │    status: {                                                         │   │
│  │      pending: '#6b7280',   // Gray                                  │   │
│  │      in_review: '#3b82f6', // Blue                                  │   │
│  │      completed: '#22c55e', // Green                                 │   │
│  │      approved: '#8b5cf6',  // Purple                                │   │
│  │    }                                                                 │   │
│  │  }                                                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Component Styling Pattern:                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  // Using cn() utility for conditional classes                       │   │
│  │  <div className={cn(                                                 │   │
│  │    "base-classes",                                                   │   │
│  │    isActive && "active-classes",                                     │   │
│  │    variant === 'primary' && "primary-classes"                        │   │
│  │  )} />                                                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Build & Deployment

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           BUILD PIPELINE                                     │
│                                                                             │
│   Development:                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │  npm run dev                                                         │  │
│   │  └─▶ Vite Dev Server (HMR enabled)                                  │  │
│   │      └─▶ http://localhost:5173                                      │  │
│   │          └─▶ Proxy /api → http://localhost:8000                     │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│   Production Build:                                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │  npm run build                                                       │  │
│   │  └─▶ TypeScript Compilation                                         │  │
│   │      └─▶ Vite Build (Rollup)                                        │  │
│   │          └─▶ dist/                                                  │  │
│   │              ├── index.html                                         │  │
│   │              ├── assets/                                            │  │
│   │              │   ├── index-[hash].js                                │  │
│   │              │   └── index-[hash].css                               │  │
│   │              └── favicon.ico                                        │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│   Docker Deployment:                                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │  Stage 1: Build                                                      │  │
│   │  ┌─────────────────────────────────────────────────────────────┐    │  │
│   │  │  FROM node:20-alpine as builder                              │    │  │
│   │  │  npm install → npm run build                                 │    │  │
│   │  └─────────────────────────────────────────────────────────────┘    │  │
│   │                                                                      │  │
│   │  Stage 2: Serve                                                      │  │
│   │  ┌─────────────────────────────────────────────────────────────┐    │  │
│   │  │  FROM nginx:alpine                                           │    │  │
│   │  │  COPY dist → /usr/share/nginx/html                          │    │  │
│   │  │  COPY nginx.conf → /etc/nginx/conf.d/default.conf           │    │  │
│   │  └─────────────────────────────────────────────────────────────┘    │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```
