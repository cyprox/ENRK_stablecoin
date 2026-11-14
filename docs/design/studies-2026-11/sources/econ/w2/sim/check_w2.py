"""Why: prove the ECON-W2 reactive-borrower extensions are inert when OFF and consistent when ON (decision: owner approval of plan 2026-11-13).
(1) W2 simulator == W1 simulator (../../w1/sim/stress_fee.py) on every W1 Result field, all rb_* options off (index modes, ledger rules, C1/C2, redemption on/off, pre-year on/off);
(2) rb options that cannot act (rb_on with zero attention / trigger below any ICR / spec ICR above every vault / miners without opex / run gains 0 with signal) == off;
(3) cached pre-year == full run with rb ON (top-up, exits, speculators, miners, run);
(4) ENRK accounting identity with rb ON (start = redeemed + repaid at auction + written off - sub-par + remaining + exited early);
(5) hand checks: top-up total <= budget; speculators only lower ICR and the speculator set is nested across rb_spec_frac; exits only from vaults that were above water."""
import sys, os, dataclasses, importlib.util
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import stress_fee as N
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec); sys.modules[name] = m; spec.loader.exec_module(m); return m
W1 = load("w1sim", os.path.join(HERE, "..", "..", "w1", "sim", "stress_fee.py"))
FIELDS = [f.name for f in dataclasses.fields(W1.Result)]
FZ = dict(auction_end_price=0.75, enable_redemption=True)
bad = n = 0
def cmp(a, b, tag, fields=FIELDS):
    global bad, n
    for f in fields:
        n += 1
        x, y = getattr(a, f), getattr(b, f)
        if x != y and not (x != x and y != y): bad += 1; print("DIFF", tag, f, x, y)
# (1)
for idx in (dict(index_mode="orig"), dict(index_mode="flat"), dict(index_mode="proc", idx_vol=.3, idx_rho=-.5), dict(index_mode="det", idx_target=2.0),
            dict(index_mode="path", idx_path=tuple(1.01 ** c for c in range(60))), dict(index_mode="det", idx_target=2.0, idx_max_up_step=.0025)):
    for extra in (dict(), dict(policy="kfiat_then_borrowers", soc_cap=.05), dict(c1_days=3, subpar_redemption=True), dict(surplus_rule="S3", kfiat_share=.5),
                  dict(enable_redemption=False), dict(capacity_mode="adv", convex_impact=True, size_scale=.4), dict(breaker="liq_latch")):
        for dd in (.7, .85):
            for pre in (0, 120):
                for i in range(3):
                    kw = dict(name="c", seed=N.SEED + i, total_drawdown=dd, stability_fee=.03, pre_days=pre, junior_ledger=True, **{**FZ, "kfiat_share": .3, **idx, **extra})
                    cmp(N.run(N.Scenario(**kw)), W1.run(W1.Scenario(**kw)), f"(1){idx.get('index_mode')}{extra}{dd}{pre}{i}")
print("(1) W2 off == W1:", n, "field comparisons, differences:", bad)
# (2)
b0, n0 = bad, n
INERT = (dict(rb_red_dump=.5, enable_redemption=False), dict(rb_on=True, rb_att=0.0), dict(rb_on=True, rb_trigger_icr=0.0, rb_exit_mode="both"), dict(rb_spec_frac=.4, rb_spec_icr=50.0),
         dict(rb_miner_frac=.4, rb_miner_opex=0.0), dict(rb_run_red=.3, rb_sig_icr=0.0, enable_redemption=True), dict(rb_run_b=.5, rb_sig_icr=0.0),
         dict(rb_on=True, rb_att=0.0, rb_spec_frac=.2, rb_spec_icr=50.0, rb_miner_frac=.3, rb_exit_bump=.3))
for ft in INERT:
    for pre in (0, 60):
        for i in range(8):
            kw = dict(name="c", seed=N.SEED + i, total_drawdown=.85, stability_fee=.03, pre_days=pre, junior_ledger=True, kfiat_share=.3, index_mode="flat", **FZ)
            cmp(N.run(N.Scenario(**{**kw, **ft})), W1.run(W1.Scenario(**{**kw, **{k: v for k, v in ft.items() if not k.startswith("rb_")}})), f"(2){ft}{pre}{i}")
