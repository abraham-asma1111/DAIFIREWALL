#!/usr/bin/env python3
"""
Optimized Training with Adjusted Rewards
Goal: F1 > 0.85, Recall > 0.85, FPR < 5%
"""

import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from src.rl_agent.environment import FirewallEnv
import sys

print("\n" + "="*70)
print("FIREWALL AI - OPTIMIZED TRAINING")
print("="*70)

# Check if data is preprocessed
print("\n🔍 Checking for preprocessed data...")
import os

data_files = [
    "data/processed/X_train.npy",
    "data/processed/y_train_binary.npy",
    "data/processed/X_val.npy",
    "data/processed/y_val_binary.npy",
    "data/processed/X_test.npy",
    "data/processed/y_test_binary.npy"
]

missing_files = [f for f in data_files if not os.path.exists(f)]

if missing_files:
    print("\n❌ ERROR: Preprocessed data not found!")
    print("\nMissing files:")
    for f in missing_files:
        print(f"   - {f}")
    print("\n⚠️ Please run preprocessing first:")
    print("   1. Download data: python data/download_data.py")
    print("   2. Preprocess: /home/abraham/miniconda3/envs/firewall/bin/python src/data/preprocessor.py")
    print()
    sys.exit(1)

print("   ✓ All data files found")

# Load training data
print("\n📊 Loading training data...")
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

# Balance the dataset
print("\n⚖️ Balancing dataset...")
benign_indices = np.where(y_combined == 0)[0]
attack_indices = np.where(y_combined == 1)[0]

print(f"   Benign samples: {len(benign_indices):,}")
print(f"   Attack samples: {len(attack_indices):,}")

# Use all data from minority class
min_samples = min(len(benign_indices), len(attack_indices))
print(f"   Using {min_samples:,} samples from each class")

# Random sample to balance
np.random.seed(42)
benign_sampled = np.random.choice(benign_indices, min_samples, replace=False)
attack_sampled = np.random.choice(attack_indices, min_samples, replace=False)

balanced_indices = np.concatenate([benign_sampled, attack_sampled])
np.random.shuffle(balanced_indices)

X_balanced = X_combined[balanced_indices]
y_balanced = y_combined[balanced_indices]

print(f"   Final balanced dataset: {len(X_balanced):,} samples")
print(f"   Benign: {(y_balanced==0).sum():,}")
print(f"   Attack: {(y_balanced==1).sum():,}")

# Create environment with OPTIMIZED rewards
print("\n🎮 Creating environment with optimized rewards...")
print("\n   Reward Structure:")
print("   - ALLOW benign:  +2  (good)")
print("   - ALLOW attack:  -25 (very bad)")
print("   - BLOCK benign:  -20 (very bad - minimize false positives)")
print("   - BLOCK attack:  +10 (good)")
print("   - RATE_LIMIT:    +1  (safe middle ground)")
print("   - FLAG_MONITOR:  +1  (safe investigation)")

env = FirewallEnv(X_balanced, y_balanced, shuffle=True)
vec_env = DummyVecEnv([lambda: env])

print("   ✓ Environment ready")

# Training configuration
print("\n🏋️ Training configuration:")
print("   Algorithm: PPO")
print("   Total timesteps: 2,000,000")
print("   Learning rate: 0.0003")
print("   Batch size: 2048")
print("   Training samples: {:,}".format(len(X_balanced)))

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
print("   This will take approximately 40 minutes")
print("   Progress will be shown below:\n")

try:
    model.learn(total_timesteps=2_000_000, progress_bar=True)
    
    print("\n💾 Saving model...")
    model.save("models/firewall_optimized")
    print("   ✓ Model saved: models/firewall_optimized.zip")
    
    print("\n" + "="*70)
    print("✅ TRAINING COMPLETE")
    print("="*70)
    print(f"\nTrained on: {len(X_balanced):,} samples (balanced)")
    print("Test set: 424K samples (separate)")
    print("\nNext steps:")
    print("  1. Evaluate: /home/abraham/miniconda3/envs/firewall/bin/python src/rl_agent/evaluate_optimized.py")
    print("  2. Check metrics: Should see FPR < 5%, F1 > 0.85")
    print()
    
except KeyboardInterrupt:
    print("\n⚠️ Training interrupted!")
    print("💾 Saving interrupted model...")
    model.save("models/firewall_optimized_interrupted")
    print("   ✓ Model saved: models/firewall_optimized_interrupted.zip")
    sys.exit(1)
