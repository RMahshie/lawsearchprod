# LawSearch AI - Docker Operations Guide

This guide provides step-by-step instructions for managing your LawSearch AI application using Docker and Docker Compose.

## Prerequisites

- Docker Desktop installed and running
- Docker Compose installed (usually comes with Docker Desktop)
- `.env` file with your `OPENAI_API_KEY` in the project root

## Quick Reference Commands

```bash
# Start the application
docker-compose up

# Start in background (detached mode)
docker-compose up -d

# Stop the application
docker-compose down

# Rebuild and start
docker-compose up --build

# View logs
docker-compose logs -f

# Check container status
docker-compose ps

# Initial data ingestion (required)
docker-compose up -d
docker cp src/ingest.py $(docker-compose ps -q backend):/app/src/ingest.py
docker cp src/config.py $(docker-compose ps -q backend):/app/src/config.py
docker-compose exec backend python3 -m src.ingest
```

## Detailed Operations Guide

### 🚀 Starting the Application

#### Option 1: Start with Real-time Logs (Recommended for Development)
```bash
docker-compose up
```
**What this does:**
- Builds Docker images if they don't exist
- Creates and starts both backend and frontend containers
- Shows real-time logs from both services in your terminal
- Press `Ctrl+C` to stop

#### Option 2: Start in Background (Detached Mode)
```bash
docker-compose up -d
```
**What this does:**
- Same as above but runs containers in the background
- Returns control to your terminal immediately
- Use `docker-compose logs -f` to view logs later

#### Option 3: Force Rebuild and Start
```bash
docker-compose up --build
```
**What this does:**
- Forces rebuilding of Docker images even if they exist
- Useful when you've made code changes
- Starts the containers with the newly built images

### 📊 Data Ingestion (Vector Database Setup)

#### Initial Data Ingestion (Required Before First Use)

The application requires vector databases to be created from the bill documents before it can answer queries. This process must be run **inside the container** to ensure ChromaDB compatibility.

```bash
# 1. Start the containers (they will be unhealthy until data is ingested)
docker-compose up -d

# 2. Copy the ingestion script into the running backend container
docker cp src/ingest.py $(docker-compose ps -q backend):/app/src/ingest.py
docker cp src/config.py $(docker-compose ps -q backend):/app/src/config.py

# 3. Run the ingestion script inside the container
docker-compose exec backend python3 -m src.ingest

# 4. Verify the backend is now healthy
curl http://localhost:8000/api/health
```

**What this does:**
- Creates 14 vector databases (one per bill division) from the HTML bill documents
- Embeds all text chunks using the configured embedding model
- Stores everything in the `/app/db/chroma/` directory (mounted volume)
- Takes ~30-60 seconds depending on your machine

**Important Notes:**
- **Must run inside container**: Running ingestion from host machine creates ChromaDB tenant mismatches
- **Required for first startup**: Backend will show "unhealthy" status until databases are created
- **Only needs to be done once**: Databases persist in the mounted volume
- **Re-run if**: You change embedding models, clear databases, or update bill documents

#### Re-ingestion After Changes

If you need to re-ingest data (e.g., after changing embedding models or updating documents):

```bash
# Clear existing databases
rm -rf db/chroma/*

# Then follow steps 1-4 above
docker-compose up -d
docker cp src/ingest.py $(docker-compose ps -q backend):/app/src/ingest.py
docker cp src/config.py $(docker-compose ps -q backend):/app/src/config.py
docker-compose exec backend python3 -m src.ingest
```

### 🛑 Stopping the Application

#### Stop Running Containers
```bash
docker-compose down
```
**What this does:**
- Gracefully stops all running containers
- Removes containers (but keeps images and volumes)
- Removes the custom network created for the app

#### Stop and Remove Everything (Including Images)
```bash
docker-compose down --rmi all --volumes
```
**What this does:**
- Stops containers
- Removes containers, networks, images, and volumes
- Use with caution - you'll need to rebuild everything

### 🔄 Restarting the Application

#### Restart All Services
```bash
docker-compose restart
```
**What this does:**
- Restarts all containers without rebuilding
- Faster than stopping and starting
- Maintains existing container configuration

#### Restart Specific Service
```bash
docker-compose restart backend
# or
docker-compose restart frontend
```
**What this does:**
- Restarts only the specified service
- Other services continue running normally

### 🔍 Monitoring and Troubleshooting

#### Check Container Status
```bash
docker-compose ps
```
**What this shows:**
- List of all containers defined in docker-compose.yml
- Current status (running, stopped, exited)
- Port mappings
- Health check status

#### View Real-time Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend

# Last 50 lines
docker-compose logs --tail=50 backend
```
**What this does:**
- Shows application logs in real-time (`-f` flag)
- Useful for debugging issues
- `Ctrl+C` to stop following logs

#### Check Resource Usage
```bash
docker stats
```
**What this shows:**
- CPU and memory usage for all running containers
- Network I/O statistics
- Live updating display

### 🔧 Building and Development

#### Build Specific Service
```bash
# Build backend only
docker-compose build backend

# Build frontend only
docker-compose build frontend

