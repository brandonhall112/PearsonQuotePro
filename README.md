# Pearson Quote Pro (first pass)

This repo is a first-pass scaffold for **Pearson Quote Pro**, built on the deployed **Pearson Commissioning Pro v1.1 (PCP)** logic and print styling.

## What works in this first pass
- CTO tab embeds PCP v1.1 UI and print preview (same behavior).
- ETO + Reactive tabs provide a Time & Material grid (days + hours/day + rate key).
- Reactive includes a Scope of Work (SOW) field that prints **above** the line item table.

## Run locally
```bash
pip install -r requirements.txt
python main.py
```

## Build onefile EXE
- Spec: `build/PearsonQuotePro_ONEFILE.spec`
- GitHub workflow: `.github/workflows/build-windows-quotepro-onefile.yml`
