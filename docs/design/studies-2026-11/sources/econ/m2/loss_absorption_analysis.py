#!/usr/bin/env python3
"""
Loss-absorption and design-lever analysis for ENRK.

Question: when a liquidated vault leaves a shortfall, who pays? Today the
seniority waterfall charges kFIAT first, then ENRK. This script measures what
changes if part of the shortfall is charged to the surviving borrowers instead,
and how the main design levers (kFIAT share, opening ICR, redemption, auction
floor) compare.

It does NOT modify stress_test_crash.py. It loads that file's source, applies a
small in-memory patch (a loss-absorption hook plus extra counters) and runs the
patched copy. With policy="waterfall" the patched copy reproduces the original
results exactly; `check` verifies this.

Standard library only. Deterministic (seed = SEED + path index).

Usage (from tests/backtesting/):
    python3 loss_absorption_analysis.py check
    python3 loss_absorption_analysis.py frozen      [--paths 200]
    python3 loss_absorption_analysis.py absorption  [--paths 500]
    python3 loss_absorption_analysis.py levers      [--paths 500]
    python3 loss_absorption_analysis.py all         [--paths 500]

Frozen configuration used everywhere unless stated: auction floor 75%,
redemption enabled, opening ICR 200%, kFIAT share 30%, 1000 vaults.

Caveats (same as stress_test_crash.py):
  * impact_coefficient (0.08) and daily_liquidation_capacity (5% of debt/day)
    dominate every figure and are assumptions, not measurements.
  * kFIAT is assumed at par (branch 1 of KFIAT-DEFINITION-GAP.md).
  * Shortfall is redistributed pro rata to surviving debt (or equally per vault
    for alloc="equal"). Collateral redistribution is not modelled.
  * The 95th percentile is unstable below ~500 paths.
"""

from __future__ import annotations

import argparse
import sys
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "stress_test_crash.py"


# ----------------------------------------------------------------------------
# In-memory patch of the stress test
# ----------------------------------------------------------------------------

_POLICY_CODE = '''
LAST: dict = {}
_ST: dict = {}


def _policy(sc, vaults, v, sk, se, st):
    """Charge part of the uncovered shortfall (sk kFIAT, se ENRK) to the
    surviving borrowers. Returns (bk, be) absorbed by borrowers."""
    if sc.policy == "waterfall" or sk + se <= 0:
        return 0.0, 0.0
    alive = [w for w in vaults if w.alive and w is not v]
    if not alive:
        return 0.0, 0.0
    dalive = sum(w.total_debt_units() for w in alive)
    if dalive <= 0:
        return 0.0, 0.0
    cap_left = (float("inf") if sc.soc_cap is None
                else max(sc.soc_cap * dalive - st["soc"], 0.0))
    total = sk + se
    if sc.policy == "borrowers_first":
        amt = min(total, cap_left)
        bk = min(amt, sk)
        be = amt - bk
    elif sc.policy == "share":
        f = min(sc.soc_share, cap_left / total)
        bk, be = f * sk, f * se
    elif sc.policy == "kfiat_then_borrowers":
        be = min(se, cap_left)
        bk = 0.0
    else:
        raise ValueError(sc.policy)
    if bk + be <= 0:
        return 0.0, 0.0
    for w in alive:
        share = (w.total_debt_units() / dalive if sc.soc_alloc == "prorata"
                 else 1.0 / len(alive))
        w.debt_kfiat += bk * share
        w.debt_enrk += be * share
        st["added"][id(w)] = st["added"].get(id(w), 0.0) + (bk + be) * share
    st["soc"] += bk + be
    return bk, be


'''


