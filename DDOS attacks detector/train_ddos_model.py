#!/usr/bin/env python3
"""
Train a DDoS / DoS detector model.

Works with the synthetic dataset produced by generate_synthetic_dataset.py.
The feature set is designed to match what the pi-agent can
actually provide at runtime (bytes, packets, rates, ratios).

Outputs a scikit-learn Pipeline saved as a joblib file.
"""

from __future__ import annotations

import argparse
from typing import List

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


# These are the features we expect — must match generate_synthetic_dataset.py
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


def train_model(
    input_path: str,
    model_out: str,
    test_size: float,
    seed: int,
) -> None:
    df = pd.read_csv(input_path)
    if "type" not in df.columns:
        raise ValueError("Input dataset must contain a 'type' column (normal/dos/ddos).")

    df = df.dropna(subset=["type"])
    y = df["type"].astype(str).str.lower()

    # Use only the known feature columns
    missing = [c for c in FEATURE_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing feature columns in input: {missing}")

    X = df[FEATURE_COLUMNS].copy()

    pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            (
                "model",
                RandomForestClassifier(
                    n_estimators=300,
                    max_depth=20,
                    random_state=seed,
                    class_weight="balanced",
                    n_jobs=-1,
                ),
            ),
        ]
    )

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=seed, stratify=y
    )

    pipeline.fit(X_train, y_train)
    preds = pipeline.predict(X_test)

    print("Classification Report:")
    print(classification_report(y_test, preds, digits=4))
    print("Confusion Matrix:")
    print(confusion_matrix(y_test, preds, labels=["normal", "dos", "ddos"]))

    # Store feature column list in the pipeline for runtime validation
    pipeline.feature_columns_ = FEATURE_COLUMNS

    joblib.dump(pipeline, model_out)
    print(f"\n✓ Saved model to {model_out}")

    # Quick sanity check — load and predict one row
    loaded = joblib.load(model_out)
    sample = X_test.iloc[:1]
    pred = loaded.predict(sample)
    proba = loaded.predict_proba(sample)
    print(f"  Sanity check: predicted={pred[0]}, confidence={proba.max():.3f}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Train a DDoS/DoS detector model.")
    parser.add_argument(
        "--input",
        default="synthetic_ddos_dataset.csv",
        help="Path to training CSV (default: synthetic_ddos_dataset.csv)",
    )
    parser.add_argument("--model-out", default="ddos_model.joblib")
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    train_model(
        input_path=args.input,
        model_out=args.model_out,
        test_size=args.test_size,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()
