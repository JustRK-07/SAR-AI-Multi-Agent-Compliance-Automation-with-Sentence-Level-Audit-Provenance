# SAR Narrative Generator with Audit Trail

AI-powered Suspicious Activity Report (SAR) generation system with complete audit trail for AML compliance.

## Features

- **Multi-Agent Pipeline**: 5 specialized AI agents for SAR generation
- **Interactive Audit Trail**: Click any sentence to see supporting evidence
- **Transaction Flow Visualization**: React Flow graph showing money movement
- **Constitutional AI**: Ensures factual, non-speculative narratives
- **Real-time Progress**: WebSocket updates during generation

## Tech Stack

### Backend
- FastAPI (Python 3.11)
- PostgreSQL / SQLite
- LangChain + LangGraph
- ChromaDB (Vector Store)
- Ollama (Llama 3.1)

### Frontend
- React 18 + TypeScript
- TailwindCSS
- TanStack Query
- React Flow

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- Ollama (optional, for LLM)

### Development Setup

1. **Clone and setup backend:**
```bash
cd sar-narrative-generator/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Seed database with sample data
python seed_data.py

# Start backend server
uvicorn app.main:app --reload --port 8000
```

2. **Setup frontend:**
```bash
cd sar-narrative-generator/frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

3. **Access the application:**
- Frontend: http://localhost:5173
- API Docs: http://localhost:8000/docs

### Docker Setup

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Project Structure

```
sar-narrative-generator/
├── backend/
│   ├── app/
│   │   ├── routers/       # API endpoints
│   │   ├── services/      # Business logic
│   │   ├── agents/        # Multi-agent pipeline
│   │   ├── models/        # Pydantic models
│   │   ├── db/            # Database models & CRUD
│   │   └── knowledge_base/ # Vector store & embeddings
│   ├── requirements.txt
│   └── seed_data.py
├── frontend/
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── pages/         # Page components
│   │   ├── services/      # API services
│   │   ├── hooks/         # Custom hooks
│   │   └── types/         # TypeScript types
│   └── package.json
└── docker-compose.yml
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/alerts | List alerts |
| GET | /api/alerts/{id} | Get alert details |
| POST | /api/sar/generate | Generate SAR |
| GET | /api/sar/{id} | Get SAR details |
| GET | /api/audit/sar/{id}/evidence/{idx} | Get sentence evidence |
| GET | /api/transactions/graph/{alert_id} | Get transaction graph |
| WS | /ws/sar/{task_id} | Real-time progress |

## Multi-Agent Pipeline

1. **Data Analyst**: Extracts facts via SQL queries
2. **Compliance Specialist**: Classifies AML typology
3. **Narrative Writer**: Generates SAR using RAG + LLM
4. **Fact Checker**: Verifies every claim against data
5. **Editor**: Polishes grammar and style

## Configuration

Create `.env` file in backend directory:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/sar_db
REDIS_URL=redis://localhost:6379
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
DEBUG=true
```

## License

MIT License - Hackathon Project

## Team

Built for Barclays Hack-O-Hire 2026
