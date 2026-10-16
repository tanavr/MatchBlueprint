# MatchBlueprint

Analyze, compare, and simulate football teams across seasons.

The Analyze, Compare and Simulate dashboards use real StatsBomb Open Data.
The initial demo covers the men's Premier League **2015/2016: 20 clubs and 380 matches**.
Prepare the data once, then run the backend and frontend below. No API keys are needed.
See [REAL_DATA.md](docs/REAL_DATA.md) for coverage checks, limitations and attribution.

## Requirements

- Python 3.12 or newer (development checks run on Python 3.13)
- Node.js 20.19+ or 22.12+ (Node.js 24 works) and npm
- Two terminal windows, both starting in the repository root

## Run locally

### Backend — terminal 1

```bash
cd backend
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
python -m app.data.prepare_demo  # first run only; downloads and prepares real data
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
after dependency changes. All three dashboards call the backend.

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
python -m ruff check app tests
python -m pip check
```

In a separate terminal, from the repository root:

```bash
cd frontend
npm test
npm run lint
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
[Vite](https://vite.dev/guide/). Analytics and chart dependencies are included.

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

Choose **Premier League → 2015/2016 → Arsenal** and analyze. The data banner
should show 20 clubs and 380 matches. If an old backend is running with
`create_demo_app --factory`, stop it and run `app.main:app` instead.
The fixture factory remains available only for synthetic development checks.

The frontend API client defaults to http://127.0.0.1:8000. To use another local port:
`VITE_API_BASE_URL=http://127.0.0.1:8001 npm run dev` from `frontend/`.
Vite variables are public configuration, never secrets. Restart Vite after changes.
The backend permits the existing localhost and 127.0.0.1 frontend origins on 5173.

Analyze, Compare, Simulate, and About Model are implemented. See [DASHBOARD.md](docs/DASHBOARD.md) for
component organization and a manual verification checklist.


## Compare two teams

Open **Compare** and independently select a competition, season and team on each
side, then click **Compare teams**. Results include both identities, a Recharts
radar, category differences, raw/normalized metric tables, similarities, and
matchup observations from the API. The chart always uses seven fixed axes and
0–100; if a dimension cannot be compared, a grouped bar chart shows supported dimensions
and explains the omissions. Raw differences are context,
not cross-league strength estimates.

The prepared Premier League season satisfies coverage requirements. Try Arsenal
against Leicester City; additional seasons must be prepared before selection.
See [DASHBOARD.md](docs/DASHBOARD.md) for comparison verification steps.

Frontend display-rule tests: `npm --prefix frontend test`.


## Run a hypothetical simulation

Open **Simulate**, select both club-seasons, and click **Run Simulation**. The page
uses `GET /simulate` and displays expected goals, win/draw/loss probabilities,
likely scorelines, model inputs, explanations and limitations. Expected goals here
are score-model means, not shot-based xG. The analytical calculation is deterministic;
rerunning unchanged inputs does not introduce new randomness.

Both season score datasets must be complete and independently reviewed, and each
selected team needs at least 10 matches. The prepared real-data demo meets these requirements. No substitute predictions
are invented. See [SIMULATION.md](docs/SIMULATION.md) for the mathematics and
[DASHBOARD.md](docs/DASHBOARD.md) for manual UI checks.

## Engineering checks

The review and remaining improvements are recorded in [ENGINEERING_REVIEW.md](docs/ENGINEERING_REVIEW.md).
Run `python -m pip_audit` in the backend environment and `npm audit` in `frontend/`
to check dependencies against current advisories. These checks require internet access.
The pytest suite itself remains offline.

Existing Python 3.9 environments need to be recreated with Python 3.12 or newer
before reinstalling `backend[dev]`. A virtual environment retains the Python version
that created it; upgrading packages alone does not upgrade Python.
