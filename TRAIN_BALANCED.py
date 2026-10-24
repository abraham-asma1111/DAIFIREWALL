"""
Balanced Training - Equal attack/benign samples
Fixes class imbalance issue
"""

import numpy as np
from stable_baselines3 import PPO
from src.rl_agent.environment import FirewallEnv

print("="*70)
print("BALANCED TRAINING - 50% ATTACK / 50% BENIGN")
print("="*70)

# Load all data
print("\nLoading data...")
X_train = np.load("data/processed/X_train.npy")
y_train = np.load("data/processed/y_train_binary.npy")

# Separate by class
benign_idx = np.where(y_train == 0)[0]
attack_idx = np.where(y_train == 1)[0]

print(f"Original distribution:")
print(f"  Benign: {len(benign_idx):,} ({len(benign_idx)/len(y_train)*100:.1f}%)")
print(f"  Attack: {len(attack_idx):,} ({len(attack_idx)/len(y_train)*100:.1f}%)")

# Balance: use all attacks, sample equal number of benign
n_samples_per_class = min(len(benign_idx), len(attack_idx))
n_samples_per_class = min(n_samples_per_class, 250000)  # Cap at 250K each for speed

benign_sample = np.random.choice(benign_idx, n_samples_per_class, replace=False)
attack_sample = np.random.choice(attack_idx, n_samples_per_class, replace=False)

# Combine and shuffle
balanced_idx = np.concatenate([benign_sample, attack_sample])
np.random.shuffle(balanced_idx)

X_balanced = X_train[balanced_idx]
y_balanced = y_train[balanced_idx]

print(f"\nBalanced dataset:")
print(f"  Total: {len(y_balanced):,}")
print(f"  Benign: {(y_balanced==0).sum():,} ({(y_balanced==0).sum()/len(y_balanced)*100:.1f}%)")
print(f"  Attack: {(y_balanced==1).sum():,} ({(y_balanced==1).sum()/len(y_balanced)*100:.1f}%)")

# Create environment
print("\nCreating environment...")
env = FirewallEnv(X_balanced, y_balanced, shuffle=True)

# Create model
print("\nInitializing PPO model...")
model = PPO(
    "MlpPolicy",
    env,
    learning_rate=3e-4,
    n_steps=2048,
    batch_size=64,
    n_epochs=5,
    gamma=0.99,
    verbose=1
)

# Train
print("\n" + "="*70)
print("TRAINING")
print("="*70)
print(f"\nTotal timesteps: 1,000,000")
print(f"Reward structure:")
print(f"  BLOCK attack: +15")
print(f"  ALLOW benign: +1")
print(f"  BLOCK benign: -5")
print(f"  ALLOW attack: -25")
print()

model.learn(
    total_timesteps=1_000_000,
    progress_bar=True
)

# Save
print("\nSaving model...")
model.save("models/firewall_balanced")
print("✓ Model saved: models/firewall_balanced.zip")

print("\n" + "="*70)
print("✅ TRAINING COMPLETE")
print("="*70)
print("\nNext: python src/rl_agent/evaluate.py")
