"""Job Application Simulator - Data Models"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict


# Stub base classes (openenv package doesn't exist)
@dataclass
class Action:
    """Base class for actions"""
    pass


@dataclass
class Observation:
    """Base class for observations"""
    pass


@dataclass
class State:
    """Base class for environment state"""
    pass


# ============================================================================
# DOMAIN MODELS
# ============================================================================

@dataclass
class JobPosting:
    """A job listing from the mock job board"""
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


@dataclass
class ApplicantProfile:
    """The job seeker's profile and preferences"""
    name: str
    skills: List[str]
    experience_years: int
    education: str
    current_role: str
    target_roles: List[str]
    preferred_locations: List[str]
    salary_min: int
    salary_max: int
    resume_sections: Dict[str, str] = field(default_factory=dict)


@dataclass
class JobAnalysis:
    """Result of analyzing a job posting"""
    job_id: str
    match_score: float  # 0.0 to 1.0
    matching_skills: List[str]
    missing_skills: List[str]
    key_requirements: List[str]
    recommended_focus: str  # What to highlight in application


@dataclass
class SubmittedApplication:
    """Record of a submitted application"""
    job_id: str
    cover_letter: str
    tailored_sections: Dict[str, str]
    submission_time: str
    match_score: float
    status: str = "pending"  # pending, accepted, rejected


# ============================================================================
# ENVIRONMENT STATE
# ============================================================================

@dataclass
class JobAppState(State):
    """Episode state for Job Application Simulator"""
    episode_id: str = ""
    step_count: int = 0
    current_job: Optional[JobPosting] = None
    applicant_profile: Optional[ApplicantProfile] = None
    applications_submitted: List[SubmittedApplication] = field(default_factory=list)
    budget_remaining: int = 10  # Max applications per episode
    last_search_results: List[JobPosting] = field(default_factory=list)
    last_analysis: Optional[JobAnalysis] = None
    total_reward: float = 0.0


# ============================================================================
# ACTIONS
# ============================================================================

@dataclass
class SearchJobs(Action):
    """Search for jobs matching criteria"""
    keywords: List[str] = field(default_factory=list)
    location: Optional[str] = None
    salary_min: Optional[int] = None
    job_type: Optional[str] = None  # full-time, contract, part-time
    remote_only: bool = False


@dataclass
class AnalyzeJob(Action):
    """Analyze a job posting for fit"""
    job_id: str = ""


@dataclass
class WriteCoverLetter(Action):
    """Generate a tailored cover letter"""
    job_id: str = ""
    tone: str = "professional"  # professional, friendly, technical
    highlight_skills: List[str] = field(default_factory=list)


@dataclass
class SubmitApplication(Action):
    """Submit application to a job"""
    job_id: str = ""
    cover_letter: str = ""
    tailored_resume_sections: Dict[str, str] = field(default_factory=dict)


@dataclass
class NextJob(Action):
    """Move to the next job in search results"""
    pass


# ============================================================================
# OBSERVATIONS
# ============================================================================

@dataclass
class JobAppObservation(Observation):
    """Observation returned after each action"""
    job_listings: List[JobPosting] = field(default_factory=list)
    current_job: Optional[JobPosting] = None
    analysis_result: Optional[JobAnalysis] = None
    cover_letter: Optional[str] = None
    cover_letter_quality: Optional[float] = None  # 0.0 to 1.0
    application_status: Optional[str] = None
    budget_remaining: int = 10
    applications_count: int = 0
    message: str = ""
    done: bool = False
    reward: float = 0.0


# ============================================================================
# STEP RESULT
# ============================================================================

@dataclass
class StepResult:
    """Result of executing an action"""
    observation: JobAppObservation
    reward: float
    done: bool
    info: Dict = field(default_factory=dict)
