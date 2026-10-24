"""
Integrated Detection System
Combines RL Agent + Anomaly Detection + Novelty Scoring
for comprehensive threat detection including zero-day attacks

"""

import numpy as np
import torch
from stable_baselines3 import PPO


class IntegratedDetector:
    """
    Three-layer defense system:
    1. RL Agent - Learned attack patterns
    2. Anomaly Detector - Behavioral deviations  
    3. Novelty Scorer - Truly novel patterns
    
    Decision logic:
    - If RL says BLOCK → BLOCK
    - If Anomaly + Novelty both HIGH → REDIRECT TO HONEYPOT
    - If Anomaly OR Novelty HIGH → FLAG_MONITOR
    - Otherwise → ALLOW
    """
    
    def __init__(self, rl_model_path, anomaly_detector=None, novelty_scorer=None):
        """
        Initialize integrated detector
        
        Args:
            rl_model_path: Path to trained PPO model
            anomaly_detector: BehavioralBaseline instance (optional)
            novelty_scorer: NoveltyScorer instance (optional)
        """
        # Load RL agent
        print("Loading RL agent...")
        self.rl_agent = PPO.load(rl_model_path)
        print("✓ RL agent loaded")
        
        # Store other detectors
        self.anomaly_detector = anomaly_detector
        self.novelty_scorer = novelty_scorer
        
        # Detection modes
        self.use_anomaly = anomaly_detector is not None
        self.use_novelty = novelty_scorer is not None
        
        print(f"✓ Anomaly detection: {'ENABLED' if self.use_anomaly else 'DISABLED'}")
        print(f"✓ Novelty scoring: {'ENABLED' if self.use_novelty else 'DISABLED'}")
        
    def detect(self, X, return_details=False):
        """
        Detect threats using integrated system
        
        Args:
            X: Network flow features (numpy array)
            return_details: If True, return detailed scores
        
        Returns:
            decisions: Array of decisions (ALLOW/BLOCK/FLAG/HONEYPOT)
            details: Dict with scores from each detector (if return_details=True)
        """
        n_samples = len(X)
        
        # 1. RL Agent decisions
        rl_actions = np.array([self.rl_agent.predict(x, deterministic=True)[0] for x in X])
        
        # Initialize decisions with RL actions
        decisions = np.array(['UNKNOWN'] * n_samples, dtype=object)
        decisions[rl_actions == 0] = 'ALLOW'
        decisions[rl_actions == 1] = 'BLOCK'
        decisions[rl_actions == 2] = 'RATE_LIMIT'
        decisions[rl_actions == 3] = 'FLAG_MONITOR'
        
        details = {
            'rl_actions': rl_actions,
            'anomaly_scores': None,
            'novelty_scores': None,
            'is_anomaly': None,
            'is_novel': None
        }
        
        # 2. Anomaly Detection (if enabled)
        if self.use_anomaly:
            anomaly_scores = self.anomaly_detector.get_anomaly_score(X)
            is_anomaly = self.anomaly_detector.is_anomaly(X)
            details['anomaly_scores'] = anomaly_scores
            details['is_anomaly'] = is_anomaly
        
        # 3. Novelty Scoring (if enabled)
        if self.use_novelty:
            novelty_scores = self.novelty_scorer.get_novelty_score(X)
            is_novel = self.novelty_scorer.is_novel(X)
            details['novelty_scores'] = novelty_scores
            details['is_novel'] = is_novel
        
        # 4. Integrated Decision Logic
        for i in range(n_samples):
            # If RL says BLOCK, always block
            if decisions[i] == 'BLOCK':
                continue
            
            # Check anomaly + novelty
            anomalous = details['is_anomaly'][i] if self.use_anomaly else False
            novel = details['is_novel'][i] if self.use_novelty else False
            
            # Both high → Redirect to honeypot (zero-day suspected!)
            if anomalous and novel:
                decisions[i] = 'HONEYPOT'
            
            # Either high → Flag for monitoring
            elif anomalous or novel:
                if decisions[i] == 'ALLOW':  # Override ALLOW
                    decisions[i] = 'FLAG_MONITOR'
        
        if return_details:
            return decisions, details
        return decisions
    
    def get_threat_level(self, X):
        """
        Calculate overall threat level: LOW, MEDIUM, HIGH, CRITICAL
        
        Args:
            X: Network flow features
        
        Returns:
            Array of threat levels
        """
        decisions, details = self.detect(X, return_details=True)
        
        threat_levels = np.array(['LOW'] * len(X), dtype=object)
        
        for i in range(len(X)):
            if decisions[i] == 'BLOCK':
                threat_levels[i] = 'HIGH'
            elif decisions[i] == 'HONEYPOT':
                threat_levels[i] = 'CRITICAL'  # Zero-day suspected!
            elif decisions[i] == 'FLAG_MONITOR':
                threat_levels[i] = 'MEDIUM'
            elif decisions[i] == 'RATE_LIMIT':
                threat_levels[i] = 'MEDIUM'
            else:  # ALLOW
                threat_levels[i] = 'LOW'
        
        return threat_levels
    
    def explain_decision(self, X_sample):
        """
        Explain why a decision was made for a single sample
        
        Args:
            X_sample: Single network flow (1D array or 2D with shape (1, 20))
        
        Returns:
            Explanation dict with scores and reasoning
        """
        if X_sample.ndim == 1:
            X_sample = X_sample.reshape(1, -1)
        
        decision, details = self.detect(X_sample, return_details=True)
        
        explanation = {
            'decision': decision[0],
            'rl_action': int(details['rl_actions'][0]),
            'rl_action_name': ['ALLOW', 'BLOCK', 'RATE_LIMIT', 'FLAG_MONITOR'][details['rl_actions'][0]],
            'reasoning': []
        }
        
        # RL reasoning
        if details['rl_actions'][0] == 1:
            explanation['reasoning'].append("RL agent classified as ATTACK")
        
        # Anomaly reasoning
        if self.use_anomaly and details['is_anomaly'][0]:
            score = details['anomaly_scores'][0]
            threshold = self.anomaly_detector.threshold
            explanation['anomaly_score'] = float(score)
            explanation['anomaly_threshold'] = float(threshold)
            explanation['reasoning'].append(f"Anomalous behavior detected (score: {score:.4f} > {threshold:.4f})")
        
        # Novelty reasoning
        if self.use_novelty and details['is_novel'][0]:
            score = details['novelty_scores'][0]
            threshold = self.novelty_scorer.threshold
            explanation['novelty_score'] = float(score)
            explanation['novelty_threshold'] = float(threshold)
            explanation['reasoning'].append(f"Novel pattern detected (score: {score:.4f} > {threshold:.4f})")
        
        # Zero-day reasoning
        if decision[0] == 'HONEYPOT':
            explanation['reasoning'].append("ZERO-DAY SUSPECTED! Both anomalous AND novel → Redirect to honeypot")
        
        return explanation


