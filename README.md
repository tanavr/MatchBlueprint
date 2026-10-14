# Football Tactical Analyzer

Analyze, compare, and simulate football teams across seasons.

The current scaffold includes a React landing page and a FastAPI backend with
`GET /health`. Analyze Team, Compare Teams, and Match Simulator are placeholders.
The website does not display football data, analytics, or simulation results yet.

The backend now includes a modular data layer for public StatsBomb JSON and a
synthetic offline fixture provider. API endpoints expose discovery and analytics;
the frontend remains a landing page.
See [DATA.md](docs/DATA.md) for usage, available competitions/seasons, caching, and
coverage limitations. Downloaded data stays in the ignored `data/cache/` directory.

The raw `TeamSeasonMetrics` engine summarizes supplied match/event records in Python.
See [METRICS.md](docs/METRICS.md) for formulas, usage, and missing-data rules. It does
not itself assign tactical scores or labels and is not connected to the website.

The separate `TacticalStyleModel` now ranks these metrics within a sufficiently
covered competition-season cohort and produces rule-based descriptions. See
[TACTICAL_MODEL.md](docs/TACTICAL_MODEL.md) for formulas, usage, synthetic examples,
and proxy limitations. This scoring layer is also not connected to the website yet.

See [API.md](docs/API.md) for the discovery, metrics, and tactical-profile endpoints,
error formats, and coverage review configuration. The default API reads cached data
only. Prepare the catalog separately with `python -m app.data.prepare` from the
activated backend environment; requesting uncached data returns 503. Event metrics
need reviewed feed coverage, and tactical scoring also needs reviewed roster counts.
For an offline sample API, run `python -m uvicorn app.main:create_demo_app --factory`.

## Requirements

- Python 3.9 or newer (Python 3.12+ recommended for new installations)
- Node.js 20.19+ or 22.12+ (Node.js 24 works) and npm
- Two terminal windows, both starting in the repository root

## Run locally

### Backend — terminal 1

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

On Windows, activate with `.venv\Scripts\activate` instead. On subsequent runs,
activate the existing environment and run the Uvicorn command; installation is only
needed after dependency changes.

- Health: <http://127.0.0.1:8000/health> — returns `{"status":"healthy"}`
- Interactive API documentation: <http://127.0.0.1:8000/docs>

### Frontend — terminal 2

```bash
cd frontend
npm ci
npm run dev
```

Open <http://localhost:5173>. On subsequent runs, use `npm run dev`; rerun `npm ci`
after dependency changes. The landing page does not call the backend yet.

The API permits browser requests from `http://localhost:5173` and
`http://127.0.0.1:5173`, following FastAPI's [CORS configuration](https://fastapi.tiangolo.com/tutorial/cors/).
Vite uses port 5173 with `strictPort`, so it will report an error instead of switching
to an origin the backend does not allow. If that port is busy, stop the other server.
Production origins will need separate configuration before deployment.

Use Ctrl+C in each terminal to stop its server. No API keys or `.env` files are needed.

## Checks

From the repository root, after installing dependencies:

```bash
cd backend
source .venv/bin/activate
python -m pytest
python -m pip check
```

In a separate terminal, from the repository root:

```bash
cd frontend
npm run build
```

The build writes ignored files to `frontend/dist/`. Run `npm run preview` from
`frontend/` to inspect that build at the URL printed in the terminal. The preview
server is separate from the port-5173 development server.

## Project layout

```text
backend/
  app/
    main.py       FastAPI application and local CORS configuration
    api/          HTTP routes and error mapping
    services/     Provider and analytics orchestration
    analytics/    Raw metrics, tactical scores, comparisons, and simulation
    data/         Provider interface, StatsBomb adapter, cache, and fixtures
    models/       Pydantic schemas
  tests/          Provider, analytics, API, health, and CORS tests
  pyproject.toml  Python dependencies and pytest configuration
frontend/
  src/            Dashboard pages, reusable components, API client, and styles
  package.json    Frontend dependencies and commands
docs/             Architecture and metric plans
```

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for the planned design and
[CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines. Frontend setup uses
[Vite](https://vite.dev/guide/). Analytics and chart dependencies will be added when
those features are implemented.

Cross-season comparisons are available through `GET /compare`. See
[API.md](docs/API.md) for request parameters and coverage requirements, and
[COMPARISON.md](docs/COMPARISON.md) for normalization and interpretation rules.

Hypothetical neutral-venue matchups are available through `GET /simulate`.
See [SIMULATION.md](docs/SIMULATION.md) for the Poisson model and evidence requirements.


## Analyze dashboard

With the backend running on port 8000, start the frontend from a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173, then choose a competition, season, and team and click
**Analyze team**. Results come from FastAPI; the frontend never substitutes invented
analytics. The default backend needs locally prepared data and reviewed coverage;
see [API.md](docs/API.md). A missing cache produces an explanatory error.

For an offline sample walkthrough, run this instead of the normal backend:

```bash
cd backend
source .venv/bin/activate
python -m uvicorn app.main:create_demo_app --factory --host 127.0.0.1 --port 8000
```

Choose **Sample League → Sample Season → Sample North**. Expect a sample-data
badge, goals for/against, unavailable event statistics, and a tactical-coverage
message. This deliberately tiny fixture cannot produce a scored tactical identity.
A complete numeric report requires a prepared, reviewed season meeting scoring
thresholds; coverage must not be invented to make a demo look complete.

The frontend API client defaults to http://127.0.0.1:8000. To use another local port:
`VITE_API_BASE_URL=http://127.0.0.1:8001 npm run dev` from `frontend/`.
Vite variables are public configuration, never secrets. Restart Vite after changes.
The backend permits the existing localhost and 127.0.0.1 frontend origins on 5173.

Analyze and About Model are implemented. Compare and Simulate navigation currently
shows clearly labeled planned interfaces. See [DASHBOARD.md](docs/DASHBOARD.md) for
component organization and a manual verification checklist.
