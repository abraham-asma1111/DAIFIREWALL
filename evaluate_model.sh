#!/bin/bash
source ~/miniconda3/etc/profile.d/conda.sh
conda activate firewall
python src/rl_agent/evaluate.py
