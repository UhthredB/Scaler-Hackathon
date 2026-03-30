"""Job Application Simulator - FastAPI Server for HF Space"""

import os
import uuid
import random
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# ============================================================================
# MODELS
# ============================================================================

class JobPosting(BaseModel):
    id: str
    title: str
    company: str
    location: str
    salary_min: int
    salary_max: int
    description: str
    requirements: List[str]
    nice_to_have: List[str]
    posted_date: str
    job_type: str = "full-time"
    remote: bool = False


class ApplicantProfile(BaseModel):
    name: str
    skills: List[str]
    experience_years: int
    education: str
    current_role: str
    target_roles: List[str]
    preferred_locations: List[str]
    salary_min: int
    salary_max: int


class JobAnalysis(BaseModel):
    job_id: str
    match_score: float
    matching_skills: List[str]
    missing_skills: List[str]
    key_requirements: List[str]
    recommended_focus: str


class SubmittedApplication(BaseModel):
    job_id: str
    cover_letter: str
    submission_time: str
    match_score: float
    status: str = "pending"


class EpisodeState(BaseModel):
    episode_id: str
    step_count: int
    current_job: Optional[JobPosting]
    applicant_profile: Optional[ApplicantProfile]
    applications_submitted: List[SubmittedApplication]
    budget_remaining: float
    last_search_results: List[JobPosting]
    total_reward: float


# ============================================================================
# SAMPLE DATA
# ============================================================================

SAMPLE_JOBS = [
    JobPosting(
        id="job-001",
        title="Senior Software Engineer",
        company="TechCorp Inc",
        location="San Francisco, CA",
        salary_min=150000,
        salary_max=200000,
        description="Join our team building next-gen cloud infrastructure. You'll work on distributed systems, microservices, and scalable APIs.",
        requirements=["Python", "Kubernetes", "AWS", "5+ years experience"],
        nice_to_have=["Go", "Terraform", "ML experience"],
        posted_date="2024-01-15",
        remote=True
    ),
    JobPosting(
        id="job-002",
        title="ML Engineer",
        company="AI Startup",
        location="Remote",
        salary_min=140000,
        salary_max=180000,
        description="Build and deploy machine learning models for production systems. Work on NLP, computer vision, and recommendation systems.",
        requirements=["Python", "TensorFlow/PyTorch", "MLOps", "3+ years ML experience"],
        nice_to_have=["Kubernetes", "CUDA optimization", "Research publications"],
        posted_date="2024-01-14",
        remote=True
    ),
    JobPosting(
        id="job-003",
        title="Backend Developer",
        company="FinTech Co",
        location="New York, NY",
        salary_min=130000,
        salary_max=170000,
        description="Design and build financial APIs and services. High-throughput, low-latency systems for trading platform.",
        requirements=["Java", "Spring Boot", "PostgreSQL", "4+ years experience"],
        nice_to_have=["Kafka", "Redis", "Financial domain knowledge"],
        posted_date="2024-01-13",
        remote=False
    ),
    JobPosting(
        id="job-004",
        title="Full Stack Engineer",
        company="SaaS Platform",
        location="Austin, TX",
        salary_min=120000,
        salary_max=160000,
        description="Build end-to-end features for our B2B SaaS product. Frontend, backend, and everything in between.",
        requirements=["React", "Node.js", "TypeScript", "3+ years experience"],
        nice_to_have=["GraphQL", "PostgreSQL", "DevOps skills"],
        posted_date="2024-01-12",
        remote=True
    ),
    JobPosting(
        id="job-005",
        title="DevOps Engineer",
        company="CloudNative Corp",
        location="Seattle, WA",
        salary_min=140000,
        salary_max=190000,
        description="Build and maintain CI/CD pipelines, infrastructure as code, and platform tooling.",
        requirements=["Kubernetes", "Terraform", "CI/CD", "AWS/GCP"],
        nice_to_have=["Python", "Go", "Platform engineering"],
        posted_date="2024-01-11",
        remote=True
    ),
]

