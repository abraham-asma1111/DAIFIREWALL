#!/bin/bash
# Automated Pipeline - Runs all steps after RL training completes

set -e  # Exit on any error

echo "======================================================================"
echo "DYNAMIC AI FIREWALL - AUTOMATED PIPELINE"
echo "======================================================================"
echo ""

# Activate conda environment
echo "[INFO] Activating firewall environment..."
source ~/miniconda3/etc/profile.d/conda.sh
conda activate firewall

# Wait for training to complete
echo "[INFO] Checking if training is complete..."
if [ -f "models/firewall_all_data.zip" ]; then
    echo "✓ Training complete! Model found: models/firewall_all_data.zip"
else
    echo "✗ Training not complete yet. Model not found."
    echo "   Current training progress:"
    tail -5 training_all_data.log | grep timesteps || echo "   (Check training_all_data.log for details)"
    echo ""
    echo "   Run this script again after training completes."
    exit 1
fi

echo ""
echo "======================================================================"
echo "STEP 1: EVALUATE RL MODEL"
echo "======================================================================"
python src/rl_agent/evaluate.py

echo ""
echo "======================================================================"
echo "STEP 2: REINSTALL TENSORFLOW"
echo "======================================================================"
echo "[INFO] Checking TensorFlow installation..."
if python -c "import tensorflow" 2>/dev/null; then
    echo "✓ TensorFlow already installed"
else
    echo "[INFO] Installing TensorFlow 2.21.0..."
    pip install tensorflow==2.21.0
fi

echo ""
echo "======================================================================"
echo "STEP 3: TRAIN BEHAVIORAL BASELINE (Anomaly Detector)"
echo "======================================================================"
python src/detection/behavioral_baseline.py

echo ""
echo "======================================================================"
echo "STEP 4: TRAIN NOVELTY SCORER (FAISS)"
echo "======================================================================"
python src/detection/novelty_scorer.py

echo ""
echo "======================================================================"
echo "STEP 5: TEST INTEGRATED DETECTION SYSTEM"
echo "======================================================================"
python src/detection/integrated_detector.py

echo ""
echo "======================================================================"
echo "✅ PIPELINE COMPLETE"
echo "======================================================================"
echo ""
echo "All models trained and tested successfully!"
echo ""
echo "Next steps:"
echo "  1. Review evaluation metrics: logs/evaluation_metrics.txt"
echo "  2. Check confusion matrix: logs/confusion_matrix_*.png"
echo "  3. Start API server: python src/api/main.py"
echo "  4. Test with live traffic: sudo python src/sensor/network_sensor.py"
echo ""