def _patched_module():
    src = SRC.read_text()

    def sub(old: str, new: str) -> None:
        nonlocal src
        if src.count(old) != 1:
            sys.exit(f"patch anchor not found exactly once in {SRC.name}:\n{old}")
        src = src.replace(old, new)

    anchor = "    daily_liquidation_capacity: float = 0.05\n"
    sub(anchor, anchor + (
        "\n    # --- loss-absorption policy (analysis only) ---\n"
        '    policy: str = "waterfall"   # waterfall | borrowers_first | share | kfiat_then_borrowers\n'
        "    soc_cap: float | None = None  # cumulative cap, fraction of surviving debt (None = none)\n"
        "    soc_share: float = 0.0        # for policy 'share'\n"
        '    soc_alloc: str = "prorata"    # prorata | equal\n'))

    sub("""            kfiat_written_off += v.debt_kfiat
            enrk_written_off += v.debt_enrk
            v.debt_kfiat = 0.0
            v.debt_enrk = 0.0
""", """            _sk, _se = v.debt_kfiat, v.debt_enrk
            _bk, _be = _policy(scenario, vaults, v, _sk, _se, _ST)
            kfiat_written_off += _sk - _bk
            enrk_written_off += _se - _be
            v.debt_kfiat = 0.0
            v.debt_enrk = 0.0
""")

    anchor = "    debt_units_start = sum(v.total_debt_units() for v in vaults)\n"
    sub(anchor, anchor + (
        "    _ST.clear()\n"
        "    _ST.update(soc=0.0, added={}, init={id(w): w.total_debt_units() for w in vaults})\n"))

    anchor = "    return Result(\n        scenario=scenario.name,"
    sub(anchor, """    _hit = [w for w in vaults if id(w) in _ST['added']]
    _tx = (sorted(_ST['added'][id(w)] / _ST['init'][id(w)] for w in _hit)
           if _hit else [0.0])
    LAST.clear()
    LAST.update(soc_pct=100.0 * _ST['soc'] / debt_units_start,
                tax_max=100.0 * _tx[-1])
""" + anchor)

    sub("def run(scenario: Scenario) -> Result:", _POLICY_CODE + "def run(scenario: Scenario) -> Result:")

    mod = types.ModuleType("stress_test_crash_patched")
    mod.__file__ = str(SRC)
    sys.modules[mod.__name__] = mod       # dataclasses needs this
    exec(compile(src, str(SRC), "exec"), mod.__dict__)
    return mod


M = _patched_module()
SEED = M.SEED


# ----------------------------------------------------------------------------
# Monte Carlo helper
# ----------------------------------------------------------------------------

def q(xs, p):
    xs = sorted(xs)
    return xs[min(int(len(xs) * p), len(xs) - 1)]


def mc(paths: int, drawdown: float, **kw) -> dict:
    rows = []
    for i in range(paths):
        r = M.run(M.Scenario(name="x", total_drawdown=drawdown, seed=SEED + i, **kw))
        rows.append((r.enrk_loss_pct, r.kfiat_loss_pct, r.stranded_hole_pct,
                     r.final_kas_ratio, M.LAST.get("soc_pct", 0.0),
                     M.LAST.get("tax_max", 0.0)))
    cols = ("enrk", "kfiat", "latent", "kas", "soc", "taxmax")
    out = {}
    for j, name in enumerate(cols):
        v = [row[j] for row in rows]
        out[name] = {"p50": q(v, .50), "p95": q(v, .95), "p99": q(v, .99),
                     "max": max(v), "mean": sum(v) / len(v)}
    return out


FROZEN = dict(auction_end_price=0.75, enable_redemption=True)


# ----------------------------------------------------------------------------
# Commands
# ----------------------------------------------------------------------------

def cmd_check(paths: int) -> None:
    """The patched copy with policy='waterfall' must equal the original."""
    sys.path.insert(0, str(HERE))
    sys.dont_write_bytecode = True
    import stress_test_crash as orig
    bad = 0
    for i in range(min(paths, 50)):
        kw = dict(name="c", total_drawdown=0.85, seed=orig.SEED + i, **FROZEN)
        a = orig.run(orig.Scenario(**kw))
        b = M.run(M.Scenario(**kw))
        for f in ("enrk_loss_pct", "kfiat_loss_pct", "stranded_hole_pct",
                  "vaults_liquidated", "final_kas_ratio"):
            if getattr(a, f) != getattr(b, f):
                bad += 1
    print("check: patched copy == original" if bad == 0
          else f"check FAILED: {bad} differences")


