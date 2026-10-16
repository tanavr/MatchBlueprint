# Real-data demo

The default prepared demo is the men's Premier League **2015/2016** from
[StatsBomb Open Data](https://github.com/statsbomb/open-data): 20 clubs,
380 matches, 38 matches per club. Arsenal, Liverpool, Leicester City and
Manchester City are actual source teams, not fixtures. This is historical data,
not a live scores service. Liverpool 2019/20 is not included.

## Prepare once

From `backend/`, with dependencies installed:

```sh
.venv/bin/python -m app.data.prepare_demo
```

Preparation downloads public files with four workers and up to three attempts,
reuses the local cache, normalizes records, checks coverage, and calculates the
existing raw metrics for each team. Allow several minutes and approximately 1 GB
of disk space. No commercial account or credentials are required.

The configured 20-club, home-and-away format is supported by the Premier League's
[format description](https://www.premierleague.com/en/premier-league-explained) and
[2015/16 club report](https://www.premierleague.com/ar/news/60138/premier-leagues-payments-to-clubs-in-201516).
Preparation verifies each ordered home/away pairing occurs exactly once, all final
scores exist, and every event feed includes both teams' start/end records for both
halves, reaches 90 minutes, and reconciles scored goals (including own goals) with
the final result. Duplicate event IDs/indices are rejected by the adapter.
These structural checks establish operational coverage; they cannot prove that
source annotation contains no omissions or errors.

An atomic snapshot, `data/prepared.json`, contains source catalog records, matches,
coverage hashes and calculated profiles. Both it and raw downloads are gitignored.
The server loads this snapshot at startup and uses the existing scoring/comparison/
simulation engines. It serves only prepared competitions and seasons; it never
makes network calls to satisfy a browser request. Re-run preparation and restart
the backend after changing metric formulas or replacing cached source files.
An unsuccessful preparation leaves the previous snapshot intact. The snapshot is
a trusted local build artifact, not an input to accept from anonymous uploaders.
Schema, version, scope and roster consistency are checked when loading it; raw
files are not reprocessed on every request. Original source hashes and retrieval
timestamps remain in the profiles for auditability.

The command defaults are demo configuration, not hardcoded analytics logic.
Other **complete double-round-robin** leagues can be added with `--competition`,
`--season`, and `--expected-teams`. Verify their format independently first.
Existing prepared seasons are retained. This command deliberately rejects partial
single-club archives, tournaments, and other formats. The underlying provider can
still retrieve those datasets separately. `FOOTBALL_PREPARED_PATH` selects an
alternative snapshot; explicit `FOOTBALL_COVERAGE_PATH` retains legacy manual mode.

## Start and check

Backend, from `backend/`:

```sh
.venv/bin/python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend, from `frontend/`:

```sh
npm run dev
```

Open http://localhost:5173. Stop any old `create_demo_app --factory` backend first;
it is the deliberately tiny test fixture, not the real app.
The banner should show Premier League 2015/2016, 20 clubs and 380 matches.
Select Arsenal for Analyze; compare Arsenal with Leicester City; then simulate
Liverpool against Manchester City. `GET /dataset` reports the loaded scopes.

## Interpretation and attribution

Scoring thresholds and formulas are unchanged. All ranks are relative to the
20-club season; they are not contemporary ratings. Metrics can remain unavailable
when source fields fail their documented requirements. Possession and pressing
are event-based proxies, not tracking measurements. The Poisson simulator remains
an uncalibrated neutral-venue hypothetical, not a guaranteed prediction.

The initial prepared dataset supports comparisons within one season. Cross-season
code remains available, but additional seasons must be prepared before they can be
selected. Raw files use a moving upstream branch; saved SHA-256 hashes identify
the actual downloaded content. Reusing the cache preserves that local snapshot.

Data credit: StatsBomb Open Data. Follow the upstream
[README](https://github.com/statsbomb/open-data#readme) and
[license](https://github.com/statsbomb/open-data/blob/master/LICENSE.pdf), including
attribution and logo requirements when sharing analysis. Raw data is not committed.

In this snapshot, unknown pass outcomes exclude many matches from the strict
completion metric, and inconsistent within-possession counter tags exclude some
counter metrics. These can prevent passing/control and counterattacking scores
from meeting the unchanged coverage thresholds. The comparison shows a grouped
0–100 bar chart of supported dimensions when the seven-axis radar is unavailable.
It never fills missing values with zero or relaxes statistical eligibility.
