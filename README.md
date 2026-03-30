---
title: Job Application Simulator
emoji: 📝
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
---

# Job Application Simulator

An **OpenEnv-compatible** simulation environment for training AI agents on strategic job application tasks.

## Overview

This environment simulates a job application process where an AI agent must:
- Search for relevant job listings
- View job details and assess match quality
- Submit applications with personalized cover letters
- Manage a limited budget
- Maximize total reward through strategic decisions

## OpenEnv Compliance ✅

This environment implements the full OpenEnv specification:

| Endpoint | Status | Description |
|----------|--------|-------------|
| `POST /reset` | ✅ | Initialize new episode |
| `POST /step` | ✅ | Execute action in environment |
| `GET /state` | ✅ | Get current environment state |
| `GET /tasks` | ✅ | List available tasks |
| `POST /tasks/{id}/grade` | ✅ | Grade task completion (0.0-1.0) |

## Tasks

### 1. Easy Apply (Easy)
Submit 3 job applications with match score > 0.5

### 2. Smart Searcher (Medium)
Find and apply to 3 best matching jobs (match > 0.7) within budget

### 3. Application Master (Hard)
Maximize total reward through strategic job selection and quality applications

## API Usage

### Reset Environment
```bash
curl -X POST https://uhthredb-job-application-simulator.hf.space/reset \
  -H "Content-Type: application/json" \
  -d '{"profile_name": "software_engineer"}'
```

### Search Jobs
```bash
curl -X POST https://uhthredb-job-application-simulator.hf.space/step \
  -H "Content-Type: application/json" \
  -d '{"episode_id": "ep_xxx", "action": "search_jobs"}'
```

### Apply to Job
```bash
curl -X POST https://uhthredb-job-application-simulator.hf.space/step \
  -H "Content-Type: application/json" \
  -d '{
    "episode_id": "ep_xxx",
    "action": "apply",
    "job_id": "job_1",
    "cover_letter": "I am interested in this position..."
  }'
```

### Grade Task
```bash
curl -X POST "https://uhthredb-job-application-simulator.hf.space/tasks/easy_apply/grade?episode_id=ep_xxx"
```

## Actions

| Action | Description | Cost |
|--------|-------------|------|
| `search_jobs` | Search for job listings | Free |
| `view_job` | View job details and match score | Free |
| `apply` | Submit job application | $5.00 |
| `check_status` | Check application status | Free |

## Running Locally

```bash
# Clone the space
git clone https://huggingface.co/spaces/UhthredB/job-application-simulator
cd job-application-simulator

# Install dependencies
pip install -r requirements.txt

# Run the server
python -m uvicorn server.main:app --reload --port 7860

# Run baseline inference
python inference.py
```

## Environment Variables

- `API_BASE_URL` - Base URL for API (default: HF Space URL)
- `MODEL_NAME` - OpenAI model name for agent decisions
- `HF_TOKEN` - Hugging Face token (optional, for private spaces)

## Files

- `server/main.py` - FastAPI application with OpenEnv endpoints
- `server/job_app_environment.py` - Environment logic and state management
- `mock_data/` - Mock job listings and applicant profiles
- `openenv.yaml` - OpenEnv specification
- `inference.py` - Baseline inference script

## License

MIT