# Build with no cache (fresh build)
docker-compose build --no-cache backend
```
**What this does:**
- Builds Docker image for specified service
- `--no-cache` ensures completely fresh build
- Useful when dependencies change

#### Development Mode with File Watching
```bash
# If you have a development override file
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```
**What this does:**
- Uses additional configuration for development
- May include volume mounts for live code reloading
- Check if `docker-compose.dev.yml` exists in your project

### 🧪 Testing and Health Checks

#### Test Backend Health
```bash
curl http://localhost:8000/api/health
```
**Expected response:**
```json
{"status":"healthy","timestamp":"...","version":"1.0.0","database_status":"connected"}
```

#### Test Frontend Health
```bash
curl http://localhost:3000/health
```
**Expected response:**
```
healthy
```

#### Test API Documentation
```bash
# Open in browser
open http://localhost:8000/docs
# or visit manually
```

#### Test a Sample Query
```bash
curl -X POST "http://localhost:8000/api/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "How much funding did FEMA receive?", "max_results": 5, "include_sources": true}'
```

### 🐛 Common Troubleshooting

#### Problem: Port Already in Use
```bash
# Find what's using port 8000
lsof -i :8000

# Find what's using port 3000
lsof -i :3000

# Kill process using port (replace PID)
kill -9 <PID>
```

#### Problem: Out of Disk Space
```bash
# Clean up unused Docker resources
docker system prune -a

# Remove unused volumes
docker volume prune

# Remove unused networks
docker network prune
```

#### Problem: Container Won't Start
```bash
# Check detailed logs
docker-compose logs backend

# Check if .env file exists and has OPENAI_API_KEY
ls -la .env
cat .env

# Rebuild without cache
docker-compose build --no-cache
```

#### Problem: Database Connection Issues
```bash
# Check if vector database directories exist
ls -la db/chroma/

# Check container can access volumes
docker-compose exec backend ls -la /app/db/chroma/
```

### 🔄 Update Workflow

When you make changes to your code:

#### For Backend Changes:
```bash
# Stop the application
docker-compose down

# Rebuild and start
docker-compose up --build backend
```

#### For Frontend Changes:
```bash
# Stop the application
docker-compose down

# Rebuild and start
docker-compose up --build frontend
```

#### For Configuration Changes (docker-compose.yml, Dockerfile):
```bash
# Stop everything
docker-compose down

# Rebuild everything
docker-compose up --build
```

### 📊 Service Information

#### Backend Service (FastAPI)
- **Container Name:** `lawsearch-backend`
- **Port:** `8000` (mapped from container port 8000)
- **Health Check:** `http://localhost:8000/api/health`
- **API Docs:** `http://localhost:8000/docs`
- **Environment:** Uses `.env` file for configuration

#### Frontend Service (React + Nginx)
- **Container Name:** `lawsearch-frontend`
- **Port:** `3000` (mapped from container port 80)
- **Health Check:** `http://localhost:3000/health`
- **Application:** `http://localhost:3000`
- **Built with:** Vite + React + TypeScript

### 🔐 Environment Variables

Make sure your `.env` file contains:
```bash
OPENAI_API_KEY=your-openai-api-key-here
```

Additional optional variables:
```bash
ENVIRONMENT=development
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
```

### 🚨 Emergency Procedures

#### Complete Reset (Nuclear Option)
```bash
# Stop everything
docker-compose down

# Remove all containers, networks, images, and volumes
docker-compose down --rmi all --volumes

# Clean up Docker system
docker system prune -a

# Rebuild from scratch
docker-compose up --build
```

#### Backup Vector Database
```bash
# Create backup of ChromaDB
tar -czf chroma_backup_$(date +%Y%m%d_%H%M%S).tar.gz db/chroma/
```

#### Restore Vector Database
```bash
# Extract backup (replace with your backup file)
tar -xzf chroma_backup_YYYYMMDD_HHMMSS.tar.gz
```

### ⚡ Performance Optimization

#### Speed Up Build Times
```bash
# Enable BuildKit for faster builds (add to your shell profile)
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Use BuildKit with docker-compose
DOCKER_BUILDKIT=1 docker-compose build
```

#### Use Docker Layer Caching
```bash
# Build with cache from registry (if using one)
docker-compose build --build-arg BUILDKIT_INLINE_CACHE=1

# Parallel builds for multiple services
docker-compose build --parallel
```

#### Monitor Build Performance
```bash
# Build with timing information
time docker-compose build

# Build specific service with progress output
docker-compose build --progress=plain backend
```

### 📝 Best Practices

1. **Always check logs first** when something isn't working
2. **Use health checks** to verify services are running properly
3. **Keep your .env file secure** and never commit it to version control
4. **Regularly clean up** unused Docker resources to save disk space
5. **Use specific service names** when troubleshooting (backend/frontend)
6. **Rebuild containers** after significant code changes
7. **Use .dockerignore** to exclude unnecessary files from build context
8. **Leverage Docker layer caching** by organizing Dockerfile commands properly

### 🆘 Getting Help

If you encounter issues:
1. Check the logs: `docker-compose logs -f`
2. Verify health endpoints are responding
3. Ensure Docker Desktop is running
4. Check if ports 3000 and 8000 are available
5. Verify your `.env` file contains the OpenAI API key

---

**Remember:** This application requires an active internet connection and a valid OpenAI API key to function properly.
