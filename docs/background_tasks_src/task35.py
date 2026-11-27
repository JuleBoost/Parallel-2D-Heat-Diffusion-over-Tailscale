import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
x=1.0; exact=-np.sin(x); eps=np.finfo(float).eps
hs=10.0**-np.arange(1,11)
D2=(np.sin(x-hs)-2*np.sin(x)+np.sin(x+hs))/hs**2
err=np.abs(D2-exact)
for h,d,e in zip(hs,D2,err): print(f"{h:.0e} & {d:.10f} & {e:.3e} \\\\")
hh=np.logspace(-10,-1,200)
plt.figure(figsize=(5.2,3.6))
plt.loglog(hs,err,"o-",label=r"measured $|D_2 f(1)-f''(1)|$")
plt.loglog(hh,hh**2/12*np.sin(1),"--",label=r"truncation $\frac{h^2}{12}|f^{(4)}|$")
plt.loglog(hh,4*eps*np.sin(1)/hh**2,":",label=r"round-off $4\varepsilon|f|/h^2$")
plt.ylim(1e-12,1e6); plt.xlabel("h"); plt.ylabel("error"); plt.legend(fontsize=8); plt.grid(alpha=.3,which="both")
plt.tight_layout(); plt.savefig("task35.pdf")
print("hopt",(48*eps)**0.25)
