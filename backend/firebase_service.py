"""Firebase storage service with a safe in-memory fallback."""

from __future__ import annotations

import json
import os
import threading
from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
except Exception:  # pragma: no cover - optional dependency path
    firebase_admin = None
    credentials = None
    firestore = None


class FirebaseService:
    """Persist assessments to Firestore when configured, otherwise use memory."""

    def __init__(self, collection_name: str = "assessments") -> None:
        self.collection_name = collection_name
        self._lock = threading.Lock()
        self._memory_store: Dict[str, Dict[str, Any]] = {}
        self._enabled = False
        self._db = None
        self._storage_backend = "memory"
        self._initialize_firestore()

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def storage_backend(self) -> str:
        return self._storage_backend

    def _initialize_firestore(self) -> None:
        if firebase_admin is None or credentials is None or firestore is None:
            return

        credentials_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
        credentials_json = os.getenv("FIREBASE_CREDENTIALS_JSON")
        project_id = os.getenv("FIREBASE_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")

        try:
            if not firebase_admin._apps:
                if credentials_path and os.path.exists(credentials_path):
                    cred = credentials.Certificate(credentials_path)
                    firebase_admin.initialize_app(cred, {"projectId": project_id} if project_id else None)
                elif credentials_json:
                    cred_dict = json.loads(credentials_json)
                    cred = credentials.Certificate(cred_dict)
                    firebase_admin.initialize_app(cred, {"projectId": project_id} if project_id else None)
                else:
                    return

            self._db = firestore.client()
            self._enabled = True
            self._storage_backend = "firestore"
        except Exception:
            self._db = None
            self._enabled = False
            self._storage_backend = "memory"

    def save_assessment(self, assessment: Dict[str, Any]) -> Dict[str, Any]:
        record = deepcopy(assessment)
        assessment_id = record.get("assessment_id")
        if not assessment_id:
            assessment_id = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
            record["assessment_id"] = assessment_id

        record.setdefault("saved_at", datetime.utcnow().isoformat())

        with self._lock:
            self._memory_store[assessment_id] = deepcopy(record)

        if self._enabled and self._db is not None:
            self._db.collection(self.collection_name).document(assessment_id).set(record)

        return record

    def get_assessment(self, assessment_id: str) -> Optional[Dict[str, Any]]:
        if self._enabled and self._db is not None:
            doc = self._db.collection(self.collection_name).document(assessment_id).get()
            if doc.exists:
                return doc.to_dict()

        with self._lock:
            record = self._memory_store.get(assessment_id)
            return deepcopy(record) if record else None

    def list_patient_assessments(self, patient_id: str) -> List[Dict[str, Any]]:
        if self._enabled and self._db is not None:
            query = self._db.collection(self.collection_name).where("patient_id", "==", patient_id).stream()
            return [doc.to_dict() for doc in query]

        with self._lock:
            return [deepcopy(record) for record in self._memory_store.values() if record.get("patient_id") == patient_id]

    def health(self) -> Dict[str, Any]:
        return {
            "enabled": self._enabled,
            "storage_backend": self._storage_backend,
            "records": len(self._memory_store),
        }
