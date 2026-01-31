from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.variables import router as variable_router
from .api.relationships import router as relationship_router
from .api.experiments import router as experiments_router
from .api.optimize import router as optimize_router

app = FastAPI(
    title="Product Optimizer API",
    description="API for managing variables and their relationships in product optimization",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(variable_router)
app.include_router(relationship_router)
app.include_router(experiments_router)
app.include_router(optimize_router)


@app.get("/")
def read_root():
    return {
        "msg": "Product Optimizer API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
