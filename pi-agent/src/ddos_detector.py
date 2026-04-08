"""DDoS detector wrapper for the Pi agent.

Translates per-device stats collected by the StatsCollector into the
feature vector expected by the trained ML model, then runs inference.

The feature set matches what generate_synthetic_dataset.py /
train_ddos_model.py produce:
  bytes_in, bytes_out, pkts_in, pkts_out, duration,
  bytes_per_sec_in, bytes_per_sec_out,
  pkt_size_avg_in, pkt_size_avg_out,
  byte_ratio, pkt_ratio
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

import joblib
import numpy as np
import pandas as pd


logger = logging.getLogger(__name__)

# Must stay in sync with train_ddos_model.py / generate_synthetic_dataset.py
FEATURE_COLUMNS: List[str] = [
    "bytes_in",
    "bytes_out",
    "pkts_in",
    "pkts_out",
    "duration",
    "bytes_per_sec_in",
    "bytes_per_sec_out",
    "pkt_size_avg_in",
    "pkt_size_avg_out",
    "byte_ratio",
    "pkt_ratio",
]

# Average packet sizes used to estimate packet counts from byte counts.
# Conservative MTU assumption for normal traffic.
NORMAL_PKT_SIZE = 1000  # bytes


@dataclass
class DetectionResult:
    mac_address: str
    prediction: str
    confidence: float
    total_bytes: int


class DdosDetector:
    def __init__(self, model_path: str, enabled: bool = False):
        self.model_path = model_path
        self.enabled = enabled
        self.model = None

        if self.enabled:
            self._load_model()

    def _load_model(self) -> None:
        try:
            self.model = joblib.load(self.model_path)
            logger.info(f"Loaded DDoS model from {self.model_path}")
        except FileNotFoundError:
            logger.error(f"DDoS model file not found: {self.model_path}")
            self.model = None
            self.enabled = False
        except Exception as e:
            logger.error(f"Failed to load DDoS model: {e}")
            self.model = None
            self.enabled = False

    def is_ready(self) -> bool:
        return self.enabled and self.model is not None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def predict(
        self,
        stats: List[Dict],
        devices: Dict[str, Dict],
        interval_seconds: int,
    ) -> List[DetectionResult]:
        """Run the ML model on per-device stats from the last collection.

        Args:
            stats: list of dicts with keys mac_address, bytes_uploaded,
                   bytes_downloaded (produced by StatsCollector).
            devices: MAC → device-info mapping (currently unused but kept
                     for future feature expansion).
            interval_seconds: the collection interval that produced *stats*.

        Returns:
            A DetectionResult for **every** device (not only attacks).
        """
        if not self.is_ready() or not stats:
            return []

        rows: List[Dict[str, float]] = []
        meta: List[Dict] = []

        for stat in stats:
            mac = stat.get("mac_address")
            if not mac:
                continue

            bytes_in = int(stat.get("bytes_downloaded", 0))
            bytes_out = int(stat.get("bytes_uploaded", 0))
            duration = max(1, int(interval_seconds))

            row = self._build_feature_row(bytes_in, bytes_out, duration)
            rows.append(row)
            meta.append({
                "mac_address": mac,
                "total_bytes": bytes_in + bytes_out,
            })

        if not rows:
            return []

        df = pd.DataFrame(rows, columns=FEATURE_COLUMNS)

        try:
            preds = self.model.predict(df)
            confidences = None
            if hasattr(self.model, "predict_proba"):
                probas = self.model.predict_proba(df)
                confidences = probas.max(axis=1)
        except Exception as e:
            logger.error(f"DDoS model prediction failed: {e}")
            return []

        results: List[DetectionResult] = []
        for idx, pred in enumerate(preds):
            conf = float(confidences[idx]) if confidences is not None else 0.0
            results.append(
                DetectionResult(
                    mac_address=meta[idx]["mac_address"],
                    prediction=str(pred),
                    confidence=conf,
                    total_bytes=meta[idx]["total_bytes"],
                )
            )

        return results

    # ------------------------------------------------------------------
    # Feature engineering
    # ------------------------------------------------------------------

    @staticmethod
    def _build_feature_row(
        bytes_in: int, bytes_out: int, duration: int
    ) -> Dict[str, float]:
        """Convert raw byte counts into the feature vector the model expects."""
        # Estimate packets (same heuristic used in training data generation)
        pkts_in = max(1, bytes_in // NORMAL_PKT_SIZE) if bytes_in > 0 else 0
        pkts_out = max(1, bytes_out // NORMAL_PKT_SIZE) if bytes_out > 0 else 0

        bytes_per_sec_in = round(bytes_in / duration, 2)
        bytes_per_sec_out = round(bytes_out / duration, 2)

        pkt_size_avg_in = round(bytes_in / max(1, pkts_in), 2)
        pkt_size_avg_out = round(bytes_out / max(1, pkts_out), 2)

        byte_ratio = round(bytes_out / (bytes_in + 1), 6)
        pkt_ratio = round(pkts_out / (pkts_in + 1), 6)

        return {
            "bytes_in": bytes_in,
            "bytes_out": bytes_out,
            "pkts_in": pkts_in,
            "pkts_out": pkts_out,
            "duration": duration,
            "bytes_per_sec_in": bytes_per_sec_in,
            "bytes_per_sec_out": bytes_per_sec_out,
            "pkt_size_avg_in": pkt_size_avg_in,
            "pkt_size_avg_out": pkt_size_avg_out,
            "byte_ratio": byte_ratio,
            "pkt_ratio": pkt_ratio,
        }