def test_integrated_detector():
    """Test the integrated detection system"""
    print("\n" + "="*70)
    print("INTEGRATED DETECTOR TEST")
    print("="*70)
    
    # Check if models exist
    import os
    if not os.path.exists("models/firewall_final.zip") and not os.path.exists("models/firewall_all_data.zip"):
        print("\n❌ No trained RL model found!")
        print("Run training first: python TRAIN_ALL_DATA.py")
        return
    
    # Load RL model
    rl_path = "models/firewall_all_data.zip" if os.path.exists("models/firewall_all_data.zip") else "models/firewall_final.zip"
    
    print(f"\nLoading models...")
    print(f"   RL model: {rl_path}")
    
    # Create integrated detector (without anomaly/novelty for now)
    detector = IntegratedDetector(rl_path)
    
    # Load test data
    print("\nLoading test data...")
    X_test = np.load("data/processed/X_test.npy")
    y_test = np.load("data/processed/y_test_binary.npy")
    
    # Test on sample
    print("\nTesting on 100 samples...")
    X_sample = X_test[:100]
    y_sample = y_test[:100]
    
    decisions = detector.detect(X_sample)
    threat_levels = detector.get_threat_level(X_sample)
    
    # Show results
    print("\nDecision Distribution:")
    for decision in ['ALLOW', 'BLOCK', 'RATE_LIMIT', 'FLAG_MONITOR', 'HONEYPOT']:
        count = (decisions == decision).sum()
        print(f"   {decision:13s}: {count:3d}")
    
    print("\nThreat Level Distribution:")
    for level in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']:
        count = (threat_levels == level).sum()
        print(f"   {level:8s}: {count:3d}")
    
    # Example explanation
    print("\nExample Explanation (First Attack Sample):")
    print("="*70)
    attack_idx = np.where(y_sample == 1)[0]
    if len(attack_idx) > 0:
        explanation = detector.explain_decision(X_sample[attack_idx[0]])
        print(f"Decision: {explanation['decision']}")
        print(f"RL Action: {explanation['rl_action_name']}")
        print("\nReasoning:")
        for reason in explanation['reasoning']:
            print(f"   - {reason}")
    
    print("\n" + "="*70)
    print("✅ TEST COMPLETE")
    print("="*70)


if __name__ == "__main__":
    test_integrated_detector()
