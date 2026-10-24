# What to Do After Training Completes

## Quick Start (Automated)

Just run this single command after training finishes:

```bash
./run_pipeline.sh
```

This will automatically:
1. Evaluate the RL model
2. Reinstall TensorFlow
3. Train behavioral baseline
4. Train novelty scorer
5. Test integrated detection

**Total time**: ~25 minutes

---

## Manual Steps (If You Prefer Control)

### Step 1: Verify Training Completed

```bash
# Check if model exists
ls -lh models/firewall_all_data.zip

# Check final metrics in log
tail -50 training_all_data.log
```

### Step 2: Evaluate RL Model (~5 minutes)

```bash
python src/rl_agent/evaluate.py
```

**What it does**:
- Tests model on test dataset
- Generates confusion matrix
- Calculates F1, precision, recall, FPR
- Saves results to `logs/`

**Expected output**:
- `logs/evaluation_metrics.txt` - Detailed metrics
- `logs/confusion_matrix_*.png` - Visual plot

**Target metrics**:
- F1 Score: > 0.90
- FPR (False Positive Rate): < 5%

### Step 3: Reinstall TensorFlow (~1 minute)

```bash
pip install tensorflow==2.21.0
```

**Why**: Needed for autoencoder (step 4). Was removed earlier to avoid conflicts with PyTorch during RL training.

### Step 4: Train Behavioral Baseline (~10 minutes)

```bash
python src/detection/behavioral_baseline.py
```

**What it does**:
- Trains autoencoder on BENIGN traffic only
- Learns what "normal" looks like
- Sets anomaly threshold
- Tests on attack samples

**Expected output**:
- `models/autoencoder.h5` - Trained model
- `models/behavioral_baseline.pkl` - Threshold and stats

**Purpose**: Detects zero-day attacks via anomaly detection

### Step 5: Train Novelty Scorer (~5 minutes)

```bash
python src/detection/novelty_scorer.py
```

**What it does**:
- Builds FAISS index from all training data
- Indexes 2.8M vectors for similarity search
- Sets novelty thresholds
- Tests on attack samples

**Expected output**:
- `models/novelty_index.faiss` - Vector index
- `models/novelty_scorer.pkl` - Metadata and thresholds

**Purpose**: Detects truly novel patterns never seen before

### Step 6: Test Integrated Detection (~2 minutes)

```bash
python src/detection/integrated_detector.py
```

**What it does**:
- Loads all 3 models (RL, Anomaly, Novelty)
- Tests on sample traffic
- Shows decision fusion logic
- Validates everything works together

**Expected output**: Test results showing decisions and threat levels

### Step 7: Start API Server

```bash
python src/api/main.py
```

**What it does**:
- Launches FastAPI backend
- Loads all trained models
- Exposes REST API endpoints
- Serves interactive docs

**Access**:
- API: `http://localhost:8000`
- Docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`

**Test with curl**:
```bash
curl -X POST "http://localhost:8000/api/v1/detect" \
  -H "Content-Type: application/json" \
  -d '{
    "features": [0.5, 0.3, 0.8, 0.1, 0.4, 0.6, 0.2, 0.9, 0.7, 0.3, 
                 0.5, 0.4, 0.6, 0.8, 0.2, 0.1, 0.7, 0.9, 0.3, 0.5]
  }'
```

---

## Optional: Live Testing

### Test with Live Network Traffic (Requires Root)

```bash
sudo python src/sensor/network_sensor.py
```

**What it does**:
- Captures live packets with Scapy
- Extracts 20 features from network flows
- Prints feature vectors in real-time

**Note**: Does NOT capture raw packets (privacy-preserving)

### Test Firewall Enforcement (Requires Root)

```bash
sudo python src/response/firewall_enforcer.py
```

**What it does**:
- Sets up iptables chain: AIFW_INPUT
- Tests BLOCK, RATE_LIMIT, HONEYPOT actions
- Shows enforcement capabilities

**Warning**: This modifies iptables. Review code before running.

---

## Monitoring Training Progress

While training is still running, you can monitor with:

```bash
# Real-time progress bar
python monitor_training.py

# Watch log file
tail -f training_all_data.log

# Check process
ps aux | grep TRAIN_ALL_DATA

# Check completion
ls -lh models/firewall_all_data.zip
```

---

## Troubleshooting

### Training Failed or Interrupted

If training crashes, the model might be saved as `models/firewall_interrupted.zip`. The evaluation script will automatically detect and use it.

To resume training, edit `TRAIN_ALL_DATA.py` and restart.

### TensorFlow Installation Issues

If `pip install tensorflow==2.21.0` fails:

```bash
# Try without version pin
pip install tensorflow

# Or use conda
conda install tensorflow
```

### FAISS Installation Issues

FAISS should already be installed. If not:

```bash
pip install faiss-cpu
```

### API Server Port Already in Use

If port 8000 is busy:

```bash
# Change port in src/api/main.py (last line)
# Or kill existing process
lsof -ti:8000 | xargs kill -9
```

---

## Expected Timeline

| Step | Duration | Cumulative |
|------|----------|------------|
| Evaluate model | 5 min | 5 min |
| Install TensorFlow | 1 min | 6 min |
| Train baseline | 10 min | 16 min |
| Train novelty | 5 min | 21 min |
| Test integration | 2 min | 23 min |
| Start API | instant | 23 min |

**Total**: ~23 minutes to MVP completion

---

## Success Criteria

✅ **MVP is complete when**:

1. RL model achieves F1 > 0.90
2. All 3 detection models trained
3. Integrated detector works
4. API server responds to requests
5. Test samples correctly classified

Then you can demo:
- Live detection via API
- Multi-layered threat analysis
- Automated response (BLOCK, RATE_LIMIT, etc.)
- Zero-day attack detection capability

---

## What's Next (Post-MVP)

1. **Dashboard**: Build Next.js UI for monitoring
2. **Dataset expansion**: Add UNSW-NB15, CTU-13, CIC-DDoS2019
3. **Live testing**: Two-VM setup (attacker + firewall)
4. **Online learning**: Continuous model updates
5. **Performance tuning**: Reduce false positives
6. **Production hardening**: Error handling, logging, monitoring

---

**Quick Reference**:
- Training log: `training_all_data.log`
- Monitor script: `python monitor_training.py`
- Auto pipeline: `./run_pipeline.sh`
- Status: `STATUS.md`
- Context: `AGENT_CONTEXT.md`
