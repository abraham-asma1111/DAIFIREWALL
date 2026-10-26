#!/usr/bin/env python3
"""
Threshold-Based Evaluation
Tests different confidence thresholds to optimize F1 score and FPR
"""

import torch
import numpy as np
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from stable_baselines3 import PPO
from src.rl_agent.environment import FirewallEnv
import matplotlib.pyplot as plt
from sklearn.metrics import precision_recall_curve, roc_curve
from datetime import datetime

print("\n" + "="*70)
print("FIREWALL AI - THRESHOLD OPTIMIZATION")
print("="*70)

# Load test data
print("\n📊 Loading test data...")
X_test = np.load("data/processed/X_test.npy")
y_test = np.load("data/processed/y_test_binary.npy")
print(f"   ✓ Test samples: {len(X_test):,}")
print(f"   ✓ Benign: {(y_test==0).sum():,} | Attacks: {(y_test==1).sum():,}")

# Load model
print("\n🤖 Loading trained model...")
model_path = "models/firewall_final_balanced"
model = PPO.load(model_path)
print("   ✓ Model loaded")

# Create environment
print("\n🎮 Getting model predictions with probabilities...")
env = FirewallEnv(X_test, y_test, shuffle=False)

obs, info = env.reset()
action_probs = []
y_true = []

for i in range(len(X_test)):
    # Get action probabilities from model
    action, _states = model.predict(obs, deterministic=False)
    
    # Get probability distribution
    obs_tensor = torch.FloatTensor(obs).unsqueeze(0)
    with torch.no_grad():
        action_dist = model.policy.get_distribution(obs_tensor)
        probs = torch.softmax(action_dist.distribution.logits, dim=-1).numpy()[0]
    
    # Probability of BLOCK action (action=1)
    block_prob = probs[1]
    action_probs.append(block_prob)
    y_true.append(y_test[i])
    
    obs, reward, terminated, truncated, info = env.step(action)
    
    if (i + 1) % 50000 == 0:
        print(f"   Progress: {i+1:,}/{len(X_test):,} samples")
    
    if terminated:
        obs, info = env.reset()

action_probs = np.array(action_probs)
y_true = np.array(y_true)

print("   ✓ Predictions complete")

# Test different thresholds
print("\n" + "="*70)
print("TESTING DIFFERENT CONFIDENCE THRESHOLDS")
print("="*70)

thresholds_to_test = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
results = []

print("\nThreshold | F1 Score | Recall | FPR    | Precision | Accuracy")
print("-" * 70)

for threshold in thresholds_to_test:
    # Apply threshold
    y_pred = (action_probs >= threshold).astype(int)
    
    # Calculate metrics
    tp = ((y_pred == 1) & (y_true == 1)).sum()
    tn = ((y_pred == 0) & (y_true == 0)).sum()
    fp = ((y_pred == 1) & (y_true == 0)).sum()
    fn = ((y_pred == 0) & (y_true == 1)).sum()
    
    accuracy = (tp + tn) / len(y_true)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
    
    results.append({
        'threshold': threshold,
        'f1': f1,
        'recall': recall,
        'fpr': fpr,
        'precision': precision,
        'accuracy': accuracy,
        'tp': tp,
        'tn': tn,
        'fp': fp,
        'fn': fn
    })
    
    # Highlight if meets targets
    meets_targets = f1 > 0.85 and recall > 0.85 and fpr < 0.05
    marker = " ← TARGET MET!" if meets_targets else ""
    
    print(f"  {threshold:.1f}     | {f1:.4f}   | {recall:.4f} | {fpr:.4f} | {precision:.4f}  | {accuracy:.4f}{marker}")

# Find best threshold based on F1 score
best_result = max(results, key=lambda x: x['f1'])

print("\n" + "="*70)
print("BEST THRESHOLD (Highest F1 Score)")
print("="*70)
print(f"\nOptimal Threshold: {best_result['threshold']:.1f}")
print(f"  F1 Score:   {best_result['f1']:.4f} (target: > 0.85) {'✓ PASS' if best_result['f1'] > 0.85 else '✗ FAIL'}")
print(f"  Recall:     {best_result['recall']:.4f} (target: > 0.85) {'✓ PASS' if best_result['recall'] > 0.85 else '✗ FAIL'}")
print(f"  Precision:  {best_result['precision']:.4f}")
print(f"  FPR:        {best_result['fpr']:.4f} (target: < 0.05) {'✓ PASS' if best_result['fpr'] < 0.05 else '✗ FAIL'}")
print(f"  Accuracy:   {best_result['accuracy']:.4f}")

print("\nConfusion Matrix:")
print(f"  True Negatives:  {best_result['tn']:,} (correct ALLOW)")
print(f"  False Positives: {best_result['fp']:,} (wrong BLOCK)")
print(f"  False Negatives: {best_result['fn']:,} (missed attack)")
print(f"  True Positives:  {best_result['tp']:,} (correct BLOCK)")

