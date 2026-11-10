# Steve Eisman research audit

An episode-by-episode audit of The Real Eisman Playbook, with a claim-level scorecard and a practical guide to his investment framework. Evidence cutoff: November 10, 2026.

Start with the [overall summary](SUMMARY.md), [best and worst material takes](BEST-AND-WORST.md), [repeated points](REPEATED-POINTS.md), or [how Eisman thinks](FRAMEWORK.md). The [tools and charts guide](TOOLS-AND-CHARTS.md) explains the analytical inputs he discusses. Read the [methodology](METHODOLOGY.md) before interpreting verdicts.

The [searchable local report](report/index.html) includes every episode review, source listing, claim, timestamp and evidence citation. Download or clone the repository and open that file in a browser. It works offline for search and navigation; original sources and evidence links require internet access. GitHub displays HTML source rather than running the report.

To serve the report locally:

```sh
python3 -m http.server 8766 --bind 127.0.0.1 --directory studies/analysts/SteveEisman/report
```

Then visit `http://localhost:8766/`. No Lavish session is required. Individual reviews are also readable as Markdown in [episodes](episodes/).

The inventory contains 192 Substack listings and 166 YouTube Videos-tab listings. These 358 listings map to 192 review items: 186 non-excerpt items and six clips. Cross-platform versions and reposts map to canonical review items. The [coverage map](COVERAGE.md) and the report's Coverage tab show every listing and its review. Clips link to their full parent reviews so their claims are not counted twice.

Guest statements remain separate from Eisman's own statements. A repeated thesis is not a new independent win, and a personal position disclosure is not a verified trading record. No aggregate accuracy percentage is reported. Some claims need mixed, unresolved or not-testable labels in addition to right, wrong and too early.

Full transcripts, subscriber source text, audio and local transcription models remain outside this repository. This directory contains original analysis, public source links, source hashes and evidence citations.

To rebuild the portable report and Markdown pages from the public analysis data:

```sh
python3 studies/analysts/SteveEisman/scripts/build_report.py
python3 studies/analysts/SteveEisman/scripts/validate.py --require-complete
```

Edit the JSON analysis or source templates and rebuild generated files. The private-workspace import script is optional and requires access to the original local research workspace; rebuilding the report does not.
