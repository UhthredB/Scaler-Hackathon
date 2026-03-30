#!/usr/bin/env python3
"""
Baseline inference script for Job Application Simulator.
Runs a simple agent that searches and applies to jobs strategically.

Usage:
    python inference.py

Environment variables:
    API_BASE_URL - Base URL of the deployed API (default: HF Space)
    MODEL_NAME - OpenAI model to use for agent decisions
"""
import os
import sys
import json
import time
import requests
from typing import Dict, Any, List

# Configuration
API_BASE = os.environ.get("API_BASE_URL", "https://uhthredb-job-application-simulator.hf.space")
MODEL_NAME = os.environ.get("MODEL_NAME", "gpt-4")
HF_TOKEN = os.environ.get("HF_TOKEN", "")

# Headers for requests
HEADERS = {"Content-Type": "application/json"}
if HF_TOKEN:
    HEADERS["Authorization"] = f"Bearer {HF_TOKEN}"


def api_call(method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
    """Make API call with error handling."""
    url = f"{API_BASE}{endpoint}"
    try:
        if method == "GET":
            resp = requests.get(url, headers=HEADERS, timeout=30, **kwargs)
        else:
            resp = requests.post(url, headers=HEADERS, timeout=30, **kwargs)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


def reset_environment() -> str:
    """Reset environment and return episode_id."""
    print("🔄 Resetting environment...")
    result = api_call("POST", "/reset", json={"profile_name": "software_engineer"})
    
    if "error" in result:
        print(f"❌ Reset failed: {result['error']}")
        sys.exit(1)
    
    episode_id = result.get("episode_id")
    print(f"✅ Episode started: {episode_id}")
    print(f"   Profile: {result.get('profile', {}).get('name', 'Unknown')}")
    print(f"   Budget: ${result.get('budget', 0):.2f}")
    return episode_id


def search_jobs(episode_id: str, query: str = "") -> List[Dict]:
    """Search for jobs."""
    result = api_call("POST", "/step", json={
        "episode_id": episode_id,
        "action": "search_jobs",
        "query": query
    })
    
    if "error" in result:
        print(f"   ⚠️ Search error: {result['error']}")
        return []
    
    jobs = result.get("jobs", [])
    print(f"   Found {len(jobs)} jobs")
    return jobs


def view_job(episode_id: str, job_id: str) -> Dict[str, Any]:
    """View job details and get match score."""
    result = api_call("POST", "/step", json={
        "episode_id": episode_id,
        "action": "view_job",
        "job_id": job_id
    })
    return result


def apply_to_job(episode_id: str, job_id: str, job_title: str, company: str) -> float:
    """Apply to a job with generated cover letter."""
    # Generate simple cover letter
    cover_letter = f"""Dear Hiring Manager at {company},

I am writing to express my strong interest in the {job_title} position. With my background in software development and passion for building impactful products, I believe I would be a valuable addition to your team.

I have experience with modern development practices and am excited about the opportunity to contribute to your company's mission. I am particularly drawn to this role because of the innovative work your team is doing.

Thank you for considering my application. I look forward to the opportunity to discuss how I can contribute to your team.

Best regards,
Candidate"""

    result = api_call("POST", "/step", json={
        "episode_id": episode_id,
        "action": "apply",
        "job_id": job_id,
        "cover_letter": cover_letter
    })
    
    if "error" in result:
        print(f"   ⚠️ Application error: {result['error']}")
        return 0.0
    
    reward = result.get("reward", 0)
    budget = result.get("budget_remaining", 0)
    print(f"   ✅ Applied! Reward: {reward:.2f}, Budget remaining: ${budget:.2f}")
    return reward


def run_baseline_agent():
    """Run baseline agent strategy."""
    print("\n" + "="*60)
    print("🎯 Job Application Simulator - Baseline Agent")
    print("="*60)
    print(f"API: {API_BASE}")
    print(f"Model: {MODEL_NAME}")
    print()
    
    # Reset environment
    episode_id = reset_environment()
    print()
    
    # Search for jobs
    print("🔍 Searching for jobs...")
    jobs = search_jobs(episode_id)
    
    if not jobs:
        print("❌ No jobs found. Exiting.")
        return {}
    print()
    
    # View each job to get match scores
    print("👀 Viewing job details...")
    job_scores = []
    for job in jobs[:5]:  # View top 5
        result = view_job(episode_id, job["id"])
        match_score = result.get("match_score", 0)
        job_scores.append({
            "id": job["id"],
            "title": job["title"],
            "company": job["company"],
            "match_score": match_score
        })
        print(f"   {job['title']} @ {job['company']}: match={match_score:.2f}")
    print()
    
    # Sort by match score and apply to top 3
    job_scores.sort(key=lambda x: x["match_score"], reverse=True)
    
    print("📝 Applying to top matched jobs...")
    total_reward = 0
    for job in job_scores[:3]:
        print(f"   Applying to: {job['title']} @ {job['company']} (match: {job['match_score']:.2f})")
        reward = apply_to_job(episode_id, job["id"], job["title"], job["company"])
        total_reward += reward
        time.sleep(0.5)  # Small delay between applications
    
    print()
    print(f"💰 Total reward earned: {total_reward:.2f}")
    print()
    
    # Get final state
    print("📊 Getting final state...")
    state = api_call("GET", f"/state?episode_id={episode_id}")
    
    if "error" not in state:
        print(f"   Steps taken: {state.get('step_count', 0)}")
        print(f"   Applications submitted: {len(state.get('applications_submitted', []))}")
        print(f"   Budget remaining: ${state.get('budget_remaining', 0):.2f}")
    print()
    
    # Grade all tasks
    print("🏆 Grading tasks...")
    scores = {}
    tasks = api_call("GET", "/tasks")
    
    for task in tasks.get("tasks", []):
        task_id = task["id"]
        result = api_call("POST", f"/tasks/{task_id}/grade", params={"episode_id": episode_id})
        scores[task_id] = result
        
        passed = "✅" if result.get("passed", False) else "❌"
        score = result.get("score", 0)
        details = result.get("details", "")
        print(f"   {passed} {task['name']}: {score:.2f} - {details}")
    
    print()
    print("="*60)
    print("📈 FINAL SCORES")
    print("="*60)
    for task_id, result in scores.items():
        print(f"   {task_id}: {result.get('score', 0):.2f}")
    print()
    
    return scores


if __name__ == "__main__":
    try:
        scores = run_baseline_agent()
        
        # Exit with error if any task failed
        all_passed = all(s.get("passed", False) for s in scores.values())
        sys.exit(0 if all_passed else 1)
        
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
