"""DDoS detector wrapper for the Pi agent."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

import joblib
import pandas as pd


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
        self.feature_columns: Optional[List[str]] = None

        if self.enabled:
            self._load_model()

    def _load_model(self) -> None:
        try:
            self.model = joblib.load(self.model_path)
            preprocessor = getattr(self.model, "named_steps", {}).get("preprocessor")
            if preprocessor is not None and hasattr(preprocessor, "feature_names_in_"):
                self.feature_columns = list(preprocessor.feature_names_in_)
            elif hasattr(self.model, "feature_names_in_"):
                self.feature_columns = list(self.model.feature_names_in_)
            else:
                self.feature_columns = None
        except Exception:
            self.model = None
            self.feature_columns = None
            self.enabled = False

    def is_ready(self) -> bool:
        return self.enabled and self.model is not None

    def predict(self, stats: List[Dict[str, int]], devices: Dict[str, Dict[str, str]], interval_seconds: int) -> List[DetectionResult]:
        if not self.is_ready() or not stats:
            return []

        rows = []
        meta: List[Dict[str, int]] = []
        for stat in stats:
            mac = stat.get("mac_address")
            if not mac:
                continue
            device = devices.get(mac.upper(), {})
            row = self._build_row(stat, device, interval_seconds)
            if row:
                rows.append(row)
                meta.append({
                    "mac_address": mac,
                    "total_bytes": int(stat.get("bytes_uploaded", 0)) + int(stat.get("bytes_downloaded", 0)),
                })

        if not rows:
            return []

        df = pd.DataFrame(rows)
        preds = self.model.predict(df)
        confidences = None
        if hasattr(self.model, "predict_proba"):
            probas = self.model.predict_proba(df)
            confidences = probas.max(axis=1)

        results: List[DetectionResult] = []
        for idx, pred in enumerate(preds):
            confidence = float(confidences[idx]) if confidences is not None else 0.0
            results.append(DetectionResult(
                mac_address=meta[idx]["mac_address"],
                prediction=str(pred),
                confidence=confidence,
                total_bytes=meta[idx]["total_bytes"],
            ))

        return results

    def _build_row(self, stat: Dict[str, int], device: Dict[str, str], interval_seconds: int) -> Dict[str, object]:
        if self.feature_columns is None:
            return {}

        defaults = self._default_feature_values(interval_seconds)
        bytes_up = int(stat.get("bytes_uploaded", 0))
        bytes_down = int(stat.get("bytes_downloaded", 0))

        ip_address = (device.get("ip_address") or "0.0.0.0").strip()
        row = dict(defaults)

        # Common byte mappings
        for key in ["src_bytes", "src_ip_bytes"]:
            if key in row:
                row[key] = bytes_up
        for key in ["dst_bytes", "dst_ip_bytes"]:
            if key in row:
                row[key] = bytes_down

        # Packet estimates (rough)
        packets_up = max(1, bytes_up // 1500) if bytes_up > 0 else 0
        packets_down = max(1, bytes_down // 1500) if bytes_down > 0 else 0
        for key in ["src_pkts"]:
            if key in row:
                row[key] = packets_up
        for key in ["dst_pkts"]:
            if key in row:
                row[key] = packets_down

        if "src_ip" in row:
            row["src_ip"] = ip_address
        if "dst_ip" in row:
            row["dst_ip"] = "0.0.0.0"

        return row

    def _default_feature_values(self, interval_seconds: int) -> Dict[str, object]:
        now_ts = int(datetime.utcnow().timestamp())
        defaults: Dict[str, object] = {}
        for col in self.feature_columns or []:
            if col in {"ts"}:
                defaults[col] = now_ts
            elif col in {"proto"}:
                defaults[col] = "tcp"
            elif col in {"service"}:
                defaults[col] = "-"
            elif col in {"conn_state"}:
                defaults[col] = "S1"
            elif col in {"http_method"}:
                defaults[col] = "GET"
            elif col in {"http_version"}:
                defaults[col] = "1.1"
            elif col in {"weird_notice", "label"}:
                defaults[col] = "F"
            elif col in {
                "dns_query",
                "ssl_subject",
                "ssl_issuer",
                "http_uri",
                "http_user_agent",
                "http_orig_mime_types",
                "http_resp_mime_types",
                "weird_name",
                "weird_addl",
            }:
                defaults[col] = "-"
            elif col in {"duration"}:
                defaults[col] = max(1, int(interval_seconds))
            else:
                defaults[col] = 0

        return defaults
