#!/bin/bash
# cloud_setup.sh — Install everything needed on a fresh Ubuntu 22.04 cloud VM
# Run: bash cloud_setup.sh
set -e

echo "=== SmallChip AI Cloud Setup ==="
echo "Date: $(date)"

# System update
sudo apt-get update -y
sudo apt-get install -y python3-pip python3-venv git wget build-essential

# Create working dir
mkdir -p ~/smallchip
cd ~/smallchip

# Clone our repo
echo "Cloning smallchip-ai..."
git clone https://github.com/hnelabhotla-boop/smallchip-ai.git
cd smallchip-ai

# Create venv
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip wheel setuptools
pip install torch torch-geometric numpy matplotlib fastapi uvicorn gdstk python-multipart
pip install -e .

# Verify
python3 -c "import torch; print(f'PyTorch: {torch.__version__}, CUDA: {torch.cuda.is_available()}')"
python3 -c "import torch_geometric; print(f'PyG: {torch_geometric.__version__}')"

# Get the V3 model
mkdir -p /Users/harshith/Documents/RLChip_ISEF/results/gat_v3_combined_60ep 2>/dev/null || true
# (V3 model is in the repo or downloaded separately)

echo "=== Setup complete ==="
echo "Next: cd smallchip-ai && source venv/bin/activate && python3 scripts/scaling_100m_numpy.py"
