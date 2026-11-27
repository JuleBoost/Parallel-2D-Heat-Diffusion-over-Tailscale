#!/bin/bash
# Run on heat-julien inside ~/mpi: builds here, copies code to the other VMs, builds there.
set -e
./build.sh
for h in heat-jad heat-marc; do
  ssh $h "mkdir -p ~/mpi"
  scp -q hello.cpp pingpong.cpp build.sh $h:~/mpi/
  ssh $h "chmod +x ~/mpi/build.sh && ~/mpi/build.sh"
done
