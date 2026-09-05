# Execution Target Assessment — Kaspa L1 vs Igra EVM

**Date:** September 3, 2026
**Status:** Findings for decision. No implementation implied.
**Question:** Where can ENRK deploy, and can collateral be held in a trust-minimised way?

**Verdict in one line:** neither layer can currently carry this protocol. Kaspa L1
cannot express a shared price oracle; Igra cannot move collateral in or out fast
enough or safely enough to back a stablecoin of meaningful size.

---

## 1. What Kaspa L1 gained with Toccata

The covenant hardfork activated on mainnet around **June 5–20, 2026** (feature
freeze April 15). It shipped:

| KIP | What it adds |
|-----|--------------|
| KIP-10 | Transaction introspection — reading fields of the *current* spending transaction |
| KIP-17 | Extended script-engine opcodes — the covenant backbone |
| KIP-20 | Covenant IDs for lineage management — lets a contract keep identity across state transitions |
| KIP-16 | ZK opcodes with verifier precompile |
| KIP-21 | Partitioned sequencing commitment architecture |

Plus **native L1 assets** and **SilverScript**, a high-level language compiling to
native Kaspa Script.

## 2. The blocker, confirmed from the KIP text itself

**KIP-10:** *"There are no opcodes to read unspent UTXOs without spending them.
The introspection capabilities are limited to examining and validating transaction
properties of the current transaction being validated."*

**KIP-17:** no mention of reading other UTXOs without spending them. The system
introspects only the current transaction and the inputs being spent.

A technical explainer citing the KIPs directly puts it plainly: *"A covenant can
only inspect its own spending transaction; no KIP gives it a shared-state read."*
And on oracles: *"A proof checks only the signature. Kaspa's L1 has none."*

ENRK's peg requires a shared price oracle read concurrently by many transactions.
**It is not expressible on Kaspa L1 today.** This is not difficulty — it is
absence of the primitive.

SilverScript independently confirms the same boundary: not Turing-complete, no
global mutable state, explicitly positioned as complementary to **vProgs**, which
are the designated shared-state path. vProgs were at RESEARCH stage in April 2026,
are not part of Toccata, and Michael Sutton's own roadmap gist shows **zero
releases, zero tags**.

**Option "Kaspa L1 native" is closed.**

## 3. Igra has two exit paths. Neither is trustless.

### 3.1 Community Guardians bridge (the official one)

From the bridge page itself: *"KAS is released on Kaspa by Igra's Community
Guardians (manual multi-sig)."*

- **manual multi-signature**, signers not named, threshold not published
- **48–72 hours**, with *"no guaranteed timeline or SLA"*
- **min 10 KAS, max 5,000 KAS per transaction**
- iKAS is burned immediately on signing; irreversible
- no audit report published

### 3.2 KasExitBridge (documented in Igra's own developer docs)

- burn-and-release: user calls `requestExit()`, the event is dispatched through
  **Hyperlane** (a third-party interoperability protocol), and **off-chain
  "Kaspa-side release actors"** observe it and unlock KAS on L1
- explicitly **not** covenant-verified and **not** protocol-verified
- **min 1,000 KAS / max 50,000 KAS per exit**
- **throttled to 20 exits or 200,000 KAS per ~25-hour window**
- the contract is being transferred to a **Governance contract**; future parameter
  changes will require governance proposals
- v1 performs **no bech32 checksum validation** — a funds-loss risk flagged in
  Igra's own documentation

No protocol-enforced or covenant-verified forced-withdrawal escape hatch exists in
any Igra documentation reviewed. Igra's "Architecture" and "Attesting Protocol"
pages could not be loaded, so a future attester security role cannot be ruled out.

### 3.3 What the throttle does to this protocol

The stress-test population holds roughly **102,700,000 KAS** of collateral.

```
102,700,000 KAS / 200,000 KAS per ~25h  ≈  513 days to unwind
```

In a crisis, the exit is throttled to about **0.2% of the collateral base per day**.

This compounds the failure the model already found. `stress_test_crash.py` showed
the protocol does not explode under stress — it **freezes**, because liquidations
stop clearing for lack of liquidator capital. Capital that cannot enter or leave
in under 48–72 hours, capped at 200,000 KAS/day network-wide, will not arrive to
rescue auctions that run for 120 minutes.

Inverted, the same number caps the protocol's viable size:

| Full unwind within | Maximum total collateral |
|---|---|
| 30 days | ~6,000,000 KAS |
| 90 days | ~18,000,000 KAS |
| 365 days | ~73,000,000 KAS |

(The Community Guardians path has no published aggregate daily limit, only a
5,000 KAS per-transaction cap and manual human processing. Total system capacity
is therefore not publicly specified, but both paths are hard-capped per
transaction and depend on off-chain human action.)

**Igra's current exit capacity cannot support a stablecoin of meaningful size.**

## 4. Kasplex is not currently better

Kasplex's Asset Bridge is documented as using **"multi-sig and ZKP verification"** —
a hybrid, with an acknowledged multisig component. The **ZK Prover page in
Kasplex's own documentation is marked "currently in progress"**, so the component
that would make withdrawal trustless is not documented as live.

## 5. The genuine future path

