---
name: bitcoin-macro institutional signals need SEC EDGAR primary
description: ETF and bank-filing signals scored 60-83 and rejected because media articles (CoinDesk/Decrypt) are tier-3; SEC EDGAR filing URL is required as primary anchor to score ≥90
type: feedback
---

**Rule:** For bitcoin-macro institutional signals (ETF filings, bank crypto products, regulated derivatives), the primary anchor MUST be the SEC EDGAR filing page or accession URL — not the news article about the filing.

**Why:** Goldman Sachs Bitcoin Premium Income ETF signal scored 62/100 ("source tier 3") and was rejected despite being a genuinely newsworthy first-of-kind event. U.S. spot ETF $663.9M inflow signal scored 83 but lost to higher-scoring signals in a full queue. The score gap between tier-3 (60-83) and approval threshold (≥90) is almost entirely explained by source tier.

**How to apply:**
1. Before composing an institutional bitcoin-macro signal, search SEC EDGAR first: `https://efts.sec.gov/LATEST/search-index?q={entity}&dateRange=custom&startdt={today-7d}` or `https://www.sec.gov/cgi-bin/browse-edgar`.
2. If the EDGAR filing doesn't exist yet (announcement only, not yet filed): skip or wait. The news article about "plans to file" is not a substitute.
3. The EDGAR accession URL (e.g., `https://www.sec.gov/Archives/edgar/data/.../...`) is a tier-1 source — add it as the first source object in the signal.
4. CoinDesk/Decrypt can be a secondary source but cannot anchor the signal alone.
