# DDoS/DoS Testing Scripts

This folder contains scripts for testing the DDoS detection pipeline end-to-end.

## Overview

| Script | Purpose | When to Use |
|--------|---------|-------------|
| `simulate_ddos_alerts.py` | Test the ML model or send mock alerts to backend | Quick validation without real traffic |
| `real_ddos_test.py` | Generate actual network traffic floods | Full pipeline testing with real packets |

---

## 1. `simulate_ddos_alerts.py`

Simulates DDoS detection without sending real network traffic. Has two modes:

### Mode: Local (Test the ML Model)

Test the trained model with synthetic traffic patterns — no backend needed.

```bash
# Test with 30 samples
python simulate_ddos_alerts.py --mode local --model ../../DDOS\ attacks\ detector/ddos_model.joblib --count 30

# Test with 50 samples
python simulate_ddos_alerts.py --mode local --model ../ddos_model.joblib --count 50
```

**Output:**
```
  #  Actual   Predicted Confidence  Match
--------------------------------------------------
  1  normal   normal        0.997      ✓
  2  ddos     ddos          0.813      ✓
  3  dos      dos           1.000      ✓
...
Accuracy: 28/30 (93.3%)
```

### Mode: Backend (Send Mock Alerts)

Send pre-built alert payloads to the backend `/agents/alerts` endpoint to verify the alert ingestion pipeline.

```bash
# Send 3 alerts (requires authentication)
python simulate_ddos_alerts.py --mode backend \
  --email admin@example.com \
  --password your_password \
  --count 3

# Send 10 DDoS alerts every 5 seconds for 3 rounds
python simulate_ddos_alerts.py --mode backend \
  --api-key YOUR_API_KEY \
  --count 10 \
  --attack-type ddos \
  --repeat 3 \
  --interval 5

# Use custom MAC addresses
python simulate_ddos_alerts.py --mode backend \
  --email admin@example.com \
  --password your_password \
  --macs AA:BB:CC:DD:EE:01 AA:BB:CC:DD:EE:02 AA:BB:CC:DD:EE:03 \
  --count 5
```

**Options:**
- `--base-url`: Backend URL (default: `http://localhost:5000/api/v1`)
- `--api-key`: Agent API key (preferred over email/password)
- `--email` / `--password`: Login credentials (obtains API key automatically)
- `--agent-name`: Agent name for registration (default: `pi-agent-test`)
- `--count`: Number of alerts per batch (default: 3)
- `--attack-type`: Force attack type (`dos` or `ddos`), otherwise random
- `--macs`: List of MAC addresses to use (default: 2 simulated MACs)
- `--repeat`: Number of batches to send (default: 1)
- `--interval`: Seconds between batches (default: 10)
- `--ensure-devices`: Sync devices before sending alerts

---

## 2. `real_ddos_test.py`

**⚠️ WARNING:** Generates **REAL network traffic floods**. Only use on networks you own or have permission to test.

### Safety Features
- ✅ Only allows targeting private IPs (10.x, 172.16-31.x, 192.168.x, 127.x)
- ✅ Requires explicit `--confirm` flag
- ✅ Duration capped at 120 seconds
- ✅ Stops cleanly on Ctrl+C

### Attack Types

| Attack | Description | Use Case |
|--------|-------------|----------|
| `udp_flood` | High-volume UDP packets (512-1400 bytes each) | Classic volumetric DoS |
| `syn_flood` | Rapid TCP SYN connection attempts | Half-open connection flood |
| `http_flood` | Rapid HTTP GET requests | Application-layer attack |
| `mixed` | UDP + SYN + HTTP simultaneously | Distributed attack simulation |

### Basic Usage

```bash
# UDP flood to localhost for 15 seconds
python real_ddos_test.py \
  --target 127.0.0.1 \
  --attack udp_flood \
  --duration 15 \
  --confirm

# SYN flood with 8 threads
python real_ddos_test.py \
  --target 192.168.1.100 \
  --attack syn_flood \
  --duration 20 \
  --threads 8 \
  --confirm

# HTTP flood to local web server
python real_ddos_test.py \
  --target 192.168.1.100 \
  --port 80 \
  --attack http_flood \
  --duration 30 \
  --confirm

# Mixed attack (most realistic)
python real_ddos_test.py \
  --target 192.168.1.100 \
  --attack mixed \
  --duration 30 \
  --confirm
```

### With ML Detection

Add `--detect` and `--model` to run the trained model on the traffic stats after the flood:

```bash
python real_ddos_test.py \
  --target 127.0.0.1 \
  --attack udp_flood \
  --duration 15 \
  --confirm \
  --detect \
  --model ../../DDOS\ attacks\ detector/ddos_model.joblib
```

**Output:**
```
============================================================
  DDoS/DoS Real Traffic Test
============================================================
  Target:   127.0.0.1:random
  Attack:   udp_flood
  Duration: 15s
  Threads:  4
  Detect:   YES
============================================================

  Packets: 45,233  |  Bytes: 52.1 MB  |  Rate: 3,015 pkt/s, 3.5 MB/s  |  Errors: 0
  Packets: 91,450  |  Bytes: 105.3 MB  |  Rate: 6,096 pkt/s, 7.0 MB/s  |  Errors: 0
...

============================================================
  FLOOD COMPLETE
============================================================
  Total packets:  137,892
  Total bytes:    158,923,445 (158.9 MB)
  Duration:       15.0s
  Avg rate:       9,192 pkt/s, 10.6 MB/s
  Errors:         0
============================================================

--- ML Model Detection ---
Prediction: DOS
   normal: 0.023 ██
      dos: 0.901 ███████████████████████████
     ddos: 0.076 ██

✓ ATTACK DETECTED: DOS with 90.1% confidence
  The pi-agent would send an alert to the backend for this traffic.

--- Victim perspective ---
Victim prediction: DDOS
   normal: 0.000 
      dos: 0.101 ███
     ddos: 0.899 ███████████████████████████

✓ VICTIM ATTACK DETECTED: DDOS with 89.9% confidence
```

