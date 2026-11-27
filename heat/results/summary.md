## Network (ping-pong, Part 0)

| pair | t_s | bandwidth 1/t_w |
|---|---|---|
| jad - marc | 94449.9 us | 0.44 MB/s |
| julien - jad | 20318.7 us | 1.60 MB/s |
| julien - marc | 111072.6 us | 1.70 MB/s |
| same VM | 8.9 us | 5310.11 MB/s |

## 1. Single-node baseline (serial, median of 3)

| VM | N | time/step | time/node t_c | spread |
|---|---|---|---|---|
| heat-julien | 512 | 0.12 ms | 0.46 ns | 11% |
| heat-julien | 1024 | 0.75 ms | 0.72 ns | 9% |
| heat-julien | 2048 | 4.67 ms | 1.11 ns | 2% |
| heat-julien | 4096 | 17.89 ms | 1.07 ns | 6% |
| heat-julien | 8192 | 70.53 ms | 1.05 ns | 2% |
| heat-jad | 512 | 0.27 ms | 1.02 ns | 23% |
| heat-jad | 1024 | 0.72 ms | 0.68 ns | 25% |
| heat-jad | 2048 | 4.70 ms | 1.12 ns | 10% |
| heat-jad | 4096 | 17.52 ms | 1.04 ns | 11% |
| heat-jad | 8192 | 69.23 ms | 1.03 ns | 13% |
| heat-marc | 512 | 0.15 ms | 0.58 ns | 6% |
| heat-marc | 1024 | 0.73 ms | 0.70 ns | 3% |
| heat-marc | 2048 | 4.10 ms | 0.98 ns | 18% |
| heat-marc | 4096 | 14.95 ms | 0.89 ns | 3% |
| heat-marc | 8192 | 59.21 ms | 0.88 ns | 4% |

Compute rate per VM (median over N): heat-julien: 1.05 ns/node (951 Mnode/s), heat-jad: 1.03 ns/node (969 Mnode/s), heat-marc: 0.88 ns/node (1133 Mnode/s)

## Effective latency during the benchmark (from N = 512 runs) vs ping-pong

| link | ping-pong t_s | effective t_s in the runs |
|---|---|---|
| julien - jad | 20.3 ms | 23.4 ms |
| julien - marc | 111.1 ms | 22.9 ms |
| jad - marc | 94.4 ms | 44.5 ms |

(For a link whose phase also contains a faster link, the value is the slower one.)

## 2. Strong scaling (median of 3, 50 steps per run)

