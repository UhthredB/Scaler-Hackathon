"""Main FastAPI application for Job Application Simulator."""

import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn

from job_app_environment import env

app = FastAPI(
    title="Job Application Simulator",
    description="An OpenEnv-compliant environment simulating job applications",
    version="1.0.0"
)

# Add CORS for HF Spaces
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request models
class ResetRequest(BaseModel):
    profile_name: str = "software_engineer"


class StepRequest(BaseModel):
    episode_id: str
    action: str
    job_id: Optional[str] = None
    query: Optional[str] = None
    cover_letter: Optional[str] = None


# Health endpoints
@app.get("/")
def root():
    return {"status": "running", "service": "job-application-simulator", "version": "1.0.0"}


@app.get("/health")
def health():
    return {"status": "healthy"}


# OpenEnv required endpoints
@app.post("/reset")
def reset(request: ResetRequest = ResetRequest()):
    """Reset environment and start new episode."""
    state = env.reset(request.profile_name)
    return {
        "episode_id": state.episode_id,
        "profile": state.current_profile,
        "budget": state.budget_remaining,
        "message": state.messages[-1] if state.messages else "Episode started"
    }


@app.post("/step")
def step(request: StepRequest):
    """Execute action in environment."""
    kwargs = {}
    if request.job_id:
        kwargs["job_id"] = request.job_id
    if request.query:
        kwargs["query"] = request.query
    if request.cover_letter:
        kwargs["cover_letter"] = request.cover_letter
    
    result = env.step(request.episode_id, request.action, **kwargs)
    return result


@app.get("/state")
def get_state(episode_id: str = Query(..., description="Episode ID")):
    """Get current environment state."""
    state = env.get_state(episode_id)
    if not state:
        raise HTTPException(status_code=404, detail="Episode not found")
    return state


@app.get("/tasks")
def list_tasks():
    """List available tasks."""
    return {"tasks": env.list_tasks()}


@app.post("/tasks/{task_id}/grade")
def grade_task(task_id: str, episode_id: str = Query(..., description="Episode ID to grade")):
    """Grade a specific task. Returns score in 0.0-1.0 range."""
    result = env.grade_task(episode_id, task_id)
    if "error" in result and result.get("error") == "Episode not found":
        raise HTTPException(status_code=404, detail="Episode not found")
    return result


# Data endpoints
@app.get("/jobs")
def get_jobs():
    """Get all available job listings."""
    from mock_data import JOBS
    return {"jobs": JOBS}


@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    """Get specific job details."""
    from mock_data import get_job_by_id, PROFILES
    job = get_job_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    # Calculate match score for default profile
    default_profile = PROFILES.get("software_engineer", {})
    match_score = 0.0
    if default_profile:
        from mock_data import calculate_match_score
        match_score = calculate_match_score(default_profile, job)
    return {"job": job, "match_score": match_score}


@app.get("/profiles")
def get_profiles():
    """Get available applicant profiles."""
    from mock_data import PROFILES
    return {"profiles": list(PROFILES.keys())}


@app.get("/profiles/{profile_name}")
def get_profile_details(profile_name: str):
    """Get specific profile details."""
    from mock_data import get_profile
    profile = get_profile(profile_name)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"profile": profile}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
