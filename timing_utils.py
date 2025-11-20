"""
Timing utilities for measuring operation performance.
"""
import time
from typing import Dict, Any
from dataclasses import dataclass, field


@dataclass
class TimingInfo:
    """Container for timing information."""
    connection_acquisition_ms: float = 0.0
    query_execution_ms: float = 0.0
    data_transformation_ms: float = 0.0
    repository_total_ms: float = 0.0
    endpoint_processing_ms: float = 0.0
    response_serialization_ms: float = 0.0
    total_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary for JSON serialization."""
        return {
            "connection_acquisition_ms": round(self.connection_acquisition_ms, 2),
            "query_execution_ms": round(self.query_execution_ms, 2),
            "data_transformation_ms": round(self.data_transformation_ms, 2),
            "repository_total_ms": round(self.repository_total_ms, 2),
            "endpoint_processing_ms": round(self.endpoint_processing_ms, 2),
            "response_serialization_ms": round(self.response_serialization_ms, 2),
            "total_ms": round(self.total_ms, 2),
        }
    
    def to_header_string(self) -> str:
        """Convert to comma-separated string for HTTP header."""
        parts = []
        if self.connection_acquisition_ms > 0:
            parts.append(f"conn={self.connection_acquisition_ms:.2f}")
        if self.query_execution_ms > 0:
            parts.append(f"query={self.query_execution_ms:.2f}")
        if self.data_transformation_ms > 0:
            parts.append(f"transform={self.data_transformation_ms:.2f}")
        if self.repository_total_ms > 0:
            parts.append(f"repo={self.repository_total_ms:.2f}")
        if self.endpoint_processing_ms > 0:
            parts.append(f"endpoint={self.endpoint_processing_ms:.2f}")
        if self.response_serialization_ms > 0:
            parts.append(f"serialize={self.response_serialization_ms:.2f}")
        parts.append(f"total={self.total_ms:.2f}")
        return ",".join(parts)


class TimingContext:
    """Context manager for timing operations."""
    
    def __init__(self, timing_info: TimingInfo, component: str):
        self.timing_info = timing_info
        self.component = component
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed_ms = (time.time() - self.start_time) * 1000
        setattr(self.timing_info, self.component, elapsed_ms)
        return False

