#!/usr/bin/env python3
"""Synchronous training - smaller scale for testing"""
import torch
import numpy as np
import sys
import os
sys.path.append('src')

# Force unbuffered output
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)
sys.stderr = os.fdopen(sys.stderr.fileno(), 'w', buffering=1)

print("="*70)
print("STARTING TRAINING")
print("="*70)

from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from rl_agent.environment import FirewallEnv

print("\n[1/5] Loading data...")
X = np.load("data/processed/X_train.npy")
y = np.load("data/processed/y_train_binary.npy")
print(f"✓ Loaded {len(X):,} samples")

print("\n[2/5] Creating environment...")
env = FirewallEnv(X, y, shuffle=True)
vec_env = DummyVecEnv([lambda: env])
print("✓ Environment ready")

print("\n[3/5] Creating model...")
model = PPO('MlpPolicy', vec_env, verbose=1, device='cpu',
            n_steps=2048, batch_size=64)
print("✓ Model created")

print("\n[4/5] Training for 500,000 steps...")
print("This will take 30-60 minutes...")
print()

os.makedirs("models", exist_ok=True)

model.learn(total_timesteps=500_000, progress_bar=True, log_interval=10)

print("\n[5/5] Saving model...")
model.save("models/firewall_final")
print("✓ Model saved to: models/firewall_final.zip")

print("\n" + "="*70)
print("TRAINING COMPLETE!")
print("="*70)
