import time, stress_fee as N
FZ=dict(auction_end_price=0.75, enable_redemption=True)
b=dict(name="v",total_drawdown=.85,crash_days=60,stability_fee=.03,pre_days=365,junior_ledger=True,kfiat_share=.3,seed=N.SEED,**FZ)
t=time.time(); snap=N.run(N.Scenario(**{**b,"index_mode":"flat"}),stop_after_pre=True); print("pre",time.time()-t)
for kw in (dict(index_mode="flat"),dict(index_mode="proc"),dict(index_mode="det",idx_target=2.0,brk_trigger="mkt",brk_action="liq",brk_latch=False)):
    t=time.time(); r=N.run(N.Scenario(**{**b,**kw}),pre=snap); print(kw,round(time.time()-t,3), r.enrk_loss_pct)
