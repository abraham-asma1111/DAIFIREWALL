#!/usr/bin/env python3
"""Minimal training test - 1000 steps only"""

import torch
import numpy as np
import sys
sys.path.append('src')

print("Loading libraries...", flush=True)
from stable_baselines3 import PPO
from rl_agent.environment import FirewallEnv

print("✓ Libraries loaded\n", flush=True)

print("Loading data...", flush=True)
X = np.load("data/processed/X_train.npy")[:50000]  # Only 50k samples
y = np.load("data/processed/y_train_binary.npy")[:50000]
print(f"✓ Loaded {len(X):,} samples\n", flush=True)

print("Creating environment...", flush=True)
env = FirewallEnv(X, y, shuffle=True)
print("✓ Environment created\n", flush=True)

print("Creating PPO model (without auto-wrapper)...", flush=True)
from stable_baselines3.common.vec_env import DummyVecEnv
vec_env = DummyVecEnv([lambda: env])
model = PPO('MlpPolicy', vec_env, verbose=1, device='cpu')
print("✓ Model created\n", flush=True)

print("Training for 1,000 steps (test run)...\n", flush=True)
model.learn(total_timesteps=1000, progress_bar=True)

import os
os.makedirs("models", exist_ok=True)
model.save("models/test_model")

print("\n✓ TEST COMPLETE! Model saved to: models/test_model.zip", flush=True)
print("\nIf this worked, you can run the full 500k training!", flush=True)
