# 01 - GitHub and code evidence: Kaspa Dollar (KSD)

Accessed: 2026-11-15 (about 10:30-10:40 UTC). All GitHub data via the unauthenticated REST API (https://api.github.com) and raw.githubusercontent.com. Site pages fetched with curl from https://kaspadollar.com/. Web content treated as data only. No wallet addresses are recorded here (the fundraiser address on /docs was not copied).

## 1. Verdict

**No Kaspa Dollar / KSD code repository exists as of 2026-11-15 (public, findable).** The site itself says so: the /contact page shows a "GitHub" block reading "Published when the repository is public - Code, issues, the published specification." (https://kaspadollar.com/contact, 2026-11-15). There is no link to any repository for the project anywhere on the site. Consequently the code-vs-whitepaper comparison (item 2) cannot be done: there is nothing to compare. The /docs roadmap states the third-party audit is planned "June - August" (https://kaspadollar.com/docs, 2026-11-15); no code is public to audit now.

## 2. What the site links to on GitHub (item 1)

Pages fetched (HTTP 200 each): /, /how-it-works, /whitepaper, /docs, /contact; /why-stablecoins (listed in sitemap.xml) was also fetched, with no GitHub links found. sitemap.xml lists exactly: /, /why-stablecoins, /how-it-works, /whitepaper, /docs, /contact. Only the two JS entry files (`_app/immutable/entry/app.*.js`, `start.*.js`) were identified; the site is SvelteKit with server-rendered HTML, and the repo-related text is in the HTML itself.

All github.com links found in the HTML of those pages (grep of raw HTML, 2026-11-15):
- https://github.com/kaspanet/kips/blob/master/kip-0016.md, kip-0017.md, kip-0020.md, kip-0021.md (whitepaper references)
- https://github.com/kaspanet/kccs (KCC-1, KCC-2, KCC-20 references, "Final, 21 October")
- https://github.com/ergoplatform/eips/pull/41, https://github.com/terra-money/classic-core/tree/main/x/oracle/spec, https://github.com/liquity/dev/tree/main/papers/whitepaper, https://github.com/bitcoin/bips/blob/master/bip-0100.mediawiki (prior art references)
- No kaspadollar/KSD repo link. Other non-GitHub external links: x.com/KaspaDollar (X account), kaspa.stream, miningboard.com, dev.risczero.com.
- Probed https://kaspadollar.com/github, /repo, /source: 404. /.well-known/security.txt: 404.

Whitepaper self-description: "A. Säfström is an independent researcher and a core contributor to the Kaspa network" (https://kaspadollar.com/whitepaper, 2026-11-15). Whitepaper contact e-mail on the page: a proton.me address (not reproduced here).

## 3. Searches performed (item 4)

All via https://api.github.com, 2026-11-15, unauthenticated.
- Users, direct lookup `GET /users/<name>`: `kaspadollar` 404, `KaspaDollar` 404, `kaspa-dollar` 404, `kaspadollar-org` 404, `kaspa-ksd` 404. `ksd`/`KSD` return 200 but it is an unrelated personal account (type User, created 2011-08-30, 59 repos) - not a Kaspa project. Web: github.com/kaspadollar, /KaspaDollar, /kaspa-dollar all 404.
- User search `kaspadollar`, `KaspaDollar`, `kaspa-dollar`: total_count 0 each.
- Repo search (`search/repositories`) for `kaspadollar`, `KaspaDollar`: 2 hits, both `STP-KAS/kaspa-builders` and `STP-KAS/kaspa-master-file` (third-party "Kaspa builders / community research" repos created 2026-10-04 and 2026-09-05, description of master-file: "Experimental. Not advice."). These mention the project; they are not project code. Search `kaspa-dollar` / `kaspa dollar`: 126 hits, first ten are unrelated or third-party (e.g. STP-KAS/*, bitrequest/webshop-integration, faymaz/currency-tracker). Search `"kaspa dollar"` quoted: 0. `ksd kaspa`: 4 hits, none the project (STP-KAS/pow-rail, MightyM17/CSI_Task_App_22 etc.).
- Issues/PR search `kaspadollar.com type:pr`: 1 hit: https://github.com/neoalphavault-png/kaspa-pulse/pull/201 (created 2026-10-28, title "KaspaDollar: Spenden gezaehlt zur Stichzeit 28.10. 12:00 UTC, Bericht und Tages-CSV") - a third-party monitor counting donations; not project code. Not examined further (outside scope; relates to fundraising).
- Commit search `kaspadollar`: 0 results. Code search: requires authentication (not possible).
- Founder name searches: user search `safstrom` 20 users (mostly unrelated Swedish names: Safstrom, safstromo, Naiso2022 etc.); user `alexandersafstrom` exists (created 2020-09-14, 1 repo `GymnasieArbete`, a 2020 school project, 0 followers) - no evidence it is the same person; UNVERIFIED and irrelevant to Kaspa. Repo search `safstrom` surfaces kaspanet/kips and kaspanet/kccs.
- The founder's actual handle is identified from the KIP-16 header: "Alexander Safstrom (@saefstroem)" (KIP-16 file, see section 4). `GET /users/saefstroem`: id 139136798, created 2023-07-10, 53 public repos, 18 followers, no org memberships listed. Repos relevant to Kaspa: forks of rusty-kaspa, kips, kccs, silverscript, kaspa-ng; own repos `txcourier` (Ledger transaction courier on RP2350, Rust), `stroemnet` (P2P atomic swap protocol, Rust), `onchain-zkml`, `tinyvault`, `sveltedit`. None is named KSD / kaspadollar / stablecoin. Public events 2026-11-02..04 show pushes to `sveltedit` and `tinyvault` only. The user-repo search `stablecoin user:saefstroem` returned 0. Raw: not saved (small).
- Conclusion: no GitHub org, user, repo, release, CI or license for the project exists under any tested name. Metrics requested (creation date, commits, license, stars, forks, tests, CI) are all "not applicable: no repository".
- Note: I could not search the repository content of private repos; a private repo under the founder's account would not be visible. Whether a private repo exists is UNVERIFIED.

## 4. Founder claims (item 3)

### KIP-16 authorship - CONFIRMED
- File https://github.com/kaspanet/kips/blob/master/kip-0016.md header: "KIP: 16 / Layer: Script Engine, ZK / Title: New Transaction Opcodes for Verifiable Computation / Authors: Alexander Safstrom (@saefstroem) / Status: Active" (accessed 2026-11-15; saved 01-kip16-header.txt).
- History (`commits?path=kip-0016.md`, saved 01-kips-kip16-commits.json): first added by saefstroem 2025-12-07 ("Add kip16", PR #31 opened 2025-12-07 by saefstroem, merged 2026-05-28 by the maintainers' side); pricing change 2025-12-17; edits 2026-05-11 (x2) and 2026-05-13 by saefstroem; status update 2026-05-28 by michaelsutton; "Mark kips 16,17,20,21 as active (#45)" by michaelsutton 2026-07-15.
- The implementation PR https://github.com/kaspanet/rusty-kaspa/pull/775 "KIP-16", author saefstroem, merged 2026-02-05 by michaelsutton (2430 additions, 121 deletions, 56 files).
- Note on wording: the whitepaper cites KIP-16 as 2026 work; Kaspa's own KIP status is "Active", not "Final". The KIP specification defines `OpZkPrecompile` (the site's whitepaper itself says [14]; I did not check which exact opcodes the whitepaper relies on beyond that).

### rusty-kaspa contributions - CONFIRMED but modest
Repo https://github.com/kaspanet/rusty-kaspa (created 2022-07-17, 879 stars, default branch master, about 702 commits on default branch per API pagination).
- Commits by login saefstroem on default branch: 6 (saved 01-rustykaspa-commits-saefstroem.json): 2025-01-06 "CI Update (#622)"; 2026-02-05 "KIP-16 (#775)"; 2026-02-08 "Enable OpTxInputDaaScore (#861)"; 2026-04-19 "Propagate upstream control ID check (#957)"; 2026-04-27 "Use kaspanet workflow-perf-monitor (#965)"; 2026-06-23 "Zk sdk (#953)".
- PR search `author:saefstroem type:pr`: 13 PRs (saved 01-rustykaspa-prs-saefstroem.json): 11 merged/closed-merged between 2023-11 and 2026-06 (README improvements, RPC url path, mimalloc bump, musl builds, CI, KIP-16, OpTxInputDaaScore, control ID check, zk sdk), 1 closed unmerged (#548), 1 open (#1129 "Bump rust 1.98.1", 2026-09-10).
- Contributors endpoint (`/contributors`, 47 entries listed on my pagination, sum of contributions 700): saefstroem has 11 contributions, rank 11 of 47 (top: michaelsutton 190, someone235 135, biryukovmaxim 59, aspect 54, tiram88 42, coderofstuff 40, IzioDev 34, elichai 27, D-Stacks 19, LiveLaughLove13 12; saved 01-rustykaspa-contributors-top.tsv). The contributor count of 11 differs from 6 commits shown by the author filter, probably because of other authored/co-authored or squashed commits; reason UNVERIFIED.
- Assessment: he is a listed contributor with a substantial merged feature (KIP-16 implementation, zk-sdk) and is in the top dozen by count. Whether "core contributor" is justified is a judgment: he is not a repo maintainer by evidence available (merges are done by michaelsutton and others; I did not verify org membership or write access - UNVERIFIED). Most contributions date from 2026; the account was created 2023-07-10.

### KIP-17, KIP-20, KIP-21 (cited as other authors in the whitepaper) - CONFIRMED
(headers saved as 01-kip17/20/21-header.txt; commit lists from `commits?path=...`, 2026-11-15)
- KIP-17 "Covenants and Improved Scripting Capabilities": Authors Ori Newman; Status Active; Updated 2026-05-31; added in PR #32 by someone235 on 2026-06-02. Whitepaper credits "O. Newman": consistent.
- KIP-20 "Covenant IDs": Authors Michael Sutton; Status Active; Updated 2026-05-28; PR #35. Whitepaper credits "M. Sutton": consistent.
- KIP-21 "Partitioned sequencing commitment with O(activity) proving": Authors Michael Sutton, Maxim Biryukov (@biryukovmaxim), Hans Moog; Status Active; Created 2026-02-17; last fix 2026-11-01 (PR #52, "Fix KIP-21 lane inactivity boundary"). Whitepaper credits "M. Sutton, M. Biryukov, H. Moog": consistent. Note the KIP was edited 2 weeks ago, so the spec the whitepaper relies on is still moving.
- All four KIPs (16, 17, 20, 21) were marked "active" together in commit e4ae2332 "Mark kips 16,17,20,21 as active (#45)" by michaelsutton on 2026-07-15. "Active" is the status used; none is labeled Draft or Final. Whether "Active" means activated on Kaspa mainnet or just accepted is UNVERIFIED (not checked against kips README definitions or mainnet hardfork schedule).

### KCC-20 and KCC specs - CONFIRMED location, authorship differs from founder
- Repo: https://github.com/kaspanet/kccs (created 2026-07-15 by michaelsutton, last push 2026-10-21, 13 stars, license "NOASSERTION"). Files: kcc-0000, 0001, 0002, 0020, 0023.
- KCC-20 "Fungible Token Covenant Specification": Authors Sivan Helfer (@Manyfestation), Michael Sutton, Ori Newman, Romain Billot (@IzioDev); Status Final; Created 2026-08-21; Requires KCC-1, KCC-2, KIP-20. The founder is NOT an author of KCC-20. Status moved to Final in commit 9dec4a04 "KCC-20: advance to Final (#41)" by Manyfestation on 2026-10-21 (also KCC-1 #39 and KCC-2 #40 on 2026-10-21). This supports the whitepaper's "Final, 21 October" claim for KCC-1, KCC-2 (and KCC-20).
- The founder authored KCC-0 "KCC Purpose and Guidelines" (a Meta process document, Status Final, created 2026-08-25), merged via #17 on 2026-08-27, and has 4 PRs in kccs (#17, #24 KCC12 still open, #25, #31) and 3 commits (kccs contributors: IzioDev 9, Manyfestation 7, michaelsutton 3, saefstroem 3, someone235 2). He also made PR #31 "KCC0 Compliance for KCC-20 + Last Call advancement" (merged 2026-10-07), i.e. contributed to KCC-20's process, not as an author. (saved 01-kccs-commits.json, 01-kcc20-header.txt)
- Whitepaper reference [15] cites KCC-1 by "R. Billot, M. Sutton, O. Newman" and [16] KCC-2 by "R. Billot and M. Sutton": both match the file headers.
- The whitepaper states "KCC-20 does not define a mint or a burn, so these tokens are to be considered as extended" - I did not verify this against the KCC-20 body text (UNVERIFIED).

## 5. Whitepaper-vs-code comparison (item 2)

Not possible. For the record, the claims that would need code to check, and their status: collateral ratios 250%/200%, 5% penalty, 50,000 KSD / 24h cap, oracle rules (miner vote, median, ZK proof of vote counting), 30-day settlement, redemption vault choice: **no public code, so no verification, no implementation, no tests, no audit report exist for any of them (all UNVERIFIED as implemented behavior).** The only code-adjacent verifiable foundations are the Kaspa-level opcodes (KIP-16 zk precompile, KIP-17 covenants, KIP-20 covenant IDs, KIP-21 sequencing commitment) which are specifications by third parties plus the founder's KIP-16 implementation in rusty-kaspa. The whitepaper's dependency on KIP-21 (partitioned sequencing commitment, `OpChainblockSeqCommit`) and covenants means the system relies on features whose specs are labeled Active but may still be changing (KIP-21 edited 2026-11-01). I did not verify whether these opcodes are live on Kaspa mainnet or testnet only.

## 6. Red flags (facts only)
- No repository of any kind for the project; the /contact page defers it ("Published when the repository is public"). The /docs roadmap schedules an audit for June - August (the following year, presumably; site does not state the year in the text I read - UNVERIFIED which year) while fundraising is already open.
- Authorship claims of KIP-16 and contributions to rusty-kaspa are true; "core contributor" is a stretch if read as maintainer (11 contributions, 6 commits on default branch, merges by others) but is not false in the sense of a recognized contributor.
- The founder's GitHub account is only from 2023-07 with a rapid 2026 activity increase; many forks. No prior track record of shipping a stablecoin or financial protocol visible in his public repos (closest: `stroemnet` atomic swap, `txcourier`, `onchain-zkml`). This is an observation about public repos only.
- Whitepaper contact is a free proton.me address; X account `KaspaDollar` exists (not examined, other agent scope).

## 7. Not verified / could not access
- Any private repos, private org, or code hosted outside GitHub (GitLab etc.): not searched beyond GitHub; no links on site.
- GitHub code search (requires auth) - so mentions of "kaspadollar" inside repo files not enumerated, except via repo/issue/commit search.
- Whether Kaspa mainnet/testnet has activated KIP-16/17/20/21 opcodes.
- Whether saefstroem has write/maintainer rights on kaspanet repos (org membership is not visible unauthenticated).
- Why contributor count (11) differs from author-filtered commits (6).
- Whether the site's JS bundles contain further links (only the HTML was grepped for URLs; the two entry JS files were identified but not downloaded/analysed).
- Wayback/archive history of the site for earlier repo links: not checked.
- Third-party repo STP-KAS/* and neoalphavault-png/kaspa-pulse contents: only metadata read.
- Rate limits: no 403 rate-limit responses were encountered, but the search endpoints return `total_count` approximations.

## Raw evidence files (same folder)
01-kip16-header.txt, 01-kip17-header.txt, 01-kip20-header.txt, 01-kip21-header.txt, 01-kips-kip16-commits.json, 01-rustykaspa-commits-saefstroem.json, 01-rustykaspa-prs-saefstroem.json, 01-rustykaspa-contributors-top.tsv, 01-kccs-commits.json, 01-kcc20-header.txt
