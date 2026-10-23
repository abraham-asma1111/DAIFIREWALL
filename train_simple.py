"""
Simplified training script without Monitor wrapper
This avoids the memory corruption issue
"""

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'

import numpy as np
import sys
sys.path.append('src')

from stable_baselines3 import PPO
from rl_agent.environment import FirewallEnv
from datetime import datetime

print("="*70)
print("SIMPLIFIED RL TRAINING - 500K TIMESTEPS")
print("="*70)

# Load data
print("\n[1/4] Loading data...")
X_train = np.load("data/processed/X_train.npy")
y_train = np.load("data/processed/y_train_binary.npy")
print(f"      ✓ Training data: {X_train.shape}")

# Create environment (NO Monitor wrapper)
print("\n[2/4] Creating environment...")
env = FirewallEnv(X_train, y_train, shuffle=True)
print("      ✓ Environment created")

# Create model
print("\n[3/4] Creating PPO model...")
model = PPO(
    policy="MlpPolicy",
    env=env,
    learning_rate=3e-4,
    n_steps=2048,
    batch_size=64,
    n_epochs=10,
    gamma=0.99,
    verbose=1,
    device="cpu"
)
print("      ✓ Model created")

# Create directories
os.makedirs("models", exist_ok=True)
os.makedirs("logs", exist_ok=True)

# Train
print("\n[4/4] Training for 500,000 timesteps...")
print(f"      Started: {datetime.now().strftime('%H:%M:%S')}")
print("      This will take 30-60 minutes on CPU...")
print("      You can stop with Ctrl+C and the model will be saved\n")

try:
    model.learn(
        total_timesteps=500_000,
        progress_bar=True,
        log_interval=10
    )
    
    # Save final model
    model.save("models/firewall_model_final")
    print(f"\n✓ Training complete at {datetime.now().strftime('%H:%M:%S')}")
    print("✓ Model saved: models/firewall_model_final.zip")
    
except KeyboardInterrupt:
    print("\n\n⚠ Training interrupted!")
    model.save("models/firewall_model_interrupted")
    print("✓ Model saved: models/firewall_model_interrupted.zip")

print("\n" + "="*70)
print("Next step: Evaluate the model")
print("  python src/rl_agent/evaluate.py")
print("="*70)
