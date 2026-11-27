#!/usr/bin/env python3
"""Part 4 analysis: tables, plots and the performance model.

    python3 analyze.py            (from ~/heat, after bench.py has finished)

Inputs : results/perf.csv (bench.py), ../mpi/pp_*.csv (ping-pong, Part 0)
Outputs: results/figs/*.png and results/summary.md (tables to paste into the report)
"""
import csv, glob, math, os, re, statistics as st
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

HOSTS = ["heat-julien", "heat-jad", "heat-marc"]
SLOTS = 4                      # vCPUs per VM (hostfile slots)
STEPS_DEFAULT = 100
HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results"); FIG = os.path.join(RES, "figs")
PP = sorted(glob.glob(os.path.join(HERE, "..", "mpi", "pp_*.csv")))          # on the VM
if not PP:                                                                   # in this repository
    PP = sorted(glob.glob(os.path.join(HERE, "..", "mpi", "results", "home_wifi_hotspot_2026-11-27", "pp_*.csv")))
os.makedirs(FIG, exist_ok=True)
out = []                       # lines of summary.md
def say(s=""): out.append(s); print(s)

# ------------------------------------------------------------------ ping-pong fits
def fit_pp(path):
    rows = [l.strip().split(",") for l in open(path) if l[:1].isdigit()]
    m = np.array([float(r[0]) for r in rows]); t = np.array([float(r[2]) for r in rows])
    ts = t[m <= 1024].mean()
    big = m >= (1 << 20)
    tw = np.polyfit(m[big], t[big], 1)[0]
    return ts, tw, m, t

net = {}                       # frozenset({hostA, hostB}) or 'same' -> (ts, tw)
say("## Network (ping-pong, Part 0)\n")
say("| pair | t_s | bandwidth 1/t_w |"); say("|---|---|---|")
plt.figure(figsize=(6, 4))
for f in PP:
    name = os.path.basename(f)[3:-4]                       # e.g. julien_jad, same_julien
    ts, tw, m, t = fit_pp(f)
    if name.startswith("same"):
        net["same"] = (ts, tw); label = "same VM"
    else:
        a, b = name.split("_"); net[frozenset({"heat-" + a, "heat-" + b})] = (ts, tw); label = f"{a} - {b}"
    say(f"| {label} | {ts*1e6:.1f} us | {1/tw/1e6:.2f} MB/s |")
    plt.loglog(m, t, "o-", ms=3, label=label)
    mm = np.logspace(3, 7.3, 50); plt.loglog(mm, ts + mm * tw, "k:", lw=0.8)
plt.xlabel("message size m (bytes)"); plt.ylabel("one-way time (s)")
plt.title("Ping-pong and fitted model $t_s + m\\,t_w$ (dotted)")
plt.legend(fontsize=8); plt.grid(alpha=.3, which="both"); plt.tight_layout()
plt.savefig(os.path.join(FIG, "pingpong.png"), dpi=150); plt.close()

def link(h1, h2):
    return net["same"] if h1 == h2 else net[frozenset({h1, h2})]

# ------------------------------------------------------------------ measurements
rows = [r for r in csv.DictReader(open(os.path.join(RES, "perf.csv"))) if r["status"] == "ok"]
for r in rows:
    for k in ("N", "P", "rep"): r[k] = int(r[k])
    for k in ("t_total", "t_comp", "t_comm"): r[k] = float(r[k])
    r["steps"] = int(r["steps"] or STEPS_DEFAULT)

def group(**kw):
    return [r for r in rows if all(r[k] == v for k, v in kw.items())]
def med(rs, k="t_total"):
    v = [r[k] for r in rs]; return st.median(v) if v else float("nan")
def spread(rs, k="t_total"):
    v = [r[k] for r in rs]; return (max(v) - min(v)) / st.median(v) if len(v) > 1 else 0.0

# ------------------------------------------------------------------ 1. baseline
say("\n## 1. Single-node baseline (serial, median of 3)\n")
say("| VM | N | time/step | time/node t_c | spread |"); say("|---|---|---|---|---|")
tc = {}                                   # host -> seconds per node update
for h in HOSTS:
    vals = []
    for N in sorted({r["N"] for r in group(exp="baseline", host=h)}):
        g = group(exp="baseline", host=h, N=N)
        if not g: continue
        step = med(g) / g[0]["steps"]; node = step / (N - 1) ** 2
        vals.append(node)
        say(f"| {h} | {N} | {step*1e3:.2f} ms | {node*1e9:.2f} ns | {100*spread(g):.0f}% |")
    if vals: tc[h] = st.median(vals)
