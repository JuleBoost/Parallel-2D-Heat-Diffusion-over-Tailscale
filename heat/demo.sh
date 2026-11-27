#!/bin/bash
# Live demo: Cases 1 and 2 across all three VMs, then heat maps.
# Usage: bash demo.sh [N] [P] [decomp] [T]      defaults: 64 3 strips 0.02
# Example on request: bash demo.sh 128 6 blocks 0.02
cd "$(dirname "$0")"
N=${1:-64}; P=${2:-3}; D=${3:-strips}; T=${4:-0.02}
M="mpirun --hostfile $HOME/hosts --map-by node --mca oob_tcp_if_include tailscale0 --mca btl_tcp_if_include tailscale0 --mca btl tcp,self"
mkdir -p demo
for C in 1 2; do
  echo "== Case $C: N=$N P=$P decomp=$D T=$T (processes spread over the VMs)"
  $M -np $P --display-map ./build/heat --case $C --N $N --r 0.25 --T $T --decomp $D --out demo/case$C.bin \
     | grep -E "decomp=|Data for node"
  python3 plot_field.py demo/case$C.bin $N demo/case$C.png
done
echo "Heat maps: ~/heat/demo/case1.png and case2.png"
echo "Copy to Windows (PowerShell): multipass transfer heat-julien:/home/ubuntu/heat/demo/case1.png heat-julien:/home/ubuntu/heat/demo/case2.png ."
