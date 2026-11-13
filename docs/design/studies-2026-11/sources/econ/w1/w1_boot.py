"""Why: builds the empirical 60-day unit-value windows (bootstrap paths) from the long history 2005-07-25..2026-11-06 for ECON-W1 (decision: owner question 2026-11-11).
Window k: path[c] = u(s_k + c + 1)/u(s_k), c = 0..59, for each unit (basket quantities fixed at the window start). Output boot.npz."""
import sys, numpy as np
sys.dont_write_bytecode = True
import units_data as U
dd, S = U.long_fx(); n = len(dd); H = 60
cn, eu, rb, gd, el = S["CNY"], S["EUR"], S["RUB"], S["gold"], S["elec"]
def win(f):
    return np.array([f(slice(s + 1, s + H + 1), s) for s in range(n - H)])
out = {"U2": win(lambda sl, s: cn[sl] / cn[s]), "U3": win(lambda sl, s: (1 + eu[sl] / eu[s] + cn[sl] / cn[s]) / 3),
       "U3b_eq": win(lambda sl, s: (1 + cn[sl] / cn[s] + rb[sl] / rb[s]) / 3), "U3b_532": win(lambda sl, s: .5 + .3 * cn[sl] / cn[s] + .2 * rb[sl] / rb[s]),
       "U4": win(lambda sl, s: el[sl] / el[s]), "U6": win(lambda sl, s: gd[sl] / gd[s]), "RUB": win(lambda sl, s: rb[sl] / rb[s])}
np.savez("boot.npz", **out)
for k, v in out.items(): print(k, v.shape, "end-of-window min/max %.3f %.3f" % (v[:, -1].min(), v[:, -1].max()), "sd log end %.4f" % np.log(v[:, -1]).std())
