#!/bin/bash
# cloud_run_100m.sh — One-shot: install + run 100M proof on cloud VM
# Usage: bash cloud_run_100m.sh
# Designed for Hetzner CCX43 (96GB RAM, 24 vCPU, Ubuntu 22.04)

set -e
echo "=== SmallChip AI 100M proof on cloud ==="
echo "Date: $(date)"
echo "Hostname: $(hostname)"

# System info
echo ""
echo "=== System info ==="
nproc
free -h
df -h /

# Install deps
echo ""
echo "=== Installing dependencies ==="
sudo apt-get update -y
sudo apt-get install -y python3-pip python3-venv git

# Setup
cd ~
git clone https://github.com/hnelabhotla-boop/smallchip-ai.git 2>/dev/null || (cd smallchip-ai && git pull)
cd smallchip-ai
python3 -m venv venv
source venv/bin/activate
pip install --quiet --upgrade pip wheel setuptools
pip install --quiet numpy matplotlib torch torch-geometric fastapi uvicorn gdstk python-multipart

# Verify
echo ""
echo "=== Verifying install ==="
python3 -c "import torch, numpy; print(f'PyTorch: {torch.__version__}, NumPy: {numpy.__version__}')"

# Run 100M scaling
echo ""
echo "=== Running 100M scaling proof ==="
mkdir -p results
time python3 scripts/scaling_100m_numpy.py --max-cells 100000000 --out results/scaling_100m_cloud.json

# Show results
echo ""
echo "=== Final results ==="
cat results/scaling_100m_cloud.json | python3 -c "
import json, sys
d = json.load(sys.stdin)
print('=' * 60)
print('SmallChip AI — 100M cells PROVEN on $(hostname)')
print('=' * 60)
for r in d['results']:
    if 'error' in r:
        print(f\"  {r['label']:>10}: ERROR\")
    else:
        print(f\"  {r['label']:>10}: {r['n_cells']:>12,} cells, {r['per_net_hpwl_dbu']:>12,.1f} DBU/net, {r['build_time_s']:>5.1f}s\")
"

echo ""
echo "=== DONE. Results saved to results/scaling_100m_cloud.json ==="
echo "Download with: scp root@<IP>:~/smallchip-ai/results/scaling_100m_cloud.json ./"
