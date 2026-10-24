# Dynamic AI Firewall with Reinforcement Learning
## Complete Product Documentation & Build Roadmap
### Developer: Abraham Asmamaw Mulugeta
### Deadline: 2 days from October 23, 2026

---

## 1. WHAT IS THIS PRODUCT?

A self-learning network firewall that uses Reinforcement Learning (RL)
to protect sensitive infrastructure (government, banks, fintech) from
cyberattacks — including zero-day attacks it has never seen before.

Unlike traditional firewalls that use static rules written by humans,
this firewall LEARNS from every decision it makes. Every attack it
sees makes it smarter. It never stops improving.

### The Core Difference
```
Traditional Firewall:  "Does this match a known bad pattern?" → Block/Allow
AI Firewall:           "Does this DEVIATE from normal behavior?" → Block/Allow/Rate-Limit/Flag
                       "Have I EVER seen anything like this?" → Zero-Day Detection
                       "What should I do based on CONTEXT?" → Intelligent Response
```

---

## 2. TARGET CUSTOMERS

| Sector | Examples | Main Threat |
|--------|----------|-------------|
| Government | INSA, Ministries, Tax Authority | Nation-state APT attacks |
| Central Bank | NBE Ethiopia | SWIFT fraud, insider threats |
| Commercial Banks | CBE, Dashen, Awash, Bunna | DDoS, credential stuffing |
| Fintech | Payment processors, mobile money | API abuse, transaction fraud |
| Telecom | Ethio Telecom | DNS attacks, SS7 exploits |

---

## 3. HOW TRAFFIC FLOWS (Critical Architecture Detail)

### Common Misconception vs Reality
```
WRONG:  Traffic → Agent → SaaS → Infrastructure
RIGHT:  Traffic → Agent → (features only) → SaaS
                                              ↓
                                          Decision
                                              ↓
                        Agent enforces ←──────┘
                              ↓
                   ALLOW → Infrastructure
                   BLOCK → Dropped at agent (never reaches infrastructure)
```

### Step by Step
```
1. Packet arrives at sensor agent (sits at network edge)
2. Agent intercepts and HOLDS the packet (traffic waits here)
3. Agent extracts 20 features from packet (< 1ms)
4. Agent sends ONLY features to SaaS (NOT the packet itself)
5. SaaS RL agent makes decision (< 5ms)
6. Decision sent back to agent (< 1ms)
7. Total wait time: < 10ms
8. ALLOW → packet released → enters infrastructure
   BLOCK → packet dropped → never reaches infrastructure
```

### What Travels to SaaS
```
SENT TO SAAS (safe — just statistics):
  { syn_count: 847, bytes_per_sec: 4500, dst_port: 22, ... }
  ~500 bytes of numbers only

NEVER SENT TO SAAS:
  Raw packets
  Packet payload (actual data)
  Bank transactions
  Passwords or messages
  Any sensitive content
```

### Why This Matters
Bank and government customers need to know:
- Their ACTUAL DATA never leaves their network
- Only traffic statistics (20 numbers) go to SaaS
- Full data privacy and compliance maintained

### Latency
```
Human feels lag:            > 100ms
Bank transaction tolerance: > 50ms
Our firewall decision:      < 10ms  ✅ completely unnoticeable
```

### Timeout / Offline Fallback
```
if SaaS response time > 10ms:
    → Do NOT keep waiting
    → Fall back to local static rules immediately
    → Traffic gets basic protection
    → Logs stored locally, synced when SaaS back online
```

### Real World Analogy
```
Airport security checkpoint:
  Passenger (traffic) arrives at gate
  Guard (agent) checks passport details only
  Guard calls HQ (SaaS) with passenger info
  HQ says ALLOW or DENY
  ALLOW → passenger boards plane (enters infrastructure)
  DENY  → passenger removed at gate (never boards)
  The passenger (traffic) never goes to HQ.
  Only their details (features) do.
```

### Agent Position in Network
```
INTERNET
    │
    ▼
[SENSOR AGENT]  ← sits here, intercepts everything
    │               holds traffic, extracts features,
    │               sends features to SaaS, enforces decision
    │
    │ (only ALLOWED traffic passes below)
    ▼
[INTERNAL INFRASTRUCTURE]
  - Bank servers
  - Government systems
  - Database servers
  - SWIFT terminals
```

---

## 4. HOW THE PRODUCT WORKS (Full Flow)

