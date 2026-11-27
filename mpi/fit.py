# Fit t(m) = ts + m*tw to a pingpong CSV.  Usage: python3 fit.py file1.csv [file2.csv ...]
import sys, numpy as np
for f in sys.argv[1:]:
    rows = [l.strip().split(",") for l in open(f) if l[:1].isdigit()]
    m = np.array([float(r[0]) for r in rows]); t = np.array([float(r[2]) for r in rows])
    ts = t[m <= 1024].mean()            # latency: small messages
    big = m >= (1 << 20)                # bandwidth: large messages
    tw = np.polyfit(m[big], t[big], 1)[0]
    print(f"{f}: ts = {ts*1e6:.1f} us, bandwidth = {1/tw/1e6:.1f} MB/s")
