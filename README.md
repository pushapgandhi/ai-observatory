# AI Observatory

[Live website](https://pushapgandhi.github.io/ai-observatory/)

A source-linked AI timeline from 2021 onward, with year/month filters, search, research/model/news filters, and weekly updates. Static HTML/CSS/JavaScript runs on GitHub Pages without API keys or a paid backend.

## Local preview

```sh
python -m http.server 4173 --directory dist --bind 127.0.0.1
```

Open http://127.0.0.1:4173. Test with `python -m unittest discover -s tests -v` and `node --check dist/app.js`.

## Weekly updates

The GitHub Actions workflow runs Mondays at 10:17 UTC, on pushes to main, and via **Actions → Weekly AI update and publish → Run workflow**. It fetches public sources, validates the archive, commits data, and publishes `dist` to Pages. GitHub may delay scheduled runs. Public repository schedules may be disabled after 60 days of inactivity; check the Actions tab if source checks become overdue.

Publisher feeds: OpenAI News, Google AI, Google DeepMind, plus up to 60 newest arXiv papers from cs.AI/cs.CL/cs.LG/cs.CV submitted in the preceding 14 days. This is a selective research feed, not an exhaustive literature database. Publisher feed history varies; curated milestones supplement earlier years. Dates are original publication dates, not ingestion dates. Imported entries are labeled and contain only a short publisher excerpt. This archive does not assess scientific validity or independently verify company benchmark claims.

The updater preserves curated summaries and historical records, canonicalizes URLs, rejects invalid/future dates and unsafe links, and writes atomically. Retries are bounded. If a source fails, the existing archive and failure status still deploy; the workflow then reports failure. The website also warns if source checks are more than nine days old. `lastChecked` records an attempt, not guaranteed success for every feed; `lastSuccessfulRefresh` records full success.

Edit historical entries in `scripts/seed.py` and run `python scripts/seed.py`; update feed parsing in `scripts/update.py`. Do not replace historical data with a single week's results.

## Publishing setup

Repository **Settings → Pages → Source: GitHub Actions**. The workflow needs repository contents write permission plus Pages/id-token permissions. Only `dist` is published. No personal documents or credentials are included.
