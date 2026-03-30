"""Job Application Simulator - Client"""

from typing import Optional, List, Union
from openenv.core import EnvClient

from models import (
    JobAppState,
    JobAppObservation,
    SearchJobs,
    AnalyzeJob,
    WriteCoverLetter,
    SubmitApplication,
    NextJob,
    StepResult,
)


class JobAppEnv(EnvClient):
    """
    Client for the Job Application Simulator environment.
    
    Usage (async):
        async with JobAppEnv(base_url="...") as env:
            obs = await env.reset(profile_name="software_engineer")
            obs = await env.step(SearchJobs(keywords=["python", "remote"]))
    
    Usage (sync):
        with JobAppEnv(base_url="...").sync() as env:
            obs = env.reset()
            obs = env.step(AnalyzeJob(job_id="job_001"))
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        super().__init__(base_url)
        self._episode_id: Optional[str] = None
    
    async def reset(
        self,
        profile_name: str = "default",
        budget: int = 10,
        difficulty: str = "normal"
    ) -> JobAppObservation:
        """
        Reset the environment and start a new episode.
        
        Args:
            profile_name: Name of applicant profile to load
            budget: Maximum number of applications allowed
            difficulty: 'easy', 'normal', or 'hard' (affects job market)
        
        Returns:
            Initial observation with applicant profile
        """
        result = await self._send_action({
            "type": "reset",
            "profile_name": profile_name,
            "budget": budget,
            "difficulty": difficulty
        })
        self._episode_id = result.get("episode_id")
        return self._parse_observation(result)
    
    async def step(
        self,
        action: Union[SearchJobs, AnalyzeJob, WriteCoverLetter, SubmitApplication, NextJob]
    ) -> StepResult:
        """
        Execute an action in the environment.
        
        Args:
            action: One of SearchJobs, AnalyzeJob, WriteCoverLetter, SubmitApplication, NextJob
        
        Returns:
            StepResult with observation, reward, and done flag
        """
        action_dict = self._action_to_dict(action)
        result = await self._send_action(action_dict)
        
        observation = self._parse_observation(result)
        return StepResult(
            observation=observation,
            reward=result.get("reward", 0.0),
            done=result.get("done", False),
            info=result.get("info", {})
        )
    
    async def state(self) -> JobAppState:
        """Get current episode state."""
        result = await self._send_action({"type": "state"})
        return self._parse_state(result)
    
    # ========================================================================
    # CONVENIENCE METHODS
    # ========================================================================
    
    async def search(
        self,
        keywords: List[str],
        location: Optional[str] = None,
        salary_min: Optional[int] = None,
        remote_only: bool = False
    ) -> JobAppObservation:
        """Search for jobs with given criteria."""
        return await self.step(SearchJobs(
            keywords=keywords,
            location=location,
            salary_min=salary_min,
            remote_only=remote_only
        ))
    
    async def analyze(self, job_id: str) -> JobAppObservation:
        """Analyze a specific job for fit."""
        return await self.step(AnalyzeJob(job_id=job_id))
    
    async def write_letter(
        self,
        job_id: str,
        tone: str = "professional",
        highlight_skills: Optional[List[str]] = None
    ) -> JobAppObservation:
        """Write a cover letter for a job."""
        return await self.step(WriteCoverLetter(
            job_id=job_id,
            tone=tone,
            highlight_skills=highlight_skills or []
        ))
    
    async def apply(
        self,
        job_id: str,
        cover_letter: str,
        tailored_sections: Optional[dict] = None
    ) -> JobAppObservation:
        """Submit an application."""
        return await self.step(SubmitApplication(
            job_id=job_id,
            cover_letter=cover_letter,
            tailored_resume_sections=tailored_sections or {}
        ))
    
    async def next_job(self) -> JobAppObservation:
        """Move to next job in results."""
        return await self.step(NextJob())
    
    # ========================================================================
    # INTERNAL HELPERS
    # ========================================================================
    
    def _action_to_dict(self, action) -> dict:
        """Convert action dataclass to dictionary."""
        if isinstance(action, SearchJobs):
            return {
                "type": "search_jobs",
                "keywords": action.keywords,
                "location": action.location,
                "salary_min": action.salary_min,
                "job_type": action.job_type,
                "remote_only": action.remote_only
            }
        elif isinstance(action, AnalyzeJob):
            return {
                "type": "analyze_job",
                "job_id": action.job_id
            }
        elif isinstance(action, WriteCoverLetter):
            return {
                "type": "write_cover_letter",
                "job_id": action.job_id,
                "tone": action.tone,
                "highlight_skills": action.highlight_skills
            }
        elif isinstance(action, SubmitApplication):
            return {
                "type": "submit_application",
                "job_id": action.job_id,
                "cover_letter": action.cover_letter,
                "tailored_resume_sections": action.tailored_resume_sections
            }
        elif isinstance(action, NextJob):
            return {"type": "next_job"}
        else:
            raise ValueError(f"Unknown action type: {type(action)}")
    
    def _parse_observation(self, data: dict) -> JobAppObservation:
        """Parse server response into observation."""
        from models import JobPosting, JobAnalysis
        
        job_listings = [
            JobPosting(**job) for job in data.get("job_listings", [])
        ]
        
        current_job = None
        if data.get("current_job"):
            current_job = JobPosting(**data["current_job"])
        
        analysis_result = None
        if data.get("analysis_result"):
            analysis_result = JobAnalysis(**data["analysis_result"])
        
        return JobAppObservation(
            job_listings=job_listings,
            current_job=current_job,
            analysis_result=analysis_result,
            cover_letter=data.get("cover_letter"),
            cover_letter_quality=data.get("cover_letter_quality"),
            application_status=data.get("application_status"),
            budget_remaining=data.get("budget_remaining", 10),
            applications_count=data.get("applications_count", 0),
            message=data.get("message", ""),
            done=data.get("done", False),
            reward=data.get("reward", 0.0)
        )
    
    def _parse_state(self, data: dict) -> JobAppState:
        """Parse server response into state."""
        from models import JobPosting, ApplicantProfile, SubmittedApplication
        
        state = JobAppState(
            episode_id=data.get("episode_id", ""),
            step_count=data.get("step_count", 0),
            budget_remaining=data.get("budget_remaining", 10),
            total_reward=data.get("total_reward", 0.0)
        )
        
        if data.get("current_job"):
            state.current_job = JobPosting(**data["current_job"])
        
        if data.get("applicant_profile"):
            state.applicant_profile = ApplicantProfile(**data["applicant_profile"])
        
        state.applications_submitted = [
            SubmittedApplication(**app) 
            for app in data.get("applications_submitted", [])
        ]
        
        state.last_search_results = [
            JobPosting(**job) 
            for job in data.get("last_search_results", [])
        ]
        
        return state
