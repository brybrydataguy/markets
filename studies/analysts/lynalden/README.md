# Lyn Alden research audit

A retrospective review of **200 member reports and 6,285 material claim occurrences**, evaluated as of **November 7, 2026**. Each article has its own review, with the claims, original horizons, qualifications, outcome evidence, and verdicts kept together.

Start with [the overall summary](SUMMARY.md), [the best and worst takes](BEST-AND-WORST.md), or [the practical thinking framework](FRAMEWORK.md).

| Read | What it contains |
| --- | --- |
| [Overall summary](SUMMARY.md) | Strengths, weaknesses, major episodes, and coverage |
| [Best and worst takes](BEST-AND-WORST.md) | Standout successes and misses, plus the most repeated points |
| [How Lyn thinks](FRAMEWORK.md) | Recurring views, ten questions to ask, and worked examples |
| [Tools and charts](TOOLS-AND-CHARTS.md) | Recurring chart families, interpretations, limitations, and glossary |
| [Article index](articles/README.md) | One review for each of the 200 articles |
| [Methodology](METHODOLOGY.md) | Materiality, evidence standards, source provenance, and scoring rules |
| [Structured data](data/) | Complete review records, synthesis, source metadata, and chart notes |
| [Searchable report](report/index.html) | Interactive local library with search, filters, and claim links |

## Open the searchable report

GitHub displays HTML source rather than running this report. Clone or download the repository, then open `studies/analysts/lynalden/report/index.html` in your browser. The report is self-contained and works offline; external evidence and member-article links require internet access and sometimes a subscription.

Alternatively, from the repository root:

```sh
python3 -m http.server 8000 --bind 127.0.0.1 --directory studies/analysts/lynalden/report
```

Open `http://127.0.0.1:8000/`. No Lavish session or other application is required.

## Interpret the scorecard

| Verdict | Claim occurrences |
| --- | ---: |
| Right | 1,402 |
| Wrong | 327 |
| Mixed | 2,011 |
| Not testable | 1,405 |
| Too early | 286 |
| Conditional pending | 139 |
| Evidence needed | 715 |
| **Total** | **6,285** |

All 200 articles have reviews. This does **not** mean every claim has a verified outcome: 715 still require evidence. Repeated theses are not independent forecasts, and explanatory claims, conditional scenarios, investment returns, and dated forecasts should not be combined into one accuracy percentage.

The source webpages were captured on November 7, 2026. Their original publication-date wording was not independently authenticated. Return comparisons are disclosed observational tests, not a reconstruction of an actual portfolio.

## Contents and provenance

This repository contains the analysis, paraphrased claims, source references, and chart-reading notes. Full member-only article snapshots, copied chart images, browser data, and temporary working files remain outside the repository. Source block numbers and hashes preserve references to the original local audit; they are not excerpts of the source text.

Spelling and spacing corrections were applied to the analysis before publication. Verdicts, numerical values, dates, and evidence URLs were preserved.

## Rebuild and validate

Python 3.9 or later is sufficient; the build uses only the standard library. Run from this directory:

```sh
python3 scripts/build_report.py
python3 scripts/build_markdown.py
python3 scripts/validate.py
```

Edit the canonical JSON records under `data/` and rebuild the generated Markdown and HTML. `README.md` and `BEST-AND-WORST.md` are authored documents. The validator checks coverage, claim identifiers, source references, evidence requirements, verdict counts, links, and publication hygiene.
