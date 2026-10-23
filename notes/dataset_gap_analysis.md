# Dataset Gap Analysis - CICIDS 2017 vs MITRE ATT&CK

## What CICIDS 2017 COVERS (15 attack types)

### Initial Access
- ❌ None

### Reconnaissance  
- ✅ T1046 - Port Scan (158,930 samples)

### Credential Access
- ✅ T1110.001 - Password Guessing (FTP-Patator: 7,938)
- ✅ T1110.001 - Password Guessing (SSH-Patator: 5,897)
- ✅ Web Attack Brute Force (1,507)

### Impact / Denial of Service
- ✅ T1498 - Network DoS (DDoS: 128,027)
- ✅ T1499 - Endpoint DoS (DoS Hulk, GoldenEye, Slowloris, Slowhttptest: 252k total)

### Execution / Persistence
- ✅ T1071.001 - C2 via Web (Bot: 1,966)

### Exfiltration / Lateral Movement
- ✅ T1210 - Exploitation of Remote Services (Infiltration: 36)

### Initial Access / Exploitation
- ✅ CWE-89 - SQL Injection (21 samples) 
- ✅ CWE-79 - XSS (652 samples)
- ✅ CVE-2014-0160 - Heartbleed (11 samples)

---

## What CICIDS 2017 DOES NOT COVER (Major Gaps)

### ❌ Command & Control (C2 Beaconing)
- T1071 - Application Layer Protocol (HTTP/HTTPS/DNS beaconing)
- T1573 - Encrypted Channel (C2 over TLS)
- NO periodic callback patterns in dataset

### ❌ Lateral Movement
- T1021.001 - RDP (Remote Desktop Protocol attacks)
- T1021.002 - SMB/Windows Admin Shares
- T1570 - Lateral Tool Transfer
- NO internal network movement patterns

### ❌ Data Exfiltration
- T1041 - Exfiltration Over C2 Channel
- T1048 - Exfiltration Over Alternative Protocol
- T1030 - Data Transfer Size Limits (slow exfiltration)
- NO large outbound data transfers to external IPs

### ❌ Privilege Escalation
- T1068 - Exploitation for Privilege Escalation
- T1078 - Valid Accounts (compromised credentials)
- NO vertical movement in network

### ❌ Defense Evasion
- T1027 - Obfuscated Files or Information
- T1055 - Process Injection
- T1070 - Indicator Removal on Host
- NO evasion techniques captured

### ❌ Persistence
- T1053 - Scheduled Task/Job
- T1543 - Create or Modify System Process
- NO long-term persistence mechanisms

### ❌ Discovery
- T1018 - Remote System Discovery
- T1083 - File and Directory Discovery
- T1135 - Network Share Discovery
- NO enumeration activities except port scan

### ❌ Credential Access (Advanced)
- T1003 - OS Credential Dumping
- T1558 - Steal or Forge Kerberos Tickets
- T1557 - Man-in-the-Middle
- Only basic brute force covered

### ❌ Initial Access (Advanced)
- T1566 - Phishing
- T1190 - Exploit Public-Facing Application
- T1133 - External Remote Services
- T1195 - Supply Chain Compromise

### ❌ Zero-Day / Advanced Persistent Threats
- NO novel attack patterns
- NO polymorphic malware
- NO multi-stage attacks
- NO real APT campaigns

---

## CRITICAL GAPS FOR ETHIOPIAN GOVERNMENT/BANK CUSTOMERS

### Banking & Fintech Specific
1. **ATM/POS Attacks** - Not in dataset
2. **SWIFT Network Attacks** - Not in dataset
3. **Mobile Banking Fraud** - Not in dataset
4. **Ransomware** - Not in dataset
5. **Cryptocurrency Mining** - Not in dataset

### APT-Style Attacks (What INSA/NBE Face)
1. **Living off the Land (LotL)** - Using legitimate tools maliciously
2. **Fileless Malware** - Memory-only attacks
3. **Supply Chain Attacks** - Compromised software updates
4. **Watering Hole Attacks** - Compromised legitimate websites

---

## SOLUTION: AUGMENT WITH ADDITIONAL DATASETS

### Recommended Additional Datasets

#### 1. **CIC-IDS-2018** (Expansion of 2017)
- **NEW:** Brute Force, Heartbleed improved
- **NEW:** DoS Slowloris improved  
- **NEW:** DDoS-LOIC-UDP, DDoS-HOIC
- **Size:** 10 days of traffic
- **Download:** https://www.unb.ca/cic/datasets/ids-2018.html

#### 2. **CSE-CIC-IDS2018** (More comprehensive)
- **NEW:** Bot traffic improved
- **NEW:** Web attack patterns expanded
- **Size:** 10 days, 80GB+

#### 3. **CIC-DDoS2019** (Latest DDoS variants)
- **NEW:** 12 different DDoS attack types
- **NEW:** DNS, LDAP, MSSQL, NetBIOS, NTP, SNMP, SSDP, UDP reflection attacks
- **Size:** 50M+ flows

#### 4. **UNSW-NB15** (Australian dataset - more modern)
- **NEW:** Backdoor, Analysis, Fuzzers, Shellcode, Worms
- **NEW:** Generic malware patterns
- **Size:** 2.5M flows, 49 features
- **Download:** https://research.unsw.edu.au/projects/unsw-nb15-dataset

