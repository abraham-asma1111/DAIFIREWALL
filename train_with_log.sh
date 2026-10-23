#!/bin/bash
# Training with logging
/home/abraham/miniconda3/envs/firewall/bin/python -u TRAIN.py 2>&1 | tee training.log
