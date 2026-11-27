#!/bin/bash
# Task 7.2: convergence study on test V, T = 0.05, r fixed.
cd "$(dirname "$0")"
R=${1:-0.2}
echo "N,steps,err_inf,err_2h" > convergence.csv
for N in 16 32 64 128 256; do
  line=$(./build/heat --case V --N $N --r $R --T 0.05)
  echo "$line"
  steps=$(echo "$line" | grep -o 'steps=[0-9]*' | cut -d= -f2)
  einf=$(echo "$line" | grep -o 'err_inf=[^ ]*' | cut -d= -f2)
  e2=$(echo "$line" | grep -o 'err_2h=[^ ]*' | cut -d= -f2)
  echo "$N,$steps,$einf,$e2" >> convergence.csv
done
python3 plot_convergence.py convergence.csv
