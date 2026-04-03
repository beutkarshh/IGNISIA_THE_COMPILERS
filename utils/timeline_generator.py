"""Utilities for normalizing and simulating ICU patient timelines."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


DEFAULT_VITALS = {
    "heart_rate": 90,
    "systolic_bp": 120,
    "diastolic_bp": 80,
    "respiratory_rate": 18,
    "temperature": 37.0,
    "spo2": 96,
}

DEFAULT_LABS = {
    "wbc": 10.0,
    "lactate": 1.5,
    "creatinine": 1.0,
    "bun": 18,
    "platelets": 220,
}


def _parse_timestamp(value: str) -> Optional[datetime]:
    if not value:
        return None

    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def _sort_key(timepoint: Dict[str, Any], fallback_index: int) -> tuple:
    timestamp = _parse_timestamp(str(timepoint.get("timestamp", "")))
    hours = timepoint.get("hours_since_admission")
    return (
        timestamp.isoformat() if timestamp else "",
        hours if isinstance(hours, int) else fallback_index,
        fallback_index,
    )


def normalize_timepoint(timepoint: Dict[str, Any], index: int) -> Dict[str, Any]:
    current = deepcopy(timepoint)

    if "vitals" not in current:
        current["vitals"] = deepcopy(DEFAULT_VITALS)
    else:
        for key, value in DEFAULT_VITALS.items():
            current["vitals"].setdefault(key, value)

    if "labs" not in current:
        current["labs"] = deepcopy(DEFAULT_LABS)
    else:
        for key, value in DEFAULT_LABS.items():
            current["labs"].setdefault(key, value)

    current.setdefault("timestamp", (datetime.utcnow() + timedelta(hours=index)).isoformat())
    current.setdefault("time_label", f"Hour {index * 6}")
    current.setdefault("hours_since_admission", index * 6)
    current.setdefault("notes", "")
    return current


def build_timeline(patient_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    timeline = patient_data.get("timeline") or patient_data.get("timeline_history") or []

    if timeline:
        ordered = sorted(enumerate(timeline), key=lambda item: _sort_key(item[1], item[0]))
        return [normalize_timepoint(point, index) for index, (_, point) in enumerate(ordered)]

    timepoints = patient_data.get("timepoints") or []
    if timepoints:
        return [normalize_timepoint(point, index) for index, point in enumerate(timepoints)]

    base_time = _parse_timestamp(str(patient_data.get("admission_time", ""))) or datetime.utcnow()
    generated: List[Dict[str, Any]] = []
    for index in range(int(patient_data.get("default_timeline_points", 4))):
        generated.append(
            normalize_timepoint(
                {
                    "timestamp": (base_time + timedelta(hours=index * 6)).isoformat(),
                    "time_label": f"Hour {index * 6}",
                    "hours_since_admission": index * 6,
                    "vitals": deepcopy(DEFAULT_VITALS),
                    "labs": deepcopy(DEFAULT_LABS),
                    "notes": patient_data.get("notes", ""),
                },
                index,
            )
        )
    return generated


def resolve_current_timepoint_index(patient_data: Dict[str, Any], explicit_index: Optional[int] = None) -> int:
    if explicit_index is not None:
        return explicit_index

    timeline = build_timeline(patient_data)
    metadata = patient_data.get("metadata") or {}
    critical_timepoint = metadata.get("critical_timepoint")
    if critical_timepoint:
        for index, point in enumerate(timeline):
            if point.get("timestamp") == critical_timepoint or point.get("time_label") == critical_timepoint:
                return index

    return max(len(timeline) - 1, 0)


def generate_patient_timeline(patient_data: Dict[str, Any], current_timepoint_index: Optional[int] = None) -> Dict[str, Any]:
    normalized = deepcopy(patient_data)
    timeline = build_timeline(normalized)
    index = resolve_current_timepoint_index(normalized, current_timepoint_index)
    normalized["timeline"] = timeline
    normalized["current_timepoint_index"] = index
    return normalized
