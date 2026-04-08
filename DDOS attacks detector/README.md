# DDoS Attacks Detector

This folder contains scripts to generate a synthetic dataset and train an ML model that classifies traffic as `normal`, `dos`, or `ddos`.

The feature set is designed to match what the **pi-agent** can actually collect at runtime (byte counts, packet estimates, rates, ratios) — so the trained model works end-to-end with real or simulated pi-agent data.

## Install dependencies

```bash
pip install pandas numpy scikit-learn joblib
```

## 1) Generate synthetic data (no input file needed)

```bash
python generate_synthetic_dataset.py --output synthetic_ddos_dataset.csv --samples-per-class 5000
```

## 2) Train a model

```bash
python train_ddos_model.py --input synthetic_ddos_dataset.csv --model-out ddos_model.joblib
```

## 3) Run predictions on a CSV

```bash
python predict_ddos.py --input synthetic_ddos_dataset.csv --model ddos_model.joblib --output predictions.csv
```

## 4) Test with the simulation script (no backend needed)

```bash
cd ../pi-agent
python scripts/simulate_ddos_alerts.py --mode local --model ../ddos_model.joblib --count 20
```

## 5) Copy trained model to pi-agent

```bash
cp ddos_model.joblib ../pi-agent/ddos_model.joblib
```

Then set `ddos_detector.enabled: true` and `ddos_detector.model_path: "ddos_model.joblib"` in `pi-agent/config.yaml`.

## Features used

| Feature | Description |
|---------|-------------|
| `bytes_in` | Bytes downloaded by the device |
| `bytes_out` | Bytes uploaded by the device |
| `pkts_in` | Estimated inbound packets |
| `pkts_out` | Estimated outbound packets |
| `duration` | Collection interval (seconds) |
| `bytes_per_sec_in` | Inbound byte rate |
| `bytes_per_sec_out` | Outbound byte rate |
| `pkt_size_avg_in` | Average inbound packet size |
| `pkt_size_avg_out` | Average outbound packet size |
| `byte_ratio` | bytes_out / (bytes_in + 1) |
| `pkt_ratio` | pkts_out / (pkts_in + 1) |
