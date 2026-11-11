# R3 Ecosystem facts (research, 2026-11-10). Read-only; nothing in the repo modified.
Tags: VERIFIED = primary page/API read this session; SECONDARY = news/aggregator; UNVERIFIED = single/promotional/unread.

## 1. Token standards
- KCC-0, 1, 2, 20 = Final; KCC-23 (metadata JSON) = Draft. VERIFIED https://github.com/kaspanet/kccs
- KCC-20 "Created: 2026-08-21", "Status: Final" (VERIFIED raw https://raw.githubusercontent.com/kaspanet/kccs/main/kcc-0020.md). Finalisation announced ~2026-10-21 (SECONDARY https://crypto.news/kaspa-finalizes-kcc-native-token-app-standards/).
- Mint/burn/supply/controller: the spec defines NONE. No mint or burn entrypoint, no total-supply field, no minter/controller. Only: "The leader MUST preserve the total token amount across the KCC-20" (transfer conservation). `owner` is as defined by KCC-2. Fungibility: states fungible only if `extension_commitment` identical. VERIFIED (fetch summarised by a small model; quotes not re-read in full file).
- Security text: borrowed receive can spend a UTXO without owner authorisation and change its outpoint; "extended state ... enforced only by covenant-specific entrypoints". VERIFIED (same).
- Open issues: kccs #14 "updating extended state conflicts with the consolidation rule" (Knitser, 7 comments, michaelsutton replied 2026-08-21); #28 "four programs share one name and not one ABI" (STP-KAS, 2026-09-20). VERIFIED GitHub API.
- Open kccs PRs (none mint/burn/oracle specific): #38 KCC3 HD wallets, #37 P2PKH via P2SH, #36 Covenant v2 draft, #29 reputation/bond/identity registry, #24 KCC12 (57 comments), #4 payment channels. VERIFIED.
- Implication: issuance/supply/controller binding for kFIAT/ENRK is NOT given by KCC-20; must be covenant-specific logic (repo's earlier "known supply-split defect" claim on KCC-0020 is not in the Final text I saw; the Final text simply has no mint/burn). Repo wording should be rechecked.
- KRC-20 (Kasplex, inscription/L2-indexer based) is a different, non-covenant model: SECONDARY https://wiki.kaspa.org/en/Kasplex_KRC_20. Not read in depth.

## 2. L1 covenant ecosystem
- Toccata active on mainnet 2026-06-30, DAA 474,165,565; node rusty-kaspa >= v2.0.1. VERIFIED https://docs.kaspa.org/toccata . NOTE repo doc says "June 5-20": inconsistent with primary; fix.
- Mainnet covenant activity: tens/day first 3 weeks, then low-high thousands/day (peak 9,837 on Aug 1); covenant UTXO set 1,411 -> 2,401 in Aug. SECONDARY https://buttondown.com/kaspalytics/archive/issue-1-toccata-live-covenant-usage-a-block/ . That source: no mature apps, audited contracts, broad wallet support.
- Silverscript: v1-rc1 2026-08-30, v1.0.0 2026-09-09 VERIFIED (GitHub API). Argent: no release/tag (SECONDARY https://kaspaexplained.com ; Argent starter "not yet release-ready").
- Announced/related, none confirmed live as covenant stablecoin/DEX/lending/oracle: 
  - KaspaDollar (Saefstroem), over-collateralised stablecoin plan, raising 5M KAS, deadline 2027-01-01; ~104k KAS raised at time of article. SECONDARY https://cryptoast.fr/kaspa-kas-kaspadollar-stablecoin-decentralise-collecte/ . A "design published 3 Nov 2026 with PoW miner oracle" claim is UNVERIFIED (one aggregator). Direct competitor/overlap with ENRK: worth reading primary.
  - Covex (THTProtocol): TN12 covenant explorer with reference oracle (pubkey-registered, timeout refund). SECONDARY https://github.com/THTProtocol/Covex
  - Order-book DEX rebuilt in Silverscript/Argent: UNVERIFIED (search snippet only).
  - Kaskad lending: Igra EVM (not L1), mainnet 24 May. SECONDARY.
  - Kaspero Labs attack-simulation tool for Silverscript (2026-11-02): UNVERIFIED.
- Testnet-10 activity: atomic swap / escrow research demos, "unaudited"; chess wager claim UNVERIFIED. No TN10 oracle found. TN12 vault demo lab exists (https://parker2017code.github.io/tn12-covenant-vault-demo/lab.html, SECONDARY).
- KEF: founding announcement mentions research grants for smart-contract dev; no grant programme specifically for audits/covenants found. SECONDARY/UNVERIFIED. No KEF-funded covenant audit found.

## 3. Igra (EVM based rollup)
- Mainnet public 2026-03-19; "based rollup": txs included on L1 and sequenced by Kaspa consensus, no dedicated sequencer. SECONDARY press (cryptopotato) + VERIFIED attesting doc https://igra-labs.gitbook.io/igralabs-docs/for-developers/architecture/specifications/igra-attesting-protocol : attesters (stake IGRA, min 400k, ~6 month lock, Phase 0 temporary) are not sequencers; "protocol remains fully operational without attesters"; light-node security ~ attester stake. => repo's "Architecture/Attesting pages could not be loaded" gap is now closable: attesters affect light nodes, not user withdrawals (doc silent on user withdrawals).
- KasExitBridge limits CHANGED vs repo (VERIFIED https://igra-labs.gitbook.io/igralabs-docs/for-developers/kasexitbridge-developer-guide.md , read at block 19,157,082 dated 2026-10-13): min 10,000 KAS; max 250,000 KAS/exit; max 25 exits and 1,000,000 KAS per 86,400-block window (global); fee 0; owned by Governance contract; params DAO-changeable; Kaspa-side release actors not identified; Hyperlane dispatch. Repo claims (1,000-50,000 KAS; 20 exits / 200,000 KAS per ~25h) are stale: 5x higher cap. Redo 3.3: 102.7M KAS / 1M/day ~ 103 days if window is ~1 day (86,400 blocks at Igra block time: window length in wall-clock UNVERIFIED).
- Community Guardians bridge page (https://ikas.katbridge.com/): 48-72h, no SLA, manual multisig, signers/threshold unpublished; deposit 10-5,000 KAS; page showed withdrawals "temporarily paused by the protocol" when fetched. VERIFIED.
- Audit: Sigma Prime on Igra contracts, SECONDARY only.
- KAT Bridge repo claims (3-of-5, 4 audits): not rechecked.

## 4. Auditors / reports
- No published audit report for any Kaspa covenant found. Silverscript: no completed audit stated (SECONDARY buttondown); repo has SECURITY.md and UNDEFINED-BEHAVIOUR.md (contents unread). No named auditor with Silverscript experience identified. UNKNOWN.

## 5. Tooling
- No node RPC lists UTXOs by covenant ID; apps need own block-scanning indexer; satellite index + 2 RPC methods discussed 2026-08-04, not a numbered proposal. SECONDARY (buttondown).
- kascov.io: public covenant explorer/indexer by covenant ID, mainnet + testnet-10, JSON API no key, SSE, webhooks, OpenAPI. VERIFIED https://kascov.io/llms.txt (third-party, retention beyond node pruning ~30h claimed; trust/uptime unknown).
- TN10 faucet/explorer listed at https://wiki.kaspa.org/en/testnets (SECONDARY; URL not tested). Wallet covenant-transaction support (Kasware, Kaspium, KaspaNG): UNKNOWN. Argent runtime: source-only, no release.

## 6. Governance / core-dev channels (kaspanet/kips #46)
- VERIFIED via fetch and GitHub API (2026-11-10): state OPEN, 2 comments, both by cyprox (2026-09-06), author_association NONE; last update 2026-09-06. NO reply from any core dev; no reaction in thread since Sept 2026.
- Adjacent activity: kips #47 (Curious-being99, concept of covenant w/ examples), #48 KIP-22 P2PKH via P2SH (someone235), #49 KIP-20 CovenantIDHash keying + test vector (Silentpartnercoding, open), #52 KIP-21 fix (michaelsutton, closed 11-01). Core devs (Sutton) active on KIPs and replied on kccs #14, so engagement exists elsewhere; #46 simply unanswered after ~2 months.
- Other channels: Kaspa Discord (#testnet), kccs repo issues/PRs. Direct contact path to Sutton/Newman/Billot unknown; consider a PR on kccs or a comment on kips #49 (KIP-20 covenant ID work) to reach reviewers. (suggestion, not a fact)

## Remains unknown
KIP-20 sibling-ID reading endorsed? Block inclusion of N~640 txs on TN10; Igra window wall-clock length and release-actor identity; any covenant-capable auditor; wallet support; KEF audit funding; status of KaspaDollar design vs ENRK; whether Final KCC-20 has later revisions beyond c0bb8f3-era main.
