"""
Behavioral Baseline using Autoencoder
Learns what "normal" (BENIGN) traffic looks like to detect anomalies
This enables zero-day attack detection

"""

import numpy as np
import os
import pickle
from datetime import datetime

# NOTE: Requires TensorFlow - install with: pip install tensorflow==2.21.0
try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers, Model
    from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
    HAS_TENSORFLOW = True
except ImportError:
    HAS_TENSORFLOW = False
    print("⚠️  TensorFlow not installed. Install with: pip install tensorflow==2.21.0")


class BehavioralBaseline:
    """
    Autoencoder-based anomaly detector
    Trained only on BENIGN traffic to learn normal behavior
    High reconstruction error = anomaly = potential zero-day attack
    """
    
    def __init__(self, input_dim=20, encoding_dim=10):
        """
        Initialize autoencoder architecture
        
        Args:
            input_dim: Number of features (20 for our dataset)
            encoding_dim: Size of compressed representation
        """
        self.input_dim = input_dim
        self.encoding_dim = encoding_dim
        self.autoencoder = None
        self.encoder = None
        self.threshold = None
        self.mean = None
        self.std = None
        
    def build_model(self):
        """Build autoencoder architecture"""
        if not HAS_TENSORFLOW:
            raise ImportError("TensorFlow required. Install: pip install tensorflow==2.21.0")
        
        # Encoder
        input_layer = layers.Input(shape=(self.input_dim,))
        encoded = layers.Dense(16, activation='relu')(input_layer)
        encoded = layers.Dense(self.encoding_dim, activation='relu')(encoded)
        
        # Decoder
        decoded = layers.Dense(16, activation='relu')(encoded)
        decoded = layers.Dense(self.input_dim, activation='sigmoid')(decoded)
        
        # Full autoencoder
        self.autoencoder = Model(input_layer, decoded)
        
        # Encoder only (for feature extraction)
        self.encoder = Model(input_layer, encoded)
        
        # Compile
        self.autoencoder.compile(
            optimizer='adam',
            loss='mse',
            metrics=['mae']
        )
        
        print("✓ Autoencoder built:")
        print(f"    Input: {self.input_dim} features")
        print(f"    Encoding: {self.encoding_dim} dimensions")
        print(f"    Output: {self.input_dim} features")
        
        return self.autoencoder
    
    def train(self, X_benign, validation_split=0.2, epochs=50, batch_size=256):
        """
        Train autoencoder on BENIGN traffic only
        
        Args:
            X_benign: Normal traffic samples (numpy array)
            validation_split: Fraction for validation
            epochs: Training epochs
            batch_size: Batch size
        """
        if self.autoencoder is None:
            self.build_model()
        
        print("\n" + "="*70)
        print("TRAINING BEHAVIORAL BASELINE")
        print("="*70)
        print(f"\nTraining on {len(X_benign):,} BENIGN samples")
        print(f"Epochs: {epochs}, Batch size: {batch_size}")
        print()
        
        # Callbacks
        callbacks = [
            EarlyStopping(
                monitor='val_loss',
                patience=5,
                restore_best_weights=True
            ),
            ModelCheckpoint(
                'models/autoencoder_best.h5',
                monitor='val_loss',
                save_best_only=True
            )
        ]
        
        # Train
        history = self.autoencoder.fit(
            X_benign, X_benign,  # Input = Output for autoencoder
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            callbacks=callbacks,
            verbose=1
        )
        
        print("\n✓ Training complete")
        
        # Calculate reconstruction errors on training data
        reconstructions = self.autoencoder.predict(X_benign, verbose=0)
        reconstruction_errors = np.mean(np.square(X_benign - reconstructions), axis=1)
        
        # Set threshold at 95th percentile of normal traffic errors
        self.threshold = np.percentile(reconstruction_errors, 95)
        
        # Calculate statistics for normalization
        self.mean = np.mean(X_benign, axis=0)
        self.std = np.std(X_benign, axis=0)
        
        print(f"\n✓ Anomaly threshold set: {self.threshold:.6f}")
        print(f"    (95th percentile of BENIGN reconstruction error)")
        
        return history
    
    def get_anomaly_score(self, X):
        """
        Calculate anomaly score for samples
        
        Args:
            X: Network flow features (numpy array)
        
        Returns:
            Anomaly scores (higher = more anomalous)
        """
        if self.autoencoder is None:
            raise ValueError("Model not trained. Call train() first.")
        
        # Reconstruct
        reconstructions = self.autoencoder.predict(X, verbose=0)
        
        # Calculate reconstruction error
        reconstruction_errors = np.mean(np.square(X - reconstructions), axis=1)
        
        return reconstruction_errors
    
    def is_anomaly(self, X):
        """
        Classify samples as normal (0) or anomaly (1)
        
        Args:
            X: Network flow features
        
        Returns:
            Binary labels (0=normal, 1=anomaly)
        """
        scores = self.get_anomaly_score(X)
        return (scores > self.threshold).astype(int)
    
    def save(self, path="models/behavioral_baseline.pkl"):
        """Save the model and threshold"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        # Save Keras model separately
        if self.autoencoder is not None:
            self.autoencoder.save("models/autoencoder.h5")
            print(f"✓ Autoencoder saved: models/autoencoder.h5")
        
        # Save threshold and stats
        with open(path, 'wb') as f:
            pickle.dump({
                'threshold': self.threshold,
                'mean': self.mean,
                'std': self.std,
                'input_dim': self.input_dim,
                'encoding_dim': self.encoding_dim
            }, f)
        
        print(f"✓ Threshold and stats saved: {path}")
    
    def load(self, path="models/behavioral_baseline.pkl"):
        """Load the model and threshold"""
        if not HAS_TENSORFLOW:
            raise ImportError("TensorFlow required")
        
        # Load threshold and stats
        with open(path, 'rb') as f:
            data = pickle.load(f)
            self.threshold = data['threshold']
            self.mean = data['mean']
            self.std = data['std']
            self.input_dim = data['input_dim']
            self.encoding_dim = data['encoding_dim']
        
        # Load Keras model
        self.autoencoder = keras.models.load_model("models/autoencoder.h5")
        self.encoder = Model(
            self.autoencoder.input,
            self.autoencoder.layers[2].output  # Encoding layer
        )
        
        print(f"✓ Behavioral baseline loaded from {path}")


def train_behavioral_baseline():
    """Main training function"""
    if not HAS_TENSORFLOW:
        print("\n❌ TensorFlow not installed!")
        print("Install with: pip install tensorflow==2.21.0")
        return
    
    print("\n" + "="*70)
    print("BEHAVIORAL BASELINE TRAINING")
    print("="*70)
    
    # Load training data
    print("\n[1/4] Loading data...")
    X_train = np.load("data/processed/X_train.npy")
    y_train = np.load("data/processed/y_train_binary.npy")
    
    # Extract only BENIGN traffic
    X_benign = X_train[y_train == 0]
    print(f"   ✓ Total samples: {len(X_train):,}")
    print(f"   ✓ BENIGN samples: {len(X_benign):,}")
    
    # Create and train model
    print("\n[2/4] Building autoencoder...")
    baseline = BehavioralBaseline(input_dim=20, encoding_dim=10)
    baseline.build_model()
    
    print("\n[3/4] Training on BENIGN traffic...")
    baseline.train(X_benign, epochs=50, batch_size=256)
    
    # Save model
    print("\n[4/4] Saving model...")
    baseline.save()
    
    # Test on some attack samples
    print("\n" + "="*70)
    print("TESTING ON ATTACK SAMPLES")
    print("="*70)
    
    X_test = np.load("data/processed/X_test.npy")
    y_test = np.load("data/processed/y_test_binary.npy")
    
    X_test_benign = X_test[y_test == 0][:1000]
    X_test_attack = X_test[y_test == 1][:1000]
    
    scores_benign = baseline.get_anomaly_score(X_test_benign)
    scores_attack = baseline.get_anomaly_score(X_test_attack)
    
    print(f"\nAnomaly Scores:")
    print(f"   BENIGN traffic:  mean={scores_benign.mean():.6f}, max={scores_benign.max():.6f}")
    print(f"   ATTACK traffic:  mean={scores_attack.mean():.6f}, max={scores_attack.max():.6f}")
    print(f"   Threshold:       {baseline.threshold:.6f}")
    
    # Detection rate
    detected = (scores_attack > baseline.threshold).sum()
    print(f"\n   ✓ Detected {detected}/{len(scores_attack)} attacks ({detected/len(scores_attack)*100:.1f}%)")
    
    print("\n" + "="*70)
    print("✅ BEHAVIORAL BASELINE COMPLETE")
    print("="*70)
    print("\nModel can now detect:")
    print("  - Known attacks (via RL agent)")
    print("  - Zero-day attacks (via anomaly detection)")
    print()


if __name__ == "__main__":
    train_behavioral_baseline()
