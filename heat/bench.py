#!/usr/bin/env python3
"""Part 4 performance runs. Run on heat-julien from ~/heat:

    nohup python3 bench.py > bench.log 2>&1 &      # keeps running if the shell closes
    tail -f bench.log                              # watch progress (Ctrl+C only stops watching)

Every run is appended to results/perf.csv and its raw output kept in results/raw/.
Runs already in perf.csv are skipped, so if anything stops, just start it again.
"""
import csv, os, re, subprocess, sys, time

STEPS = int(os.environ.get("STEPS", "100"))   # fixed number of steps for every run (STEPS=50 for the hotspot)
R = 0.25               # at the stability limit
REPS = 3               # median of 3
HOSTS = ["heat-julien", "heat-jad", "heat-marc"]
HEAT = os.path.expanduser("~/heat/build/heat")
MPI = ["mpirun", "--hostfile", os.path.expanduser("~/hosts"),
       "--mca", "oob_tcp_if_include", "tailscale0",
       "--mca", "btl_tcp_if_include", "tailscale0", "--mca", "btl", "tcp,self"]
LOCAL = os.environ.get("BENCH_LOCAL") == "1"          # only for testing on one machine
if LOCAL:
    MPI = ["mpirun", "--oversubscribe", "--allow-run-as-root"]

OUT = "results"; RAW = os.path.join(OUT, "raw"); CSV = os.path.join(OUT, "perf.csv")
FIELDS = ["exp", "decomp", "map", "host", "N", "P", "Px", "Py", "rep", "steps",
          "t_total", "t_comp", "t_comm", "wall", "status"]

def experiments():
    E = []
    # 1. single-node baseline: serial on every VM
    for host in HOSTS:
        for N in [512, 1024, 2048, 4096, 8192]:
            E.append(dict(exp="baseline", decomp="serial", map="-", host=host, N=N, P=1))
    # 2. strong scaling: fixed N, growing P, two placements
    for N in [512, 2048, 8192]:
        for mp in ["slot", "node"]:
            for d in ["strips", "blocks"]:
                for P in [2, 3, 4, 6, 8, 12]:
                    E.append(dict(exp="strong", decomp=d, map=mp, host="-", N=N, P=P))
    # 3. weak scaling: ~1024 x 1024 interior nodes per process
    for d in ["strips", "blocks"]:
        for P in [1, 2, 4, 8, 12]:
            N = round(1024 * P ** 0.5) + 1
            E.append(dict(exp="weak", decomp=d, map="node", host="-", N=N, P=P))
    return [dict(e, rep=k) for e in E for k in range(1, REPS + 1)]

def key(e):
    return f"{e['exp']}_{e['decomp']}_{e['map']}_{e['host']}_N{e['N']}_P{e['P']}_r{e['rep']}"

def command(e):
    args = [HEAT, "--case", "1", "--N", str(e["N"]), "--r", str(R), "--steps", str(STEPS),
            "--decomp", e["decomp"]]
    if e["decomp"] == "serial":
        host = [] if LOCAL else ["--host", e["host"] + ":1"]
        return MPI + host + ["-np", "1"] + args
    return MPI + ["--map-by", e["map"], "-np", str(e["P"])] + args

def main():
    os.makedirs(RAW, exist_ok=True)
    done = set()
    if os.path.exists(CSV):
        with open(CSV) as f:
            done = {r["key"] for r in csv.DictReader(f) if r["status"] == "ok"}
    else:
        with open(CSV, "w", newline="") as f:
            csv.writer(f).writerow(["key"] + FIELDS)
    todo = [e for e in experiments() if key(e) not in done]
    total = len(todo)
    print(f"{len(done)} runs already done, {total} to do", flush=True)
    t_start, n = time.time(), 0
    for e in todo:
        k = key(e)
        t0 = time.time()
        try:
            p = subprocess.run(command(e), capture_output=True, text=True, timeout=1800)
            out, status = p.stdout + p.stderr, ("ok" if p.returncode == 0 else f"rc{p.returncode}")
        except subprocess.TimeoutExpired as x:
            out, status = str(x), "timeout"
        wall = time.time() - t0
        with open(os.path.join(RAW, k + ".txt"), "w") as f:
            f.write(" ".join(command(e)) + "\n" + out)
        kv = dict(re.findall(r"(\w+)=([^\s]+)", out))
        if status == "ok" and "t_total" not in kv:
            status = "noparse"
        row = dict(e, Px=kv.get("Px", ""), Py=kv.get("Py", ""), steps=kv.get("steps", ""),
                   t_total=kv.get("t_total", ""), t_comp=kv.get("t_comp", ""),
                   t_comm=kv.get("t_comm", ""), wall=f"{wall:.2f}", status=status)
        with open(CSV, "a", newline="") as f:
            csv.writer(f).writerow([k] + [row[c] for c in FIELDS])
        n += 1
        el = time.time() - t_start
        eta = el / n * (total - n)
        print(f"[{n}/{total}] {100*n/total:5.1f}%  ETA {int(eta//3600)}h{int(eta%3600//60):02d}m  "
              f"{k:42s} {status:7s} t_total={row['t_total']} t_comm={row['t_comm']}", flush=True)
    print("ALL DONE", flush=True)

if __name__ == "__main__":
    main()
