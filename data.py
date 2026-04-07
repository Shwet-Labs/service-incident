# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Pre-generated incident dataset for the Service Incident Triage environment.

All incidents are statically defined — no runtime simulation.
Each incident has pre-tagged anomalies, logs, and metrics across 3 difficulty levels.
"""

from typing import Dict, List, Literal

from pydantic import BaseModel, Field


class Incident(BaseModel):
    """A single pre-generated service incident."""

    incident_id: str
    services: List[str] = Field(description="Services involved in this incident")
    root_cause: str = Field(description="The service that is the actual root cause")
    severity: Literal["P0", "P1", "P2"] = Field(description="Ground-truth severity")
    logs: Dict[str, str] = Field(description="Full logs per service (hidden until inspected)")
    metrics: Dict[str, Dict[str, float]] = Field(
        description="Full metrics per service (hidden until inspected)"
    )
    difficulty: Literal["easy", "medium", "hard"]
    initial_visible_service: str = Field(
        description="Service whose log snippet is visible at episode start"
    )
    anomaly_services_logs: List[str] = Field(
        description="Services whose logs contain anomaly signals"
    )
    anomaly_services_metrics: List[str] = Field(
        description="Services whose metrics contain anomaly signals"
    )


# ---------------------------------------------------------------------------
# Pre-generated incidents
# ---------------------------------------------------------------------------

INCIDENTS: List[Incident] = [
    # -----------------------------------------------------------------------
    # EASY (5 incidents) — one service clearly spiking, obvious root cause
    # -----------------------------------------------------------------------
    Incident(
        incident_id="easy_001",
        services=["auth", "payments", "db"],
        root_cause="db",
        severity="P0",
        logs={
            "auth": (
                "2026-03-29T14:02:11.042Z auth-svc-7b8d replica-1 [INFO] "
                "GET /login 200 82ms uid=a]3f01\n"
                "2026-03-29T14:02:11.318Z auth-svc-7b8d replica-1 [INFO] "
                "POST /token/refresh 200 91ms uid=7ec42\n"
                "2026-03-29T14:02:12.005Z auth-svc-7b8d replica-2 [INFO] "
                "GET /login 200 79ms uid=d9b17\n"
                "2026-03-29T14:02:12.440Z auth-svc-7b8d replica-1 [INFO] "
                "health_check status=ok latency=4ms"
            ),
            "payments": (
                "2026-03-29T14:02:10.819Z payments-svc-3a1c worker-2 [INFO] "
                "POST /charge 200 115ms txn=txn_8f2e1 amount=49.99\n"
                "2026-03-29T14:02:11.203Z payments-svc-3a1c worker-1 [INFO] "
                "POST /charge 200 108ms txn=txn_9c3a7 amount=12.00\n"
                "2026-03-29T14:02:11.992Z payments-svc-3a1c worker-2 [INFO] "
                "throughput=12.3 req/s p99=120ms queue_depth=0\n"
                "2026-03-29T14:02:12.341Z payments-svc-3a1c worker-1 [INFO] "
                "health_check status=ok latency=6ms"
            ),
            "db": (
                "2026-03-29T14:02:10.002Z postgres-primary db01 [WARNING] "
                "connection pool usage 95/100 slots — approaching limit\n"
                "2026-03-29T14:02:10.487Z postgres-primary db01 [ERROR] "
                "PID 4821: connection timeout after 30012ms client=payments-svc "
                "query=\"SELECT * FROM transactions WHERE status='pending'\"\n"
                "2026-03-29T14:02:10.891Z postgres-primary db01 [CRITICAL] "
                "connection pool EXHAUSTED max=100 active=100 waiting=847 "
                "oldest_wait=28.4s\n"
                "2026-03-29T14:02:11.102Z postgres-primary db01 [CRITICAL] "
                "disk I/O saturated iops=15000/15000 await=245ms util=100%% "
                "device=/dev/sda1\n"
                "2026-03-29T14:02:11.503Z postgres-replica-3 db03 [CRITICAL] "
                "kernel: Out of memory: Killed process 2819 (postgres) "
                "total-vm:8241532kB anon-rss:7891204kB — OOM score 892\n"
                "2026-03-29T14:02:11.884Z postgres-primary db01 [ERROR] "
                "replication lag replica-3=UNREACHABLE replica-2=4.2s "
                "wal_sender_state=streaming"
            ),
        },
        metrics={
            "auth": {"latency_ms": 85, "error_rate": 0.01, "cpu_pct": 22, "memory_pct": 45},
            "payments": {"latency_ms": 120, "error_rate": 0.02, "cpu_pct": 35, "memory_pct": 55},
            "db": {"latency_ms": 5200, "error_rate": 0.78, "cpu_pct": 99, "memory_pct": 97},
        },
        difficulty="easy",
        initial_visible_service="auth",
        anomaly_services_logs=["db"],
        anomaly_services_metrics=["db"],
    ),
    Incident(
        incident_id="easy_002",
        services=["gateway", "cache", "notifications"],
        root_cause="cache",
        severity="P1",
        logs={
            "gateway": (
                "2026-03-29T09:15:01.112Z nginx-gw gw-01 [info] "
                "upstream_response_time=0.042s status=200 request=\"GET /api/v2/users\"\n"
                "2026-03-29T09:15:01.887Z nginx-gw gw-01 [info] "
                "connections_active=312 connections_idle=88 req/s=502\n"
                "2026-03-29T09:15:02.340Z nginx-gw gw-02 [info] "
                "upstream_response_time=0.038s status=200 request=\"POST /api/v2/orders\"\n"
                "2026-03-29T09:15:03.001Z nginx-gw gw-01 [info] "
                "health_check upstream=auth-svc status=healthy latency=12ms"
            ),
            "cache": (
                "2026-03-29T09:15:00.882Z redis-sentinel sentinel-1 [WARNING] "
                "+sdown master mymaster 10.0.3.22 6379\n"
                "2026-03-29T09:15:01.003Z redis-node-2 redis [ERROR] "
                "CLUSTERDOWN The cluster is down — node 10.0.3.22:6379 "
                "marked as FAIL by 3/5 sentinels\n"
                "2026-03-29T09:15:01.421Z redis-sentinel sentinel-2 [WARNING] "
                "+failover-state-select-slave master mymaster 10.0.3.22 6379\n"
                "2026-03-29T09:15:02.104Z redis-sentinel sentinel-1 [ERROR] "
                "-failover-abort-no-good-slave master mymaster 10.0.3.22 6379 — "
                "failover STALLED no eligible replica\n"
                "2026-03-29T09:15:02.887Z cache-proxy proxy-01 [ERROR] "
                "cache_miss_rate=0.95 eviction_count=48201 oom_policy=allkeys-lru "
                "used_memory=15.8GB maxmemory=16GB\n"
                "2026-03-29T09:15:03.201Z cache-proxy proxy-01 [ERROR] "
                "reconnect_attempt=14 target=10.0.3.22:6379 error=\"connection refused\""
            ),
            "notifications": (
                "2026-03-29T09:15:01.002Z notif-svc worker-1 [INFO] "
                "queue_depth=0 processed=0 status=idle\n"
                "2026-03-29T09:15:02.110Z notif-svc worker-1 [INFO] "
                "health_check status=ok smtp_conn=alive sqs_depth=0\n"
                "2026-03-29T09:15:03.004Z notif-svc worker-1 [INFO] "
                "heartbeat ts=1711700103 uptime=48201s"
            ),
        },
        metrics={
            "gateway": {"latency_ms": 45, "error_rate": 0.005, "cpu_pct": 18, "memory_pct": 30},
            "cache": {"latency_ms": 3800, "error_rate": 0.65, "cpu_pct": 88, "memory_pct": 95},
            "notifications": {"latency_ms": 30, "error_rate": 0.0, "cpu_pct": 5, "memory_pct": 15},
        },
        difficulty="easy",
        initial_visible_service="gateway",
        anomaly_services_logs=["cache"],
        anomaly_services_metrics=["cache"],
    ),
    Incident(
        incident_id="easy_003",
        services=["auth", "gateway", "notifications"],
        root_cause="auth",
        severity="P0",
        logs={
            "auth": (
                "2026-03-29T11:30:00.510Z auth-svc-7b8d replica-1 [ERROR] "
                "LDAP bind failed host=ldap01.corp.internal:636 error=\"connection timed out\" "
                "attempt=1/3\n"
                "2026-03-29T11:30:01.220Z auth-svc-7b8d replica-2 [ERROR] "
                "LDAP bind failed host=ldap02.corp.internal:636 error=\"connection refused\" "
                "attempt=3/3\n"
                "2026-03-29T11:30:01.891Z auth-svc-7b8d replica-1 [CRITICAL] "
                "ALL LDAP backends UNREACHABLE — authentication pipeline BLOCKED "
                "queued_requests=5012 circuit_breaker=OPEN\n"
                "2026-03-29T11:30:02.405Z auth-svc-7b8d replica-1 [ERROR] "
                "krb5_renew_ticket: KDC unreachable realm=CORP.INTERNAL "
                "error=KRB5KRB_AP_ERR_SKEW\n"
                "2026-03-29T11:30:03.008Z auth-svc-7b8d replica-2 [CRITICAL] "
                "POST /login 503 0ms — all upstream auth backends offline "
                "rejected=5000 last_success=182s_ago"
            ),
            "gateway": (
                "2026-03-29T11:30:01.003Z nginx-gw gw-01 [info] "
                "upstream_response_time=0.051s status=200 request=\"GET /health\"\n"
                "2026-03-29T11:30:01.892Z nginx-gw gw-02 [info] "
                "connections_active=145 req/s=301 upstream_errors=0\n"
                "2026-03-29T11:30:02.710Z nginx-gw gw-01 [info] "
                "health_check all_upstreams=healthy latency_avg=48ms"
            ),
            "notifications": (
                "2026-03-29T11:30:00.889Z notif-svc worker-1 [INFO] "
                "dispatched=42 delivered=42 failed=0 queue_depth=0\n"
                "2026-03-29T11:30:01.904Z notif-svc worker-2 [INFO] "
                "email batch_id=em_8a2f sent=42 bounced=0\n"
                "2026-03-29T11:30:02.812Z notif-svc worker-1 [INFO] "
                "health_check status=ok"
            ),
        },
        metrics={
            "auth": {"latency_ms": 8500, "error_rate": 0.92, "cpu_pct": 75, "memory_pct": 80},
            "gateway": {"latency_ms": 55, "error_rate": 0.01, "cpu_pct": 20, "memory_pct": 35},
            "notifications": {"latency_ms": 25, "error_rate": 0.0, "cpu_pct": 8, "memory_pct": 20},
        },
        difficulty="easy",
        initial_visible_service="notifications",
        anomaly_services_logs=["auth"],
        anomaly_services_metrics=["auth"],
    ),
    Incident(
        incident_id="easy_004",
        services=["payments", "cache", "db"],
        root_cause="payments",
        severity="P1",
        logs={
            "payments": (
                "2026-03-29T16:45:00.201Z payments-svc-3a1c worker-1 [ERROR] "
                "POST /webhooks/stripe 502 12042ms error=\"upstream connect error\" "
                "webhook_id=evt_1NqX8z2eZvKYlo\n"
                "2026-03-29T16:45:01.108Z payments-svc-3a1c worker-2 [ERROR] "
                "ssl_handshake_failed host=api.stripe.com:443 "
                "error=\"certificate has expired\" not_after=2026-03-28T23:59:59Z\n"
                "2026-03-29T16:45:01.892Z payments-svc-3a1c worker-1 [ERROR] "
                "retry_queue overflow max=500 current=1203 "
                "oldest_retry=2026-03-29T16:32:00Z dropped=48\n"
                "2026-03-29T16:45:02.410Z payments-svc-3a1c worker-3 [CRITICAL] "
                "payment processing HALTED — PSP gateway unreachable "
                "stuck_transactions=1200 revenue_impact=$58,420"
            ),
            "cache": (
                "2026-03-29T16:45:00.550Z redis-node-1 redis [INFO] "
                "keyspace hits=1842201 misses=152003 hit_rate=0.924\n"
                "2026-03-29T16:45:01.320Z redis-node-2 redis [INFO] "
                "connected_clients=84 used_memory_human=4.2GB maxmemory=8GB\n"
                "2026-03-29T16:45:02.001Z cache-proxy proxy-01 [INFO] "
                "health_check all_nodes=healthy latency_avg=2ms"
            ),
            "db": (
                "2026-03-29T16:45:00.120Z postgres-primary db01 [INFO] "
                "checkpoint starting: time\n"
                "2026-03-29T16:45:01.034Z postgres-primary db01 [INFO] "
                "replication lag replica-1=0.2s replica-2=0.1s within_sla=true\n"
                "2026-03-29T16:45:02.205Z postgres-primary db01 [INFO] "
                "active_connections=42/100 query_p99=38ms"
            ),
        },
        metrics={
            "payments": {"latency_ms": 4100, "error_rate": 0.71, "cpu_pct": 60, "memory_pct": 70},
            "cache": {"latency_ms": 12, "error_rate": 0.0, "cpu_pct": 15, "memory_pct": 50},
            "db": {"latency_ms": 45, "error_rate": 0.01, "cpu_pct": 30, "memory_pct": 40},
        },
        difficulty="easy",
        initial_visible_service="cache",
        anomaly_services_logs=["payments"],
        anomaly_services_metrics=["payments"],
    ),
    Incident(
        incident_id="easy_005",
        services=["gateway", "auth", "db"],
        root_cause="gateway",
        severity="P0",
        logs={
            "gateway": (
                "2026-03-29T08:00:00.112Z nginx-gw gw-01 [emerg] "
                "4012#0: worker process 4015 exited on signal 11 (core dumped)\n"
                "2026-03-29T08:00:00.518Z nginx-gw gw-01 [emerg] "
                "4012#0: worker process 4016 exited on signal 11 (core dumped)\n"
                "2026-03-29T08:00:01.003Z nginx-gw gw-01 [crit] "
                "connect() to 10.0.1.50:8080 failed (111: Connection refused) "
                "upstream=\"http://backend-pool\"\n"
                "2026-03-29T08:00:01.440Z alb-health health-checker [ERROR] "
                "target=gw-01:80 status=UNHEALTHY consecutive_failures=5 "
                "last_status=503\n"
                "2026-03-29T08:00:01.892Z nginx-gw gw-02 [error] "
                "503 rate=100%% upstream_attempts=0 no_live_upstreams=true"
            ),
            "auth": (
                "2026-03-29T08:00:00.305Z auth-svc-7b8d replica-1 [INFO] "
                "POST /token/validate 200 68ms uid=c2e91\n"
                "2026-03-29T08:00:01.120Z auth-svc-7b8d replica-2 [INFO] "
                "JWT validation pipeline ok signing_key=current ttl=3600s\n"
                "2026-03-29T08:00:01.880Z auth-svc-7b8d replica-1 [INFO] "
                "health_check status=ok latency=5ms"
            ),
            "db": (
                "2026-03-29T08:00:00.091Z postgres-primary db01 [INFO] "
                "LOG: checkpoint complete: wrote 1204 buffers (7.3%%)\n"
                "2026-03-29T08:00:01.002Z postgres-primary db01 [INFO] "
                "active_connections=31/100 query_p99=32ms\n"
                "2026-03-29T08:00:01.750Z postgres-primary db01 [INFO] "
                "autovacuum launcher started"
            ),
        },
        metrics={
            "gateway": {"latency_ms": 12000, "error_rate": 0.99, "cpu_pct": 5, "memory_pct": 10},
            "auth": {"latency_ms": 70, "error_rate": 0.01, "cpu_pct": 25, "memory_pct": 40},
            "db": {"latency_ms": 35, "error_rate": 0.005, "cpu_pct": 28, "memory_pct": 42},
        },
        difficulty="easy",
        initial_visible_service="db",
        anomaly_services_logs=["gateway"],
        anomaly_services_metrics=["gateway"],
    ),
    # -----------------------------------------------------------------------
    # MEDIUM (5 incidents) — multiple noisy signals, correlated failures
    # -----------------------------------------------------------------------
    Incident(
        incident_id="med_001",
        services=["auth", "payments", "db"],
        root_cause="db",
        severity="P0",
        logs={
            "auth": (
                "2026-03-29T13:10:00.410Z auth-svc-7b8d replica-1 [WARNING] "
                "GET /login 200 412ms uid=f8e21 — latency above SLO (200ms)\n"
                "2026-03-29T13:10:01.120Z auth-svc-7b8d replica-2 [WARNING] "
                "user_profile_lookup timeout upstream=user-svc after 5000ms "
                "retry=1/3\n"
                "2026-03-29T13:10:01.890Z auth-svc-7b8d replica-1 [WARNING] "
                "user_profile_lookup succeeded after retry=3 total_time=8420ms "
                "uid=f8e21\n"
                "2026-03-29T13:10:02.550Z auth-svc-7b8d replica-2 [INFO] "
                "token_validation ok but upstream dependency slow p99=450ms"
            ),
            "payments": (
                "2026-03-29T13:10:00.305Z payments-svc-3a1c worker-1 [WARNING] "
                "SELECT transaction_history timeout after 5000ms "
                "query_id=q_8f21a db_host=db01\n"
                "2026-03-29T13:10:01.008Z payments-svc-3a1c worker-2 [WARNING] "
                "db query retry succeeded attempt=2 latency=3200ms "
                "query_id=q_8f21a\n"
                "2026-03-29T13:10:01.702Z payments-svc-3a1c worker-1 [WARNING] "
                "fallback_to_cache partial_data=true txn_count=142/500 "
                "cache_hit=true\n"
                "2026-03-29T13:10:02.410Z payments-svc-3a1c worker-3 [INFO] "
                "processing delayed p99=800ms normal_p99=120ms"
            ),
            "db": (
                "2026-03-29T13:10:00.102Z postgres-primary db01 [ERROR] "
                "replication lag replica-1=10.4s replica-2=8.7s "
                "exceeds threshold (5s)\n"
                "2026-03-29T13:10:00.518Z postgres-primary db01 [ERROR] "
                "WAL sender backlog: 2.4GB pending segments "
                "wal_write_rate=48MB/s flush_rate=12MB/s\n"
                "2026-03-29T13:10:01.003Z postgres-primary db01 [WARNING] "
                "connection pool saturation 98/100 active "
                "oldest_idle=0ms wait_queue=24\n"
                "2026-03-29T13:10:01.512Z postgres-primary db01 [ERROR] "
                "disk IOPS throttled by cloud provider "
                "provisioned=3000 current=2998 throttle_count=847 "
                "await_ms=82\n"
                "2026-03-29T13:10:02.001Z postgres-primary db01 [WARNING] "
                "slow_query duration=3201ms query=\"SELECT * FROM transactions "
                "WHERE user_id=$1 ORDER BY created_at DESC LIMIT 100\""
            ),
        },
        metrics={
            "auth": {"latency_ms": 450, "error_rate": 0.12, "cpu_pct": 40, "memory_pct": 55},
            "payments": {"latency_ms": 800, "error_rate": 0.18, "cpu_pct": 45, "memory_pct": 60},
            "db": {"latency_ms": 3200, "error_rate": 0.45, "cpu_pct": 92, "memory_pct": 88},
        },
        difficulty="medium",
        initial_visible_service="auth",
        anomaly_services_logs=["auth", "payments", "db"],
        anomaly_services_metrics=["payments", "db"],
    ),
    Incident(
        incident_id="med_002",
        services=["gateway", "cache", "payments"],
        root_cause="cache",
        severity="P1",
        logs={
            "gateway": (
                "2026-03-29T10:20:00.110Z nginx-gw gw-01 [error] "
                "504 Gateway Timeout upstream=cache-svc "
                "request=\"GET /api/checkout/session\" response_time=5.002s\n"
                "2026-03-29T10:20:00.890Z nginx-gw gw-02 [warning] "
                "retry storm detected on /api/checkout — 3x normal "
                "retry_rate client_retries=412/s\n"
                "2026-03-29T10:20:01.403Z nginx-gw gw-01 [error] "
                "504 Gateway Timeout upstream=cache-svc "
                "request=\"GET /api/checkout/cart\" response_time=5.001s\n"
                "2026-03-29T10:20:02.001Z nginx-gw gw-01 [warning] "
                "upstream_5xx_rate=0.15 circuit_breaker=half-open"
            ),
            "cache": (
                "2026-03-29T10:20:00.002Z redis-sentinel sentinel-1 [WARNING] "
                "+sdown master mymaster 10.0.3.22 6379\n"
                "2026-03-29T10:20:00.503Z redis-sentinel sentinel-2 [WARNING] "
                "+odown master mymaster 10.0.3.22 6379 #quorum 3/5\n"
                "2026-03-29T10:20:01.008Z redis-sentinel sentinel-1 [ERROR] "
                "+failover-state-select-slave master mymaster — "
                "election in progress epoch=42\n"
                "2026-03-29T10:20:01.510Z redis-node-3 redis [ERROR] "
                "READONLY You can't write against a read only replica — "
                "partial data loss shard-3 keys_lost=1204\n"
                "2026-03-29T10:20:02.003Z cache-proxy proxy-01 [ERROR] "
                "client reconnection errors=248 target=10.0.3.22:6379 "
                "pool_active=2/50 pool_failed=48"
            ),
            "payments": (
                "2026-03-29T10:20:00.405Z payments-svc-3a1c worker-1 [WARNING] "
                "session data retrieval slow cache_miss=true "
                "fallback=db latency=480ms session_id=sess_8f2a\n"
                "2026-03-29T10:20:01.210Z payments-svc-3a1c worker-2 [WARNING] "
                "checkout latency elevated p99=500ms normal_p99=80ms "
                "cache_misses increasing miss_rate=0.62\n"
                "2026-03-29T10:20:02.018Z payments-svc-3a1c worker-1 [INFO] "
                "fallback to DB for session reads active sessions_from_db=312"
            ),
        },
        metrics={
            "gateway": {"latency_ms": 600, "error_rate": 0.15, "cpu_pct": 50, "memory_pct": 45},
            "cache": {"latency_ms": 2800, "error_rate": 0.52, "cpu_pct": 70, "memory_pct": 92},
            "payments": {"latency_ms": 500, "error_rate": 0.10, "cpu_pct": 38, "memory_pct": 50},
        },
        difficulty="medium",
        initial_visible_service="gateway",
        anomaly_services_logs=["gateway", "cache", "payments"],
        anomaly_services_metrics=["cache"],
    ),
    Incident(
        incident_id="med_003",
        services=["auth", "notifications", "db"],
        root_cause="auth",
        severity="P1",
        logs={
            "auth": (
                "2026-03-29T15:05:00.201Z auth-svc-7b8d replica-1 [ERROR] "
                "POST /oauth2/token 429 from idp.okta.com — rate limited "
                "retry_after=30s bucket=org_a1b2c3\n"
                "2026-03-29T15:05:01.003Z auth-svc-7b8d replica-2 [ERROR] "
                "token refresh failure uid=e4f21 error=\"upstream_rate_limited\" "
                "session invalidated — forced re-auth\n"
                "2026-03-29T15:05:01.810Z auth-svc-7b8d replica-1 [ERROR] "
                "cascading session invalidation batch_size=340 reason=token_expiry "
                "idp_rate_limit=true\n"
                "2026-03-29T15:05:02.502Z auth-svc-7b8d replica-2 [WARNING] "
                "login success rate=0.40 (normal=0.98) active_sessions "
                "dropping uid_affected=~2100"
            ),
            "notifications": (
                "2026-03-29T15:05:00.408Z notif-svc worker-1 [WARNING] "
                "API token validation failed upstream=auth-svc "
                "POST /dispatch 401 notif_id=n_8f2e\n"
                "2026-03-29T15:05:01.215Z notif-svc worker-2 [WARNING] "
                "email delivery delayed queue_depth=502 "
                "reason=auth_token_invalid retry_in=30s\n"
                "2026-03-29T15:05:02.003Z notif-svc worker-1 [INFO] "
                "partial dispatch ok channel=sms count=12 "
                "channel=email blocked=true"
            ),
            "db": (
                "2026-03-29T15:05:00.102Z postgres-primary db01 [INFO] "
                "query_p99=72ms active_connections=38/100 within_sla=true\n"
                "2026-03-29T15:05:01.008Z postgres-primary db01 [INFO] "
                "read queries uptick "
                "session_revalidation_queries=+180/s normal=40/s\n"
                "2026-03-29T15:05:01.892Z postgres-primary db01 [INFO] "
                "autovacuum running on sessions table rows_removed=0"
            ),
        },
        metrics={
            "auth": {"latency_ms": 2200, "error_rate": 0.60, "cpu_pct": 65, "memory_pct": 70},
            "notifications": {"latency_ms": 350, "error_rate": 0.08, "cpu_pct": 25, "memory_pct": 35},
            "db": {"latency_ms": 80, "error_rate": 0.02, "cpu_pct": 35, "memory_pct": 48},
        },
        difficulty="medium",
        initial_visible_service="notifications",
        anomaly_services_logs=["auth", "notifications"],
        anomaly_services_metrics=["auth"],
    ),
    Incident(
        incident_id="med_004",
        services=["gateway", "auth", "cache"],
        root_cause="gateway",
        severity="P0",
        logs={
            "gateway": (
                "2026-03-29T07:30:00.102Z nginx-gw gw-01 [error] "
                "SSL_do_handshake() failed: certificate verify error "
                "depth=1 err=\"unable to get local issuer certificate\" "
                "client=10.0.5.42\n"
                "2026-03-29T07:30:00.810Z nginx-gw gw-02 [error] "
                "502 Bad Gateway — WAF rule 942100 matched "
                "request=\"POST /api/auth/callback\" client=10.0.5.88 "
                "false_positive=likely\n"
                "2026-03-29T07:30:01.403Z nginx-gw gw-01 [crit] "
                "connection reset by peer during health probe "
                "upstream=10.0.1.50:8080 consecutive=3\n"
                "2026-03-29T07:30:02.001Z nginx-gw gw-01 [error] "
                "TLS cert chain mismatch on 50%% of requests "
                "cn=*.api.example.com issuer=R3 expiry=valid "
                "intermediate=MISSING"
            ),
            "auth": (
                "2026-03-29T07:30:00.405Z auth-svc-7b8d replica-1 [WARNING] "
                "POST /oauth2/callback received 503 from gateway "
                "retry=1/3 timeout=5000ms\n"
                "2026-03-29T07:30:01.203Z auth-svc-7b8d replica-2 [WARNING] "
                "truncated token payload received from gateway "
                "expected_len=1842 actual_len=924 oauth_state=st_8f2e\n"
                "2026-03-29T07:30:02.008Z auth-svc-7b8d replica-1 [WARNING] "
                "retry succeeded attempt=3 latency=2100ms "
                "callback_id=cb_a1b2c3"
            ),
            "cache": (
                "2026-03-29T07:30:00.510Z cache-proxy proxy-01 [WARNING] "
                "invalidation event out of order seq=4821 "
                "expected=4819 delta=2 source=auth-svc\n"
                "2026-03-29T07:30:01.312Z cache-proxy proxy-01 [WARNING] "
                "stale session data served uid_count=~200 "
                "ttl_override=true max_age=30s\n"
                "2026-03-29T07:30:02.003Z redis-node-1 redis [INFO] "
                "keyspace hits=842102 misses=21004 hit_rate=0.976"
            ),
        },
        metrics={
            "gateway": {"latency_ms": 1800, "error_rate": 0.48, "cpu_pct": 78, "memory_pct": 60},
            "auth": {"latency_ms": 400, "error_rate": 0.15, "cpu_pct": 35, "memory_pct": 45},
            "cache": {"latency_ms": 150, "error_rate": 0.05, "cpu_pct": 20, "memory_pct": 55},
        },
        difficulty="medium",
        initial_visible_service="cache",
        anomaly_services_logs=["gateway", "auth", "cache"],
        anomaly_services_metrics=["gateway"],
    ),
    Incident(
        incident_id="med_005",
        services=["payments", "notifications", "db"],
        root_cause="payments",
        severity="P1",
        logs={
            "payments": (
                "2026-03-29T18:00:00.201Z payments-svc-3a1c worker-1 [ERROR] "
                "webhook deserialization failed source=stripe "
                "error=\"invalid JSON: unexpected token at pos 842\" "
                "webhook_id=evt_3Nq8z\n"
                "2026-03-29T18:00:01.008Z payments-svc-3a1c worker-2 [ERROR] "
                "webhook deserialization failed source=stripe "
                "error=\"missing required field: payment_intent\" "
                "webhook_id=evt_4Pq9a failure_rate=0.60\n"
                "2026-03-29T18:00:01.810Z payments-svc-3a1c worker-1 [ERROR] "
                "DLQ enqueue txn_id=txn_8f2e1 reason=deserialization_failure "
                "dlq_depth=340 dlq_capacity=500 manual_reconciliation=required\n"
                "2026-03-29T18:00:02.503Z payments-svc-3a1c worker-3 [WARNING] "
                "callback_failure_rate=0.60 healthy_callbacks=0.40 "
                "source=stripe api_version=2025-12-01"
            ),
            "notifications": (
                "2026-03-29T18:00:00.405Z notif-svc worker-1 [WARNING] "
                "payment confirmation email template render failed "
                "field=transaction_amount value=null notif_id=n_2f8a\n"
                "2026-03-29T18:00:01.210Z notif-svc worker-2 [WARNING] "
                "upstream payments API partial response "
                "GET /transactions/txn_8f2e1 — missing fields: "
                "[amount, currency, status]\n"
                "2026-03-29T18:00:02.003Z notif-svc worker-1 [INFO] "
                "delayed queue_depth=180 retry_after=60s"
            ),
            "db": (
                "2026-03-29T18:00:00.102Z postgres-primary db01 [INFO] "
                "transaction_table writes=142/s within_normal_range=true\n"
                "2026-03-29T18:00:01.003Z postgres-primary db01 [INFO] "
                "REINDEX TABLE idx_transactions_created_at completed "
                "duration=0.48s\n"
                "2026-03-29T18:00:01.810Z postgres-primary db01 [INFO] "
                "checkpoint_delay=0.5s within_tolerance=true "
                "wal_size=128MB"
            ),
        },
        metrics={
            "payments": {"latency_ms": 1500, "error_rate": 0.38, "cpu_pct": 55, "memory_pct": 65},
            "notifications": {"latency_ms": 280, "error_rate": 0.12, "cpu_pct": 30, "memory_pct": 40},
            "db": {"latency_ms": 60, "error_rate": 0.01, "cpu_pct": 32, "memory_pct": 50},
        },
        difficulty="medium",
        initial_visible_service="db",
        anomaly_services_logs=["payments", "notifications"],
        anomaly_services_metrics=["payments"],
    ),
    # -----------------------------------------------------------------------
    # HARD (5 incidents) — misleading logs, hidden root cause, ambiguous metrics
    # -----------------------------------------------------------------------
    Incident(
        incident_id="hard_001",
        services=["auth", "payments", "db"],
        root_cause="db",
        severity="P0",
        logs={
            "auth": (
                "2026-03-29T12:00:00.102Z auth-svc-7b8d replica-1 [ERROR] "
                "LDAP query timeout after 5000ms host=ldap01.corp.internal "
                "query=\"(&(uid=e4f21)(objectClass=person))\" attempt=2/3\n"
                "2026-03-29T12:00:01.003Z auth-svc-7b8d replica-2 [ERROR] "
                "GET /login 504 5012ms uid=e4f21 — user_profile_lookup "
                "cascading timeout from upstream user-profile-svc\n"
                "2026-03-29T12:00:01.810Z auth-svc-7b8d replica-1 [WARNING] "
                "circuit_breaker threshold=70%% current=68%% "
                "upstream=user-profile-svc trend=rising\n"
                "2026-03-29T12:00:02.503Z auth-svc-7b8d replica-2 [ERROR] "
                "user complaints ticket_count=42 category=slow_login "
                "avg_login_time=8.2s normal=0.4s"
            ),
            "payments": (
                "2026-03-29T12:00:00.305Z payments-svc-3a1c worker-1 [ERROR] "
                "POST /authorize 500 txn=txn_c2e91 "
                "error=\"transaction rollback: deadlock detected\" "
                "retry=1/3\n"
                "2026-03-29T12:00:01.108Z payments-svc-3a1c worker-2 [ERROR] "
                "fraud detection false positive rate elevated "
                "fp_rate=0.12 normal=0.02 — suspected DB latency "
                "causing score timeout\n"
                "2026-03-29T12:00:01.892Z payments-svc-3a1c worker-1 [ERROR] "
                "PSP connectivity degraded timeout=3 count=12/100 "
                "error=\"read timeout after 8000ms\" "
                "host=api.stripe.com\n"
                "2026-03-29T12:00:02.510Z payments-svc-3a1c worker-3 [WARNING] "
                "transaction_rollback_rate=0.28 normal=0.01 "
                "suspected_cause=upstream_latency"
            ),
            "db": (
                "2026-03-29T12:00:00.050Z postgres-primary db01 [INFO] "
                "autovacuum: VACUUM transactions — "
                "removed 48201 dead tuples, 2841024 remain\n"
                "2026-03-29T12:00:01.003Z postgres-primary db01 [INFO] "
                "replication lag: replica-1=2.1s replica-2=1.8s "
                "within threshold (5s)\n"
                "2026-03-29T12:00:01.810Z postgres-primary db01 [INFO] "
                "connection_count=75/100 idle=12 active=63 "
                "waiting=0 status=accepting_connections"
            ),
        },
        metrics={
            "auth": {"latency_ms": 1200, "error_rate": 0.35, "cpu_pct": 55, "memory_pct": 65},
            "payments": {"latency_ms": 900, "error_rate": 0.28, "cpu_pct": 48, "memory_pct": 58},
            "db": {"latency_ms": 680, "error_rate": 0.15, "cpu_pct": 85, "memory_pct": 82},
        },
        difficulty="hard",
        initial_visible_service="auth",
        anomaly_services_logs=["auth", "payments"],
        anomaly_services_metrics=["db"],
    ),
    Incident(
        incident_id="hard_002",
        services=["gateway", "cache", "notifications"],
        root_cause="notifications",
        severity="P2",
        logs={
            "gateway": (
                "2026-03-29T14:45:00.110Z nginx-gw gw-01 [error] "
                "502 Bad Gateway upstream=notification-svc "
                "request=\"POST /api/notify\" response_time=8.201s\n"
                "2026-03-29T14:45:00.888Z nginx-gw gw-01 [warning] "
                "connection pool draining upstream=notification-svc "
                "active=48/50 idle=2 wait_queue=12\n"
                "2026-03-29T14:45:01.512Z nginx-gw gw-02 [warning] "
                "request queueing at LB depth=24 "
                "upstream=notification-svc avg_wait=2.4s\n"
                "2026-03-29T14:45:02.003Z nginx-gw gw-01 [warning] "
                "DNS resolution delay target=notif-svc.internal "
                "latency=850ms normal=2ms resolver=10.0.0.2"
            ),
            "cache": (
                "2026-03-29T14:45:00.205Z redis-node-1 redis [ERROR] "
                "eviction storm on shard notification-templates "
                "evicted=8421 in_last=60s policy=allkeys-lru\n"
                "2026-03-29T14:45:01.003Z redis-node-2 redis [WARNING] "
                "used_memory=12.4GB maxmemory=16GB memory_pressure=high "
                "large_payload_avg=48KB bucket=notif-templates\n"
                "2026-03-29T14:45:01.810Z cache-proxy proxy-01 [ERROR] "
                "LRU thrashing detected on shard=notif-templates "
                "hit_rate=0.60 normal=0.95 churn_rate=142/s\n"
                "2026-03-29T14:45:02.503Z redis-node-1 redis [WARNING] "
                "memory fragmentation ratio=1.82 target=1.0 "
                "rss=22.6GB used=12.4GB"
            ),
            "notifications": (
                "2026-03-29T14:45:00.102Z notif-svc dispatcher-1 [INFO] "
                "queue_depth=150 capacity=10000 utilization=1.5%%\n"
                "2026-03-29T14:45:01.003Z notif-svc dispatcher-1 [INFO] "
                "email delivery rate=42/s normal=45/s within_sla=true "
                "smtp_conn=alive\n"
                "2026-03-29T14:45:01.810Z notif-svc dispatcher-2 [INFO] "
                "SMS gateway connected provider=twilio "
                "success_rate=0.99 latency=120ms\n"
                "2026-03-29T14:45:02.503Z notif-svc dispatcher-1 [INFO] "
                "health_check status=ok uptime=172800s"
            ),
        },
        metrics={
            "gateway": {"latency_ms": 380, "error_rate": 0.10, "cpu_pct": 42, "memory_pct": 50},
            "cache": {"latency_ms": 250, "error_rate": 0.08, "cpu_pct": 55, "memory_pct": 78},
            "notifications": {"latency_ms": 120, "error_rate": 0.03, "cpu_pct": 30, "memory_pct": 40},
        },
        difficulty="hard",
        initial_visible_service="cache",
        anomaly_services_logs=["gateway", "cache"],
        anomaly_services_metrics=["cache"],
    ),
    Incident(
        incident_id="hard_003",
        services=["auth", "cache", "gateway"],
        root_cause="cache",
        severity="P1",
        logs={
            "auth": (
                "2026-03-29T16:20:00.102Z auth-svc-7b8d replica-1 [ERROR] "
                "session validation failed session_id=sess_4f8a "
                "error=\"stale token in cache\" — forced re-auth uid=b2c91\n"
                "2026-03-29T16:20:00.880Z auth-svc-7b8d replica-2 [ERROR] "
                "token_cache returning stale entries ttl_remaining=-120s "
                "cache_key=tok:b2c91 invalidation_lag=true\n"
                "2026-03-29T16:20:01.510Z auth-svc-7b8d replica-1 [WARNING] "
                "session count anomaly active=84201 expected=~42000 "
                "duplicate_sessions=true cause=cache_inconsistency\n"
                "2026-03-29T16:20:02.203Z auth-svc-7b8d replica-2 [ERROR] "
                "forced re-authentication rate=0.30 normal=0.01 "
                "affected_users=~1200"
            ),
            "cache": (
                "2026-03-29T16:20:00.050Z redis-node-1 redis [INFO] "
                "cluster_state=ok cluster_slots_assigned=16384 "
                "cluster_slots_ok=16384\n"
                "2026-03-29T16:20:01.003Z redis-node-2 redis [INFO] "
                "used_memory_human=11.5GB maxmemory=16GB "
                "evicted_keys=0 connected_clients=142\n"
                "2026-03-29T16:20:01.810Z redis-node-3 redis [INFO] "
                "replication status=in_sync offset_diff=0 "
                "link_status=up\n"
                "2026-03-29T16:20:02.503Z redis-node-1 redis [INFO] "
                "keyspace db0: keys=2841024 expires=1420512 "
                "avg_ttl=1800042ms"
            ),
            "gateway": (
                "2026-03-29T16:20:00.305Z nginx-gw gw-01 [error] "
                "rate_limiter miscount uid=c3d92 "
                "reported_req=500 actual_req=12 bucket=api_v2 "
                "429 returned incorrectly\n"
                "2026-03-29T16:20:01.108Z nginx-gw gw-02 [error] "
                "distributed lock contention on session-store "
                "lock_wait=2.4s lock_key=rate:c3d92 "
                "suspected=shared_state_corruption\n"
                "2026-03-29T16:20:01.892Z nginx-gw gw-01 [error] "
                "rate_limiter false 429s uid_count=~180 "
                "error_budget_impact=high bypass_enabled=false\n"
                "2026-03-29T16:20:02.510Z nginx-gw gw-02 [warning] "
                "session store read latency=320ms normal=5ms "
                "backend=redis suspect=data_corruption"
            ),
        },
        metrics={
            "auth": {"latency_ms": 550, "error_rate": 0.30, "cpu_pct": 45, "memory_pct": 58},
            "cache": {"latency_ms": 95, "error_rate": 0.02, "cpu_pct": 40, "memory_pct": 72},
            "gateway": {"latency_ms": 320, "error_rate": 0.22, "cpu_pct": 52, "memory_pct": 48},
        },
        difficulty="hard",
        initial_visible_service="gateway",
        anomaly_services_logs=["auth", "gateway"],
        anomaly_services_metrics=["auth", "gateway"],
    ),
    Incident(
        incident_id="hard_004",
        services=["payments", "db", "notifications"],
        root_cause="db",
        severity="P0",
        logs={
            "payments": (
                "2026-03-29T19:00:00.102Z payments-svc-3a1c worker-1 [CRITICAL] "
                "payment processing STALLED — all DB writes timing out "
                "error=\"canceling statement due to lock timeout\" "
                "txn=txn_8f2e1\n"
                "2026-03-29T19:00:00.810Z payments-svc-3a1c worker-2 [CRITICAL] "
                "transaction isolation conflict level=SERIALIZABLE "
                "deadlock_count=48 rollback_rate=0.85\n"
                "2026-03-29T19:00:01.503Z payments-svc-3a1c worker-1 [CRITICAL] "
                "emergency payment queue activated pending=2004 "
                "capacity=5000 drain_rate=0/s "
                "revenue_at_risk=$142,800\n"
                "2026-03-29T19:00:02.201Z payments-svc-3a1c worker-3 [ERROR] "
                "circuit_breaker=OPEN upstream=db01 "
                "failure_rate=0.85 threshold=0.50"
            ),
            "db": (
                "2026-03-29T19:00:00.050Z postgres-primary db01 [INFO] "
                "scheduled maintenance: ALTER TABLE transactions "
                "ADD COLUMN metadata jsonb DEFAULT '{}' — online DDL\n"
                "2026-03-29T19:00:01.003Z postgres-primary db01 [INFO] "
                "online schema migration progress: 42%% "
                "rows_processed=2.4M/5.7M estimated_completion=15min\n"
                "2026-03-29T19:00:01.810Z postgres-primary db01 [NOTICE] "
                "performance impact expected during migration — "
                "advisory lock held lock_id=184205 mode=ACCESS EXCLUSIVE\n"
                "2026-03-29T19:00:02.503Z postgres-primary db01 [INFO] "
                "autovacuum paused during DDL — will resume after "
                "migration complete"
            ),
            "notifications": (
                "2026-03-29T19:00:00.305Z notif-svc worker-1 [ERROR] "
                "GET /transactions/txn_8f2e1 500 — cannot retrieve "
                "transaction details error=\"relation locked\"\n"
                "2026-03-29T19:00:01.108Z notif-svc worker-2 [ERROR] "
                "payment confirmation dispatch failed batch_size=142 "
                "reason=upstream_500 source=payments-svc\n"
                "2026-03-29T19:00:01.892Z notif-svc worker-1 [WARNING] "
                "customer complaint volume spiking "
                "zendesk_tickets=+48 in_last=5min category=payment_failed\n"
                "2026-03-29T19:00:02.510Z notif-svc worker-2 [ERROR] "
                "retry exhausted notif_id=n_c2e91 attempts=3/3 "
                "last_error=\"502 Bad Gateway\""
            ),
        },
        metrics={
            "payments": {"latency_ms": 6000, "error_rate": 0.85, "cpu_pct": 30, "memory_pct": 40},
            "db": {"latency_ms": 180, "error_rate": 0.05, "cpu_pct": 90, "memory_pct": 85},
            "notifications": {"latency_ms": 400, "error_rate": 0.40, "cpu_pct": 35, "memory_pct": 45},
        },
        difficulty="hard",
        initial_visible_service="payments",
        anomaly_services_logs=["payments", "notifications"],
        anomaly_services_metrics=["payments", "db", "notifications"],
    ),
    Incident(
        incident_id="hard_005",
        services=["auth", "gateway", "notifications"],
        root_cause="gateway",
        severity="P1",
        logs={
            "auth": (
                "2026-03-29T06:15:00.102Z auth-svc-7b8d replica-1 [ERROR] "
                "SAML assertion validation timeout idp=enterprise-sso.corp "
                "duration=12042ms threshold=5000ms uid=sso_admin_1\n"
                "2026-03-29T06:15:01.003Z auth-svc-7b8d replica-2 [ERROR] "
                "external IdP slow response provider=okta "
                "latency=8420ms normal=200ms endpoint=/saml/sso\n"
                "2026-03-29T06:15:01.810Z auth-svc-7b8d replica-1 [WARNING] "
                "fallback to local auth active success_rate=0.62 "
                "sso_bypass=true affected_org=acme-corp\n"
                "2026-03-29T06:15:02.503Z auth-svc-7b8d replica-2 [ERROR] "
                "MFA service degraded provider=duo timeout_rate=0.25 "
                "push_delivery_delayed=true avg_delay=8.2s"
            ),
            "gateway": (
                "2026-03-29T06:15:00.050Z nginx-gw gw-01 [info] "
                "health_check upstream=auth-svc status=healthy "
                "latency=180ms (elevated, threshold=500ms)\n"
                "2026-03-29T06:15:01.003Z nginx-gw gw-01 [info] "
                "request_throughput=480/s within_normal_range "
                "(baseline=500/s variance=4%%)\n"
                "2026-03-29T06:15:01.810Z nginx-gw gw-02 [warning] "
                "connection reuse errors count=5 total=5012 "
                "error_rate=0.001 keepalive_timeout=60s\n"
                "2026-03-29T06:15:02.503Z nginx-gw gw-01 [info] "
                "upstream_health all_checks=passing "
                "no_failed_probes last_failure=48h_ago"
            ),
            "notifications": (
                "2026-03-29T06:15:00.305Z notif-svc worker-1 [ERROR] "
                "webhook delivery failed partner=acme-corp "
                "POST https://hooks.acme.com/events 0ms "
                "error=\"tls: failed to verify certificate: "
                "x509: certificate signed by unknown authority\"\n"
                "2026-03-29T06:15:01.108Z notif-svc worker-2 [ERROR] "
                "TLS handshake error outbound host=hooks.partner-b.io:443 "
                "error=\"certificate pinning validation failed\" "
                "pin_sha256=mismatch\n"
                "2026-03-29T06:15:01.892Z notif-svc worker-1 [ERROR] "
                "webhook delivery failure_rate=0.60 "
                "affected_partners=[acme-corp, partner-b, globex] "
                "channel=https\n"
                "2026-03-29T06:15:02.510Z notif-svc worker-2 [WARNING] "
                "DLQ growing dead_letter_count=842 "
                "capacity=10000 oldest=2026-03-29T06:00:00Z"
            ),
        },
        metrics={
            "auth": {"latency_ms": 950, "error_rate": 0.25, "cpu_pct": 50, "memory_pct": 55},
            "gateway": {"latency_ms": 200, "error_rate": 0.04, "cpu_pct": 65, "memory_pct": 70},
            "notifications": {"latency_ms": 600, "error_rate": 0.55, "cpu_pct": 40, "memory_pct": 48},
        },
        difficulty="hard",
        initial_visible_service="auth",
        anomaly_services_logs=["auth", "notifications"],
        anomaly_services_metrics=["auth", "notifications", "gateway"],
    ),
]


def get_incidents_by_difficulty(difficulty: Literal["easy", "medium", "hard"]) -> List[Incident]:
    """Return all incidents for a given difficulty level."""
    return [inc for inc in INCIDENTS if inc.difficulty == difficulty]


def get_incident_by_id(incident_id: str) -> Incident:
    """Return a specific incident by ID. Raises ValueError if not found."""
    for inc in INCIDENTS:
        if inc.incident_id == incident_id:
            return inc
    raise ValueError(f"Incident '{incident_id}' not found")
