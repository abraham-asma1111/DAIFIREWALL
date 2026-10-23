"""
Quick training test - Train for 10k steps to verify everything works
Before running the full 500k training
"""

# CRITICAL: Set environment variables BEFORE any imports
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
os.environ['OMP_NUM_THREADS'] = '4'

import numpy as np
import sys

from stable_baselines3 import PPO
from stable_baselines3.common.monitor import Monitor

sys.path.append('src')
from rl_agent.environment import FirewallEnv

print("="*70)
print("QUICK TRAINING TEST - 10,000 timesteps")
print("="*70)

print("\n[1/4] Loading small subset of data...")
X_train = np.load("data/processed/X_train.npy")[:10000]  # Only 10k samples
y_train = np.load("data/processed/y_train_binary.npy")[:10000]
print(f"      ✓ Data loaded: {X_train.shape}")

print("\n[2/4] Creating environment...")
env = FirewallEnv(X_train, y_train, shuffle=True)
env = Monitor(env)
print("      ✓ Environment created")

print("\n[3/4] Creating PPO model...")
model = PPO(
    policy="MlpPolicy",
    env=env,
    learning_rate=3e-4,
    n_steps=2048,
    batch_size=64,
    verbose=1,
    device="cpu"
)
print("      ✓ Model created")

print("\n[4/4] Training (this takes ~2-3 minutes)...\n")

try:
    model.learn(total_timesteps=10_000, progress_bar=True)
    print("\n" + "="*70)
    print("✓ QUICK TEST COMPLETE!")
    print("="*70)
    print("\nEverything works! You can now run the full training:")
    print("  python src/rl_agent/train.py")
    print()
except Exception as e:
    print(f"\n✗ Error during training: {e}")
    import traceback
    traceback.print_exc()
