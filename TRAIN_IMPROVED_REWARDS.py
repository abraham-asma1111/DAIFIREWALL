#!/usr/bin/env python3
"""
Training with Improved Reward Function
Goal: Recall > 80%, FPR < 3%, F1 > 0.85

Previous attempt (firewall_natural.zip):
  Recall: 61.3%, FPR: 1.08%, F1: 0.740
  Problem: Too conservative (blocks only high-confidence attacks)

Solution: Increase penalty for missing attacks, increase reward for catching attacks
"""

import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.callbacks import CheckpointCallback
import sys
import os

# Create modified environment with improved rewards
import gymnasium as gym
from gymnasium import spaces

class ImprovedFirewallEnv(gym.Env):
    """
    Firewall Environment with IMPROVED reward structure
    
    Key Changes from Previous:
    - ALLOW attack: -28 (was -25) - make missing attacks WORSE
    - BLOCK attack: +13 (was +10) - reward catching attacks MORE
    - BLOCK benign: -18 (was -20) - slightly reduce FP penalty
    
    Expected behavior: Agent will be more aggressive in blocking suspicious traffic
    """
    
    metadata = {"render_modes": ["human"]}
    
    def __init__(self, X_data, y_data, shuffle=True):
        super().__init__()
        
        self.X_data = X_data
        self.y_data = y_data
        self.n_samples = len(X_data)
        self.shuffle = shuffle
        
        self.observation_space = spaces.Box(low=0.0, high=1.0, shape=(20,), dtype=np.float32)
        self.action_space = spaces.Discrete(4)
        
        self.current_step = 0
        self.max_steps = self.n_samples
        self.sample_indices = np.arange(self.n_samples)
        
        self.episode_stats = {
            'correct_blocks': 0,
            'correct_allows': 0,
            'false_positives': 0,
            'false_negatives': 0,
            'rate_limits': 0,
            'flags': 0,
            'total_reward': 0
        }
        
    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        
        if self.shuffle:
            np.random.shuffle(self.sample_indices)
        
        self.current_step = 0
        self.episode_stats = {
            'correct_blocks': 0,
            'correct_allows': 0,
            'false_positives': 0,
            'false_negatives': 0,
            'rate_limits': 0,
            'flags': 0,
            'total_reward': 0
        }
        
        idx = self.sample_indices[self.current_step]
        observation = self.X_data[idx].astype(np.float32)
        
        return observation, {}
    
    def step(self, action):
        idx = self.sample_indices[self.current_step]
        true_label = self.y_data[idx]
        
        reward = self._calculate_reward(action, true_label)
        self._update_stats(action, true_label)
        self.episode_stats['total_reward'] += reward
        
        self.current_step += 1
        terminated = self.current_step >= self.max_steps
        truncated = False
        
        if not terminated:
            idx = self.sample_indices[self.current_step]
            observation = self.X_data[idx].astype(np.float32)
        else:
            observation = np.zeros(20, dtype=np.float32)
        
        info = {
            'true_label': int(true_label),
            'action_taken': int(action),
            'is_correct': self._is_correct_decision(action, true_label)
        }
        
        return observation, reward, terminated, truncated, info
    
    def _calculate_reward(self, action, true_label):
        """
        IMPROVED REWARD STRUCTURE
        Goal: Push recall from 61% to 80%+ while keeping FPR < 3%
        """
        is_attack = (true_label == 1)
        
        if action == 0:  # ALLOW
            if is_attack:
                return -28  # INCREASED from -25 (missing attacks is worse)
            else:
                return +2   # Normal operation
        
        elif action == 1:  # BLOCK
            if is_attack:
                return +13  # INCREASED from +10 (catching attacks rewarded more)
            else:
                return -18  # DECREASED from -20 (FP slightly less bad)
        
        elif action == 2:  # RATE_LIMIT
            if is_attack:
                return +8   # Good defensive action
            else:
                return -4   # Minor disruption
        
        elif action == 3:  # FLAG_MONITOR
            if is_attack:
                return +4   # At least caught it
            else:
                return -1   # Wasted resources
        
        return 0
    
    def _is_correct_decision(self, action, true_label):
        is_attack = (true_label == 1)
        
        if action == 0:
            return not is_attack
        elif action == 1:
            return is_attack
        elif action in [2, 3]:
            return is_attack
        
        return False
    
    def _update_stats(self, action, true_label):
        is_attack = (true_label == 1)
        
        if action == 0:
            if is_attack:
                self.episode_stats['false_negatives'] += 1
            else:
                self.episode_stats['correct_allows'] += 1
        elif action == 1:
            if is_attack:
                self.episode_stats['correct_blocks'] += 1
            else:
                self.episode_stats['false_positives'] += 1
        elif action == 2:
            self.episode_stats['rate_limits'] += 1
        elif action == 3:
            self.episode_stats['flags'] += 1
    
    def get_episode_stats(self):
        total_decisions = self.current_step
        if total_decisions == 0:
            return self.episode_stats
        
        stats = self.episode_stats.copy()
        
        tp = stats['correct_blocks']
        fp = stats['false_positives']
        fn = stats['false_negatives']
        tn = stats['correct_allows']
        
        stats['precision'] = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        stats['recall'] = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        
        p = stats['precision']
        r = stats['recall']
        stats['f1_score'] = 2 * (p * r) / (p + r) if (p + r) > 0 else 0.0
        
        correct = stats['correct_blocks'] + stats['correct_allows']
        stats['accuracy'] = correct / total_decisions if total_decisions > 0 else 0.0
        stats['fpr'] = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        
        return stats


