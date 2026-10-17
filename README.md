# MatchBlueprint

MatchBlueprint turns football match events into season-level statistics, interpretable tactical profiles, and probabilistic matchup estimates. Its Python analytics engine powers a React dashboard for exploring how teams play and comparing their styles.

**Current demo:** men's Premier League 2015/16 — 20 clubs, 380 matches, and 38 matches per club, using StatsBomb Open Data. Additional seasons require preparation; the demo does not currently offer other seasons or live scores.

## Key features

- **Team analysis:** goals, shots, shot-based xG, passing, defensive activity and possession-related metrics, with per-metric coverage.
- **Tactical profiles:** seven scoring dimensions based on competition-season percentile ranks, with rule-based identities and explanations.
- **Team comparison:** raw differences, normalized style differences, charts, similarities and matchup observations. The engine supports different seasons; the prepared demo currently contains one.
- **Match simulation:** estimated goals, win/draw/loss probabilities and likely scorelines from an analytical Poisson model.
- **Reproducible data preparation:** replaceable providers, local caching, source hashes, coverage checks and prepared metric snapshots. API requests do not download or reprocess raw event files.

## Screenshots

Screenshots will be added for these views:

| View | What it shows |
| --- | --- |
| Analyze | Team statistics, tactical identity and dimension scores |
| Compare | Side-by-side styles, comparison chart and metric tables |
| Simulate | Expected goals, outcome probabilities and likely scorelines |

## Architecture

```text
StatsBomb public JSON
        ↓
Collection + cache → provider normalization → validated match/event models
        ↓
Team-season metrics → prepared local snapshot
        ↓
Service layer → tactical scoring / comparison / simulation
        ↓
FastAPI → React dashboard
```

Collection is separate from serving requests. Analytics functions accept typed records and perform no network calls; routes validate requests and delegate to the service layer. The provider interface allows another dataset to be added without replacing the scoring engine.

```text
backend/app/
  data/        Provider contract, StatsBomb adapter and preparation commands
  models/      Pydantic data and response schemas
  analytics/   Raw metrics, percentile scoring, comparison and Poisson simulation
  services/    Data selection, coverage checks and analytics orchestration
  api/         REST endpoints and error responses
backend/tests/ Synthetic fixtures, analytics tests and API tests
frontend/src/  React pages, reusable components, charts and API client
data/          Local downloads and prepared profiles; excluded from Git
docs/          Formulas, data contracts and engineering review
```

For a code walkthrough, start with [team_season.py](backend/app/analytics/team_season.py), [tactical.py](backend/app/analytics/tactical.py), [simulation.py](backend/app/analytics/simulation.py), then [football.py](backend/app/services/football.py).

## Technology stack

| Layer | Technologies |
| --- | --- |
| Analytics | Python; standard-library numerical functions for aggregation, ranks and probability calculations |
| API and validation | FastAPI, Pydantic, Uvicorn |
| Data retrieval | HTTPX, public StatsBomb JSON, filesystem cache |
| Frontend | React, JavaScript, Vite, Recharts |
| Verification | pytest, FastAPI TestClient, Node test runner, Ruff, ESLint, GitHub Actions |

The current model uses explicit statistical formulas; it does not require a trained ML model, an LLM service, pandas or SciPy.

## Tactical scoring

Raw rates use accumulated totals and their appropriate denominators. Missing fields exclude affected observations rather than being counted as zero. Each metric records which matches contributed to it.

For an eligible team, a component score is its average-rank percentile within the competition-season:

```text
percentile = 100 × (rank − 1) / (number of eligible teams − 1)
```

Ties share ranks. Multi-component dimensions average their percentiles with equal weights and require matching observation sets.

| Dimension | Underlying metrics |
| --- | --- |
| Possession | Share of both teams' attempted passes |
| Pressing | Advanced defensive actions as a share of defensive actions |
| Directness | Average pass distance and signed forward progression per pass |
| Attacking intensity | Shots and attacking-third activity per match |
| Defensive activity | Defensive actions per match |
| Counterattacking tendency | Share of possessions tagged as counters by the source |
| Passing/control | Pass completion and passes per possession |

Default eligibility requires at least 10 matches per team, 10 eligible teams, and 80% coverage of expected matches and the season roster. Explicit rules assign identities from prominent traits, including upper-quartile scores. Scores measure relative style, not overall team quality.

Possession and pressing are **proxies**, not direct measurements of possession time or pressure. In the prepared dataset, incomplete pass outcomes and inconsistent counter tags can make some dimensions unavailable. The comparison displays supported dimensions without filling missing values with zero.

Formulas and rules: [METRICS.md](docs/METRICS.md), [TACTICAL_MODEL.md](docs/TACTICAL_MODEL.md), [COMPARISON.md](docs/COMPARISON.md).

## Match simulation

For each team's season, let `g` be average goals per team-match:

```text
attack ratio     = goals scored per match / g
concession ratio = goals conceded per match / g
shared baseline  = (g_A + g_B) / 2

expected goals A = shared baseline × attack ratio A × concession ratio B
expected goals B = shared baseline × attack ratio B × concession ratio A
```

Independent Poisson distributions turn these estimates into scoreline probabilities. Summing scorelines where A wins, the teams draw, or B wins produces the three outcome probabilities. The computation is analytical and deterministic, with omitted probability mass bounded by 1e-8.

The simulator's expected goals are model scoring averages, distinct from the shot-based xG reported in team analysis. It assumes a neutral venue and uses season scoring rates, not tactical scores as arbitrary probability multipliers. See [SIMULATION.md](docs/SIMULATION.md) for the derivation.

