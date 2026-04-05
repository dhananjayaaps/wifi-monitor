#!/usr/bin/env python3
"""Simulate DDoS/DOS alerts for testing backend integration."""

from __future__ import annotations

import argparse
import random
import time
from typing import List, Dict

import requests


def build_alerts(mac_list: List[str], count: int, attack_type: str | None) -> List[Dict[str, object]]:
    alerts = []
    for _ in range(count):
        mac = random.choice(mac_list).upper()
        if attack_type:
            attack = attack_type
        else:
            attack = random.choice(["dos", "ddos"])
        confidence = round(random.uniform(0.7, 0.99), 3)
        total_bytes = random.randint(2_000_000, 50_000_000)
        alerts.append({
            "mac_address": mac,
            "alert_type": attack,
            "confidence": confidence,
            "total_bytes": total_bytes,
        })
    return alerts


def _get_api_key_from_login(base_url: str, email: str, password: str, agent_name: str) -> str:
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


def send_alerts(base_url: str, api_key: str, alerts: List[Dict[str, object]], cooldown: int) -> None:
    url = f"{base_url.rstrip('/')}/agents/alerts"
    headers = {
        "Content-Type": "application/json",
        "X-Agent-API-Key": api_key,
    }
    payload = {
        "alerts": alerts,
        "cooldown_seconds": cooldown,
    }

    response = requests.post(url, json=payload, headers=headers, timeout=10)
    print(f"Status: {response.status_code}")
    print(response.text)


def sync_devices(base_url: str, api_key: str, macs: List[str]) -> None:
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
    print(f"Device sync status: {response.status_code}")
    print(response.text)


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulate DDoS/DOS alerts.")
    parser.add_argument("--base-url", default="http://localhost:5000/api/v1")
    parser.add_argument("--api-key", help="Agent API key (X-Agent-API-Key)")
    parser.add_argument("--email", help="Login email (if api-key not provided)")
    parser.add_argument("--password", help="Login password (if api-key not provided)")
    parser.add_argument("--agent-name", default="pi-agent", help="Agent name for key lookup")
    parser.add_argument(
        "--ensure-devices",
        action="store_true",
        help="Sync devices before sending alerts",
    )
    parser.add_argument(
        "--mac",
        action="append",
        dest="macs",
        default=[],
        help="Target MAC address (repeat for multiple)",
    )
    parser.add_argument("--count", type=int, default=1, help="Alerts per batch")
    parser.add_argument("--cooldown", type=int, default=300, help="Cooldown seconds for backend")
    parser.add_argument("--repeat", type=int, default=1, help="How many batches to send")
    parser.add_argument("--interval", type=int, default=5, help="Seconds between batches")
    parser.add_argument(
        "--attack-type",
        choices=["dos", "ddos"],
        help="Force a single alert type",
    )
    args = parser.parse_args()

    if not args.macs:
        args.macs = ["AA:BB:CC:DD:EE:01"]

    api_key = args.api_key
    if not api_key:
        if not args.email or not args.password:
            raise SystemExit("Provide --api-key or --email/--password to fetch the agent key")
        api_key = _get_api_key_from_login(args.base_url, args.email, args.password, args.agent_name)
        print("Fetched agent API key successfully")

    if args.ensure_devices:
        sync_devices(args.base_url, api_key, args.macs)

    for i in range(args.repeat):
        alerts = build_alerts(args.macs, args.count, args.attack_type)
        print(f"Sending batch {i + 1}/{args.repeat} with {len(alerts)} alerts")
        send_alerts(args.base_url, api_key, alerts, args.cooldown)
        if i + 1 < args.repeat:
            time.sleep(args.interval)


if __name__ == "__main__":
    main()
