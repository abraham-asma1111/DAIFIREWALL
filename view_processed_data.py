"""
View processed data summary
"""
import numpy as np

print("="*70)
print("PROCESSED DATA SUMMARY")
print("="*70)

# Load all files
files = {
    'X_train': 'data/processed/X_train.npy',
    'X_val': 'data/processed/X_val.npy',
    'X_test': 'data/processed/X_test.npy',
    'y_train': 'data/processed/y_train_binary.npy',
    'y_val': 'data/processed/y_val_binary.npy',
    'y_test': 'data/processed/y_test_binary.npy',
}

print("\nFile Sizes and Shapes:")
print("-" * 70)
for name, path in files.items():
    data = np.load(path)
    print(f"{name:12s}: {str(data.shape):20s} | dtype: {data.dtype} | size: {data.nbytes/(1024**2):.2f} MB")

# Show sample data
print("\n" + "="*70)
print("SAMPLE DATA (First 3 rows of training set)")
print("="*70)

X_train = np.load('data/processed/X_train.npy')
y_train = np.load('data/processed/y_train_binary.npy')

print("\nFeatures (X_train) - First 3 samples, First 5 features:")
print(X_train[:3, :5])

print("\nLabels (y_train) - First 20 samples:")
print(y_train[:20])
print(f"  0 = BENIGN, 1 = ATTACK")

print("\n" + "="*70)
print("CLASS DISTRIBUTION")
print("="*70)

for split in ['train', 'val', 'test']:
    y = np.load(f'data/processed/y_{split}_binary.npy')
    benign = (y == 0).sum()
    attack = (y == 1).sum()
    total = len(y)
    
    print(f"\n{split.upper()} set ({total:,} samples):")
    print(f"  Benign: {benign:,} ({benign/total*100:.2f}%)")
    print(f"  Attack: {attack:,} ({attack/total*100:.2f}%)")

print("\n" + "="*70)
print("FEATURE STATISTICS (Training Set)")
print("="*70)

print(f"\nMin value:  {X_train.min():.6f}")
print(f"Max value:  {X_train.max():.6f}")
print(f"Mean value: {X_train.mean():.6f}")
print(f"Std dev:    {X_train.std():.6f}")

print("\nFeature-wise stats (first 5 features):")
for i in range(5):
    feat_min = X_train[:, i].min()
    feat_max = X_train[:, i].max()
    feat_mean = X_train[:, i].mean()
    print(f"  Feature {i}: min={feat_min:.4f}, max={feat_max:.4f}, mean={feat_mean:.4f}")

print("\n✓ Data looks good and ready for training!")
