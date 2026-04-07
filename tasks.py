# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Task definitions for the Service Incident Triage environment.

Three difficulty levels, each with its own incident pool and step budget.
"""

from typing import Dict, List

from pydantic import BaseModel, Field

try:
    from .data import get_incidents_by_difficulty
except ImportError:
    from data import get_incidents_by_difficulty


class Task(BaseModel):
    """A single evaluation task."""

    task_id: str
    description: str
    difficulty: str
    incident_ids: List[str] = Field(description="IDs of incidents in this task's pool")
    max_steps: int = Field(description="Maximum steps before episode auto-ends")


def build_tasks() -> Dict[str, Task]:
    """Build and return the three task definitions."""
    easy_incidents = get_incidents_by_difficulty("easy")
    medium_incidents = get_incidents_by_difficulty("medium")
    hard_incidents = get_incidents_by_difficulty("hard")

    return {
        "easy": Task(
            task_id="easy",
            description=(
                "Easy incident triage: one service is clearly failing with obvious "
                "anomalies in logs and metrics. The agent should identify the root "
                "cause and severity with minimal inspections (1-2 steps)."
            ),
            difficulty="easy",
            incident_ids=[inc.incident_id for inc in easy_incidents],
            max_steps=3,
        ),
        "medium": Task(
            task_id="medium",
            description=(
                "Medium incident triage: multiple services show elevated signals. "
                "Noisy logs and correlated failures require 2-3 inspections to "
                "disambiguate the true root cause from downstream effects."
            ),
            difficulty="medium",
            incident_ids=[inc.incident_id for inc in medium_incidents],
            max_steps=5,
        ),
        "hard": Task(
            task_id="hard",
            description=(
                "Hard incident triage: misleading logs and ambiguous metrics. "
                "The real root cause may report healthy logs while other services "
                "show loud errors as downstream effects. Requires careful, "
                "systematic investigation across multiple services."
            ),
            difficulty="hard",
            incident_ids=[inc.incident_id for inc in hard_incidents],
            max_steps=6,
        ),
    }


TASKS = build_tasks()
