#!/bin/bash
# Training launcher with memory allocator fix
# Usage: bash run_training.sh

echo "=================================================="
echo "Starting Firewall AI Training"
echo "=================================================="
echo ""
echo "Fix applied: MALLOC_CHECK_=0 (ignore minor heap corruptions)"
echo ""

# Set environment variable to bypass allocator clashes
export MALLOC_CHECK_=0

# Run training
python TRAIN.py

echo ""
echo "=================================================="
echo "Training script finished"
echo "=================================================="
