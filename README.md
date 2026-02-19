# License Plate Recognition - Project Context

## Overview

A full-stack application for license plate recognition using OCR. Users upload license plate images via a web interface, and the system asynchronously processes them using EasyOCR to extract plate numbers.

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│     Frontend    │────▶│   FastAPI API   │────▶│   PostgreSQL    │
│   (React/Vite)  │     │    (port 8000)  │     │   (port 5432)   │
│    port 80/5173 │     └────────┬────────┘     └─────────────────┘
└─────────────────┘              │
                                 ▼
                          ┌─────────────┐     ┌─────────────────┐
                          │    Redis    │────▶│  Celery Worker  │
                          │ (port 6379) │     │   (EasyOCR)     │
                          └─────────────┘     └─────────────────┘
```

## Tech Stack

### Backend (`app/`)

- **Python 3.12** with **FastAPI** - Async REST API
- **PostgreSQL** - Database (SQLAlchemy 2.0 + asyncpg)
- **Redis** - Message broker for Celery
- **Celery** - Distributed task queue for async processing
- **EasyOCR** - Deep learning-based OCR (supports 80+ languages)
- **OpenCV** - Image preprocessing (grayscale, CLAHE, thresholding)

### Frontend (`web/`)

- **Vite 6** + **React 19** + **TypeScript**
- **TanStack Router** - File-based routing with type safety
- **TanStack Query** - Data fetching, caching, and polling
- **Tailwind CSS 3** - Utility-first styling

### Infrastructure

- **Docker Compose** - Container orchestration
- **nginx** - Frontend static serving and API proxy

## Project Structure

```
license-plate-recognition/
├── Dockerfile                        # Backend Docker image
├── Makefile                          # Development commands
├── alembic.ini                       # Alembic configuration
├── requirements.txt                  # Python dependencies
├── app/                              # Backend (Python/FastAPI)
│   ├── __init__.py
│   ├── main.py                       # FastAPI app, CORS, static files
│   ├── CLAUDE.md                     # Backend detailed docs
│   ├── shared/                       # Shared utilities
│   │   ├── __init__.py               # Exports config & database
│   │   ├── config.py                 # Pydantic settings from env
│   │   └── database.py               # SQLAlchemy async engine & session
│   ├── models/                       # Database models & schemas
│   │   ├── __init__.py               # Exports all models & schemas
│   │   ├── recognition.py            # RecognitionRequest model
│   │   └── schemas.py                # Pydantic request/response schemas
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py                 # POST/GET /api/v1/recognition
│   ├── services/
│   │   ├── __init__.py
│   │   ├── storage.py                # StorageService (Local/S3/Supabase)
│   │   └── recognition.py            # EasyOCR integration
│   ├── worker/
│   │   ├── __init__.py
│   │   ├── celery_app.py             # Celery configuration
│   │   └── tasks.py                  # process_plate_recognition task
│   └── migrations/                   # Alembic migrations
│       ├── env.py                    # Migration environment
│       ├── script.py.mako            # Migration template
│       └── versions/                 # Migration files
├── web/                              # Frontend (React/Vite)
│   ├── CLAUDE.md                     # Frontend detailed docs
│   ├── src/
│   │   ├── main.tsx                  # App entry, QueryClient, Router
│   │   ├── index.css                 # Tailwind imports
│   │   ├── routes/
│   │   │   ├── __root.tsx            # Root layout with header
│   │   │   ├── index.tsx             # Home page (upload + list)
│   │   │   └── requests/
│   │   │       └── $requestId.tsx    # Request detail page
│   │   ├── components/
│   │   │   ├── ImageUpload.tsx       # Drag-and-drop upload
│   │   │   ├── RequestList.tsx       # Table of all requests
│   │   │   └── RequestStatus.tsx     # Status badge component
│   │   ├── api/
│   │   │   └── client.ts             # API functions (fetch wrapper)
│   │   └── types/
│   │       └── index.ts              # TypeScript interfaces
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts                # Vite + TanStack Router plugin
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── nginx.conf                    # Production nginx config
│   ├── index.html
│   └── Dockerfile
├── images/                           # Sample test images
│   ├── placa1.jpg
│   ├── placa2.jpg
│   ├── placa3.JPG
│   └── placa4.jpg
├── docker-compose.yml                # All services definition
├── .env.example                      # Environment template
├── .gitignore
├── LICENSE
├── README.md
└── CLAUDE.md                         # This file
```

## API Endpoints

| Method | Endpoint                                  | Description                        |
| ------ | ----------------------------------------- | ---------------------------------- |
| `POST` | `/api/v1/recognition`                     | Upload image, returns `request_id` |
| `GET`  | `/api/v1/recognition/{id}`                | Get request status and result      |
| `GET`  | `/api/v1/recognition?page=1&page_size=10` | List requests (paginated)          |
| `GET`  | `/health`                                 | Health check endpoint              |
| `GET`  | `/uploads/{filename}`                     | Serve uploaded images              |

### Request/Response Examples

**POST /api/v1/recognition**

```bash
curl -X POST http://localhost:8000/api/v1/recognition \
  -F "file=@plate.jpg"
```

```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "PENDING",
  "created_at": "2024-01-24T10:00:00Z"
}
```

**GET /api/v1/recognition/{id}**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "image_url": "/uploads/550e8400-e29b-41d4-a716-446655440000.jpg",
  "plate_number": "ABC1234",
  "status": "COMPLETED",
  "error_message": null,
  "created_at": "2024-01-24T10:00:00Z",
  "updated_at": "2024-01-24T10:00:05Z"
}
```

## Database Schema

