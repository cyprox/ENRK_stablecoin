# P1 - Documentary consistency audit (read-only), ENRK_stablecoin @ 33c4248, 2026-11-09

Method: every file below was read in full or by targeted range before being cited (PROJECT-STATE rule 3). Reference = docs/design/FROZEN_PARAMETERS.md. Nothing in the repo was modified; simulations were run on a copy in the scratchpad (python3 -I). Scratch files: scratchpad/{sim,run_sim.py,links.py,pdf.swift,deck.txt,sysmap.txt}.

## 0. Scope facts
- docs/analysis/ and docs/specifications/ exist but are EMPTY (also research/, scripts/). PROJECT_MANIFEST.md still lists files in them as "Complete".
- Scanned: README, PROJECT-STATE, PROJECT_MANIFEST (gitignored, .gitignore:50), KFIAT-DEFINITION-GAP (untracked), docs/ENRK_ECOSYSTEM_PROPOSAL, 15 files in docs/design (+ harness-binding-fix.patch), docs/ENRK-System-Map.pdf (12 pp, text extracted), analyse_projet/ PDF (27 pp) and .py.
- Relative links: 63 checked, 0 broken (no #anchor links exist). Code-level cross refs checked: 119 `#[test]` attributes counted in contracts/igra/src (5+11+13+24+6+7+11+11+16+10+5 = 119, OK; not executed to avoid creating target/); kaspa_tokens.rs 827 lines OK, oracle_feeds.rs 557 OK, Rust total 4,663 lines ("~5,000" OK); "145 references" to kfiat in kaspa_tokens.rs = 145 lines OK; "82 of 86 commits by Michael Sutton" at d08e52d OK (git shortlog on local argent/); argent HEAD = e76ee07 OK; 642/532 and 99.93% re-derived from the published fixed/marginal costs OK; 9.2 KAS overflow threshold OK; 513 days exit time OK.
- Search for SIMULATION-FROZEN-CONFIG-2026-11-09.md and ENRK-LOSS-ABSORPTION-SCENARIOS.md (find /Users/simoes, maxdepth 4-5, excluding Library): ABSENT. Only analyse_projet/loss_absorption_analysis.py exists.
- Claude outputs/ENRK-repo-patch.zip (gitignored, 345 KB, 2026-09-05 17:40): contains PROJECT-STATE.md, docs/ENRK-System-Map.pdf, docs/design/{STRESS-TEST-CRASH-RESULTS,EXECUTION_TARGET_ASSESSMENT,PHASE_4_ARCHITECTURE_PROPOSAL,L1_NATIVE_REDUCED_SPEC}.md, CHANGES.md. It is the Sept-5 hygiene-pass patch bundle (pre-measurement versions). Obsolete; must not be re-applied (would revert the L1 spec/assessment/state to pre-Sept-6 content).

## BLOCKERS

B1. PROJECT_MANIFEST.md asserts every value the Sept 5 hygiene pass deleted documents for.
- :137-141 "Price: 100% -> 85%", "80% -> Stability Pool / 20% -> Treasury"; :143-146 "Primary: Band Protocol / Fallback: Chainlink"; :60 "Community governance (optional)"; :38 "Oracle integration (Band Protocol)"; :37 "Igra smart contract (Rust)"; :1-19,:72-110 list ~10 files that do not exist (Frozen-Parameters.md, Deployment-Strategy.md, Token-Naming-ENRK.md, ...); :172 "Last Updated: September 3".
- Mitigation: file is gitignored, so not published. But it sits in the repo root next to README and contradicts FROZEN on 5 of the 6 stale-value classes you asked about.
- Rec: delete it or replace with a 3-line pointer to PROJECT-STATE.md (owner decision). Do not leave as is.

B2. Reference figures in FROZEN_PARAMETERS (and copies) that the repo's own script does not reproduce.
 a) FROZEN §2 (:46-48) "200% -> 250% moves ENRK p95 loss from 11.2% to 11.6% - very slightly worse". Copied in Immutable-By-Design.md (~l.76-78 "11.2% to 11.6% - slightly worse"), STRESS-TEST banner :11-13, REDEMPTION :134, README :128-129, System Map p.? ("moves ENRK p95 loss from 11.2% to 11.6%"). Reproduction with tests/backtesting/stress_test_crash.py copy, -85%, 200 paths, floor 75, target_icr 2.0 vs 2.5: no redemption ENRK p95 11.13 -> 9.85 (better); with redemption 4.26 -> 3.75 (better). The analysis deck (pp.16,18) also shows 250% improving (4.1 -> 3.3; 4.3 -> 3.8). Conclusion "keep 200%" can still stand on the 25% capital cost, but "slightly worse" is false on the current script and is the stated evidence for a frozen parameter. kFIAT p95 is flat (55.7 -> 55.5) so "buys little" is defensible; "worse" is not.
 b) FROZEN §4 :106-107, REDEMPTION :75-83, System Map "kFIAT 2%" at -85% with redemption. Reproduction (200 paths): kFIAT loss median 6.25, p95 38.97, worst 66.5. No statistic gives 2%. The statistic (median/mean/p95) is never named in any of the 4 documents. Deck p.9 and p.26 flag the same non-reproduction. Related: RECOVERY-MODE :41-46 and :66 "ENRK 0% -> 1%, kFIAT 5% -> 14%" have unlabeled statistics (match medians in recovery_mode_results.txt, 120 paths; current 200-path run gives median 1.2/15.5).
 c) FROZEN §4 :99 and README :124, ECOSYSTEM :214, L1_SPEC :365 "p95 latent hole 46% -> 0%" for floor 75 WITHOUT redemption: recovery_mode_results.txt (120 paths) gives 0%, but a 200-path run gives 3.84% (p95), 0.0% only with redemption. The deck (p.17) shows 4%. Not wrong in kind, but "zero" is path-count sensitive (deck p.26 notes p95 unstable < 500 paths).
