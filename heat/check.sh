#!/bin/bash
# Checkpoint C2/C3: parallel output must be bit-for-bit identical to serial (cmp).
# Usage: bash check.sh strips   or   bash check.sh blocks
# Processes are spread over the VMs (--map-by node), so P >= 2 always uses several VMs.
cd "$(dirname "$0")"
D=${1:-strips}
M="mpirun --hostfile $HOME/hosts --map-by node --mca oob_tcp_if_include tailscale0 --mca btl_tcp_if_include tailscale0 --mca btl tcp,self"
mkdir -p /tmp/heatcheck; ok=0; bad=0
for c in 1 2; do
  for N in 16 33 64 100; do           # 33 and 100: N-1 not divisible by 3 / by 4
    ./build/heat --case $c --N $N --r 0.2 --steps 50 --out /tmp/heatcheck/serial.bin >/dev/null
    for P in 1 2 3 4; do
      $M -np $P ./build/heat --case $c --N $N --r 0.2 --steps 50 --decomp $D --out /tmp/heatcheck/par.bin >/dev/null
      if cmp -s /tmp/heatcheck/serial.bin /tmp/heatcheck/par.bin; then
        echo "OK    case=$c N=$N P=$P $D"; ok=$((ok+1))
      else
        echo "DIFF  case=$c N=$N P=$P $D"; bad=$((bad+1))
      fi
    done
  done
done
echo "identical: $ok   different: $bad"
