#!/usr/bin/env python3
"""
Model Evaluation with Bayesian Risk-Based Guard
Uses cost-sensitive risk minimization to optimize model decisions
Target: Recall > 85%, FPR < 5%, F1 > 0.85
"""

import numpy as np
import sys
import os
import torch as th
from stable_baselines3 import PPO
from src.rl_agent.environment import FirewallEnv
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, classification_report
from datetime import datetime
import json

print("\n" + "="*70)
print("FIREWALL AI - EVALUATION WITH BAYESIAN RISK GUARD")
print("="*70)


class BayesianRiskDecisionGuard:
    """
    Applies cost-sensitive risk reduction to Stable-Baselines3 probability matrices
    to drive FPR below 5% while keeping threat Recall above 85%.
    
    Uses Bayesian Risk Minimization: selects action that minimizes expected cost
    """
    
    def __init__(self, target_fpr=0.05):
        self.target_fpr = target_fpr
        
        # Asymmetrical Cost Matrix Configuration
        # [Action Rows: 0=ALLOW, 1=BLOCK, 2=RATE_LIMIT, 3=FLAG] x [True Class Columns: 0=Benign, 1=Attack]
        self.cost_matrix = np.array([
            [0.0,  50.0],  # Row 0 (ALLOW): Low cost for benign, HIGH penalty for missing an attack
            [15.0,  0.0],  # Row 1 (BLOCK): Moderate cost for blocking clean user, zero cost for stopping threats
            [3.0,  10.0],  # Row 2 (RATE_LIMIT): Low friction for clean users, minor penalty if attack leaks
            [1.0,  20.0]   # Row 3 (FLAG): Minimal friction for clean users, moderate penalty for passive tracking
        ])
        
        # Track statistics
        self.stats = {
            'total_decisions': 0,
            'risk_overrides': 0,
            'actions_kept': 0,
            'allow_to_block': 0,
            'block_to_allow': 0,
            'soft_to_block': 0
        }
        
        print(f"[PATCH ENGAGED] Bayesian Risk Calibration Engine initialized")
        print(f"  Target FPR: {target_fpr*100:.1f}%")
        print(f"\n  Cost Matrix (Actions x Classes):")
        print(f"            Benign  Attack")
        print(f"  ALLOW     {self.cost_matrix[0,0]:.1f}    {self.cost_matrix[0,1]:.1f}")
        print(f"  BLOCK     {self.cost_matrix[1,0]:.1f}    {self.cost_matrix[1,1]:.1f}")
        print(f"  RATE_LIM  {self.cost_matrix[2,0]:.1f}    {self.cost_matrix[2,1]:.1f}")
        print(f"  FLAG      {self.cost_matrix[3,0]:.1f}    {self.cost_matrix[3,1]:.1f}")
    
    def select_optimal_action(self, raw_action_probabilities, original_action=None):
        """
        Calculates the expected operational risk for each action choice.
        Selects the action that minimizes overall risk.
        
        Args:
            raw_action_probabilities: tensor/array [4] with probabilities for each action
            original_action: int, the model's original choice (for statistics)
        
        Returns:
            optimal_action: int (0-3) that minimizes expected risk
        """
        self.stats['total_decisions'] += 1
        
        # Convert the categorical probabilities to numpy format
        if isinstance(raw_action_probabilities, th.Tensor):
            probs = raw_action_probabilities.detach().cpu().numpy().flatten()
        else:
            probs = np.array(raw_action_probabilities).flatten()
        
        # Ensure probabilities sum to 1 (numerical stability)
        probs = probs / (probs.sum() + 1e-10)
        
        # Extrapolate binary class expectations from multi-action distribution
        # The model's action probabilities tell us how likely it thinks there's an attack
        # BLOCK action = high attack probability
        # ALLOW action = high benign probability
        # RATE_LIMIT/FLAG = uncertain, moderate attack probability
        p_attack = probs[1] + 0.5 * probs[2] + 0.3 * probs[3]  # Weighted combination
        p_benign = 1.0 - p_attack
        p_vector = np.array([p_benign, p_attack])
        
        # Calculate expected risk for each action: R(a) = Sum_s ( Cost(a,s) * P(s) )
        # This is the core of Bayesian decision theory
        expected_risks = np.dot(self.cost_matrix, p_vector)
        
        # Select action with minimum expected risk
        optimal_action = int(np.argmin(expected_risks))
        
        # Track overrides
        if original_action is not None and optimal_action != original_action:
            self.stats['risk_overrides'] += 1
            
            # Track specific override types
            if original_action == 0 and optimal_action == 1:
                self.stats['allow_to_block'] += 1
            elif original_action == 1 and optimal_action == 0:
                self.stats['block_to_allow'] += 1
            elif original_action in [2, 3] and optimal_action == 1:
                self.stats['soft_to_block'] += 1
        else:
            self.stats['actions_kept'] += 1
        
        return optimal_action
    
    def get_stats(self):
        """Return guard statistics"""
        total = self.stats['total_decisions']
        return {
            **self.stats,
            'override_rate': (self.stats['risk_overrides'] / total * 100) if total > 0 else 0
        }


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

