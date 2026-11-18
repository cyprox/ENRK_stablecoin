# Code map: crash-simulator family (studies-2026-11)

Why: one place that says which simulator module descends from which, what checks guard each step, and where the outputs are (decision: owner approval of plan 2026-11-13; format of the map not yet validated by the owner).
Scope: only `sources/econ/w2/sim/`, the latest copy of the family. Earlier stages (`sources/econ/{t3,v1,w1,...}/`) hold the older working copies.

## Lineage (each step is validated against the previous one: all new options OFF == previous behaviour)

| Stage | Module | Adds | Check (0 differences expected) |
|---|---|---|---|
| original | `stress_test_crash.py` (byte-identical to the repo's `tests/backtesting/stress_test_crash.py`, diffed 2026-11-17; econ-v5 section 0 found the same for the v1 copy) | the original crash simulator | `base0/check.py` (parts 1-3 compare `stress_fee` with it) |
| T3 | `base0/stress_fee.py` (T3 reference) | peg-index dynamics inside the crash (`index_mode` orig / flat / proc / det); the other features of `stress_fee` on top of the original (fee, calm pre-year, cached snapshot) are tested by `base0/check.py` and were not itemised here | `base0/check.py`, `base0/check_t3.py` |
| V1 | `v1ref/stress_fee.py` (V1 reference), catalogue `v1_exp.py` | surplus rule "SP" (phi_j / phi_r), `size_scale` (debt-ceiling sweep), failed-auction floor schedule (C1), further options listed in the "ECON-V1 extension" block of `stress_fee.py` | `check_v1.py` |
| W1 | `stress_fee.py` minus rb_* (reference in `../../w1/sim/`) | index_mode "path" (unit-of-account paths), `idx_max_up_step` | `check_w1.py` |
| W2 | `stress_fee.py` (this directory) | `rb_*` options, all OFF by default: attentive owners, top-up, early exit / self-liquidation, leveraged-long speculators, miner opex drain, ENRK holder run | `check_w2.py` |

`t3_scen.py` is the scenario catalogue shared by the T3 stage. `p3ref/` holds the reference used by `check_v1.py` part (5) (carry-over legacy basis).

## W2 entry points

| File | Role |
|---|---|
| `w2_exp.py` | cell catalogue: `hl()` headline (500 paths), `oat()` one-at-a-time sweeps, `sens()` impact x capacity, `size()` sustainable-size grid; profiles N0, TOP, EXIT, DEF, SPEC, MIN, RUN, CENTRAL_B, FRIENDLY_B, HOSTILE_B, CENTRAL_R, HOSTILE_R, S0 |
| `w2_run.py` | Monte Carlo runner: paired paths (path i = SEED+i), pool of at most 3 processes, shared calm pre-year snapshot per (fee, speculator set, size); writes `HL/OAT/SENS/SIZE.pkl` (not committed, 22-60 MB) |
| `analyze_w2.py` | tables, paired differences, bootstrap CIs; `python3 -I -B analyze_w2.py > tables_w2.txt` |
| `check_w2.py` | equivalence and consistency checks for the rb_* options (30,060 comparisons) |
| `run_runs.sh`, `run_all.sh` | reproduction of the Monte Carlo steps, one pool at a time |
| `tables_w2.txt` | all tables behind the report |

Reports: `reports/econ-w2-reactive-borrowers.md`, review `reports/review-w1-x1b-w2-independent.md`.

## Known duplication and limits (reported, not resolved)
- The helpers in `analyze_w2.py` (`load`, `col`, `pct`, `bidx`, `cim`, `ciq`, `S`, `f`, `hd`) are copies of `../../w1/sim/analyze_w1.py`, not imports.
- `check_v1.py` and `check_w1.py` differ from the earlier copies in `../../w1/sim` only by a `sys.path.insert` line and, for `check_w1.py`, comment relabels (2026-11-15); `v1_exp.py` differs by one removed unused import; `check_w2.py` is new (comment relabels 2026-11-15). `analyze_err.txt` is an empty leftover.
- Many public functions have no docstring; only module headers carry the "Why:" line.
- `qgate` T201 (print) is raised 216 times: scripts print their results by design.
