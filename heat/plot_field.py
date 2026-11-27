# Show a field file as an image. Usage: python3 plot_field.py u.bin N [out.png]
import sys, numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
f, N = sys.argv[1], int(sys.argv[2]); out = sys.argv[3] if len(sys.argv) > 3 else f.replace(".bin", ".png")
u = np.fromfile(f, dtype="<f8").reshape(N + 1, N + 1)
plt.imshow(u, origin="lower", extent=[0, 1, 0, 1], cmap="inferno"); plt.colorbar(label="u")
plt.xlabel("x"); plt.ylabel("y"); plt.title(f); plt.savefig(out, dpi=150); print("saved", out)
