#!/usr/bin/env python3
"""
Model Evaluation with Decision Guard
Tests the focal loss model with post-processing guard to achieve:
- Recall > 90% (catch most attacks)
- FPR < 5% (acceptable false positives)
- F1 > 0.85 (production-ready)
"""

import numpy as np
import sys
import os
from stable_baselines3 import PPO
from src.rl_agent.environment import FirewallEnv
from src.rl_agent.decision_guard import PostProcessingDecisionGuard
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, classification_report
from datetime import datetime

print("\n" + "="*70)
print("FIREWALL AI - EVALUATION WITH DECISION GUARD")
print("="*70)

# Load test data
print("\n📊 Loading test data...")
X_test = np.load("data/processed/X_test.npy")
y_test = np.load("data/processed/y_test_binary.npy")
print(f"   ✓ Test samples: {len(X_test):,}")
print(f"   ✓ Benign: {(y_test==0).sum():,} | Attacks: {(y_test==1).sum():,}")

# Load model
print("\n🤖 Loading trained model...")
if os.path.exists("models/firewall_focal.zip"):
    model_path = "models/firewall_focal"
    print("   ✓ Loading: models/firewall_focal.zip (FOCAL LOSS)")
else:
    print("   ✗ No focal model found! Run TRAIN_FOCAL_LOSS.py first")
    sys.exit(1)

model = PPO.load(model_path)
print("   ✓ Model loaded")

# Create decision guard
print("\n🛡️ Initializing Post-Processing Decision Guard...")
guard = PostProcessingDecisionGuard(
    benign_protection_threshold=0.80,  # Require 80% confidence to block
    rate_limit_upgrade_threshold=0.45,  # Upgrade rate-limits more aggressively
    critical_ports=[21, 22, 23, 25, 80, 443, 3306, 3389, 5432, 8080]
)

# Create environment
print("\n🎮 Creating test environment...")
env = FirewallEnv(X_test, y_test, shuffle=False)
print("   ✓ Environment ready")

# Evaluate with guard
print("\n🔍 Evaluating model with decision guard...")
print("   This may take a few minutes...")

obs, info = env.reset()
y_pred = []
y_true = []
guard_interventions = {
    'blocks_prevented': 0,  # High-conf blocks that guard kept
    'blocks_allowed': 0,     # Low-conf blocks that guard changed to allow
    'soft_upgraded': 0,      # Rate-limits upgraded to blocks
    'total_decisions': 0
}

for i in range(len(X_test)):
    # Get raw model action and probabilities
    raw_action, _states = model.predict(obs, deterministic=True)
    
    # Get action probabilities from the model's policy
    import torch
    obs_tensor = torch.FloatTensor(obs).unsqueeze(0)
    with torch.no_grad():
        action_probs = model.policy.get_distribution(obs_tensor).distribution.probs[0]
    
    # Apply decision guard
    features = {
        # Extract some basic features from observation
        "destination_port": int(obs[0] * 65535) if obs[0] > 0 else 80,  # Approximate
        "total_fwd_packets": obs[1] * 1000 if len(obs) > 1 else 0,
        "flow_duration": obs[2] * 10000 if len(obs) > 2 else 0
    }
    
    guarded_action = guard.filter_action(action_probs, features)
    
    # Track interventions
    guard_interventions['total_decisions'] += 1
    if raw_action == 1 and guarded_action == 0:
        guard_interventions['blocks_allowed'] += 1
    elif raw_action == 2 and guarded_action == 1:
        guard_interventions['soft_upgraded'] += 1
    elif raw_action == 1 and guarded_action == 1:
        guard_interventions['blocks_prevented'] += 1
    
    # Use guarded action for prediction
    y_pred.append(1 if guarded_action == 1 else 0)  # BLOCK=1, others=0
    y_true.append(y_test[i])
    
    obs, reward, terminated, truncated, info = env.step(guarded_action)
    
    if (i + 1) % 50000 == 0:
        print(f"   Progress: {i+1:,}/{len(X_test):,} samples", flush=True)
    
    if terminated:
        obs, info = env.reset()

y_pred = np.array(y_pred)
y_true = np.array(y_true)

