---
title: Service Incident Triage Environment
emoji: 🚨
colorFrom: purple
colorTo: red
sdk: docker
pinned: false
app_port: 7860
tags:
  - openenv
base_path: /web
---

# Service Incident Triage — OpenEnv Environment

An AI agent acts as an **on-call engineer** performing service incident triage.
Given partial logs and metrics from a multi-service system, the agent must
strategically inspect services, identify the root cause, and declare the
correct severity — all while minimizing unnecessary diagnostic steps.

> **Environment type:** POMDP (partially observable Markov decision process)
> **Episode length:** 3–6 steps depending on difficulty

---

## Motivation

Real incident response requires quickly narrowing down which service is failing
from noisy, incomplete signals. This environment captures that challenge:

- Partial observability — only one service's logs are visible at the start.
- Information-gathering actions cost steps.
- Misleading signals at higher difficulties.
- Shaped reward encourages efficient investigation.

---

## Action Space

Every action is a JSON object with three fields:

| Field      | Type   | Values | Description |
|------------|--------|--------|-------------|
| `action`   | string | `inspect_logs`, `inspect_metrics`, `declare` | What to do |
| `target`   | string | service name (e.g. `"db"`, `"auth"`) | Which service to act on |
| `severity` | string | `P0`, `P1`, `P2` | **Required** only for `declare` |

### Action semantics

| Action | Effect |
|--------|--------|
| `inspect_logs(target)` | Reveals the full log text for that service |
| `inspect_metrics(target)` | Reveals latency, error rate, CPU, memory for that service |
| `declare(target, severity)` | Ends the episode with a root-cause declaration |

---

## Observation Space

| Field | Type | Description |
|-------|------|-------------|
| `visible_logs` | `dict[str, str]` | Service → log text (only for inspected services) |
| `visible_metrics` | `dict[str, dict[str, float]]` | Service → `{latency_ms, error_rate, cpu_pct, memory_pct}` |
| `services` | `list[str]` | All services in the current incident |
| `step_count` | `int` | Steps taken so far |
| `max_steps` | `int` | Step budget for this task |
| `message` | `str` | Human-readable status after each action |
| `incident_id` | `str` | Current incident identifier |
| `done` | `bool` | Whether the episode has ended |
| `reward` | `float` | Reward for the latest step |

---

## Reward Function

### Intermediate rewards
| Signal | Reward |
|--------|--------|
| Useful inspection (reveals anomaly) | **+0.1** |
| Redundant / uninformative inspection | **−0.05** |

### Terminal rewards
| Outcome | Reward |
|---------|--------|
| Correct service **and** severity | **+1.0** |
| Correct service, wrong severity | **+0.6** |
| Wrong service | **0.0 − 0.3 penalty** |

### Penalties
| Condition | Penalty |
|-----------|---------|
| Exceeding step budget | **−0.2** |

---

## Tasks

| Task | Difficulty | Max Steps | Description |
|------|-----------|-----------|-------------|
| `easy` | 🟢 Easy | 3 | One service clearly spiking; obvious anomaly in logs and metrics |
| `medium` | 🟡 Medium | 5 | Multiple noisy signals; correlated failures across services |
| `hard` | 🔴 Hard | 6 | Misleading logs; hidden root cause; requires careful multi-service investigation |

Each task has **5 pre-generated incidents** (15 total) with deterministic seeding
for reproducible evaluation.

---

## Setup & Usage

### Prerequisites

```bash
pip install openenv-core[core]>=0.2.2
```

### Start the server locally

```bash
cd service_incident
uvicorn server.app:app --host 0.0.0.0 --port 7860
```

### Run with Docker

```bash
cd service_incident
docker build -f server/Dockerfile -t service-incident-env .
docker run -p 7860:7860 service-incident-env
```

### Interact via HTTP

```bash
# Reset with a task
curl -X POST http://localhost:7860/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": "easy", "seed": 42}'

# Step — inspect logs
curl -X POST http://localhost:7860/step \
  -H "Content-Type: application/json" \
  -d '{"action": "inspect_logs", "target": "db"}'

# Step — declare
curl -X POST http://localhost:7860/step \
  -H "Content-Type: application/json" \
  -d '{"action": "declare", "target": "db", "severity": "P0"}'

# Get state
curl http://localhost:7860/state
```

### Deploy to Hugging Face Spaces

```bash
openenv push service_incident --space-id your-username/service-incident-triage
```

### Run the baseline inference

```bash
export API_BASE_URL="https://api.openai.com/v1"
export MODEL_NAME="gpt-4o-mini"
export HF_TOKEN="your-api-key"
export ENV_URL="http://localhost:7860"

python inference.py
```

---

## Baseline Scores

| Task | Average Score |
|------|--------------|
| easy | *(run inference.py to fill)* |
| medium | *(run inference.py to fill)* |
| hard | *(run inference.py to fill)* |

---

## Project Structure

```
service_incident/
├── __init__.py                 # Package exports
├── client.py                   # WebSocket client (EnvClient subclass)
├── data.py                     # Pre-generated incident dataset (15 incidents)
├── models.py                   # Action & Observation Pydantic models
├── openenv.yaml                # OpenEnv spec metadata
├── pyproject.toml              # Python project configuration
├── tasks.py                    # Task definitions (easy / medium / hard)
├── README.md                   # This file
└── server/
    ├── __init__.py
    ├── app.py                  # FastAPI application (create_app)
    ├── Dockerfile              # Container build
    ├── requirements.txt        # Server dependencies
    └── service_incident_environment.py  # Core POMDP environment logic
```
