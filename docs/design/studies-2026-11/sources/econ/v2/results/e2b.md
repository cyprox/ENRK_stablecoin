
### liquidity shocks, shield=1 (locked ENRK cannot sell in the shock); mean over f{10,20,30} x Ka x Kc x g = 81 cells
| policy | area>1pt avoided %% | change in max depth (pts) | reserve spent (pts debt) | cost per pt-day avoided | reserve at shock (pts) | cells helped (CI>0) %% | cells harmed %% |
|---|---|---|---|---|---|---|---|
| b_ORA | +41 | -0.13 | 0.174 | 0.0110 | 6.9 | 100 | 0 |
| b_RV | +34 | -0.08 | 0.124 | 0.0093 | 7.0 | 100 | 0 |
| c_y20 | +64 | -1.51 | 4.035 | 0.1621 | 5.6 | 100 | 0 |
| c_y50 | +71 | -1.72 | 7.785 | 0.2836 | 3.5 | 100 | 0 |
| d_ORA_y20 | +5 | -0.06 | 0.039 | 0.0206 | 7.0 | 100 | 0 |
| d_ORA_y50 | +10 | -0.09 | 0.116 | 0.0302 | 7.0 | 100 | 0 |
| d_ORA_y100 | +12 | -0.10 | 0.252 | 0.0538 | 7.0 | 100 | 0 |
| d_RV_y50 | +6 | -0.19 | 0.618 | 0.2486 | 7.0 | 100 | 0 |
| e0_fixed | -0 | +0.00 | 0.000 | nan | 7.0 | 0 | 4 |
| e_ctrl | +3 | -0.01 | 0.000 | 0.0000 | 6.9 | 37 | 37 |

### liquidity shocks, shield=0.5; mean over f{10,20,30} x Ka x Kc x g = 81 cells
| policy | area>1pt avoided %% | change in max depth (pts) | reserve spent (pts debt) | cost per pt-day avoided | reserve at shock (pts) | cells helped (CI>0) %% | cells harmed %% |
|---|---|---|---|---|---|---|---|
| b_ORA | +41 | -0.13 | 0.174 | 0.0110 | 6.9 | 100 | 0 |
| b_RV | +34 | -0.08 | 0.124 | 0.0093 | 7.0 | 100 | 0 |
| c_y20 | +50 | -0.92 | 4.049 | 0.2083 | 5.6 | 100 | 0 |
| c_y50 | +54 | -1.00 | 7.788 | 0.3736 | 3.5 | 100 | 0 |
| d_ORA_y20 | +4 | -0.04 | 0.039 | 0.0250 | 7.0 | 100 | 0 |
| d_ORA_y50 | +9 | -0.05 | 0.118 | 0.0352 | 7.0 | 100 | 0 |
| d_ORA_y100 | +11 | -0.06 | 0.257 | 0.0628 | 7.0 | 100 | 0 |
| d_RV_y50 | +5 | -0.14 | 0.628 | 0.3326 | 7.0 | 89 | 0 |
| e0_fixed | -0 | +0.00 | 0.000 | nan | 7.0 | 0 | 4 |
| e_ctrl | +3 | -0.01 | 0.000 | 0.0000 | 6.9 | 37 | 37 |

### liquidity shocks, shield=0 (locked holders sell like everyone); mean over f{10,20,30} x Ka x Kc x g = 81 cells
| policy | area>1pt avoided %% | change in max depth (pts) | reserve spent (pts debt) | cost per pt-day avoided | reserve at shock (pts) | cells helped (CI>0) %% | cells harmed %% |
|---|---|---|---|---|---|---|---|
| b_ORA | +41 | -0.13 | 0.174 | 0.0110 | 6.9 | 100 | 0 |
| b_RV | +34 | -0.08 | 0.124 | 0.0093 | 7.0 | 100 | 0 |
| c_y20 | +33 | -0.25 | 4.060 | 0.3166 | 5.6 | 99 | 0 |
| c_y50 | +32 | -0.15 | 7.788 | 0.6238 | 3.5 | 95 | 4 |
| d_ORA_y20 | +3 | -0.01 | 0.040 | 0.0317 | 7.0 | 100 | 0 |
| d_ORA_y50 | +7 | -0.01 | 0.120 | 0.0419 | 7.0 | 100 | 0 |
| d_ORA_y100 | +9 | -0.01 | 0.263 | 0.0754 | 7.0 | 100 | 0 |
| d_RV_y50 | +3 | -0.08 | 0.639 | 0.4999 | 7.0 | 81 | 7 |
| e0_fixed | -0 | +0.00 | 0.000 | nan | 7.0 | 0 | 4 |
| e_ctrl | +3 | -0.01 | 0.000 | 0.0000 | 6.9 | 37 | 37 |