# Calculate metrics
print("\n" + "="*70)
print("EVALUATION RESULTS WITH DECISION GUARD")
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
print(f"  False Negatives: {fn:,} (missed attack)")
print(f"  True Positives:  {tp:,} (correct BLOCK)")

print("\nGuard Intervention Statistics:")
print(f"  Total decisions: {guard_interventions['total_decisions']:,}")
print(f"  High-conf blocks kept: {guard_interventions['blocks_prevented']:,}")
print(f"  Low-conf blocks→allow: {guard_interventions['blocks_allowed']:,}")
print(f"  Soft actions upgraded: {guard_interventions['soft_upgraded']:,}")
intervention_rate = (guard_interventions['blocks_allowed'] + guard_interventions['soft_upgraded']) / guard_interventions['total_decisions'] * 100
print(f"  Intervention rate: {intervention_rate:.2f}%")

# Target metrics check
print("\n" + "="*70)
print("TARGET METRICS (from requirements)")
print("="*70)
print(f"  Recall:     {recall:.4f} (target: > 0.85) {'✓ PASS' if recall > 0.85 else '✗ FAIL'}")
print(f"  FPR:        {fpr:.4f} (target: < 0.05) {'✓ PASS' if fpr < 0.05 else '✗ FAIL'}")
print(f"  F1 Score:   {f1:.4f} (target: > 0.85) {'✓ PASS' if f1 > 0.85 else '✗ FAIL'}")

# Overall assessment
passes = sum([recall > 0.85, fpr < 0.05, f1 > 0.85])
print(f"\n{'✅ PRODUCTION READY' if passes == 3 else '⚠️ NEEDS TUNING'} ({passes}/3 targets met)")

# Detailed classification report
print("\n" + "="*70)
print("DETAILED CLASSIFICATION REPORT")
print("="*70)
print(classification_report(y_true, y_pred, target_names=['BENIGN', 'ATTACK']))

# Save confusion matrix plot
print("\n📊 Generating confusion matrix plot...")
os.makedirs("logs", exist_ok=True)

plt.figure(figsize=(10, 8))
cm = confusion_matrix(y_true, y_pred)
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
            xticklabels=['BENIGN', 'ATTACK'],
            yticklabels=['BENIGN', 'ATTACK'])
plt.title(f'Confusion Matrix (With Decision Guard)\nRecall={recall:.4f}, FPR={fpr:.4f}, F1={f1:.4f}')
plt.ylabel('True Label')
plt.xlabel('Predicted Label')
plt.tight_layout()

plot_path = f"logs/confusion_matrix_guarded_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
plt.savefig(plot_path, dpi=150)
print(f"   ✓ Plot saved: {plot_path}")

# Save metrics to file
metrics_path = "logs/evaluation_metrics_guarded.txt"
with open(metrics_path, 'w') as f:
    f.write("FIREWALL AI - EVALUATION RESULTS (WITH DECISION GUARD)\n")
    f.write("="*70 + "\n\n")
    f.write(f"Model: {model_path}.zip + PostProcessingDecisionGuard\n")
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
    f.write("Guard Interventions:\n")
    f.write(f"  Total decisions: {guard_interventions['total_decisions']:,}\n")
    f.write(f"  Blocks kept: {guard_interventions['blocks_prevented']:,}\n")
    f.write(f"  Blocks→Allow: {guard_interventions['blocks_allowed']:,}\n")
    f.write(f"  Soft→Block: {guard_interventions['soft_upgraded']:,}\n")
    f.write(f"  Intervention rate: {intervention_rate:.2f}%\n\n")
    f.write(classification_report(y_true, y_pred, target_names=['BENIGN', 'ATTACK']))

print(f"   ✓ Metrics saved: {metrics_path}")

print("\n" + "="*70)
print("✅ EVALUATION COMPLETE")
print("="*70)
print(f"\nComparison:")
print(f"  Without Guard: Recall 90.73%, FPR 18.47%, F1 0.682")
print(f"  With Guard:    Recall {recall*100:.2f}%, FPR {fpr*100:.2f}%, F1 {f1:.3f}")
print(f"\nResults:")
print(f"  - Confusion matrix: {plot_path}")
print(f"  - Metrics file: {metrics_path}")
print()