- Rec: re-run with >=500 paths, state statistic + path count + seed next to every cited loss figure, and correct the 11.2/11.6 sentence in all 6 places the same day (hygiene rule 1).

B3. Deck figures are untraceable inside the repo (hygiene rule 2: "Nothing counts as recorded until committed").
- analyse_projet/ENRK - Dossier pitch deck complet.pdf pp.14-20 cite "ENRK-LOSS-ABSORPTION-SCENARIOS.md du projet" (p.14) and a frozen-config simulation; neither document exists anywhere on the machine. The only artifact is analyse_projet/loss_absorption_analysis.py, which is untracked and cannot run where it sits: :44-45 `SRC = HERE / "stress_test_crash.py"` but analyse_projet/ has no stress_test_crash.py (docstring :19 says run from tests/backtesting/).
- I reproduced the deck's headline frozen-config numbers independently (200 paths: ENRK p95 4.26, kFIAT median 6.25/p95 38.97, worst 16.2/66.5, latent p95 0), so p.8-p.11 are credible; pp.14-18 (500-path rule comparisons) were not re-run.
- Rec: commit the .py + result files (or the missing .md) before the deck is used externally; until then label pp.14-20 "unrecorded".

## IMPORTANT

I1. docs/ENRK-System-Map.pdf is stale yet PROJECT-STATE.md:156 (index) calls it "Start here for the overview" and README:139 lists it.
- p.1 "Execution layer: Kaspa L1 - pending validation"; p.12 "Covenant oracle construction UNVALIDATED"; p.9-10 lists the original 5 open questions incl. "What are SilverScript's script-size limits?" (answered Sept 6); "Igra path was set aside" vs PROJECT-STATE "Open: Kaspa L1 vs Igra"; "Q1: ... against an embedded constant" (refuted by Q1c). Last touched 8c9be59 (Sept 5). Footer/p.1 URL "github.com/cyprox/ENRK" and p.12 "github.com/cyprox/ENRK" - the repo is cyprox/ENRK_stablecoin (git remote).
- Rec: regenerate or add a banner "pre-measurement, Sept 5".

I2. ECOSYSTEM_PROPOSAL contradicts itself on Q1c and atomicity.
- :109-110 "Its covenant_id is frozen into every vault script" and :122 `OpInputCovenantId(1) == ORACLE_COVENANT_ID` vs :239-243 and :303 "covenant_id cannot be a compile-time constant". :147-151 "Round R is consumed and round R+1 created atomically ... removes the window entirely" vs :246-248 "not atomic as written". §5 discloses it but §3.2/§3.3 (the "part we most want reviewed") carry no marker.
- :374 "with the flow moving permanently to the protocol" vs FROZEN §6/§10.4 "Fee destination after the cap = open (burn on L1 / pro-rata reserve on Igra)".
- Rec: add inline "see §5" notes to §3.2/3.3; reword :374.

