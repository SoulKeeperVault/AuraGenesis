"""
Aura Face Recognition Engine
Recognizes Owner + known faces from camera feed.
Integrates with aura_core Global Workspace.
Hardware: RPi Camera Module v2/3 / USB webcam
"""

from __future__ import annotations

import pickle
from pathlib import Path
from typing import Dict, List, Optional

import cv2
import numpy as np

try:
    import face_recognition  # type: ignore
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False
    print("[FaceRecognition] face_recognition not installed. Run: pip install face-recognition")


class AuraFaceRecognizer:
    """
    Real-time face recognition for Aura.
    - Learns faces from photos (add_known_face)
    - Recognizes them live from camera frames
    - Reports to Global Workspace: 'Owner detected! Confidence: 0.95'
    """

    def __init__(self, known_faces_dir: str = "known_faces", tolerance: float = 0.55):
        self.known_faces_dir = Path(known_faces_dir)
        self.known_faces_dir.mkdir(parents=True, exist_ok=True)
        self.tolerance = tolerance
        self.known_encodings: List[np.ndarray] = []
        self.known_names: List[str] = []
        self._load_encodings()

    # ------------------------------------------------------------------ #
    #  Training                                                            #
    # ------------------------------------------------------------------ #

    def add_known_face(self, name: str, image_path: str) -> bool:
        """Register a new face from a photo file. Call once per person."""
        if not FACE_RECOGNITION_AVAILABLE:
            return False
        image = face_recognition.load_image_file(image_path)
        encodings = face_recognition.face_encodings(image)
        if not encodings:
            print(f"[FaceRecognition] No face found in {image_path}")
            return False
        self.known_encodings.append(encodings[0])
        self.known_names.append(name)
        self._save_encodings()
        print(f"[FaceRecognition] ✅ Registered: {name}")
        return True

    # ------------------------------------------------------------------ #
    #  Recognition                                                         #
    # ------------------------------------------------------------------ #

    def recognize_faces(self, frame: np.ndarray) -> List[Dict]:
        """
        Detect and recognize faces in a BGR camera frame.
        Returns list of dicts: {'name', 'confidence', 'bbox': (x, y, w, h)}
        """
        if not FACE_RECOGNITION_AVAILABLE or not self.known_encodings:
            return []

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        locations = face_recognition.face_locations(rgb, model="hog")  # hog = faster on Pi
        encodings = face_recognition.face_encodings(rgb, locations)

        results: List[Dict] = []
        for enc, (top, right, bottom, left) in zip(encodings, locations):
            distances = face_recognition.face_distance(self.known_encodings, enc)
            best_idx = int(np.argmin(distances))
            matched = distances[best_idx] <= self.tolerance

            name = self.known_names[best_idx] if matched else "Unknown"
            confidence = float(1.0 - distances[best_idx]) if matched else 0.0

            results.append({
                "name": name,
                "confidence": round(confidence, 3),
                "bbox": (left, top, right - left, bottom - top),
            })

        return results

    def draw_boxes(self, frame: np.ndarray, results: List[Dict]) -> np.ndarray:
        """Draw bounding boxes + names on frame for debug/UI display."""
        for r in results:
            x, y, w, h = r["bbox"]
            color = (0, 255, 0) if r["name"] != "Unknown" else (0, 0, 255)
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            label = f"{r['name']} ({r['confidence']:.0%})"
            cv2.putText(frame, label, (x, y - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        return frame

    # ------------------------------------------------------------------ #
    #  Persistence                                                         #
    # ------------------------------------------------------------------ #

    def _save_encodings(self) -> None:
        path = self.known_faces_dir / "encodings.pkl"
        with open(path, "wb") as f:
            pickle.dump({"encodings": self.known_encodings, "names": self.known_names}, f)

    def _load_encodings(self) -> None:
        path = self.known_faces_dir / "encodings.pkl"
        if path.exists():
            with open(path, "rb") as f:
                data = pickle.load(f)
                self.known_encodings = data.get("encodings", [])
                self.known_names = data.get("names", [])
            print(f"[FaceRecognition] Loaded {len(self.known_names)} known face(s): {self.known_names}")

    # ------------------------------------------------------------------ #
    #  Global Workspace broadcast helper                                   #
    # ------------------------------------------------------------------ #

    def to_workspace_signal(self, results: List[Dict]) -> Optional[str]:
        """
        Convert recognition results to a natural-language signal
        for Aura's Global Workspace.
        Example: 'Owner entered the room (confidence: 95%)'
        """
        known = [r for r in results if r["name"] != "Unknown"]
        unknown = [r for r in results if r["name"] == "Unknown"]

        parts: List[str] = []
        for r in known:
            parts.append(f"{r['name']} detected (confidence: {r['confidence']:.0%})")
        if unknown:
            parts.append(f"{len(unknown)} unknown person(s) in view")

        return " | ".join(parts) if parts else None
