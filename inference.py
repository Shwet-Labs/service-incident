"""
Inference Script — Service Incident Triage
===================================
MANDATORY
- Before submitting, ensure the following variables are defined in your environment configuration:
    API_BASE_URL   The API endpoint for the LLM.
    MODEL_NAME     The model identifier to use for inference.
    HF_TOKEN       Your Hugging Face / API key.
    API_KEY        OpenRouter API key (falls back to HF_TOKEN).
    ENV_URL        The URL of the running service incident environment server.

- Defaults are set only for API_BASE_URL and MODEL_NAME:
    API_BASE_URL = os.getenv("API_BASE_URL", "https://openrouter.ai/api/v1")
    MODEL_NAME   = os.getenv("MODEL_NAME", "anthropic/claude-sonnet-4")

- The inference script must be named `inference.py` and placed in the root directory of the project
- Participants must use OpenAI Client for all LLM calls using above variables

STDOUT FORMAT
- The script must emit exactly three line types to stdout, in this order:

    [START] task=<task_name> env=<benchmark> model=<model_name>
    [STEP]  step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
    [END]   success=<true|false> steps=<n> score=<score> rewards=<r1,r2,...,rn>

  Rules:
    - One [START] line at episode begin.
    - One [STEP] line per step, immediately after env.step() returns.
    - One [END] line after env.close(), always emitted (even on exception).
    - reward and rewards are formatted to 2 decimal places.
    - done and success are lowercase booleans: true or false.
    - error is the raw last_action_error string, or null if none.
    - All fields on a single line with no newlines within a line.
    - Each tasks should return score in [0, 1]

  Example:
    [START] task=easy env=service_incident model=anthropic/claude-sonnet-4
    [STEP] step=1 action=inspect_metrics(db) reward=0.10 done=false error=null
    [STEP] step=2 action=declare(db,P0) reward=1.00 done=true error=null
    [END] success=true steps=2 score=1.00 rewards=0.10,1.00
"""

import asyncio
import json
import os
import textwrap
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from openai import OpenAI

from client import ServiceIncidentEnv
from models import ServiceIncidentAction

load_dotenv()

