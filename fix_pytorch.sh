#!/bin/bash
# Reinstall PyTorch CPU-only version to fix memory corruption

echo "Uninstalling current PyTorch..."
pip uninstall -y torch torchvision torchaudio

echo "Installing PyTorch CPU-only..."
pip install torch --index-url https://download.pytorch.org/whl/cpu

echo "✓ Done! Now try training again"
