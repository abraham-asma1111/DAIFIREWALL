#!/usr/bin/env python3
"""
System Status Check
Checks status of all AI Firewall components
"""

import os
import sys
import numpy as np
from datetime import datetime
from pathlib import Path

print("\n" + "="*70)
print("DYNAMIC AI FIREWALL - SYSTEM STATUS")
print("="*70)
print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# 1. DATA STATUS
print("📊 DATA STATUS")
print("-" * 70)
data_dir = Path("data/processed")
if data_dir.exists():
    files = {
        "X_train.npy": "Training features",
        "y_train_binary.npy": "Training labels",
        "X_val.npy": "Validation features",
        "y_val_binary.npy": "Validation labels",
        "X_test.npy": "Test features",
        "y_test_binary.npy": "Test labels",
        "feature_names.txt": "Feature names",
        "label_mapping.txt": "Label mapping"
    }
    
    for file, desc in files.items():
        path = data_dir / file
        if path.exists():
            if file.endswith('.npy'):
                data = np.load(path)
                print(f"  ✓ {desc:25} {len(data):,} samples")
            else:
                print(f"  ✓ {desc:25} exists")
        else:
            print(f"  ✗ {desc:25} MISSING")
    
    # Calculate total samples
    if (data_dir / "X_train.npy").exists() and (data_dir / "X_val.npy").exists():
        X_train = np.load(data_dir / "X_train.npy")
        X_val = np.load(data_dir / "X_val.npy")
        X_test = np.load(data_dir / "X_test.npy")
        total = len(X_train) + len(X_val) + len(X_test)
        print(f"\n  Total dataset: {total:,} samples")
        print(f"    Train: {len(X_train):,} ({len(X_train)/total*100:.1f}%)")
        print(f"    Val:   {len(X_val):,} ({len(X_val)/total*100:.1f}%)")
        print(f"    Test:  {len(X_test):,} ({len(X_test)/total*100:.1f}%)")
else:
    print("  ✗ Data directory not found!")
    print("  Run: python data/download_data.py")
    print("       python src/data/preprocessor.py")

# 2. MODEL STATUS
print("\n🤖 MODEL STATUS")
print("-" * 70)
model_dir = Path("models")
if model_dir.exists():
    models = {
        "firewall_final_balanced.zip": "Final balanced model (RECOMMENDED)",
        "firewall_fast.zip": "Fast training model",
        "firewall_all_data.zip": "All data model",
        "autoencoder.h5": "Anomaly detector",
        "behavioral_baseline.pkl": "Behavioral baseline",
        "novelty_index.faiss": "Novelty scorer index",
        "novelty_scorer.pkl": "Novelty scorer model"
    }
    
    found_models = 0
    for model, desc in models.items():
        path = model_dir / model
        if path.exists():
            size_mb = path.stat().st_size / (1024 * 1024)
            mod_time = datetime.fromtimestamp(path.stat().st_mtime)
            print(f"  ✓ {desc:40} {size_mb:.1f} MB")
            print(f"    Last modified: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
            found_models += 1
        else:
            print(f"  ✗ {desc:40} MISSING")
    
    print(f"\n  Total models: {found_models}/{len(models)}")
else:
    print("  ✗ Models directory not found!")

# 3. TRAINING STATUS
print("\n🏋️ TRAINING STATUS")
print("-" * 70)
training_files = [
    ("training_final.log", "Final balanced training"),
    ("training_fast.log", "Fast training"),
    ("training_all.log", "All data training")
]

active_training = False
for log_file, desc in training_files:
    if os.path.exists(log_file):
        size_kb = os.path.getsize(log_file) / 1024
        mod_time = datetime.fromtimestamp(os.path.getmtime(log_file))
        age_minutes = (datetime.now() - mod_time).total_seconds() / 60
        
        # Check if recently updated (training likely active)
        if age_minutes < 5:
            print(f"  🔄 {desc:30} ACTIVE (updated {age_minutes:.1f}m ago)")
            active_training = True
            
            # Show last few lines
            with open(log_file, 'r') as f:
                lines = f.readlines()[-10:]
                for line in lines:
                    if 'total_timesteps' in line or 'fps' in line:
                        print(f"     {line.strip()}")
        else:
            print(f"  ✓ {desc:30} completed {age_minutes:.0f}m ago")

if not active_training:
    print("  ℹ️  No active training sessions")

# 4. BACKEND STATUS
print("\n⚙️ BACKEND STATUS")
print("-" * 70)
backend_files = {
    "src/api/main.py": "FastAPI server",
    "src/sensor/network_sensor.py": "Network sensor",
    "src/response/firewall_enforcer.py": "Firewall enforcer",
    "src/detection/integrated_detector.py": "Integrated detector"
}

for file, desc in backend_files.items():
    if os.path.exists(file):
        print(f"  ✓ {desc:30} ready")
    else:
        print(f"  ✗ {desc:30} MISSING")

# 5. EVALUATION RESULTS
print("\n📈 LATEST EVALUATION RESULTS")
print("-" * 70)
metrics_file = "logs/evaluation_metrics.txt"
if os.path.exists(metrics_file):
    with open(metrics_file, 'r') as f:
        lines = f.readlines()
        in_metrics = False
        for line in lines:
            if line.strip().startswith("Metrics:"):
                in_metrics = True
            elif in_metrics and line.strip() and not line.strip().startswith("Confusion"):
                print(f"  {line.strip()}")
            elif line.strip().startswith("Confusion"):
                break
    
    # Show confusion matrix plot
    cm_files = sorted([f for f in os.listdir("logs") if f.startswith("confusion_matrix")])
    if cm_files:
        latest_cm = cm_files[-1]
        print(f"\n  Latest confusion matrix: logs/{latest_cm}")
else:
    print("  ℹ️  No evaluation results yet")
    print("  Run: /home/abraham/miniconda3/envs/firewall/bin/python src/rl_agent/evaluate.py")

# 6. RECOMMENDATIONS
print("\n💡 RECOMMENDATIONS")
print("-" * 70)

recommendations = []

# Check if model exists
if not (model_dir / "firewall_final_balanced.zip").exists():
    if active_training:
        recommendations.append("⏳ Wait for training to complete (~15-20 minutes remaining)")
    else:
        recommendations.append("🏋️ Train model: /home/abraham/miniconda3/envs/firewall/bin/python TRAIN_FINAL.py")

# Check if evaluated
if not os.path.exists(metrics_file):
    if (model_dir / "firewall_final_balanced.zip").exists():
        recommendations.append("📊 Evaluate model: /home/abraham/miniconda3/envs/firewall/bin/python src/rl_agent/evaluate.py")

# Check backend
if os.path.exists("src/api/main.py"):
    recommendations.append("🚀 Test API: /home/abraham/miniconda3/envs/firewall/bin/python src/api/main.py")

if recommendations:
    for rec in recommendations:
        print(f"  {rec}")
else:
    print("  ✅ All systems ready!")

# 7. QUICK COMMANDS
print("\n⚡ QUICK COMMANDS")
print("-" * 70)
print("  Monitor training:  tail -f training_final.log")
print("  Check progress:    grep 'total_timesteps' training_final.log | tail -5")
print("  Evaluate model:    /home/abraham/miniconda3/envs/firewall/bin/python src/rl_agent/evaluate.py")
print("  Start API:         /home/abraham/miniconda3/envs/firewall/bin/python src/api/main.py")
print("  Check this status: /home/abraham/miniconda3/envs/firewall/bin/python system_status.py")

print("\n" + "="*70 + "\n")