```
STEP 1: Customer installs lightweight sensor agent on their server
        (small Python script, runs silently in background)

STEP 2: Sensor intercepts ALL incoming network traffic
        Traffic WAITS at the sensor — does not enter infrastructure yet

STEP 3: Sensor extracts 20 statistical features from each flow (< 1ms)
        e.g. packet rate, byte count, TCP flags, port numbers

STEP 4: Features sent to SaaS backend (encrypted TLS 1.3, < 3ms)
        NOT the traffic itself — only the statistics

STEP 5: SaaS RL Agent makes decision (< 5ms):
        → ALLOW          (safe traffic, release it)
        → BLOCK          (confirmed attack, drop it)
        → RATE_LIMIT     (suspicious, throttle it)
        → FLAG_MONITOR   (unusual, allow but watch closely)
        → HONEYPOT       (zero-day, redirect to trap)

STEP 6: Decision sent back to sensor (< 1ms)
        Total round trip: < 10ms

STEP 7: Sensor enforces decision:
        ALLOW  → releases packet into infrastructure
        BLOCK  → drops packet via iptables DROP rule
        Others → applies appropriate action

STEP 8: Everything logged to immutable audit database (compliance)

STEP 9: Agent learns from confirmed outcomes, gets smarter over time
```

---

## 5. ZERO-DAY DETECTION (Most Important Feature)

Most firewalls FAIL on zero-day attacks because they only recognize
attacks they have seen before. This system detects attacks it has
NEVER seen before.

```
LAYER 1 — BEHAVIORAL BASELINE
  Learn what NORMAL looks like for this customer's network.
  Tool: Autoencoder neural network (TensorFlow/Keras)
  How: Train on 2 weeks of normal traffic only
  Test: If reconstruction error is HIGH → traffic is abnormal

LAYER 2 — ANOMALY SCORING
  Score how far traffic deviates from normal.
  Tools: Isolation Forest + Statistical z-scores (scikit-learn)
  Score 0.0 = completely normal
  Score 1.0 = extreme deviation from normal

LAYER 3 — NOVELTY SCORING
  "Have we EVER seen anything like this?"
  Tool: FAISS similarity search (Facebook AI)
  How: Searches millions of past flows in < 1ms
  Low distance  = familiar pattern (seen before)
  High distance = genuinely new/novel pattern

LAYER 4 — RL AGENT DECISION
  Combines ALL signals:
  - Current flow features (20 values)
  - Anomaly score from Layer 1+2
  - Novelty score from Layer 3
  - Behavioral history (last 20 flows from this IP via LSTM)
  - Time context (2am traffic is more suspicious than 2pm)
  - External threat intelligence (is this IP known bad?)
  Makes final decision with confidence score + explanation

LAYER 5 — HONEYPOT RESPONSE (for high novelty)
  If novelty score > 0.8:
  → Silently redirect attacker to fake server
  → Attacker thinks they succeeded
  → We watch everything they do safely
  → We learn exactly how this new attack works
  → We update the model automatically
  → All customers are now protected from this attack
```

---

## 6. FULL SYSTEM ARCHITECTURE

```
┌─────────────────────────────────────────────────┐
│              CUSTOMER NETWORK                   │
│                                                 │
│  [INTERNET TRAFFIC]                             │
│         │                                       │
│         ▼                                       │
│  ┌──────────────────────────────────────────┐   │
│  │         SENSOR AGENT (on-premise)        │   │
│  │  - Intercepts ALL traffic                │   │
│  │  - Holds traffic (waits for decision)    │   │
│  │  - Extracts 20 features per flow         │   │
│  │  - Sends features to SaaS via TLS 1.3   │   │
│  │  - Enforces decisions via iptables       │   │
│  │  - Falls back to local rules if offline  │   │
│  └──────────────────┬───────────────────────┘   │
│                     │ features only (not traffic)│
└─────────────────────┼───────────────────────────┘
                      │
          ┌───────────┘ encrypted (TLS 1.3)
          ▼
┌─────────────────────────────────────────────────┐
│              SAAS BACKEND                       │
│                                                 │
│  [API Gateway] → rate limit, auth, WAF          │
│         │                                       │
│  [Kafka] → real-time event streaming            │
│         │                                       │
│  ┌──────▼──────┐  ┌──────────────────────────┐  │
│  │ Behavioral  │  │     RL AGENT (PPO)       │  │
│  │ Baseline    │→ │  State(129 dims)         │  │
│  │ Autoencoder │  │  → Action + Confidence   │  │
│  │ Iso.Forest  │  │  → Explanation (SHAP)    │  │
│  └─────────────┘  └──────────────────────────┘  │
│         │                    │                  │
│  [Novelty Scorer]    [Decision Engine]          │
│  (FAISS)             → enforce action           │
│         │                    │                  │
│  [TimescaleDB]        [Redis Cache]             │
│  immutable audit log  hot rules/IPs             │
│                                                 │
│  [Alert Service] → email, webhook, SIEM         │
│  [Dashboard]     → Next.js real-time UI         │
│  [Report Engine] → PCI DSS, ISO 27001 reports   │
└─────────────────────────────────────────────────┘
          │
          │ decision (ALLOW/BLOCK/etc)
          ▼
   Back to Sensor Agent
   Sensor enforces it
```

