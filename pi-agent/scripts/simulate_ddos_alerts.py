#!/usr/bin/env python3
"""
Simulate realistic DDoS/DoS traffic through the pi-agent pipeline.

This script can operate in two modes:

1. **Local model test** (--mode local):
   Generates synthetic traffic feature vectors, runs them through the
   trained ML model, and prints the predictions.  No backend required.

2. **Backend alert test** (--mode backend):
   Sends pre-built alert payloads to the backend /agents/alerts endpoint
   to verify the alert ingestion pipeline.

Usage examples
--------------
# Test the model locally (no backend needed):
  python simulate_ddos_alerts.py --mode local --model ../ddos_model.joblib

# Send alerts to backend:
  python simulate_ddos_alerts.py --mode backend --email admin@wifi.com --password admin123
"""

from __future__ import annotations

import argparse
import random
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

# ---------------------------------------------------------------------------
# Local model testing
# ---------------------------------------------------------------------------

def _generate_traffic_sample(
    traffic_type: str, duration: int = 30
) -> Dict[str, float]:
    """Generate a single traffic feature row matching the model's expectations."""
    rng = np.random.default_rng()

    if traffic_type == "normal":
        bytes_in = int(rng.integers(1_000, 5_000_000))
        bytes_out = int(rng.integers(500, 1_000_000))
        pkt_size_in = int(rng.integers(400, 1500))
        pkt_size_out = int(rng.integers(200, 1400))
    elif traffic_type == "dos":
        # DoS: attacker with massive outbound
        bytes_out = int(rng.integers(10_000_000, 200_000_000))
        bytes_in = int(rng.integers(500, 500_000))
        pkt_size_out = int(rng.integers(40, 200))  # small flood packets
        pkt_size_in = int(rng.integers(300, 1400))
    elif traffic_type == "ddos":
        # DDoS victim: massive inbound, tiny packets
        bytes_in = int(rng.integers(50_000_000, 500_000_000))
        bytes_out = int(rng.integers(100, 200_000))
        pkt_size_in = int(rng.integers(40, 150))
        pkt_size_out = int(rng.integers(200, 1000))
    else:
        raise ValueError(f"Unknown traffic type: {traffic_type}")

    pkts_in = max(1, bytes_in // pkt_size_in)
    pkts_out = max(1, bytes_out // pkt_size_out)

    return {
        "bytes_in": bytes_in,
        "bytes_out": bytes_out,
        "pkts_in": pkts_in,
        "pkts_out": pkts_out,
        "duration": duration,
        "bytes_per_sec_in": round(bytes_in / duration, 2),
        "bytes_per_sec_out": round(bytes_out / duration, 2),
        "pkt_size_avg_in": round(bytes_in / max(1, pkts_in), 2),
        "pkt_size_avg_out": round(bytes_out / max(1, pkts_out), 2),
        "byte_ratio": round(bytes_out / (bytes_in + 1), 6),
        "pkt_ratio": round(pkts_out / (pkts_in + 1), 6),
    }


def run_local_test(model_path: str, count: int) -> None:
    """Run the model locally on synthetic traffic and print results."""
    import joblib
    import pandas as pd

    print(f"Loading model from {model_path} ...")
    model = joblib.load(model_path)

    traffic_types = ["normal", "dos", "ddos"]
    rows = []
    labels = []

    for _ in range(count):
        ttype = random.choice(traffic_types)
        row = _generate_traffic_sample(ttype)
        rows.append(row)
        labels.append(ttype)

    df = pd.DataFrame(rows)
    preds = model.predict(df)
    probas = model.predict_proba(df) if hasattr(model, "predict_proba") else None

    correct = 0
    print(f"\n{'#':>3}  {'Actual':<8} {'Predicted':<8} {'Confidence':>10}  {'Match':>5}")
    print("-" * 50)
    for i, (actual, pred) in enumerate(zip(labels, preds)):
        conf = f"{probas[i].max():.3f}" if probas is not None else "N/A"
        match = "✓" if actual == pred else "✗"
        if actual == pred:
            correct += 1
        print(f"{i+1:>3}  {actual:<8} {pred:<8} {conf:>10}  {match:>5}")

    accuracy = correct / len(labels) * 100
    print(f"\nAccuracy: {correct}/{len(labels)} ({accuracy:.1f}%)")

    # Summary by class
    print("\nPer-class breakdown:")
    for ttype in traffic_types:
        indices = [i for i, l in enumerate(labels) if l == ttype]
        if not indices:
            continue
        class_correct = sum(1 for i in indices if preds[i] == ttype)
        print(f"  {ttype}: {class_correct}/{len(indices)} correct")


# ---------------------------------------------------------------------------
# Backend alert testing
# ---------------------------------------------------------------------------

def _get_api_key_from_login(base_url: str, email: str, password: str, agent_name: str) -> str:
    import requests

    login_url = f"{base_url.rstrip('/')}/auth/login"
    response = requests.post(
        login_url,
        json={"email": email, "password": password},
        timeout=10,
    )
    response.raise_for_status()
    token = response.json().get("access_token")
    if not token:
        raise RuntimeError("Login succeeded but no access_token in response")

    register_url = f"{base_url.rstrip('/')}/agents/register"
    reg_resp = requests.post(
        register_url,
        json={"name": agent_name},
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    if reg_resp.status_code in (200, 201):
        api_key = reg_resp.json().get("data", {}).get("api_key")
        if api_key:
            return api_key

    # Fallback: try GET key endpoint
    key_url = f"{base_url.rstrip('/')}/agents/key?name={agent_name}"
    key_resp = requests.get(
        key_url,
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    key_resp.raise_for_status()
    api_key = key_resp.json().get("data", {}).get("api_key")
    if not api_key:
        raise RuntimeError("Agent key not found in response")
    return api_key


def build_alerts(
    mac_list: List[str], count: int, attack_type: Optional[str]
) -> List[Dict]:
    alerts = []
    for _ in range(count):
        mac = random.choice(mac_list).upper()
        attack = attack_type or random.choice(["dos", "ddos"])
        confidence = round(random.uniform(0.75, 0.99), 3)
        total_bytes = random.randint(10_000_000, 200_000_000)
        alerts.append({
            "mac_address": mac,
            "alert_type": attack,
            "confidence": confidence,
            "total_bytes": total_bytes,
        })
    return alerts


def sync_devices(base_url: str, api_key: str, macs: List[str]) -> None:
    import requests

    url = f"{base_url.rstrip('/')}/agents/devices"
    headers = {
        "Content-Type": "application/json",
        "X-Agent-API-Key": api_key,
    }
    devices = []
    for idx, mac in enumerate(macs, start=1):
        devices.append({
            "mac_address": mac.upper(),
            "ip_address": f"192.168.1.{100 + idx}",
            "hostname": f"sim-device-{idx}",
            "manufacturer": "Simulated",
            "device_type": "simulated",
        })

    response = requests.post(url, json={"devices": devices}, headers=headers, timeout=10)
    print(f"Device sync: {response.status_code} — {response.text}")


def send_alerts(base_url: str, api_key: str, alerts: List[Dict]) -> None:
    import requests

    url = f"{base_url.rstrip('/')}/agents/alerts"
    headers = {
        "Content-Type": "application/json",
        "X-Agent-API-Key": api_key,
    }
    payload = {"alerts": alerts}
    response = requests.post(url, json=payload, headers=headers, timeout=10)
    print(f"Alert response: {response.status_code} — {response.text}")


def run_backend_test(args) -> None:
    import requests

    api_key = args.api_key
    if not api_key:
        if not args.email or not args.password:
            raise SystemExit("Provide --api-key or --email/--password")
        api_key = _get_api_key_from_login(
            args.base_url, args.email, args.password, args.agent_name
        )
        print(f"✓ Obtained API key")

    macs = args.macs or ["AA:BB:CC:DD:EE:01", "AA:BB:CC:DD:EE:02"]

    if args.ensure_devices:
        sync_devices(args.base_url, api_key, macs)

    for i in range(args.repeat):
        alerts = build_alerts(macs, args.count, args.attack_type)
        print(f"\nBatch {i + 1}/{args.repeat} — {len(alerts)} alert(s)")
        for a in alerts:
            print(f"  {a['alert_type'].upper()} → {a['mac_address']} (conf={a['confidence']})")
        send_alerts(args.base_url, api_key, alerts)
        if i + 1 < args.repeat:
            time.sleep(args.interval)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Simulate DDoS/DoS traffic for testing."
    )
    parser.add_argument(
        "--mode",
        choices=["local", "backend"],
        default="local",
        help="'local' = test model offline, 'backend' = send alerts to API",
    )

    # Local mode options
    parser.add_argument(
        "--model",
        default="../ddos_model.joblib",
        help="Path to trained model (local mode)",
    )
    parser.add_argument(
        "--count", type=int, default=10,
        help="Number of samples/alerts to generate",
    )

    # Backend mode options
    parser.add_argument("--base-url", default="http://localhost:5000/api/v1")
    parser.add_argument("--api-key", help="Agent API key")
    parser.add_argument("--email", help="Login email")
    parser.add_argument("--password", help="Login password")
    parser.add_argument("--agent-name", default="pi-agent")
    parser.add_argument("--ensure-devices", action="store_true")
    parser.add_argument(
        "--mac", action="append", dest="macs", default=[],
        help="Target MAC (repeat for multiple)",
    )
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--interval", type=int, default=5)
    parser.add_argument(
        "--attack-type", choices=["dos", "ddos"],
        help="Force a single alert type",
    )

    args = parser.parse_args()

    if args.mode == "local":
        run_local_test(args.model, args.count)
    else:
        run_backend_test(args)


if __name__ == "__main__":
    main()
