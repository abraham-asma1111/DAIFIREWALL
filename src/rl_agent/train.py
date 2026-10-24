"""
RL Agent Training Script - PPO Algorithm
Trains the firewall agent to detect and block cyberattacks

"""

# CRITICAL: Disable TensorFlow before any imports (prevents conflicts with PyTorch)
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress TensorFlow warnings
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'  # Disable oneDNN custom ops
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'  # Force CPU-only (avoid CUDA conflicts)
os.environ['OMP_NUM_THREADS'] = '4'  # Limit OpenMP threads

import numpy as np
from datetime import datetime
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import CheckpointCallback, EvalCallback
from stable_baselines3.common.monitor import Monitor
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from rl_agent.environment import FirewallEnv


# Configuration
TOTAL_TIMESTEPS = 500_000  # 500k timesteps as per requirements
LEARNING_RATE = 3e-4
N_STEPS = 2048
BATCH_SIZE = 64
N_EPOCHS = 10
GAMMA = 0.99
GAE_LAMBDA = 0.95
CLIP_RANGE = 0.2

# Paths
DATA_DIR = "data/processed"
MODEL_DIR = "models"
LOG_DIR = "logs"
CHECKPOINT_DIR = os.path.join(MODEL_DIR, "checkpoints")
BEST_MODEL_DIR = os.path.join(MODEL_DIR, "best")
TENSORBOARD_LOG = os.path.join(LOG_DIR, "tensorboard")


def load_data():
    """Load preprocessed training and validation data"""
    print("=" * 70)
    print("LOADING PREPROCESSED DATA")
    print("=" * 70)
    
    X_train = np.load(os.path.join(DATA_DIR, "X_train.npy"))
    y_train = np.load(os.path.join(DATA_DIR, "y_train_binary.npy"))
    X_val = np.load(os.path.join(DATA_DIR, "X_val.npy"))
    y_val = np.load(os.path.join(DATA_DIR, "y_val_binary.npy"))
    
    print(f"\n✓ Training data:   {X_train.shape} samples")
    print(f"✓ Validation data: {X_val.shape} samples")
    
    # Show class distribution
    n_benign_train = (y_train == 0).sum()
    n_attack_train = (y_train == 1).sum()
    n_benign_val = (y_val == 0).sum()
    n_attack_val = (y_val == 1).sum()
    
    print(f"\nTraining set:")
    print(f"  - Benign: {n_benign_train:,} ({n_benign_train/len(y_train)*100:.1f}%)")
    print(f"  - Attack: {n_attack_train:,} ({n_attack_train/len(y_train)*100:.1f}%)")
    
    print(f"\nValidation set:")
    print(f"  - Benign: {n_benign_val:,} ({n_benign_val/len(y_val)*100:.1f}%)")
    print(f"  - Attack: {n_attack_val:,} ({n_attack_val/len(y_val)*100:.1f}%)")
    print()
    
    return X_train, y_train, X_val, y_val


def create_environments(X_train, y_train, X_val, y_val):
    """Create training and validation environments"""
    print("=" * 70)
    print("CREATING ENVIRONMENTS")
    print("=" * 70)
    
    # Create environments
    train_env = FirewallEnv(X_train, y_train, shuffle=True)
    val_env = FirewallEnv(X_val, y_val, shuffle=False)
    
    # Wrap with Monitor for logging
    os.makedirs(LOG_DIR, exist_ok=True)
    train_env = Monitor(train_env, os.path.join(LOG_DIR, "train_monitor.csv"))
    val_env = Monitor(val_env, os.path.join(LOG_DIR, "val_monitor.csv"))
    
    print(f"\n✓ Training environment created:")
    print(f"    - Observation space: {train_env.observation_space}")
    print(f"    - Action space: {train_env.action_space}")
    print(f"    - Max steps per episode: {train_env.max_steps:,}")
    
    print(f"\n✓ Validation environment created")
    print()
    
    return train_env, val_env


def create_callbacks(val_env):
    """Create training callbacks for checkpointing and evaluation"""
    print("=" * 70)
    print("SETTING UP CALLBACKS")
    print("=" * 70)
    
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    os.makedirs(BEST_MODEL_DIR, exist_ok=True)
    
    # Checkpoint callback: save model every 50k steps
    checkpoint_callback = CheckpointCallback(
        save_freq=50_000,
        save_path=CHECKPOINT_DIR,
        name_prefix="firewall_model",
        save_replay_buffer=False,
        save_vecnormalize=False,
    )
    
    # Evaluation callback: evaluate and save best model
    eval_callback = EvalCallback(
        val_env,
        best_model_save_path=BEST_MODEL_DIR,
        log_path=LOG_DIR,
        eval_freq=10_000,  # Evaluate every 10k steps
        deterministic=True,
        render=False,
        n_eval_episodes=5,
    )
    
    print("\n✓ Checkpoint callback: Save every 50,000 steps")
    print(f"    → {CHECKPOINT_DIR}/")
    
    print(f"\n✓ Evaluation callback: Evaluate every 10,000 steps")
    print(f"    → Best model saved to: {BEST_MODEL_DIR}/")
    print()
    
    return [checkpoint_callback, eval_callback]