---

## 7. TECH STACK

### Already Installed (conda env: firewall, Python 3.11)
```
RL:               stable-baselines3==2.9.0, gymnasium==1.4.0
Neural Networks:  torch==2.14.1, tensorflow==2.21.0, keras==3.15.1
Anomaly:          scikit-learn==1.9.1
Similarity:       faiss-cpu==1.15.1
Explainability:   shap==0.51.0
Data:             pandas==3.1.0, numpy==2.4.6
Visualization:    matplotlib==3.11.2, seaborn==0.13.2
API:              fastapi==0.161.1, uvicorn==0.54.0
Notebook:         jupyter, jupyterlab
Utils:            python-dotenv, pytest
```

### Still Needed (install when reaching that phase)
```
Streaming:        confluent-kafka
Cache:            redis
Database:         psycopg2, timescaledb
Networking:       scapy (packet capture for sensor agent)
Frontend:         Node.js, Next.js, Tailwind CSS
Containers:       Docker, Kubernetes
Monitoring:       prometheus-client, grafana
```

---

## 8. PROJECT FOLDER STRUCTURE

```
~/Desktop/DAIFIREWALL/
│
├── AGENT_CONTEXT.md           ← this file (read first always)
├── requirements.txt
│
├── data/
│   ├── raw/                   ← CICIDS 2017 CSV files go here
│   └── processed/             ← preprocessed numpy arrays
│       ├── X_train.npy
│       ├── X_test.npy
│       ├── y_train.npy
│       └── y_test.npy
│
├── models/
│   ├── best/                  ← best_model.zip (from training)
│   ├── checkpoints/           ← periodic saves during training
│   └── scaler.pkl             ← feature normalizer
│
├── logs/
│   ├── tensorboard/           ← tensorboard --logdir logs/tensorboard
│   └── confusion_matrix.png
│
├── notebooks/
│   └── 01_data_exploration.ipynb
│
└── src/
    ├── data/
    │   └── preprocessor.py        ← loads, cleans, normalizes CICIDS
    │
    ├── detection/
    │   ├── behavioral_baseline.py ← autoencoder + isolation forest
    │   ├── novelty_scorer.py      ← FAISS similarity search
    │   └── ensemble.py            ← combines all detection signals
    │
    ├── rl_agent/
    │   ├── environment.py         ← Gymnasium FirewallEnv
    │   ├── train.py               ← PPO training script
    │   ├── evaluate.py            ← metrics + confusion matrix
    │   └── state_builder.py       ← builds 129-dim state vector
    │
    ├── response/
    │   ├── action_executor.py     ← executes all 5 actions
    │   ├── honeypot_redirector.py ← redirects zero-day to honeypot
    │   └── quarantine_manager.py  ← isolates infected internal hosts
    │
    ├── learning/
    │   ├── online_learner.py      ← continuous model updates
    │   └── experience_buffer.py   ← prioritized replay buffer
    │
    └── api/
        ├── main.py                ← FastAPI entry point
        ├── routes/
        │   ├── firewall.py        ← POST /api/v1/firewall/decision
        │   ├── analytics.py       ← GET  /api/v1/analytics/
        │   └── tenants.py         ← multi-tenant management
        └── core/
            ├── rl_engine.py       ← loads and runs RL model
            └── feature_extractor.py
```

---

## 9. RL AGENT DESIGN

### State (What the Agent Sees — 129 dimensions total)
```
Current flow features:     20 values (normalized 0-1)
Anomaly scores:             4 values (from baseline models)
Behavioral history:        64 values (LSTM encoding of last 20 flows)
Time context:               6 values (hour, weekday, is_night, etc.)
Threat intel:               5 values (IP reputation, country risk, etc.)
Network state:             10 values (global traffic health)
─────────────────────────────────────────
Total:                    129 dimensions
```

