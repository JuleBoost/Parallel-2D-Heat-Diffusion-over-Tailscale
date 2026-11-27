#!/bin/bash
# Run on heat-julien in ~/heat: builds here, copies the source to the other VMs, builds there.
set -e
cd "$(dirname "$0")"
cmake -B build -S . >/dev/null && cmake --build build | tail -1
for h in heat-jad heat-marc; do
  ssh $h "mkdir -p ~/heat"
  scp -q heat.cpp CMakeLists.txt $h:~/heat/
  ssh $h "cd ~/heat && cmake -B build -S . >/dev/null && cmake --build build | tail -1 && echo built on \$(hostname)"
done
