# Table with observed orders + log-log plot (Task 7.2). Usage: python3 plot_convergence.py convergence.csv
import sys, math, numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
d = np.genfromtxt(sys.argv[1], delimiter=",", names=True)
N, einf, e2 = d["N"], d["err_inf"], d["err_2h"]
print(f"{'N':>5} {'h':>10} {'steps':>7} {'err_inf':>12} {'err_2h':>12} {'p_obs':>6}")
for k in range(len(N)):
    p = "—" if k == 0 else f"{math.log(einf[k-1]/einf[k]) / math.log(2):.2f}"
    print(f"{int(N[k]):>5} {1/N[k]:>10.5f} {int(d['steps'][k]):>7} {einf[k]:>12.4e} {e2[k]:>12.4e} {p:>6}")
h = 1 / N
plt.loglog(h, einf, "o-", label=r"$\|e\|_\infty$")
plt.loglog(h, e2, "s-", label=r"$\|e\|_{2,h}$")
plt.loglog(h, einf[0] * (h / h[0])**2, "k--", label=r"slope 2 ($h^2$)")
plt.xlabel("h"); plt.ylabel("error at T = 0.05"); plt.legend(); plt.grid(True, which="both", alpha=.3)
plt.title("Convergence study, test V"); plt.savefig("convergence.png", dpi=150)
print("saved convergence.png")
