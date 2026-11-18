# KaspaDollar due diligence: team, accounts, domain, fundraiser (evidence only)

Accessed 2026-11-15. No wallet addresses are recorded here (aggregates only). All web content treated as untrusted data.

## 1. People

- F1. Site /docs states: "Kaspa Dollar is led by Alexander Safstrom, a Kaspa core developer and the author of KIP-16 ... with the help and support of the rest of the Kaspa core team." Source: https://kaspadollar.com/docs (2026-11-15).
- F2. KIP-16 header lists "Authors: Alexander Safstrom (@saefstroem)", Status: Active, title "New Transaction Opcodes for Verifiable Computation" (OpZkPrecompile). Source: https://raw.githubusercontent.com/kaspanet/kips/master/kip-0016.md (2026-11-15). KIP-16 "Active" marking was done in kaspanet/kips PR #45 "Mark kips 16,17,20,21 as active", opened by user michaelsutton (https://github.com/kaspanet/kips/pull/45, via GitHub search API, 2026-11-15). So the KIP-16 authorship claim is VERIFIED.
- F3. GitHub user saefstroem: created 2023-07-10, 53 public repos, 18 followers, bio "~" (https://api.github.com/users/saefstroem, 2026-11-15). GitHub commit search shows 11 commits by this account in kaspanet/rusty-kaspa, latest seen 2025-01-06 (CI/lint changes) (https://api.github.com/search/commits?q=author:saefstroem+repo:kaspanet/rusty-kaspa, 2026-11-15). Search results are capped and may be incomplete. Link between this GitHub account and the person "Alexander" relies on the KIP author line; I did not independently verify legal identity.
- F4. The X handle @asaefstroem is the one named in KaspaDollar's launch post and press (see 5.1). The page was not fetched (see section 7).
- F5. A Medium post by Michael Sutton (Kaspa core developer) says KIP-16 was authored and implemented by Alexander Safstrom (per search-engine summary of https://medium.com/@michaelsuttonil/kaspa-covenants-toccata-hard-fork-outlook-a4d81a40900c; page itself not opened, so UNVERIFIED in detail).
- F6. "Kaspa core developer" status: supported by KIP authorship and rusty-kaspa commits (F2, F3). Whether he is currently an official member of a "core team" was not verified from an official Kaspa source (no kaspa.org team page found).
- F7. Endorsement by Kaspa core team: Cryptoast (2026-10-26) says Michael Sutton "pledged to do whatever he can technically" to help the team overcome protocol obstacles, citing https://x.com/michaelsuttonil/status/2114040191719444646 (relayed via WebFetch summary of https://cryptoast.fr/kaspa-kas-kaspadollar-stablecoin-decentralise-collecte/; I did not open the X post). A 2026-11-10 KuCoin-republished community post (author "Shawnz") says Sutton responded to oracle-decentralisation criticism by saying it is a reason to decentralise mining (secondhand: https://www.kucoin.com/news/community/KAS/6af30ca54fd70f00078ea81e). So one named core dev appears supportive in a technical sense; this is NOT confirmation that "the rest of the Kaspa core team" supports the project. No denial found; no official Kaspa (kaspa.org) endorsement found. The claim about the whole core team: UNVERIFIED.
- F8. Prior controversies/red flags about the person: none found in searches run. Absence of evidence only; not exhaustive.
- Contact email in whitepaper (proton.me) not re-checked here; the site's contact is support@kaspadollar.com (mailto on /docs).

## 2. Accounts and linked sites

- Site links only X: https://x.com/KaspaDollar. No Telegram/Discord/GitHub/Medium/YouTube linked from home or /docs (link extraction, 2026-11-15).
- X launch post by KaspaDollar dated 2026-10-23, text begins "Today we are introducing KaspaDollar, an initiative led by core developer ..." (https://x.com/KaspaDollar/status/2113601328975098237, quoted in Cryptoast; not opened directly).
- X profile page: WebFetch returned HTTP 402; not accessed. Creation date, follower count, posting history UNVERIFIED.
- KuCoin "Kaspa Hub" repost 2026-10-24 confirms the announcement ("Kaspa core developer @asaefstroem has introduced KaspaDollar"): https://www.kucoin.com/news/insight/KAS/6adc78b9b1e8a7000772254d.
- Related but separate: $KDOLLAR meme token (KCC-20, on KaspaRocket) at https://kdollar.space/. The page says it is a community site "Curated By @pedroprotecc of $PHANT", does "not speak for its development team", is not a stablecoin and gives no right to future KaspaDollar tokens, and that 100% of its KaspaRocket trading fees are sent on-chain to the "KaspaDollar Initiative wallet"; it also claims the team bought kdollar.kas / kdollar.k domains. These are claims on a third-party page (WebFetch summary 2026-11-15); the fee flow and domain purchase are UNVERIFIED. Note: meme-token fees feeding the same wallet could be mixed into the fundraiser balance if that wallet is the collection address (not checked).
- Lookalike domains: DNS A lookups for kaspadollar.net/.org/.io/.xyz/.app, kaspa-dollar.com, ksd.finance returned no A record (2026-11-15). Not a full impersonation scan; fake X accounts not searched.

## 3. Domain and infrastructure

- RDAP (Verisign, https://rdap.verisign.com/com/v1/domain/kaspadollar.com, 2026-11-15): registered 2026-08-21T19:43:35Z, expires 2027-08-21, registrar Cloudflare, Inc., status client transfer prohibited, nameservers audrey/nitin.ns.cloudflare.com. Registrant data redacted/not shown. (rdap.org redirected with 302.)
- DNS: A records 188.114.96.0 / 188.114.97.0 (Cloudflare range); MX mail.protonmail.ch / mailsec.protonmail.ch; TXT protonmail verification and SPF include protonmail. Server header: cloudflare; site built with SvelteKit (x-sveltekit-page header).
- TLS: issuer Google Trust Services (WE1), subject CN=kaspadollar.com, notBefore 2026-10-14, notAfter 2027-01-12 (openssl, 2026-11-15). Cert issued 9 days before the first deposit and 9 days before the public launch post.
- Domain registered about 2 months before the public announcement (2026-10-23). The domain pre-dates the announcement; the first on-chain receipt is 2026-10-23.
- Wayback Machine: CDX endpoint returned HTTP 429 repeatedly; availability API returned no snapshot for kaspadollar.com near 2026-10-01 ({"archived_snapshots": {}}). Site history, changed claims, removed claims: UNVERIFIED / not reconstructed.

## 4. Fundraiser transparency (public chain data via https://api.kaspa.org, 2026-11-15; addresses withheld)

Site claims: homepage "640,011 of 5,000,000 KAS has been raised so far, 12.8%"; target 5,000,000 KAS, closes 2027-01-01; refunds if target missed (https://kaspadollar.com/, /docs).
Chain results for the collection address published on /docs:
- Balance: 640,011.267 KAS (balance field 64001126709996 sompi). Matches the homepage figure (640,011) and is a live read, so the counter appears to be the on-chain balance, not an independent claim. Note: 640,011 KAS is about 12.8% of target; the headline "640,000" in the brief matches.
- Transactions: 848 total, all incoming; 0 transactions spending from the address (no outgoing). Consistent with "funds held".
- First receipt 2026-10-23T12:17Z; last receipt 2026-11-15T10:25Z (fundraiser is active).
- Monthly inflow: October 2026 about 228,785 KAS; November (to the 15th) about 411,226 KAS. Cryptoast reported 103,977 KAS on 2026-10-26, so raising accelerated after that (about 6x since).
- Largest single receipts (KAS): 200,000; 44,995; 20,000; 20,000; 20,000; 12,345; then 10,000 several times. The single 200,000 KAS receipt is about 31% of the total balance. Largest summed input-sender totals (by input address, apportioned): 100,000; 100,000; 70,000; 45,000; 13,000. Distinct input addresses across incoming txs: 1,472 (many txs are multi-input, so this is NOT a count of distinct contributors). Self-funding cannot be ruled in or out from this; no address attribution was attempted (kaspa.stream labels not queried).
- Spending reports: /docs says "Every transaction out of the fundraising address is published at the end of each month". Since no outgoing transactions exist, there is nothing to report yet; no monthly report page was found on the site (links: /, /why-stablecoins, /how-it-works, /whitepaper, /docs, /contact only).
- Use of funds (/docs): 72% (3,600,000 KAS) "development fees, relationship building, travel to conferences, promotion and marketing, representation of Kaspa"; 28% (1,400,000 KAS) audit. Funds go to an address with no stated multisig/custody structure on /docs (UNVERIFIED whether single-key). The 72% bucket is not itemised and includes the lead developer's own fees. Target (about USD 175,000 at 0.035 USD/KAS per Cryptoast) is the project's own claim.
- Refund terms: refunds only returnable to the sending address; exchange contributions need a manual email claim with DKIM headers, "No guarantees can be made" (/docs).
- Roadmap on /docs: Jan fundraiser closes; Jan-Apr build; May testnet; Jun-Aug audit; Sep mainnet (year 2027 per Cryptoast). If the target is missed the refund is promised; no escrow/timelock is described.

## 5. Community reception (search-engine and fetched pages; no Reddit/Telegram/Discord archives reachable)

5.1 Coverage:
- Cryptoast, 2026-10-26, "Kaspa : vers un premier stablecoin décentralisé ?" by Mattis Meichler: descriptive; compares to Aave GHO; 103,977 KAS raised at time of writing. https://cryptoast.fr/kaspa-kas-kaspadollar-stablecoin-decentralise-collecte/
- KuCoin news "Kaspa Hub" repost, 2026-10-24. https://www.kucoin.com/news/insight/KAS/6adc78b9b1e8a7000772254d
- cryptonews.net (republishing bsc.news), 2026-11-09, "Kaspa Dollar Publishes Working Whitepaper for KAS-Backed KSD Stablecoin With No Admin Key": says contracts would have no admin key or developer fee, KAS only collateral; notes whitepaper is a working draft, audit pending, CoinMarketCap describes it as non-live spec; no outside endorsement or criticism. https://cryptonews.net/news/altcoins/33723755/
- Publish0x article (title "The Rise of Decentralized Native Stablecoins: Why Kaspa Dollar and DigiDollar Signal a Healthier Future for Crypto"): 403, not read.
5.2 Criticism: the only specific critique found is the oracle-decentralisation concern (miner price votes while 2-3 pools produce most blocks), reported secondhand 2026-11-10 (Shawnz via KuCoin, URL in F7). No scam allegations about KaspaDollar found. Searches also surfaced unrelated Kaspa-fraud items (TradeOgre) not about this project.
5.3 No coverage by kaspa.org or other official Kaspa channels found. Search is limited to a US search engine; Reddit r/kaspa, Telegram, Discord, Kaspa forum content was not found/reachable.

## 6. Red flags / observations (facts, not conclusions)

- Whole-team claim "rest of the Kaspa core team" is unverified; only one named supporter (Sutton), from secondhand reports.
- One named developer; fundraising address custody structure undisclosed; 72% of funds unitemised.
- A single 200,000 KAS receipt is about 31% of the total; contributor concentration is high, and fundraising is only about 12.8% of target 6 weeks in.
- Fee flows from an unofficial meme token (KDOLLAR) are said to go to an initiative wallet; unverified which wallet.
- Positives: KIP-16 authorship verified from the official KIPs repo; funds unspent per chain; counter matches chain; refund terms published; domain on Cloudflare registrar with consistent infra.

## 7. Not verified / could not access

- x.com/KaspaDollar and x.com/asaefstroem profiles (HTTP 402): creation date, followers, history, authenticity.
- Wayback snapshots/CDX (HTTP 429): site history, earlier raised amounts/claims, removals.
- Domain registrant identity (redacted); WHOIS CLI not used.
- Official Kaspa channels (Discord/Telegram/Reddit/forum) statements; kaspa.org mentions.
- Michael Sutton's actual X post and Medium post (only secondhand text).
- Whether the collection address is also the meme-token fee wallet; any address labels on kaspa.stream; whether 200,000 KAS and other large inputs are insider-linked.
- Whitepaper contents (other agents' scope); whitepaper email address not re-verified.
- Lookalike/fake-fundraiser scan limited to six DNS guesses.