### d_ORA_y50 and c_y50 and b_ORA by carry capital Kc (shield=1 and 0)
E2 Kc 0.03 b_ORA avoided +26% dmaxdep -0.11 spent 0.168 cost 0.0128
E2 Kc 0.03 c_y50 avoided +58% dmaxdep -2.15 spent 7.580 cost 0.2634
E2 Kc 0.03 d_ORA_y50 avoided +8% dmaxdep -0.12 spent 0.166 cost 0.0435
E2 Kc 0.03 d_ORA_y100 avoided +9% dmaxdep -0.13 spent 0.365 cost 0.0791
E2 Kc 0.1 b_ORA avoided +44% dmaxdep -0.12 spent 0.174 cost 0.0104
E2 Kc 0.1 c_y50 avoided +77% dmaxdep -1.82 spent 7.838 cost 0.2695
E2 Kc 0.1 d_ORA_y50 avoided +10% dmaxdep -0.07 spent 0.122 cost 0.0337
E2 Kc 0.1 d_ORA_y100 avoided +12% dmaxdep -0.07 spent 0.263 cost 0.0583
E2 Kc 0.3 b_ORA avoided +62% dmaxdep -0.16 spent 0.178 cost 0.0102
E2 Kc 0.3 c_y50 avoided +86% dmaxdep -1.19 spent 7.938 cost 0.3241
E2 Kc 0.3 d_ORA_y50 avoided +14% dmaxdep -0.08 spent 0.060 cost 0.0147
E2 Kc 0.3 d_ORA_y100 avoided +17% dmaxdep -0.11 spent 0.128 cost 0.0259
E2s0 Kc 0.03 b_ORA avoided +26% dmaxdep -0.11 spent 0.168 cost 0.0128
E2s0 Kc 0.03 c_y50 avoided +10% dmaxdep +0.26 spent 7.523 cost 1.5712
E2s0 Kc 0.03 d_ORA_y50 avoided +4% dmaxdep +0.02 spent 0.173 cost 0.0853
E2s0 Kc 0.03 d_ORA_y100 avoided +5% dmaxdep +0.04 spent 0.383 cost 0.1560
E2s0 Kc 0.1 b_ORA avoided +44% dmaxdep -0.12 spent 0.174 cost 0.0104
E2s0 Kc 0.1 c_y50 avoided +35% dmaxdep -0.03 spent 7.828 cost 0.5958
E2s0 Kc 0.1 d_ORA_y50 avoided +7% dmaxdep +0.00 spent 0.126 cost 0.0451
E2s0 Kc 0.1 d_ORA_y100 avoided +9% dmaxdep +0.02 spent 0.274 cost 0.0791
E2s0 Kc 0.3 b_ORA avoided +62% dmaxdep -0.16 spent 0.178 cost 0.0102
E2s0 Kc 0.3 c_y50 avoided +69% dmaxdep -0.69 spent 8.013 cost 0.4104
E2s0 Kc 0.3 d_ORA_y50 avoided +13% dmaxdep -0.07 spent 0.061 cost 0.0162
E2s0 Kc 0.3 d_ORA_y100 avoided +16% dmaxdep -0.09 spent 0.132 cost 0.0290

### by arb capital Ka (shield=1)
Ka 0.02 b_ORA avoided +28% dmaxdep -0.14 spent 0.177 cost 0.0104
Ka 0.02 c_y50 avoided +67% dmaxdep -2.05 spent 7.841 cost 0.1916
Ka 0.02 d_ORA_y50 avoided +9% dmaxdep -0.12 spent 0.228 cost 0.0420
Ka 0.05 b_ORA avoided +47% dmaxdep -0.15 spent 0.182 cost 0.0105
Ka 0.05 c_y50 avoided +73% dmaxdep -1.90 spent 7.795 cost 0.2914
Ka 0.05 d_ORA_y50 avoided +10% dmaxdep -0.10 spent 0.093 cost 0.0256
Ka 0.15 b_ORA avoided +74% dmaxdep -0.11 spent 0.162 cost 0.0124
Ka 0.15 c_y50 avoided +83% dmaxdep -1.22 spent 7.718 cost 0.5260
Ka 0.15 d_ORA_y50 avoided +14% dmaxdep -0.04 spent 0.027 cost 0.0109

### by reserve inflow g (shield=1): reserve at shock and (c) spending
g 0.03 c_y50 avoided +69% spent 2.829 Rshock 1.9
g 0.03 d_ORA_y50 avoided +10% spent 0.116 Rshock 3.0
g 0.03 b_ORA avoided +41% spent 0.174 Rshock 2.9
g 0.06 c_y50 avoided +73% spent 6.475 Rshock 3.2
g 0.06 d_ORA_y50 avoided +10% spent 0.116 Rshock 6.0
g 0.06 b_ORA avoided +41% spent 0.174 Rshock 5.9
g 0.12 c_y50 avoided +72% spent 14.051 Rshock 5.5
g 0.12 d_ORA_y50 avoided +10% spent 0.116 Rshock 12.0
g 0.12 b_ORA avoided +41% spent 0.174 Rshock 11.8
