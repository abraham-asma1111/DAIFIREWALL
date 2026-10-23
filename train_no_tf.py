#!/usr/bin/env python3
"""
Training script that NEVER loads TensorFlow
Only uses PyTorch through stable-baselines3
"""

# Block TensorFlow imports completely
import sys
class BlockTensorFlow:
    def find_module(self, fullname, path=None):
        if fullname.startswith('tensorflow'):
            raise ImportError(f"TensorFlow is blocked: {fullname}")
        return None

sys.meta_path.insert(0, BlockTensorFlow())

# Set environment variables
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
os.environ['OMP_NUM_THREADS'] = '4'

import numpy as np
sys.path.append('src')

print("Importing stable_baselines3 (PyTorch only)...")
from stable_baselines3 import PPO

print("Importing FirewallEnv...")
from rl_agent.environment import FirewallEnv

from datetime import datetime

print("\n" + "="*70)
print("FIREWALL RL TRAINING - 500,000 TIMESTEPS")
print("="*70)

# Load data
print("\n[1/5] Loading training data...")
X_train = np.load("data/processed/X_train.npy")
y_train = np.load("data/processed/y_train_binary.npy")
print(f"      ✓ Training: {X_train.shape}, {y_train.shape}")
print(f"      ✓ Benign: {(y_train==0).sum():,}, Attack: {(y_train==1).sum():,}")

# Create environment
print("\n[2/5] Creating Firewall environment...")
env = FirewallEnv(X_train, y_train, shuffle=True)
print(f"      ✓ Observation space: {env.observation_space}")
print(f"      ✓ Action space: {env.action_space} (ALLOW, BLOCK, RATE_LIMIT, FLAG)")

# Create model
print("\n[3/5] Creating PPO model...")
model = PPO(
    policy="MlpPolicy",
    env=env,
    learning_rate=3e-4,
    n_steps=2048,
    batch_size=64,
    n_epochs=10,
    gamma=0.99,
    gae_lambda=0.95,
    clip_range=0.2,
    verbose=1,
    device="cpu"
)
n_params = sum(p.numel() for p in model.policy.parameters())
print(f"      ✓ Model created with {n_params:,} parameters")

# Create directories
print("\n[4/5] Setting up directories...")
os.makedirs("models", exist_ok=True)
os.makedirs("logs", exist_ok=True)
print("      ✓ Directories ready")

# Train
print("\n[5/5] Starting training...")
print("="*70)
print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("Total timesteps: 500,000")
print("Estimated time: 30-60 minutes on CPU")
print("Press Ctrl+C to stop early (model will be saved)")
print("="*70)
print()

start_time = datetime.now()

try:
    model.learn(
        total_timesteps=500_000,
        progress_bar=True,
        log_interval=10
    )
    
    # Save model
    model_path = "models/firewall_model_final"
    model.save(model_path)
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds() / 60
    
    print("\n" + "="*70)
    print("✓ TRAINING COMPLETE!")
    print("="*70)
    print(f"End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Duration: {duration:.1f} minutes")
    print(f"Model saved: {model_path}.zip")
    
    # Get final stats
    stats = env.get_episode_stats()
    print(f"\nFinal Episode Stats:")
    print(f"  Accuracy:  {stats['accuracy']:.4f}")
    print(f"  Precision: {stats['precision']:.4f}")
    print(f"  Recall:    {stats['recall']:.4f}")
    print(f"  F1 Score:  {stats['f1_score']:.4f}")
    print(f"  FPR:       {stats['fpr']:.4f}")
    
except KeyboardInterrupt:
    model_path = "models/firewall_model_interrupted"
    model.save(model_path)
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds() / 60
    
    print("\n" + "="*70)
    print("⚠ TRAINING INTERRUPTED")
    print("="*70)
    print(f"Duration: {duration:.1f} minutes")
    print(f"Model saved: {model_path}.zip")

except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
    
    # Try to save model anyway
    try:
        model.save("models/firewall_model_error")
        print("Model saved to: models/firewall_model_error.zip")
    except:
        print("Could not save model")

print("\n" + "="*70)
print("NEXT STEPS")
print("="*70)
print("1. Evaluate the model:")
print("     python src/rl_agent/evaluate.py")
print("2. Test on new data:")
print("     python test_model.py")
print("="*70)
