# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Service Incident Triage Environment Implementation.

A POMDP environment where an AI agent acts as an on-call engineer.
The agent is given partial logs/metrics and must inspect services to
identify the failing service, assign severity, and declare the root cause.
"""

import random
from typing import Optional
from uuid import uuid4

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

try:
    from ..data import Incident, get_incident_by_id, get_incidents_by_difficulty
    from ..models import ServiceIncidentAction, ServiceIncidentObservation
    from ..rubrics import ServiceIncidentGrader
    from ..tasks import TASKS
except ImportError:
    from data import Incident, get_incident_by_id, get_incidents_by_difficulty
    from models import ServiceIncidentAction, ServiceIncidentObservation
    from rubrics import ServiceIncidentGrader
    from tasks import TASKS


class ServiceIncidentEnvironment(Environment):
    """
    Service Incident Triage environment (POMDP).

    The agent starts with partial visibility (one service's log snippet)
    and must strategically inspect logs/metrics to identify the root cause
    service and its severity. The episode ends when the agent declares or
    when max_steps is reached.

    Reward structure:
      - Useful inspection (reveals anomaly): +0.1
      - Redundant inspection: -0.05
      - Correct service + severity: +1.0
      - Correct service only: +0.6
      - Wrong declaration: 0.0 with -0.3 penalty
      - Exceeding step budget: -0.2
    """

    SUPPORTS_CONCURRENT_SESSIONS: bool = True

    def __init__(self) -> None:
        """Initialize the environment."""
        super().__init__(rubric=ServiceIncidentGrader())
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self._incident: Optional[Incident] = None
        self._inspected_logs: set[str] = set()
        self._inspected_metrics: set[str] = set()
        self._max_steps: int = 6
        self._episode_done: bool = True
        self._cumulative_reward: float = 0.0
        self._task_id: str = "easy"
        self._visible_logs: dict[str, str] = {}
        self._visible_metrics: dict[str, dict[str, float]] = {}
        self._rng = random.Random(42)

    def reset(
        self,
        seed: Optional[int] = None,
        episode_id: Optional[str] = None,
        **kwargs,
    ) -> ServiceIncidentObservation:
        """
        Reset the environment and start a new incident episode.

        Kwargs:
            task_id: "easy", "medium", or "hard" (default: "easy")
            incident_id: specific incident ID to use (optional)
        """
        if seed is not None:
            self._rng = random.Random(seed)

        self._task_id = kwargs.get("task_id", "easy")
        if self._task_id not in TASKS:
            self._task_id = "easy"

        task = TASKS[self._task_id]
        self._max_steps = task.max_steps

        # Select incident
        requested_id = kwargs.get("incident_id")
        if requested_id:
            self._incident = get_incident_by_id(requested_id)
        else:
            incidents = get_incidents_by_difficulty(task.difficulty)
            self._incident = self._rng.choice(incidents)

        # Reset episode state
        eid = episode_id or str(uuid4())
        self._state = State(episode_id=eid, step_count=0)
        self._inspected_logs = set()
        self._inspected_metrics = set()
        self._episode_done = False
        self._cumulative_reward = 0.0

        # Initial partial visibility: one service's log snippet
        init_svc = self._incident.initial_visible_service
        self._visible_logs = {init_svc: self._incident.logs[init_svc]}
        self._visible_metrics = {}
        self._inspected_logs.add(init_svc)

        return ServiceIncidentObservation(
            visible_logs=dict(self._visible_logs),
            visible_metrics=dict(self._visible_metrics),
            services=list(self._incident.services),
            step_count=0,
            max_steps=self._max_steps,
            message=(
                f"Incident {self._incident.incident_id} reported. "
                f"Initial log from '{init_svc}' is visible. "
                f"Services involved: {', '.join(self._incident.services)}. "
                f"You have {self._max_steps} steps to investigate and declare."
            ),
            incident_id=self._incident.incident_id,
            done=False,
            reward=0.0,
            metadata={"task_id": self._task_id, "cumulative_reward": 0.0},
        )

    def step(
        self,
        action: ServiceIncidentAction,
        timeout_s: Optional[float] = None,
        **kwargs,
    ) -> ServiceIncidentObservation:
        """Execute one step in the environment."""
        if self._episode_done:
            return self._make_obs(
                message="Episode already ended. Call reset() to start a new episode.",
                reward=0.0,
                done=True,
            )

        if self._incident is None:
            return self._make_obs(
                message="No active incident. Call reset() first.",
                reward=0.0,
                done=True,
            )

        # Validate target service
        if action.target not in self._incident.services:
            return self._make_obs(
                message=(
                    f"Invalid target '{action.target}'. "
                    f"Valid services: {', '.join(self._incident.services)}"
                ),
                reward=-0.05,
                done=False,
                increment_step=True,
            )

        self._state.step_count += 1
        step_reward = 0.0
        message = ""

        if action.action == "inspect_logs":
            step_reward, message = self._handle_inspect_logs(action.target)
        elif action.action == "inspect_metrics":
            step_reward, message = self._handle_inspect_metrics(action.target)
        elif action.action == "declare":
            step_reward, message = self._handle_declare(action.target, action.severity)

        # Step budget penalty
        if not self._episode_done and self._state.step_count >= self._max_steps:
            step_reward += -0.2
            self._episode_done = True
            message += " Step budget exhausted — episode ended."

        self._cumulative_reward += step_reward

        return self._make_obs(
            message=message,
            reward=step_reward,
            done=self._episode_done,
        )

    def _handle_inspect_logs(self, target: str) -> tuple[float, str]:
        """Handle an inspect_logs action."""
        if target in self._inspected_logs:
            return -0.05, f"Logs for '{target}' were already inspected. Redundant action."

        self._inspected_logs.add(target)
        self._visible_logs[target] = self._incident.logs[target]

        if target in self._incident.anomaly_services_logs:
            return +0.1, f"Inspected logs for '{target}' — anomaly signals detected."
        return 0.0, f"Inspected logs for '{target}' — no anomalies found."

    def _handle_inspect_metrics(self, target: str) -> tuple[float, str]:
        """Handle an inspect_metrics action."""
        if target in self._inspected_metrics:
            return -0.05, f"Metrics for '{target}' were already inspected. Redundant action."

        self._inspected_metrics.add(target)
        self._visible_metrics[target] = self._incident.metrics[target]

        if target in self._incident.anomaly_services_metrics:
            return +0.1, f"Inspected metrics for '{target}' — anomaly signals detected."
        return 0.0, f"Inspected metrics for '{target}' — no anomalies found."

    def _handle_declare(self, target: str, severity: str) -> tuple[float, str]:
        """Handle a declare action. Ends the episode."""
        self._episode_done = True
        correct_service = target == self._incident.root_cause
        correct_severity = severity == self._incident.severity

        if correct_service and correct_severity:
            return +1.0, (
                f"CORRECT! Root cause: '{target}', severity: {severity}. "
                f"Incident resolved successfully."
            )
        elif correct_service:
            return +0.6, (
                f"Partially correct. Root cause '{target}' is right, but severity "
                f"should be {self._incident.severity}, not {severity}."
            )
        else:
            return -0.3, (
                f"INCORRECT. You declared '{target}' ({severity}), but the root "
                f"cause was '{self._incident.root_cause}' ({self._incident.severity})."
            )

    def _make_obs(
        self,
        message: str,
        reward: float,
        done: bool,
        increment_step: bool = False,
    ) -> ServiceIncidentObservation:
        """Build an observation from current state."""
        if increment_step:
            self._state.step_count += 1
            self._cumulative_reward += reward
            if self._state.step_count >= self._max_steps:
                self._episode_done = True
                done = True
                message += " Step budget exhausted — episode ended."

        meta: dict = {
            "task_id": self._task_id,
            "cumulative_reward": self._cumulative_reward,
        }
        # On terminal observations, include grader_score clamped to (0, 1) strictly
        if done:
            meta["grader_score"] = max(0.01, min(0.99, self._cumulative_reward))

        return ServiceIncidentObservation(
            visible_logs=dict(self._visible_logs),
            visible_metrics=dict(self._visible_metrics),
            services=list(self._incident.services) if self._incident else [],
            step_count=self._state.step_count,
            max_steps=self._max_steps,
            message=message,
            incident_id=self._incident.incident_id if self._incident else "",
            done=done,
            reward=reward,
            metadata=meta,
        )

    @property
    def state(self) -> State:
        """Get the current environment state."""
        return self._state