def train_agent(train_env, val_env):
    """Train the PPO agent"""
    print("=" * 70)
    print("TRAINING PPO AGENT")
    print("=" * 70)
    
    print("\nHyperparameters:")
    print(f"  - Algorithm: PPO (Proximal Policy Optimization)")
    print(f"  - Total timesteps: {TOTAL_TIMESTEPS:,}")
    print(f"  - Learning rate: {LEARNING_RATE}")
    print(f"  - Steps per rollout: {N_STEPS:,}")
    print(f"  - Batch size: {BATCH_SIZE}")
    print(f"  - Epochs per update: {N_EPOCHS}")
    print(f"  - Discount factor (gamma): {GAMMA}")
    print(f"  - GAE lambda: {GAE_LAMBDA}")
    print(f"  - Clip range: {CLIP_RANGE}")
    
    # Create tensorboard log directory
    os.makedirs(TENSORBOARD_LOG, exist_ok=True)
    
    print(f"\n✓ TensorBoard logs: {TENSORBOARD_LOG}/")
    print("  To monitor training, run:")
    print(f"    tensorboard --logdir {TENSORBOARD_LOG}")
    
    # Create callbacks
    callbacks = create_callbacks(val_env)
    
    # Create PPO model
    print("\n" + "=" * 70)
    print("INITIALIZING MODEL")
    print("=" * 70)
    
    model = PPO(
        policy="MlpPolicy",
        env=train_env,
        learning_rate=LEARNING_RATE,
        n_steps=N_STEPS,
        batch_size=BATCH_SIZE,
        n_epochs=N_EPOCHS,
        gamma=GAMMA,
        gae_lambda=GAE_LAMBDA,
        clip_range=CLIP_RANGE,
        verbose=1,
        tensorboard_log=TENSORBOARD_LOG,
        device="cpu"  # Use CPU (no GPU detected)
    )
    
    print("\n✓ Model initialized")
    print(f"    Policy network: MLP (Multi-Layer Perceptron)")
    print(f"    Total parameters: ~{sum(p.numel() for p in model.policy.parameters()):,}")
    
    # Start training
    print("\n" + "=" * 70)
    print("STARTING TRAINING")
    print("=" * 70)
    print(f"\nTraining started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("This may take 30-60 minutes on CPU...\n")
    
    try:
        model.learn(
            total_timesteps=TOTAL_TIMESTEPS,
            callback=callbacks,
            progress_bar=True
        )
        
        print("\n" + "=" * 70)
        print("TRAINING COMPLETE!")
        print("=" * 70)
        print(f"\nTraining finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Save final model
        final_model_path = os.path.join(MODEL_DIR, "firewall_model_final")
        model.save(final_model_path)
        print(f"\n✓ Final model saved to: {final_model_path}.zip")
        
        return model
        
    except KeyboardInterrupt:
        print("\n\n⚠ Training interrupted by user!")
        print("Saving model checkpoint...")
        
        interrupted_model_path = os.path.join(MODEL_DIR, "firewall_model_interrupted")
        model.save(interrupted_model_path)
        print(f"✓ Model saved to: {interrupted_model_path}.zip")
        
        return model


def main():
    """Main training pipeline"""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 20 + "RL AGENT TRAINING" + " " * 31 + "║")
    print("║" + " " * 12 + "Dynamic AI Firewall - PPO Algorithm" + " " * 21 + "║")
    print("╚" + "=" * 68 + "╝")
    print()
    
    # Load data
    X_train, y_train, X_val, y_val = load_data()
    
    # Create environments
    train_env, val_env = create_environments(X_train, y_train, X_val, y_val)
    
    # Train agent
    model = train_agent(train_env, val_env)
    
    # Show final message
    print("\n" + "=" * 70)
    print("NEXT STEPS")
    print("=" * 70)
    print("\n1. Evaluate the model:")
    print("     python src/rl_agent/evaluate.py")
    print("\n2. View TensorBoard logs:")
    print(f"     tensorboard --logdir {TENSORBOARD_LOG}")
    print("\n3. Best model location:")
    print(f"     {BEST_MODEL_DIR}/best_model.zip")
    print()


if __name__ == "__main__":
    main()
