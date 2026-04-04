#!/usr/bin/env python3
"""Run inference with a trained DDoS detector model."""

from __future__ import annotations

import argparse

import joblib
import pandas as pd


def predict(input_path: str, model_path: str, output_path: str) -> None:
    model = joblib.load(model_path)
    df = pd.read_csv(input_path)

    if "type" in df.columns:
        features = df.drop(columns=["type"])
    else:
        features = df

    preds = model.predict(features)
    output = df.copy()
    output["predicted_type"] = preds

    if hasattr(model, "predict_proba"):
        probas = model.predict_proba(features)
        for idx, cls in enumerate(model.classes_):
            output[f"prob_{cls}"] = probas[:, idx]

    output.to_csv(output_path, index=False)
    print(f"Wrote predictions to {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Predict normal/dos/ddos.")
    parser.add_argument("--input", required=True, help="Path to input CSV")
    parser.add_argument("--model", required=True, help="Path to ddos_model.joblib")
    parser.add_argument("--output", default="predictions.csv")
    args = parser.parse_args()

    predict(args.input, args.model, args.output)


if __name__ == "__main__":
    main()
