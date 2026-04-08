#!/usr/bin/env python3
"""
Generate a fully synthetic dataset for DDoS/DoS detection.

Creates realistic network traffic patterns from scratch — no external
input file required.  The features match what the pi-agent collector
can actually provide so the trained model works end-to-end.

Features produced (per observation interval):
  bytes_in        – bytes downloaded by a device
  bytes_out       – bytes uploaded by a device
  pkts_in         – estimated inbound packets
  pkts_out        – estimated outbound packets
  duration        – collection interval in seconds
  bytes_per_sec_in  – bytes_in / duration
  bytes_per_sec_out – bytes_out / duration
  pkt_size_avg_in   – avg inbound packet size
  pkt_size_avg_out  – avg outbound packet size
  byte_ratio      – bytes_out / (bytes_in + 1)
  pkt_ratio       – pkts_out / (pkts_in + 1)
  type            – label: normal / dos / ddos
"""

from __future__ import annotations

import argparse
from typing import List

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Traffic profile generators
# ---------------------------------------------------------------------------

def _gen_normal(n: int, rng: np.random.Generator) -> pd.DataFrame:
    """Normal browsing / streaming / IoT idle traffic."""
    duration = rng.choice([10, 15, 30, 60], size=n)

    # Moderate, balanced traffic
    bytes_in = rng.integers(1_000, 5_000_000, size=n)
    bytes_out = rng.integers(500, 1_000_000, size=n)

    # Realistic packet sizes (500-1500 bytes avg)
    pkt_size_in = rng.integers(400, 1500, size=n).astype(float)
    pkt_size_out = rng.integers(200, 1400, size=n).astype(float)

    pkts_in = np.maximum(1, (bytes_in / pkt_size_in).astype(int))
    pkts_out = np.maximum(1, (bytes_out / pkt_size_out).astype(int))

    return _build_df(bytes_in, bytes_out, pkts_in, pkts_out, duration, "normal")


def _gen_dos(n: int, rng: np.random.Generator) -> pd.DataFrame:
    """
    DoS pattern — single source flooding a target.

    Characteristics:
      • Very high outbound bytes or very high inbound bytes
      • Many small packets (SYN floods, UDP floods)
      • Extreme byte ratio (heavily skewed one direction)
    """
    duration = rng.choice([10, 15, 30], size=n)

    # ~60% are outbound floods (attacker), ~40% inbound floods (victim)
    is_attacker = rng.random(n) < 0.6

    bytes_out = np.where(
        is_attacker,
        rng.integers(10_000_000, 200_000_000, size=n),   # huge upload
        rng.integers(500, 500_000, size=n),               # minimal upload
    )
    bytes_in = np.where(
        is_attacker,
        rng.integers(500, 500_000, size=n),               # minimal download
        rng.integers(10_000_000, 200_000_000, size=n),    # huge download
    )

    # Small packets — SYN/UDP floods use 40-200 byte packets
    pkt_size_out = np.where(
        is_attacker,
        rng.integers(40, 200, size=n),
        rng.integers(300, 1400, size=n),
    ).astype(float)
    pkt_size_in = np.where(
        is_attacker,
        rng.integers(300, 1400, size=n),
        rng.integers(40, 200, size=n),
    ).astype(float)

    pkts_out = np.maximum(1, (bytes_out / pkt_size_out).astype(int))
    pkts_in = np.maximum(1, (bytes_in / pkt_size_in).astype(int))

    return _build_df(bytes_in, bytes_out, pkts_in, pkts_out, duration, "dos")


