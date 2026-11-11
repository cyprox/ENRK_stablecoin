#!/usr/bin/env python3
"""
ENRK crash stress test — "the darkest possible future"

Models the full protocol under a severe KAS drawdown, not just the peg formula:
a population of vaults, peg computation from four indices, ICR collapse,
Dutch-auction liquidation with realistic bidder scarcity, the ENRK/kFIAT
seniority waterfall, and the reflexive loop where liquidated collateral is
dumped on the market and pushes KAS lower still.

The question it answers: in a deep crypto crash, does the 30% kFIAT buffer plus
200% over-collateralisation protect ENRK holders — or is an uncorrelated reserve
actually required?

Standard library only. Deterministic (fixed seed).

Usage:
    python3 stress_test_crash.py
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

SEED = 20260903

# ----------------------------------------------------------------------------
# Protocol parameters (frozen constants from contracts/igra/src/lib.rs)
# ----------------------------------------------------------------------------

MCR_TRIGGER = 1.50           # liquidation threshold
KFIAT_MAX_SHARE = 0.30       # junior tranche cap, at mint
AUCTION_START_PRICE = 1.00   # Dutch auction opens at market price
AUCTION_END_PRICE = 0.85     # ...and floors at a 15% discount
LIQUIDATION_FEE = 0.04

PEG_FLOOR, PEG_CEIL = 0.1, 5.0   # clipping applied in peg.rs


# ----------------------------------------------------------------------------
# Peg formulas
# ----------------------------------------------------------------------------

@dataclass(frozen=True)
class PegFormula:
    """Weights on (hashrate, energy, fees, adoption). Must sum to 1.0."""
    name: str
    hashrate: float
    energy: float
    fees: float
    adoption: float

    def __post_init__(self) -> None:
        total = self.hashrate + self.energy + self.fees + self.adoption
        assert abs(total - 1.0) < 1e-9, f"{self.name}: weights sum to {total}"

    def value(self, h: float, e: float, f: float, a: float) -> float:
        raw = self.hashrate * h + self.energy * e + self.fees * f + self.adoption * a
        return min(max(raw, PEG_FLOOR), PEG_CEIL)


# The deployed choice: 30% uncorrelated global energy hedge.
FORMULA_35 = PegFormula("Alt 3.5 (deployed)", 0.40, 0.30, 0.20, 0.10)

# The rejected alternative: pure Kaspa indexing. The 30% energy weight is
# reassigned to hashrate, so the peg tracks the network — and the collateral.
FORMULA_ALT3 = PegFormula("Alt 3 (pure Kaspa)", 0.70, 0.00, 0.20, 0.10)


# ----------------------------------------------------------------------------
# Index response model
# ----------------------------------------------------------------------------

@dataclass(frozen=True)
class IndexResponse:
    """
    How each peg index responds to a KAS price ratio r (r = price / price_0).

    Each index moves as r ** elasticity:
      elasticity 0.0 -> fully uncorrelated (flat)
      elasticity 1.0 -> moves one-for-one with price

    hashrate 0.40: miners capitulate, but difficulty adjusts and efficient rigs
      survive. Bitcoin 2018 and 2022 both saw ~-40% hashrate against ~-80% price,
      which is close to r**0.4.
    fees 0.60: on-chain activity falls hard but not to zero.
    adoption 0.30: adoption metrics are sticky; users leave slowly.
    """
    hashrate_elasticity: float = 0.40
    fees_elasticity: float = 0.60
    adoption_elasticity: float = 0.30
    energy_multiplier: float = 1.00   # exogenous; 1.0 = flat through the crash

    def indices(self, price_ratio: float) -> tuple[float, float, float, float]:
        r = max(price_ratio, 1e-6)
        h = r ** self.hashrate_elasticity
        f = r ** self.fees_elasticity
        a = r ** self.adoption_elasticity
        e = self.energy_multiplier
        clip = lambda x: min(max(x, PEG_FLOOR), PEG_CEIL)
        return clip(h), clip(e), clip(f), clip(a)


# ----------------------------------------------------------------------------
# Vault population
# ----------------------------------------------------------------------------

@dataclass
class Vault:
    collateral_kas: float
    debt_enrk: float     # senior, denominated in peg units
    debt_kfiat: float    # junior
    alive: bool = True
    in_auction_since: int | None = None
    stuck_since: int | None = None     # ECON-V1: first day an auction on this vault failed (C1 floor schedule)

    def total_debt_units(self) -> float:
        return self.debt_enrk + self.debt_kfiat

    def icr(self, kas_price: float, peg: float) -> float:
        debt_value = self.total_debt_units() * peg
        if debt_value <= 0:
            return math.inf
        return (self.collateral_kas * kas_price) / debt_value


def build_population(
    n: int,
    kas_price_0: float,
    peg_0: float,
    target_icr: float,
    icr_spread: float,
    kfiat_share: float,
    mcr_trigger: float,
    rng: random.Random,
    size_scale: float = 1.0,
) -> list[Vault]:
    """
    Vault sizes are log-normal (a few whales, a long tail of small positions).

    Opening ICR is drawn from a lognormal centred on target_icr: nobody opens
    exactly at the minimum, but the distribution is tight against it, because
    capital efficiency is what borrowers optimise for.
    """
    vaults: list[Vault] = []
    for _ in range(n):
        size_kas = rng.lognormvariate(mu=math.log(50_000), sigma=1.2) * size_scale   # ECON-V1: size_scale (debt ceiling sweep)
        icr = target_icr * rng.lognormvariate(mu=0.0, sigma=icr_spread)
        icr = max(icr, mcr_trigger * 1.02)   # nobody opens already liquidatable

        collateral_value = size_kas * kas_price_0
        total_debt_units = collateral_value / (icr * peg_0)

        vaults.append(Vault(
            collateral_kas=size_kas,
            debt_enrk=total_debt_units * (1.0 - kfiat_share),
            debt_kfiat=total_debt_units * kfiat_share,
        ))
    return vaults


# ----------------------------------------------------------------------------
# Scenario
# ----------------------------------------------------------------------------

@dataclass
class Scenario:
    name: str
    total_drawdown: float        # e.g. 0.85 for -85%
    crash_days: int = 60
    formula: PegFormula = FORMULA_35
    response: IndexResponse = field(default_factory=IndexResponse)
    target_icr: float = 2.00
    icr_spread: float = 0.22
    kfiat_share: float = KFIAT_MAX_SHARE
    n_vaults: int = 1000
    seed: int = SEED

    # --- Parameters under study -------------------------------------------
    # Defaults reproduce the original run exactly.
    mcr_trigger: float = MCR_TRIGGER
    auction_end_price: float = AUCTION_END_PRICE

    # Recovery Mode (Liquity-style). Available on Igra EVM; NOT expressible on
    # Kaspa L1, which has no way to read system-wide aggregate state. Set
    # recovery_threshold to enable: when the whole system's collateral ratio
    # falls below it, the effective MCR rises to recovery_mcr, forcing
    # deleveraging while market depth still exists.
    recovery_threshold: float | None = None
    recovery_mcr: float = 2.00

    # Redemption -- equilibrium mechanism #1, and the one never implemented.
    # An ENRK holder burns R and receives collateral worth R * peg at face
    # value, taken from the LOWEST-ICR vaults first (Liquity's choice: it pays
    # down the worst debt and improves system health).
    #
    # Its structural limit: with `a` the collateral value and `b` the debt
    # value, redeeming `r` gives a new ratio (a-r)/(b-r). That IMPROVES a
    # healthy vault (a > b) and DEGRADES an underwater one. Face value simply
    # cannot be paid once the collateral is not there, hence redemption_min_icr.
    #
    # Unlike liquidation, redemption needs no liquidator capital -- the redeemer
    # already holds the ENRK. That is why it may work precisely when auctions
    # freeze, and why omitting it may have made the freeze finding pessimistic.
    enable_redemption: bool = False
    redemption_base_rate: float = 0.002       # of ENRK supply per day, calm
    redemption_stress_sensitivity: float = 0.05   # rises with drawdown
    redemption_min_icr: float = 1.00          # cannot redeem below this
    redemption_fee: float = 0.01

    # Market microstructure
    daily_volume_kas: float = 40_000_000.0
    # Square-root impact coefficient: dumping one full day of volume in a day
    # moves price by this fraction. 0.08 is roughly one daily volatility unit
    # for crypto under stress. Empirical impact laws put a full-volume order
    # at ~1 sigma; a crash is exactly when depth evaporates, so this is the
    # single most load-bearing assumption in the model.
    impact_coefficient: float = 0.08
    # Liquidators demand a bigger discount as stress rises. Required discount
    # = base + stress_sensitivity * drawdown_so_far. The auction can only ever
    # offer 15%, so beyond a point NOTHING clears.
    base_required_discount: float = 0.04
    stress_sensitivity: float = 0.18
    auction_days: int = 1        # 120 minutes, so it resolves within the day

    # Gap risk. A smooth decline lets every vault be liquidated while its
    # collateral still covers its debt, which makes any CDP system look safe.
    # Real crashes gap: on 2020-03-12 ETH fell ~50% in a day and Maker vaults
    # went from healthy to deeply insolvent between price updates, never
    # passing through a zone where liquidation could recover the debt.
    # 4% of days carry a -25% jump: roughly one Black-Thursday-class move
    # per 60-day crash window.
    jump_probability: float = 0.04
    jump_size: float = 0.25

    # Liquidator capital constraint, as a fraction of opening total debt that
    # can be absorbed per day. Liquidators must fund bids with real capital,
    # and in a crash their capital is already committed elsewhere. This — not
    # the auction curve — is the binding constraint in a mass-liquidation
    # event, and it is what actually broke on Black Thursday. Vaults that do
    # not fit in today's capacity keep sinking while they wait.
    daily_liquidation_capacity: float = 0.05

    # --- ECON-M2 extension (all default OFF: defaults reproduce the original) ---
    # Recurring stability fee, annual rate on debt value (peg units), paid in KAS
    # out of the vault collateral each day. Charged only on vaults not in auction
    # unless fee_in_auction.
    stability_fee: float = 0.0
    fee_in_auction: bool = False
    # Pre-crash period of normal operation (flat KAS price, no exogenous jumps,
    # no rng use). Redemption and market impact are OFF in it (assumptions).
    pre_days: int = 0
    pre_redemption: bool = False
    pre_impact: bool = False
    # Junior ledger. dist_rule D1|D2|D3, surplus_rule S1|S2|S3 (see Ledger).
    junior_ledger: bool = False
    dist_rule: str = "D1"
    surplus_rule: str = "S1"
    treasury_share: float = 0.20      # D2: share to treasury until cap (assumption)
    treasury_cap: float = 0.05        # D2 cap, fraction of opening debt value (assumption)
    reserve_absorbs: bool = True      # reserve/treasury counts as collateral in the waterfall

    # --- ECON-T3 extension: peg-index dynamics (all default OFF = original) ---
    # index_mode: "orig" = original elastic IndexResponse (peg falls with KAS as r**elasticity);
    #   "flat" = I == 1 for ever (the literal "flat index" KAS-only crash);
    #   "proc" = stochastic process (see IndexState); "det" = deterministic log-linear ramp to idx_target
    #   by the last crash day.  Debt value = units * I everywhere (ICR, redemption, auction, ledger, latent hole).
    index_mode: str = "orig"
    idx_vol: float = 0.22            # annual vol of the diffusion part
    idx_rho: float = 0.0             # corr(index return, lagged KAS return)
    idx_lag: int = 14                # days KAS leads the index (1-3 weeks)
    idx_shrink: float = 0.5          # shrink of the regression beta (a4 s4.4 convention)
    idx_jumps: bool = True           # energy jumps overlay
    idx_jump_pm: float = 0.08        # monthly P(|energy move| > 15%)
    idx_target: float = 1.0          # det: terminal multiplier at the last crash day
    idx_in_pre: bool = False         # process also runs in the calm pre-year (needs a full run, no cache)
    kas_daily_sd: float = 0.049      # a4: KAS daily sd, used only for the regression beta
    # Circuit breaker (circuit_breaker.rs: trunc(|I-1|*100) > 10 -> trips, i.e. |I-1| >= 11%).
    #   "none"      never called (as in the code base, AUDIT I12)
    #   "mb"        wired to I; pauses mint/burn = redemption; LATCHED ("until manual resolution"); liquidations continue
    #   "liq_latch" as "mb" but liquidations halt too while paused (latched until the end of the horizon)
    #   "liq_live"  as "liq_latch" but un-latched: paused only on days with |I-1| >= 11%
    breaker: str = "none"
    capacity_mode: str = "units"     # "units" (original) | "value" (liquidator capital in USD: units capacity = cap*D0*I0/I) | "adv"

    # --- ECON-V1 extension (all default OFF = ECON-T3 behaviour) ---
    # surplus rule "SP": phi_j of each day's auction surplus -> junior income, phi_r -> reserve (as ECON-T1)
    phi_j: float = 0.0
    phi_r: float = 0.0
    # system size multiplier on every vault's collateral (debt ceiling sweep); rng draws unchanged (paired)
    size_scale: float = 1.0
    # capacity_mode "adv": liquidator capital per day = adv_frac * daily_volume_kas * kas_price_t / peg_t  (USD-valued, shrinks with price)
    adv_frac: float = 0.01
    # convex impact: impact = k*sqrt(p) + conv_beta*max(p - conv_p0, 0), p = KAS dumped / daily_volume_kas
    convex_impact: bool = False
    conv_p0: float = 0.09
    conv_beta: float = 3.4
    # P4 loss rule: "waterfall" | "borrowers_first" | "kfiat_then_borrowers"; soc_cap as a fraction of OPENING debt units
    # (cumulative gross pushed, fixed basis) when soc_basis == "opening"; soc_basis == "legacy" reproduces p3's flawed basis
    # (cap * surviving debt now - cumulative pushed).  soc_cap None = uncapped.
    policy: str = "waterfall"
    soc_cap: float | None = None
    soc_basis: str = "opening"
    # P14 C1: floor deepens by c1_step every c1_days days a vault has been stuck, down to c1_min; bidder_greed g: on a
    # deepened floor the fill discount = required + g*(deepened offered - required)  (g=0 cooperative, 1 = floor always taken)
    c1_days: int = 0
    c1_step: float = 0.05
    c1_min: float = 0.50
    bidder_greed: float = 0.0
    # P14 C2: vaults under min ICR (total ICR < redemption_min_icr) can be redeemed against at min(face, collateral) (pro rata)
    subpar_redemption: bool = False


@dataclass
class Result:
    scenario: str
    formula: str
    final_kas_ratio: float
    final_peg: float
    mean_icr_start: float
    mean_icr_end: float
    vaults_liquidated: int
    vaults_total: int
    auctions_expired: int
    auctions_filled: int
    debt_units_start: float
    kfiat_written_off: float
    enrk_written_off: float
    enrk_loss_pct: float
    kfiat_loss_pct: float
    # Vaults still open at the end whose collateral no longer covers their debt.
    # Not yet a realised loss, but the tokens are already circulating unbacked.
    stranded_vaults: int
    stranded_hole_pct: float
    # Value transferred from vault owners to liquidators via the auction
    # discount, as a percentage of opening debt. This is the price of
    # protection, and it is paid in calm conditions too.
    discount_cost_pct: float
    recovery_days: int
    redeemed_pct: float          # ENRK redeemed, % of opening ENRK debt
    redemption_blocked_pct: float  # demand that found no eligible vault
    # --- ECON-M2 extension ---
    liquidated_pre: int = 0
    fee_paid_pct: float = 0.0        # fee value paid, % of opening debt (all periods)
    fee_paid_pre_pct: float = 0.0
    surplus_pct: float = 0.0         # auction surplus (beyond debt), % of opening debt
    surplus_pre_pct: float = 0.0
    junior_inc_pre_pct: float = 0.0  # junior income at receipt, % of junior face, end of pre period
    junior_inc_pct: float = 0.0      # same, end of crash
    junior_hold_pct: float = 0.0     # KAS income marked at END price (held, not sold)
    reserve_end_pct: float = 0.0     # reserve+treasury value at end, % opening debt
    reserve_used_pct: float = 0.0    # reserve value consumed by shortfalls, % opening debt
    # --- ECON-T3 extension ---
    unbacked_usd_pct: float = 0.0    # (write-offs valued at I of the write-off day + latent hole at end I) / opening debt VALUE
    unbacked_units_pct: float = 0.0  # same in peg units / opening units
    breaker_days: int = 0
    peg_max: float = 1.0
    peg_min: float = 1.0
    # --- ECON-V1 ---
    freeze_days: int = 0            # crash days ending with >= 1 alive vault under water (collateral value < debt value)
    latent_max_pct: float = 0.0     # peak (over crash days) of the under-water hole, % opening debt units
    pushed_pct: float = 0.0         # cumulative gross shortfall pushed to surviving borrowers, % opening debt units
    deep_transfer_pct: float = 0.0  # value given to bidders by fills deeper than the ORIGINAL floor, % opening debt units
    subpar_loss_pct: float = 0.0    # ENRK face redeemed at a loss (sub-par), % opening ENRK
    subpar_redeemed_pct: float = 0.0
    enrk_repaid_auction: float = 0.0
    enrk_remaining: float = 0.0     # ENRK debt still on alive vaults at the end (peg units)
    enrk_start: float = 0.0
    redeemed_units: float = 0.0
    kas_end_price_ratio: float = 1.0


class Ledger:
    """Junior / treasury / reserve accounting. Income is credited at receipt, in
    peg units, at that day's KAS price (the junior is assumed to sell on receipt);
    raw KAS received is also kept so it can be marked at the end price instead.
    Fee income is in KAS; auction surplus is peg-unit cash (the model sells the
    whole collateral)."""

    def __init__(self, sc: "Scenario", face_junior: float, debt_start: float):
        self.sc = sc
        self.face = face_junior
        self.cap_units = sc.treasury_cap * debt_start
        self.inc_units = 0.0        # junior income at receipt (peg units)
        self.inc_kas = 0.0          # junior fee income, raw KAS
        self.inc_surplus = 0.0      # junior surplus income (peg units)
        self.res_kas = 0.0
        self.res_units = 0.0
        self.sink_units = 0.0       # non-absorbing sink (no junior exists)
        self.used_units = 0.0

    def res_value(self, price: float, peg: float) -> float:
        return self.res_units + self.res_kas * price / peg

    def _junior_part_kas(self, kas: float, price: float, peg: float) -> None:
        if self.face > 0:
            self.inc_kas += kas
            self.inc_units += kas * price / peg
        else:
            self.sink_units += kas * price / peg

    def credit_fee(self, fee_kas: float, price: float, peg: float) -> None:
        d = self.sc.dist_rule
        if d == "D1":
            self._junior_part_kas(fee_kas, price, peg)
        elif d == "D2":
            if self.res_value(price, peg) < self.cap_units:
                t = fee_kas * self.sc.treasury_share
                self.res_kas += t
                fee_kas -= t
            self._junior_part_kas(fee_kas, price, peg)
        else:  # D3
            self.res_kas += fee_kas

    def credit_surplus(self, units: float, price: float, peg: float) -> None:
        sr = self.sc.surplus_rule
        if sr == "S1" or units <= 0:
            return
        if sr == "S3":
            self.res_units += units
            return
        if sr == "SP":
            self.res_units += self.sc.phi_r * units
            j = self.sc.phi_j * units
            if self.face > 0:
                self.inc_surplus += j
                self.inc_units += j
            else:
                self.sink_units += j
            return
        d = self.sc.dist_rule     # S2: surplus goes through the same distribution rule
        if d == "D1":
            j = units
        elif d == "D2":
            j = units
            if self.res_value(price, peg) < self.cap_units:
                t = units * self.sc.treasury_share
                self.res_units += t
                j = units - t
        else:
            self.res_units += units
            return
        if self.face > 0:
            self.inc_surplus += j
            self.inc_units += j
        else:
            self.sink_units += j

    def draw(self, need: float, price: float, peg: float) -> float:
        """Use reserve as extra collateral to cover `need` peg units."""
        if need <= 0:
            return 0.0
        take_u = min(self.res_units, need)
        self.res_units -= take_u
        need -= take_u
        take_k = 0.0
        if need > 0 and self.res_kas > 0:
            k_needed = need * peg / price
            k = min(self.res_kas, k_needed)
            self.res_kas -= k
            take_k = k * price / peg
        got = take_u + take_k
        self.used_units += got
        return got

    def hold_value(self, price: float, peg: float) -> float:
        return self.inc_surplus + self.inc_kas * price / peg


class IndexState:
    """Why: peg-index process I(t) for ECON-T3 (decision: owner brief 2026-11-10, params econ-a4 s6).
    I = clip(exp(x) * J, 0.1, 5). x: log diffusion, martingale drift, annual vol idx_vol, plus
    beta*shrink*(KAS log-return lagged idx_lag days), beta = rho*sigma_I_daily/sigma_K_daily;
    idiosyncratic part sqrt(1-rho^2)*sigma. J: permanent energy jumps, daily prob p_month/30,
    size sign*U(15%,40%) on the energy component, weight 0.3 -> index factor (1+0.3*m).
    Random draws are consumed every day so that paths are paired across rho / vol / mode."""

    def __init__(self, sc: "Scenario"):
        import random as _r
        self.sc = sc
        self.rng = _r.Random(sc.seed * 1_000_003 + 17)
        self.x = 0.0
        self.J = 1.0
        self.rk: list[float] = []

    def step(self, cday: int, days: int, rk_today: float) -> float:
        sc = self.sc
        if sc.index_mode == "det":
            return min(max(sc.idx_target ** ((cday + 1) / days), PEG_FLOOR), PEG_CEIL)
        dt = 1.0 / 365.0
        sd = sc.idx_vol * math.sqrt(dt)
        eps = self.rng.gauss(0.0, 1.0)
        ju = self.rng.random(); jm = self.rng.random(); js = self.rng.random()
        self.rk.append(rk_today)
        lagged = self.rk[-1 - sc.idx_lag] if len(self.rk) > sc.idx_lag else 0.0
        beta = sc.idx_rho * sd / sc.kas_daily_sd
        self.x += (-0.5 * sc.idx_vol ** 2 * dt
                   + sd * math.sqrt(max(1.0 - sc.idx_rho ** 2, 0.0)) * eps
                   + beta * sc.idx_shrink * lagged)
        if sc.idx_jumps and ju < sc.idx_jump_pm / 30.0:
            m = (0.15 + 0.25 * jm) * (1.0 if js < 0.5 else -1.0)
            self.J *= 1.0 + 0.3 * m
        return min(max(math.exp(self.x) * self.J, PEG_FLOOR), PEG_CEIL)


def _push(sc: "Scenario", vaults, v, sk: float, se: float, soc_cum: float, d0: float):
    """Why: P4 carry-over of an uncovered shortfall to surviving borrowers (decision: ECON-V1 brief 2026-11-11, p3-sim s.2).
    Same rules as analyse_projet/loss_absorption_analysis.py (pro rata to current total debt of all other alive vaults);
    cap: soc_basis 'opening' = soc_cap * OPENING debt - cumulative gross pushed (fixed basis); 'legacy' = soc_cap * surviving debt now
    - cumulative pushed (the p3 flaw, kept for reproduction).  Returns (bk, be, pushed)."""
    alive = [w for w in vaults if w.alive and w is not v]
    if not alive:
        return 0.0, 0.0, 0.0
    dalive = sum(w.total_debt_units() for w in alive)
    if dalive <= 0:
        return 0.0, 0.0, 0.0
    if sc.soc_cap is None:
        cap_left = float("inf")
    elif sc.soc_basis == "opening":
        cap_left = max(sc.soc_cap * d0 - soc_cum, 0.0)
    else:
        cap_left = max(sc.soc_cap * dalive - soc_cum, 0.0)
    total = sk + se
    if sc.policy == "borrowers_first":
        amt = min(total, cap_left)
        bk = min(amt, sk)
        be = amt - bk
    elif sc.policy == "kfiat_then_borrowers":
        be = min(se, cap_left)
        bk = 0.0
    else:
        raise ValueError(sc.policy)
    if bk + be <= 0:
        return 0.0, 0.0, 0.0
    for w in alive:
        share = w.total_debt_units() / dalive
        w.debt_kfiat += bk * share
        w.debt_enrk += be * share
    return bk, be, bk + be


def run(scenario: Scenario, pre=None, stop_after_pre: bool = False) -> Result:
    rng = random.Random(scenario.seed)

    kas_price_0 = 0.10
    h, e, f, a = scenario.response.indices(1.0)
    peg_0 = scenario.formula.value(h, e, f, a)

    vaults = build_population(
        scenario.n_vaults, kas_price_0, peg_0,
        scenario.target_icr, scenario.icr_spread, scenario.kfiat_share,
        scenario.mcr_trigger, rng, scenario.size_scale,
    )

    debt_units_start = sum(v.total_debt_units() for v in vaults)
    enrk_start = sum(v.debt_enrk for v in vaults)
    kfiat_start = sum(v.debt_kfiat for v in vaults)
    icr_start = _mean_icr(vaults, kas_price_0, peg_0)

    kas_price = kas_price_0
    exogenous_ratio = 1.0
    reflexive_multiplier = 1.0   # cumulative damage from liquidation dumping

    kfiat_written_off = 0.0
    enrk_written_off = 0.0
    auctions_expired = 0
    auctions_filled = 0
    liquidated = 0
    discount_cost = 0.0
    recovery_days = 0
    redeemed = 0.0
    redemption_blocked = 0.0

    # --- ECON-M2 extension state ---
    P = scenario.pre_days
    ledger = (Ledger(scenario, kfiat_start, debt_units_start)
              if scenario.junior_ledger else None)
    fee_units_total = 0.0
    surplus_total = 0.0
    fee_tl: list[float] = []     # per pre day: fee KAS collected
    sur_tl: list[float] = []     # per pre day: auction surplus (peg units)
    liquidated_pre = 0
    fee_pre = 0.0
    surplus_pre = 0.0
    inc_pre = 0.0
    start_day = 0
    # --- ECON-T3 state ---
    mode = scenario.index_mode
    istate = IndexState(scenario) if mode in ("proc", "det") else None
    prev_ratio = 1.0
    peg = peg_0
    peg_max = peg_min = peg_0
    breaker_days = 0
    breaker_latched = False
    wo_value = 0.0
    freeze_days = 0
    latent_max = 0.0
    soc_cum = 0.0
    deep_transfer = 0.0
    subpar_loss = 0.0
    subpar_face = 0.0
    enrk_repaid_auction = 0.0
    if pre is not None:
        for v, (c, al, ia) in zip(vaults, pre["vaults"]):
            v.collateral_kas, v.alive, v.in_auction_since = c, al, ia
        auctions_expired = pre["auctions_expired"]
        auctions_filled = pre["auctions_filled"]
        liquidated = pre["liquidated"]
        discount_cost = pre["discount_cost"]
        fee_units_total = pre["fee_units_total"]
        surplus_total = pre["surplus_total"]
        fee_tl, sur_tl = pre["fee_tl"], pre["sur_tl"]
        if ledger is not None:
            for fk, su in zip(fee_tl, sur_tl):
                if fk > 0:
                    ledger.credit_fee(fk, kas_price_0, peg_0)
                if su > 0:
                    ledger.credit_surplus(su, kas_price_0, peg_0)
        start_day = P

    # Daily decline calibrated so that the drift plus the expected jump
    # contribution lands on total_drawdown by the final day. Without this
    # normalisation, adding jumps would silently deepen every scenario.
    days = scenario.crash_days
    expected_jump_log = (
        scenario.jump_probability * math.log(1.0 - scenario.jump_size)
    )
    drift_log = (math.log(1.0 - scenario.total_drawdown) / days) - expected_jump_log
    daily_decay = math.exp(drift_log)

    for day in range(start_day, P + days):
        in_pre = day < P
        if day == P:
            liquidated_pre = liquidated
            fee_pre = fee_units_total
            surplus_pre = surplus_total
            if ledger is not None and kfiat_start > 0:
                inc_pre = ledger.inc_units / kfiat_start
            if stop_after_pre:
                return {
                    "vaults": [(v.collateral_kas, v.alive, v.in_auction_since)
                               for v in vaults],
                    "auctions_expired": auctions_expired,
                    "auctions_filled": auctions_filled,
                    "liquidated": liquidated, "discount_cost": discount_cost,
                    "fee_units_total": fee_units_total,
                    "surplus_total": surplus_total,
                    "fee_tl": fee_tl, "sur_tl": sur_tl,
                }
        if not in_pre:
            exogenous_ratio *= daily_decay
            if rng.random() < scenario.jump_probability:
                exogenous_ratio *= (1.0 - scenario.jump_size)
        price_ratio = exogenous_ratio * reflexive_multiplier
        kas_price = kas_price_0 * price_ratio

        if mode == "orig":
            h, e, f, a = scenario.response.indices(price_ratio)
            peg = scenario.formula.value(h, e, f, a)
        elif mode == "flat":
            peg = peg_0
        else:   # "proc" | "det": index I(t); only active in the crash unless idx_in_pre
            rk_today = math.log(price_ratio / prev_ratio) if price_ratio > 0 else 0.0
            if in_pre and not scenario.idx_in_pre:
                peg = peg_0
            else:
                peg = peg_0 * istate.step(day - P, days, rk_today)
        prev_ratio = price_ratio
        peg_max = max(peg_max, peg); peg_min = min(peg_min, peg)

        # Circuit breaker, wired to the index value (assumption: only input available)
        halt_red = halt_liq = False
        if scenario.breaker != "none":
            if int(abs(peg - 1.0) * 100) > 10:
                breaker_latched = True
                tripped_now = True
            else:
                tripped_now = False
            paused = tripped_now if scenario.breaker == "liq_live" else breaker_latched
            if paused:
                breaker_days += 1
                halt_red = True
                halt_liq = scenario.breaker in ("liq_latch", "liq_live")

        drawdown_so_far = 1.0 - price_ratio
        required_discount = min(
            scenario.base_required_discount
            + scenario.stress_sensitivity * max(drawdown_so_far, 0.0),
            1.0,
        )
        offered_discount = 1.0 - scenario.auction_end_price

        # Recovery Mode: read the system-wide collateral ratio and raise the
        # effective MCR when it falls below the threshold. This is the whole
        # mechanism, and it is exactly what needs global aggregate state.
        effective_mcr = scenario.mcr_trigger
        if scenario.recovery_threshold is not None:
            system_icr = _mean_icr(vaults, kas_price, peg)
            if system_icr < scenario.recovery_threshold:
                effective_mcr = scenario.recovery_mcr
                recovery_days += 1

        # ---- Stability fee: KAS taken from vault collateral ---------------
        sur_today = 0.0
        if scenario.stability_fee > 0.0:
            k_fee = scenario.stability_fee / 365.0 * peg / kas_price
            fee_kas_today = 0.0
            for v in vaults:
                if not v.alive:
                    continue
                if v.in_auction_since is not None and not scenario.fee_in_auction:
                    continue
                fk = (v.debt_enrk + v.debt_kfiat) * k_fee
                if fk > v.collateral_kas:
                    fk = v.collateral_kas
                v.collateral_kas -= fk
                fee_kas_today += fk
            fee_units_total += fee_kas_today * kas_price / peg
            if ledger is not None and fee_kas_today > 0:
                ledger.credit_fee(fee_kas_today, kas_price, peg)
            if in_pre:
                fee_tl.append(fee_kas_today)
        elif in_pre:
            fee_tl.append(0.0)

        # ---- Redemption pass -------------------------------------------
        if scenario.enable_redemption and (not in_pre or scenario.pre_redemption) and not halt_red:
            outstanding = sum(v.debt_enrk for v in vaults if v.alive)
            demand = outstanding * (
                scenario.redemption_base_rate
                + scenario.redemption_stress_sensitivity * max(drawdown_so_far, 0.0)
            )
            _minicr = scenario.redemption_min_icr
            eligible = sorted(
                (v for v in vaults
                 if v.alive
                 and v.debt_enrk > 0
                 and (scenario.subpar_redemption or v.icr(kas_price, peg) >= _minicr)),
                key=lambda v: v.icr(kas_price, peg),
            )
            for v in eligible:
                if demand <= 0:
                    break
                take = min(demand, v.debt_enrk)
                if scenario.subpar_redemption and v.icr(kas_price, peg) < _minicr:
                    # C2: redeem against an under-water vault at min(face, collateral), pro rata to its ENRK debt.
                    # ENRK is senior: collateral covers ENRK first; the kFIAT part is wiped when collateral < ENRK debt.
                    cval = v.collateral_kas * kas_price / peg            # collateral in peg units
                    ratio = min(cval / v.debt_enrk, 1.0)                 # recovery per unit ENRK face
                    f = take / v.debt_enrk
                    v.collateral_kas -= (f * v.collateral_kas) if ratio < 1.0 else (take * peg / kas_price)
                    loss_face = take * (1.0 - ratio)
                    if loss_face > 0:
                        enrk_written_off += loss_face
                        wo_value += loss_face * peg
                        subpar_loss += loss_face
                        # kFIAT behind it is wiped in the same proportion (collateral did not even cover ENRK)
                        kw = f * v.debt_kfiat
                        kfiat_written_off += kw
                        wo_value += kw * peg
                        v.debt_kfiat -= kw
                    v.debt_enrk -= take
                    demand -= take
                    redeemed += take
                    subpar_face += take
                    if v.debt_enrk <= 1e-12 and v.debt_kfiat <= 1e-12:
                        v.alive = False
                    continue
                collateral_out = take * peg / kas_price
                if collateral_out >= v.collateral_kas:
                    # Face value cannot be honoured; skip rather than overdraw.
                    continue
                v.debt_enrk -= take
                v.collateral_kas -= collateral_out
                demand -= take
                redeemed += take
            redemption_blocked += max(demand, 0.0)

        kas_dumped_today = 0.0
        capacity_left = scenario.daily_liquidation_capacity * debt_units_start
        if scenario.capacity_mode == "value":
            capacity_left *= peg_0 / peg
        elif scenario.capacity_mode == "adv":
            capacity_left = scenario.adv_frac * scenario.daily_volume_kas * kas_price / peg

        for v in (() if halt_liq else vaults):
            if not v.alive:
                continue
            if v.icr(kas_price, peg) >= effective_mcr:
                v.in_auction_since = None
                v.stuck_since = None
                continue

            if v.in_auction_since is None:
                v.in_auction_since = day
                continue
            if day - v.in_auction_since < scenario.auction_days:
                continue

            # Auction resolves today.
            offered_eff = offered_discount
            deepened = False
            if scenario.c1_days > 0 and v.stuck_since is not None:
                steps = (day - v.stuck_since) // scenario.c1_days
                if steps > 0:
                    floor_eff = max(scenario.auction_end_price - scenario.c1_step * steps, scenario.c1_min)
                    if floor_eff < scenario.auction_end_price:
                        offered_eff = 1.0 - floor_eff
                        deepened = True
            if required_discount > offered_eff:
                # No bidder at any point in the 15% descent. The auction simply
                # fails: the collateral is NOT destroyed and the debt is NOT
                # written off. The vault stays open and is re-auctioned tomorrow,
                # which is what actually happens on-chain.
                auctions_expired += 1
                v.in_auction_since = day   # restart the clock, try again
                if v.stuck_since is None:
                    v.stuck_since = day
                continue

            if v.total_debt_units() > capacity_left:
                # Liquidators are tapped out for today. The vault waits — and
                # keeps falling while it waits.
                auctions_expired += 1
                v.in_auction_since = day
                if v.stuck_since is None:
                    v.stuck_since = day
                continue
            capacity_left -= v.total_debt_units()

            auctions_filled += 1
            # A Dutch auction clears at the FIRST price a bidder accepts, not at
            # the floor. The price descends from 100%; a liquidator takes it the
            # moment it reaches their required discount. The floor only binds
            # when that requirement is deeper than the auction can descend --
            # which is exactly the stress case. Modelling every fill at the
            # floor massively overstates the cost of a deeper floor in calm
            # markets.
            fill_price = max(1.0 - required_discount, scenario.auction_end_price)
            if deepened:
                fill_price = min(fill_price, 1.0 - (required_discount + scenario.bidder_greed * (offered_eff - required_discount)))
                if 1.0 - fill_price > offered_discount:
                    deep_transfer += v.collateral_kas * kas_price * ((1.0 - fill_price) - offered_discount) / peg
            proceeds_units = v.collateral_kas * kas_price * fill_price / peg
            discount_cost += (
                v.collateral_kas * kas_price * (1.0 - fill_price) / peg
            )
            net = proceeds_units * (1.0 - LIQUIDATION_FEE)
            if ledger is not None and scenario.reserve_absorbs:
                _short = v.debt_enrk + v.debt_kfiat - net
                if _short > 0:
                    net += ledger.draw(_short, kas_price, peg)
            kas_dumped_today += v.collateral_kas

            # Seniority waterfall: ENRK is repaid first, so a shortfall lands
            # on kFIAT first. That ordering IS "kFIAT absorbs losses first".
            enrk_repaid = min(net, v.debt_enrk)
            enrk_repaid_auction += enrk_repaid
            v.debt_enrk -= enrk_repaid
            net -= enrk_repaid

            kfiat_repaid = min(net, v.debt_kfiat)
            v.debt_kfiat -= kfiat_repaid
            net -= kfiat_repaid

            if net > 0:
                sur_today += net     # surplus beyond debt (before write-offs)
            # Anything still owed after the collateral is exhausted is a
            # realised loss for token holders. (Surplus `net` would return to
            # the vault owner; it is not the protocol's.)
            _sk, _se = v.debt_kfiat, v.debt_enrk
            if scenario.policy != "waterfall" and _sk + _se > 0:
                _bk, _be, _pushed = _push(scenario, vaults, v, _sk, _se, soc_cum, debt_units_start)
                soc_cum += _pushed
                _sk -= _bk; _se -= _be
            kfiat_written_off += _sk
            enrk_written_off += _se
            wo_value += (_sk + _se) * peg
            v.debt_kfiat = 0.0
            v.debt_enrk = 0.0
            v.alive = False
            liquidated += 1

        if not in_pre:
            _hole = 0.0
            for _v in vaults:
                if _v.alive:
                    _cov = _v.collateral_kas * kas_price / peg
                    _d = _v.debt_enrk + _v.debt_kfiat
                    if _cov < _d:
                        _hole += _d - _cov
            if _hole > 0.0:
                freeze_days += 1
                latent_max = max(latent_max, _hole)

        # Reflexive loop: today's liquidated collateral hits the order book.
        # Square-root market impact (Kyle / Almgren-Chriss), the standard
        # empirical law: impact scales with sqrt(order size / daily volume),
        # not linearly. A linear law compounds absurdly over 60 days.
        surplus_total += sur_today
        if ledger is not None and sur_today > 0:
            ledger.credit_surplus(sur_today, kas_price, peg)
        if in_pre:
            sur_tl.append(sur_today)

        if kas_dumped_today > 0 and (not in_pre or scenario.pre_impact):
            participation = kas_dumped_today / scenario.daily_volume_kas
            impact = scenario.impact_coefficient * math.sqrt(participation)
            if scenario.convex_impact and participation > scenario.conv_p0:
                impact += scenario.conv_beta * (participation - scenario.conv_p0)
            reflexive_multiplier *= max(1.0 - impact, 0.05)

    final_ratio = exogenous_ratio * reflexive_multiplier
    kas_price = kas_price_0 * final_ratio
    if mode == "orig":
        h, e, f, a = scenario.response.indices(final_ratio)
        peg_end = scenario.formula.value(h, e, f, a)
    else:
        peg_end = peg   # index of the last simulated day (the final reflexive impact does not move it)

    # Latent hole: vaults still open whose collateral no longer covers the debt.
    stranded_vaults = 0
    stranded_hole = 0.0
    for v in vaults:
        if not v.alive:
            continue
        cover = v.collateral_kas * kas_price / peg_end
        if cover < v.total_debt_units():
            stranded_vaults += 1
            stranded_hole += v.total_debt_units() - cover

    return Result(
        scenario=scenario.name,
        formula=scenario.formula.name,
        final_kas_ratio=final_ratio,
        final_peg=peg_end,
        mean_icr_start=icr_start,
        mean_icr_end=_mean_icr(vaults, kas_price, peg_end),
        vaults_liquidated=liquidated,
        vaults_total=scenario.n_vaults,
        auctions_expired=auctions_expired,
        auctions_filled=auctions_filled,
        debt_units_start=debt_units_start,
        kfiat_written_off=kfiat_written_off,
        enrk_written_off=enrk_written_off,
        enrk_loss_pct=100.0 * enrk_written_off / enrk_start if enrk_start else 0.0,
        kfiat_loss_pct=100.0 * kfiat_written_off / kfiat_start if kfiat_start else 0.0,
        discount_cost_pct=(
            100.0 * discount_cost / debt_units_start if debt_units_start else 0.0
        ),
        recovery_days=recovery_days,
        redeemed_pct=(100.0 * redeemed / enrk_start if enrk_start else 0.0),
        redemption_blocked_pct=(
            100.0 * redemption_blocked / enrk_start if enrk_start else 0.0
        ),
        stranded_vaults=stranded_vaults,
        stranded_hole_pct=(
            100.0 * stranded_hole / debt_units_start if debt_units_start else 0.0
        ),
        liquidated_pre=liquidated_pre,
        fee_paid_pct=100.0 * fee_units_total / debt_units_start,
        fee_paid_pre_pct=100.0 * fee_pre / debt_units_start,
        surplus_pct=100.0 * surplus_total / debt_units_start,
        surplus_pre_pct=100.0 * surplus_pre / debt_units_start,
        junior_inc_pre_pct=100.0 * inc_pre,
        junior_inc_pct=(100.0 * ledger.inc_units / kfiat_start
                        if ledger is not None and kfiat_start > 0 else 0.0),
        junior_hold_pct=(100.0 * ledger.hold_value(kas_price, peg_end) / kfiat_start
                         if ledger is not None and kfiat_start > 0 else 0.0),
        reserve_end_pct=(100.0 * ledger.res_value(kas_price, peg_end) / debt_units_start
                         if ledger is not None else 0.0),
        reserve_used_pct=(100.0 * ledger.used_units / debt_units_start
                          if ledger is not None else 0.0),
        unbacked_usd_pct=100.0 * (wo_value + stranded_hole * peg_end) / (debt_units_start * peg_0),
        unbacked_units_pct=100.0 * (kfiat_written_off + enrk_written_off + stranded_hole) / debt_units_start,
        breaker_days=breaker_days, peg_max=peg_max, peg_min=peg_min,
        freeze_days=freeze_days, latent_max_pct=100.0 * latent_max / debt_units_start,
        pushed_pct=100.0 * soc_cum / debt_units_start,
        deep_transfer_pct=100.0 * deep_transfer / debt_units_start,
        subpar_loss_pct=100.0 * subpar_loss / enrk_start if enrk_start else 0.0,
        subpar_redeemed_pct=100.0 * subpar_face / enrk_start if enrk_start else 0.0,
        enrk_repaid_auction=enrk_repaid_auction,
        enrk_remaining=sum(v.debt_enrk for v in vaults if v.alive),
        enrk_start=enrk_start, redeemed_units=redeemed, kas_end_price_ratio=final_ratio,
    )


def _mean_icr(vaults: list[Vault], kas_price: float, peg: float) -> float:
    """Aggregate ICR over surviving vaults (total collateral / total debt)."""
    coll = sum(v.collateral_kas for v in vaults if v.alive) * kas_price
    debt = sum(v.total_debt_units() for v in vaults if v.alive) * peg
    return coll / debt if debt > 0 else math.inf


# ----------------------------------------------------------------------------
# Minimum-ICR search
# ----------------------------------------------------------------------------

def min_icr_for_zero_enrk_loss(
    base: Scenario, lo: float = 1.51, hi: float = 12.0, tol: float = 0.05
) -> float | None:
    """Smallest opening ICR at which no ENRK holder loses anything."""
    probe = Scenario(**{**base.__dict__, "target_icr": hi})
    if run(probe).enrk_written_off > 0:
        return None
    while hi - lo > tol:
        mid = (lo + hi) / 2
        probe = Scenario(**{**base.__dict__, "target_icr": mid})
        if run(probe).enrk_written_off > 0:
            lo = mid
        else:
            hi = mid
    return hi



# ----------------------------------------------------------------------------
# Monte Carlo
# ----------------------------------------------------------------------------

def monte_carlo(base: Scenario, paths: int = 200) -> dict[str, tuple[float, float, float]]:
    """
    Re-run a scenario across many random paths. A single path proves nothing:
    the jump timing alone can swing the outcome, and it is the tail that
    decides whether an immutable protocol survives.

    Returns {metric: (median, p95, worst)}.
    """
    enrk, kfiat, latent = [], [], []
    for i in range(paths):
        r = run(Scenario(**{**base.__dict__, "seed": SEED + i}))
        enrk.append(r.enrk_loss_pct)
        kfiat.append(r.kfiat_loss_pct)
        latent.append(r.stranded_hole_pct)

    def stats(xs: list[float]) -> tuple[float, float, float]:
        xs = sorted(xs)
        return (
            xs[len(xs) // 2],
            xs[min(int(len(xs) * 0.95), len(xs) - 1)],
            xs[-1],
        )

    return {"ENRK loss": stats(enrk), "kFIAT loss": stats(kfiat),
            "latent hole": stats(latent)}


# ----------------------------------------------------------------------------
# Reporting
# ----------------------------------------------------------------------------

def _hdr(title: str) -> None:
    print(f"\n{title}")
    print("=" * len(title))


def report(results: list[Result]) -> None:
    print(f"{'Scenario':<32}{'KAS':>7}{'peg':>7}{'liq':>6}{'stuck':>7}"
          f"{'kFIAT':>8}{'ENRK':>8}{'latent':>8}")
    print("-" * 83)
    for r in results:
        print(f"{r.scenario:<32}"
              f"{r.final_kas_ratio:>7.2f}"
              f"{r.final_peg:>7.3f}"
              f"{r.vaults_liquidated:>6}"
              f"{r.stranded_vaults:>7}"
              f"{r.kfiat_loss_pct:>7.0f}%"
              f"{r.enrk_loss_pct:>7.0f}%"
              f"{r.stranded_hole_pct:>7.0f}%")
    print("  KAS/peg = end values as a ratio of start.  liq = vaults liquidated,")
    print("  stuck = still open but under water.  latent = unbacked debt not yet realised.")


def main() -> None:
    print("ENRK CRASH STRESS TEST")
    print(f"seed={SEED}  vaults=1000  MCR=150%  kFIAT share=30%  "
          f"auction floor={AUCTION_END_PRICE:.0%}")

    # --- 1. Crash severity, deployed formula ---------------------------------
    _hdr("1. Crash severity — deployed formula (Alt 3.5), opening ICR 200%")
    sev = []
    for dd in (0.50, 0.70, 0.85, 0.95):
        sev.append(run(Scenario(name=f"KAS {-dd:.0%}", total_drawdown=dd)))
    report(sev)

    # --- 2. Peg formula comparison -------------------------------------------
    _hdr("2. Peg formula — same -85% crash, opening ICR 200%")
    cmp_ = []
    for formula in (FORMULA_35, FORMULA_ALT3):
        cmp_.append(run(Scenario(
            name=f"KAS -85%  {formula.name}",
            total_drawdown=0.85, formula=formula,
        )))
    report(cmp_)

    # --- 3. The genuinely darkest case ---------------------------------------
    _hdr("3. Energy crisis + crypto crash (2022 pattern), -85%")
    print("Energy up 60% while KAS collapses: the hedge pushes the peg UP")
    print("exactly as collateral falls. Worst possible case for solvency.")
    dark = []
    for mult, label in ((1.00, "energy flat"), (1.60, "energy +60%")):
        dark.append(run(Scenario(
            name=f"KAS -85%, {label}",
            total_drawdown=0.85,
            response=IndexResponse(energy_multiplier=mult),
        )))
    report(dark)

    # --- 4. Over-collateralisation ladder ------------------------------------
    _hdr("4. Opening ICR ladder — -85% crash, deployed formula")
    ladder = []
    for icr in (2.00, 3.00, 4.00, 6.00):
        ladder.append(run(Scenario(
            name=f"opening ICR {icr:.0%}", total_drawdown=0.85, target_icr=icr,
        )))
    report(ladder)

    # --- 5. Minimum ICR for zero ENRK loss -----------------------------------
    _hdr("5. Minimum opening ICR for zero ENRK loss")
    for dd in (0.70, 0.85, 0.95):
        base = Scenario(name="probe", total_drawdown=dd)
        need = min_icr_for_zero_enrk_loss(base)
        shown = "not reachable below 1200%" if need is None else f"{need*100:.0f}%"
        print(f"  KAS {-dd:>5.0%}  ->  {shown}")

    # --- 6. Auction viability ------------------------------------------------
    _hdr("6. Where the Dutch auction stops clearing")
    print("The auction floor is 85% of market, a 15% discount. Liquidators")
    print("demand base 4% + 18% x drawdown. Beyond the crossover, no auction")
    print("fills at any point in the descent:")
    print(f"    required = 4% + 18% x drawdown  >  15%  when  drawdown > "
          f"{(0.15 - 0.04) / 0.18:.0%}")

    _hdr("7. Monte Carlo — 200 random paths per drawdown, opening ICR 200%")
    print(f"{'Drawdown':<12}{'metric':<14}{'median':>9}{'p95':>9}{'worst':>9}")
    print("-" * 53)
    for dd in (0.70, 0.85, 0.95):
        stats = monte_carlo(Scenario(name="mc", total_drawdown=dd))
        for i, (metric, (med, p95, worst)) in enumerate(stats.items()):
            label = f"KAS {-dd:.0%}" if i == 0 else ""
            print(f"{label:<12}{metric:<14}{med:>8.0f}%{p95:>8.0f}%{worst:>8.0f}%")
        print()

    print("\nAll figures are scenario-dependent, not forecasts. The parameters")
    print("that matter most are in Scenario: impact_coefficient and")
    print("stress_sensitivity. Change them and re-run before trusting any number.")


if __name__ == "__main__":
    main()
