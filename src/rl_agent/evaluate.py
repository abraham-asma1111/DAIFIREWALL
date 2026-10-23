"""
Model Evaluation Script
Evaluates the trained PPO agent on test data and generates metrics

Author: Abraham Asmamaw Mulugeta
Date: October 23, 2026
"""

import torch
import numpy as np
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from stable_baselines3 import PPO
from src.rl_agent.environment import FirewallEnv
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, classification_report
from datetime import datetime

print("\n" + "="*70)
print("FIREWALL AI - MODEL EVALUATION")
print("="*70)

# Load test data
print("\n📊 Loading test data...")
X_test = np.load("data/processed/X_test.npy")
y_test = np.load("data/processed/y_test_binary.npy")
print(f"   ✓ Test samples: {len(X_test):,}")
print(f"   ✓ Benign: {(y_test==0).sum():,} | Attacks: {(y_test==1).sum():,}")

# Load model
print("\n🤖 Loading trained model...")
if os.path.exists("models/firewall_final.zip"):
    model_path = "models/firewall_final"
    print("   ✓ Loading: models/firewall_final.zip")
elif os.path.exists("models/firewall_interrupted.zip"):
    model_path = "models/firewall_interrupted"
    print("   ✓ Loading: models/firewall_interrupted.zip")
elif os.path.exists("models/test_model.zip"):
    model_path = "models/test_model"
    print("   ✓ Loading: models/test_model.zip")
else:
    print("   ✗ No trained model found!")
    print("   Run training first: python TRAIN.py")
    sys.exit(1)

model = PPO.load(model_path)
print("   ✓ Model loaded")

# Create environment
print("\n🎮 Creating test environment...")
env = FirewallEnv(X_test, y_test, shuffle=False)
print("   ✓ Environment ready")

# Evaluate
print("\n🔍 Evaluating model on test set...")
print("   This may take a few minutes...")

obs, info = env.reset()
y_pred = []
y_true = []

for i in range(len(X_test)):
    action, _states = model.predict(obs, deterministic=True)
    y_pred.append(1 if action == 1 else 0)  # BLOCK=1, others=0
    y_true.append(y_test[i])
    
    obs, reward, terminated, truncated, info = env.step(action)
    
    if (i + 1) % 50000 == 0:
        print(f"   Progress: {i+1:,}/{len(X_test):,} samples", flush=True)
    
    if terminated:
        obs, info = env.reset()

y_pred = np.array(y_pred)
y_true = np.array(y_true)

# Calculate metrics
print("\n" + "="*70)
print("EVALUATION RESULTS")
print("="*70)

# Basic metrics
tp = ((y_pred == 1) & (y_true == 1)).sum()
tn = ((y_pred == 0) & (y_true == 0)).sum()
fp = ((y_pred == 1) & (y_true == 0)).sum()
fn = ((y_pred == 0) & (y_true == 1)).sum()

accuracy = (tp + tn) / len(y_true)
precision = tp / (tp + fp) if (tp + fp) > 0 else 0
recall = tp / (tp + fn) if (tp + fn) > 0 else 0
f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
fpr = fp / (fp + tn) if (fp + tn) > 0 else 0

print("\nBinary Classification Metrics:")
print(f"  Accuracy:  {accuracy:.4f} ({accuracy*100:.2f}%)")
print(f"  Precision: {precision:.4f}")
print(f"  Recall:    {recall:.4f}")
print(f"  F1 Score:  {f1:.4f}")
print(f"  FPR:       {fpr:.4f} ({fpr*100:.2f}%)")

print("\nConfusion Matrix:")
print(f"  True Negatives:  {tn:,} (correct ALLOW)")
print(f"  False Positives: {fp:,} (wrong BLOCK)")
print(f"  False Negatives: {fn:,} (missed attack - dangerous!)")
print(f"  True Positives:  {tp:,} (correct BLOCK)")

# Target metrics check
print("\n" + "="*70)
print("TARGET METRICS (from requirements)")
print("="*70)
print(f"  F1 Score:   {f1:.4f} (target: > 0.90) {'✓ PASS' if f1 > 0.90 else '✗ FAIL'}")
print(f"  FPR:        {fpr:.4f} (target: < 0.05) {'✓ PASS' if fpr < 0.05 else '✗ FAIL'}")

# Detailed classification report
print("\n" + "="*70)
print("DETAILED CLASSIFICATION REPORT")
print("="*70)
print(classification_report(y_true, y_pred, target_names=['BENIGN', 'ATTACK']))

# Save confusion matrix plot
print("\n📊 Generating confusion matrix plot...")
os.makedirs("logs", exist_ok=True)

plt.figure(figsize=(8, 6))
cm = confusion_matrix(y_true, y_pred)
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
            xticklabels=['BENIGN', 'ATTACK'],
            yticklabels=['BENIGN', 'ATTACK'])
plt.title(f'Confusion Matrix\nF1={f1:.4f}, FPR={fpr:.4f}')
plt.ylabel('True Label')
plt.xlabel('Predicted Label')
plt.tight_layout()

plot_path = f"logs/confusion_matrix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
plt.savefig(plot_path, dpi=150)
print(f"   ✓ Plot saved: {plot_path}")

# Save metrics to file
metrics_path = "logs/evaluation_metrics.txt"
with open(metrics_path, 'w') as f:
    f.write("FIREWALL AI - EVALUATION RESULTS\n")
    f.write("="*70 + "\n\n")
    f.write(f"Model: {model_path}.zip\n")
    f.write(f"Evaluation Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"Test Samples: {len(X_test):,}\n\n")
    f.write("Metrics:\n")
    f.write(f"  Accuracy:  {accuracy:.4f}\n")
    f.write(f"  Precision: {precision:.4f}\n")
    f.write(f"  Recall:    {recall:.4f}\n")
    f.write(f"  F1 Score:  {f1:.4f}\n")
    f.write(f"  FPR:       {fpr:.4f}\n\n")
    f.write("Confusion Matrix:\n")
    f.write(f"  TN: {tn:,}  FP: {fp:,}\n")
    f.write(f"  FN: {fn:,}  TP: {tp:,}\n\n")
    f.write(classification_report(y_true, y_pred, target_names=['BENIGN', 'ATTACK']))

print(f"   ✓ Metrics saved: {metrics_path}")

print("\n" + "="*70)
print("✅ EVALUATION COMPLETE")
print("="*70)
print(f"\nResults:")
print(f"  - Confusion matrix: {plot_path}")
print(f"  - Metrics file: {metrics_path}")
print()