### The 20 Flow Features Used
```
Flow Duration, Total Fwd Packets, Total Backward Packets,
Total Length Fwd Packets, Total Length Bwd Packets,
Flow Bytes/s, Flow Packets/s, Flow IAT Mean, Flow IAT Std,
Flow IAT Max, Fwd IAT Mean, Bwd IAT Mean, SYN Flag Count,
RST Flag Count, PSH Flag Count, ACK Flag Count,
Destination Port, Packet Length Mean, Packet Length Variance,
Average Packet Size
```

### Actions (What Agent Can Do)
```
0 = ALLOW          → release traffic into infrastructure
1 = BLOCK          → drop via iptables, add IP to blocklist
2 = RATE_LIMIT     → throttle to 10% bandwidth via tc
3 = FLAG_MONITOR   → allow but log everything, alert SOC team
4 = HONEYPOT       → redirect to fake server (zero-day only)
```

### Reward Function
```
BLOCK   + attack  = +10.0   (true positive — great)
ALLOW   + benign  = +1.0    (true negative — good)
FLAG    + attack  = +6.0    (partial credit — caught it)
RATE    + attack  = +5.0    (partial credit)
BLOCK   + benign  = -8.0    (false positive — bad for banks)
ALLOW   + attack  = -15.0   (false negative — worst case)
```

---

## 10. TRAINING DATASET — CICIDS 2017

### What It Is
Network traffic dataset from University of New Brunswick, Canada.
Contains labeled flows for a full week of activity.
Each row = one network flow with 80+ features and a label.

### Files Needed
```
Monday-WorkingHours.pcap_ISCX.csv              → normal traffic
Tuesday-WorkingHours.pcap_ISCX.csv             → FTP/SSH Brute Force
Wednesday-workingHours.pcap_ISCX.csv           → DoS, Heartbleed
Thursday-WorkingHours-Morning.pcap_ISCX.csv    → Web attacks
Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv → DDoS, PortScan, Bot
```

### Download Options
```
Option 1 — UNB direct (slow):
  https://www.unb.ca/cic/datasets/ids-2017.html

Option 2 — Kaggle (faster, recommended):
  pip install kaggle
  kaggle datasets download -d cicdataset/cicids2017 -p data/raw/
  (requires free Kaggle account + API key)
```

### Labels
```
BENIGN = 0  (normal traffic)
ATTACK = 1  (everything else):
  FTP-Patator, SSH-Patator (brute force)
  DoS slowloris, DoS Hulk, DoS GoldenEye (denial of service)
  Heartbleed, Web Attack XSS, SQL Injection
  Bot, DDoS, PortScan, Infiltration
```

### Important Data Issues to Handle
```
1. Column names have leading spaces → strip with: df.columns.str.strip()
2. Contains inf values → replace with NaN then drop
3. Class imbalance (benign >> attacks) → use resample to balance
4. Use TEMPORAL split (not random) → prevents data leakage
```

---

## 11. COMPLIANCE STANDARDS

```
ISO/IEC 27001:2022    → audit logs, risk management, incident response
NIST CSF 2.0          → identify, protect, detect, respond, recover
PCI DSS v4.0          → mandatory for all bank customers
SWIFT CSP             → mandatory for banks using SWIFT network
MITRE ATT&CK          → maps every detection to attack technique ID
OWASP Top 10          → web attack detection at HTTP layer
NBE Directive SBB/84  → Ethiopian banking IT security requirement
```

### Attack Techniques System Must Detect
```
T1046 — Port Scan         (SYN to many ports, no ACK back)
T1110 — Brute Force       (many failed logins from same IP)
T1498 — DDoS              (massive packet flood, many source IPs)
T1071 — C2 Beaconing      (periodic callbacks, high payload entropy)
T1078 — Credential Stuffing (distributed login attempts)
T1190 — Web Exploit       (SQL injection, XSS, RCE)
NOVEL — Zero-Day          (anything with novelty score > 0.8)
```

---

## 12. BUILD ROADMAP (2-Day Sprint)

