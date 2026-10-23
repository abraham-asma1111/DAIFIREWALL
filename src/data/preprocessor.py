"""
CICIDS 2017 Dataset Preprocessor
Loads, cleans, normalizes, and saves network flow data for RL training.

Author: Abraham Asmamaw Mulugeta
Date: October 23, 2026
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
import os
import glob
from pathlib import Path

# Configuration
DATA_DIR = "data/ab9206c3bac8b47df55ac79d63c06e77883f261842132e69ee1420d96cdafea9"
PROCESSED_DIR = "data/processed"
RANDOM_SEED = 42

# 20 Key Features (from AGENT_CONTEXT.md)
KEY_FEATURES = [
    'Flow Duration',
    'Total Fwd Packets',
    'Total Backward Packets',
    'Total Length of Fwd Packets',
    'Total Length of Bwd Packets',
    'Flow Bytes/s',
    'Flow Packets/s',
    'Flow IAT Mean',
    'Flow IAT Std',
    'Flow IAT Max',
    'Fwd IAT Mean',
    'Bwd IAT Mean',
    'SYN Flag Count',
    'RST Flag Count',
    'PSH Flag Count',
    'ACK Flag Count',
    'Destination Port',
    'Packet Length Mean',
    'Packet Length Variance',
    'Average Packet Size'
]


def load_all_csv_files(data_dir):
    """Load all CICIDS 2017 CSV files into a single DataFrame."""
    print("=" * 70)
    print("LOADING CICIDS 2017 DATASET")
    print("=" * 70)
    
    csv_files = glob.glob(os.path.join(data_dir, "*.csv"))
    
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {data_dir}")
    
    print(f"Found {len(csv_files)} CSV files\n")
    
    dfs = []
    for i, filepath in enumerate(csv_files, 1):
        filename = os.path.basename(filepath)
        print(f"[{i}/{len(csv_files)}] Loading {filename}...")
        
        try:
            df = pd.read_csv(filepath, encoding='utf-8', low_memory=False)
            
            # Clean column names (remove leading/trailing spaces)
            df.columns = df.columns.str.strip()
            
            print(f"    ✓ Loaded {len(df):,} rows, {len(df.columns)} columns")
            dfs.append(df)
            
        except Exception as e:
            print(f"    ✗ ERROR: {e}")
            continue
    
    if not dfs:
        raise ValueError("No CSV files could be loaded successfully")
    
    # Combine all DataFrames
    print(f"\nCombining all files...")
    combined_df = pd.concat(dfs, ignore_index=True)
    print(f"✓ Total dataset: {len(combined_df):,} rows\n")
    
    return combined_df


def clean_and_prepare_data(df):
    """Clean data: handle missing values, infinities, and select features."""
    print("=" * 70)
    print("DATA CLEANING")
    print("=" * 70)
    
    # Show label distribution BEFORE cleaning
    print("\nLabel Distribution (BEFORE cleaning):")
    print(df['Label'].value_counts())
    print(f"\nTotal rows: {len(df):,}")
    
    # Replace infinite values with NaN
    print("\n[1/5] Replacing infinite values with NaN...")
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    
    # Check for missing values in key features
    print("\n[2/5] Checking missing values in key features...")
    missing_counts = df[KEY_FEATURES].isnull().sum()
    features_with_missing = missing_counts[missing_counts > 0]
    
    if len(features_with_missing) > 0:
        print("    Features with missing values:")
        for feat, count in features_with_missing.items():
            pct = (count / len(df)) * 100
            print(f"      - {feat}: {count:,} ({pct:.2f}%)")
    else:
        print("    ✓ No missing values in key features")
    
    # Drop rows with ANY missing values in key features or Label
    print("\n[3/5] Dropping rows with missing values...")
    initial_rows = len(df)
    df_clean = df[KEY_FEATURES + ['Label']].dropna()
    rows_dropped = initial_rows - len(df_clean)
    print(f"    ✓ Dropped {rows_dropped:,} rows ({(rows_dropped/initial_rows)*100:.2f}%)")
    print(f"    ✓ Remaining: {len(df_clean):,} rows")
    
    # Check for any remaining invalid values
    print("\n[4/5] Checking for remaining invalid values...")
    invalid_mask = ~np.isfinite(df_clean[KEY_FEATURES].values)
    if invalid_mask.any():
        print(f"    ⚠ WARNING: Found {invalid_mask.sum()} invalid values after cleaning")
        df_clean = df_clean[~invalid_mask.any(axis=1)]
        print(f"    ✓ Removed invalid rows, remaining: {len(df_clean):,}")
    else:
        print("    ✓ No invalid values found")
    
    # Show label distribution AFTER cleaning
    print("\n[5/5] Label Distribution (AFTER cleaning):")
    label_counts = df_clean['Label'].value_counts()
    print(label_counts)
    print(f"\nTotal rows after cleaning: {len(df_clean):,}")
    print()
    
    return df_clean


def encode_labels(df):
    """Encode labels: Binary (BENIGN=0, ATTACK=1) and save label mapping."""
    print("=" * 70)
    print("LABEL ENCODING")
    print("=" * 70)
    
    # Create binary labels (for RL agent simplicity in MVP)
    # BENIGN = 0 (ALLOW), All attacks = 1 (BLOCK)
    print("\nEncoding Strategy: Binary Classification")
    print("  - BENIGN → 0 (ALLOW)")
    print("  - All Attacks → 1 (BLOCK)")
    
    # Map all attack types to 1, BENIGN to 0
    df['Label_Binary'] = df['Label'].apply(lambda x: 0 if x == 'BENIGN' else 1)
    
    # Also keep multi-class labels for future use
    unique_labels = df['Label'].unique()
    label_to_id = {label: idx for idx, label in enumerate(sorted(unique_labels))}
    df['Label_Multiclass'] = df['Label'].map(label_to_id)
    
    print(f"\nUnique attack types found: {len(unique_labels)}")
    print("\nLabel Mapping (Multiclass):")
    for label, idx in sorted(label_to_id.items(), key=lambda x: x[1]):
        count = (df['Label'] == label).sum()
        print(f"  {idx:2d} → {label:30s} ({count:,} samples)")
    
    print(f"\nBinary Label Distribution:")
    binary_counts = df['Label_Binary'].value_counts()
    for label, count in binary_counts.items():
        label_name = "BENIGN (ALLOW)" if label == 0 else "ATTACK (BLOCK)"
        pct = (count / len(df)) * 100
        print(f"  {label} ({label_name}): {count:,} ({pct:.2f}%)")
    
    # Save label mapping for future reference
    mapping_path = os.path.join(PROCESSED_DIR, "label_mapping.txt")
    with open(mapping_path, 'w') as f:
        f.write("BINARY LABELS:\n")
        f.write("0 = BENIGN (ALLOW)\n")
        f.write("1 = ATTACK (BLOCK)\n\n")
        f.write("MULTICLASS LABELS:\n")
        for label, idx in sorted(label_to_id.items(), key=lambda x: x[1]):
            f.write(f"{idx} = {label}\n")
    
    print(f"\n✓ Label mapping saved to: {mapping_path}\n")
    
    return df, label_to_id


def normalize_features(X_train, X_val, X_test):
    """Normalize features to [0, 1] range using MinMaxScaler."""
    print("=" * 70)
    print("FEATURE NORMALIZATION")
    print("=" * 70)
    
    print("\nNormalizing features to [0, 1] range using MinMaxScaler...")
    print("(Scaler fitted on TRAINING set only to prevent data leakage)")
    
    scaler = MinMaxScaler(feature_range=(0, 1))
    
    # Fit on training set only
    X_train_scaled = scaler.fit_transform(X_train)
    
    # Transform validation and test sets using training scaler
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)
    
    print(f"\n✓ Training set scaled:   {X_train_scaled.shape}")
    print(f"✓ Validation set scaled: {X_val_scaled.shape}")
    print(f"✓ Test set scaled:       {X_test_scaled.shape}")
    
    # Show sample statistics
    print(f"\nTraining set stats after scaling:")
    print(f"  Min:  {X_train_scaled.min():.6f}")
    print(f"  Max:  {X_train_scaled.max():.6f}")
    print(f"  Mean: {X_train_scaled.mean():.6f}")
    print()
    
    return X_train_scaled, X_val_scaled, X_test_scaled, scaler


def split_and_save_data(df):
    """Split data into train/val/test and save as numpy arrays."""
    print("=" * 70)
    print("TRAIN/VAL/TEST SPLIT")
    print("=" * 70)
    
    # Extract features and labels
    X = df[KEY_FEATURES].values
    y_binary = df['Label_Binary'].values
    y_multiclass = df['Label_Multiclass'].values
    
    print(f"\nFeature matrix shape: {X.shape}")
    print(f"Binary labels shape:  {y_binary.shape}")
    print(f"Multiclass labels:    {y_multiclass.shape}")
    
    # Split: 70% train, 15% val, 15% test (stratified by binary label)
    print("\nSplitting strategy: 70% train / 15% val / 15% test")
    print("(Stratified sampling to maintain class balance)")
    
    # First split: 70% train, 30% temp
    X_train, X_temp, y_train_bin, y_temp_bin, y_train_multi, y_temp_multi = train_test_split(
        X, y_binary, y_multiclass, 
        test_size=0.30, 
        random_state=RANDOM_SEED, 
        stratify=y_binary
    )
    
    # Second split: 50% val, 50% test (from the 30% temp)
    X_val, X_test, y_val_bin, y_test_bin, y_val_multi, y_test_multi = train_test_split(
        X_temp, y_temp_bin, y_temp_multi,
        test_size=0.50,
        random_state=RANDOM_SEED,
        stratify=y_temp_bin
    )
    
    print(f"\n✓ Training set:   {X_train.shape[0]:,} samples ({X_train.shape[0]/len(df)*100:.1f}%)")
    print(f"✓ Validation set: {X_val.shape[0]:,} samples ({X_val.shape[0]/len(df)*100:.1f}%)")
    print(f"✓ Test set:       {X_test.shape[0]:,} samples ({X_test.shape[0]/len(df)*100:.1f}%)")
    
    # Show class distribution in each set
    print("\nClass Distribution (Binary):")
    print(f"  Train - Benign: {(y_train_bin==0).sum():,} ({(y_train_bin==0).sum()/len(y_train_bin)*100:.1f}%) | Attack: {(y_train_bin==1).sum():,} ({(y_train_bin==1).sum()/len(y_train_bin)*100:.1f}%)")
    print(f"  Val   - Benign: {(y_val_bin==0).sum():,} ({(y_val_bin==0).sum()/len(y_val_bin)*100:.1f}%) | Attack: {(y_val_bin==1).sum():,} ({(y_val_bin==1).sum()/len(y_val_bin)*100:.1f}%)")
    print(f"  Test  - Benign: {(y_test_bin==0).sum():,} ({(y_test_bin==0).sum()/len(y_test_bin)*100:.1f}%) | Attack: {(y_test_bin==1).sum():,} ({(y_test_bin==1).sum()/len(y_test_bin)*100:.1f}%)")
    
    # Normalize features
    X_train_scaled, X_val_scaled, X_test_scaled, scaler = normalize_features(
        X_train, X_val, X_test
    )
    
    # Save to numpy files
    print("=" * 70)
    print("SAVING PROCESSED DATA")
    print("=" * 70)
    
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    
    files_to_save = {
        'X_train.npy': X_train_scaled,
        'X_val.npy': X_val_scaled,
        'X_test.npy': X_test_scaled,
        'y_train_binary.npy': y_train_bin,
        'y_val_binary.npy': y_val_bin,
        'y_test_binary.npy': y_test_bin,
        'y_train_multiclass.npy': y_train_multi,
        'y_val_multiclass.npy': y_val_multi,
        'y_test_multiclass.npy': y_test_multi,
    }
    
    print("\nSaving files:")
    for filename, data in files_to_save.items():
        filepath = os.path.join(PROCESSED_DIR, filename)
        np.save(filepath, data)
        file_size = os.path.getsize(filepath) / (1024 * 1024)  # MB
        print(f"  ✓ {filename:<25s} - {data.shape} - {file_size:.2f} MB")
    
    # Save feature names
    feature_names_path = os.path.join(PROCESSED_DIR, "feature_names.txt")
    with open(feature_names_path, 'w') as f:
        for i, feature in enumerate(KEY_FEATURES):
            f.write(f"{i}: {feature}\n")
    print(f"  ✓ feature_names.txt")
    
    print(f"\n✓ All files saved to: {PROCESSED_DIR}/")
    print()


def main():
    """Main preprocessing pipeline."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "CICIDS 2017 PREPROCESSOR" + " " * 30 + "║")
    print("║" + " " * 10 + "Dynamic AI Firewall - RL Training Data" + " " * 20 + "║")
    print("╚" + "=" * 68 + "╝")
    print()
    
    # Step 1: Load data
    df = load_all_csv_files(DATA_DIR)
    
    # Step 2: Clean data
    df_clean = clean_and_prepare_data(df)
    
    # Step 3: Encode labels
    df_encoded, label_mapping = encode_labels(df_clean)
    
    # Step 4: Split and save
    split_and_save_data(df_encoded)
    
    # Final summary
    print("=" * 70)
    print("PREPROCESSING COMPLETE ✓")
    print("=" * 70)
    print("\nNext Steps:")
    print("  1. Run: python src/rl_agent/train.py")
    print("  2. Monitor training with TensorBoard")
    print("  3. Evaluate model with: python src/rl_agent/evaluate.py")
    print()
    print("Dataset Summary:")
    print(f"  - Total samples:  {len(df_encoded):,}")
    print(f"  - Features:       {len(KEY_FEATURES)}")
    print(f"  - Attack types:   {len(label_mapping)}")
    print(f"  - Output folder:  {PROCESSED_DIR}/")
    print()


if __name__ == "__main__":
    main()
