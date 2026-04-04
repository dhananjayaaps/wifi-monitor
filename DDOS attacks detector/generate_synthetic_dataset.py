#!/usr/bin/env python3
"""Generate a synthetic TON-IoT-style dataset for normal/dos/ddos."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Dict, Iterable, List

import numpy as np
import pandas as pd


@dataclass
class ColumnRules:
    clamp_min: float | None = None
    clamp_max: float | None = None
    integer_like: bool = False


def _infer_integer_like(series: pd.Series) -> bool:
    if not pd.api.types.is_numeric_dtype(series):
        return False
    sample = series.dropna().head(200)
    if sample.empty:
        return False
    return np.all(np.isclose(sample, np.round(sample)))


def _build_rules(columns: Iterable[str], df: pd.DataFrame) -> Dict[str, ColumnRules]:
    rules: Dict[str, ColumnRules] = {}
    for col in columns:
        rules[col] = ColumnRules(integer_like=_infer_integer_like(df[col]))

    # Common network column clamps
    for col in columns:
        lower = None
        upper = None
        if col in {"src_port", "dst_port"}:
            lower, upper = 0, 65535
        elif col in {"duration"}:
            lower = 0
        elif any(token in col for token in ["bytes", "pkts"]):
            lower = 0

        if lower is not None or upper is not None:
            rules[col].clamp_min = lower
            rules[col].clamp_max = upper
    return rules


def _apply_noise(df: pd.DataFrame, numeric_cols: List[str], noise_scale: float) -> pd.DataFrame:
    noisy = df.copy()
    rules = _build_rules(numeric_cols, df)
    for col in numeric_cols:
        col_std = df[col].std(skipna=True)
        if pd.isna(col_std) or col_std == 0:
            col_std = 1.0
        noise = np.random.normal(0, col_std * noise_scale, size=len(df))
        noisy[col] = df[col] + noise

        rule = rules[col]
        if rule.integer_like:
            noisy[col] = np.round(noisy[col])
        if rule.clamp_min is not None:
            noisy[col] = noisy[col].clip(lower=rule.clamp_min)
        if rule.clamp_max is not None:
            noisy[col] = noisy[col].clip(upper=rule.clamp_max)
    return noisy


def _synthesize_class(df: pd.DataFrame, size: int, noise_scale: float) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    sampled = df.sample(n=size, replace=True, random_state=None).reset_index(drop=True)
    numeric_cols = sampled.select_dtypes(include=["number"]).columns.tolist()
    numeric_cols = [c for c in numeric_cols if c not in {"label"}]
    return _apply_noise(sampled, numeric_cols, noise_scale=noise_scale)


def generate_synthetic_dataset(
    input_path: str,
    output_path: str,
    samples_per_class: int,
    noise_scale: float,
    seed: int,
) -> None:
    np.random.seed(seed)

    df = pd.read_csv(input_path)
    if "type" not in df.columns:
        raise ValueError("Input dataset must contain a 'type' column with normal/dos/ddos.")

    classes = ["normal", "dos", "ddos"]
    synthetic_parts = []
    for cls in classes:
        cls_df = df[df["type"].astype(str).str.lower() == cls]
        if cls_df.empty:
            print(f"Warning: no rows found for class '{cls}'.")
            continue
        synthetic_parts.append(_synthesize_class(cls_df, samples_per_class, noise_scale))

    if not synthetic_parts:
        raise ValueError("No synthetic samples were generated. Check class labels.")

    synthetic = pd.concat(synthetic_parts, ignore_index=True)
    synthetic.to_csv(output_path, index=False)
    print(f"Wrote {len(synthetic)} rows to {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic TON-IoT dataset.")
    parser.add_argument("--input", required=True, help="Path to ton-iot.csv")
    parser.add_argument("--output", required=True, help="Path to write synthetic CSV")
    parser.add_argument("--samples-per-class", type=int, default=5000)
    parser.add_argument("--noise-scale", type=float, default=0.05)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    generate_synthetic_dataset(
        input_path=args.input,
        output_path=args.output,
        samples_per_class=args.samples_per_class,
        noise_scale=args.noise_scale,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()
