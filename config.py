"""
SwarmSentinel — Centralized Configuration
==========================================

Single source of truth for all configurable parameters.
Values are loaded from environment variables with sensible defaults.
"""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class GraphConfig:
    """Pheromone graph tuning parameters."""
    decay_rate: float = 0.95
    min_threshold: float = 0.01
    decay_interval: float = 30.0
    max_nodes: int = 50000
    max_edges: int = 200000
    reinforcement_blend_old: float = 0.7
    reinforcement_blend_new: float = 0.3
    hotspot_threshold: float = 0.5
    backend: str = "memory"  # "memory" or "redis"


@dataclass
class DetectorConfig:
    """Anomaly detector thresholds."""
    zscore_threshold: float = 2.0
    zscore_max_delta: float = 50.0
    frequency_threshold: int = 2
    frequency_max_delta: float = 30.0
    sequence_unique_threshold: int = 3
    sequence_max_delta: float = 40.0
    min_history_samples: int = 3


@dataclass
class SwarmConfig:
    """Ant swarm agent parameters."""
    num_scouts: int = 5
    soldier_threshold: float = 15.0
    scout_pheromone_strength: float = 0.3
    soldier_pheromone_strength: float = 50.0
    queen_hotspot_min_strength: float = 3.0
    convergence_threshold: float = 5.0
    max_soldiers: int = 20
    investigation_timeout_seconds: float = 300.0


@dataclass
class CorrelationConfig:
    """Incident correlation parameters."""
    window_seconds: float = 300.0
    create_threshold: float = 60.0
    severity_critical: float = 80.0
    severity_high: float = 60.0
    severity_medium: float = 40.0


@dataclass
class QueueConfig:
    """Event queue parameters."""
    max_size: int = 10000
    batch_size: int = 50
    flush_interval: float = 0.5


@dataclass
class APIConfig:
    """API server configuration."""
    api_key: str = ""
    rate_limit_requests: int = 30
    rate_limit_window_seconds: int = 60
    cors_origins: list = field(default_factory=lambda: ["*"])
    ws_heartbeat_seconds: float = 30.0
    max_incidents_per_page: int = 50


@dataclass
class AppConfig:
    """Top-level application configuration."""
    graph: GraphConfig = field(default_factory=GraphConfig)
    detector: DetectorConfig = field(default_factory=DetectorConfig)
    swarm: SwarmConfig = field(default_factory=SwarmConfig)
    correlation: CorrelationConfig = field(default_factory=CorrelationConfig)
    queue: QueueConfig = field(default_factory=QueueConfig)
    api: APIConfig = field(default_factory=APIConfig)
    version: str = "2.0.0"
    environment: str = "development"
    log_level: str = "INFO"
    redis_url: Optional[str] = None

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Load configuration from environment variables."""
        cfg = cls()

        # API
        cfg.api.api_key = (os.getenv("API_KEY") or "").strip()
        cfg.api.rate_limit_requests = int(os.getenv("RATE_LIMIT_REQUESTS", "30"))
        cfg.api.rate_limit_window_seconds = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))

        # Graph
        cfg.graph.decay_rate = float(os.getenv("GRAPH_DECAY_RATE", "0.95"))
        cfg.graph.backend = os.getenv("GRAPH_BACKEND", "memory")

        # Environment
        cfg.environment = os.getenv("ENVIRONMENT", "development")
        cfg.log_level = os.getenv("LOG_LEVEL", "INFO")
        cfg.redis_url = os.getenv("REDIS_URL")

        # Correlation
        cfg.correlation.window_seconds = float(os.getenv("CORRELATION_WINDOW", "300"))
        cfg.correlation.create_threshold = float(os.getenv("CORRELATION_THRESHOLD", "60"))

        return cfg

    def to_dict(self) -> dict:
        """Serialize config for /health or /metrics endpoints (redacts secrets)."""
        return {
            "version": self.version,
            "environment": self.environment,
            "graph_backend": self.graph.backend,
            "graph_max_nodes": self.graph.max_nodes,
            "queue_max_size": self.queue.max_size,
            "rate_limit": f"{self.api.rate_limit_requests}/{self.api.rate_limit_window_seconds}s",
            "api_key_set": bool(self.api.api_key),
            "redis_configured": bool(self.redis_url),
        }


# Module-level singleton
config = AppConfig.from_env()