### DAY 2 — Data & First Agent
```
MORNING:
  [ ] Download CICIDS 2017 dataset (Kaggle)
  [ ] Unzip into data/raw/
  [ ] Create src/data/preprocessor.py
  [ ] Run preprocessor → creates data/processed/*.npy files

AFTERNOON:
  [ ] Create src/rl_agent/environment.py (FirewallEnv)
  [ ] Create src/rl_agent/train.py
  [ ] Start training (500k timesteps, ~30-60 min on CPU)
  [ ] Monitor with: tensorboard --logdir logs/tensorboard/

EVENING:
  [ ] Create src/rl_agent/evaluate.py
  [ ] Run evaluation → F1 score + confusion matrix
  [ ] Target: F1 > 0.85
```

### DAY 3 — Zero-Day Layer + API
```
MORNING:
  [ ] Create src/detection/behavioral_baseline.py
      - Autoencoder trained on benign traffic only
      - Isolation Forest for outlier scoring
      - Test on known attacks → should get high anomaly score

  [ ] Create src/detection/novelty_scorer.py
      - Build FAISS index from training flows
      - Test: known attacks = low novelty, new patterns = high novelty

AFTERNOON:
  [ ] Upgrade FirewallEnv state to include anomaly + novelty scores
  [ ] Retrain agent with upgraded 129-dim state vector
  [ ] Create src/api/main.py (FastAPI)
  [ ] Test: POST /api/v1/firewall/decision

EVENING:
  [ ] Dockerize the application
  [ ] Write README.md
  [ ] Push to GitHub
  [ ] Record demo video
```

---

## 13. KEY COMMANDS REFERENCE

```bash
# ALWAYS run this first every time you open terminal
conda activate firewall
cd ~/Desktop/DAIFIREWALL

# Download dataset via Kaggle
pip install kaggle
# put kaggle.json in ~/.kaggle/
kaggle datasets download -d cicdataset/cicids2017 -p data/raw/
unzip data/raw/cicids2017.zip -d data/raw/

# Preprocessing
python src/data/preprocessor.py

# Training
python src/rl_agent/train.py

# Monitor training (open new terminal)
tensorboard --logdir logs/tensorboard/
# open browser: http://localhost:6006

# Evaluate
python src/rl_agent/evaluate.py

# Run API
uvicorn src.api.main:app --reload --port 8000

# Test API
curl -X POST http://localhost:8000/api/v1/firewall/decision \
  -H "Content-Type: application/json" \
  -d '{"features": [0.1, 0.5, 0.3, ...]}'
```

---

## 14. TARGET METRICS

```
F1 Score:              > 0.90
Precision:             > 0.92
Recall:                > 0.88
False Positive Rate:   < 5%    (critical for banks)
False Negative Rate:   < 10%
Decision Latency:      < 10ms
Zero-Day Detection:    novelty score > 0.8 triggers honeypot
```

---

## 15. INSTRUCTIONS FOR AI AGENT (Kiro/Claude)

When helping with this project follow these rules:

```
1.  ALWAYS use Python 3.11 (conda env: firewall)
2.  ALWAYS cd ~/Desktop/DAIFIREWALL before running anything
3.  Use stable-baselines3 PPO — NOT DQN or A2C
4.  Use gymnasium (NOT old gym package)
5.  CICIDS column names have leading spaces — always strip them:
      df.columns = df.columns.str.strip()
6.  CICIDS has inf values — always handle:
      df.replace([np.inf, -np.inf], np.nan, inplace=True)
      df.dropna(inplace=True)
7.  Class imbalance exists — always balance with resample
8.  Use TEMPORAL split not random split (prevents data leakage)
9.  Save all models to models/ folder
10. Save all logs to logs/ folder
11. Target F1 > 0.90 before moving to next phase
12. Traffic NEVER goes to SaaS — only 20 feature values go
13. Sensor agent HOLDS traffic while waiting for SaaS decision
14. Total decision time must be < 10ms
15. Every decision must have SHAP explanation for regulators
```

---

## 16. DEVELOPER INFO

```
Name:        Abraham Asmamaw Mulugeta
Degree:      BSc Cyber Security, Bahir Dar University (CGPA 3.62, 2026)
Cert:        INSA Cyber Talent Certified 2026
Experience:  Penetration Tester Intern at INSA (Jul-Sep 2025)
Email:       abrahamasmamaw4@gmail.com
Portfolio:   abrahamportfolio2026.vercel.app
LinkedIn:    linkedin.com/in/abraham-asmamaw-12217a383
Goal:        Get hired at INSA as a cybersecurity engineer
Project:     Dynamic AI Firewall — built to stand out at INSA
```