| N | decomp | map | P | Px x Py | T_P (s) | S(P) | E(P) | comm share | model T_P | model (eff. t_s) | spread |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 512 | strips | slot | 2 | 1x2 | 0.004 | 1.52 | 0.76 | 32% | 0.008 | 0.008 | 12% |
| 512 | strips | slot | 3 | 1x3 | 0.004 | 1.67 | 0.56 | 47% | 0.006 | 0.006 | 15% |
| 512 | strips | slot | 4 | 1x4 | 0.003 | 1.93 | 0.48 | 53% | 0.004 | 0.004 | 2% |
| 512 | strips | slot | 6 | 1x6 | 2.408 | 0.00 | 0.00 | 100% | 2.290 | 2.601 | 12% |
| 512 | strips | slot | 8 | 1x8 | 2.412 | 0.00 | 0.00 | 100% | 2.290 | 2.600 | 3% |
| 512 | strips | slot | 12 | 1x12 | 4.450 | 0.00 | 0.00 | 100% | 10.372 | 5.378 | 6% |
| 512 | strips | node | 2 | 1x2 | 2.342 | 0.00 | 0.00 | 100% | 2.295 | 2.605 | 1% |
| 512 | strips | node | 3 | 1x3 | 4.468 | 0.00 | 0.00 | 100% | 10.376 | 5.381 | 2% |
| 512 | strips | node | 4 | 1x4 | 4.440 | 0.00 | 0.00 | 100% | 11.352 | 5.380 | 5% |
| 512 | strips | node | 6 | 1x6 | 4.412 | 0.00 | 0.00 | 100% | 11.351 | 5.379 | 9% |
| 512 | strips | node | 8 | 1x8 | 4.696 | 0.00 | 0.00 | 100% | 11.351 | 5.378 | 5% |
| 512 | strips | node | 12 | 1x12 | 4.932 | 0.00 | 0.00 | 100% | 11.350 | 5.378 | 3% |
| 512 | blocks | slot | 2 | 1x2 | 0.005 | 1.34 | 0.67 | 37% | 0.008 | 0.008 | 12% |
| 512 | blocks | slot | 3 | 1x3 | 0.004 | 1.60 | 0.53 | 50% | 0.006 | 0.006 | 119% |
| 512 | blocks | slot | 4 | 2x2 | 0.004 | 1.61 | 0.40 | 64% | 0.005 | 0.005 | 29% |
| 512 | blocks | slot | 6 | 2x3 | 2.423 | 0.00 | 0.00 | 100% | 2.163 | 2.473 | 15% |
| 512 | blocks | slot | 8 | 2x4 | 2.400 | 0.00 | 0.00 | 100% | 2.162 | 2.473 | 2% |
| 512 | blocks | slot | 12 | 3x4 | 7.968 | 0.00 | 0.00 | 100% | 19.431 | 9.441 | 3% |
| 512 | blocks | node | 2 | 1x2 | 2.349 | 0.00 | 0.00 | 100% | 2.294 | 2.604 | 2% |
| 512 | blocks | node | 3 | 1x3 | 4.442 | 0.00 | 0.00 | 100% | 10.372 | 5.378 | 5% |
| 512 | blocks | node | 4 | 2x2 | 4.572 | 0.00 | 0.00 | 100% | 22.459 | 4.943 | 4% |
| 512 | blocks | node | 6 | 2x3 | 6.630 | 0.00 | 0.00 | 100% | 22.417 | 9.672 | 38% |
| 512 | blocks | node | 8 | 2x4 | 6.483 | 0.00 | 0.00 | 100% | 22.397 | 9.596 | 6% |
| 512 | blocks | node | 12 | 3x4 | 4.347 | 0.00 | 0.00 | 100% | 9.678 | 4.683 | 3% |
| 2048 | strips | slot | 2 | 1x2 | 0.137 | 1.70 | 0.85 | 5% | 0.111 | 0.111 | 10% |
| 2048 | strips | slot | 3 | 1x3 | 0.124 | 1.88 | 0.63 | 9% | 0.075 | 0.075 | 8% |
| 2048 | strips | slot | 4 | 1x4 | 0.124 | 1.89 | 0.47 | 8% | 0.056 | 0.056 | 2% |
| 2048 | strips | slot | 6 | 1x6 | 3.147 | 0.07 | 0.01 | 99% | 3.091 | 3.402 | 10% |
| 2048 | strips | slot | 8 | 1x8 | 3.264 | 0.07 | 0.01 | 99% | 3.082 | 3.393 | 16% |
| 2048 | strips | slot | 12 | 1x12 | 5.609 | 0.04 | 0.00 | 100% | 13.163 | 8.168 | 7% |
| 2048 | strips | node | 2 | 1x2 | 3.408 | 0.07 | 0.03 | 97% | 3.165 | 3.475 | 13% |
| 2048 | strips | node | 3 | 1x3 | 5.753 | 0.04 | 0.01 | 98% | 13.218 | 8.224 | 24% |
| 2048 | strips | node | 4 | 1x4 | 6.509 | 0.04 | 0.01 | 99% | 13.200 | 8.205 | 23% |
| 2048 | strips | node | 6 | 1x6 | 6.045 | 0.04 | 0.01 | 99% | 13.182 | 8.187 | 14% |
| 2048 | strips | node | 8 | 1x8 | 8.082 | 0.03 | 0.00 | 100% | 13.172 | 8.178 | 3% |
| 2048 | strips | node | 12 | 1x12 | 11.923 | 0.02 | 0.00 | 100% | 13.163 | 8.168 | 11% |
| 2048 | blocks | slot | 2 | 1x2 | 0.134 | 1.74 | 0.87 | 11% | 0.111 | 0.111 | 14% |
| 2048 | blocks | slot | 3 | 1x3 | 0.131 | 1.78 | 0.59 | 7% | 0.075 | 0.075 | 28% |
| 2048 | blocks | slot | 4 | 2x2 | 0.125 | 1.86 | 0.47 | 17% | 0.057 | 0.057 | 17% |
| 2048 | blocks | slot | 6 | 2x3 | 2.934 | 0.08 | 0.01 | 98% | 2.581 | 2.891 | 8% |
| 2048 | blocks | slot | 8 | 2x4 | 2.964 | 0.08 | 0.01 | 99% | 2.572 | 2.882 | 3% |
| 2048 | blocks | slot | 12 | 3x4 | 9.642 | 0.02 | 0.00 | 100% | 21.066 | 11.077 | 17% |
| 2048 | blocks | node | 2 | 1x2 | 3.023 | 0.08 | 0.04 | 96% | 3.164 | 3.474 | 6% |
| 2048 | blocks | node | 3 | 1x3 | 5.536 | 0.04 | 0.01 | 98% | 13.215 | 8.220 | 1% |
| 2048 | blocks | node | 4 | 2x2 | 5.191 | 0.04 | 0.01 | 99% | 23.234 | 5.762 | 3% |
| 2048 | blocks | node | 6 | 2x3 | 7.398 | 0.03 | 0.01 | 99% | 23.055 | 12.018 | 6% |
| 2048 | blocks | node | 8 | 2x4 | 7.440 | 0.03 | 0.00 | 99% | 22.965 | 11.702 | 1% |
| 2048 | blocks | node | 12 | 3x4 | 5.405 | 0.04 | 0.00 | 99% | 10.389 | 5.394 | 6% |
| 8192 | strips | slot | 2 | 1x2 | 2.363 | 1.49 | 0.75 | 2% | 1.765 | 1.765 | 12% |
| 8192 | strips | slot | 3 | 1x3 | 1.934 | 1.82 | 0.61 | 7% | 1.178 | 1.178 | 2% |
| 8192 | strips | slot | 4 | 1x4 | 1.863 | 1.89 | 0.47 | 5% | 0.884 | 0.884 | 3% |
| 8192 | strips | slot | 6 | 1x6 | 10.254 | 0.34 | 0.06 | 94% | 6.709 | 7.020 | 9% |
| 8192 | strips | slot | 8 | 1x8 | 10.392 | 0.34 | 0.04 | 96% | 6.562 | 6.873 | 10% |
| 8192 | strips | slot | 12 | 1x12 | 17.773 | 0.20 | 0.02 | 98% | 24.533 | 19.538 | 7% |
| 8192 | strips | node | 2 | 1x2 | 10.703 | 0.33 | 0.16 | 83% | 7.885 | 8.195 | 5% |
| 8192 | strips | node | 3 | 1x3 | 18.149 | 0.19 | 0.06 | 93% | 25.415 | 20.420 | 9% |
| 8192 | strips | node | 4 | 1x4 | 19.672 | 0.18 | 0.04 | 96% | 25.121 | 20.126 | 32% |
| 8192 | strips | node | 6 | 1x6 | 22.744 | 0.16 | 0.03 | 97% | 24.827 | 19.832 | 22% |
| 8192 | strips | node | 8 | 1x8 | 40.075 | 0.09 | 0.01 | 99% | 24.680 | 19.685 | 34% |
| 8192 | strips | node | 12 | 1x12 | 48.225 | 0.07 | 0.01 | 99% | 24.533 | 19.538 | 17% |
| 8192 | blocks | slot | 2 | 1x2 | 2.260 | 1.56 | 0.78 | 4% | 1.765 | 1.765 | 9% |
| 8192 | blocks | slot | 3 | 1x3 | 1.946 | 1.81 | 0.60 | 10% | 1.178 | 1.178 | 13% |
| 8192 | blocks | slot | 4 | 2x2 | 2.151 | 1.64 | 0.41 | 7% | 0.885 | 0.885 | 2% |
| 8192 | blocks | slot | 6 | 2x3 | 5.498 | 0.64 | 0.11 | 87% | 4.666 | 4.976 | 2% |
| 8192 | blocks | slot | 8 | 2x4 | 5.390 | 0.65 | 0.08 | 90% | 4.518 | 4.829 | 15% |
| 8192 | blocks | slot | 12 | 3x4 | 23.762 | 0.15 | 0.01 | 99% | 27.813 | 17.824 | 1% |
| 8192 | blocks | node | 2 | 1x2 | 11.834 | 0.30 | 0.15 | 86% | 7.884 | 8.194 | 14% |
| 8192 | blocks | node | 3 | 1x3 | 20.016 | 0.18 | 0.06 | 94% | 25.411 | 20.416 | 471% |
| 8192 | blocks | node | 4 | 2x2 | 20.608 | 0.17 | 0.04 | 96% | 26.954 | 9.655 | 4% |
| 8192 | blocks | node | 6 | 2x3 | 27.703 | 0.13 | 0.02 | 98% | 31.803 | 21.814 | 24% |
| 8192 | blocks | node | 8 | 2x4 | 29.429 | 0.12 | 0.01 | 98% | 30.425 | 20.435 | 18% |
| 8192 | blocks | node | 12 | 3x4 | 8.680 | 0.41 | 0.03 | 96% | 13.438 | 8.444 | 13% |

