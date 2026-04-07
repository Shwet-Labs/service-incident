# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Grader rubrics for the Service Incident Triage environment.

Each task has a programmatic grader that scores agent performance on a
0.0–1.0 scale. The grader normalizes the cumulative reward (which can
exceed [0, 1] due to intermediate bonuses/penalties) into the required
range.

Scoring breakdown:
  - Correct root cause + severity: base 1.0
  - Correct root cause only: base 0.6
  - Wrong root cause: base 0.0
  - Useful inspections add up to +0.1 each
  - Redundant inspections penalize -0.05 each
  - Step budget exceeded: -0.2
  - The raw cumulative is clamped to [0.0, 1.0]
"""

from typing import Any, Dict, List, Tuple

from openenv.core.rubrics.trajectory import TrajectoryRubric


# Strict bounds: scores must be in open interval (0, 1)
_EPS = 0.01


class ServiceIncidentGrader(TrajectoryRubric):
    """Trajectory-based grader for service incident triage episodes.

    Accumulates (action, observation) pairs over an episode and produces
    a final score in (0.0, 1.0) when the episode ends.

    The score is the cumulative reward clamped to (_EPS, 1-_EPS):
      - Perfect run (correct cause + severity + useful inspections) → ~0.99
      - Partial success (correct service, wrong severity) → 0.6–0.7
      - Wrong root cause → ~0.01
    """

    def __init__(self) -> None:
        super().__init__(intermediate_reward=0.0)

    def score_trajectory(self, trajectory: List[Tuple[Any, Any]]) -> float:
        """Score the complete episode trajectory.

        Extracts the cumulative reward from the final observation's metadata
        and clamps it to [0.0, 1.0].

        Args:
            trajectory: List of (action, observation) tuples.

        Returns:
            Grader score in [0.0, 1.0].
        """
        if not trajectory:
            return _EPS

        _, final_obs = trajectory[-1]

        # Extract cumulative reward from metadata
        metadata = getattr(final_obs, "metadata", {}) or {}
        cumulative = metadata.get("cumulative_reward", 0.0)

        # Clamp to strictly (0, 1)
        return max(_EPS, min(1.0 - _EPS, cumulative))

    def compute_step_rewards(self) -> List[float]:
        """Compute per-step rewards for credit assignment.

        Uses uniform credit assignment: each step gets an equal share
        of the final trajectory score.

        Returns:
            List of per-step rewards.
        """
        if not self._trajectory:
            return []

        final_score = self.score_trajectory(self._trajectory)
        n_steps = len(self._trajectory)
        return [final_score / n_steps] * n_steps
