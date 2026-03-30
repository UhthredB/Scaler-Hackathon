"""Mock data for Job Application Simulator."""

import random
from typing import List, Dict, Any

# Sample applicant profiles
PROFILES = {
    "software_engineer": {
        "name": "Alex Developer",
        "skills": ["Python", "JavaScript", "React", "Node.js", "SQL", "Git"],
        "experience_years": 5,
        "education": "BS Computer Science",
        "current_role": "Mid-level Developer",
        "target_roles": ["Senior Developer", "Tech Lead"],
        "preferred_locations": ["Remote", "San Francisco", "New York"],
        "salary_min": 120000,
        "salary_max": 180000,
        "resume_sections": {
            "summary": "Experienced full-stack developer passionate about building scalable applications.",
            "highlights": "Led migration of monolith to microservices, mentored 3 junior developers."
        }
    },
    "data_scientist": {
        "name": "Sam Data",
        "skills": ["Python", "Machine Learning", "TensorFlow", "SQL", "Statistics", "R"],
        "experience_years": 3,
        "education": "MS Data Science",
        "current_role": "Data Analyst",
        "target_roles": ["Data Scientist", "ML Engineer"],
        "preferred_locations": ["New York", "Remote"],
        "salary_min": 130000,
        "salary_max": 170000,
        "resume_sections": {
            "summary": "Data professional transitioning to ML engineering.",
            "highlights": "Built prediction model that increased revenue by 15%."
        }
    },
    "product_manager": {
        "name": "Jordan PM",
        "skills": ["Product Strategy", "Agile", "User Research", "Analytics", "Roadmapping"],
        "experience_years": 4,
        "education": "MBA",
        "current_role": "Associate Product Manager",
        "target_roles": ["Product Manager", "Senior PM"],
        "preferred_locations": ["San Francisco", "Remote"],
        "salary_min": 140000,
        "salary_max": 200000,
        "resume_sections": {
            "summary": "Product manager with technical background and strong analytics skills.",
            "highlights": "Launched 3 products with 2M+ users, improved retention by 25%."
        }
    }
}

# Sample job listings
JOBS = [
    {
        "id": "job_001",
        "title": "Senior Python Developer",
        "company": "TechCorp",
        "location": "Remote",
        "type": "full-time",
        "salary_range": "$120k - $150k",
        "required_skills": ["Python", "Django", "PostgreSQL", "AWS"],
        "preferred_skills": ["Docker", "Kubernetes"],
        "description": "Build scalable backend services for our SaaS platform.",
        "experience_required": 5
    },
    {
        "id": "job_002",
        "title": "Full Stack Engineer",
        "company": "StartupXYZ",
        "location": "Remote",
        "type": "full-time",
        "salary_range": "$100k - $130k",
        "required_skills": ["JavaScript", "React", "Node.js", "MongoDB"],
        "preferred_skills": ["TypeScript", "GraphQL"],
        "description": "Join our fast-growing team building the future of X.",
        "experience_required": 3
    },
    {
        "id": "job_003",
        "title": "Machine Learning Engineer",
        "company": "AI Labs",
        "location": "San Francisco",
        "type": "full-time",
        "salary_range": "$150k - $180k",
        "required_skills": ["Python", "TensorFlow", "Machine Learning", "MLOps"],
        "preferred_skills": ["PyTorch", "Kubernetes"],
        "description": "Deploy ML models at scale for production systems.",
        "experience_required": 4
    },
    {
        "id": "job_004",
        "title": "Backend Developer",
        "company": "FinanceApp",
        "location": "New York",
        "type": "full-time",
        "salary_range": "$110k - $140k",
        "required_skills": ["Python", "FastAPI", "SQL", "Redis"],
        "preferred_skills": ["Go", "Microservices"],
        "description": "Build secure financial APIs.",
        "experience_required": 3
    },
    {
        "id": "job_005",
        "title": "DevOps Engineer",
        "company": "CloudCo",
        "location": "Remote",
        "type": "full-time",
        "salary_range": "$130k - $160k",
        "required_skills": ["AWS", "Docker", "Kubernetes", "CI/CD"],
        "preferred_skills": ["Terraform", "Python"],
        "description": "Manage cloud infrastructure and CI/CD pipelines.",
        "experience_required": 4
    },
    {
        "id": "job_006",
        "title": "Junior Software Developer",
        "company": "LocalTech",
        "location": "Chicago",
        "type": "full-time",
        "salary_range": "$70k - $90k",
        "required_skills": ["Python", "JavaScript", "SQL"],
        "preferred_skills": ["React", "Django"],
        "description": "Great opportunity for developers starting their career.",
        "experience_required": 1
    },
    {
        "id": "job_007",
        "title": "Data Engineer",
        "company": "DataDriven",
        "location": "Remote",
        "type": "full-time",
        "salary_range": "$120k - $150k",
        "required_skills": ["Python", "Spark", "SQL", "Airflow"],
        "preferred_skills": ["AWS", "Kafka"],
        "description": "Build and maintain data pipelines.",
        "experience_required": 3
    },
    {
        "id": "job_008",
        "title": "Product Manager",
        "company": "ProductCo",
        "location": "San Francisco",
        "type": "full-time",
        "salary_range": "$140k - $170k",
        "required_skills": ["Product Strategy", "Agile", "Analytics"],
        "preferred_skills": ["Technical background"],
        "description": "Lead product development for our core platform.",
        "experience_required": 5
    }
]


def get_jobs() -> List[Dict[str, Any]]:
    """Return all available jobs."""
    return JOBS


def get_job_by_id(job_id: str) -> Dict[str, Any]:
    """Get a specific job by ID."""
    for job in JOBS:
        if job["id"] == job_id:
            return job
    return None


def get_profile(name: str) -> Dict[str, Any]:
    """Get a specific profile."""
    return PROFILES.get(name)


def calculate_match_score(profile: Dict[str, Any], job: Dict[str, Any]) -> float:
    """Calculate how well a profile matches a job."""
    profile_skills = set(s.lower() for s in profile.get("skills", []))
    required_skills = set(s.lower() for s in job.get("required_skills", []))
    preferred_skills = set(s.lower() for s in job.get("preferred_skills", []))
    
    # Required skills match (60% weight)
    required_match = len(profile_skills & required_skills) / len(required_skills) if required_skills else 0
    
    # Preferred skills match (20% weight)
    preferred_match = len(profile_skills & preferred_skills) / len(preferred_skills) if preferred_skills else 0
    
    # Experience match (20% weight)
    exp_required = job.get("experience_required", 0)
    exp_actual = profile.get("experience_years", 0)
    exp_match = min(exp_actual / exp_required, 1.0) if exp_required > 0 else 1.0
    
    score = (required_match * 0.6) + (preferred_match * 0.2) + (exp_match * 0.2)
    return round(score, 2)