I3. L1_NATIVE_REDUCED_SPEC.md internal contradictions.
- :417 "The gating problem - oracle freshness - is resolved (§2.3, §2.4)" and :465 "The L1 path no longer has a hole in it" vs :147-157 ("does not hold for the construction as currently written") and open item 7 (:442). :406 table says "Price oracle: §2.3 unsolved". :86 `== ORACLE_COVENANT_ID` vs :73-75 (not a constant). :190-193 "Exact numbers are deliberately omitted ... a specific maximum N is not [certain]" vs :212-219 measured table. :375 "`Recovery-Mode-Analysis`" is not a file name.
- Rec: fix :417/:465 (these are rule-1 leftovers).

I4. EXECUTION_TARGET_ASSESSMENT.md.
- :22-24 "Verdict in one line: neither layer can currently carry this protocol. Kaspa L1 cannot express a shared price oracle" - directly contradicted by the banner (:7-20) and §8; :58-59 "It is not expressible on Kaspa L1 today." The banner covers it only by reference. Rule 1.
- :139-142 states the Guardians route has "no published aggregate daily limit", but :245 (and ECOSYSTEM :66 "Both KAS routes are capped at ~200,000 KAS per 24 hours") say both routes are capped. Only KasExitBridge has the 200k/25h throttle (:105).
- :117 "102,700,000 KAS" stress-test collateral has no traceable derivation (also reused UB-EXPOSURE :80).

I5. PHASE_4_ARCHITECTURE_PROPOSAL.md: banner (:7-13) covers fee design, but §5.1 (:150-165 80/20 pool/treasury split), §5.2 (:176-189 fees minted), §7 (:266-286 treasury "Open decision ... Burn / 100% pool / Keep") and §9 (:309-320 "What I need from you ... Treasury") remain as live open questions; treasury is decided in FROZEN §6. Status line :3 "PROPOSAL - awaiting approval, no code written"; first-person chat residue ("I have no strong view"). 164-test plan (:304) never realised (119 tests).
- Rec: mark §5.1/5.2/7/9 SUPERSEDED inline, or delete them.

I6. STRESS-TEST-CRASH-RESULTS.md: banner (:6-15) lists two corrections but :125-134 ("What this changed in the design") still says Recovery Mode "became the identified fix ... its unavailability on L1 is the most significant loss" and the 250% result "made a gold reserve unnecessary" - exactly the Sept 4 four-hour contradiction PROJECT-STATE rule 1 describes, left in the same file. :92-93 "Raising the minimum ... to 250% removes the exposure" also stands unflagged beyond the banner.
- Table :49-59 does not match its own committed output tests/backtesting/stress_test_results.txt (section 7): doc -85% kFIAT 5/12/15 vs txt 5/10/14; -95% kFIAT 3/7/9 vs txt 3/6/7.

I7. GITHUB-ISSUE-46-UPDATE.md.
- :88 "Compute mass remains 3-4% under limit at both breaking points": A N=640 485,854/500,000 = 2.8% under; B N=530 444,764/500,000 = 11.0% under. False for B.
- :22,:109,:113 call the measured object an "N->N round transition"/"640-entry round transition"; REMEASUREMENT §6.1 says N=642 measures N independent USE spends, republication is unmeasured and `sweep` is 1->2 (:56). README:26 / ECOSYSTEM:304 / PROJECT-STATE:48 "Ceiling on N per oracle round" inherit the wording.
- :194,:239 still "640 / 530" after the :62 correction. GITHUB-ISSUE-46-COMMENT.md (posted text) :7,:34,:50 likewise, with no banner.
- PROJECT-STATE:52 "Published as two comments on issue #46 on September 6" - repo holds one comment file; GITHUB-ISSUE-46-COMMENT-2.md is "Draft. Not posted" (:3). ORACLE-BINDING:42 says issue holds "two comments" (unverifiable offline). Clarify which two.

