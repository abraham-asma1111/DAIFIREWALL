#!/usr/bin/env python3
"""Test each import individually"""

import sys

print("=" * 60, flush=True)
print("TESTING IMPORTS", flush=True)
print("=" * 60, flush=True)

try:
    print("\n1. Testing torch import...", flush=True)
    import torch
    print(f"   ✓ torch {torch.__version__}", flush=True)
except Exception as e:
    print(f"   ✗ ERROR: {e}", flush=True)
    sys.exit(1)

try:
    print("\n2. Testing numpy import...", flush=True)
    import numpy as np
    print(f"   ✓ numpy {np.__version__}", flush=True)
except Exception as e:
    print(f"   ✗ ERROR: {e}", flush=True)
    sys.exit(1)

try:
    print("\n3. Testing gymnasium import...", flush=True)
    import gymnasium
    print(f"   ✓ gymnasium {gymnasium.__version__}", flush=True)
except Exception as e:
    print(f"   ✗ ERROR: {e}", flush=True)
    sys.exit(1)

try:
    print("\n4. Testing stable_baselines3 import...", flush=True)
    from stable_baselines3 import PPO
    print(f"   ✓ stable_baselines3 imported", flush=True)
except Exception as e:
    print(f"   ✗ ERROR: {e}", flush=True)
    sys.exit(1)

try:
    print("\n5. Testing FirewallEnv import...", flush=True)
    sys.path.append('src')
    from rl_agent.environment import FirewallEnv
    print(f"   ✓ FirewallEnv imported", flush=True)
except Exception as e:
    print(f"   ✗ ERROR: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60, flush=True)
print("✓ ALL IMPORTS SUCCESSFUL", flush=True)
print("=" * 60, flush=True)
print("\nYou can now run TRAIN.py", flush=True)
