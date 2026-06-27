from __future__ import annotations

"""Roboflow PPE detection integration.

Uses the hosted Roboflow PPE combined model for object detection.
Model: personal-protective-equipment-combined-model/8
Detects: helmet, no_helmet, vest, no_vest, and people.
"""
import base64
from typing import Optional, TypedDict

import requests

from app.config import ROBOFLOW_API_KEY

ROBOFLOW_MODEL_ID = "personal-protective-equipment-combined-model/8"
ROBOFLOW_API_URL = "https://serverless.roboflow.com"
ROBOFLOW_TIMEOUT_SECONDS = 45


class RawDetection(TypedDict):
    label: str
    confidence: float
    boundingBox: Optional[dict]
    frameTimestamp: Optional[float]


def run_roboflow_inference(frames: list[dict]) -> list[RawDetection]:
    """Run Roboflow PPE detection on a list of frames.

    frames: list of {"path": str, "frameTimestamp": float | None}

    Returns list of RawDetection results.
    """
    if not ROBOFLOW_API_KEY:
        raise ValueError("ROBOFLOW_API_KEY not set in environment")

    detections: list[RawDetection] = []

    for frame in frames:
        try:
            frame_detections = _analyze_frame_with_roboflow(
                frame["path"], frame.get("frameTimestamp")
            )
            detections.extend(frame_detections)
        except Exception as e:
            print(f"Warning: Roboflow inference failed for frame {frame['path']}: {e}")
            raise

    return detections


def _analyze_frame_with_roboflow(
    image_path: str,
    frame_timestamp: Optional[float]
) -> list[RawDetection]:
    """Analyze a single frame with Roboflow API."""
    result = _post_image_to_roboflow(image_path)
    return _parse_roboflow_response(result, frame_timestamp)


def _post_image_to_roboflow(image_path: str) -> dict:
    """Post a base64-encoded image to Roboflow's hosted REST API."""
    with open(image_path, "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode("utf-8")

    response = requests.post(
        f"{ROBOFLOW_API_URL}/{ROBOFLOW_MODEL_ID}",
        params={
            "api_key": ROBOFLOW_API_KEY,
            "format": "json",
            "image_type": "base64",
        },
        data=encoded_image,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=ROBOFLOW_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return response.json()


def _parse_roboflow_response(
    response: dict,
    frame_timestamp: Optional[float]
) -> list[RawDetection]:
    """Parse Roboflow API response and extract detections.

    Roboflow returns predictions with class, confidence, and bounding box.
    Map Roboflow class names to our standard PPE labels.
    """
    detections: list[RawDetection] = []

    # Roboflow returns predictions as a list in the response
    predictions = response.get("predictions", [])

    for pred in predictions:
        class_name = pred.get("class", "").lower()

        # Map Roboflow class names to our standard labels
        # Common PPE classes from Roboflow: person, helmet, hardhat, vest, safety_vest, etc.
        label = _map_roboflow_class(class_name)

        if label:  # Only include recognized PPE labels
            # Roboflow returns bounding box with x, y, width, height directly in pred
            bbox = {
                "x": int(pred.get("x", 0)),
                "y": int(pred.get("y", 0)),
                "width": int(pred.get("width", 100)),
                "height": int(pred.get("height", 100)),
            }

            detections.append({
                "label": label,
                "confidence": float(pred.get("confidence", 0.5)),
                "boundingBox": bbox,
                "frameTimestamp": frame_timestamp,
            })

    return detections


def _map_roboflow_class(class_name: str) -> Optional[str]:
    """Map Roboflow class names to standard PPE labels.

    Standard labels: person, helmet, no_helmet, vest, no_vest
    """
    # Normalize input: lowercase and replace hyphens/underscores with spaces
    name_normalized = class_name.lower().strip().replace("-", " ").replace("_", " ")

    # Map common variations (note: normalized names have spaces instead of hyphens).
    # Roboflow's personal-protective-equipment-combined-model returns class names
    # like "NO-Hardhat" and "NO-Safety Vest" (with hyphens); after normalization
    # those become "no hardhat" and "no safety vest".
    mapping = {
        "person": "person",
        "people": "person",
        "worker": "person",
        "helmet": "helmet",
        "hardhat": "helmet",
        "hard hat": "helmet",
        "no helmet": "no_helmet",
        "no hardhat": "no_helmet",       # Roboflow: "NO-Hardhat"
        "without helmet": "no_helmet",
        "without hardhat": "no_helmet",
        "person without helmet": "no_helmet",
        "person no helmet": "no_helmet",
        "vest": "vest",
        "safety vest": "vest",
        "reflective vest": "vest",
        "hi vis vest": "vest",
        "high vis vest": "vest",
        "no vest": "no_vest",
        "no safety vest": "no_vest",     # Roboflow: "NO-Safety Vest"
        "without vest": "no_vest",
        "without safety vest": "no_vest",
        "person without vest": "no_vest",
        "person no vest": "no_vest",
    }

    return mapping.get(name_normalized)