# Create Bayesian risk-based guard
print("\n🛡️ Initializing Bayesian Risk Decision Guard...")
guard = BayesianRiskDecisionGuard(target_fpr=0.05)

# Create environment
print("\n🎮 Creating test environment...")
env = FirewallEnv(X_test, y_test, shuffle=False)
print("   ✓ Environment ready")

# Evaluate with Bayesian guard
print("\n🔍 Evaluating model with Bayesian risk minimization...")
print("   Processing 424K samples (this will take a few minutes)...\n")

obs, info = env.reset()
y_pred = []
y_true = []

for i in range(len(X_test)):
    # Convert observation to tensor
    obs_tensor = th.as_tensor(obs, dtype=th.float32).to(model.device).reshape(1, -1)
    
    # Get raw action probabilities from policy (NOT deterministic to get distributions)
    with th.no_grad():
        # Get the policy distribution
        distribution = model.policy.get_distribution(obs_tensor)
        action_probs = distribution.distribution.probs[0]
    
    # Get model's original action
    original_action = int(th.argmax(action_probs).item())
    
    # Apply Bayesian risk minimization
    optimal_action = guard.select_optimal_action(action_probs, original_action)
    
    # Record prediction (binary: BLOCK=1, others=0)
    y_pred.append(1 if optimal_action == 1 else 0)
    y_true.append(y_test[i])
    
    # Step environment with optimal action
    obs, reward, terminated, truncated, info = env.step(optimal_action)
    
    if (i + 1) % 50000 == 0:
        print(f"   Progress: {i+1:,}/{len(X_test):,} samples ({(i+1)/len(X_test)*100:.1f}%)")
    
    if terminated:
        obs, info = env.reset()

y_pred = np.array(y_pred)
y_true = np.array(y_true)

# Calculate metrics
print("\n" + "="*70)
print("EVALUATION RESULTS WITH BAYESIAN RISK GUARD")
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

# Guard statistics
guard_stats = guard.get_stats()
print("\nBayesian Risk Guard Statistics:")
print(f"  Total decisions: {guard_stats['total_decisions']:,}")
print(f"  Risk-based overrides: {guard_stats['risk_overrides']:,}")
print(f"  Actions kept: {guard_stats['actions_kept']:,}")
print(f"  ALLOW→BLOCK: {guard_stats['allow_to_block']:,}")
print(f"  BLOCK→ALLOW: {guard_stats['block_to_allow']:,}")
print(f"  Soft→BLOCK: {guard_stats['soft_to_block']:,}")
print(f"  Override rate: {guard_stats['override_rate']:.2f}%")

# Target metrics check
print("\n" + "="*70)
print("TARGET METRICS (from requirements)")
print("="*70)
print(f"  Recall:     {recall:.4f} (target: > 0.85) {'✅ PASS' if recall > 0.85 else '❌ FAIL'}")
print(f"  FPR:        {fpr:.4f} (target: < 0.05) {'✅ PASS' if fpr < 0.05 else '❌ FAIL'}")
print(f"  F1 Score:   {f1:.4f} (target: > 0.85) {'✅ PASS' if f1 > 0.85 else '❌ FAIL'}")

# Overall assessment
passes = sum([recall > 0.85, fpr < 0.05, f1 > 0.85])
if passes == 3:
    print(f"\n✅✅✅ PRODUCTION READY - ALL TARGETS MET ({passes}/3)")
    status = "PRODUCTION_READY"
elif passes == 2:
    print(f"\n✅ PILOT READY - Most targets met ({passes}/3)")
    status = "PILOT_READY"
else:
    print(f"\n⚠️ NEEDS TUNING - ({passes}/3 targets met)")
    status = "NEEDS_TUNING"

# Comparison
print("\n" + "="*70)
print("IMPROVEMENT COMPARISON")
print("="*70)
print(f"  Without Guard:     Recall 90.73%, FPR 18.47%, F1 0.682")
print(f"  With Bayesian Guard: Recall {recall*100:.2f}%, FPR {fpr*100:.2f}%, F1 {f1:.3f}")
print(f"\n  FPR Reduction: {18.47 - fpr*100:.2f} percentage points")
print(f"  Recall Change: {(recall*100 - 90.73):.2f} percentage points")
print(f"  F1 Improvement: {(f1 - 0.682)*100:.2f} percentage points")

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

