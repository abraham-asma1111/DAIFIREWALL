"""
Novelty Scorer using FAISS (Facebook AI Similarity Search)
Detects truly novel traffic patterns never seen before
Key component for zero-day attack detection

"""

import numpy as np
import os
import pickle
import faiss


class NoveltyScorer:
    """
    Uses FAISS to build an index of known traffic patterns
    Measures how "novel" new traffic is by finding nearest neighbors
    High novelty score = potential zero-day attack
    """
    
    def __init__(self, dimension=20):
        """
        Initialize novelty scorer
        
        Args:
            dimension: Feature dimension (20 for our dataset)
        """
        self.dimension = dimension
        self.index = None
        self.threshold = None
        self.trained_samples = 0
        
    def build_index(self, X_train):
        """
        Build FAISS index from training data
        
        Args:
            X_train: Training features (numpy array, float32)
        """
        print("\n" + "="*70)
        print("BUILDING NOVELTY INDEX")
        print("="*70)
        
        # Convert to float32 (required by FAISS)
        X_train = X_train.astype('float32')
        n_samples = len(X_train)
        
        print(f"\nIndexing {n_samples:,} samples...")
        
        # Create FAISS index (L2 distance)
        self.index = faiss.IndexFlatL2(self.dimension)
        
        # Add vectors to index
        self.index.add(X_train)
        self.trained_samples = n_samples
        
        print(f"✓ Index built with {self.index.ntotal:,} vectors")
        
        # Calculate distances to set threshold
        print("\nCalculating novelty threshold...")
        
        # Sample 10k random points to calculate typical distances
        sample_size = min(10000, n_samples)
        sample_idx = np.random.choice(n_samples, sample_size, replace=False)
        X_sample = X_train[sample_idx]
        
        # Find k=5 nearest neighbors for each sample
        k = 5
        distances, _ = self.index.search(X_sample, k + 1)  # k+1 because first is itself
        
        # Use distance to 5th neighbor (excluding self at k=0)
        avg_distances = np.mean(distances[:, 1:k+1], axis=1)
        
        # Set threshold at 95th percentile
        self.threshold = np.percentile(avg_distances, 95)
        
        print(f"✓ Novelty threshold set: {self.threshold:.6f}")
        print(f"    (95th percentile of average k-NN distance)")
        
    def get_novelty_score(self, X, k=5):
        """
        Calculate novelty score for samples
        
        Args:
            X: Network flow features (numpy array)
            k: Number of nearest neighbors to consider
        
        Returns:
            Novelty scores (higher = more novel/suspicious)
        """
        if self.index is None:
            raise ValueError("Index not built. Call build_index() first.")
        
        X = X.astype('float32')
        
        # Search for k nearest neighbors
        distances, indices = self.index.search(X, k)
        
        # Novelty score = average distance to k nearest neighbors
        novelty_scores = np.mean(distances, axis=1)
        
        return novelty_scores
    
    def is_novel(self, X, k=5):
        """
        Classify samples as known (0) or novel (1)
        
        Args:
            X: Network flow features
            k: Number of nearest neighbors
        
        Returns:
            Binary labels (0=known, 1=novel)
        """
        scores = self.get_novelty_score(X, k=k)
        return (scores > self.threshold).astype(int)
    
    def get_novelty_level(self, X, k=5):
        """
        Get novelty level: LOW, MEDIUM, HIGH, CRITICAL
        
        Args:
            X: Network flow features
            k: Number of nearest neighbors
        
        Returns:
            Array of novelty levels
        """
        scores = self.get_novelty_score(X, k=k)
        
        levels = np.empty(len(scores), dtype=object)
        
        # Define thresholds
        low_threshold = self.threshold * 0.5
        medium_threshold = self.threshold
        high_threshold = self.threshold * 1.5
        
        levels[scores < low_threshold] = "LOW"
        levels[(scores >= low_threshold) & (scores < medium_threshold)] = "MEDIUM"
        levels[(scores >= medium_threshold) & (scores < high_threshold)] = "HIGH"
        levels[scores >= high_threshold] = "CRITICAL"
        
        return levels
    
    def save(self, path="models/novelty_scorer.pkl"):
        """Save the index and threshold"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, "models/novelty_index.faiss")
        print(f"✓ FAISS index saved: models/novelty_index.faiss")
        
        # Save metadata
        with open(path, 'wb') as f:
            pickle.dump({
                'threshold': self.threshold,
                'dimension': self.dimension,
                'trained_samples': self.trained_samples
            }, f)
        
        print(f"✓ Metadata saved: {path}")
    
    def load(self, path="models/novelty_scorer.pkl"):
        """Load the index and threshold"""
        # Load metadata
        with open(path, 'rb') as f:
            data = pickle.load(f)
            self.threshold = data['threshold']
            self.dimension = data['dimension']
            self.trained_samples = data['trained_samples']
        
        # Load FAISS index
        self.index = faiss.read_index("models/novelty_index.faiss")
        
        print(f"✓ Novelty scorer loaded from {path}")
        print(f"    Index contains {self.index.ntotal:,} vectors")


def train_novelty_scorer():
    """Main training function"""
    print("\n" + "="*70)
    print("NOVELTY SCORER TRAINING")
    print("="*70)
    
    # Load training data
    print("\n[1/4] Loading data...")
    X_train = np.load("data/processed/X_train.npy")
    y_train = np.load("data/processed/y_train_binary.npy")
    
    print(f"   ✓ Training samples: {len(X_train):,}")
    print(f"   ✓ Features: {X_train.shape[1]}")
    
    # Create and build index
    print("\n[2/4] Building FAISS index...")
    scorer = NoveltyScorer(dimension=X_train.shape[1])
    scorer.build_index(X_train)
    
    # Save model
    print("\n[3/4] Saving model...")
    scorer.save()
    
    # Test on attack samples
    print("\n[4/4] Testing on attack samples...")
    print("="*70)
    
    X_test = np.load("data/processed/X_test.npy")
    y_test = np.load("data/processed/y_test_binary.npy")
    
    # Get some benign and attack samples
    X_test_benign = X_test[y_test == 0][:1000]
    X_test_attack = X_test[y_test == 1][:1000]
    
    scores_benign = scorer.get_novelty_score(X_test_benign)
    scores_attack = scorer.get_novelty_score(X_test_attack)
    
    print(f"\nNovelty Scores:")
    print(f"   BENIGN traffic:  mean={scores_benign.mean():.6f}, max={scores_benign.max():.6f}")
    print(f"   ATTACK traffic:  mean={scores_attack.mean():.6f}, max={scores_attack.max():.6f}")
    print(f"   Threshold:       {scorer.threshold:.6f}")
    
    # Detection rate
    novel_attacks = (scores_attack > scorer.threshold).sum()
    print(f"\n   ✓ Detected {novel_attacks}/{len(scores_attack)} novel attacks ({novel_attacks/len(scores_attack)*100:.1f}%)")
    
    # Novelty levels
    levels_attack = scorer.get_novelty_level(X_test_attack)
    print(f"\n   Novelty Distribution (Attacks):")
    for level in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
        count = (levels_attack == level).sum()
        print(f"      {level:8s}: {count:4d} ({count/len(levels_attack)*100:.1f}%)")
    
    print("\n" + "="*70)
    print("✅ NOVELTY SCORER COMPLETE")
    print("="*70)
    print("\nCapabilities:")
    print("  - Detects truly novel traffic patterns")
    print("  - Classifies novelty: LOW/MEDIUM/HIGH/CRITICAL")
    print("  - Complements RL agent and anomaly detector")
    print()


if __name__ == "__main__":
    train_novelty_scorer()
