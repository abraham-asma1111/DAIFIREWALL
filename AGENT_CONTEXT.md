# Dynamic AI Firewall — Project Context for AI Agent

## What This Project Is
A self-learning network firewall that uses Reinforcement Learning (PPO algorithm)
to detect and block cyberattacks in real time — including zero-day attacks it has
never seen before. Built as a SaaS platform targeting government, banks, and fintech
in Ethiopia and beyond.

## Target Customers
- Government ministries and agencies (INSA Ethiopia)
- Central Bank of Ethiopia (NBE)
- Commercial banks (CBE, Dashen, Awash, Bunna)
- Fintech and payment processors
- Telecom (Ethio Telecom)

## How It Works
1. A lightweight sensor agent runs on the customer's server
2. It captures network traffic and extracts features (NOT raw packets)
3. Features are sent to the SaaS backend
4. The RL agent makes a decision: ALLOW / BLOCK / RATE_LIMIT / FLAG_MONITOR
5. Decision is sent back to sensor which enforces it via iptables
6. Every decision is logged for audit and compliance
7. The agent continuously learns from new data

## Zero-Day Detection (Most Important Feature)
The system detects attacks it has NEVER seen before by:
- Learning what NORMAL traffic looks like (behavioral baseline)
- Detecting deviations from normal (anomaly scoring)
- Scoring how NEW/NOVEL the traffic is (novelty scoring via FAISS)
- When novelty is very high → redirect to honeypot to observe the attack
- After observing → learn from it → update the model → protect all customers

## Tech Stack
- RL Framework:       stable-baselines3 (PPO algorithm), gymnasium
- Neural Networks:    PyTorch (RL agent), TensorFlow/Keras (autoencoder)
- Anomaly Detection:  scikit-learn IsolationForest + custom autoencoder
- Novelty Scoring:    FAISS (Facebook AI Similarity Search)
- Explainability:     SHAP (why did the agent block this?)
- Backend API:        FastAPI + uvicorn
- Streaming:          Apache Kafka (real-time flow processing)
- Databases:          PostgreSQL (config), TimescaleDB (traffic logs), Redis (cache)
- Frontend:           Next.js + Tailwind CSS
- Containers:         Docker + Kubernetes
- CI/CD:              GitHub Actions
- Secrets:            HashiCorp Vault
- Monitoring:         Prometheus + Grafana

## Environment Setup (Already Done)
- OS: Kali Linux
- Python: 3.11 via Miniconda (conda env name: firewall)
- All packages installed and verified
- Activate with: conda activate firewall
- Project folder: ~/Desktop/DAIFIREWALL

## Project Structure
DAIFIREWALL/
├── data/                  ← CICIDS 2017 dataset goes here
│   └── MachineLearningCSV.zip  ← downloading now
├── data/processed/        ← preprocessed numpy arrays
├── notebooks/             ← Jupyter EDA notebooks
├── models/                ← saved RL models
│   ├── best/              ← best model from training
│   └── checkpoints/       ← periodic checkpoints
├── logs/                  ← training logs, confusion matrix
│   └── tensorboard/       ← tensorboard logs
├── notes/                 ← daily progress notes
├── tests/                 ← unit tests
└── src/
    ├── data/              ← preprocessor.py
    ├── detection/         ← behavioral_baseline.py, novelty_scorer.py
    ├── rl_agent/          ← environment.py, train.py, evaluate.py
    ├── response/          ← honeypot_redirector.py, quarantine_manager.py
    └── learning/          ← online_learner.py, experience_buffer.py

## Training Dataset
- Name: CICIDS 2017 (Canadian Institute for Cybersecurity IDS Dataset)
- Source: University of New Brunswick
- Download: MachineLearningCSV.zip (downloading now)
- Contains: Labeled network flows for Monday-Friday
- Labels: BENIGN, DDoS, PortScan, Bot, Brute Force, DoS, Web Attacks etc.
- After download: unzip into data/ folder

## RL Agent Design
- Algorithm: PPO (Proximal Policy Optimization)
- State: 20 network flow features (normalized 0-1)
- Actions: 4 (ALLOW=0, BLOCK=1, RATE_LIMIT=2, FLAG_MONITOR=3)
- Reward: +10 block attack, +1 allow benign, -8 block benign, -15 allow attack
- Training: 500,000 timesteps on CICIDS 2017
- Target: F1 > 0.90, False Positive Rate < 5%

## Key Features (20) Used for Training
Flow Duration, Total Fwd Packets, Total Backward Packets,
Total Length Fwd Packets, Total Length Bwd Packets,
Flow Bytes/s, Flow Packets/s, Flow IAT Mean, Flow IAT Std,
Flow IAT Max, Fwd IAT Mean, Bwd IAT Mean, SYN Flag Count,
RST Flag Count, PSH Flag Count, ACK Flag Count,
Destination Port, Packet Length Mean, Packet Length Variance,
Average Packet Size

## Compliance Standards
- ISO/IEC 27001:2022 (information security management)
- NIST CSF 2.0 (identify, protect, detect, respond, recover)
- PCI DSS v4.0 (payment card industry - for bank customers)
- SWIFT CSP (for banks using SWIFT network)
- MITRE ATT&CK (attack technique mapping)
- OWASP Top 10 (web attack detection)
- NBE Directive SBB/84/2022 (Ethiopian banking IT security)

## Attack Types System Must Detect
- Port Scan (T1046) - SYN packets to many ports, no ACK
- Brute Force (T1110) - repeated failed logins from same IP
- DDoS (T1498) - massive packet flood from many IPs
- C2 Beaconing (T1071) - periodic callbacks to attacker server
- Lateral Movement - unusual internal host-to-host connections
- Data Exfiltration - high outbound bytes to unknown destinations
- Zero-Day - anything highly anomalous never seen before

## Current Status (Day 1 Complete, Day 2 In Progress)
DONE:
- Project structure created
- Conda environment (firewall) with all packages installed
- CICIDS 2017 dataset downloading (MachineLearningCSV.zip)
- Git initialized

NEXT STEPS IN ORDER:
1. Unzip dataset into data/ folder
2. Run src/data/preprocessor.py → creates data/processed/*.npy files
3. Run src/rl_agent/train.py → trains PPO agent for 500k timesteps
4. Run src/rl_agent/evaluate.py → generates confusion matrix and F1 score
5. Add behavioral baseline (autoencoder) in src/detection/
6. Add novelty scorer (FAISS) in src/detection/
7. Build FastAPI backend in src/api/
8. Build Next.js dashboard

## Deadline
2 days from October 23, 2026

## Developer
Abraham Asmamaw Mulugeta
BSc Cyber Security, Bahir Dar University
INSA Cyber Talent Certified 2026
Email: abrahamasmamaw4@gmail.com
Portfolio: abrahamportfolio2026.vercel.app
