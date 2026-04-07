# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""Service Incident Triage Environment Client."""

from typing import Dict

from openenv.core import EnvClient
from openenv.core.client_types import StepResult
from openenv.core.env_server.types import State

from models import ServiceIncidentAction, ServiceIncidentObservation


class ServiceIncidentEnv(
    EnvClient[ServiceIncidentAction, ServiceIncidentObservation, State]
):
    """
    Client for the Service Incident Triage Environment.

    This client maintains a persistent WebSocket connection to the environment
    server, enabling efficient multi-step interactions with lower latency.

    Example:
        >>> async with ServiceIncidentEnv(base_url="http://localhost:8000") as client:
        ...     result = await client.reset(task_id="easy")
        ...     print(result.observation.services)
        ...     print(result.observation.visible_logs)
        ...
        ...     result = await client.step(
        ...         ServiceIncidentAction(action="inspect_metrics", target="db")
        ...     )
        ...     print(result.observation.visible_metrics)
        ...
        ...     result = await client.step(
        ...         ServiceIncidentAction(action="declare", target="db", severity="P0")
        ...     )
        ...     print(result.reward, result.done)
    """

    def _step_payload(self, action: ServiceIncidentAction) -> Dict:
        """Convert ServiceIncidentAction to JSON payload for step message."""
        payload = {
            "action": action.action,
            "target": action.target,
        }
        if action.severity is not None:
            payload["severity"] = action.severity
        return payload

    def _parse_result(self, payload: Dict) -> StepResult[ServiceIncidentObservation]:
        """Parse server response into StepResult[ServiceIncidentObservation]."""
        obs_data = payload.get("observation", {})
        observation = ServiceIncidentObservation(
            visible_logs=obs_data.get("visible_logs", {}),
            visible_metrics=obs_data.get("visible_metrics", {}),
            services=obs_data.get("services", []),
            step_count=obs_data.get("step_count", 0),
            max_steps=obs_data.get("max_steps", 6),
            message=obs_data.get("message", ""),
            incident_id=obs_data.get("incident_id", ""),
            done=payload.get("done", False),
            reward=payload.get("reward"),
            metadata=obs_data.get("metadata", {}),
        )

        return StepResult(
            observation=observation,
            reward=payload.get("reward"),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: Dict) -> State:
        """Parse server response into State object."""
        return State(
            episode_id=payload.get("episode_id"),
            step_count=payload.get("step_count", 0),
        )
