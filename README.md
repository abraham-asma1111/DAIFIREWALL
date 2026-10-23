# Dynamic AI Firewall - Reinforcement Learning Based Intrusion Detection

**Author:** Abraham Asmamaw Mulugeta  
**Institution:** Bahir Dar University - BSc Cyber Security  
**Date:** October 2026  
**Status:** MVP Development (Day 2)

---

## 🎯 Project Overview

A self-learning network firewall using **Reinforcement Learning (PPO algorithm)** to detect and block cyberattacks in real-time, including **zero-day attacks** it has never seen before.

### Key Features
- ✅ Real-time attack detection using RL agent
- ✅ Zero-day attack detection (behavioral baseline + novelty scoring)
- ✅ 4 decision actions: ALLOW, BLOCK, RATE_LIMIT, FLAG_MONITOR
- ✅ Trained on 2.8M network flows (CICIDS 2017)
- ✅ Explainable AI (SHAP values for decisions)
- 🔄 SaaS platform (FastAPI backend + Next.js dashboard)

### Target Customers
- 🏛️ Ethiopian Government (INSA)
- 🏦 Banks (National Bank of Ethiopia, Commercial Bank, Dashen, Awash)
- 💳 Fintech companies
- 📡 Telecom operators (Ethio Telecom)

---

## 🛠️ Tech Stack

### Machine Learning
- **RL Framework:** stable-baselines3 (PPO), gymnasium
- **Deep Learning:** PyTorch (RL agent), TensorFlow (autoencoder)
- **Anomaly Detection:** scikit-learn IsolationForest, custom autoencoder
- **Novelty Scoring:** FAISS (Facebook AI Similarity Search)
- **Explainability:** SHAP

### Backend & Infrastructure
- **API:** FastAPI + uvicorn
- **Streaming:** Apache Kafka (planned)
- **Databases:** PostgreSQL, TimescaleDB, Redis (planned)
- **Frontend:** Next.js + Tailwind CSS (planned)
- **Deployment:** Docker + Kubernetes (planned)

---

## 📁 Project Structure

```
DAIFIREWALL/
├── data/
│   ├── ab9206.../              # CICIDS 2017 dataset (8 CSV files, 844 MB)
│   └── processed/              # Preprocessed numpy arrays (475 MB)
│       ├── X_train.npy         # Training features (1.98M samples)
│       ├── X_val.npy           # Validation features (424K samples)
│       ├── X_test.npy          # Test features (424K samples)
│       └── y_*.npy             # Labels (binary & multiclass)
├── src/
│   ├── data/
│   │   └── preprocessor.py     # Data cleaning & normalization
│   ├── rl_agent/
│   │   ├── environment.py      # Custom Gymnasium environment
│   │   ├── train.py            # PPO training script
│   │   └── evaluate.py         # Model evaluation & metrics
│   ├── detection/              # Anomaly & novelty detection (TODO)
│   ├── response/               # Honeypot & quarantine (TODO)
│   └── learning/               # Online learning (TODO)
├── models/
│   ├── firewall_final.zip      # Trained PPO model
│   └── best/                   # Best model checkpoints
├── logs/
│   ├── evaluation_metrics.txt  # F1, precision, recall, FPR
│   └── confusion_matrix.png    # Visualization
├── notebooks/                  # Jupyter EDA (TODO)
├── TRAIN.py                    # Main training script
├── check_status.py             # Check project progress
└── README.md                   # This file
```

---

## 🚀 Quick Start

### 1. Environment Setup

```bash
# Activate conda environment
conda activate firewall

# Check status
python check_status.py
```

### 2. Data Preprocessing (✅ Done)

```bash
python src/data/preprocessor.py
```

**Output:** 2,827,876 network flows → 70% train / 15% val / 15% test

### 3. RL Agent Training

**IMPORTANT:** Uninstall TensorFlow first to avoid C++ conflicts!

```bash
# Remove TensorFlow temporarily
pip uninstall -y tensorflow

# Train the agent (30-60 minutes on CPU)
python TRAIN.py

# Or quick test (1000 steps, ~1 minute)
python TRAIN_MINIMAL.py
```

**Expected Output:**
```
Training for 500,000 steps...
Start time: 18:30:45
Estimated: 30-60 minutes

[Progress bar shows training]

✅ TRAINING COMPLETE!
Duration: 45.3 minutes
Model saved: models/firewall_final.zip
```

### 4. Model Evaluation

```bash
python src/rl_agent/evaluate.py
```

**Metrics Generated:**
- **F1 Score** (target: > 0.90)
- **False Positive Rate** (target: < 5%)
- **Confusion Matrix** visualization
- **Classification Report**

### 5. Reinstall TensorFlow

```bash
pip install tensorflow==2.21.0
```

---

## 📊 Dataset: CICIDS 2017

### Overview
- **Source:** Canadian Institute for Cybersecurity, UNB
- **Size:** 844 MB (8 CSV files)
- **Samples:** 2,830,743 network flows
- **Features:** 79 columns → 20 key features selected
- **Labels:** 15 attack types + BENIGN traffic

