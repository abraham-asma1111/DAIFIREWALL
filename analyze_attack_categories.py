#!/usr/bin/env python3
"""
Attack Category Analysis
Identifies which specific attack types contribute to the 39% missed attack rate
Helps answer: "What specific attack categories make up that missing 39%?"
"""

import numpy as np
import pandas as pd
from stable_baselines3 import PPO
from src.rl_agent.environment import FirewallEnv
import os
import sys

print("\n" + "="*70)
print("ATTACK CATEGORY ANALYSIS")
print("="*70)

# Load test data
print("\n📊 Loading test data...")
X_test = np.load("data/processed/X_test.npy")
y_test_binary = np.load("data/processed/y_test_binary.npy")
y_test_multiclass = np.load("data/processed/y_test_multiclass.npy")

print(f"   ✓ Test samples: {len(X_test):,}")
print(f"   ✓ Benign: {(y_test_binary==0).sum():,}")
print(f"   ✓ Attacks: {(y_test_binary==1).sum():,}")

# Load label mapping
label_mapping = {}
with open("data/processed/label_mapping.txt", 'r') as f:
    for line in f:
        if ':' in line:
            idx, label = line.strip().split(': ')
            label_mapping[int(idx)] = label

print(f"\n   Attack types in dataset: {len(label_mapping)}")
for idx, label in sorted(label_mapping.items()):
    count = (y_test_multiclass == idx).sum()
    print(f"     {idx:2d}. {label:30s} - {count:,} samples")

# Load model
print("\n🤖 Loading model for evaluation...")
if os.path.exists("models/firewall_focal.zip"):
    model_path = "models/firewall_focal"
    print("   ✓ Using: firewall_focal.zip")
elif os.path.exists("models/firewall_improved.zip"):
    model_path = "models/firewall_improved"
    print("   ✓ Using: firewall_improved.zip")
elif os.path.exists("models/firewall_natural.zip"):
    model_path = "models/firewall_natural"
    print("   ✓ Using: firewall_natural.zip")
else:
    print("   ✗ No model found! Run training first.")
    sys.exit(1)

model = PPO.load(model_path)

# Evaluate per attack category
print("\n🔍 Evaluating model performance per attack category...")

env = FirewallEnv(X_test, y_test_binary, shuffle=False)
obs, info = env.reset()

predictions = []
for i in range(len(X_test)):
    action, _states = model.predict(obs, deterministic=True)
    predictions.append(action)
    obs, reward, terminated, truncated, info = env.step(action)
    
    if (i + 1) % 50000 == 0:
        print(f"   Progress: {i+1:,}/{len(X_test):,}", flush=True)
    
    if terminated:
        obs, info = env.reset()

predictions = np.array(predictions)

# Analyze per category
print("\n" + "="*70)
print("PER-CATEGORY DETECTION PERFORMANCE")
print("="*70)

results = []