#### 5. **CTU-13** (Botnet Traffic)
- **NEW:** Real botnet captures (Neris, Rbot, etc.)
- **NEW:** C2 beaconing patterns  
- **NEW:** Long-duration malicious sessions
- **Size:** 13 scenarios of real malware

#### 6. **EMBER** (Malware Classification)
- **NEW:** PE file features from real malware
- **Size:** 1.1M samples
- Useful for file-based detection

#### 7. **Create Synthetic Zero-Day Data**
- Use **FAISS + Autoencoder** to generate:
  - Novel port scan patterns
  - Unusual protocol behaviors  
  - Abnormal packet timing sequences
  - Mutated attack signatures

---

## RECOMMENDED APPROACH FOR YOUR PROJECT

### Phase 1: Use CICIDS 2017 ONLY (Current - Day 2-3)
**Rationale:**
- ✅ 2.8M samples is enough to train initial RL agent
- ✅ Covers 80% of common attacks (DDoS, Port Scan, Brute Force, Web Attacks)
- ✅ Fast iteration - prove the concept works
- ✅ Meets 2-day MVP deadline

**What to build:**
1. Preprocessor for CICIDS 2017
2. PPO RL agent trained on 15 attack classes
3. Basic anomaly detection (autoencoder)
4. Simple novelty scoring (FAISS on known attacks)

### Phase 2: Augment Dataset (Week 2)
**Add these datasets:**
1. **UNSW-NB15** - Modern attack types (Backdoor, Shellcode, Worms)
2. **CTU-13** - Real botnet C2 beaconing
3. **CIC-DDoS2019** - Latest DDoS variants

**New capabilities:**
- Detect C2 beaconing (periodic callbacks)
- Detect lateral movement (internal host scanning)
- Detect data exfiltration (large outbound transfers)
- Retrain RL agent on 30+ attack classes

### Phase 3: Zero-Day Simulation (Week 3)
**Synthetic data generation:**
1. Use trained autoencoder to generate "normal" variations
2. Use FAISS to identify feature space gaps
3. Create synthetic attacks in unexplored regions
4. Test if agent can detect truly novel patterns

---

## ALTERNATIVE: FOCUS ON BEHAVIORAL BASELINE (Better for Zero-Day)

Instead of relying only on labeled attacks, focus on **anomaly detection**:

### Strategy 1: Behavior-Based Detection
1. Train autoencoder on BENIGN traffic only (1.8M samples)
2. Learn what "normal" looks like for Ethiopian government/bank networks
3. Anything with high reconstruction error = anomaly = potential zero-day
4. RL agent learns to block based on deviation score, not specific attack labels

### Strategy 2: Feature Engineering for Ethiopia Context
Add domain-specific features:
- Banking hours vs. non-banking hours
- Known Ethiopian IP ranges (Ethio Telecom)
- SWIFT message patterns
- ATM transaction timing
- Government network topology

### Strategy 3: Transfer Learning
1. Pre-train on CICIDS 2017 (known attacks)
2. Fine-tune on your own captured traffic (when deployed)
3. Continuously learn from real customer environments
4. Agent adapts to Ethiopian threat landscape

---

## MY RECOMMENDATION

### For 2-Day Deadline (MVP):
**Use CICIDS 2017 only** - It's sufficient to prove:
- RL agent can learn to block attacks
- Anomaly detection can detect deviations
- System architecture works end-to-end
- Zero-day detection concept is viable (via novelty scoring)

### For Production Deployment:
**Add datasets in this order:**
1. **UNSW-NB15** (backdoors, worms) - Week 2
2. **CTU-13** (botnet C2) - Week 2  
3. **CIC-DDoS2019** (latest DDoS) - Week 3
4. **Synthetic zero-day** (generated data) - Week 3
5. **Real customer traffic** (online learning) - After deployment

---

## BOTTOM LINE

**You are correct** - CICIDS 2017 alone is not enough for comprehensive coverage of MITRE ATT&CK.

**BUT** - For your 2-day deadline and MVP demonstration:
- ✅ It's enough to train a working RL agent
- ✅ It proves the zero-day detection concept
- ✅ It demonstrates value to INSA/NBE customers
- ✅ You can expand later with more datasets

**The key differentiator for your product is NOT the training dataset - it's the BEHAVIORAL BASELINE + CONTINUOUS LEARNING that will detect attacks not in any dataset.**

---

## SHOULD YOU DOWNLOAD MORE DATASETS NOW?

### Option A: Stick with CICIDS 2017 (RECOMMENDED)
- **Pro:** Ship MVP in 2 days, iterate fast
- **Pro:** Prove concept works before investing more time
- **Pro:** 2.8M samples is scientifically valid for academic paper
- **Con:** Limited attack coverage

### Option B: Add UNSW-NB15 now
- **Pro:** More modern attacks (2015 vs 2017)
- **Pro:** 49 features vs 79 (simpler preprocessing)
- **Con:** Extra 1-2 days to integrate
- **Con:** Misses your deadline

### Option C: Add CIC-IDS-2018 now  
- **Pro:** Direct successor to 2017, compatible format
- **Pro:** Adds 10 more days of traffic
- **Con:** 80GB+ download and preprocessing time
- **Con:** Misses your deadline

**My vote: Option A - Ship the MVP with CICIDS 2017, expand later**

What do you think? Should we proceed with CICIDS 2017 for now and augment later, or do you want to integrate more datasets before training?