title_text = f'Confusion Matrix (Bayesian Risk Guard)\n'
title_text += f'Recall={recall:.4f}, FPR={fpr:.4f}, F1={f1:.4f}\n'
if passes == 3:
    title_text += '✅ PRODUCTION READY - ALL TARGETS MET'
elif passes == 2:
    title_text += '✅ PILOT READY'
else:
    title_text += '⚠️ NEEDS TUNING'
plt.title(title_text)
plt.ylabel('True Label')
plt.xlabel('Predicted Label')
plt.tight_layout()

plot_path = f"logs/confusion_matrix_bayesian_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
plt.savefig(plot_path, dpi=150)
print(f"   ✓ Plot saved: {plot_path}")

# Save metrics to file
metrics_path = "logs/evaluation_metrics_bayesian.txt"
with open(metrics_path, 'w') as f:
    f.write("FIREWALL AI - EVALUATION RESULTS (BAYESIAN RISK GUARD)\n")
    f.write("="*70 + "\n\n")
    f.write(f"Model: {model_path}.zip + BayesianRiskDecisionGuard\n")
    f.write(f"Evaluation Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"Test Samples: {len(X_test):,}\n")
    f.write(f"Status: {status}\n\n")
    f.write("Metrics:\n")
    f.write(f"  Accuracy:  {accuracy:.4f}\n")
    f.write(f"  Precision: {precision:.4f}\n")
    f.write(f"  Recall:    {recall:.4f}\n")
    f.write(f"  F1 Score:  {f1:.4f}\n")
    f.write(f"  FPR:       {fpr:.4f}\n\n")
    f.write("Target Metrics:\n")
    f.write(f"  Recall > 0.85: {'✅ PASS' if recall > 0.85 else '❌ FAIL'}\n")
    f.write(f"  FPR < 0.05: {'✅ PASS' if fpr < 0.05 else '❌ FAIL'}\n")
    f.write(f"  F1 > 0.85: {'✅ PASS' if f1 > 0.85 else '❌ FAIL'}\n\n")
    f.write("Confusion Matrix:\n")
    f.write(f"  TN: {tn:,}  FP: {fp:,}\n")
    f.write(f"  FN: {fn:,}  TP: {tp:,}\n\n")
    f.write("Guard Statistics:\n")
    for key, value in guard_stats.items():
        f.write(f"  {key}: {value}\n")
    f.write("\n")
    f.write(classification_report(y_true, y_pred, target_names=['BENIGN', 'ATTACK']))

print(f"   ✓ Metrics saved: {metrics_path}")

# Save JSON performance log
json_path = "logs/performance_verification.json"
performance_data = {
    "model": model_path + ".zip",
    "guard_type": "BayesianRiskDecisionGuard",
    "evaluation_date": datetime.now().isoformat(),
    "test_samples": int(len(X_test)),
    "metrics": {
        "accuracy": float(accuracy),
        "precision": float(precision),
        "recall": float(recall),
        "f1_score": float(f1),
        "fpr": float(fpr)
    },
    "confusion_matrix": {
        "true_negatives": int(tn),
        "false_positives": int(fp),
        "false_negatives": int(fn),
        "true_positives": int(tp)
    },
    "target_status": {
        "recall_pass": bool(recall > 0.85),
        "fpr_pass": bool(fpr < 0.05),
        "f1_pass": bool(f1 > 0.85),
        "overall_status": status,
        "targets_met": f"{passes}/3"
    },
    "guard_statistics": guard_stats,
    "comparison": {
        "without_guard": {"recall": 0.9073, "fpr": 0.1847, "f1": 0.682},
        "with_guard": {"recall": float(recall), "fpr": float(fpr), "f1": float(f1)},
        "improvements": {
            "fpr_reduction_pp": float(18.47 - fpr*100),
            "recall_change_pp": float(recall*100 - 90.73),
            "f1_improvement_pp": float((f1 - 0.682)*100)
        }
    }
}

with open(json_path, 'w') as f:
    json.dump(performance_data, f, indent=2)
print(f"   ✓ JSON log saved: {json_path}")

print("\n" + "="*70)
print("✅ EVALUATION COMPLETE")
print("="*70)
print(f"\nResults:")
print(f"  - Confusion matrix: {plot_path}")
print(f"  - Metrics file: {metrics_path}")
print(f"  - JSON verification: {json_path}")
print()