for idx in sorted(label_mapping.keys()):
    label_name = label_mapping[idx]
    
    # Get samples for this category
    mask = y_test_multiclass == idx
    if mask.sum() == 0:
        continue
    
    # For benign (label 0), success = ALLOW
    # For attacks (label 1+), success = BLOCK
    if idx == 0:  # BENIGN
        y_true_binary = y_test_binary[mask]
        y_pred_actions = predictions[mask]
        
        # Correct = ALLOW (action 0)
        correct = (y_pred_actions == 0).sum()
        total = len(y_pred_actions)
        accuracy = correct / total if total > 0 else 0
        
        # False positives
        fp = (y_pred_actions == 1).sum()
        fpr = fp / total if total > 0 else 0
        
        results.append({
            'category': label_name,
            'total': total,
            'detected': correct,
            'missed': total - correct,
            'detection_rate': accuracy * 100,
            'type': 'BENIGN'
        })
        
        print(f"\n{label_name}")
        print(f"  Type: BENIGN TRAFFIC")
        print(f"  Total samples: {total:,}")
        print(f"  Correctly allowed: {correct:,} ({accuracy*100:.1f}%)")
        print(f"  False positives: {fp:,} ({fpr*100:.2f}%)")
    
    else:  # ATTACK
        y_true_binary = y_test_binary[mask]
        y_pred_actions = predictions[mask]
        
        # Correct = BLOCK (action 1) or RATE_LIMIT (action 2) or FLAG (action 3)
        # In binary terms: attack should NOT be ALLOWED
        detected = (y_pred_actions != 0).sum()  # Not ALLOW
        blocked = (y_pred_actions == 1).sum()   # Explicit BLOCK
        missed = (y_pred_actions == 0).sum()     # ALLOWED (bad!)
        
        total = len(y_pred_actions)
        detection_rate = detected / total if total > 0 else 0
        block_rate = blocked / total if total > 0 else 0
        miss_rate = missed / total if total > 0 else 0
        
        results.append({
            'category': label_name,
            'total': total,
            'detected': detected,
            'missed': missed,
            'detection_rate': detection_rate * 100,
            'type': 'ATTACK'
        })
        
        print(f"\n{label_name}")
        print(f"  Type: ATTACK")
        print(f"  Total samples: {total:,}")
        print(f"  Detected (any response): {detected:,} ({detection_rate*100:.1f}%)")
        print(f"  Blocked (action=1): {blocked:,} ({block_rate*100:.1f}%)")
        print(f"  Missed (allowed): {missed:,} ({miss_rate*100:.1f}%) {'⚠️ HIGH' if miss_rate > 0.5 else '✓'}")

# Summary: Which attacks are hardest to detect?
print("\n" + "="*70)
print("HARDEST TO DETECT ATTACKS (Sorted by Miss Rate)")
print("="*70)

attack_results = [r for r in results if r['type'] == 'ATTACK']
attack_results_sorted = sorted(attack_results, key=lambda x: x['detection_rate'])

print("\nAttacks with LOWEST detection rates:")
for i, result in enumerate(attack_results_sorted[:5], 1):
    print(f"{i}. {result['category']:30s} - {result['detection_rate']:.1f}% detected ({result['missed']:,} missed)")

print("\nAttacks with HIGHEST detection rates:")
for i, result in enumerate(sorted(attack_results, key=lambda x: x['detection_rate'], reverse=True)[:5], 1):
    print(f"{i}. {result['category']:30s} - {result['detection_rate']:.1f}% detected ({result['missed']:,} missed)")

# Total attack leakage
total_attacks = sum(r['total'] for r in attack_results)
total_missed = sum(r['missed'] for r in attack_results)
overall_miss_rate = total_missed / total_attacks if total_attacks > 0 else 0

print("\n" + "="*70)
print("OVERALL ATTACK LEAKAGE")
print("="*70)
print(f"Total attacks: {total_attacks:,}")
print(f"Attacks missed: {total_missed:,}")
print(f"Attack leakage rate: {overall_miss_rate*100:.1f}%")
print(f"Attack detection rate: {(1-overall_miss_rate)*100:.1f}%")

if overall_miss_rate > 0.15:
    print("\n⚠️ Attack leakage > 15% - NOT production ready")
    print("   Recommendation: Continue training with focal loss")
elif overall_miss_rate > 0.05:
    print("\n⚠️ Attack leakage 5-15% - Acceptable for pilot")
    print("   Recommendation: Deploy with monitoring")
else:
    print("\n✅ Attack leakage < 5% - Production ready!")

# Save results
os.makedirs("logs", exist_ok=True)
df = pd.DataFrame(results)
df.to_csv("logs/attack_category_analysis.csv", index=False)
print(f"\n💾 Detailed results saved: logs/attack_category_analysis.csv")

print("\n" + "="*70)
print("✅ ANALYSIS COMPLETE")
print("="*70)
