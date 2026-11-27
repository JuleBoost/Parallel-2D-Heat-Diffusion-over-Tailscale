#!/bin/bash
# Live progress of run_pingpong.sh. Run in a 2nd shell tab:  bash ~/mpi/progress.sh
cd ~/mpi
w() { local m=$1 r; if ((m<=65536)); then r=200; elif ((m<=1048576)); then r=20; else r=3; fi; echo $(( r*(m+50000) )); }
total=0; for ((m=8; m<=16777216; m*=2)); do total=$((total+$(w $m))); done; total=$((total*3))
done_work() { local d=0 f m; for f in pp_julien_jad.csv pp_julien_marc.csv pp_jad_marc.csv; do
  [ -f "$f" ] || continue; for m in $(grep -E '^[0-9]' "$f" | cut -d, -f1); do d=$((d+$(w $m))); done; done; echo $d; }
t0=$(date +%s); d0=$(done_work)
while true; do
  d=$(done_work); now=$(date +%s); el=$((now-t0)); pct=$((100*d/total))
  if (( d>d0 && el>0 )); then left=$(( (total-d)*el/(d-d0) )); eta="$((left/60))m$((left%60))s"; else eta="estimating"; fi
  cur=$(ls -t pp_*.csv 2>/dev/null | head -1)
  if [ -n "$cur" ]; then last=$(tail -n1 "$cur" | cut -d, -f1); age=$((now-$(stat -c %Y "$cur"))); else last=-; age=0; fi
  printf "\r%3d%%  ETA %-11s  %-20s at %9s B  (last update %ss ago)   " "$pct" "$eta" "$cur" "$last" "$age"
  (( d>=total )) && { echo; echo "DONE"; break; }
  sleep 5
done
