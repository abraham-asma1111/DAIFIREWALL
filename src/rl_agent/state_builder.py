"""
State Builder for 129-Dimensional RL Agent State
Combines flow features, anomaly scores, behavioral history, time context, threat intel, network state
"""

import numpy as np
from datetime import datetime
from collections import deque
from typing import Optional, Dict
import pickle
import os


class StateBuilder:
    """
    Builds 129-dimensional state vector for RL agent
    
    State Composition:
    - Current flow features:     20 dims
    - Anomaly scores:             4 dims
    - Behavioral history:        64 dims (LSTM encoding)
    - Time context:               6 dims
    - Threat intel:               5 dims
    - Network state:             10 dims
    - Novelty score:             20 dims (FAISS distances)
    ─────────────────────────────────
    Total:                      129 dims
    """
    
    def __init__(self, 
                 anomaly_detector=None,
                 novelty_scorer=None,
                 history_size: int = 20):
        """
        Initialize state builder
        
        Args:
            anomaly_detector: Behavioral baseline model
            novelty_scorer: Novelty scorer model
            history_size: Number of past flows to track
        """
        self.anomaly_detector = anomaly_detector
        self.novelty_scorer = novelty_scorer
        self.history_size = history_size
        
        # Behavioral history buffer (per IP)
        self.flow_history: Dict[str, deque] = {}
        
        # Network state tracking
        self.global_stats = {
            'total_flows': 0,
            'blocked_count': 0,
            'allowed_count': 0,
            'attack_count': 0,
            'avg_flow_rate': 0.0,
            'peak_flow_rate': 0.0,
            'unique_ips': set(),
            'suspicious_ips': set(),
            'current_threat_level': 0.0,
            'ddos_indicator': 0.0
        }
        
        # Threat intelligence database (mock - replace with real feed)
        self.threat_intel_db = self._load_threat_intel()
    
    def _load_threat_intel(self) -> Dict:
        """Load threat intelligence feeds"""
        # Mock implementation - replace with real feeds (AbuseIPDB, AlienVault, etc.)
        return {
            'known_bad_ips': set(),
            'known_good_ips': set(),
            'country_risk_scores': {
                'CN': 0.7, 'RU': 0.8, 'KP': 0.9,  # High risk
                'US': 0.2, 'GB': 0.2, 'DE': 0.2,  # Low risk
                'ET': 0.3,  # Ethiopia - medium-low
            }
        }
    
    def build_state(self, 
                   flow_features: np.ndarray,
                   src_ip: Optional[str] = None,
                   dst_ip: Optional[str] = None,
                   timestamp: Optional[datetime] = None) -> np.ndarray:
        """
        Build complete 129-dimensional state vector
        
        Args:
            flow_features: 20 network flow features
            src_ip: Source IP address
            dst_ip: Destination IP address
            timestamp: Flow timestamp
            
        Returns:
            129-dimensional state vector
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        if src_ip is None:
            src_ip = "unknown"
        
        # Ensure flow_features is 1D array of 20 values
        if flow_features.ndim > 1:
            flow_features = flow_features.flatten()
        flow_features = flow_features[:20]
        
        # 1. Current flow features (20 dims)
        current_features = flow_features
        
        # 2. Anomaly scores (4 dims)
        anomaly_scores = self._get_anomaly_scores(flow_features.reshape(1, -1))
        
        # 3. Behavioral history (64 dims)
        history_encoding = self._get_history_encoding(src_ip, flow_features)
        
        # 4. Time context (6 dims)
        time_context = self._get_time_context(timestamp)
        
        # 5. Threat intelligence (5 dims)
        threat_intel = self._get_threat_intel(src_ip, dst_ip)
        
        # 6. Network state (10 dims)
        network_state = self._get_network_state()
        
        # 7. Novelty score (20 dims - k-NN distances)
        novelty_features = self._get_novelty_features(flow_features.reshape(1, -1))
        
        # Combine all components
        state = np.concatenate([
            current_features,      # 20
            anomaly_scores,        # 4
            history_encoding,      # 64
            time_context,          # 6
            threat_intel,          # 5
            network_state,         # 10
            novelty_features       # 20
        ])
        
        # Update history
        self._update_history(src_ip, flow_features)
        
        return state.astype(np.float32)
    
    def _get_anomaly_scores(self, X: np.ndarray) -> np.ndarray:
        """
        Get anomaly scores from behavioral baseline
        
        Returns 4 values:
        - Reconstruction error (autoencoder)
        - Isolation forest score
        - Statistical z-score
        - Combined anomaly score
        """
        if self.anomaly_detector is None:
            return np.zeros(4, dtype=np.float32)
        
        try:
            # Reconstruction error
            recon_error = self.anomaly_detector.get_anomaly_score(X)[0]
            
            # Normalize to 0-1
            recon_score = min(recon_error / (self.anomaly_detector.threshold * 2), 1.0)
            
            # Other scores (placeholder - extend when isolation forest added)
            iso_forest_score = recon_score * 0.9  # Correlated
            z_score = recon_score * 1.1  # Slightly different
            combined_score = (recon_score + iso_forest_score + z_score) / 3.0
            
            return np.array([recon_score, iso_forest_score, z_score, combined_score], 
                          dtype=np.float32)
        except:
            return np.zeros(4, dtype=np.float32)
    
    def _get_history_encoding(self, src_ip: str, current_features: np.ndarray) -> np.ndarray:
        """
        Get LSTM encoding of behavioral history
        
        Returns 64-dim encoding of last 20 flows from this IP
        For MVP: simple statistical encoding (mean, std, min, max of features)
        Full version: LSTM encoder
        """
        if src_ip not in self.flow_history:
            # No history - return zeros
            return np.zeros(64, dtype=np.float32)
        
        history = np.array(list(self.flow_history[src_ip]))
        
        # Statistical encoding (simplified)
        # For each of 20 features: mean, std, min, max = 80 values
        # Compress to 64 using PCA or selection
        
        if len(history) < 2:
            return np.zeros(64, dtype=np.float32)
        
        # Calculate statistics
        feature_means = np.mean(history, axis=0)[:16]  # First 16 features
        feature_stds = np.std(history, axis=0)[:16]
        feature_mins = np.min(history, axis=0)[:16]
        feature_maxs = np.max(history, axis=0)[:16]
        
        encoding = np.concatenate([feature_means, feature_stds, feature_mins, feature_maxs])
        
        return encoding.astype(np.float32)[:64]
    
    def _get_time_context(self, timestamp: datetime) -> np.ndarray:
        """
        Get time context features
        
        Returns 6 values:
        - Hour of day (0-23 normalized to 0-1)
        - Day of week (0-6 normalized to 0-1)
        - Is night (18:00-06:00)
        - Is weekend
        - Is business hours (08:00-17:00)
        - Time since last flow (normalized)
        """
        hour = timestamp.hour / 23.0
        day_of_week = timestamp.weekday() / 6.0
        is_night = 1.0 if timestamp.hour >= 18 or timestamp.hour <= 6 else 0.0
        is_weekend = 1.0 if timestamp.weekday() >= 5 else 0.0
        is_business_hours = 1.0 if 8 <= timestamp.hour <= 17 else 0.0
        
        # Time since last flow (placeholder - needs tracking)
        time_since_last = 0.5
        
        return np.array([hour, day_of_week, is_night, is_weekend, 
                        is_business_hours, time_since_last], dtype=np.float32)
    
    def _get_threat_intel(self, src_ip: str, dst_ip: Optional[str]) -> np.ndarray:
        """
        Get threat intelligence scores
        
        Returns 5 values:
        - IP reputation score (0-1, higher = more suspicious)
        - Country risk score (0-1)
        - Is in blocklist
        - Is in allowlist
        - Recent activity score
        """
        # IP reputation (mock - integrate with real feeds)
        is_known_bad = 1.0 if src_ip in self.threat_intel_db['known_bad_ips'] else 0.0
        is_known_good = 1.0 if src_ip in self.threat_intel_db['known_good_ips'] else 0.0
        
        # Country risk (extract from IP - simplified)
        country_risk = 0.3  # Default medium risk
        
        # Recent activity
        recent_activity = min(self.global_stats['total_flows'] / 10000.0, 1.0)
        
        # IP frequency score
        ip_frequency = 0.5  # Placeholder
        
        return np.array([is_known_bad, country_risk, is_known_good, 
                        recent_activity, ip_frequency], dtype=np.float32)
    
    def _get_network_state(self) -> np.ndarray:
        """
        Get global network health metrics
        
        Returns 10 values:
        - Total flow rate (normalized)
        - Block rate (blocks / total)
        - Attack rate (attacks / total)
        - Unique IP count (normalized)
        - Suspicious IP ratio
        - Current threat level (0-1)
        - DDoS indicator (0-1)
        - Port scan indicator
        - Brute force indicator
        - Overall health score
        """
        total = max(self.global_stats['total_flows'], 1)
        
        flow_rate = min(self.global_stats['avg_flow_rate'] / 1000.0, 1.0)
        block_rate = self.global_stats['blocked_count'] / total
        attack_rate = self.global_stats['attack_count'] / total
        unique_ip_count = min(len(self.global_stats['unique_ips']) / 1000.0, 1.0)
        suspicious_ratio = len(self.global_stats['suspicious_ips']) / max(len(self.global_stats['unique_ips']), 1)
        threat_level = self.global_stats['current_threat_level']
        ddos_indicator = self.global_stats['ddos_indicator']
        
        # Additional indicators (placeholder)
        port_scan_indicator = 0.0
        brute_force_indicator = 0.0
        health_score = 1.0 - (attack_rate + threat_level) / 2.0
        
        return np.array([flow_rate, block_rate, attack_rate, unique_ip_count,
                        suspicious_ratio, threat_level, ddos_indicator,
                        port_scan_indicator, brute_force_indicator, health_score],
                       dtype=np.float32)
    
    def _get_novelty_features(self, X: np.ndarray) -> np.ndarray:
        """
        Get novelty scores from FAISS
        
        Returns 20 values:
        - Distances to k=20 nearest neighbors
        """
        if self.novelty_scorer is None:
            return np.ones(20, dtype=np.float32) * 0.5
        
        try:
            # Get k=20 nearest neighbors
            k = 20
            X_float32 = X.astype('float32')
            distances, _ = self.novelty_scorer.index.search(X_float32, k)
            
            # Normalize distances
            normalized_distances = distances[0] / (self.novelty_scorer.threshold * 2)
            normalized_distances = np.clip(normalized_distances, 0, 1)
            
            return normalized_distances.astype(np.float32)
        except:
            return np.ones(20, dtype=np.float32) * 0.5
    
    def _update_history(self, src_ip: str, features: np.ndarray):
        """Update flow history for IP"""
        if src_ip not in self.flow_history:
            self.flow_history[src_ip] = deque(maxlen=self.history_size)
        
        self.flow_history[src_ip].append(features)
    
    def update_network_stats(self, decision: str, is_attack: bool, src_ip: str):
        """Update global network statistics"""
        self.global_stats['total_flows'] += 1
        
        if decision == "BLOCK":
            self.global_stats['blocked_count'] += 1
        elif decision == "ALLOW":
            self.global_stats['allowed_count'] += 1
        
        if is_attack:
            self.global_stats['attack_count'] += 1
            self.global_stats['suspicious_ips'].add(src_ip)
        
        self.global_stats['unique_ips'].add(src_ip)
        
        # Update threat level
        recent_attack_rate = self.global_stats['attack_count'] / max(self.global_stats['total_flows'], 1)
        self.global_stats['current_threat_level'] = min(recent_attack_rate * 2.0, 1.0)
        
        # DDoS detection (simple heuristic)
        unique_ip_rate = len(self.global_stats['unique_ips']) / max(self.global_stats['total_flows'], 1)
        if unique_ip_rate > 0.7 and recent_attack_rate > 0.3:
            self.global_stats['ddos_indicator'] = 1.0
        else:
            self.global_stats['ddos_indicator'] *= 0.95  # Decay
    
    def save(self, path: str = "models/state_builder.pkl"):
        """Save state builder configuration"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as f:
            pickle.dump({
                'flow_history': dict(self.flow_history),
                'global_stats': self.global_stats,
                'threat_intel_db': self.threat_intel_db
            }, f)
    
    def load(self, path: str = "models/state_builder.pkl"):
        """Load state builder configuration"""
        with open(path, 'rb') as f:
            data = pickle.load(f)
            self.flow_history = {k: deque(v, maxlen=self.history_size) 
                               for k, v in data['flow_history'].items()}
            self.global_stats = data['global_stats']
            self.threat_intel_db = data['threat_intel_db']