## 3. Weak scaling (~1024 x 1024 nodes per process, map-by node)

| decomp | P | N | T_P (s) | comm share | model | model (eff. t_s) |
|---|---|---|---|---|---|---|
| strips | 1 | 1025 | 0.043 | 0% | 0.055 | 0.055 |
| strips | 2 | 1449 | 2.780 | 98% | 2.811 | 3.121 |
| strips | 4 | 2049 | 5.953 | 99% | 13.202 | 8.207 |
| strips | 8 | 2897 | 7.300 | 99% | 14.733 | 9.738 |
| strips | 12 | 3548 | 10.908 | 100% | 15.908 | 10.914 |
| blocks | 1 | 1025 | 0.043 | 0% | 0.055 | 0.055 |
| blocks | 2 | 1449 | 2.620 | 98% | 2.810 | 3.120 |
| blocks | 4 | 2049 | 5.466 | 99% | 23.234 | 5.762 |
| blocks | 8 | 2897 | 8.172 | 99% | 23.563 | 12.877 |
| blocks | 12 | 3548 | 5.902 | 98% | 11.103 | 6.108 |

## 4. Model: when does spreading over the machines pay off?

| setting | P | decomp | crossover N (model) |
|---|---|---|---|
| Tailscale (ping-pong t_s), map-by node | 3 | strips | 57012 |
| Tailscale (ping-pong t_s), map-by node | 3 | blocks | 57012 |
| Tailscale (ping-pong t_s), map-by node | 12 | strips | 43147 |
| Tailscale (ping-pong t_s), map-by node | 12 | blocks | 20051 |
| Tailscale (ping-pong t_s), map-by slot | 12 | strips | 43147 |
| Tailscale (ping-pong t_s), map-by slot | 12 | blocks | 33811 |
| Tailscale (effective t_s), map-by node | 3 | strips | 55061 |
| Tailscale (effective t_s), map-by node | 3 | blocks | 55061 |
| Tailscale (effective t_s), map-by node | 12 | strips | 40243 |
| Tailscale (effective t_s), map-by node | 12 | blocks | 15713 |
| Tailscale (effective t_s), map-by slot | 12 | strips | 40243 |
| Tailscale (effective t_s), map-by slot | 12 | blocks | 28407 |
| real cluster (t_s=1us, 10 GB/s), map-by node | 3 | strips | <= 64 (always) |
| real cluster (t_s=1us, 10 GB/s), map-by node | 3 | blocks | <= 64 (always) |
| real cluster (t_s=1us, 10 GB/s), map-by node | 12 | strips | <= 64 (always) |
| real cluster (t_s=1us, 10 GB/s), map-by node | 12 | blocks | 68 |
| real cluster (t_s=1us, 10 GB/s), map-by slot | 12 | strips | <= 64 (always) |
| real cluster (t_s=1us, 10 GB/s), map-by slot | 12 | blocks | 68 |

## 5. Part 3 question: strips or blocks? (model, map-by node)

| P | N | strips (s/step) | blocks (s/step) | faster |
|---|---|---|---|---|
| 4 | 512 | 0.2270 | 0.4492 | strips |
| 4 | 2048 | 0.2640 | 0.4647 | strips |
| 4 | 8192 | 0.5024 | 0.5391 | strips |
| 8 | 512 | 0.2270 | 0.4479 | strips |
| 8 | 2048 | 0.2634 | 0.4593 | strips |
| 8 | 8192 | 0.4936 | 0.6085 | strips |