**KIP-16** adds ZK opcodes with a verifier precompile, and its stated motivation is
explicitly *"trustless asset movement between layers or other blockchains"*. A
covenant that gates a spend on a verified ZK proof **is** a trustless bridge.

This is the right primitive. But it is a building block, not a bridge. Sutton's
roadmap places the **native asset canonical bridge at Milestone 4**, deferred
pending a Native Assets & ICC proof of concept.

Two further cautions on the L1 asset track:

- **KCC-0020**, the fungible-token standard for native L1 assets, is a draft with a
  **known supply-split defect**. Not a foundation for immutable money.
- No documented pattern exists for an L1-native asset whose issuance policy is
  enforced by L2 logic or an external proof.

## 6. Atomic swaps: constructible, never built

Kaspa's script engine already contains HTLC primitives — `OpCheckLockTimeVerify`
(176), `OpCheckSequenceVerify` (177), `OpSHA256` (168), `OpBlake2b` (170). These
**predate Toccata**; they are part of the Bitcoin-derived base script. KIP-10 and
KIP-17 add introspection, not new locking primitives.

But no working, technically documented atomic-swap implementation was found — only
one promotional social-media claim with no repository or writeup. `rusty-kaspa`'s
`standard.rs` defines only P2PK/P2SH templates, no HTLC template.

Atomic swaps are permissionless and inherently L2-agnostic, which makes them
attractive: they need no upgradeable registry of supported chains. But building
one as a dependency of immutable code, with no prior art, is a research project.

## 7. Component-by-component

| Component | Kaspa L1 native | Notes |
|---|---|---|
| Vault (collateral custody) | **Yes** | A UTXO with spending conditions is the advertised covenant use case |
| Dutch auction | **Probably** | Local to one vault; price descent is a function of time |
| ENRK / kFIAT as tokens | **Qualified yes** | Native assets shipped, but KCC-0020 has a known defect |
| kFIAT 30% cap | **Plausible by redesign** | Via conservation of quota tokens rather than reading a counter |
| Stability Pool | **No** | Shared mutable balance |
| Recovery Mode | **No** | Requires system-wide aggregate ICR |
| Oracle / peg feed | **No — gating** | No reference-input equivalent. Confirmed from KIP text |

## 8. The three remaining paths

**Path 1 — Deploy on Igra, bounded and disclosed.**
Freeze a maximum total collateral constant sized to what the exit path can unwind,
and publish the reasoning: *"this protocol is capped at X KAS because the layer it
lives on can move Y per day."* This does not pretend the bridge is safe; it sizes
the protocol so the bridge cannot become a trap, converting an unbounded hidden
risk into a bounded disclosed one. Fork to v2 with a higher cap when KIP-16
delivers a trustless bridge.
*Cost:* confines the protocol to roughly 6–18M KAS. Collateral still sits behind a
multisig and off-chain actors for as long as it is deployed.

**Path 2 — Finish the design, deploy when the infrastructure opens.**
Complete the specification, the Solidity implementation, the economic audit and the
stress testing now, while KIP-16 bridges and vProgs mature. Deploy the day one of
the two doors opens.
*Cost:* no launch date. Depends on third-party roadmaps.

**Path 3 — Investigate KAT Bridge first.**
The one unexamined option. Its operator and security model could not be determined
from public web content; it requires reading the contract directly.
*Cost:* a delay, but a short one, and it closes the last open question.

## 9. What remains unknown

- **KAT Bridge**: operator, custody model, security. Not determinable from public
  pages; needs direct contract inspection.
- Igra's "Architecture" and "Attesting Protocol" pages could not be loaded — a
  future attester security role cannot be ruled out.
- Kaspa L1 UTXO contention under concurrent load: no public measurement found.
  Less decisive now that §2 closes the L1 path regardless.

---

## Sources

- [KIP-10 — transaction introspection](https://github.com/kaspanet/kips/blob/master/kip-0010.md)
- [KIP-16 — ZK opcodes and verifier precompile](https://github.com/kaspanet/kips/blob/master/kip-0016.md)
- [KIP-17 — covenants](https://github.com/kaspanet/kips/blob/master/kip-0017.md)
- [KIP-20 — covenant IDs](https://github.com/kaspanet/kips/blob/master/kip-0020.md)
- [Michael Sutton — Covenants++ "Toccata" hard-fork outlook](https://medium.com/@michaelsuttonil/kaspa-covenants-toccata-hard-fork-outlook-a4d81a40900c)
- [Michael Sutton — vProgs roadmap gist](https://gist.github.com/michaelsutton/5bd9ab358f692ee4f54ce2842a0815d1)
- [Kaspa WASM32 SDK — opcode reference](https://kaspa.aspectron.org/docs/enums/Opcodes.html)
- [Igra — KasExitBridge developer guide](https://igra-labs.gitbook.io/igralabs-docs/for-developers/kasexitbridge-developer-guide.md)
- [Igra bridge — Community Guardians multisig](https://ikas.katbridge.com/)
- [Kasplex — bridge documentation](https://docs-kasplex.gitbook.io/l2-network/kasplex-network/bridge.md)
- [Hail the SilverScript — Kas Magazine](https://kasmagazine.com/article/hail-the-silverscript)
- [Kaskad — lending on Kaspa, running on Igra EVM in Solidity](https://www.kaskad.app/)
- [KRON — DEX on native L1](https://kron.technology/)