I8. Oracle "condition (a)" (spender must co-spend a real vault) is claimed as the DoS-resistance mechanism in ECOSYSTEM:146, L1_SPEC:137-140 but is NOT implemented in either variant: examples/enrk/a/oracle.ag:24-29 admits it ("deliberately omitted ... dependency cycle ... see NOTES.md"); b/oracle.ag `use` (l.21-24) has no vault check either. NOTES.md does not exist anywhere in the repo (dangling reference). UB-EXPOSURE:176-178 says only "Variant A's use still lacks condition (a)" - B lacks it too. README "What is not claimed" does not mention it.

I9. BACKTESTING / PEG-FORMULA numbers inconsistent and unsourced.
- PEG-FORMULA:21-27 gives Alt 3 volatility/drawdown/Sharpe "NaN" (diverges) as the "definitive" figures; BACKTESTING:114-120 gives Alt 3 vol 45-65%, max DD -78%. FROZEN §1:28-29 mixes them: "cut peg drawdown from -78% to -17.3%" (-78% from the superseded estimate, -17.3% from the definitive run). Same scenario named differently: bull case Alt 3 "+600%" (PEG:127) vs "+580%" (BACKTESTING:211), Alt 3.5 +211% vs +386%.
- The 4,380-day simulation script is not in the repo (PROJECT_MANIFEST:98 lists ENRK_Backtest_Simple.py as TODO; tests/backtesting has only stress_test_crash.py and recovery_mode_analysis.py). Data "2014-2026" for a chain that started 2021 (BACKTESTING:63 admits Bitcoin proxy) - the 25.0% / -17.3% / 0.42 / 886 / 319 figures have no reproducible source.
- BACKTESTING:190-211 scenario probabilities "~40% / ~30% / ~10%" have no source (deck p.6 explicitly says its scenarios have no calibrated probability). :161 "Bitcoin 50 EH/s in 2021 to 120 EH/s in 2024" looks wrong (order of magnitude) - unsourced, check.

I10. KFIAT-DEFINITION-GAP.md (untracked) vs the rest.
- Not indexed in PROJECT-STATE/README; PROJECT-STATE (Sept 15) does not list "kFIAT denomination" as an open decision though the deck (p.23) calls it the gating question, and KFIAT:142-144 says every published kFIAT figure assumes par. FROZEN §3 lists kFIAT cap as decided with no denomination.
- Verified OK: types.rs:80/106 end_price 85, :119-142 80/20, types.rs:220 the only consumer, 8 signatures, 145 lines, chronology (types.rs one commit 4b39b92).
- Small inaccuracies: :113 vs real line numbers not re-checked; :207 required_bid is at liquidation.rs:206 (off by one); :149 PHASE_4 "added Sept 5" - it first appears Sept 3 under "Claude outputs/" (4b39b92), renamed Sept 5; liquidation.rs:8,:115,:129 also carry the stale 85% (omitted from §7).

I11. harness not fixed in repo: tests/enrk_mass.rs:91 still `CovenantBinding::new(0, covenant_id)`; fix exists only as docs/design/harness-binding-fix.patch (unapplied, unindexed in README/PROJECT-STATE, author line `enrk@kaspa.network` = an invented-looking address on a domain the project does not appear to own). GITHUB-ISSUE-46-UPDATE:220-225 and REMEASUREMENT §9.1 acknowledge it. Rec: apply (owner go), or at least index the patch; replace the e-mail.

I12. README / PROJECT-STATE index gaps: README:141-154 omits ORACLE-BINDING, REMEASUREMENT-2026-09-15, UNDEFINED-BEHAVIOUR-EXPOSURE, GITHUB-ISSUE-46-COMMENT-2, harness patch (REMEASUREMENT is linked at :40 only). PROJECT-STATE:48,52 and header "Last updated: September 15" - 55 days stale relative to 2026-11-09, no mention of deck/loss-absorption work or KFIAT doc.

