#!/usr/bin/env python3
"""
Training with Natural (Imbalanced) Distribution
Train and test on SAME distribution - no artificial balancing
"""

import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from src.rl_agent.environment import FirewallEnv
import sys

print("\n" + "="*70)
print("FIREWALL AI - NATURAL DISTRIBUTION TRAINING")
print("="*70)

# Load training data (NO BALANCING)
print("\n📊 Loading training data (natural distribution)...")
X_train = np.load("data/processed/X_train.npy")
y_train = np.load("data/processed/y_train_binary.npy")
X_val = np.load("data/processed/X_val.npy")
y_val = np.load("data/processed/y_val_binary.npy")

print(f"   Train: {len(X_train):,} samples")
print(f"   Val:   {len(X_val):,} samples")

# Combine train + val for more data
X_combined = np.vstack([X_train, X_val])
y_combined = np.concatenate([y_train, y_val])
print(f"   Combined: {len(X_combined):,} samples")

# Check natural distribution
benign_count = (y_combined == 0).sum()
attack_count = (y_combined == 1).sum()
benign_pct = benign_count / len(y_combined) * 100
attack_pct = attack_count / len(y_combined) * 100

print(f"\n⚖️ Natural data distribution:")
print(f"   Benign: {benign_count:,} ({benign_pct:.1f}%)")
print(f"   Attack: {attack_count:,} ({attack_pct:.1f}%)")
print(f"   ✓ Training on SAME distribution as real-world traffic")

# Create environment with OPTIMIZED rewards
print("\n🎮 Creating environment with optimized rewards...")
print("\n   Reward Structure (balanced for natural distribution):")
print("   - ALLOW benign:  +2  (encourage correct allows)")
print("   - ALLOW attack:  -25 (catastrophic security failure)")
print("   - BLOCK benign:  -20 (very bad - false positive)")
print("   - BLOCK attack:  +10 (good - caught attack)")
print("   - RATE_LIMIT:    middle ground")
print("   - FLAG_MONITOR:  investigation mode")

env = FirewallEnv(X_combined, y_combined, shuffle=True)
vec_env = DummyVecEnv([lambda: env])

print("   ✓ Environment ready")

# Training configuration
print("\n🏋️ Training configuration:")
print("   Algorithm: PPO")
print("   Total timesteps: 3,000,000 (more data, more training)")
print("   Learning rate: 0.0003")
print("   Batch size: 2048")
print(f"   Training samples: {len(X_combined):,}")
print(f"   Data distribution: {benign_pct:.1f}% benign, {attack_pct:.1f}% attack")

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
print("   This will take approximately 50-60 minutes")
print("   Progress will be shown below:\n")

try:
    model.learn(total_timesteps=3_000_000, progress_bar=True)
    
    print("\n💾 Saving model...")
    model.save("models/firewall_natural")
    print("   ✓ Model saved: models/firewall_natural.zip")
    
    print("\n" + "="*70)
    print("✅ TRAINING COMPLETE")
    print("="*70)
    print(f"\nTrained on: {len(X_combined):,} samples (natural distribution)")
    print(f"Distribution: {benign_pct:.1f}% benign, {attack_pct:.1f}% attack")
    print("Test set: 424K samples (same distribution)")
    print("\nNext steps:")
    print("  1. Evaluate: /home/abraham/miniconda3/envs/firewall/bin/python src/rl_agent/evaluate.py")
    print("  2. Expected: FPR < 5%, Recall > 85%, F1 > 0.85")
    print()
    
except KeyboardInterrupt:
    print("\n⚠️ Training interrupted!")
    print("💾 Saving interrupted model...")
    model.save("models/firewall_natural_interrupted")
    print("   ✓ Model saved: models/firewall_natural_interrupted.zip")
    sys.exit(1)