```sql
CREATE TABLE recognition_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    image_url VARCHAR(500) NOT NULL,
    plate_number VARCHAR(50),
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',  -- PENDING, COMPLETED, FAILED
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## Docker Services

| Service  | Image              | Port | Description            |
| -------- | ------------------ | ---- | ---------------------- |
| `db`     | postgres:16-alpine | 5432 | PostgreSQL database    |
| `redis`  | redis:7-alpine     | 6379 | Message broker         |
| `app`    | ./Dockerfile       | 8000 | FastAPI backend        |
| `worker` | ./Dockerfile       | -    | Celery worker          |
| `web`    | ./web/Dockerfile   | 80   | React frontend (nginx) |

## Development Commands

Use `make help` to see all available commands.

```bash
# Quick start with Docker
make docker-up                    # Start all services
make docker-logs                  # View logs
make docker-down                  # Stop services

# Local development (requires PostgreSQL & Redis running)
make install                      # Install Python dependencies
make migrate                      # Run database migrations
make api                          # Start FastAPI server
make worker                       # Start Celery worker (separate terminal)

# Database migrations
make migrate                      # Apply migrations
make migrate-create MSG="add new field"  # Create new migration
make migrate-down                 # Rollback one version

# Frontend development (pnpm or npm)
cd web
pnpm install                      # Or: npm install
pnpm dev                          # Or: npm run dev (http://localhost:5173)

# Testing
make test-upload                  # Test with sample image
```

### Without Make

```bash
# Docker
docker-compose up --build

# Backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Worker (separate terminal)
celery -A app.worker.celery_app worker --loglevel=info
```

```

## Environment Variables

Copy `.env.example` to `.env` and configure:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/plate_recognition` | PostgreSQL connection |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection |
| `STORAGE_TYPE` | `local` | Storage backend: `local`, `s3`, `supabase` |
| `UPLOAD_DIR` | `uploads` | Local upload directory |
| `CORS_ORIGINS` | `["http://localhost:5173"]` | Allowed CORS origins |
| `AWS_ACCESS_KEY_ID` | - | For S3 storage |
| `AWS_SECRET_ACCESS_KEY` | - | For S3 storage |
| `AWS_BUCKET_NAME` | - | For S3 storage |
| `SUPABASE_URL` | - | For Supabase storage |
| `SUPABASE_KEY` | - | For Supabase storage |
| `SUPABASE_BUCKET` | - | For Supabase storage |

## Recognition Flow

```

1. User uploads image via frontend
   └── POST /api/v1/recognition (multipart/form-data)

2. Backend receives image
   ├── Validates file is an image
   ├── Generates UUID for request
   ├── Saves image to storage (local/S3/Supabase)
   ├── Creates DB record with status=PENDING
   └── Queues Celery task: process_plate_recognition(request_id)

3. Celery worker picks up task
   ├── Loads image from storage
   ├── Preprocesses image (grayscale, CLAHE, bilateral filter)
   ├── Runs EasyOCR to extract text
   ├── Validates text against plate patterns
   └── Updates DB: status=COMPLETED, plate_number=result

4. Frontend polls for updates
   └── GET /api/v1/recognition/{id} every 2 seconds while PENDING

5. User sees result
   └── plate_number displayed with COMPLETED/FAILED status

````

## Key Implementation Details

### Storage Service (`app/services/storage.py`)
Abstract `StorageService` class with implementations:
- `LocalStorageService` - Saves to filesystem, serves via `/uploads`
- `S3StorageService` - AWS S3 (stub, extend as needed)
- `SupabaseStorageService` - Supabase Storage (stub, extend as needed)

### Recognition Service (`app/services/recognition.py`)
- Uses EasyOCR with English language model
- Preprocessing: grayscale → CLAHE → bilateral filter → adaptive threshold
- Pattern matching for common plate formats (ABC1234, ABC1D23, etc.)
- Returns highest confidence match that looks like a plate

### Frontend Polling
- TanStack Query `refetchInterval` set to 2000ms while status is PENDING
- Automatically stops polling when COMPLETED or FAILED

## Testing

```bash
# Test with sample images
curl -X POST http://localhost:8000/api/v1/recognition \
  -F "file=@images/placa1.jpg"

# Check result
curl http://localhost:8000/api/v1/recognition/{request_id}

# Interactive API docs
open http://localhost:8000/docs
````

## Useful Locations

- **Config & Settings**: `app/shared/config.py`
- **Database Setup**: `app/shared/database.py`
- **Database Models**: `app/models/recognition.py`
- **Pydantic Schemas**: `app/models/schemas.py`
- **API Routes**: `app/api/routes.py`
- **OCR Logic**: `app/services/recognition.py`
- **Celery Tasks**: `app/worker/tasks.py`
- **Migrations**: `app/migrations/versions/`
- **Frontend Pages**: `web/src/routes/`
- **API Client**: `web/src/api/client.ts`
- **Docker Config**: `docker-compose.yml`, `Dockerfile`

## Known Issues & Fixes

### Backend: Uploads Directory

The `uploads` directory must exist before FastAPI mounts static files. This is handled in `app/main.py` at module load time (before app instantiation):

```python
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
```

### Frontend: TanStack Router Versions

TanStack Router packages must have matching versions to avoid plugin errors. All packages are pinned to version `1.94.0`. If you encounter plugin errors, do a clean install:

```bash
cd web
rm -rf node_modules pnpm-lock.yaml  # Or package-lock.json
pnpm install  # Or npm install
```

## Detailed Documentation

For more detailed context on each part of the application:

- **Backend details**: See `app/CLAUDE.md`
- **Frontend details**: See `web/CLAUDE.md`
