"""
Minimal test to isolate the issue
"""
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

print("Step 1: Import numpy...")
import numpy as np
print("✓ numpy imported")

print("\nStep 2: Import gymnasium...")
import gymnasium as gym
print("✓ gymnasium imported")

print("\nStep 3: Import stable_baselines3...")
from stable_baselines3 import PPO
print("✓ stable_baselines3 imported")

print("\nStep 4: Create simple environment...")
env = gym.make('CartPole-v1')
print("✓ CartPole environment created")

print("\nStep 5: Create PPO model...")
try:
    model = PPO('MlpPolicy', env, verbose=0, device='cpu')
    print("✓ PPO model created")
except Exception as e:
    print(f"✗ Error creating model: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\nStep 6: Train for 100 steps...")
try:
    model.learn(total_timesteps=100, progress_bar=False)
    print("✓ Training complete!")
except Exception as e:
    print(f"✗ Error during training: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n✓ ALL TESTS PASSED - stable_baselines3 is working!")