print("\n" + "="*70)
print("FIREWALL AI - IMPROVED REWARD TRAINING")
print("="*70)

print("\n📊 Previous Results (firewall_natural.zip):")
print("   Recall: 61.3% ❌ (too low)")
print("   FPR: 1.08% ✓ (good)")
print("   F1: 0.740 ❌ (below target 0.85)")
print("\n   Problem: Agent too conservative, misses 39% of attacks")

print("\n🎯 Target Metrics:")
print("   Recall: > 80% (catch most attacks)")
print("   FPR: < 3% (acceptable false positives)")
print("   F1: > 0.85 (balanced performance)")

print("\n💡 Solution: Adjusted reward function")
print("   Changes:")
print("   - ALLOW attack: -28 (was -25) → Missing attacks hurts MORE")
print("   - BLOCK attack: +13 (was +10) → Catching attacks rewards MORE")
print("   - BLOCK benign: -18 (was -20) → False positives slightly less bad")
print("\n   Expected: Agent will be more aggressive at blocking attacks")

# Load training data
print("\n📊 Loading training data...")
X_train = np.load("data/processed/X_train.npy")
y_train = np.load("data/processed/y_train_binary.npy")
X_val = np.load("data/processed/X_val.npy")
y_val = np.load("data/processed/y_val_binary.npy")

X_combined = np.vstack([X_train, X_val])
y_combined = np.concatenate([y_train, y_val])

benign_count = (y_combined == 0).sum()
attack_count = (y_combined == 1).sum()
benign_pct = benign_count / len(y_combined) * 100
attack_pct = attack_count / len(y_combined) * 100

print(f"   Total samples: {len(X_combined):,}")
print(f"   Distribution: {benign_pct:.1f}% benign, {attack_pct:.1f}% attack")
print("   ✓ Natural distribution (matches real-world traffic)")

# Create environment
print("\n🎮 Creating environment with improved rewards...")
env = ImprovedFirewallEnv(X_combined, y_combined, shuffle=True)
vec_env = DummyVecEnv([lambda: env])

# Create checkpoints directory
os.makedirs("models/improved_checkpoints", exist_ok=True)

# Checkpoint callback (save every 500k steps)
checkpoint_callback = CheckpointCallback(
    save_freq=500000,
    save_path="models/improved_checkpoints/",
    name_prefix="firewall_improved"
)

# Training configuration
print("\n🏋️ Training configuration:")
print("   Algorithm: PPO")
print("   Total timesteps: 3,000,000")
print("   Learning rate: 0.0003")
print("   Batch size: 64")
print("   Training time: ~50-60 minutes")

# Create PPO model
print("\n🤖 Initializing PPO model...")
model = PPO(
    "MlpPolicy",
    vec_env,
    learning_rate=0.0003,
    n_steps=2048,
    batch_size=64,
    n_epochs=10,
    gamma=0.99,
    verbose=1,
    tensorboard_log="./logs/tensorboard/"
)

print("   ✓ Model initialized")

# Train
print("\n🚀 Starting training...")
print("   Progress will be shown below:")
print("   Checkpoints saved every 500k timesteps\n")

try:
    model.learn(
        total_timesteps=3_000_000,
        callback=checkpoint_callback,
        progress_bar=True
    )
    
    print("\n💾 Saving final model...")
    model.save("models/firewall_improved")
    print("   ✓ Model saved: models/firewall_improved.zip")
    
    print("\n" + "="*70)
    print(" TRAINING COMPLETE")
    print("="*70)
    print(f"\nTrained on: {len(X_combined):,} samples")
    print(f"Distribution: {benign_pct:.1f}% benign, {attack_pct:.1f}% attack")
    print("\nImproved Rewards:")
    print("  - ALLOW attack: -28 (was -25)")
    print("  - BLOCK attack: +13 (was +10)")
    print("  - BLOCK benign: -18 (was -20)")
    print("\nNext steps:")
    print("  1. Evaluate: /home/abraham/miniconda3/envs/firewall/bin/python src/rl_agent/evaluate.py")
    print("  2. Expected improvement:")
    print("     - Recall: 75-85% (up from 61%)")
    print("     - FPR: 2-3% (slightly up from 1%)")
    print("     - F1: 0.82-0.87 (up from 0.74)")
    print()
    
except KeyboardInterrupt:
    print("\n⚠️ Training interrupted!")
    print("💾 Saving interrupted model...")
    model.save("models/firewall_improved_interrupted")
    print("   ✓ Model saved: models/firewall_improved_interrupted.zip")
    sys.exit(1)