SAMPLE_PROFILES = {
    "software_engineer": ApplicantProfile(
        name="Alex Developer",
        skills=["Python", "JavaScript", "React", "Node.js", "PostgreSQL", "Docker", "AWS", "Git"],
        experience_years=5,
        education="BS Computer Science",
        current_role="Software Engineer",
        target_roles=["Senior Software Engineer", "Full Stack Developer", "ML Engineer"],
        preferred_locations=["Remote", "San Francisco", "New York"],
        salary_min=130000,
        salary_max=180000
    ),
    "ml_engineer": ApplicantProfile(
        name="Sam Data",
        skills=["Python", "TensorFlow", "PyTorch", "MLOps", "SQL", "Docker", "Kubernetes"],
        experience_years=4,
        education="MS Machine Learning",
        current_role="Data Scientist",
        target_roles=["ML Engineer", "AI Engineer", "Research Scientist"],
        preferred_locations=["Remote", "San Francisco", "Seattle"],
        salary_min=140000,
        salary_max=200000
    ),
}

# Tasks for grading
TASKS = [
    {"id": "apply-quality", "name": "Quality Applications", "description": "Submit high-quality applications with good match scores"},
    {"id": "budget-efficiency", "name": "Budget Efficiency", "description": "Maximize reward within budget constraints"},
    {"id": "search-optimization", "name": "Search Optimization", "description": "Find and identify best-matching jobs"},
]


# ============================================================================
# APP STATE
# ============================================================================

episodes: Dict[str, EpisodeState] = {}


# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title="Job Application Simulator",
    description="An environment for testing AI agents on job application tasks",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "environment": "job-application-simulator"}


@app.post("/reset")
async def reset(profile_name: str = "software_engineer"):
    """Reset environment and start new episode."""
    episode_id = f"ep-{uuid.uuid4().hex[:8]}"
    
    profile = SAMPLE_PROFILES.get(profile_name, SAMPLE_PROFILES["software_engineer"])
    
    episodes[episode_id] = EpisodeState(
        episode_id=episode_id,
        step_count=0,
        current_job=None,
        applicant_profile=profile,
        applications_submitted=[],
        budget_remaining=100.0,  # Starting budget
        last_search_results=[],
        total_reward=0.0
    )
    
    return {
        "episode_id": episode_id,
        "profile": profile.model_dump(),
        "budget": 100.0,
        "message": f"Episode started for {profile.name}"
    }


