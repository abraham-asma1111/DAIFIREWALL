#!/usr/bin/env python3
"""
Training on ALL 2.8M samples (train + val + test combined)
For maximum learning from the entire CICIDS 2017 dataset
"""
import torch
import numpy as np
import sys
import os
sys.path.append('src')

# Force unbuffered output
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)
sys.stderr = os.fdopen(sys.stderr.fileno(), 'w', buffering=1)

print("="*70)
print("TRAINING ON ALL 2.8M SAMPLES")
print("="*70)

from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from rl_agent.environment import FirewallEnv
from datetime import datetime

print("\n[1/6] Loading ALL data (train + val + test)...")
X_train = np.load("data/processed/X_train.npy")
y_train = np.load("data/processed/y_train_binary.npy")
print(f"   ✓ Train: {len(X_train):,} samples")

X_val = np.load("data/processed/X_val.npy")
y_val = np.load("data/processed/y_val_binary.npy")
print(f"   ✓ Val:   {len(X_val):,} samples")

X_test = np.load("data/processed/X_test.npy")
y_test = np.load("data/processed/y_test_binary.npy")
print(f"   ✓ Test:  {len(X_test):,} samples")

# Combine all data
X_all = np.concatenate([X_train, X_val, X_test], axis=0)
y_all = np.concatenate([y_train, y_val, y_test], axis=0)
print(f"\n   ✅ TOTAL: {len(X_all):,} samples")
print(f"      Benign: {(y_all==0).sum():,} ({(y_all==0).sum()/len(y_all)*100:.1f}%)")
print(f"      Attack: {(y_all==1).sum():,} ({(y_all==1).sum()/len(y_all)*100:.1f}%)")

print("\n[2/6] Creating environment with ALL data...")
env = FirewallEnv(X_all, y_all, shuffle=True)
vec_env = DummyVecEnv([lambda: env])
print("   ✓ Environment ready")

print("\n[3/6] Creating PPO model...")
model = PPO('MlpPolicy', vec_env, verbose=1, device='cpu',
            learning_rate=3e-4,
            n_steps=2048,
            batch_size=64,
            n_epochs=10,
            gamma=0.99,
            gae_lambda=0.95,
            clip_range=0.2)
n_params = sum(p.numel() for p in model.policy.parameters())
print(f"   ✓ Model created with {n_params:,} parameters")

print("\n[4/6] Preparing directories...")
os.makedirs("models", exist_ok=True)
os.makedirs("logs", exist_ok=True)
print("   ✓ Directories ready")

# Calculate timesteps to see all data at least once
# To see each sample at least once, we need len(X_all) timesteps
# But PPO works best with more passes, so let's do 2-3x
timesteps = 2_800_000  # See each sample ~1 time (can increase to 5M or 10M for more passes)

print("\n[5/6] Training...")
print("="*70)
start = datetime.now()
print(f"   Start time: {start.strftime('%H:%M:%S')}")
print(f"   Total samples: {len(X_all):,}")
print(f"   Total timesteps: {timesteps:,}")
print(f"   Estimated time: 60-90 minutes on CPU")
print("="*70)
print()

try:
    model.learn(total_timesteps=timesteps, progress_bar=True, log_interval=10)
    
    # Save model
    print("\n[6/6] Saving model...")
    model.save("models/firewall_all_data")
    end = datetime.now()
    duration = (end - start).total_seconds() / 60
    
    print("\n" + "="*70)
    print("✅ TRAINING COMPLETE!")
    print("="*70)
    print(f"   End time: {end.strftime('%H:%M:%S')}")
    print(f"   Duration: {duration:.1f} minutes")
    print(f"   Model: models/firewall_all_data.zip")
    print(f"   Trained on: {len(X_all):,} samples")
    
    # Get final stats
    stats = env.get_episode_stats()
    print(f"\n   Final Stats:")
    print(f"      Accuracy:  {stats['accuracy']:.4f}")
    print(f"      Precision: {stats['precision']:.4f}")
    print(f"      Recall:    {stats['recall']:.4f}")
    print(f"      F1 Score:  {stats['f1_score']:.4f}")
    print(f"      FPR:       {stats['fpr']:.4f}")
    print()
    
except KeyboardInterrupt:
    print("\n⚠️  Training interrupted!")
    model.save("models/firewall_all_data_interrupted")
    print("   Model saved: models/firewall_all_data_interrupted.zip")

except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
print("NEXT STEPS")
print("="*70)
print("1. Reinstall TensorFlow: pip install tensorflow==2.21.0")
print("2. Evaluate model: python src/rl_agent/evaluate.py")
print("="*70)
