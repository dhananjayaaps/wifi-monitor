#!/usr/bin/env python3
"""Train a DDoS detector model for normal/dos/ddos."""

from __future__ import annotations

import argparse
from typing import List

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


DROP_DEFAULT = {
    "label",
    "src_ip",
    "dst_ip",
    "dns_query",
    "ssl_subject",
    "ssl_issuer",
    "http_uri",
    "http_user_agent",
    "http_orig_mime_types",
    "http_resp_mime_types",
    "weird_name",
    "weird_addl",
}


def _build_features(df: pd.DataFrame, drop_cols: List[str]) -> pd.DataFrame:
    drop = set(drop_cols)
    if "type" in df.columns:
        drop.add("type")
    return df.drop(columns=[c for c in drop if c in df.columns])


def train_model(input_path: str, model_out: str, test_size: float, seed: int, drop_cols: List[str]) -> None:
    df = pd.read_csv(input_path)
    if "type" not in df.columns:
        raise ValueError("Input dataset must contain a 'type' column with normal/dos/ddos.")

    df = df.dropna(subset=["type"])
    y = df["type"].astype(str).str.lower()
    X = _build_features(df, drop_cols)

    categorical_cols = X.select_dtypes(include=["object"]).columns.tolist()
    numeric_cols = [c for c in X.columns if c not in categorical_cols]

    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    numeric_pipeline = Pipeline(
        steps=[("imputer", SimpleImputer(strategy="median"))]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("categorical", categorical_pipeline, categorical_cols),
            ("numeric", numeric_pipeline, numeric_cols),
        ]
    )

    model = RandomForestClassifier(
        n_estimators=300,
        random_state=seed,
        class_weight="balanced",
        n_jobs=-1,
    )

    pipeline = Pipeline(steps=[("preprocessor", preprocessor), ("model", model)])

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=seed, stratify=y
    )

    pipeline.fit(X_train, y_train)
    preds = pipeline.predict(X_test)

    print("Classification report:")
    print(classification_report(y_test, preds, digits=4))
    print("Confusion matrix:")
    print(confusion_matrix(y_test, preds))

    joblib.dump(pipeline, model_out)
    print(f"Saved model to {model_out}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Train a DDoS detector model.")
    parser.add_argument("--input", required=True, help="Path to training CSV")
    parser.add_argument("--model-out", default="ddos_model.joblib")
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--include-ip",
        action="store_true",
        help="Include src_ip and dst_ip columns in training.",
    )
    parser.add_argument(
        "--drop-cols",
        nargs="*",
        default=[],
        help="Additional columns to drop.",
    )
    args = parser.parse_args()

    drop_cols = set(DROP_DEFAULT).union(args.drop_cols)
    if args.include_ip:
        drop_cols.discard("src_ip")
        drop_cols.discard("dst_ip")

    train_model(
        input_path=args.input,
        model_out=args.model_out,
        test_size=args.test_size,
        seed=args.seed,
        drop_cols=sorted(drop_cols),
    )


if __name__ == "__main__":
    main()
