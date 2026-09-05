#!/usr/bin/env python3
"""
Recovery Mode vs static parameterisation

Liquity's Recovery Mode raises collateral requirements automatically when the
SYSTEM-WIDE collateral ratio falls below a threshold, forcing deleveraging while
market depth still exists. It is the identified fix for the freeze found by
stress_test_crash.py.

It requires reading aggregate state across every vault. That is available on
Igra EVM and NOT expressible on Kaspa L1, where a covenant can only inspect its
own spending transaction.

So the question this script answers is:

    If we cannot have Recovery Mode, what static parameterisation buys
    equivalent protection — and what does it cost in calm conditions?

Because a static parameter is always on. Recovery Mode costs nothing until it
triggers; a permanently stricter MCR is paid every single day, by everyone.

Standard library only. Deterministic.

Usage:
    python3 recovery_mode_analysis.py
"""

from __future__ import annotations

import statistics
from dataclasses import replace

from stress_test_crash import SEED, Scenario, run

PATHS = 120          # Monte Carlo paths per configuration
CRASH = 0.85         # stress scenario
CALM = 0.20          # ordinary bear market, for measuring the cost of protection


# ----------------------------------------------------------------------------
# Configurations under test
# ----------------------------------------------------------------------------

CONFIGS: list[tuple[str, dict]] = [
    # The protocol as currently specified, with no Recovery Mode.
    ("baseline  MCR 150 / floor 85",
     dict(mcr_trigger=1.50, auction_end_price=0.85)),

    # The benchmark: what Igra EVM can do and Kaspa L1 cannot.
    ("RECOVERY MODE  trigger 150 -> MCR 200",
     dict(mcr_trigger=1.50, auction_end_price=0.85,
          recovery_threshold=1.50, recovery_mcr=2.00)),

    # Static substitute A: liquidate earlier, always.
    ("static  MCR 175 / floor 85",
     dict(mcr_trigger=1.75, auction_end_price=0.85)),
    ("static  MCR 200 / floor 85",
     dict(mcr_trigger=2.00, auction_end_price=0.85)),

    # Static substitute B: let the auction descend deeper, so it still clears
    # when liquidators demand a bigger discount. Costs nothing until reached.
    ("static  MCR 150 / floor 75",
     dict(mcr_trigger=1.50, auction_end_price=0.75)),
    ("static  MCR 150 / floor 70",
     dict(mcr_trigger=1.50, auction_end_price=0.70)),
    ("static  MCR 150 / floor 60",
     dict(mcr_trigger=1.50, auction_end_price=0.60)),

    # Combined.
    ("static  MCR 175 / floor 70",
     dict(mcr_trigger=1.75, auction_end_price=0.70)),
]


# ----------------------------------------------------------------------------
# Monte Carlo harness
# ----------------------------------------------------------------------------

def sweep(drawdown: float, overrides: dict, paths: int = PATHS) -> dict:
    """Run one configuration across many paths; return summary statistics."""
    latent, enrk, kfiat, discount, liq, recovery = [], [], [], [], [], []

    base = Scenario(name="cfg", total_drawdown=drawdown, **overrides)
    for i in range(paths):
        r = run(replace(base, seed=SEED + i))
        latent.append(r.stranded_hole_pct)
        enrk.append(r.enrk_loss_pct)
        kfiat.append(r.kfiat_loss_pct)
        discount.append(r.discount_cost_pct)
        liq.append(r.vaults_liquidated)
        recovery.append(r.recovery_days)

    def p95(xs: list[float]) -> float:
        xs = sorted(xs)
        return xs[min(int(len(xs) * 0.95), len(xs) - 1)]

    return {
        "latent_med": statistics.median(latent),
        "latent_p95": p95(latent),
        "enrk_med": statistics.median(enrk),
        "enrk_p95": p95(enrk),
        "kfiat_med": statistics.median(kfiat),
        "discount_med": statistics.median(discount),
        "liq_med": statistics.median(liq),
        "recovery_med": statistics.median(recovery),
    }


def _hdr(title: str) -> None:
    print(f"\n{title}")
    print("=" * len(title))


def main() -> None:
    print("RECOVERY MODE vs STATIC PARAMETERISATION")
    print(f"{PATHS} Monte Carlo paths per configuration, 1000 vaults, "
          f"opening ICR 200%")
    print("latent = unbacked debt not yet realised, the freeze metric")
    print("discount = value transferred from vault owners to liquidators")

    # ---- 1. Protection under stress ----------------------------------------
    _hdr(f"1. Protection under stress (KAS {-CRASH:.0%})")
    print(f"{'configuration':<38}{'latent':>9}{'p95':>7}"
          f"{'ENRK':>7}{'kFIAT':>7}{'liq':>6}{'RMdays':>8}")
    print("-" * 82)

    crash_results = {}
    for name, cfg in CONFIGS:
        s = sweep(CRASH, cfg)
        crash_results[name] = s
        print(f"{name:<38}{s['latent_med']:>8.0f}%{s['latent_p95']:>6.0f}%"
              f"{s['enrk_med']:>6.0f}%{s['kfiat_med']:>6.0f}%"
              f"{s['liq_med']:>6.0f}{s['recovery_med']:>8.0f}")

    # ---- 2. Cost in calm conditions ----------------------------------------
    _hdr(f"2. Cost in calm conditions (ordinary bear market, KAS {-CALM:.0%})")
    print("A static parameter is always on. This is what it costs when nothing")
    print("dramatic happens — which is almost all of the time.\n")
    print(f"{'configuration':<38}{'liq':>7}{'discount':>10}{'latent':>9}")
    print("-" * 64)

    calm_results = {}
    for name, cfg in CONFIGS:
        s = sweep(CALM, cfg)
        calm_results[name] = s
        print(f"{name:<38}{s['liq_med']:>7.0f}"
              f"{s['discount_med']:>9.1f}%{s['latent_med']:>8.0f}%")

    # ---- 3. Protection bought per unit of cost -----------------------------
    _hdr("3. Protection bought, against cost paid")
    base_crash = crash_results["baseline  MCR 150 / floor 85"]
    base_calm = calm_results["baseline  MCR 150 / floor 85"]

    print("Improvement is the reduction in the p95 latent hole under crash.")
    print("Cost is extra liquidations and extra discount paid in calm markets.\n")
    print(f"{'configuration':<38}{'latent p95':>12}{'calm liq':>10}"
          f"{'calm disc':>11}")
    print("-" * 71)
    for name, _ in CONFIGS:
        c, k = crash_results[name], calm_results[name]
        d_latent = c["latent_p95"] - base_crash["latent_p95"]
        d_liq = k["liq_med"] - base_calm["liq_med"]
        d_disc = k["discount_med"] - base_calm["discount_med"]
        print(f"{name:<38}{d_latent:>+11.0f}%{d_liq:>+10.0f}"
              f"{d_disc:>+10.1f}%")

    print("\nNegative latent = better protection. Positive costs = worse in calm markets.")
    print("\nThe row to compare everything against is RECOVERY MODE: it is what")
    print("Igra EVM can do and Kaspa L1 cannot. Any static configuration that")
    print("matches its protection while costing little in calm conditions is a")
    print("viable substitute; one that only matches it by liquidating people in")
    print("ordinary markets is not.")


if __name__ == "__main__":
    main()
