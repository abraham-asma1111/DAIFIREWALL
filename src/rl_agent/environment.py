"""
Custom Gymnasium Environment for Network Firewall RL Agent
The agent observes network flow features and decides: ALLOW, BLOCK, RATE_LIMIT, or FLAG_MONITOR

"""

import gymnasium as gym
from gymnasium import spaces
import numpy as np


class FirewallEnv(gym.Env):
    """
    Custom Gymnasium Environment for Firewall Decision Making
    
    State Space: 20 network flow features (normalized 0-1)
    Action Space: 4 discrete actions
        0 = ALLOW
        1 = BLOCK
        2 = RATE_LIMIT
        3 = FLAG_MONITOR
    
    Reward Structure:
        +10  : Block an attack (correct block)
        +1   : Allow benign traffic (correct allow)
        -8   : Block benign traffic (false positive)
        -15  : Allow an attack (false negative - security breach!)
        -5   : Rate limit benign traffic (unnecessary throttling)
        +5   : Rate limit attack (good response)
        +2   : Flag attack for monitoring (conservative response)
        -1   : Flag benign for monitoring (wasted resources)
    """
    
    metadata = {"render_modes": ["human"]}
    
    def __init__(self, X_data, y_data, shuffle=True):
        """
        Initialize the environment
        
        Args:
            X_data: numpy array of shape (n_samples, 20) - network flow features
            y_data: numpy array of shape (n_samples,) - binary labels (0=benign, 1=attack)
            shuffle: whether to shuffle the data at each reset
        """
        super().__init__()
        
        # Store data
        self.X_data = X_data
        self.y_data = y_data
        self.n_samples = len(X_data)
        self.shuffle = shuffle
        
        # Observation space: 20 features, each in [0, 1]
        self.observation_space = spaces.Box(
            low=0.0, 
            high=1.0, 
            shape=(20,), 
            dtype=np.float32
        )
        
        # Action space: 4 discrete actions
        self.action_space = spaces.Discrete(4)
        
        # Episode tracking
        self.current_step = 0
        self.max_steps = self.n_samples
        self.sample_indices = np.arange(self.n_samples)
        
        # Statistics tracking
        self.episode_stats = {
            'correct_blocks': 0,
            'correct_allows': 0,
            'false_positives': 0,
            'false_negatives': 0,
            'rate_limits': 0,
            'flags': 0,
            'total_reward': 0
        }
        
    def reset(self, seed=None, options=None):
        """Reset the environment to initial state"""
        super().reset(seed=seed)
        
        # Shuffle data if requested
        if self.shuffle:
            np.random.shuffle(self.sample_indices)
        
        # Reset episode tracking
        self.current_step = 0
        
        # Reset statistics
        self.episode_stats = {
            'correct_blocks': 0,
            'correct_allows': 0,
            'false_positives': 0,
            'false_negatives': 0,
            'rate_limits': 0,
            'flags': 0,
            'total_reward': 0
        }
        
        # Get first observation
        idx = self.sample_indices[self.current_step]
        observation = self.X_data[idx].astype(np.float32)
        
        info = {}
        
        return observation, info
    
    def step(self, action):
        """
        Execute one step in the environment
        
        Args:
            action: int in [0, 1, 2, 3]
                0 = ALLOW
                1 = BLOCK
                2 = RATE_LIMIT
                3 = FLAG_MONITOR
        
        Returns:
            observation: next state (20 features)
            reward: float
            terminated: bool (episode ended)
            truncated: bool (episode truncated)
            info: dict with additional information
        """
        
        # Get current sample
        idx = self.sample_indices[self.current_step]
        true_label = self.y_data[idx]  # 0 = benign, 1 = attack
        
        # Calculate reward based on action and true label
        reward = self._calculate_reward(action, true_label)
        
        # Update statistics
        self._update_stats(action, true_label)
        self.episode_stats['total_reward'] += reward
        
        # Move to next step
        self.current_step += 1
        
        # Check if episode is done
        terminated = self.current_step >= self.max_steps
        truncated = False
        
        # Get next observation (if not terminated)
        if not terminated:
            idx = self.sample_indices[self.current_step]
            observation = self.X_data[idx].astype(np.float32)
        else:
            observation = np.zeros(20, dtype=np.float32)
        
        # Info dictionary
        info = {
            'true_label': int(true_label),
            'action_taken': int(action),
            'is_correct': self._is_correct_decision(action, true_label)
        }
        
        return observation, reward, terminated, truncated, info
    
    def _calculate_reward(self, action, true_label):
        """
        Calculate reward based on action and true label
        
        Reward Philosophy:
        - Security is CRITICAL: False negatives heavily penalized (-15)
        - Availability matters: False positives penalized but less (-8)
        - Conservative actions (rate_limit, flag) have intermediate rewards
        """
        
        is_attack = (true_label == 1)
        
        if action == 0:  # ALLOW
            if is_attack:
                return -15  # Security breach! Very bad
            else:
                return +1   # Correct, normal operation
        
        elif action == 1:  # BLOCK
            if is_attack:
                return +10  # Excellent! Stopped attack
            else:
                return -8   # False positive, service disruption
        
        elif action == 2:  # RATE_LIMIT
            if is_attack:
                return +5   # Good, slowed down attack
            else:
                return -5   # Unnecessary throttling
        
        elif action == 3:  # FLAG_MONITOR
            if is_attack:
                return +2   # Conservative but acceptable
            else:
                return -1   # Wasted monitoring resources
        
        return 0  # Should never reach here
    
    def _is_correct_decision(self, action, true_label):
        """Check if the action was correct"""
        is_attack = (true_label == 1)
        
        # ALLOW is correct only for benign traffic
        if action == 0:
            return not is_attack
        
        # BLOCK is correct only for attacks
        elif action == 1:
            return is_attack
        
        # RATE_LIMIT and FLAG are partially correct for attacks
        elif action in [2, 3]:
            return is_attack
        
        return False
    
    def _update_stats(self, action, true_label):
        """Update episode statistics"""
        is_attack = (true_label == 1)
        
        if action == 0:  # ALLOW
            if is_attack:
                self.episode_stats['false_negatives'] += 1
            else:
                self.episode_stats['correct_allows'] += 1
        
        elif action == 1:  # BLOCK
            if is_attack:
                self.episode_stats['correct_blocks'] += 1
            else:
                self.episode_stats['false_positives'] += 1
        
        elif action == 2:  # RATE_LIMIT
            self.episode_stats['rate_limits'] += 1
        
        elif action == 3:  # FLAG_MONITOR
            self.episode_stats['flags'] += 1
    
    def get_episode_stats(self):
        """Return episode statistics"""
        total_decisions = self.current_step
        if total_decisions == 0:
            return self.episode_stats
        
        # Calculate metrics
        stats = self.episode_stats.copy()
        
        # Precision: TP / (TP + FP)
        tp = stats['correct_blocks']
        fp = stats['false_positives']
        stats['precision'] = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        
        # Recall: TP / (TP + FN)
        fn = stats['false_negatives']
        stats['recall'] = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        
        # F1 Score
        p = stats['precision']
        r = stats['recall']
        stats['f1_score'] = 2 * (p * r) / (p + r) if (p + r) > 0 else 0.0
        
        # Accuracy
        correct = stats['correct_blocks'] + stats['correct_allows']
        stats['accuracy'] = correct / total_decisions if total_decisions > 0 else 0.0
        
        # False Positive Rate
        tn = stats['correct_allows']
        stats['fpr'] = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        
        return stats
    
    def render(self):
        """Render the environment (print statistics)"""
        stats = self.get_episode_stats()
        print(f"\n--- Episode Statistics (Step {self.current_step}/{self.max_steps}) ---")
        print(f"Correct Blocks:     {stats['correct_blocks']:,}")
        print(f"Correct Allows:     {stats['correct_allows']:,}")
        print(f"False Positives:    {stats['false_positives']:,}")
        print(f"False Negatives:    {stats['false_negatives']:,}")
        print(f"Rate Limits:        {stats['rate_limits']:,}")
        print(f"Flags:              {stats['flags']:,}")
        print(f"Total Reward:       {stats['total_reward']:.2f}")
        print(f"Accuracy:           {stats['accuracy']:.4f}")
        print(f"Precision:          {stats['precision']:.4f}")
        print(f"Recall:             {stats['recall']:.4f}")
        print(f"F1 Score:           {stats['f1_score']:.4f}")
        print(f"False Positive Rate: {stats['fpr']:.4f}")
        print("---\n")


