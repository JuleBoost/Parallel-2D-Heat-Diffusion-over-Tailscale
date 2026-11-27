import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
lam=50.0
def fe(dt,T=1.0):
    n=round(T/dt); u=1.0; us=[u]
    for _ in range(n): u=u+dt*(-lam*u); us.append(u)
    return np.array(us)
def be(dt,T=1.0):
    n=round(T/dt); u=1.0; us=[u]
    for _ in range(n): u=u/(1+lam*dt); us.append(u)
    return np.array(us)
# (b) scan dt = 1/n
print("(b) scan")
for n in [20,22,24,25,26,28,30,40,50]:
    dt=1/n; u=fe(dt); print(f"dt={dt:.5f} 1-lam*dt={1-lam*dt:+.3f} |u(1)|={abs(u[-1]):.3e} max|u|={np.abs(u).max():.3e}")
print("(c) convergence, relative error at t=1")
ex=np.exp(-lam)
prev=None
rows=[]
for dt in [1e-3,5e-4,2.5e-4,1.25e-4,6.25e-5,3.125e-5]:
    u=fe(dt)[-1]; e=abs(u-ex); rel=e/ex
    p="" if prev is None else f"{np.log2(prev/e):.2f}"
    rows.append((dt,u,e,rel,p)); print(f"{dt:.3e} & {u:.4e} & {e:.3e} & {rel:.3e} & {p} \\\\"); prev=e
print("(d) backward Euler")
for n in [5,10,20,25,26,40,100]:
    dt=1/n; u=be(dt); print(f"dt={dt:.4f} u(1)={u[-1]:.3e} monotone={np.all(np.diff(u)<=0)}")
# figure: FE at dt just below/above 2/lam, and BE at large dt
fig,ax=plt.subplots(1,2,figsize=(8,3.2))
for n,st in [(26,"-"),(25,"--"),(24,":")]:
    dt=1/n; u=fe(dt); ax[0].plot(np.arange(len(u))*dt,u,st,label=f"FE $\\Delta t=1/{n}$ ($\\lambda\\Delta t={lam*dt:.2f}$)")
ax[0].set_xlabel("t"); ax[0].set_ylabel("u"); ax[0].legend(fontsize=7); ax[0].set_title("Forward Euler near the limit", fontsize=9)
tt=np.linspace(0,1,400); ax[1].semilogy(tt,np.exp(-lam*tt),"k-",label="exact")
for n in [5,10,40]:
    dt=1/n; u=be(dt); ax[1].semilogy(np.arange(len(u))*dt,u,"o-",ms=3,label=f"BE $\\Delta t=1/{n}$")
ax[1].set_xlabel("t"); ax[1].legend(fontsize=7); ax[1].set_title("Backward Euler, large steps", fontsize=9)
plt.tight_layout(); plt.savefig("task41.pdf")
