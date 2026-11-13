"""Why: compact unit x architecture x scenario table for the ECON-W1 report (reads WB.pkl, WD.pkl). python3 -B table_main.py"""
import sys
sys.dont_write_bytecode = True
import analyze_w1 as A
WB, WD = A.load("WB"), A.load("WD")
ARCH = ("A0", "A3", "A5", "A8", "STACK")
ROWS85 = [("U1", "flat"), ("U0", "p_base"), ("U0", "x1.5"), ("U0", "x2"), ("U5", "p_base"), ("U5", "x1.5"), ("U2", "s0"), ("U2", "boot"), ("U2", "s+10"), ("U2", "s+20"), ("U2", "s-20"), ("U2", "j+20"), ("U2", "j-20"),
          ("U3", "boot"), ("U3", "s+20"), ("U3b_eq", "s0"), ("U3b_eq", "boot"), ("U3b_eq", "s+20"), ("U3b_532", "boot"), ("U3b_532", "s+20"), ("U4", "s0"), ("U4", "boot"), ("U6", "s0"), ("U6", "boot"), ("U6", "s+20")]
def row(d, u, m, depth):
    out = []
    for a in ARCH:
        k = (u, m, depth, a)
        if k not in d["data"]: out.append("-"); continue
        o = A.S(d, k); out.append(f"{o['en95']:.1f} / {o['ubm']:.1f} / {o['kfm']:.0f}")
    return out
print("KAS -85%, 60 d. Cell = ENRK p95 (% of ENRK) / unbacked mean (% opening debt value) / kFIAT mean loss (% face). 500 paired paths.")
print("| unit variant | scenario (unit path) | A0 r0 s0 | A3 r3 s30 | A5 r3 s30 S3 | A8 r3 s50 | STACK r3 s70 S3 C1a+C2 |"); print("|---|---|---|---|---|---|---|")
for u, m in ROWS85: print(f"| {u} | {m} | " + " | ".join(row(WB, u, m, 85)) + " |")
for u in ("U2", "U3", "U3b_eq", "U3b_532", "U4", "U6"):
    for m in ("worst+", "worst-"): print(f"| {u} | {m} (worst historical 60d window) | " + " | ".join(row(WD, u, m, 85)) + " |")
print("\nKAS -70%, 60 d, same cell format.")
print("| unit variant | scenario | A0 | A3 | A5 | A8 | STACK |"); print("|---|---|---|---|---|---|---|")
for u, m in [("U1", "flat"), ("U0", "p_base"), ("U0", "x1.5"), ("U0", "x2"), ("U5", "p_base"), ("U5", "x1.5"), ("U2", "s0"), ("U2", "boot"), ("U2", "s+10"), ("U2", "s+20"), ("U2", "s-20"), ("U3", "boot"), ("U3b_eq", "boot"), ("U3b_eq", "s+20"), ("U3b_532", "boot"), ("U4", "boot"), ("U6", "boot"), ("U6", "s+20")]:
    print(f"| {u} | {m} | " + " | ".join(row(WB, u, m, 70)) + " |")