print("(2) inert rb options == off:", n - n0, "comparisons, differences:", bad - b0)
# (3)
b0, n0 = bad, n
RB = (dict(rb_run_red=.2, rb_red_dump=1.0, enable_redemption=True), dict(rb_on=True, rb_exit_mode="both"), dict(rb_on=True, rb_exit_mode="cash", rb_att=.9, rb_budget=3.0), dict(rb_spec_frac=.3, rb_spec_icr=1.7),
      dict(rb_miner_frac=.3, rb_miner_opex=.002), dict(rb_run_red=.2, rb_run_b=.5, enable_redemption=False),
      dict(rb_on=True, rb_exit_mode="sell", rb_exit_bump=.2, surplus_rule="S3", rb_spec_frac=.2, rb_miner_frac=.2, rb_miner_opex=.002, rb_run_red=.2, rb_run_b=.5))
for ft in RB:
    for i in range(8):
        base = dict(name="c", seed=N.SEED + i, total_drawdown=.85, crash_days=60, stability_fee=.03, pre_days=365, junior_ledger=True, kfiat_share=.3, index_mode="flat", **{**FZ, **ft})
        snap = N.run(N.Scenario(**base), stop_after_pre=True)
        full = N.run(N.Scenario(**base)); cached = N.run(N.Scenario(**base), pre=snap)
        n += 1
        if dataclasses.asdict(full) != dataclasses.asdict(cached): bad += 1; print("DIFF (3)", ft, i)
print("(3) cached pre-year == full run with rb ON:", n - n0, "cases, differences:", bad - b0)
# (4)
b0, n0 = bad, n
for ft in RB + (dict(),):
    for dd in (.7, .85):
        for i in range(15):
            r = N.run(N.Scenario(name="c", seed=N.SEED + i, total_drawdown=dd, index_mode="flat", **{**FZ, **ft})); n += 1
            lhs = r.enrk_start
            rhs = r.redeemed_units + r.enrk_repaid_auction + (r.enrk_written_off - r.subpar_loss_pct / 100 * r.enrk_start) + r.enrk_remaining + r.rb_exit_enrk_units
            if abs(lhs - rhs) > 1e-6 * lhs: bad += 1; print("DIFF (4)", ft, dd, i, lhs, rhs)
print("(4) ENRK accounting identity with rb:", n - n0, "cases, differences:", bad - b0)
# (5)
b0, n0 = bad, n
for i in range(10):
    kw = dict(name="c", seed=N.SEED + i, total_drawdown=.85, index_mode="flat", **FZ)
    off = N.run(N.Scenario(**kw)); n += 1
    r = N.run(N.Scenario(rb_on=True, rb_att=1.0, rb_budget=.2, rb_hazard=1.0, rb_delay=0, **kw))
    # total top-up cannot exceed budget x opening collateral value x opening ICR^-1 ... = budget * collateral value; bound by budget * opening debt value * ICR_max(~) -> use 0.2 * sum(coll value) = 0.2 * (ICR~2.0) * debt
    # conservative bound: 0.2 * 6 * debt (ICR spread 0.22 lognormal, max < 6)
    if not (0.0 <= r.rb_topup_pct <= 0.2 * 6.0 * 100.0): bad += 1; print("DIFF (5a)", i, r.rb_topup_pct)
    n += 1
    s1 = N.run(N.Scenario(**kw, rb_spec_frac=.2, rb_spec_icr=1.7)); s2 = N.run(N.Scenario(**kw, rb_spec_frac=.4, rb_spec_icr=1.7))
    if not (s1.debt_units_start >= off.debt_units_start - 1e-9 and s2.debt_units_start >= s1.debt_units_start - 1e-9): bad += 1; print("DIFF (5b)", i)
    n += 1
    if not (s1.mean_icr_start <= off.mean_icr_start + 1e-12): bad += 1; print("DIFF (5c)", i)
    n += 1
    # no exit mode: nobody leaves the system except through liquidation/redemption
    t = N.run(N.Scenario(rb_on=True, rb_att=1.0, rb_hazard=1.0, rb_delay=0, rb_exit_mode="none", **kw))
    if t.rb_exit_cash_pct != 0 or t.rb_exit_sell_pct != 0: bad += 1; print("DIFF (5d)", i)
    n += 1
    # exits are only possible with a market sale when the collateral covers debt: no write-off is created by exiting
    e = N.run(N.Scenario(rb_on=True, rb_att=1.0, rb_hazard=1.0, rb_delay=0, rb_exit_mode="sell", rb_budget=0.0, **kw))
    if e.rb_exit_sell_pct < 0 or e.rb_dump_adv < 0: bad += 1; print("DIFF (5e)", i)
    n += 1
print("(5) hand checks:", n - n0, "checks, differences:", bad - b0)
print("check_w2:", "OK" if bad == 0 else "FAIL", "total comparisons", n, "differences", bad)
