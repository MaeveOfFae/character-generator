"""Main FastAPI application for Character Generator."""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import blueprints, chat, config, drafts, export, generation, lineage, models, offspring, seedgen, similarity, templates, validation

# Create FastAPI app
app = FastAPI(
    title="Character Generator API",
    description="API for template-aware character generation, draft management, validation, and export",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(config.router, prefix="/api/config", tags=["Config"])
app.include_router(models.router, prefix="/api/models", tags=["Models"])
app.include_router(templates.router, prefix="/api/templates", tags=["Templates"])
app.include_router(blueprints.router, prefix="/api/blueprints", tags=["Blueprints"])
app.include_router(drafts.router, prefix="/api/drafts", tags=["Drafts"])
app.include_router(lineage.router, prefix="/api/lineage", tags=["Lineage"])
app.include_router(generation.router, prefix="/api/generate", tags=["Generation"])
app.include_router(seedgen.router, prefix="/api/seedgen", tags=["Seed Generator"])
app.include_router(similarity.router, prefix="/api/similarity", tags=["Similarity"])
app.include_router(offspring.router, prefix="/api/offspring", tags=["Offspring"])
app.include_router(export.router, prefix="/api/export", tags=["Export"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(validation.router, prefix="/api/validate", tags=["Validation"])


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "Character Generator API",
        "version": "2.0.0",
        "docs": "/docs",
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


def run():
    """Run the API server."""
    import uvicorn
    uvicorn.run(
        "bpui.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    run()
