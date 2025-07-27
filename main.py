from fastapi import FastAPI
from contextlib import asynccontextmanager
from routes import agent_routes
from config import settings
from fastapi.middleware.cors import CORSMiddleware


# Define the lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles startup and shutdown events for the FastAPI application.
    """
    if not settings.OPENAI_API_KEY:
        print("FastAPI Startup: OPENAI_API_KEY is missing. Agent operations may fail.")
    if not settings.TAVILY_API_KEY:
        print("FastAPI Startup: TAVILY_API_KEY is missing. Internet search may fail.")
    yield
    print("FastAPI Shutdown: Application is shutting down.")


app = FastAPI(
    title="Auraa Agent Microservice",
    description="API for the Auraa Manager Agent to process user queries using specialized sub-agents.",
    version="1.0.0",
    lifespan=lifespan,
)


# Configure CORS middleware
# This allows all origins, methods, and headers.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the API router
app.include_router(agent_routes.router)


@app.get("/")
async def read_root():
    """
    Root endpoint for basic health check.
    """
    return {"message": "Auraa Agent Microservice is running!"}


# Run: uvicorn main:app --reload --port 8000
# access at http://127.0.0.1:8000/docs