if __name__ == "__main__":
    # Test the environment
    print("Testing FirewallEnv...")
    
    # Load preprocessed data
    X_test = np.load("data/processed/X_test.npy")
    y_test = np.load("data/processed/y_test_binary.npy")
    
    print(f"Loaded test data: {X_test.shape}, {y_test.shape}")
    
    # Create environment with small subset for testing
    test_size = 1000
    env = FirewallEnv(X_test[:test_size], y_test[:test_size], shuffle=True)
    
    print(f"\nEnvironment created:")
    print(f"  Observation space: {env.observation_space}")
    print(f"  Action space: {env.action_space}")
    print(f"  Max steps: {env.max_steps}")
    
    # Test reset
    obs, info = env.reset()
    print(f"\nInitial observation shape: {obs.shape}")
    print(f"Sample observation (first 5 features): {obs[:5]}")
    
    # Test a few random steps
    print("\nTesting random actions:")
    for i in range(5):
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)
        
        action_names = ['ALLOW', 'BLOCK', 'RATE_LIMIT', 'FLAG_MONITOR']
        label_names = ['BENIGN', 'ATTACK']
        
        print(f"  Step {i+1}: Action={action_names[action]:12s} | True Label={label_names[info['true_label']]:6s} | Reward={reward:+6.1f} | Correct={info['is_correct']}")
    
    # Show statistics
    env.render()
    
    print("✓ Environment test complete!")
