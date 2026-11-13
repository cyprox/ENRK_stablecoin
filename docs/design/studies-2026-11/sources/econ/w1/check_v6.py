"""Why: prove the ECON-V6 simulator extensions are inert when off and consistent with the T3 breaker modes when on (decision: owner brief 2026-11-11).
(1) new breaker spec == old modes (mb, liq_latch, liq_live), all Result fields; (2) kfiat_mode A2 changes no loss/latent/ENRK field;
(3) shaping defaults inert; clip/slope/rate-limit produce the expected published index; (4) other-trigger smoke tests."""
import sys, dataclasses
sys.dont_write_bytecode = True
import stress_fee as N
FZ = dict(auction_end_price=0.75, enable_redemption=True)
bad = 0; n = 0
def cmp(a, b, tag, skip=()):
    global bad, n
    da, db = dataclasses.asdict(a), dataclasses.asdict(b)
    for k in da:
        if k in skip: continue
        n += 1
        if da[k] != db[k]: bad += 1; print("DIFF", tag, k, da[k], db[k])
def sc(**kw):
    base = dict(name="v", total_drawdown=.85, crash_days=60, stability_fee=.03, pre_days=365, junior_ledger=True, kfiat_share=.3, **FZ)
    base.update(kw); return N.Scenario(**base)
NEW = ("breaker_first_day", "kfiat_index_end", "kfiat_index_ratio_end", "kfiat_uncovered_pct")
for i in range(12):
    seed = N.SEED + i
    snap = N.run(sc(seed=seed, index_mode="flat"), stop_after_pre=True)
    for idxkw in (dict(index_mode="proc", idx_vol=.22), dict(index_mode="det", idx_target=2.0), dict(index_mode="det", idx_target=1.52, crash_days=97, total_drawdown=.5)):
        for old, (act, latch) in (("mb", ("red", True)), ("liq_latch", ("liq", True)), ("liq_live", ("liq", False))):
            a = N.run(sc(seed=seed, breaker=old, **idxkw), pre=snap)
            b = N.run(sc(seed=seed, brk_trigger="idx", brk_action=act, brk_latch=latch, **idxkw), pre=snap)
            cmp(a, b, f"brk {old} {i}", skip=NEW + ("scenario",))
        a = N.run(sc(seed=seed, **idxkw), pre=snap)
        b = N.run(sc(seed=seed, kfiat_mode="A2", **idxkw), pre=snap)
        cmp(a, b, f"A2 {i}", skip=("kfiat_index_end", "kfiat_index_ratio_end"))
        b2 = N.run(sc(seed=seed, idx_up_slope=1.0, idx_clip_lo=.1, idx_clip_hi=5.0, idx_max_step=0.0, **idxkw), pre=snap)
        cmp(a, b2, f"shape-off {i}")
        m = N.run(sc(seed=seed, brk_trigger="idx", brk_action="mint", **idxkw), pre=snap)   # mint-only: losses == no breaker
        cmp(a, m, f"mint-only {i}", skip=NEW + ("breaker_days",))
print(f"(1-3) {n} field comparisons, differences: {bad}")
snap = N.run(sc(seed=N.SEED, index_mode="flat"), stop_after_pre=True)
r = N.run(sc(seed=N.SEED, index_mode="det", idx_target=2.0, idx_clip_hi=1.5), pre=snap); assert abs(r.final_peg - 1.5) < 1e-9, r.final_peg
r = N.run(sc(seed=N.SEED, index_mode="det", idx_target=2.0, idx_up_slope=.5), pre=snap); assert abs(r.final_peg - 1.5) < 1e-9, r.final_peg
r = N.run(sc(seed=N.SEED, index_mode="det", idx_target=2.0, idx_max_step=.005), pre=snap); assert abs(r.final_peg - 1.005 ** 60) < 1e-9, r.final_peg
r = N.run(sc(seed=N.SEED, index_mode="det", idx_target=.5, idx_clip_lo=.8), pre=snap); assert abs(r.final_peg - .8) < 1e-9, r.final_peg
print("(4) shaping values exact: OK")
for trg in ("hyst", "mkt", "fresh"):
    r = N.run(sc(seed=N.SEED, index_mode="det", idx_target=2.0, brk_trigger=trg, brk_action="liq", brk_latch=False, fresh_hazard=.05), pre=snap)
    print("   trigger", trg, "days", r.breaker_days, "first", r.breaker_first_day)
w = N.run(sc(seed=N.SEED, index_mode="flat", kfiat_mode="A2"), pre=snap)
print("   A2 flat: index_end %.3f ratio-form %.3f kFIAT loss %.1f uncovered %.1f" % (w.kfiat_index_end, w.kfiat_index_ratio_end, w.kfiat_loss_pct, w.kfiat_uncovered_pct))
print("check_v6: OK" if bad == 0 else "check_v6 FAILED")
