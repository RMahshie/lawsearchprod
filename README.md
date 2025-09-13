# LawSearch AI - Federal Appropriations Query System

A production-ready AI-powered system for querying federal appropriations bills using natural language. Built with **FastAPI**, **React**, and **OpenAI**, containerized with **Docker** for easy deployment.

## 🌟 Features

- **Natural Language Queries**: Ask questions about federal appropriations in plain English
- **Intelligent Routing**: Automatically searches across relevant appropriations divisions
- **Source Attribution**: Every answer includes citations from original legislative documents
- **Real-time Processing**: Fast RAG (Retrieval-Augmented Generation) pipeline
- **Production Ready**: Dockerized with health checks, CORS, and security headers
- **Modern Stack**: FastAPI backend + React TypeScript frontend

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│   React Frontend │    │   FastAPI Backend│    │   OpenAI + ChromaDB │
│   (Port 3000)   │◄──►│   (Port 8000)    │◄──►│   RAG Pipeline      │
└─────────────────┘    └──────────────────┘    └─────────────────────┘
```

### Tech Stack
- **Backend**: FastAPI, Pydantic, LangChain, ChromaDB
- **Frontend**: React, TypeScript, Vite, Axios, React Query
- **AI**: OpenAI GPT-4o, text-embedding-3-small
- **Infrastructure**: Docker, Docker Compose, Nginx

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- OpenAI API key ([Get one here](https://platform.openai.com/account/api-keys))

### 1. Clone and Setup
```bash
git clone <repository-url>
cd lawsearchprod
cp .env.example .env
```

### 2. Configure Environment
Edit `.env` file and add your OpenAI API key:
```bash
OPENAI_API_KEY=sk-your-openai-api-key-here
```

### 3. Run with Docker
```bash
# Build and start all services
docker-compose up --build

# Or run in background
docker-compose up -d --build
```

### 4. Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 🛠️ Development Setup

### Option 1: Docker Development
```bash
# Use development docker-compose with hot reload
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

### Option 2: Local Development
```bash
# Install dependencies
npm install                    # Root level scripts
npm run install:frontend      # React dependencies
pip install -r requirements.txt  # Python dependencies

# Run services separately
npm run dev:backend           # FastAPI server (localhost:8000)
npm run dev:frontend          # React dev server (localhost:5173)

# Or run both concurrently
npm run dev
```

## 📋 Available Scripts

```bash
# Development
npm run dev                   # Run both frontend and backend
npm run dev:frontend          # React development server
npm run dev:backend           # FastAPI development server

# Building
npm run build                 # Build frontend for production
npm run build:frontend        # Build React app
npm run build:backend         # No-op (Python doesn't need building)

# Docker
npm run docker:build          # Build Docker images
npm run docker:up             # Start all services
npm run docker:down           # Stop all services
npm run docker:dev            # Development mode with hot reload
npm run docker:logs           # View logs

# Utilities
npm run clean                 # Clean build artifacts and Docker
npm run test                  # Run tests
npm run lint                  # Lint frontend code
```

## 🔧 Configuration

### Environment Variables

#### Backend (.env)
```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
ENVIRONMENT=development

# OpenAI (Required)
OPENAI_API_KEY=sk-your-key-here
LLM_INGEST=gpt-4o
LLM_QA=gpt-4o
EMBEDDING_MODEL=text-embedding-3-small

# RAG Settings
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
TOP_K_RETRIEVAL=8
SIMILARITY_THRESHOLD=0.7

# CORS
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]
```

#### Frontend (frontend/.env)
```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_DEBUG=false
```

## 📖 API Documentation

### Endpoints

#### `POST /api/query`
Submit a query about federal appropriations.

**Request:**
```json
{
  "question": "How much funding did FEMA receive in 2024?",
  "max_results": 8,
  "include_sources": true,
  "divisions_filter": null
}
```

**Response:**
```json
{
  "answer": "Based on the 2024 Consolidated Appropriations Act...",
  "processing_time": 3.45,
  "selected_divisions": ["DEPARTMENT OF HOMELAND SECURITY"],
  "sources": [...],
  "timestamp": "2024-03-15T14:30:00Z",
  "query_id": "query_20240315_143000_abc123"
}
```

#### `GET /api/health`
Health check endpoint.

#### `GET /api/status`
Detailed status information.

### Interactive Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🗂️ Project Structure

```
lawsearchprod/
├── app/                      # FastAPI backend
│   ├── api/endpoints/        # API route handlers
│   ├── core/                 # Configuration and utilities
│   ├── models/               # Pydantic models
│   ├── services/             # Business logic (RAG service)
│   └── main.py              # FastAPI application
├── frontend/                 # React frontend
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── services/         # API client
│   │   ├── types/           # TypeScript interfaces
│   │   └── hooks/           # React Query hooks
│   └── package.json
├── data/bills/              # Appropriations bill documents
├── db/chroma/               # ChromaDB vector storage
├── docker-compose.yml       # Production Docker setup
├── docker-compose.dev.yml   # Development Docker setup
├── Dockerfile.backend       # Backend Docker image
├── Dockerfile.frontend      # Frontend Docker image
└── requirements.txt         # Python dependencies
```

## 🔍 Data Sources

The system queries the following 2024 appropriations bills:
- **Division A**: Military Construction, Veterans Affairs
- **Division B**: Agriculture, Rural Development, FDA
- **Division C**: Commerce, Justice, Science
- **Division D**: Energy and Water Development
- **Division E**: Interior, Environment
- **Division F**: Transportation, Housing, Urban Development
- **Division G**: Other Matters
- **Further Consolidated Appropriations Act** (8 additional divisions)

## 🧪 Testing the System

### Sample Queries
Try these example questions:
- "How much funding was allocated to NASA in 2024?"
- "What cybersecurity initiatives received funding?"
- "How much did FEMA receive for disaster relief?"
- "What transportation projects were funded?"

### Health Checks
```bash
# Backend health
curl http://localhost:8000/api/health

# Frontend health (Docker)
curl http://localhost:3000/health
```

## 🚀 Deployment

### Production Deployment
1. Set production environment variables
2. Build and deploy with Docker Compose
3. Configure reverse proxy (nginx/traefik)
4. Set up SSL certificates
5. Configure monitoring and logging

### Scaling Considerations
- Use Redis for caching query results
- Implement rate limiting
- Add monitoring with Prometheus/Grafana
- Use container orchestration (Kubernetes)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

MIT License - see LICENSE file for details.

## 🆘 Troubleshooting

### Common Issues

**Frontend can't connect to backend:**
- Check CORS settings in backend configuration
- Verify API_BASE_URL in frontend environment

**OpenAI API errors:**
- Ensure OPENAI_API_KEY is set correctly
- Check API key permissions and billing

**Docker build issues:**
- Clear Docker cache: `docker system prune -a`
- Check Docker daemon is running

**Performance issues:**
- Reduce CHUNK_SIZE for faster processing
- Adjust TOP_K_RETRIEVAL for relevance vs speed

### Logs
```bash
# View all logs
docker-compose logs -f

# View specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

---

**Built with ❤️ for legal and policy research**