@app.post("/step")
async def step(action_data: dict):
    """Execute an action in the environment."""
    episode_id = action_data.get("episode_id")
    action = action_data.get("action")
    
    if not episode_id or episode_id not in episodes:
        raise HTTPException(status_code=400, detail="Invalid episode_id")
    
    state = episodes[episode_id]
    state.step_count += 1
    
    if action == "search_jobs":
        query = action_data.get("query", "")
        # Simple search - return jobs matching query or all jobs
        if query:
            jobs = [j for j in SAMPLE_JOBS if query.lower() in j.title.lower() or query.lower() in j.description.lower()]
        else:
            jobs = SAMPLE_JOBS.copy()
        
        state.last_search_results = jobs
        return {
            "jobs": [j.model_dump() for j in jobs],
            "count": len(jobs),
            "budget_remaining": state.budget_remaining
        }
    
    elif action == "view_job":
        job_id = action_data.get("job_id")
        job = next((j for j in SAMPLE_JOBS if j.id == job_id), None)
        
        if not job:
            return {"error": "Job not found"}
        
        state.current_job = job
        
        # Calculate match score
        profile = state.applicant_profile
        matching_skills = [s for s in profile.skills if any(s.lower() in r.lower() for r in job.requirements)]
        missing_skills = [r for r in job.requirements if not any(s.lower() in r.lower() for s in profile.skills)]
        match_score = len(matching_skills) / max(len(job.requirements), 1)
        
        analysis = {
            "job_id": job_id,
            "match_score": match_score,
            "matching_skills": matching_skills,
            "missing_skills": missing_skills,
            "job_details": job.model_dump()
        }
        
        return analysis
    
    elif action == "apply":
        job_id = action_data.get("job_id")
        cover_letter = action_data.get("cover_letter", "")
        
        # Check budget
        apply_cost = 10.0
        if state.budget_remaining < apply_cost:
            return {"error": "Insufficient budget", "budget_remaining": state.budget_remaining}
        
        job = next((j for j in SAMPLE_JOBS if j.id == job_id), None)
        if not job:
            return {"error": "Job not found"}
        
        # Calculate match score
        profile = state.applicant_profile
        matching_skills = [s for s in profile.skills if any(s.lower() in r.lower() for r in job.requirements)]
        match_score = len(matching_skills) / max(len(job.requirements), 1)
        
        # Calculate reward based on match and cover letter quality
        cover_letter_quality = min(len(cover_letter) / 500, 1.0)  # Simple heuristic
        base_reward = match_score * 50
        bonus = cover_letter_quality * 20
        reward = base_reward + bonus
        
        # Apply cost
        state.budget_remaining -= apply_cost
        state.total_reward += reward
        
        # Record application
        application = SubmittedApplication(
            job_id=job_id,
            cover_letter=cover_letter,
            submission_time=datetime.now().isoformat(),
            match_score=match_score,
            status="pending"
        )
        state.applications_submitted.append(application)
        
        return {
            "status": "applied",
            "job_id": job_id,
            "reward": reward,
            "match_score": match_score,
            "budget_remaining": state.budget_remaining,
            "application_number": len(state.applications_submitted)
        }
    
    else:
        return {"error": f"Unknown action: {action}"}


@app.get("/state")
async def get_state(episode_id: str):
    """Get current environment state."""
    if episode_id not in episodes:
        raise HTTPException(status_code=404, detail="Episode not found")
    
    state = episodes[episode_id]
    return {
        "episode_id": state.episode_id,
        "step_count": state.step_count,
        "applicant_profile": state.applicant_profile.model_dump() if state.applicant_profile else None,
        "current_job": state.current_job.model_dump() if state.current_job else None,
        "applications_submitted": [a.model_dump() for a in state.applications_submitted],
        "budget_remaining": state.budget_remaining,
        "total_reward": state.total_reward,
        "last_search_results": [j.model_dump() for j in state.last_search_results]
    }


@app.get("/tasks")
async def get_tasks():
    """Get available tasks for grading."""
    return {"tasks": TASKS}


@app.post("/tasks/{task_id}/grade")
async def grade_task(task_id: str, episode_id: str = Query(...)):
    """Grade a specific task for an episode."""
    if episode_id not in episodes:
        raise HTTPException(status_code=404, detail="Episode not found")
    
    state = episodes[episode_id]
    
    if task_id == "apply-quality":
        # Grade based on average match score of applications
        if not state.applications_submitted:
            return {"passed": False, "score": 0.0, "details": "No applications submitted"}
        
        avg_match = sum(a.match_score for a in state.applications_submitted) / len(state.applications_submitted)
        score = avg_match * 100
        passed = avg_match >= 0.4
        return {"passed": passed, "score": score, "details": f"Average match: {avg_match:.2f}"}
    
    elif task_id == "budget-efficiency":
        # Grade based on total reward vs budget used
        budget_used = 100.0 - state.budget_remaining
        if budget_used <= 0:
            return {"passed": False, "score": 0.0, "details": "No budget used"}
        
        efficiency = state.total_reward / budget_used
        score = min(efficiency * 10, 100)
        passed = efficiency >= 1.0
        return {"passed": passed, "score": score, "details": f"Efficiency: {efficiency:.2f} reward per unit budget"}
    
    elif task_id == "search-optimization":
        # Grade based on finding and viewing jobs
        score = min(state.step_count * 10, 100)
        passed = state.step_count >= 3
        return {"passed": passed, "score": score, "details": f"Steps taken: {state.step_count}"}
    
    else:
        return {"passed": False, "score": 0.0, "details": "Unknown task"}


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
