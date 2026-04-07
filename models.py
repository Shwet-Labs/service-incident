# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Data models for the Service Incident Triage Environment.

Actions: inspect_logs, inspect_metrics, or declare a root cause.
Observations: partially revealed logs/metrics with episode status.
"""

from typing import Dict, List, Literal, Optional

from openenv.core.env_server.types import Action, Observation
from pydantic import Field, model_validator


class ServiceIncidentAction(Action):
    """
    Action for the Service Incident Triage environment.

    Three possible actions:
      - inspect_logs: reveal the logs for a target service
      - inspect_metrics: reveal the metrics for a target service
      - declare: declare a root cause service and severity (ends episode)
    """

    action: Literal["inspect_logs", "inspect_metrics", "declare"] = Field(
        ..., description="The action type to perform"
    )
    target: str = Field(
        ..., description="Service name to inspect or declare as root cause"
    )
    severity: Optional[Literal["P0", "P1", "P2"]] = Field(
        default=None,
        description="Severity level — required when action is 'declare'",
    )

    @model_validator(mode="after")
    def _validate_severity_on_declare(self) -> "ServiceIncidentAction":
        if self.action == "declare" and self.severity is None:
            raise ValueError("severity is required when action is 'declare'")
        return self


class ServiceIncidentObservation(Observation):
    """
    Observation from the Service Incident Triage environment.

    Contains the currently visible (revealed) logs and metrics, the list of
    services in the incident, and episode progress information.
    """

    visible_logs: Dict[str, str] = Field(
        default_factory=dict,
        description="Revealed logs keyed by service name",
    )
    visible_metrics: Dict[str, Dict[str, float]] = Field(
        default_factory=dict,
        description="Revealed metrics keyed by service name",
    )
    services: List[str] = Field(
        default_factory=list,
        description="All service names involved in this incident",
    )
    step_count: int = Field(default=0, description="Current step number")
    max_steps: int = Field(default=6, description="Maximum steps before auto-end")
    message: str = Field(default="", description="Human-readable status message")
    incident_id: str = Field(default="", description="Current incident identifier")
