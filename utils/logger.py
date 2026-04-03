"""Structured JSON logging for the ICU Clinical Assistant."""

import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional


class JSONFormatter(logging.Formatter):
    """Format logs as JSON for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        
        # Add extra fields
        if hasattr(record, 'patient_id'):
            log_data['patient_id'] = record.patient_id
        if hasattr(record, 'assessment_id'):
            log_data['assessment_id'] = record.assessment_id
        if hasattr(record, 'execution_time_ms'):
            log_data['execution_time_ms'] = record.execution_time_ms
        if hasattr(record, 'agent'):
            log_data['agent'] = record.agent
        if hasattr(record, 'event'):
            log_data['event'] = record.event
        if hasattr(record, 'agent_timings'):
            log_data['agent_timings'] = record.agent_timings
        if hasattr(record, 'risk_score'):
            log_data['risk_score'] = record.risk_score
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


def setup_logger(name: str, level: str = 'INFO') -> logging.Logger:
    """
    Set up structured JSON logger.
    
    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Avoid adding duplicate handlers
    if not logger.handlers:
        # Console handler with JSON formatting
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
    
    return logger


def log_assessment_start(logger: logging.Logger, patient_id: str, assessment_id: str):
    """Log assessment start."""
    logger.info(
        "Assessment started",
        extra={
            'patient_id': patient_id,
            'assessment_id': assessment_id,
            'event': 'assessment_start'
        }
    )


def log_assessment_complete(
    logger: logging.Logger,
    patient_id: str,
    assessment_id: str,
    risk_score: int,
    execution_time_ms: int,
    agent_timings: Optional[Dict[str, int]] = None
):
    """Log assessment completion with metrics."""
    logger.info(
        "Assessment completed",
        extra={
            'patient_id': patient_id,
            'assessment_id': assessment_id,
            'risk_score': risk_score,
            'execution_time_ms': execution_time_ms,
            'agent_timings': agent_timings or {},
            'event': 'assessment_complete'
        }
    )


def log_agent_execution(logger: logging.Logger, agent_name: str, execution_time_ms: int):
    """Log individual agent execution."""
    logger.debug(
        f"Agent {agent_name} executed",
        extra={
            'agent': agent_name,
            'execution_time_ms': execution_time_ms,
            'event': 'agent_execution'
        }
    )