API_KEY = os.getenv("API_KEY") or os.getenv("HF_TOKEN")
API_BASE_URL = os.getenv("API_BASE_URL", "https://openrouter.ai/api/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "anthropic/claude-sonnet-4")
ENV_URL = os.getenv("ENV_URL", "http://localhost:8000")
BENCHMARK = "service_incident"

# Task configs: task_id -> (max_steps, incident_ids)
TASK_CONFIGS = {
    "easy": {"max_steps": 3, "incident_ids": [f"easy_00{i}" for i in range(1, 6)]},
    "medium": {"max_steps": 5, "incident_ids": [f"med_00{i}" for i in range(1, 6)]},
    "hard": {"max_steps": 6, "incident_ids": [f"hard_00{i}" for i in range(1, 6)]},
}

TEMPERATURE = 0.2
MAX_TOKENS = 512

SYSTEM_PROMPT = textwrap.dedent("""\
You are an expert on-call engineer performing service incident triage.

You are given partial logs and metrics from a multi-service system experiencing an incident.
Your goal is to identify the root cause service and its severity (P0, P1, or P2) as efficiently as possible.

Available actions (respond with exactly one JSON object):
1. {"action": "inspect_logs", "target": "<service_name>"} — Reveal full logs for a service.
2. {"action": "inspect_metrics", "target": "<service_name>"} — Reveal latency, error_rate, cpu, memory for a service.
3. {"action": "declare", "target": "<service_name>", "severity": "<P0|P1|P2>"} — Declare root cause. Ends episode.

Strategy:
- You start with one service's logs already visible. Analyze them first.
- Inspect metrics or logs of suspicious services to narrow down the root cause.
- The root cause is the UPSTREAM service causing failures, not a downstream victim showing errors.
- Look for: connection pool exhaustion, disk I/O saturation, OOM kills, certificate errors, cluster failures.
- Downstream services will show timeouts/retries pointing to the real culprit.
- Severity guide: P0 = service completely down / data loss risk, P1 = major degradation, P2 = minor / non-critical.
- Be efficient — each inspection costs a step. Declare as soon as you have enough evidence.

IMPORTANT: Respond with ONLY a single JSON object. No explanation, no markdown, no extra text.""")


def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action_str: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(
        f"[STEP] step={step} action={action_str} reward={reward:.2f} done={done_val} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} score={score:.2f} rewards={rewards_str}",
        flush=True,
    )


def format_observation_for_llm(obs: Any) -> str:
    """Format the current observation into a prompt for the LLM."""
    parts = []

    parts.append(f"Incident: {obs.incident_id}")
    parts.append(f"Services involved: {', '.join(obs.services)}")
    parts.append(f"Step: {obs.step_count}/{obs.max_steps}")
    parts.append(f"Message: {obs.message}")

    if obs.visible_logs:
        parts.append("\n--- Visible Logs ---")
        for svc, log_text in obs.visible_logs.items():
            parts.append(f"\n[{svc}]:\n{log_text}")

    if obs.visible_metrics:
        parts.append("\n--- Visible Metrics ---")
        for svc, metrics in obs.visible_metrics.items():
            metrics_str = ", ".join(f"{k}={v}" for k, v in metrics.items())
            parts.append(f"[{svc}]: {metrics_str}")

    if not obs.visible_metrics:
        parts.append("\nNo metrics inspected yet.")

    remaining = obs.max_steps - obs.step_count
    parts.append(f"\nYou have {remaining} step(s) remaining. Choose your next action wisely.")
    if remaining == 1:
        parts.append("WARNING: This is your LAST step. You MUST declare now or the episode will end with a penalty.")

    return "\n".join(parts)


def parse_llm_action(response_text: str) -> Dict[str, str]:
    """Parse the LLM's JSON response into an action dict."""
    text = response_text.strip()

    # Strip markdown code fences if present
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()

    # Try to find JSON object in the response
    start = text.find("{")
    end = text.rfind("}") + 1
    if start != -1 and end > start:
        text = text[start:end]

    return json.loads(text)


def format_action_str(action_dict: Dict[str, str]) -> str:
    """Format action dict into a compact string for logging."""
    act = action_dict.get("action", "unknown")
    target = action_dict.get("target", "unknown")
    if act == "declare":
        severity = action_dict.get("severity", "?")
        return f"declare({target},{severity})"
    return f"{act}({target})"


def get_llm_action(
    client: OpenAI,
    messages: List[Dict[str, str]],
) -> Dict[str, str]:
    """Get the next action from the LLM."""
    completion = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
        stream=False,
    )
    response_text = (completion.choices[0].message.content or "").strip()
    return parse_llm_action(response_text), response_text