# Find threshold with best balance (lowest FPR while keeping recall > 0.85)
balanced_results = [r for r in results if r['recall'] > 0.85]
if balanced_results:
    balanced_best = min(balanced_results, key=lambda x: x['fpr'])
    
    print("\n" + "="*70)
    print("BALANCED THRESHOLD (High Recall + Low FPR)")
    print("="*70)
    print(f"\nRecommended Threshold: {balanced_best['threshold']:.1f}")
    print(f"  F1 Score:   {balanced_best['f1']:.4f}")
    print(f"  Recall:     {balanced_best['recall']:.4f} (catches {balanced_best['recall']*100:.1f}% of attacks)")
    print(f"  Precision:  {balanced_best['precision']:.4f}")
    print(f"  FPR:        {balanced_best['fpr']:.4f} ({balanced_best['fpr']*100:.1f}% false alarms)")
    print(f"  Accuracy:   {balanced_best['accuracy']:.4f}")
    
    print("\nConfusion Matrix:")
    print(f"  True Negatives:  {balanced_best['tn']:,}")
    print(f"  False Positives: {balanced_best['fp']:,}")
    print(f"  False Negatives: {balanced_best['fn']:,}")
    print(f"  True Positives:  {balanced_best['tp']:,}")

# Plot threshold analysis
print("\n📊 Generating threshold analysis plots...")

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# F1 Score vs Threshold
thresholds = [r['threshold'] for r in results]
f1_scores = [r['f1'] for r in results]
recalls = [r['recall'] for r in results]
fprs = [r['fpr'] for r in results]
precisions = [r['precision'] for r in results]

axes[0, 0].plot(thresholds, f1_scores, 'b-o', linewidth=2)
axes[0, 0].axhline(y=0.85, color='r', linestyle='--', label='Target (0.85)')
axes[0, 0].axvline(x=best_result['threshold'], color='g', linestyle='--', alpha=0.5, label=f"Best ({best_result['threshold']:.1f})")
axes[0, 0].set_xlabel('Confidence Threshold')
axes[0, 0].set_ylabel('F1 Score')
axes[0, 0].set_title('F1 Score vs Threshold')
axes[0, 0].legend()
axes[0, 0].grid(True, alpha=0.3)

# Recall vs Threshold
axes[0, 1].plot(thresholds, recalls, 'g-o', linewidth=2)
axes[0, 1].axhline(y=0.85, color='r', linestyle='--', label='Target (0.85)')
axes[0, 1].set_xlabel('Confidence Threshold')
axes[0, 1].set_ylabel('Recall')
axes[0, 1].set_title('Recall vs Threshold')
axes[0, 1].legend()
axes[0, 1].grid(True, alpha=0.3)

# FPR vs Threshold
axes[1, 0].plot(thresholds, fprs, 'r-o', linewidth=2)
axes[1, 0].axhline(y=0.05, color='g', linestyle='--', label='Target (0.05)')
axes[1, 0].set_xlabel('Confidence Threshold')
axes[1, 0].set_ylabel('False Positive Rate')
axes[1, 0].set_title('FPR vs Threshold')
axes[1, 0].legend()
axes[1, 0].grid(True, alpha=0.3)

# Precision-Recall Trade-off
axes[1, 1].plot(thresholds, precisions, 'b-o', label='Precision', linewidth=2)
axes[1, 1].plot(thresholds, recalls, 'g-o', label='Recall', linewidth=2)
axes[1, 1].set_xlabel('Confidence Threshold')
axes[1, 1].set_ylabel('Score')
axes[1, 1].set_title('Precision-Recall Trade-off')
axes[1, 1].legend()
axes[1, 1].grid(True, alpha=0.3)

plt.tight_layout()
plot_path = f"logs/threshold_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
plt.savefig(plot_path, dpi=150)
print(f"   ✓ Plot saved: {plot_path}")

# Save recommendations
print("\n💾 Saving recommendations...")
rec_path = "logs/threshold_recommendations.txt"
with open(rec_path, 'w') as f:
    f.write("THRESHOLD OPTIMIZATION RESULTS\n")
    f.write("="*70 + "\n\n")
    f.write(f"Model: {model_path}.zip\n")
    f.write(f"Evaluation Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"Test Samples: {len(X_test):,}\n\n")
    
    f.write("BEST THRESHOLD (Highest F1):\n")
    f.write(f"  Threshold: {best_result['threshold']:.1f}\n")
    f.write(f"  F1 Score:  {best_result['f1']:.4f}\n")
    f.write(f"  Recall:    {best_result['recall']:.4f}\n")
    f.write(f"  Precision: {best_result['precision']:.4f}\n")
    f.write(f"  FPR:       {best_result['fpr']:.4f}\n\n")
    
    if balanced_results:
        f.write("RECOMMENDED THRESHOLD (Balanced):\n")
        f.write(f"  Threshold: {balanced_best['threshold']:.1f}\n")
        f.write(f"  F1 Score:  {balanced_best['f1']:.4f}\n")
        f.write(f"  Recall:    {balanced_best['recall']:.4f}\n")
        f.write(f"  Precision: {balanced_best['precision']:.4f}\n")
        f.write(f"  FPR:       {balanced_best['fpr']:.4f}\n\n")
    
    f.write("IMPLEMENTATION:\n")
    f.write("Update src/rl_agent/evaluate.py and src/api/main.py:\n")
    if balanced_results:
        f.write(f"  CONFIDENCE_THRESHOLD = {balanced_best['threshold']:.1f}\n")
    else:
        f.write(f"  CONFIDENCE_THRESHOLD = {best_result['threshold']:.1f}\n")

print(f"   ✓ Recommendations saved: {rec_path}")

print("\n" + "="*70)
print("✅ THRESHOLD ANALYSIS COMPLETE")
print("="*70)
print(f"\nResults:")
print(f"  - Threshold analysis: {plot_path}")
print(f"  - Recommendations: {rec_path}")
print()
