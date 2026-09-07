#!/bin/bash
# launch_v5.sh — Boot V5 training on the Hetzner cloud VM.
# Run after the user powers on ubuntu-32gb-ash-1 from the Hetzner console.
# Usage: bash scripts/launch_v5.sh
set -e

cd ~/smallchip-ai
source venv/bin/activate

echo "=== Pulling latest code ==="
git pull origin main

echo "=== Generating augmented training data (5K + 8K + 10K + 15K subsets) ==="
# We need to add the 5K-15K bigblue1 subsets to training data, but they're DEFs.
# For now, use the existing 510 chips + V3-generated augmented placements.

echo "=== Starting V5 training (200 epochs) ==="
mkdir -p results/gat_v5
nohup python3 scripts/train_v5_aggressive.py \
  --data data/combined_training_data.json \
  --epochs 200 \
  --save-dir results/gat_v5 \
  --hidden 128 \
  --num-layers 3 \
  --heads 4 \
  --lr 1e-3 \
  --log-every 5 \
  > /tmp/v5.log 2>&1 &
echo "V5 started, PID: $!"
echo ""
echo "Monitor with: tail -f /tmp/v5.log"
echo "After 50 epochs (about 1.5 hours on CCX33), the best model is at:"
echo "  results/gat_v5/gat_v5_model_best.pt"