def run_episode(
    client: OpenAI,
    env: Any,
    task_id: str,
    incident_id: str,
    seed: int = 42,
) -> float:
    """Run a single episode and return the score in [0, 1]."""
    max_steps = TASK_CONFIGS[task_id]["max_steps"]
    task_name = f"{task_id}/{incident_id}"

    log_start(task=task_name, env=BENCHMARK, model=MODEL_NAME)

    rewards: List[float] = []
    steps_taken = 0
    score = 0.0
    success = False

    try:
        result = env.reset(task_id=task_id, incident_id=incident_id, seed=seed)
        obs = result.observation

        # Build conversation history
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
        ]

        for step in range(1, max_steps + 1):
            if obs.done:
                break

            # Build user message from current observation
            obs_text = format_observation_for_llm(obs)
            messages.append({"role": "user", "content": obs_text})

            # Get LLM action
            error = None
            try:
                action_dict, raw_response = get_llm_action(client, messages)
                messages.append({"role": "assistant", "content": raw_response})
            except Exception as e:
                # Fallback: on last step, try to declare based on what we know
                error = str(e)
                action_dict = _fallback_action(obs, step, max_steps)
                messages.append({"role": "assistant", "content": json.dumps(action_dict)})

            # Build the action
            try:
                action = ServiceIncidentAction(**action_dict)
            except Exception as e:
                error = str(e)
                action_dict = _fallback_action(obs, step, max_steps)
                action = ServiceIncidentAction(**action_dict)

            action_str = format_action_str(action_dict)

            # Step the environment
            result = env.step(action)
            obs = result.observation
            reward = result.reward or 0.0
            done = result.done

            rewards.append(reward)
            steps_taken = step

            log_step(step=step, action_str=action_str, reward=reward, done=done, error=error)

            if done:
                break

        # Use the server's authoritative cumulative_reward from metadata
        # (matches ServiceIncidentGrader.score_trajectory logic exactly)
        metadata = getattr(obs, "metadata", {}) or {}
        cumulative = metadata.get("cumulative_reward", sum(rewards))
        score = max(0.0, min(1.0, cumulative))
        success = score >= 0.5

    except Exception as e:
        print(f"[DEBUG] Episode error: {e}", flush=True)
        score = max(0.0, min(1.0, score))
    finally:
        score = max(0.0, min(1.0, score))
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

    return score


def _fallback_action(obs: Any, step: int, max_steps: int) -> Dict[str, str]:
    """Generate a fallback action when LLM response is unparseable."""
    remaining = max_steps - step + 1 if step <= max_steps else 0

    # On last step or if we've inspected things, just declare the first service
    if remaining <= 1:
        # Pick the most suspicious service based on visible data
        target = _guess_root_cause(obs)
        return {"action": "declare", "target": target, "severity": "P0"}

    # Otherwise inspect metrics/logs of an uninspected service
    inspected_logs = set(obs.visible_logs.keys())
    inspected_metrics = set(obs.visible_metrics.keys())
    for svc in obs.services:
        if svc not in inspected_metrics:
            return {"action": "inspect_metrics", "target": svc}
    for svc in obs.services:
        if svc not in inspected_logs:
            return {"action": "inspect_logs", "target": svc}

    target = _guess_root_cause(obs)
    return {"action": "declare", "target": target, "severity": "P0"}


def _guess_root_cause(obs: Any) -> str:
    """Heuristic guess at root cause from visible metrics."""
    if obs.visible_metrics:
        worst_svc = max(
            obs.visible_metrics.keys(),
            key=lambda s: obs.visible_metrics[s].get("error_rate", 0),
        )
        return worst_svc
    return obs.services[0]


def main() -> None:
    """Run inference across all tasks and incidents."""
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    env = ServiceIncidentEnv(base_url=ENV_URL).sync()

    all_scores: Dict[str, List[float]] = {}

    with env:
        for task_id in ["easy", "medium", "hard"]:
            task_scores = []
            for incident_id in TASK_CONFIGS[task_id]["incident_ids"]:
                score = run_episode(
                    client=client,
                    env=env,
                    task_id=task_id,
                    incident_id=incident_id,
                    seed=42,
                )
                task_scores.append(score)
            all_scores[task_id] = task_scores
            avg = sum(task_scores) / len(task_scores) if task_scores else 0
            print(f"\n[SUMMARY] task={task_id} avg_score={avg:.3f} scores={[f'{s:.2f}' for s in task_scores]}\n", flush=True)

    # Final summary
    print("\n" + "=" * 60, flush=True)
    print("FINAL RESULTS", flush=True)
    print("=" * 60, flush=True)
    total_scores = []
    for task_id, scores in all_scores.items():
        avg = sum(scores) / len(scores) if scores else 0
        total_scores.extend(scores)
        print(f"  {task_id:8s}: avg={avg:.3f}  ({len(scores)} episodes)", flush=True)
    overall = sum(total_scores) / len(total_scores) if total_scores else 0
    print(f"  {'overall':8s}: avg={overall:.3f}  ({len(total_scores)} episodes)", flush=True)
    print("=" * 60, flush=True)


if __name__ == "__main__":
    main()
