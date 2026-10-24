"""
Fast Training - Optimized for Quick Results
Uses smaller subset, no eval callback
"""

import numpy as np
from stable_baselines3 import PPO
from src.rl_agent.environment import FirewallEnv

print("="*70)
print("FAST TRAINING - OPTIMIZED FOR SPEED")
print("="*70)

# Load subset of data for faster training
print("\nLoading data subset...")
X_train = np.load("data/processed/X_train.npy")
y_train = np.load("data/processed/y_train_binary.npy")

# Use only 500K samples for faster training
sample_size = 500000
indices = np.random.choice(len(X_train), sample_size, replace=False)
X_train_subset = X_train[indices]
y_train_subset = y_train[indices]

print(f"Training samples: {len(X_train_subset):,} (subset)")

# Create environment
print("\nCreating environment...")
env = FirewallEnv(X_train_subset, y_train_subset, shuffle=True)

# Create model - simpler config, no callbacks
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

# Train - fewer timesteps, faster convergence
print("\n" + "="*70)
print("TRAINING")
print("="*70)
print(f"\nTotal timesteps: 1,000,000")
print(f"Expected time: ~20 minutes\n")

model.learn(
    total_timesteps=1_000_000,
    progress_bar=True
)

# Save
print("\nSaving model...")
model.save("models/firewall_fast")
print("✓ Model saved: models/firewall_fast.zip")

print("\n" + "="*70)
print("✅ TRAINING COMPLETE")
print("="*70)
print("\nNext: python src/rl_agent/evaluate.py")
