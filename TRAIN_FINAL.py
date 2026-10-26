"""
Final Training - Use ALL 2.5M data (train+val), balanced 50/50
Test on remaining test set
"""

import numpy as np
from stable_baselines3 import PPO
from src.rl_agent.environment import FirewallEnv

print("="*70)
print("FINAL TRAINING - ALL 2.5M DATA, BALANCED")
print("="*70)

# Load train + val (use for training)
print("\nLoading training data (train + val)...")
X_train = np.load("data/processed/X_train.npy")
y_train = np.load("data/processed/y_train_binary.npy")
X_val = np.load("data/processed/X_val.npy")
y_val = np.load("data/processed/y_val_binary.npy")

# Combine train and val
X_all = np.concatenate([X_train, X_val])
y_all = np.concatenate([y_train, y_val])

print(f"Total available: {len(y_all):,} samples")

# Separate by class
benign_idx = np.where(y_all == 0)[0]
attack_idx = np.where(y_all == 1)[0]

print(f"\nOriginal distribution:")
print(f"  Benign: {len(benign_idx):,} ({len(benign_idx)/len(y_all)*100:.1f}%)")
print(f"  Attack: {len(attack_idx):,} ({len(attack_idx)/len(y_all)*100:.1f}%)")

# Balance: equal samples from each class
n_per_class = min(len(benign_idx), len(attack_idx))
print(f"\nUsing {n_per_class:,} samples per class")

benign_sample = np.random.choice(benign_idx, n_per_class, replace=False)
attack_sample = np.random.choice(attack_idx, n_per_class, replace=False)

# Combine and shuffle
balanced_idx = np.concatenate([benign_sample, attack_sample])
np.random.shuffle(balanced_idx)

X_balanced = X_all[balanced_idx]
y_balanced = y_all[balanced_idx]

print(f"\nFinal training set:")
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
    batch_size=128,
    n_epochs=10,
    gamma=0.99,
    verbose=1
)

# Train - more timesteps for larger dataset
timesteps = min(2_000_000, len(y_balanced) * 3)  # See each sample ~3 times

print("\n" + "="*70)
print("TRAINING")
print("="*70)
print(f"\nTotal timesteps: {timesteps:,}")
print(f"Training samples: {len(y_balanced):,}")
print(f"Epochs: ~{timesteps/len(y_balanced):.1f}")
print(f"\nReward structure:")
print(f"  BLOCK attack: +15")
print(f"  ALLOW benign: +1")
print(f"  BLOCK benign: -5")
print(f"  ALLOW attack: -25")
print()

model.learn(
    total_timesteps=timesteps,
    progress_bar=True
)

# Save
print("\nSaving model...")
model.save("models/firewall_final_balanced")
print("✓ Model saved: models/firewall_final_balanced.zip")

print("\n" + "="*70)
print("✅ TRAINING COMPLETE")
print("="*70)
print(f"\nTrained on: {len(y_balanced):,} samples (balanced)")
print(f"Test set: 424K samples (separate)")
print("\nNext: python src/rl_agent/evaluate.py")
