"""Test if PPO can be created without crashes"""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'

print("Step 1: Import gym...")
import gymnasium as gym

print("Step 2: Create CartPole env...")
env = gym.make('CartPole-v1')

print("Step 3: Import PPO...")
from stable_baselines3 import PPO

print("Step 4: Create PPO model...")
model = PPO('MlpPolicy', env, verbose=0, device='cpu')

print("✓ SUCCESS! PPO works")
print("\nNow trying with custom environment...")

import numpy as np
import sys
sys.path.append('src')
from rl_agent.environment import FirewallEnv

X_small = np.random.rand(100, 20).astype(np.float32)
y_small = np.random.randint(0, 2, 100)

print("Creating FirewallEnv...")
firewall_env = FirewallEnv(X_small, y_small, shuffle=False)

print("Creating PPO with FirewallEnv...")
model2 = PPO('MlpPolicy', firewall_env, verbose=0, device='cpu')

print("✓ SUCCESS! Custom environment works too!")
print("\nYou can now run: python train_simple.py")
