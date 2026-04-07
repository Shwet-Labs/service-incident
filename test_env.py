"""
Test script for the Service Incident Triage environment.

Requires the server to be running:
    cd service_incident
    python -m uvicorn server.app:app --host 127.0.0.1 --port 8000
"""

from client import ServiceIncidentEnv
from models import ServiceIncidentAction

SERVER_URL = "http://127.0.0.1:8000"


def test_easy_episode():
    """Full easy episode: reset → inspect → declare correctly."""
    print("=" * 50)
    print("TEST 1: Easy episode — correct declaration")
    print("=" * 50)

    env = ServiceIncidentEnv(base_url=SERVER_URL).sync()
    with env:
        result = env.reset(task_id="easy", seed=42)
        obs = result.observation
        print(f"  Incident: {obs.incident_id}")
        print(f"  Services: {obs.services}")
        print(f"  Initial logs visible: {list(obs.visible_logs.keys())}")
        print(f"  Message: {obs.message}")
        assert not obs.done
        assert obs.step_count == 0

        # Step 1: inspect metrics for db
        result = env.step(ServiceIncidentAction(action="inspect_metrics", target="db"))
        obs = result.observation
        print(f"  Step 1: reward={result.reward} — {obs.message}")
        assert "db" in obs.visible_metrics
        assert result.reward == 0.1  # db has anomaly metrics

        # Step 2: declare db as root cause with P0
        result = env.step(ServiceIncidentAction(action="declare", target="db", severity="P0"))
        obs = result.observation
        print(f"  Step 2: reward={result.reward} — {obs.message}")
        assert result.done
        assert result.reward == 1.0  # correct service + severity

    print("  PASSED\n")


def test_wrong_declaration():
    """Declare the wrong service — should get penalty."""
    print("=" * 50)
    print("TEST 2: Wrong declaration")
    print("=" * 50)

    env = ServiceIncidentEnv(base_url=SERVER_URL).sync()
    with env:
        result = env.reset(task_id="easy", seed=42)
        obs = result.observation
        print(f"  Incident: {obs.incident_id}, Services: {obs.services}")

        # Declare wrong service immediately
        result = env.step(ServiceIncidentAction(action="declare", target="auth", severity="P1"))
        obs = result.observation
        print(f"  Wrong declare: reward={result.reward} — {obs.message}")
        assert result.done
        assert result.reward == -0.3  # wrong service penalty

    print("  PASSED\n")


def test_correct_service_wrong_severity():
    """Correct service but wrong severity — partial credit."""
    print("=" * 50)
    print("TEST 3: Correct service, wrong severity")
    print("=" * 50)

    env = ServiceIncidentEnv(base_url=SERVER_URL).sync()
    with env:
        result = env.reset(task_id="easy", seed=42)
        obs = result.observation
        print(f"  Incident: {obs.incident_id} (root_cause=db, severity=P0)")

        result = env.step(ServiceIncidentAction(action="declare", target="db", severity="P2"))
        obs = result.observation
        print(f"  Partial: reward={result.reward} — {obs.message}")
        assert result.done
        assert result.reward == 0.6  # correct service, wrong severity

    print("  PASSED\n")


def test_redundant_inspection():
    """Re-inspecting already-seen logs should give negative reward."""
    print("=" * 50)
    print("TEST 4: Redundant inspection penalty")
    print("=" * 50)

    env = ServiceIncidentEnv(base_url=SERVER_URL).sync()
    with env:
        result = env.reset(task_id="medium", seed=1)
        obs = result.observation
        initial_svc = list(obs.visible_logs.keys())[0]
        print(f"  Incident: {obs.incident_id}, initial log: {initial_svc}")

        # Re-inspect the already visible service's logs
        result = env.step(ServiceIncidentAction(action="inspect_logs", target=initial_svc))
        obs = result.observation
        print(f"  Redundant: reward={result.reward} — {obs.message}")
        assert result.reward == -0.05

    print("  PASSED\n")


