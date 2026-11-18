# contracts/

## What this directory is

`contracts/igra/` is a Rust crate (`enrk-igra`, 11 modules under `contracts/igra/src/`) written for the Igra / EVM path.

**Owner decision of 2026-11-13: the execution layer is Kaspa L1 and Igra is NOT retained.** See `PROJECT-STATE.md` (line 15 and the "Open" section). The crate is kept as a reference (an executable specification) and is not the implementation target. It does not deploy (`README.md`, "What is not claimed"). No code here has been audited.

## Where the L1 work lives

- Design: `docs/design/L1_NATIVE_REDUCED_SPEC.md`; status and open questions: `PROJECT-STATE.md`.
- Argent sources (oracle and vault, variants A and B): `examples/enrk/a/` and `examples/enrk/b/` (`oracle.ag`, `vault.ag`), plus `examples/enrk/probe_const_covid.ag`.
- Measurement harness: `tests/enrk_mass.rs`. It needs a checkout of the Argent repository to compile, and the committed copy still fails at N = 2 (line 90-92 binds every output to input 0); see `docs/design/REMEASUREMENT-2026-09-15.md` section 5.1 and section 8.
- Method and results: `docs/design/GITHUB-ISSUE-46-UPDATE.md`, `docs/design/REMEASUREMENT-2026-09-15.md`.

## Known differences between this crate and `docs/design/FROZEN_PARAMETERS.md`

- Auction floor: 85 in `igra/src/types.rs:80,106` and `igra/src/lib.rs:68`; the frozen document says 75% (section 4, line 90).
- Fee split: permanent 80/20 in `igra/src/lib.rs:70-71` and `igra/src/types.rs:120,142`, with no 2,500,000 treasury cap anywhere in the crate; the frozen document says 20% until the cap, then 0% (section 6).
- Fee denomination: the fee is added to vault debt (`igra/src/vault.rs:136,139,217`) and collected nowhere; the frozen document says KAS taken from vault collateral (section 6).
- Withdrawal ratio: `withdraw_collateral` checks the 150% MCR (`igra/src/vault.rs:361`); the Argent vaults require 200% (`examples/enrk/a/vault.ag:59`, `examples/enrk/b/vault.ag:59`). No document states which one is frozen.

## Status of fixes

Changes to this code await the owner's decision. See `docs/design/AUDIT-2026-11-09.md`, items B2, B3, I8-I13, I23 and I26.
