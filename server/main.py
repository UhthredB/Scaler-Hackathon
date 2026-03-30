"""
Job Application Simulator - FastAPI Server

Run with: uvicorn server.main:app --reload
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn

from .job_app_environment import JobAppEnvironment

# Create app
app = FastAPI(
    title="Job Application Simulator",
    description="OpenEnv environment for training agents to apply for jobs",
    version="0.1.0"
)

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global environment instance
env = JobAppEnvironment()


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class ResetRequest(BaseModel):
    profile_name: str = "software_engineer"
    budget: int = 10
    difficulty: str = "normal"


class ActionRequest(BaseModel):
    episode_id: str
    action: Dict[str, Any]


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Health check"""
    return {"status": "ok", "environment": "job-application-simulator"}


@app.get("/health")
async def health():
    """Health check endpoint for HF Spaces"""
    return {"status": "healthy"}


@app.post("/reset")
async def reset(request: ResetRequest):
    """Start a new episode"""
    try:
        state = env.reset(
            profile_name=request.profile_name,
            budget=request.budget,
            difficulty=request.difficulty
        )
        return state.model_dump()
    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}


@app.post("/step")
async def step(request: ActionRequest):
    """Execute an action in the episode"""
    return env.step(request.episode_id, request.action)


@app.get("/state/{episode_id}")
async def get_state(episode_id: str):
    """Get current episode state"""
    result = env.step(episode_id, {"type": "state"})
    if "error" in result:
        raise HTTPException(status_code=404, detail=f"Episode {episode_id} not found")
    return result


@app.get("/jobs")
async def list_jobs():
    """List all available jobs in the database"""
    from mock_data import get_jobs
    return {"jobs": get_jobs()}


@app.get("/profiles")
async def list_profiles():
    """List available applicant profiles"""
    from mock_data import PROFILES
    return {"profiles": list(PROFILES.keys())}


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=7860)
    parser.add_argument("--host", default="0.0.0.0")
    args = parser.parse_args()
    uvicorn.run(app, host=args.host, port=args.port)
