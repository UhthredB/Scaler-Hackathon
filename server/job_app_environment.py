"""Job Application Environment - OpenEnv compliant implementation."""

import uuid
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mock_data import get_jobs, get_job_by_id, get_profile, calculate_match_score


class JobAppState(BaseModel):
    """State of a job application episode."""
    episode_id: str
    step_count: int = 0
    current_profile: Optional[Dict[str, Any]] = None
    budget_remaining: float = 100.0
    applications_submitted: List[Dict[str, Any]] = Field(default_factory=list)
    total_reward: float = 0.0
    done: bool = False
    messages: List[str] = Field(default_factory=list)


class JobAppEnvironment:
    """Job Application Simulator Environment."""
    
    def __init__(self):
        self.episodes: Dict[str, JobAppState] = {}
        self.application_cost = 5.0  # Cost per application
        self.max_steps = 20
        
    def reset(self, profile_name: str = "software_engineer") -> JobAppState:
        """Reset environment and start new episode."""
        episode_id = f"ep_{uuid.uuid4().hex[:8]}"
        profile = get_profile(profile_name)
        
        state = JobAppState(
            episode_id=episode_id,
            current_profile=profile,
            messages=[f"Welcome! You are applying as {profile.get('name', 'Applicant')}."]
        )
        self.episodes[episode_id] = state
        return state
    
    def step(self, episode_id: str, action: str, **kwargs) -> Dict[str, Any]:
        """Execute action in environment."""
        state = self.episodes.get(episode_id)
        if not state:
            return {"error": "Episode not found", "done": True}
        
        if state.done:
            return {"error": "Episode already completed", "done": True}
        
        state.step_count += 1
        result = {"step": state.step_count, "action": action}
        
        if action == "search_jobs":
            jobs = get_jobs()
            query = kwargs.get("query", "")
            if query:
                jobs = [j for j in jobs if query.lower() in j["title"].lower() or query.lower() in j["company"].lower()]
            result["jobs"] = jobs[:5]  # Return top 5
            result["budget_remaining"] = state.budget_remaining
            state.messages.append(f"Searched for jobs: found {len(result['jobs'])} listings")
        
        elif action == "view_job":
            job_id = kwargs.get("job_id")
            job = get_job_by_id(job_id)
            if job:
                match_score = calculate_match_score(state.current_profile, job)
                result["job"] = job
                result["match_score"] = match_score
                state.messages.append(f"Viewed job: {job['title']} at {job['company']} (match: {match_score})")
            else:
                result["error"] = "Job not found"
        
        elif action == "apply":
            job_id = kwargs.get("job_id")
            cover_letter = kwargs.get("cover_letter", "")
            job = get_job_by_id(job_id)
            
            if not job:
                result["error"] = "Job not found"
            elif state.budget_remaining < self.application_cost:
                result["error"] = "Insufficient budget"
                state.done = True
            else:
                state.budget_remaining -= self.application_cost
                match_score = calculate_match_score(state.current_profile, job)
                
                # Calculate reward based on match score and cover letter quality
                cover_letter_bonus = min(0.2, len(cover_letter) / 500)  # Up to 0.2 bonus
                reward = match_score * 10 + cover_letter_bonus * 10
                
                application = {
                    "job_id": job_id,
                    "job_title": job["title"],
                    "company": job["company"],
                    "match_score": match_score,
                    "cover_letter_length": len(cover_letter),
                    "reward": round(reward, 2)
                }
                state.applications_submitted.append(application)
                state.total_reward += reward
                state.messages.append(f"Applied to {job['title']} at {job['company']} - reward: {reward:.2f}")
                
                result["application"] = application
                result["reward"] = round(reward, 2)
                result["budget_remaining"] = state.budget_remaining
            
        elif action == "check_status":
            result["applications"] = state.applications_submitted
            result["budget_remaining"] = state.budget_remaining
            result["total_reward"] = state.total_reward
        
        else:
            result["error"] = f"Unknown action: {action}"
        
        # Check termination conditions
        if state.step_count >= self.max_steps or state.budget_remaining < self.application_cost:
            state.done = True
            result["done"] = True
            result["final_reward"] = state.total_reward
            state.messages.append(f"Episode complete! Total reward: {state.total_reward:.2f}")
        
        result["budget_remaining"] = state.budget_remaining
        result["total_reward"] = state.total_reward
        return result
    
    def get_state(self, episode_id: str) -> Optional[Dict[str, Any]]:
        """Get current state of episode."""
        state = self.episodes.get(episode_id)
        if state:
            return state.model_dump()
        return None
    
    def grade_task(self, episode_id: str, task_id: str) -> Dict[str, Any]:
        """Grade task completion. Returns score in 0.0-1.0 range."""
        state = self.episodes.get(episode_id)
        if not state:
            return {"error": "Episode not found", "score": 0.0, "passed": False}
        
        if task_id == "easy_apply":
            # Submit 3 applications with match score > 0.5
            high_match = [a for a in state.applications_submitted if a.get("match_score", 0) > 0.5]
            score = min(1.0, len(high_match) / 3.0)
            return {
                "task_id": task_id,
                "score": round(score, 2),
                "passed": score >= 1.0,
                "details": f"{len(high_match)}/3 applications with match > 0.5"
            }
        
        elif task_id == "smart_searcher":
            # Find and apply to 3 best matching jobs within budget
            if state.budget_remaining < 0:
                return {"task_id": task_id, "score": 0.0, "passed": False, "details": "Budget exceeded"}
            high_match = [a for a in state.applications_submitted if a.get("match_score", 0) > 0.7]
            score = min(1.0, len(high_match) / 3.0)
            return {
                "task_id": task_id,
                "score": round(score, 2),
                "passed": score >= 1.0,
                "details": f"{len(high_match)}/3 applications with match > 0.7"
            }
        
        elif task_id == "application_master":
            # Maximize total reward
            max_possible = 30.0
            score = min(1.0, state.total_reward / max_possible)
            return {
                "task_id": task_id,
                "score": round(score, 2),
                "passed": score >= 0.8,
                "details": f"Total reward: {state.total_reward:.2f}/{max_possible}"
            }
        
        return {"error": "Unknown task", "score": 0.0, "passed": False}
    
    def list_tasks(self) -> List[Dict[str, Any]]:
        """Return available tasks."""
        return [
            {
                "id": "easy_apply",
                "name": "Easy Apply",
                "difficulty": "easy",
                "description": "Submit 3 job applications with match score > 0.5",
                "max_reward": 1.0
            },
            {
                "id": "smart_searcher",
                "name": "Smart Searcher",
                "difficulty": "medium",
                "description": "Find and apply to 3 best matching jobs (match > 0.7) within budget",
                "max_reward": 1.0
            },
            {
                "id": "application_master",
                "name": "Application Master",
                "difficulty": "hard",
                "description": "Maximize total reward through strategic job selection and quality applications",
                "max_reward": 1.0
            }
        ]


# Global environment instance
env = JobAppEnvironment()