### Full Options

```bash
python real_ddos_test.py \
  --target 192.168.1.100           # Target IP (required, must be private)
  --port 80                        # Target port (0=random for UDP/SYN)
  --attack udp_flood               # udp_flood | syn_flood | http_flood | mixed
  --duration 30                    # Duration in seconds (max 120)
  --threads 4                      # Number of attack threads
  --confirm                        # Required safety flag
  --detect                         # Run ML detection after flood
  --model ../ddos_model.joblib     # Path to trained model
```

---

## End-to-End Testing Workflow

### Scenario 1: Test Model Accuracy (No Network)

```bash
# Generate fresh dataset
cd ../../DDOS\ attacks\ detector
python generate_synthetic_dataset.py --samples-per-class 5000

# Train model
python train_ddos_model.py --input synthetic_ddos_dataset.csv

# Test model
cd ../pi-agent/scripts
python simulate_ddos_alerts.py --mode local --model ../../DDOS\ attacks\ detector/ddos_model.joblib --count 50
```

### Scenario 2: Test Backend Alert Pipeline (No Traffic)

```bash
# Start backend
cd ../../backend
python run.py

# Start admin frontend
cd ../admin-frontend
npm run dev

# Send mock alerts
cd ../pi-agent/scripts
python simulate_ddos_alerts.py --mode backend \
  --email admin@example.com \
  --password your_password \
  --count 5 \
  --repeat 3 \
  --interval 5

# Check the admin dashboard for alerts
```

### Scenario 3: Full Real Traffic Test

```bash
# 1. Start backend
cd ../../backend
python run.py

# 2. Start pi-agent on target device (e.g., Raspberry Pi)
cd ../pi-agent
# Edit config.yaml: set ddos_detector.enabled: true
python run.py

# 3. From attacker machine, run the flood
cd scripts
python real_ddos_test.py \
  --target 192.168.1.100 \
  --attack mixed \
  --duration 30 \
  --threads 8 \
  --confirm \
  --detect \
  --model ../../DDOS\ attacks\ detector/ddos_model.joblib

# 4. Check pi-agent logs for DDoS detection
tail -f ../logs/agent.log

# 5. Check admin dashboard for alerts
```

---

## Troubleshooting

### "Target is NOT a private IP address"
The script only allows targeting private networks for safety. Use:
- `127.0.0.1` (localhost)
- `192.168.x.x`
- `10.x.x.x`
- `172.16.x.x` to `172.31.x.x`

### "Traffic classified as NORMAL"
If the ML model doesn't detect the flood:
- Increase `--duration` (try 30-60 seconds)
- Increase `--threads` (try 8-16 threads)
- Use `--attack mixed` for multi-vector flood
- Make sure the model was trained on realistic data

### No alerts in backend
Check:
1. Pi-agent config: `ddos_detector.enabled: true`
2. Model path is correct in `config.yaml`
3. Pi-agent is authenticated (check logs)
4. Backend is running and reachable
5. Alert confidence exceeds `min_confidence` threshold (default 0.7)

### Permission denied (SYN flood on Windows)
Some attack types may need elevated privileges. Run PowerShell as Administrator:
```powershell
# Run as Administrator
cd pi-agent\scripts
python real_ddos_test.py --target 127.0.0.1 --attack syn_flood --duration 15 --confirm
```

---

## File Locations

```
pi-agent/
├── scripts/
│   ├── README.md                    ← You are here
│   ├── simulate_ddos_alerts.py      ← Mock traffic simulation
│   └── real_ddos_test.py            ← Real traffic generator
├── ddos_model.joblib                ← Trained ML model (copied from DDOS attacks detector/)
└── config.yaml                      ← Enable ddos_detector here

DDOS attacks detector/
├── generate_synthetic_dataset.py    ← Generate training data
├── train_ddos_model.py              ← Train the model
├── predict_ddos.py                  ← Batch prediction tool
├── ddos_model.joblib                ← Source model file
└── synthetic_ddos_dataset.csv       ← Training dataset
```

---

## Notes

- **Local testing** (`simulate_ddos_alerts.py --mode local`) is fast and safe for development
- **Backend testing** sends alerts without generating traffic — good for UI/API testing
- **Real traffic testing** (`real_ddos_test.py`) simulates actual attacks the pi-agent will detect
- The pi-agent must be running with `ddos_detector.enabled: true` to process real traffic
- Alert cooldown (default 5 minutes) prevents duplicate alerts for the same MAC + attack type

---

## Quick Reference

```bash
# Train model
cd ../../DDOS\ attacks\ detector
python generate_synthetic_dataset.py
python train_ddos_model.py

# Test model locally
cd ../pi-agent/scripts
python simulate_ddos_alerts.py --mode local --model ../../DDOS\ attacks\ detector/ddos_model.joblib --count 30

# Send mock alerts to backend
python simulate_ddos_alerts.py --mode backend --email admin@example.com --password pass --count 5

# Generate real flood + detect
python real_ddos_test.py --target 127.0.0.1 --attack udp_flood --duration 15 --confirm --detect --model ../../DDOS\ attacks\ detector/ddos_model.joblib

# Full mixed attack
python real_ddos_test.py --target 192.168.1.100 --attack mixed --duration 30 --threads 8 --confirm --detect
```