## MINOR
- Header dates stale: FROZEN_PARAMETERS:3 "September 3" (file added Sept 5, edited Sept 15 with §10 content); L1_SPEC:3, EXECUTION:3, PHASE_4:3 "September 3" despite Sept 6/15 edits; Immutable-By-Design has no date; ECOSYSTEM:5 "September 2026".
- FROZEN §6 :168 uses $0.12/kWh to price the 2.5M cap (~$300k) while PEG-FORMULA:65 sets the launch baseline at ~$0.08/kWh. The two should agree or the cap's dollar value is ambiguous. Sum of FROZEN's line items = 205k-410k USD (OK around 300k). Deck p.20 uses "40-100k per code audit" (ECOSYSTEM:331) - FROZEN assumes code audits are externally funded; consistent but the budget line "economic audit 30-70k" differs from "40-100k" scale.
- README:104-106 "Past a 61% drawdown ... 57% of total debt at p95" mixes the -85% threshold story with the -95% p95 figure (57% is STRESS-TEST:70 at -95%; README:124 "46%" is -85%). UB-EXPOSURE:119 repeats "57% of debt at p95". State the drawdown.
- UB-EXPOSURE:36-39 says "Four of the eight categories are absent" then lists five. UB:224 "a hundred or so lines" vs 280 lines of .ag.
- REMEASUREMENT:354-356 "ORACLE-BINDING.md if written, and §7 of this document's companion note" - ORACLE-BINDING exists; companion note is unspecified.
- Deck vs docs: p.22 "overflow from ~10 KAS" vs 9.2 KAS; p.13 kFIAT worst case "66%" vs p.9 "67%"; p.17 floor-85+redemption latent 26% vs REDEMPTION:58 32% (path counts differ); p.10 latent "45%" vs FROZEN 46%. All are within sampling noise and the deck footnotes most of them.
- STABLECOIN-FAILURE-ANALYSIS: no sources section; Terra/Curve/Anchor figures ($285M, 48%, 75%, 80%), "four or five times since 2021", "Iron" and "Ethena" mentioned without support; MakerDAO "governance failure" cited in the closing paragraph but never analysed.
- ECOSYSTEM:281-283 "Kaskad chose Igra EVM. KRON is on L1 but is an AMM" - third-party claims; sources only in EXECUTION Sources list. L1_SPEC:33-35 "private-key reconstruction on each exit" unsourced.
- GITHUB-ISSUE-46-UPDATE:127 / COMMENT:44 "other stablecoins rely on centralized or L2 oracles with similar latencies" - unsupported comparative claim in a document aimed at core devs.
- PEG-FORMULA:127 labels a hand computation "Measured".
- Immutable-By-Design:~193 "worst case for the oracle is ... recoverable" - in an immutable protocol nothing is recoverable by the protocol; wording.
- Empty tracked-looking directories docs/analysis, docs/specifications, research, scripts (not in git).

## Stale-value sweep result (docs + PDFs, excluding PROJECT_MANIFEST)
- Auction floor 85: only appears as history (STRESS-TEST, RECOVERY-MODE, REDEMPTION, banners, comparison tables) and in code comments (types.rs, liquidation.rs). OK.
- 80/20 pool/treasury: only in PHASE_4 §5.1 (I5), KFIAT:190 (as code-stale note), types.rs.
- Band/Chainlink: only PROJECT_MANIFEST (B1), KFIAT:191, types.rs.
- DAO/governance: docs only mention it as "none"; EXECUTION:106 and L1_SPEC:405,:476 refer to Igra's governance, correct context.
- Treasury cap 2,500,000: consistent in README, FROZEN, Immutable, System Map, deck p.13/p.20.
- Fees in KAS: consistent everywhere except PHASE_4 §5.2 (I5).
- Peg weights 40/30/20/10 and clip [0.1, 5.0], ICR 200, MCR 150, kFIAT 30% at mint, auction 120 min, fees 2/4/1, breaker 10%/6h, redemption floor 100%: consistent in README, PROJECT-STATE, Immutable, System Map, deck p.3-4. Deck p.3-4,p.13 match FROZEN.

## Deck-specific cross-check vs FROZEN (analyse_projet PDF)
Matches FROZEN: p.3 parameter table, p.4 weights and "7 points / 17% vs 10%", p.13 "20% jusqu'a 2,5 M", p.20 arithmetic (2.5M/(0.004 x debt); $300k). Departures it flags itself: ENRK 4.3% vs 5.0% (p.8), kFIAT 6.3%/39% vs "2%" (p.9). Departures it does NOT flag: 250% ICR improves ENRK p95 (p.16, p.18) while FROZEN says worse (B2a); p.22 "10 KAS" vs 9.2; p.12 leverage table is internally consistent (liquidation threshold -34% checks out: 0.66 / (0.5 x 0.88) = 1.5). p.21 "Rust 119 tests" OK; "Stability Pool defectueux", "no deployed code" OK. Deck cites commit 33c4248 = HEAD, OK.
