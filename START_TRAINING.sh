#!/bin/bash
# Start full training - Run this in your terminal!
# Usage: bash START_TRAINING.sh

echo "=========================================="
echo "FIREWALL AI - STARTING FULL TRAINING"
echo "=========================================="
echo ""

# Check if TensorFlow is installed
if python -c "import tensorflow" 2>/dev/null; then
    echo "⚠️  WARNING: TensorFlow is installed!"
    echo "This will cause training to crash."
    echo ""
    read -p "Uninstall TensorFlow now? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        pip uninstall -y tensorflow
        echo "✓ TensorFlow uninstalled"
    else
        echo "❌ Cannot proceed with TensorFlow installed"
        exit 1
    fi
fi

echo ""
echo "Starting training..."
echo "This will take 30-60 minutes on CPU"
echo "Press Ctrl+C to stop early (model will be saved)"
echo ""

# Run training
python -u TRAIN.py

echo ""
echo "=========================================="
echo "Training finished!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Reinstall TensorFlow: pip install tensorflow==2.21.0"
echo "2. Evaluate model: python src/rl_agent/evaluate.py"
echo ""
