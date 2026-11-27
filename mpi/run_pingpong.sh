#!/bin/bash
# Run on heat-julien inside ~/mpi. Measures same-VM and every cross-VM pair.
M="mpirun --hostfile $HOME/hosts --mca oob_tcp_if_include tailscale0 --mca btl_tcp_if_include tailscale0 --mca btl tcp,self -np 2"
$M --host heat-julien:2 ./pingpong > pp_same_julien.csv
$M --host heat-julien,heat-jad  ./pingpong > pp_julien_jad.csv
$M --host heat-julien,heat-marc ./pingpong > pp_julien_marc.csv
$M --host heat-jad,heat-marc    ./pingpong > pp_jad_marc.csv
python3 fit.py pp_*.csv
