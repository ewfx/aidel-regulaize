# 360° Risk Lens

A comprehensive risk analysis system for financial transactions and entity monitoring.

## Features

- Real-time transaction risk analysis
- Entity extraction and relationship mapping
- Multi-source data enrichment (OFAC, SEC)
- Graph-based relationship analysis
- Vector similarity search
- Streaming data processing with Kafka
- Beautiful React dashboard with real-time updates

## Tech Stack

### Backend
- FastAPI
- MongoDB
- Neo4j (Graph Database)
- ChromaDB (Vector Store)
- Apache Kafka
- Transformers (NLP)
- SpaCy (Entity Extraction)

### Frontend
- React
- TanStack Query
- Tailwind CSS
- Lucide Icons

## Prerequisites

- Docker and Docker Compose
- Node.js 20+
- Python 3.11+

## Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/ewfx/aidel-regulaize.git
   cd aidel-regulaize
   ```

2. Start the infrastructure services:
(Install the docker app for your OS, if you dont have it already)
   ```bash
   cd code/src
   docker-compose up -d
   ```

3. Start the frontend:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   This should start the UI
   
4. Set up the backend:
   ```bash
   cd backend
   python -m venv .
   source ./bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   uvicorn main:app --reload
   ```

5. Access the application:
   - Frontend: http://localhost:5173
   - API Docs: http://localhost:8000/docs
   - Kafka UI: http://localhost:8080
   - Neo4j Browser: http://localhost:7474
   - ChromaDB UI: http://localhost:8001

## Environment Variables

### Backend (.env)
```env
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=risk_analysis
SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# ChromaDB settings
CHROMA_HOST=localhost
CHROMA_PORT=8001

# Neo4j settings
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=<password for neo4j>
```

## API Endpoints

### Transactions
- `GET /api/transactions` - List transactions
- `POST /api/transactions` - Create transaction
- `GET /api/transactions/{id}` - Get transaction details
- `PUT /api/transactions/{id}` - Update transaction
- `DELETE /api/transactions/{id}` - Delete transaction

### Entities
- `GET /api/entities` - Search entities
- `GET /api/entities/{id}` - Get entity details

### Files
- `POST /api/files` - Upload file
- `GET /api/files` - List files
- `GET /api/files/{id}` - Get file status
- `DELETE /api/files/{id}` - Delete file

### Pipeline
- `GET /api/pipeline/status/{file_id}` - Get processing status

## Development

### Code Structure

```
.
├── backend/
│   ├── app/
│   │   ├── core/          # Core configuration
│   │   ├── models/        # Data models
│   │   ├── routers/       # API routes
│   │   └── services/      # Business logic
│   ├── tests/             # Backend tests
│   └── requirements.txt   # Python dependencies
├── frontend/
│   ├── components/        # React components
│   ├── services/          # API client
│   └── types/            # TypeScript types
└── docker-compose.yml    # Infrastructure setup
```

### Testing

Run backend tests:
```bash
cd backend
pytest
```

Run frontend tests:
```bash
npm test
```