## Data source and attribution

Match and event data is provided by **[StatsBomb Open Data](https://github.com/statsbomb/open-data)**. Preparation checks the complete home-and-away schedule, final scores, event half boundaries and agreement between event goals and match results, while retaining source URLs, retrieval timestamps and content hashes.

No commercial credentials or API keys are needed. Raw downloads and prepared profiles are excluded from Git; a fresh clone downloads and prepares them locally. Synthetic fixtures are used only for offline tests and explicitly labeled sample mode.

StatsBomb data has its own [license](https://github.com/statsbomb/open-data/blob/master/LICENSE.pdf). Follow its [attribution and logo requirements](https://github.com/statsbomb/open-data#terms--conditions) when sharing analyses; official assets are linked from the [media pack](https://statsbomb.com/media-pack/).

See [REAL_DATA.md](docs/REAL_DATA.md) for preparation checks and [DATA.md](docs/DATA.md) for the provider contract and source limitations.

## Limitations

- The demo covers one historical season. A competition's presence in the open-data catalog does not guarantee a full league schedule.
- Percentiles compare teams within their own season. Cross-season comparisons do not establish absolute league or era strength.
- Event-derived activity cannot establish tactical intent, defensive block height or continuous off-ball movement.
- Simulation omits home advantage, injuries, lineups and goal dependence. It has not been calibrated or backtested as a forecasting product.
- Passing/control and counterattack scores may be unavailable where source coverage fails the thresholds. Structural validation cannot prove that every source annotation is correct.

## Local setup

Requirements: **Python 3.12+** (tested on 3.13), **Node.js 20.19+ or 22.12+** (tested on 24), and npm. No `.env` file is required.

Clone the repository:

```bash
git clone https://github.com/tanavr/football-tactical-analyzer.git
cd football-tactical-analyzer
```

In the first terminal:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
python -m app.data.prepare_demo
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Check `python3 --version` first; use `python3.13` or `python3.12` if the default is older. On Windows, create the environment with a supported Python installation and activate it with `.venv\Scripts\activate` in Command Prompt.

Preparation takes several minutes and approximately 1.2 GB of cache storage. It is only needed initially, when adding a dataset, or after changes that require rebuilding metrics. Subsequent starts need only environment activation and the Uvicorn command. Existing Python 3.9 virtual environments must be recreated.

In a second terminal, starting from the repository root:

```bash
cd frontend
npm ci
npm run dev
```

Open **http://localhost:5173**. Try analyzing Arsenal, comparing Arsenal with Leicester City, or simulating Liverpool against Manchester City. Select Premier League and 2015/2016 for each team.

The API runs at http://127.0.0.1:8000, with interactive documentation at http://127.0.0.1:8000/docs. CORS allows localhost and 127.0.0.1 on frontend port 5173. Stop an existing server if that port is occupied. Stop each development server with Ctrl+C.

To use a different backend port, set `VITE_API_BASE_URL` when starting Vite, for example `VITE_API_BASE_URL=http://127.0.0.1:8001 npm run dev`. The variable is public configuration, not a secret. Use `app.main:app` for real data; `create_demo_app` is the small synthetic fixture factory.

## API overview

All routes below use `GET`:

| Route | Returns |
| --- | --- |
| `/health` | Service health |
| `/dataset` | Prepared competitions, seasons and match/team counts |
| `/competitions` | Available competitions |
| `/competitions/{competition}/seasons` | Seasons in a competition |
| `/competitions/{competition}/seasons/{season}/teams` | Available teams |
| `/competitions/{competition}/seasons/{season}/teams/{team}/metrics` | Raw season metrics and coverage |
| `/competitions/{competition}/seasons/{season}/teams/{team}/tactical-profile` | Scores, identity and explanation |
| `/compare` | Differences and stylistic comparison |
| `/simulate` | Expected goals, outcome probabilities and scorelines |

Compare and simulate require `competition_a`, `season_a`, `team_a`, `competition_b`, `season_b`, and `team_b`. IDs are namespaced, such as `statsbomb:competition:2`, `statsbomb:season:27`, and `statsbomb:team:1` for Arsenal. Response models, examples and errors are documented in [API.md](docs/API.md).

## Testing and quality checks

Backend, from `backend/` with the environment activated:

```bash
python -m pytest
python -m ruff check app tests
python -m compileall -q app
python -m pip check
```

Frontend, from `frontend/`:

```bash
npm test
npm run lint
npm run build
```

The current suite contains **215 backend tests and 8 frontend helper tests**. Backend tests use synthetic fixtures and block external HTTP; no downloaded dataset is required. Tests cover metric denominators, missing data, percentile ranks, normalization boundaries, Poisson probability invariants, API behavior and prepared-data validation.

GitHub Actions runs tests, lint and the frontend build on pushes and pull requests. Dependency audits require network access: run `python -m pip_audit` in the backend environment and `npm audit` in the frontend directory. The engineering review documents the remaining TestClient deprecation warning and testing gaps.

## Future improvements

- Prepare additional complete competition-season datasets and add another provider.
- Evaluate simulation calibration with chronological backtests, then assess home advantage and smoothing.
- Add browser tests for selection flows, cancellation, retries and responsive layouts.
- Complete a screen-reader and contrast audit, and add request timeouts and render-error recovery.
- Pin Python dependencies and upstream data revisions for reproducible deployments.

Further reading: [Architecture](docs/ARCHITECTURE.md) · [Engineering review](docs/ENGINEERING_REVIEW.md) · [Contributing](CONTRIBUTING.md).