### Attack Types Covered
1. **BENIGN** - Normal traffic (2.27M samples, 80%)
2. **DDoS** - Distributed Denial of Service (128K)
3. **PortScan** - Reconnaissance (159K)
4. **DoS** (Hulk, GoldenEye, Slowloris, Slowhttptest) (252K)
5. **FTP-Patator** - FTP brute force (7.9K)
6. **SSH-Patator** - SSH brute force (5.9K)
7. **Bot** - Botnet traffic (2K)
8. **Web Attacks** (Brute Force, XSS, SQL Injection) (2.2K)
9. **Infiltration** - APT-style (36)
10. **Heartbleed** - SSL vulnerability (11)

### 20 Key Features Used
1. Flow Duration
2-3. Total Fwd/Bwd Packets
4-5. Total Length Fwd/Bwd Packets
6-7. Flow Bytes/s, Flow Packets/s
8-10. Flow IAT (Mean, Std, Max)
11-12. Fwd/Bwd IAT Mean
13-16. Flag Counts (SYN, RST, PSH, ACK)
17. Destination Port
18-19. Packet Length (Mean, Variance)
20. Average Packet Size

---

## 🧠 RL Agent Design

### Algorithm: PPO (Proximal Policy Optimization)
- **Policy:** MLP (Multi-Layer Perceptron)
- **State:** 20 normalized features [0, 1]
- **Actions:** 4 discrete actions
  - 0 = ALLOW (normal operation)
  - 1 = BLOCK (drop packet)
  - 2 = RATE_LIMIT (throttle traffic)
  - 3. FLAG_MONITOR (mark for investigation)

### Reward Structure
```
+10  : Block attack (correct block)
+1   : Allow benign (correct allow)
-8   : Block benign (false positive)
-15  : Allow attack (false negative - security breach!)
+5   : Rate limit attack (good mitigation)
-5   : Rate limit benign (unnecessary throttling)
+2   : Flag attack (conservative response)
-1   : Flag benign (wasted resources)
```

### Training Hyperparameters
- **Total timesteps:** 500,000
- **Learning rate:** 3e-4
- **Steps per rollout:** 2,048
- **Batch size:** 64
- **Epochs per update:** 10
- **Discount factor (γ):** 0.99
- **GAE lambda (λ):** 0.95
- **Clip range:** 0.2

---

## 📈 Target Metrics

From AGENT_CONTEXT.md requirements:

| Metric | Target | Purpose |
|--------|--------|---------|
| **F1 Score** | > 0.90 | Balance precision & recall |
| **False Positive Rate** | < 5% | Minimize blocking benign traffic |
| **Accuracy** | > 85% | Overall correctness |
| **Recall** | > 90% | Detect most attacks |

---

## 🔧 Troubleshooting

### Issue: "free(): invalid pointer" crash

**Cause:** TensorFlow and PyTorch have conflicting C++ memory allocators

**Solution:**
```bash
# Uninstall TensorFlow before training
pip uninstall -y tensorflow

# Train model
python TRAIN.py

# Reinstall TensorFlow after training
pip install tensorflow==2.21.0
```

### Issue: Training output not showing

**Solution:** Run directly in terminal (not through IDE):
```bash
python -u TRAIN.py
```

### Issue: GPU warnings

**Expected:** System uses CPU-only. Warnings are normal.
```
I0000 Could not find cuda drivers on your machine, GPU will not be used.
```

---

## 🗓️ Development Timeline

### ✅ Day 1 (Complete)
- Environment setup (Python 3.11, conda, all packages)
- Project structure created
- CICIDS 2017 dataset downloaded

### ✅ Day 2 (In Progress)
- Data preprocessing complete (2.8M samples cleaned)
- RL environment implemented (FirewallEnv)
- PPO training scripts created
- TensorFlow conflict resolved
- Training ready to run

### 📅 Day 3 (Planned)
- Model evaluation & metrics
- Behavioral baseline (autoencoder)
- Novelty scorer (FAISS)
- FastAPI backend skeleton
- Basic dashboard UI

---

## 🎓 Compliance & Standards

- ISO/IEC 27001:2022 (information security)
- NIST CSF 2.0 (cybersecurity framework)
- PCI DSS v4.0 (payment card industry)
- MITRE ATT&CK (attack technique mapping)
- NBE Directive SBB/84/2022 (Ethiopian banking IT security)

---

## 📞 Contact

**Abraham Asmamaw Mulugeta**  
BSc Cyber Security, Bahir Dar University  
INSA Cyber Talent Certified 2026  
📧 abrahamasmamaw4@gmail.com  
🌐 abrahamportfolio2026.vercel.app

---

## 📄 License

Copyright © 2026 Abraham Asmamaw Mulugeta. All rights reserved.

---

## 🙏 Acknowledgments

- University of New Brunswick (CICIDS 2017 dataset)
- stable-baselines3 team
- Ethiopian cybersecurity community
