from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.lifespan import lifespan
from app.routers import background_remover, background_remover_parallel

# Load environment variables
load_dotenv(override=True)

app = FastAPI(
    title="Background Remover Service",
    description="A service to remove backgrounds from images using RedactedService API",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(background_remover.router)
app.include_router(background_remover_parallel.router)


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint for health check."""
    return {"message": "Background Remover Service is running"}


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}
