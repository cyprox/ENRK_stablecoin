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
) -> list[Vault]:
    """
    Vault sizes are log-normal (a few whales, a long tail of small positions).

    Opening ICR is drawn from a lognormal centred on target_icr: nobody opens
    exactly at the minimum, but the distribution is tight against it, because
    capital efficiency is what borrowers optimise for.
    """
    vaults: list[Vault] = []
    for _ in range(n):
        size_kas = rng.lognormvariate(mu=math.log(50_000), sigma=1.2)
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


def run(scenario: Scenario) -> Result:
    rng = random.Random(scenario.seed)

    kas_price_0 = 0.10
    h, e, f, a = scenario.response.indices(1.0)
    peg_0 = scenario.formula.value(h, e, f, a)

    vaults = build_population(
        scenario.n_vaults, kas_price_0, peg_0,
        scenario.target_icr, scenario.icr_spread, scenario.kfiat_share,
        scenario.mcr_trigger, rng,
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

    # Daily decline calibrated so that the drift plus the expected jump
    # contribution lands on total_drawdown by the final day. Without this
    # normalisation, adding jumps would silently deepen every scenario.
    days = scenario.crash_days
    expected_jump_log = (
        scenario.jump_probability * math.log(1.0 - scenario.jump_size)
    )
    drift_log = (math.log(1.0 - scenario.total_drawdown) / days) - expected_jump_log
    daily_decay = math.exp(drift_log)

    for day in range(days):
        exogenous_ratio *= daily_decay
        if rng.random() < scenario.jump_probability:
            exogenous_ratio *= (1.0 - scenario.jump_size)
        price_ratio = exogenous_ratio * reflexive_multiplier
        kas_price = kas_price_0 * price_ratio

        h, e, f, a = scenario.response.indices(price_ratio)
        peg = scenario.formula.value(h, e, f, a)

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

        # ---- Redemption pass -------------------------------------------
        if scenario.enable_redemption:
            outstanding = sum(v.debt_enrk for v in vaults if v.alive)
            demand = outstanding * (
                scenario.redemption_base_rate
                + scenario.redemption_stress_sensitivity * max(drawdown_so_far, 0.0)
            )
            eligible = sorted(
                (v for v in vaults
                 if v.alive
                 and v.debt_enrk > 0
                 and v.icr(kas_price, peg) >= scenario.redemption_min_icr),
                key=lambda v: v.icr(kas_price, peg),
            )
            for v in eligible:
                if demand <= 0:
                    break
                take = min(demand, v.debt_enrk)
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

        for v in vaults:
            if not v.alive:
                continue
            if v.icr(kas_price, peg) >= effective_mcr:
                v.in_auction_since = None
                continue

            if v.in_auction_since is None:
                v.in_auction_since = day
                continue
            if day - v.in_auction_since < scenario.auction_days:
                continue

            # Auction resolves today.
            if required_discount > offered_discount:
                # No bidder at any point in the 15% descent. The auction simply
                # fails: the collateral is NOT destroyed and the debt is NOT
                # written off. The vault stays open and is re-auctioned tomorrow,
                # which is what actually happens on-chain.
                auctions_expired += 1
                v.in_auction_since = day   # restart the clock, try again
                continue

            if v.total_debt_units() > capacity_left:
                # Liquidators are tapped out for today. The vault waits — and
                # keeps falling while it waits.
                auctions_expired += 1
                v.in_auction_since = day
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
            proceeds_units = v.collateral_kas * kas_price * fill_price / peg
            discount_cost += (
                v.collateral_kas * kas_price * (1.0 - fill_price) / peg
            )
            net = proceeds_units * (1.0 - LIQUIDATION_FEE)
            kas_dumped_today += v.collateral_kas

            # Seniority waterfall: ENRK is repaid first, so a shortfall lands
            # on kFIAT first. That ordering IS "kFIAT absorbs losses first".
            enrk_repaid = min(net, v.debt_enrk)
            v.debt_enrk -= enrk_repaid
            net -= enrk_repaid

            kfiat_repaid = min(net, v.debt_kfiat)
            v.debt_kfiat -= kfiat_repaid
            net -= kfiat_repaid

            # Anything still owed after the collateral is exhausted is a
            # realised loss for token holders. (Surplus `net` would return to
            # the vault owner; it is not the protocol's.)
            kfiat_written_off += v.debt_kfiat
            enrk_written_off += v.debt_enrk
            v.debt_kfiat = 0.0
            v.debt_enrk = 0.0
            v.alive = False
            liquidated += 1

        # Reflexive loop: today's liquidated collateral hits the order book.
        # Square-root market impact (Kyle / Almgren-Chriss), the standard
        # empirical law: impact scales with sqrt(order size / daily volume),
        # not linearly. A linear law compounds absurdly over 60 days.
        if kas_dumped_today > 0:
            participation = kas_dumped_today / scenario.daily_volume_kas
            impact = scenario.impact_coefficient * math.sqrt(participation)
            reflexive_multiplier *= max(1.0 - impact, 0.05)

    final_ratio = exogenous_ratio * reflexive_multiplier
    kas_price = kas_price_0 * final_ratio
    h, e, f, a = scenario.response.indices(final_ratio)
    peg_end = scenario.formula.value(h, e, f, a)

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
