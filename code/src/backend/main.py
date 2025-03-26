from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from motor.motor_asyncio import AsyncIOMotorClient
import uvicorn
from app.routers import entities, files, transactions, pipeline
from app.core.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to MongoDB
    app.mongodb_client = AsyncIOMotorClient(settings.MONGODB_URL)
    app.mongodb = app.mongodb_client[settings.MONGODB_DB_NAME]
    
    yield
    
    # Shutdown: Close MongoDB connection
    app.mongodb_client.close()

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
        
    openapi_schema = get_openapi(
        title="Risk Analysis API",
        version="1.0.0",
        description="""
        Risk Analysis System API for entity risk assessment and transaction processing.
        
        ## Features
        
        * Entity risk analysis and scoring
        * Transaction processing and monitoring
        * File upload and processing
        * Integration with OFAC and SEC data
        * Complete data processing pipeline
        
        ## Pipeline Stages
        
        1. Ingestion: Load and validate data
        2. Extraction: Parse and identify entities
        3. Enrichment: Add external context
        4. Assessment: Analyze patterns
        5. Risk Scoring: Calculate risk levels
        6. Reporting: Generate insights
        
        ## Authentication
        
        All endpoints require authentication using JWT tokens.
        """,
        routes=app.routes,
        tags=[
            {
                "name": "pipeline",
                "description": "Data processing pipeline operations",
            },
            {
                "name": "entities",
                "description": "Operations with entities including risk analysis and enrichment",
            },
            {
                "name": "files",
                "description": "File upload and processing operations",
            },
            {
                "name": "transactions",
                "description": "Transaction processing and monitoring",
            },
        ],
        contact={
            "name": "API Support",
            "email": "support@example.com",
            "url": "https://example.com/support",
        },
        license_info={
            "name": "Apache 2.0",
            "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
        },
    )
    
    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app = FastAPI(
    title="Risk Analysis API",
    description="API for entity risk analysis and transaction processing",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None,  # Disable default docs
    redoc_url=None,  # Disable default redoc
)

# Custom documentation endpoints
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="Risk Analysis API",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
        swagger_favicon_url="https://fastapi.tiangolo.com/img/favicon.png",
    )

@app.get("/openapi.json", include_in_schema=False)
async def get_openapi_endpoint():
    return custom_openapi()

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite's default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(pipeline.router, prefix="/api/pipeline", tags=["pipeline"])
app.include_router(entities.router, prefix="/api/entities", tags=["entities"])
app.include_router(files.router, prefix="/api/files", tags=["files"])
app.include_router(transactions.router, prefix="/api/transactions", tags=["transactions"])

@app.get("/api/health")
async def health_check():
    """
    Check the health status of the API.
    
    Returns:
        dict: A dictionary containing the health status
    """
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        workers=1,
        log_level="info"
    )