def test_step_budget_exhaustion():
    """Exceed max_steps — should auto-end with penalty."""
    print("=" * 50)
    print("TEST 5: Step budget exhaustion")
    print("=" * 50)

    env = ServiceIncidentEnv(base_url=SERVER_URL).sync()
    with env:
        result = env.reset(task_id="easy", seed=42)
        obs = result.observation
        print(f"  Incident: {obs.incident_id}, max_steps={obs.max_steps}")

        services = obs.services
        # Use all 3 steps on inspections without declaring
        for i in range(3):
            svc = services[i % len(services)]
            result = env.step(ServiceIncidentAction(action="inspect_metrics", target=svc))
            obs = result.observation
            print(f"  Step {i+1}: reward={result.reward}, done={result.done} — {obs.message}")

        assert result.done, "Episode should have ended at max_steps"

    print("  PASSED\n")


def test_medium_episode():
    """Medium difficulty episode with multiple inspections."""
    print("=" * 50)
    print("TEST 6: Medium episode — multi-step investigation")
    print("=" * 50)

    env = ServiceIncidentEnv(base_url=SERVER_URL).sync()
    with env:
        result = env.reset(task_id="medium", seed=0)
        obs = result.observation
        print(f"  Incident: {obs.incident_id}")
        print(f"  Services: {obs.services}")
        print(f"  Max steps: {obs.max_steps}")

        # Inspect all services' metrics
        for svc in obs.services:
            result = env.step(ServiceIncidentAction(action="inspect_metrics", target=svc))
            print(f"  Inspect metrics({svc}): reward={result.reward}")

        # Find the service with highest latency from visible metrics
        latest_obs = result.observation
        best_svc = max(
            latest_obs.visible_metrics.keys(),
            key=lambda s: latest_obs.visible_metrics[s]["latency_ms"],
        )

        result = env.step(
            ServiceIncidentAction(action="declare", target=best_svc, severity="P0")
        )
        print(f"  Declare {best_svc}/P0: reward={result.reward} — {result.observation.message}")
        assert result.done

    print("  PASSED\n")


def test_hard_episode():
    """Hard difficulty episode."""
    print("=" * 50)
    print("TEST 7: Hard episode — misleading signals")
    print("=" * 50)

    env = ServiceIncidentEnv(base_url=SERVER_URL).sync()
    with env:
        result = env.reset(task_id="hard", seed=0)
        obs = result.observation
        print(f"  Incident: {obs.incident_id}")
        print(f"  Services: {obs.services}")
        print(f"  Initial logs: {list(obs.visible_logs.keys())}")
        print(f"  Max steps: {obs.max_steps}")

        # Inspect everything
        for svc in obs.services:
            result = env.step(ServiceIncidentAction(action="inspect_logs", target=svc))
            print(f"  Logs({svc}): reward={result.reward}")
            if result.done:
                break

        if not result.done:
            for svc in obs.services:
                result = env.step(ServiceIncidentAction(action="inspect_metrics", target=svc))
                print(f"  Metrics({svc}): reward={result.reward}")
                if result.done:
                    break

        if not result.done:
            result = env.step(
                ServiceIncidentAction(action="declare", target=obs.services[0], severity="P0")
            )
            print(f"  Declare: reward={result.reward} — {result.observation.message}")

        assert result.done

    print("  PASSED\n")


def test_state_endpoint():
    """Test the state() method."""
    print("=" * 50)
    print("TEST 8: State endpoint")
    print("=" * 50)

    env = ServiceIncidentEnv(base_url=SERVER_URL).sync()
    with env:
        env.reset(task_id="easy", seed=42)
        state = env.state()
        print(f"  After reset: episode_id={state.episode_id}, step_count={state.step_count}")
        assert state.step_count == 0

        env.step(ServiceIncidentAction(action="inspect_logs", target="db"))
        state = env.state()
        print(f"  After step:  episode_id={state.episode_id}, step_count={state.step_count}")
        assert state.step_count == 1

    print("  PASSED\n")


if __name__ == "__main__":
    test_easy_episode()
    test_wrong_declaration()
    test_correct_service_wrong_severity()
    test_redundant_inspection()
    test_step_budget_exhaustion()
    test_medium_episode()
    test_hard_episode()
    test_state_endpoint()

    print("=" * 50)
    print("ALL TESTS PASSED!")
    print("=" * 50)
