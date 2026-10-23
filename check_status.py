#!/usr/bin/env python3
"""Check project status - what's done, what's next"""

import os
import sys
from datetime import datetime

print("\n" + "="*70)
print("FIREWALL AI - PROJECT STATUS")
print("="*70)
print(f"Checked: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# Check data
print("📊 DATA PREPROCESSING:")
data_files = [
    "data/processed/X_train.npy",
    "data/processed/X_val.npy",
    "data/processed/X_test.npy",
    "data/processed/y_train_binary.npy",
    "data/processed/y_val_binary.npy",
    "data/processed/y_test_binary.npy"
]
data_ready = all(os.path.exists(f) for f in data_files)
if data_ready:
    print("   ✅ COMPLETE - Data preprocessed and ready")
    import numpy as np
    X_train = np.load("data/processed/X_train.npy")
    print(f"      Training samples: {len(X_train):,}")
else:
    print("   ❌ NOT DONE - Run: python src/data/preprocessor.py")

# Check model
print("\n🤖 MODEL TRAINING:")
models = {
    "models/firewall_final.zip": "Full training complete",
    "models/firewall_interrupted.zip": "Training interrupted (partial)",
    "models/test_model.zip": "Test model only"
}

model_found = False
for model_path, desc in models.items():
    if os.path.exists(model_path):
        size = os.path.getsize(model_path) / (1024**2)
        print(f"   ✅ FOUND - {desc}")
        print(f"      Location: {model_path}")
        print(f"      Size: {size:.2f} MB")
        model_found = True
        break

if not model_found:
    print("   ❌ NOT DONE - Run: python TRAIN.py")
    print("      (Make sure TensorFlow is uninstalled first)")

# Check evaluation
print("\n📈 MODEL EVALUATION:")
if os.path.exists("logs/evaluation_metrics.txt"):
    print("   ✅ COMPLETE - Model evaluated")
    print("      Results: logs/evaluation_metrics.txt")
    if os.path.exists("logs/confusion_matrix_*.png"):
        print("      Plot: logs/confusion_matrix_*.png")
else:
    print("   ❌ NOT DONE - Run: python src/rl_agent/evaluate.py")

# Check TensorFlow status
print("\n🔧 ENVIRONMENT:")
try:
    import tensorflow
    print(f"   ⚠️  TensorFlow {tensorflow.__version__} is installed")
    print("      This may cause training conflicts!")
    print("      Uninstall: pip uninstall -y tensorflow")
except ImportError:
    print("   ✅ TensorFlow not installed (good for training)")

try:
    import torch
    print(f"   ✅ PyTorch {torch.__version__} installed")
except ImportError:
    print("   ❌ PyTorch not installed")

try:
    import stable_baselines3
    print(f"   ✅ stable-baselines3 {stable_baselines3.__version__} installed")
except ImportError:
    print("   ❌ stable-baselines3 not installed")

# Next steps
print("\n" + "="*70)
print("NEXT STEPS:")
print("="*70)

if not data_ready:
    print("1. Preprocess data: python src/data/preprocessor.py")
elif not model_found:
    print("1. Uninstall TensorFlow: pip uninstall -y tensorflow")
    print("2. Train model: python TRAIN.py (30-60 min)")
elif not os.path.exists("logs/evaluation_metrics.txt"):
    print("1. Evaluate model: python src/rl_agent/evaluate.py")
    print("2. Check results: cat logs/evaluation_metrics.txt")
else:
    print("✅ Core RL pipeline complete!")
    print("\nNext phases:")
    print("1. Reinstall TensorFlow: pip install tensorflow==2.21.0")
    print("2. Build anomaly detector (autoencoder)")
    print("3. Build novelty scorer (FAISS)")
    print("4. Build FastAPI backend")
    print("5. Build Next.js dashboard")

print()