def cmd_frozen(paths: int) -> None:
    print(f"\nFROZEN CONFIG - {paths} paths per level (floor 75%, redemption on)")
    print(f"{'crash':>6} {'KAS p50':>8} {'ENRK p50':>9} {'p95':>6} {'max':>6}"
          f" {'kFIAT p50':>10} {'p95':>6} {'latent p95':>11}")
    for dd in (0.10, 0.30, 0.50, 0.70, 0.85, 0.95):
        r = mc(paths, dd, **FROZEN)
        print(f"{-dd:>6.0%} {r['kas']['p50']:>8.2f} {r['enrk']['p50']:>9.1f}"
              f" {r['enrk']['p95']:>6.1f} {r['enrk']['max']:>6.1f}"
              f" {r['kfiat']['p50']:>10.1f} {r['kfiat']['p95']:>6.1f}"
              f" {r['latent']['p95']:>11.1f}")


POLICIES = {
    "A  waterfall (kFIAT, then ENRK)": dict(policy="waterfall"),
    "B1 borrowers first, no cap": dict(policy="borrowers_first"),
    "B2 borrowers first, no cap, equal": dict(policy="borrowers_first", soc_alloc="equal"),
    "B3 borrowers first, cap 5%": dict(policy="borrowers_first", soc_cap=0.05),
    "B4 borrowers first, cap 15%": dict(policy="borrowers_first", soc_cap=0.15),
    "C1 25% to borrowers": dict(policy="share", soc_share=0.25),
    "C2 50% to borrowers": dict(policy="share", soc_share=0.50),
    "C3 75% to borrowers": dict(policy="share", soc_share=0.75),
    "D1 kFIAT, borrowers (cap 10%), ENRK": dict(policy="kfiat_then_borrowers", soc_cap=0.10),
    "D2 kFIAT, borrowers (no cap), ENRK": dict(policy="kfiat_then_borrowers"),
}


def cmd_absorption(paths: int) -> None:
    print(f"\nLOSS ABSORPTION - {paths} paths per cell, frozen config")
    for dd in (0.50, 0.70, 0.85, 0.95):
        print(f"\ncrash {-dd:.0%}")
        print(f"{'policy':<38} {'ENRK p95':>8} {'p99':>6} {'kFIAT p95':>10}"
              f" {'latent p95':>11} {'pushed p50/p95 %':>17} {'max burden p95 %':>17}")
        for name, kw in POLICIES.items():
            r = mc(paths, dd, **FROZEN, **kw)
            print(f"{name:<38} {r['enrk']['p95']:>8.1f} {r['enrk']['p99']:>6.1f}"
                  f" {r['kfiat']['p95']:>10.1f} {r['latent']['p95']:>11.1f}"
                  f" {r['soc']['p50']:>8.1f}/{r['soc']['p95']:<8.0f}"
                  f" {r['taxmax']['p95']:>17.0f}")
    print("\npushed = shortfall charged to survivors, % of opening debt; can exceed "
          "100% because a re-liquidated survivor re-socialises the same shortfall.")


def cmd_levers(paths: int) -> None:
    print(f"\nDESIGN LEVERS - crash -85%, {paths} paths, waterfall")
    print(f"{'lever':<34} {'ENRK p95':>8} {'p99':>6} {'kFIAT p95':>10} {'latent p95':>11}")

    def line(label, **kw):
        r = mc(paths, 0.85, **kw)
        print(f"{label:<34} {r['enrk']['p95']:>8.1f} {r['enrk']['p99']:>6.1f}"
              f" {r['kfiat']['p95']:>10.1f} {r['latent']['p95']:>11.1f}")

    for ks in (0.0, 0.15, 0.30, 0.50):
        line(f"kFIAT share {ks:.0%}", kfiat_share=ks, **FROZEN)
    for icr in (1.6, 1.8, 2.0, 2.5, 3.0):
        line(f"opening ICR {icr:.0%}", target_icr=icr, **FROZEN)
    line("floor 75%, no redemption", auction_end_price=0.75)
    line("floor 85% + redemption", auction_end_price=0.85, enable_redemption=True)
    line("floor 85%, no redemption", auction_end_price=0.85)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("command", choices=["check", "frozen", "absorption", "levers", "all"])
    ap.add_argument("--paths", type=int, default=None)
    a = ap.parse_args()
    if a.command in ("check", "all"):
        cmd_check(a.paths or 50)
    if a.command in ("frozen", "all"):
        cmd_frozen(a.paths or 200)
    if a.command in ("absorption", "all"):
        cmd_absorption(a.paths or 500)
    if a.command in ("levers", "all"):
        cmd_levers(a.paths or 500)


if __name__ == "__main__":
    main()