say("\nCompute rate per VM (median over N): " +
    ", ".join(f"{h}: {tc[h]*1e9:.2f} ns/node ({1/tc[h]/1e6:.0f} Mnode/s)" for h in tc))

# ------------------------------------------------------------------ performance model
def placement(P, mp):
    """host of each rank: --map-by slot fills a VM first, --map-by node is round-robin."""
    return [HOSTS[k // SLOTS] if mp == "slot" else HOSTS[k % len(HOSTS)] for k in range(P)]

def dims(P):
    """same as MPI_Dims_create(P, 2): dims[0] >= dims[1]; dims[0] = Py, dims[1] = Px."""
    best = None
    for a in range(1, P + 1):
        if P % a == 0:
            b = P // a
            if a >= b and (best is None or a - b < best[0] - best[1]): best = (a, b)
    return best

def split(n, p, k):
    base, rem = divmod(n, p); return base + (1 if k < rem else 0)

def model_step(N, P, decomp, mp, net_override=None, tc_override=None):
    """time per step = slowest rank's compute + the halo-exchange phases.
    Each MPI_Sendrecv phase lasts as long as its slowest pair: t_s + m t_w (Task 8.2)."""
    host = placement(P, mp)
    if isinstance(net_override, dict):          # per-pair (ts, tw) values
        lk = lambda a, b: net["same"] if a == b else net_override[frozenset({a, b})]
    elif net_override:
        lk = lambda a, b: net_override
    else:
        lk = link
    tcf = (lambda h: tc_override) if tc_override else (lambda h: tc.get(h, st.median(tc.values())))
    if decomp == "strips" or P == 1:
        Py, Px = P, 1
    else:
        Py, Px = dims(P)
    comp, phases = 0.0, {"ud": 0.0, "lr": 0.0}
    for r in range(P):
        cy, cx = (r, 0) if decomp == "strips" else divmod(r, Px)
        ny, nx = split(N - 1, Py, cy), split(N - 1, Px, cx)
        comp = max(comp, nx * ny * tcf(host[r]))
        row_bytes = 8 * (nx + 2) if decomp == "strips" else 8 * nx   # strips send N+1 values
        for nb in ([r + 1] if cy < Py - 1 else []):               # up neighbour (rows)
            nbr = nb if decomp == "strips" else r + Px
            ts, tw = lk(host[r], host[nbr]); phases["ud"] = max(phases["ud"], ts + row_bytes * tw)
        if decomp == "blocks" and cx < Px - 1:                     # right neighbour (columns)
            ts, tw = lk(host[r], host[r + 1]); phases["lr"] = max(phases["lr"], ts + 8 * ny * tw)
    comm = 2 * phases["ud"] + 2 * phases["lr"]                      # 2 Sendrecv per direction
    return comp + comm, comp, comm

# ------------------------------------------------------------------ effective latencies
# For N = 512 a halo message is only ~4 KB, so a step costs (number of exchange phases) x
# (latency of the slowest link involved). Three runs isolate the three links:
#   strips, map-by node, P=2  : phases use only julien-jad              (2 phases)
#   blocks, map-by node, P=4  : every phase involves julien-marc (and julien-jad)  (4 phases)
#   strips, map-by slot, P=12 : phases involve julien-jad and jad-marc  (2 phases)
def per_phase(d, mp, P, phases):
    g = group(exp="strong", N=512, decomp=d, map=mp, P=P)
    return med(g) / g[0]["steps"] / phases if g else float("nan")
JJ, JL, JM = frozenset({"heat-julien", "heat-jad"}), frozenset({"heat-julien", "heat-marc"}), frozenset({"heat-jad", "heat-marc"})
eff_ts = {JJ: per_phase("strips", "node", 2, 2),
          JL: per_phase("blocks", "node", 4, 4),
          JM: per_phase("strips", "slot", 12, 2)}
net_eff = {k: (eff_ts[k], net[k][1]) for k in eff_ts}
say("\n## Effective latency during the benchmark (from N = 512 runs) vs ping-pong\n")
say("| link | ping-pong t_s | effective t_s in the runs |"); say("|---|---|---|")
for k, lab in [(JJ, "julien - jad"), (JL, "julien - marc"), (JM, "jad - marc")]:
    say(f"| {lab} | {net[k][0]*1e3:.1f} ms | {eff_ts[k]*1e3:.1f} ms |")
say("\n(For a link whose phase also contains a faster link, the value is the slower one.)")

# ------------------------------------------------------------------ 2. strong scaling
say(f"\n## 2. Strong scaling (median of 3, {rows[0]['steps']} steps per run)\n")
T1 = {N: med(group(exp="baseline", host=HOSTS[0], N=N)) for N in {r["N"] for r in rows}}
say("| N | decomp | map | P | Px x Py | T_P (s) | S(P) | E(P) | comm share | model T_P | model (eff. t_s) | spread |")
say("|---|---|---|---|---|---|---|---|---|---|---|---|")
Ns = sorted({r["N"] for r in group(exp="strong")})
styles = {("strips", "slot"): ("C0", "o-"), ("strips", "node"): ("C0", "s--"),
          ("blocks", "slot"): ("C3", "o-"), ("blocks", "node"): ("C3", "s--")}
fig, ax = plt.subplots(len(Ns), 3, figsize=(13, 3.4 * len(Ns)), squeeze=False)
for i, N in enumerate(Ns):
    t1 = T1.get(N, float("nan"))
    for (d, mp), (c, ls) in styles.items():
        Ps, S, E, share, Sm, Se = [], [], [], [], [], []
        for P in sorted({r["P"] for r in group(exp="strong", N=N, decomp=d, map=mp)}):
            g = group(exp="strong", N=N, decomp=d, map=mp, P=P)
            tp = med(g); steps = g[0]["steps"]
            m_tot, _, _ = model_step(N, P, d, mp)
            m_eff = model_step(N, P, d, mp, net_override=net_eff)[0]
            sh = med(g, "t_comm") / tp
            Ps.append(P); S.append(t1 / tp); E.append(t1 / tp / P); share.append(sh)
            Sm.append(t1 / (m_tot * steps)); Se.append(t1 / (m_eff * steps))
            pxpy = f"{g[0]['Px'] or 1}x{g[0]['Py'] or P}"
            say(f"| {N} | {d} | {mp} | {P} | {pxpy} | {tp:.3f} | {t1/tp:.2f} | {t1/tp/P:.2f} | "
                f"{100*sh:.0f}% | {m_tot*steps:.3f} | {m_eff*steps:.3f} | {100*spread(g):.0f}% |")
        if not Ps: continue
        lab = f"{d}, map-by {mp}"
        ax[i][0].plot([1] + Ps, [1] + S, ls, color=c, ms=4, label=lab)
        ax[i][0].plot([1] + Ps, [1] + Sm, ":", color=c, lw=1)
        ax[i][0].plot([1] + Ps, [1] + Se, "-.", color=c, lw=0.8, alpha=.6)
        ax[i][1].plot([1] + Ps, [1] + E, ls, color=c, ms=4, label=lab)
        ax[i][2].plot(Ps, [100 * s for s in share], ls, color=c, ms=4, label=lab)
    ax[i][0].plot([1, 12], [1, 12], "k-", lw=0.5, alpha=.4)
    ax[i][0].set_yscale("log"); ax[i][0].set_ylabel(f"N = {N}\nspeed-up S(P)")
    ax[i][1].set_ylabel("efficiency E(P)"); ax[i][1].set_yscale("log")
    ax[i][2].set_ylabel("time in halo exchange (%)"); ax[i][2].set_ylim(0, 100)
    for a in ax[i]: a.set_xlabel("P"); a.grid(alpha=.3, which="both"); a.set_xticks([1, 2, 3, 4, 6, 8, 12])
ax[0][0].set_title("Speed-up (dotted: model, dash-dot: model with effective $t_s$)", fontsize=9); ax[0][1].set_title("Efficiency"); ax[0][2].set_title("Communication share")
ax[0][2].legend(fontsize=7)
plt.tight_layout(); plt.savefig(os.path.join(FIG, "strong_scaling.png"), dpi=150); plt.close()

# ------------------------------------------------------------------ 3. weak scaling
say("\n## 3. Weak scaling (~1024 x 1024 nodes per process, map-by node)\n")
say("| decomp | P | N | T_P (s) | comm share | model | model (eff. t_s) |"); say("|---|---|---|---|---|---|---|")
plt.figure(figsize=(6, 4))
for d, c in [("strips", "C0"), ("blocks", "C3")]:
    Ps, T, Tm = [], [], []
    for P in sorted({r["P"] for r in group(exp="weak", decomp=d)}):
        g = group(exp="weak", decomp=d, P=P); N = g[0]["N"]; tp = med(g)
        mt = model_step(N, P, d, "node")[0] * g[0]["steps"]
        Ps.append(P); T.append(tp); Tm.append(mt)
        me = model_step(N, P, d, "node", net_override=net_eff)[0] * g[0]["steps"]
        say(f"| {d} | {P} | {N} | {tp:.3f} | {100*med(g,'t_comm')/tp:.0f}% | {mt:.3f} | {me:.3f} |")
    if Ps:
        plt.plot(Ps, T, "o-", color=c, label=f"{d} measured"); plt.plot(Ps, Tm, ":", color=c, label=f"{d} model")
plt.xlabel("P"); plt.ylabel(f"run time, {rows[0]['steps']} steps (s)"); plt.title("Weak scaling (ideal: flat)")
plt.legend(fontsize=8); plt.grid(alpha=.3); plt.tight_layout()
plt.savefig(os.path.join(FIG, "weak_scaling.png"), dpi=150); plt.close()

# ------------------------------------------------------------------ 4. crossover + real cluster
say("\n## 4. Model: when does spreading over the machines pay off?\n")
Ngrid = np.unique(np.logspace(np.log10(64), np.log10(65536), 200).astype(int))
def crossover(P, d, mp, **kw):
    for N in Ngrid:
        tser = (N - 1) ** 2 * (kw.get("tc_override") or tc[HOSTS[0]])
        if model_step(N, P, d, mp, **kw)[0] < tser: return N
    return None
say("| setting | P | decomp | crossover N (model) |"); say("|---|---|---|---|")
real = (1e-6, 1 / 10e9)                                   # t_s = 1 us, 10 GB/s
for lab, kw in [("Tailscale (ping-pong t_s)", {}), ("Tailscale (effective t_s)", {"net_override": net_eff}),
                ("real cluster (t_s=1us, 10 GB/s)", {"net_override": real})]:
    for P, mp in [(3, "node"), (12, "node"), (12, "slot")]:
        for d in ["strips", "blocks"]:
            x = crossover(P, d, mp, **kw)
            txt = "> 65536" if x is None else ("<= 64 (always)" if x == Ngrid[0] else str(x))
            say(f"| {lab}, map-by {mp} | {P} | {d} | {txt} |")

plt.figure(figsize=(6.5, 4.2))
for lab, kw, ls in [("Tailscale", {}, "-"), ("real cluster", {"net_override": real}, "--")]:
    for d, c in [("strips", "C0"), ("blocks", "C3")]:
        S = [(N - 1) ** 2 * tc[HOSTS[0]] / model_step(N, 12, d, "node", **kw)[0] for N in Ngrid]
        plt.loglog(Ngrid, S, ls, color=c, label=f"{d}, {lab}")
plt.axhline(1, color="k", lw=0.6); plt.axhline(12, color="k", lw=0.6, ls=":")
for N in Ns:
    for d, c in [("strips", "C0"), ("blocks", "C3")]:
        g = group(exp="strong", N=N, decomp=d, map="node", P=12)
        if g: plt.plot(N, T1[N] / med(g), "o", color=c)
plt.xlabel("N"); plt.ylabel("speed-up with P = 12 (map-by node)")
plt.title("Model speed-up vs N (dots: measured)"); plt.legend(fontsize=7); plt.grid(alpha=.3, which="both")
plt.tight_layout(); plt.savefig(os.path.join(FIG, "model_vs_N.png"), dpi=150); plt.close()

# strips vs blocks prediction asked in Part 3
say("\n## 5. Part 3 question: strips or blocks? (model, map-by node)\n")
say("| P | N | strips (s/step) | blocks (s/step) | faster |"); say("|---|---|---|---|---|")
for P in [4, 8]:
    for N in [512, 2048, 8192]:
        a = model_step(N, P, "strips", "node")[0]; b = model_step(N, P, "blocks", "node")[0]
        say(f"| {P} | {N} | {a:.4f} | {b:.4f} | {'strips' if a < b else 'blocks'} |")

open(os.path.join(RES, "summary.md"), "w").write("\n".join(out) + "\n")
print("\nwrote results/summary.md and results/figs/*.png")
