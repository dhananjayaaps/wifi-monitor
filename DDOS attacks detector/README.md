# DDoS Attacks Detector

This folder contains scripts to generate a synthetic dataset and train a model that classifies traffic as `normal`, `dos`, or `ddos`.

## Install dependencies

```bash
pip install pandas numpy scikit-learn joblib
```

## 1) Generate synthetic data

```bash
python generate_synthetic_dataset.py --input /path/to/ton-iot.csv --output synthetic_ton_iot.csv --samples-per-class 5000
```

## 2) Train a model

```bash
python train_ddos_model.py --input synthetic_ton_iot.csv --model-out ddos_model.joblib
```

## 3) Run predictions

```bash
python predict_ddos.py --input /path/to/ton-iot.csv --model ddos_model.joblib --output predictions.csv
```

## Notes

- The training script drops high-cardinality fields like IPs and URIs by default. Use `--include-ip` to keep IPs.
- The synthetic generator bootstraps existing rows and adds numeric noise to widen the dataset distribution.