def _gen_ddos(n: int, rng: np.random.Generator) -> pd.DataFrame:
    """
    DDoS pattern — distributed attack, many sources to one victim.

    Characteristics:
      • Extremely high inbound bytes & packet counts
      • Very small inbound packets (amplification / reflection)
      • Very high packet-per-second rates
    """
    duration = rng.choice([10, 15, 30], size=n)

    # Massive inbound flood
    bytes_in = rng.integers(50_000_000, 500_000_000, size=n)
    bytes_out = rng.integers(100, 200_000, size=n)  # almost no outbound

    # Tiny packets — amplification attacks
    pkt_size_in = rng.integers(40, 150, size=n).astype(float)
    pkt_size_out = rng.integers(200, 1000, size=n).astype(float)

    pkts_in = np.maximum(1, (bytes_in / pkt_size_in).astype(int))
    pkts_out = np.maximum(1, (bytes_out / pkt_size_out).astype(int))

    return _build_df(bytes_in, bytes_out, pkts_in, pkts_out, duration, "ddos")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_df(
    bytes_in: np.ndarray,
    bytes_out: np.ndarray,
    pkts_in: np.ndarray,
    pkts_out: np.ndarray,
    duration: np.ndarray,
    label: str,
) -> pd.DataFrame:
    """Assemble a DataFrame with derived features."""
    df = pd.DataFrame({
        "bytes_in": bytes_in.astype(int),
        "bytes_out": bytes_out.astype(int),
        "pkts_in": pkts_in.astype(int),
        "pkts_out": pkts_out.astype(int),
        "duration": duration.astype(int),
    })

    df["bytes_per_sec_in"] = (df["bytes_in"] / df["duration"]).round(2)
    df["bytes_per_sec_out"] = (df["bytes_out"] / df["duration"]).round(2)
    df["pkt_size_avg_in"] = (df["bytes_in"] / df["pkts_in"].clip(lower=1)).round(2)
    df["pkt_size_avg_out"] = (df["bytes_out"] / df["pkts_out"].clip(lower=1)).round(2)
    df["byte_ratio"] = (df["bytes_out"] / (df["bytes_in"] + 1)).round(6)
    df["pkt_ratio"] = (df["pkts_out"] / (df["pkts_in"] + 1)).round(6)
    df["type"] = label

    return df


def _add_noise(df: pd.DataFrame, noise_scale: float, rng: np.random.Generator) -> pd.DataFrame:
    """Add Gaussian noise to numeric columns and reclamp."""
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    noisy = df.copy()
    for col in numeric_cols:
        std = df[col].std()
        if pd.isna(std) or std == 0:
            std = 1.0
        noise = rng.normal(0, std * noise_scale, size=len(df))
        noisy[col] = df[col] + noise
        # Keep non-negative for all our features
        noisy[col] = noisy[col].clip(lower=0)
        # Re-round integer-like columns
        if col in {"bytes_in", "bytes_out", "pkts_in", "pkts_out", "duration"}:
            noisy[col] = np.maximum(1, np.round(noisy[col])).astype(int)

    # Recompute derived features after noise
    noisy["bytes_per_sec_in"] = (noisy["bytes_in"] / noisy["duration"].clip(lower=1)).round(2)
    noisy["bytes_per_sec_out"] = (noisy["bytes_out"] / noisy["duration"].clip(lower=1)).round(2)
    noisy["pkt_size_avg_in"] = (noisy["bytes_in"] / noisy["pkts_in"].clip(lower=1)).round(2)
    noisy["pkt_size_avg_out"] = (noisy["bytes_out"] / noisy["pkts_out"].clip(lower=1)).round(2)
    noisy["byte_ratio"] = (noisy["bytes_out"] / (noisy["bytes_in"] + 1)).round(6)
    noisy["pkt_ratio"] = (noisy["pkts_out"] / (noisy["pkts_in"] + 1)).round(6)

    return noisy


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

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


def generate_synthetic_dataset(
    output_path: str,
    samples_per_class: int = 5000,
    noise_scale: float = 0.05,
    seed: int = 42,
) -> pd.DataFrame:
    """Generate a balanced synthetic dataset with normal / dos / ddos traffic."""
    rng = np.random.default_rng(seed)

    normal_df = _gen_normal(samples_per_class, rng)
    dos_df = _gen_dos(samples_per_class, rng)
    ddos_df = _gen_ddos(samples_per_class, rng)

    combined = pd.concat([normal_df, dos_df, ddos_df], ignore_index=True)

    # Add noise for variety
    combined = _add_noise(combined, noise_scale, rng)

    # Shuffle
    combined = combined.sample(frac=1, random_state=seed).reset_index(drop=True)

    combined.to_csv(output_path, index=False)
    print(f"✓ Generated {len(combined)} rows ({samples_per_class} per class) → {output_path}")
    return combined


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a fully synthetic DDoS detection dataset (no input file needed)."
    )
    parser.add_argument(
        "--output", default="synthetic_ddos_dataset.csv",
        help="Path to write the synthetic CSV (default: synthetic_ddos_dataset.csv)",
    )
    parser.add_argument("--samples-per-class", type=int, default=5000)
    parser.add_argument("--noise-scale", type=float, default=0.05)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    generate_synthetic_dataset(
        output_path=args.output,
        samples_per_class=args.samples_per_class,
        noise_scale=args.noise_scale,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()
