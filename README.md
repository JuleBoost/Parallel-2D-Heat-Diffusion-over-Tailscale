# Parallel 2D heat diffusion with MPI over Tailscale

Explicit finite-difference solver for the 2D heat equation `u_t = α (u_xx + u_yy)` on the unit
square, with a serial version, a 1D strip decomposition and a 2D block decomposition (MPI).

## Team

| Member | Contribution | Tools used |
|---|---|---|
| Julien Boustany | Cluster setup (Tailscale, SSH, Open MPI), solver and MPI code, ping-pong and benchmark runs, performance analysis, Tasks 3.5, 4.1, 6.7 and 7.2, summary report and slides | Multipass, Tailscale, Open MPI, C++/CMake, Python, Claude (Opus 5.5, claude.ai) |
| Jad Allam | His VM and node setup, background-notes Tasks 1.1 to 5.5 (finite differences, discrete Laplacian, update rule, truncation error) | Multipass, Tailscale, Claude (claude.ai) |
| Marc Germani | His VM and node setup, background-notes Tasks 6.1 to 8.2 (stability analysis, convergence order, communication model) | Multipass, Tailscale, Claude (claude.ai) |

## Repository layout

| Path | Content |
|---|---|
| `heat/heat.cpp` | the solver (serial, strips, blocks) |
| `heat/CMakeLists.txt` | build |
| `heat/hosts.example` | example Open MPI hostfile |
| `heat/sync.sh` | copy the source to the other VMs and build on all of them |
| `heat/check.sh` | correctness: serial vs strips/blocks for several N and P, compared with `cmp` |
| `heat/convergence.sh`, `plot_convergence.py` | convergence study on test V (Task 7.2) |
| `heat/plot_field.py` | heat map of an output file |
| `heat/bench.py` | Part 4 performance runs → `results/perf.csv`, raw outputs in `results/raw/` |
| `heat/analyze.py` | Part 4 tables, plots and performance model → `results/summary.md`, `results/figs/` |
| `heat/demo.sh` | live demo: Cases 1 and 2 on the three VMs + heat maps |
| `mpi/hello.cpp`, `mpi/pingpong.cpp` | MPI hello world and ping-pong (Part 0) |
| `mpi/run_pingpong.sh`, `mpi/fit.py`, `mpi/progress.sh` | ping-pong runs, fit of `t_s + m t_w`, live progress |
| `mpi/results/home_wifi_hotspot_2026-11-27/` | ping-pong used for the benchmark (Julien on home Wi-Fi, Jad + Marc on one 4G hotspot) |
| `mpi/results/hotspot_2026-11-21/` | first ping-pong, all three on a 4G hotspot |
| `heat/results/` | `perf.csv` (291 runs), `raw/` (every run's output), `summary.md`, `figs/` (scaling, model, ping-pong, convergence, Task 6.7) |
| `docs/` | `background_tasks_final.pdf` (all Tasks), `background_tasks_src/` (scripts and LaTeX for Tasks 3.5, 4.1, 6.7, 7.2); add the summary report and slides here |
| `llm_log/` | complete logs of all LLM interactions |


## Build (one command)

Ubuntu 24.04 with `build-essential cmake openmpi-bin libopenmpi-dev`:

```
cd heat && cmake -B build && cmake --build build
```

Flags: `-O3 -ffp-contract=off`, C++17. On the cluster, `bash sync.sh` (run on heat-julien)
builds the same source at the same path (`~/heat/build/heat`) on all VMs.

## Command-line options

| Option | Meaning | Example |
|---|---|---|
| `--case` | `1` (four hot edges), `2` (hot top and bottom), `V` (verification, exact solution) | `--case 2` |
| `--N` | number of intervals per direction (grid is (N+1)×(N+1)) | `--N 1024` |
| `--r` | α Δt / h²; refused if r > 1/4 (stability limit) | `--r 0.25` |
| `--T` | final time; Δt is chosen so that T/Δt is an integer and r is not exceeded | `--T 0.05` |
| `--steps` | fixed number of steps (use exactly one of `--T` / `--steps`) | `--steps 500` |
| `--out` | output file: (N+1)² little-endian doubles, row-major, row j = line y_j, no header | `--out u.bin` |
| `--decomp` | `serial` (1 process), `strips` or `blocks` | `--decomp blocks` |
| `--force 1` | allow an unstable r (only used for Task 6.7) | |
| `--print 1` | print each rank's local array incl. ghost rows (debugging, small N only) | |

Output: one line `key=value`, e.g.
`decomp=blocks P=12 Px=3 Py=4 case=1 N=2048 r=0.25 steps=100 T=... t_total=... t_comp=... t_comm=...`
(`err_inf`, `err_2h` added for `--case V`). `t_comp` and `t_comm` are the maxima over ranks.

## Run on one VM

```
./build/heat --case 2 --N 512 --r 0.25 --steps 500 --out u.bin          # serial
mpirun -np 4 ./build/heat --case 2 --N 512 --r 0.25 --steps 500 --decomp blocks --out u.bin
python3 plot_field.py u.bin 512                                         # -> u.png
```

## Run on the cluster

Copy `hosts.example` to `~/hosts`. Open MPI must use the Tailscale interface:

```
mpirun --hostfile ~/hosts --map-by node \
       --mca oob_tcp_if_include tailscale0 --mca btl_tcp_if_include tailscale0 --mca btl tcp,self \
       -np 12 ~/heat/build/heat --case 1 --N 2048 --r 0.25 --steps 100 --decomp blocks
```

`--map-by node` spreads ranks round-robin over the VMs; `--map-by slot` fills each VM first.

## Reproduce the results

```
cd ~/mpi && ./run_pingpong.sh            # Part 0: latency/bandwidth of every pair
cd ~/heat && bash convergence.sh | tee results/convergence.txt          # Part 1
bash check.sh strips | tee results/check_strips.txt                    # Part 2: cmp vs serial
bash check.sh blocks | tee results/check_blocks.txt                    # Part 3: cmp vs serial
STEPS=50 nohup python3 bench.py > bench.log 2>&1 &   # Part 4: all timing runs (resumable)
python3 analyze.py                       # Part 4: tables, plots, model
bash demo.sh                             # live demo
```

## Design notes

- One contiguous array per time level, indexed by one function, two levels swapped after each step.
- Every decomposition evaluates exactly the same expression
  `u + r*(left + right + down + up - 4*u)`, so outputs are bit-for-bit identical to serial.
- Strips: rank 0 owns the bottom strip; neighbours `rank±1`, `MPI_PROC_NULL` outside; whole rows
  (N+1 doubles) sent with `MPI_Sendrecv` straight from the array.
- Blocks: `MPI_Dims_create` + `MPI_Cart_create` (non-periodic), neighbours from `MPI_Cart_shift`;
  columns sent with an `MPI_Type_vector` datatype. Corner ghosts are not exchanged (the 5-point
  stencil does not use them).
- Rows/columns are split as evenly as possible: the first `(N-1) mod P` parts get one extra.
- Rank 0 gathers the interior blocks with `MPI_Gatherv` and writes the file.
