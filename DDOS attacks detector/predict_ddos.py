#!/usr/bin/env python3
"""
Run inference with a trained DDoS detector model.

Accepts a CSV with the same feature columns used during training.
Adds predicted_type and per-class probability columns to the output.
"""

from __future__ import annotations

import argparse
from typing import List

import joblib
import pandas as pd


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


def predict(input_path: str, model_path: str, output_path: str) -> None:
    model = joblib.load(model_path)
    df = pd.read_csv(input_path)

    # Use only the feature columns the model was trained on
    feature_cols = getattr(model, "feature_columns_", FEATURE_COLUMNS)
    missing = [c for c in feature_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Input CSV is missing columns required by the model: {missing}")

    features = df[feature_cols]

    preds = model.predict(features)
    output = df.copy()
    output["predicted_type"] = preds

    if hasattr(model, "predict_proba"):
        probas = model.predict_proba(features)
        for idx, cls in enumerate(model.classes_):
            output[f"prob_{cls}"] = probas[:, idx]

    output.to_csv(output_path, index=False)
    print(f"✓ Wrote {len(output)} predictions to {output_path}")

    # Print summary
    print("\nPrediction summary:")
    print(output["predicted_type"].value_counts().to_string())


def main() -> None:
    parser = argparse.ArgumentParser(description="Predict normal/dos/ddos from traffic features.")
    parser.add_argument("--input", required=True, help="Path to input CSV")
    parser.add_argument("--model", default="ddos_model.joblib", help="Path to trained model")
    parser.add_argument("--output", default="predictions.csv")
    args = parser.parse_args()

    predict(args.input, args.model, args.output)


if __name__ == "__main__":
    main()
