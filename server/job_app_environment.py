"""
Job Application Simulator - Server-Side Environment Implementation

This module implements the core environment logic that runs on the server.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import asdict
import sys
import os

# Add parent directory to path for imports when running as module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import (
    JobPosting,
    ApplicantProfile,
    JobAnalysis,
    SubmittedApplication,
    JobAppState,
    JobAppObservation,
    SearchJobs,
    AnalyzeJob,
    WriteCoverLetter,
    SubmitApplication,
    NextJob,
)
from mock_data import get_jobs, get_profile


class JobAppEnvironment:
    """
    Core environment logic for Job Application Simulator.
    
    This class manages the episode state and processes actions.
    """
    
    def __init__(self, job_db: Optional[List[Dict]] = None):
        """
        Initialize environment with job database.
        
        Args:
            job_db: List of job dictionaries (uses mock data if not provided)
        """
        self.job_db = job_db or get_jobs()
        self.episodes: Dict[str, JobAppState] = {}
    
    def reset(
        self,
        profile_name: str = "software_engineer",
        budget: int = 10,
        difficulty: str = "normal"
    ) -> Dict[str, Any]:
        """
        Start a new episode.
        
        Args:
            profile_name: Name of applicant profile
            budget: Maximum applications allowed
            difficulty: 'easy', 'normal', or 'hard'
        
        Returns:
            Initial observation dict
        """
        episode_id = str(uuid.uuid4())[:8]
        
        # Load profile
        profile_data = get_profile(profile_name)
        applicant = ApplicantProfile(**profile_data)
        
        # Initialize state
        state = JobAppState(
            episode_id=episode_id,
            step_count=0,
            applicant_profile=applicant,
            budget_remaining=budget,
            applications_submitted=[],
            last_search_results=[],
            total_reward=0.0,
            current_job=None,
            last_analysis=None
        )
        
        self.episodes[episode_id] = state
        
        return self._make_observation(state, f"Episode started. Profile: {applicant.name}. Budget: {budget} applications.")
    
    def step(self, episode_id: str, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an action in the episode.
        
        Args:
            episode_id: Active episode ID
            action: Action dictionary with 'type' field
        
        Returns:
            Observation dict with reward and done flag
        """
        state = self.episodes.get(episode_id)
        if not state:
            return self._error_observation(f"Episode {episode_id} not found")
        
        action_type = action.get("type", "")
        state.step_count += 1
        
        # Route to appropriate handler
        if action_type == "search_jobs":
            return self._handle_search(state, action)
        elif action_type == "analyze_job":
            return self._handle_analyze(state, action)
        elif action_type == "write_cover_letter":
            return self._handle_write_letter(state, action)
        elif action_type == "submit_application":
            return self._handle_submit(state, action)
        elif action_type == "next_job":
            return self._handle_next_job(state, action)
        elif action_type == "state":
            return asdict(state)
        else:
            return self._error_observation(f"Unknown action type: {action_type}")
    
    # ========================================================================
    # ACTION HANDLERS
    # ========================================================================
    
    def _handle_search(self, state: JobAppState, action: Dict) -> Dict:
        """Handle SearchJobs action"""
        keywords = action.get("keywords", [])
        location = action.get("location")
        salary_min = action.get("salary_min")
        remote_only = action.get("remote_only", False)
        
        # Filter jobs
        results = []
        for job_data in self.job_db:
            job = JobPosting(**job_data)
            
            # Check keywords (search in title and description)
            if keywords:
                text = f"{job.title} {job.description}".lower()
                if not any(kw.lower() in text for kw in keywords):
                    continue
            
            # Check location
            if location and location.lower() not in job.location.lower():
                if not job.remote:
                    continue
            
            # Check salary
            if salary_min and job.salary_max < salary_min:
                continue
            
            # Check remote
            if remote_only and not job.remote:
                continue
            
            results.append(job)
        
        state.last_search_results = results
        
        reward = -0.1  # Cost of searching
        state.total_reward += reward
        
        message = f"Found {len(results)} jobs"
        if keywords:
            message += f" matching '{', '.join(keywords)}'"
        
        return self._make_observation(state, message, reward=reward)
    
    def _handle_analyze(self, state: JobAppState, action: Dict) -> Dict:
        """Handle AnalyzeJob action"""
        job_id = action.get("job_id")
        
        # Find the job
        job = self._find_job(state, job_id)
        if not job:
            return self._error_observation(f"Job {job_id} not found in current results")
        
        state.current_job = job
        
        # Analyze match
        applicant = state.applicant_profile
        matching_skills = []
        missing_skills = []
        
        for req in job.requirements:
            req_lower = req.lower()
            # Check if any applicant skill matches this requirement
            found = False
            for skill in applicant.skills:
                if skill.lower() in req_lower or req_lower in skill.lower():
                    matching_skills.append(req)
                    found = True
                    break
            if not found:
                # Check for partial matches (e.g., "Python" matches "5+ years Python")
                if any(skill.lower() in req_lower for skill in applicant.skills):
                    matching_skills.append(req)
                else:
                    missing_skills.append(req)
        
        # Calculate match score
        total_reqs = len(job.requirements)
        if total_reqs > 0:
            match_score = len(matching_skills) / total_reqs
        else:
            match_score = 1.0
        
        # Determine reward based on match quality
        if match_score >= 0.7:
            reward = 0.5
        elif match_score >= 0.5:
            reward = 0.1
        else:
            reward = -0.2
        
        state.total_reward += reward
        
        # Create analysis
        analysis = JobAnalysis(
            job_id=job_id,
            match_score=match_score,
            matching_skills=matching_skills,
            missing_skills=missing_skills,
            key_requirements=job.requirements[:3],
            recommended_focus=", ".join(matching_skills[:3]) if matching_skills else "Transferable skills"
        )
        
        state.last_analysis = analysis
        
        message = f"Match score: {match_score:.0%}. "
        if matching_skills:
            message += f"Strong in: {', '.join(matching_skills[:3])}. "
        if missing_skills:
            message += f"Missing: {', '.join(missing_skills[:2])}."
        
        return self._make_observation(state, message, reward=reward)
    
    def _handle_write_letter(self, state: JobAppState, action: Dict) -> Dict:
        """Handle WriteCoverLetter action"""
        job_id = action.get("job_id")
        tone = action.get("tone", "professional")
        highlight_skills = action.get("highlight_skills", [])
        
        job = self._find_job(state, job_id)
        if not job:
            return self._error_observation(f"Job {job_id} not found")
        
        applicant = state.applicant_profile
        
        # Generate cover letter (simplified - in real impl would use LLM)
        skills_to_highlight = highlight_skills if highlight_skills else applicant.skills[:3]
        
        cover_letter = self._generate_cover_letter(
            applicant=applicant,
            job=job,
            skills=skills_to_highlight,
            tone=tone
        )
        
        # Calculate quality (simplified heuristic)
        quality = self._evaluate_cover_letter(cover_letter, job, applicant)
        
        # Reward based on quality
        if quality >= 0.8:
            reward = 1.0
        elif quality >= 0.6:
            reward = 0.5
        else:
            reward = -0.5
        
        state.total_reward += reward
        
        message = f"Cover letter generated. Quality: {quality:.0%}"
        
        obs = self._make_observation(state, message, reward=reward)
        obs["cover_letter"] = cover_letter
        obs["cover_letter_quality"] = quality
        
        return obs
    
    def _handle_submit(self, state: JobAppState, action: Dict) -> Dict:
        """Handle SubmitApplication action"""
        job_id = action.get("job_id")
        cover_letter = action.get("cover_letter", "")
        tailored_sections = action.get("tailored_resume_sections", {})
        
        # Check budget
        if state.budget_remaining <= 0:
            return self._make_observation(
                state,
                "Application budget exhausted!",
                reward=-3.0,
                done=True
            )
        
        job = self._find_job(state, job_id)
        if not job:
            return self._error_observation(f"Job {job_id} not found")
        
        # Get or calculate match score
        if state.last_analysis and state.last_analysis.job_id == job_id:
            match_score = state.last_analysis.match_score
        else:
            match_score = self._quick_match(state.applicant_profile, job)
        
        # Deduct budget
        state.budget_remaining -= 1
        
        # Create application record
        application = SubmittedApplication(
            job_id=job_id,
            cover_letter=cover_letter,
            tailored_sections=tailored_sections,
            submission_time=datetime.now().isoformat(),
            match_score=match_score,
            status="pending"
        )
        state.applications_submitted.append(application)
        
        # Calculate reward
        if match_score >= 0.7:
            reward = 2.0
            # Simulate acceptance for good matches
            if match_score >= 0.8 and cover_letter:
                application.status = "accepted"
                reward += 3.0
                message = f"🎉 Application accepted! Great match ({match_score:.0%})"
            else:
                message = f"Application submitted. Match: {match_score:.0%}"
        elif match_score >= 0.5:
            reward = 0.5
            message = f"Application submitted. Decent match ({match_score:.0%})"
        else:
            reward = -1.0
            message = f"Application submitted but poor match ({match_score:.0%}). Consider targeting better fits."
        
        state.total_reward += reward
        
        # Check if budget exhausted
        done = state.budget_remaining <= 0
        
        obs = self._make_observation(state, message, reward=reward, done=done)
        obs["application_status"] = application.status
        
        return obs
    
    def _handle_next_job(self, state: JobAppState, action: Dict) -> Dict:
        """Handle NextJob action - cycle through search results"""
        if not state.last_search_results:
            return self._make_observation(state, "No search results. Use SearchJobs first.")
        
        # Find current job index
        if state.current_job:
            current_idx = next(
                (i for i, j in enumerate(state.last_search_results) if j.id == state.current_job.id),
                -1
            )
            next_idx = (current_idx + 1) % len(state.last_search_results)
        else:
            next_idx = 0
        
        state.current_job = state.last_search_results[next_idx]
        
        return self._make_observation(
            state,
            f"Viewing job {next_idx + 1} of {len(state.last_search_results)}: {state.current_job.title}"
        )
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    def _find_job(self, state: JobAppState, job_id: str) -> Optional[JobPosting]:
        """Find job by ID in search results or database"""
        # Check search results first
        for job in state.last_search_results:
            if job.id == job_id:
                return job
        
        # Fall back to full database
        for job_data in self.job_db:
            if job_data["id"] == job_id:
                return JobPosting(**job_data)
        
        return None
    
    def _quick_match(self, applicant: ApplicantProfile, job: JobPosting) -> float:
        """Quick match calculation"""
        matching = 0
        for req in job.requirements:
            if any(skill.lower() in req.lower() for skill in applicant.skills):
                matching += 1
        return matching / len(job.requirements) if job.requirements else 1.0
    
    def _generate_cover_letter(
        self,
        applicant: ApplicantProfile,
        job: JobPosting,
        skills: List[str],
        tone: str
    ) -> str:
        """Generate a simple cover letter (placeholder for LLM)"""
        tone_openers = {
            "professional": "I am writing to express my strong interest in",
            "friendly": "I'm excited to apply for",
            "technical": "I am applying for"
        }
        
        opener = tone_openers.get(tone, tone_openers["professional"])
        
        letter = f"""Dear Hiring Manager,

{opener} the {job.title} position at {job.company}.

With {applicant.experience_years} years of experience as a {applicant.current_role}, I bring expertise in {', '.join(skills[:3])}. My background includes {applicant.resume_sections.get('experience', 'relevant professional experience')}.

I am particularly drawn to {job.company}'s mission and believe my skills in {skills[0] if skills else 'software development'} would enable me to contribute meaningfully to your team.

Thank you for considering my application. I look forward to the opportunity to discuss how I can contribute to {job.company}.

Best regards,
{applicant.name}
"""
        return letter
    
    def _evaluate_cover_letter(
        self,
        letter: str,
        job: JobPosting,
        applicant: ApplicantProfile
    ) -> float:
        """Evaluate cover letter quality (simplified heuristic)"""
        score = 0.5  # Base score
        
        # Check for personalization
        if job.company in letter:
            score += 0.1
        if job.title in letter:
            score += 0.1
        
        # Check for skill mentions
        skills_mentioned = sum(1 for skill in applicant.skills if skill in letter)
        score += min(0.2, skills_mentioned * 0.05)
        
        # Check length (not too short, not too long)
        word_count = len(letter.split())
        if 150 <= word_count <= 300:
            score += 0.1
        
        return min(1.0, score)
    
    def _make_observation(
        self,
        state: JobAppState,
        message: str,
        reward: float = 0.0,
        done: bool = False
    ) -> Dict[str, Any]:
        """Create observation dictionary"""
        return {
            "episode_id": state.episode_id,
            "job_listings": [asdict(j) for j in state.last_search_results],
            "current_job": asdict(state.current_job) if state.current_job else None,
            "analysis_result": asdict(state.last_analysis) if state.last_analysis else None,
            "budget_remaining": state.budget_remaining,
            "applications_count": len(state.applications_submitted),
            "message": message,
            "done": done,
            "reward": reward,
            "total_reward": state.total_reward
        }
    
    def _error_observation(self, error: str) -> Dict[str, Any]:
        """Create error observation"""
        return {
            "job_listings": [],
            "current_job": None,
            "analysis_result": None,
            "budget_remaining": 0,
            "applications_count": 0,
            "message": f"Error: {error}",
            "done": False,
            "reward": 0.0
        }


# For testing
if __name__ == "__main__":
    env = JobAppEnvironment()
    
    # Test reset
    print("=== Testing Reset ===")
    obs = env.reset(profile_name="software_engineer", budget=5)
    print(f"Episode: {obs['episode_id']}")
    print(f"Message: {obs['message']}")
    
    episode_id = obs["episode_id"]
    
    # Test search
    print("\n=== Testing Search ===")
    obs = env.step(episode_id, {"type": "search_jobs", "keywords": ["python", "remote"]})
    print(f"Found {len(obs['job_listings'])} jobs")
    for job in obs['job_listings'][:3]:
        print(f"  - {job['title']} at {job['company']}")
    
    # Test analyze
    print("\n=== Testing Analyze ===")
    if obs['job_listings']:
        job_id = obs['job_listings'][0]['id']
        obs = env.step(episode_id, {"type": "analyze_job", "job_id": job_id})
        print(f"Match score: {obs.get('analysis_result', {}).get('match_score', 0):.0%}")
        print(f"Message: {obs['message']}")
    
    print("\n=== Done ===")
