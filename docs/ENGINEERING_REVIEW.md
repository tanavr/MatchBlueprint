# Engineering review — 16 October 2026

Reviewed the repository at `28014fa` and the cleanup built on it. The application
is a usable local historical-data demo. Its separation of providers, analytics,
services and routes should be retained. This review does not establish forecasting
accuracy or certify a public deployment.

## Findings and priority

Severity reflects impact on this application's data integrity and operation, not
just how much code could be improved. Inspection preceded implementation. The
security dependency findings below were added after the advisory audit completed.

### CRITICAL

None identified in the reviewed code. This is not a penetration-test guarantee.

### HIGH — fixed

| Finding | Impact before cleanup | Resolution |
| --- | --- | --- |
| H1: Incomplete prepared-snapshot validation | A malformed local artifact could mix real/sample provenance, duplicate profile match IDs, include unknown coverage IDs or inconsistent/non-finite metrics. These could be served as raw statistics or fail later in scoring/serialization. Cached goal totals could disagree with the match scores used by simulation. | Validate provenance across catalog, matches, teams and profiles; match and event references; metric names, units, finite totals, status and coverage; and goal metrics against saved scores before serving. Added regression tests. |
| H2: Explicit coverage overridden by automatic snapshot | `create_app(coverage=[])` could load the local snapshot and activate its coverage instead, making behavior depend on developer-local files and disregarding caller configuration. | Automatic snapshot loading now requires that coverage was not explicitly supplied. Tested with a real temporary snapshot file and explicit empty coverage. |
| H3: Old Python environment retained vulnerable dependencies | The Python 3.9 environment's audit reported 25 advisories across 9 packages, including runtime AnyIO/Starlette and development/installation/audit tooling. Not all advisory paths are exercised by this read-only app, but leaving the environment unchanged prevents installation of several patched releases. | Require Python 3.12+, rebuild the local environment on installed Python 3.13, set patched Starlette/AnyIO/pytest/setuptools floors and audit again. The rebuilt environment has no known advisories at review time. |

Snapshot validation checks internal consistency. It cannot authenticate maliciously
rewritten data where every field has been changed consistently. Snapshots remain
trusted local build artifacts, not user uploads. Event-based numbers are not all
recomputed at startup; source annotation accuracy is still an external assumption.

### MEDIUM

| Finding | Status / next action |
| --- | --- |
| Missing lint and automated quality gates | Fixed: ESLint 10 with JavaScript, React Hooks and React key checks; Ruff checks for Python syntax/import/undefined-name problems; GitHub Actions runs both test suites, lint and build. Hosted workflow execution remains to be confirmed after pushing. |
| Documentation contradicted working behavior | Fixed the claims that the frontend was unintegrated and no derived-profile cache existed; documented partial chart fallback, new validation and Python requirements. |
| Frontend tests only cover display helpers | Still open. Eight tests cover comparison availability and simulation probabilities, but there are no automated React/browser tests for dependent selectors, cancellation, retry, keyboard navigation or mobile layout. Add interaction tests before substantial UI changes. |
| Statistical model has no predictive evaluation | Still open by design. Test symmetry, probability totals and formulas do not establish calibration. Backtest chronologically against simple baselines before claiming predictive accuracy. Do not silently change the model during a reliability refactor. |
| Manual-coverage serving recalculates events | Still open. Prepared mode is fast, but the older manual mode loads and aggregates whole cohorts per request. Large seasons or concurrent requests can consume substantial CPU and memory. Prefer prepared mode for hosting; measure before adding another cache. |
| No application-level browser request timeout or error boundary | Still open. Requests cancel on selection change/unmount and failures show errors, but an indefinitely pending fetch can leave a loading state. Unexpected render failures have no page-level fallback. Add bounded requests and a recoverable boundary with interaction tests. |
| Type safety is incomplete | Still open. Pydantic validates API records and Python functions are mostly annotated, but there is no full mypy/Pyright check; React uses JavaScript and most responses rely on the server contract. Ruff is not a type checker. Start with service/analytics checking rather than a wholesale TypeScript conversion. |
| Reproducibility and deployment preparation | Still open. npm has a lockfile; Python uses compatible dependency ranges rather than a complete lock. The upstream data branch moves, although downloaded content hashes are retained. Pin a source revision and tested Python dependency resolution for a reproducible deployment. Review StatsBomb attribution/logo terms before publishing. |

### LOW

- `Compare` and `Simulate` duplicate some request-state/cancellation code. Their team
  selector is already shared. A small shared request hook may help later; the
  current duplication does not justify rewriting working pages.
- JSX is often compressed onto long lines; Python test annotations are uneven.
  Formatting only the touched preparation tests kept this cleanup focused.
- About Model's displayed version and explanatory copy are maintained separately
  from backend model constants; keep them synchronized when the model changes.
- Some secondary text is 10px. It merits a readability/contrast pass on phones.
- The current Starlette TestClient emits one deprecation warning about its httpx
  integration. Tests pass; migration to httpx2 remains separate work, including
  updating transport-mocking assumptions. The warning has not been suppressed.
- The comparison bundle is about 419 kB uncompressed / 118 kB gzip. It is already
  lazy-loaded; measure user experience before changing chart libraries.

## Coverage of the review

| Area | Assessment |
| --- | --- |
| Architecture / Python organization | Provider interface and canonical models separate retrieval from pure analytics; services coordinate routes. Snapshot artifact validation may reuse pure metrics, without network access. No architecture rewrite needed. |
| React organization / duplication | Pages, reusable selectors, results, chart components and centralized API client are separated. Compare/Simulate request lifecycles are similar but small. |
| API design / errors | Scoped competition-season IDs avoid ambiguous teams and seasons; Pydantic responses and 404/409/422/502/503 mappings are consistent. Provider errors are sanitized. Unexpected errors remain server errors rather than false successes. |
| Analytics correctness | Reviewed weighted numerator/denominator aggregation, missing-data exclusion, signed progression, possession grouping, percentile ties, constant cohorts, common-match requirements and rule thresholds. Existing tests cover these; the cleanup fixes artifact validation rather than changing formulas. |
| Statistical assumptions | Scores describe relative style, not absolute team quality. Possession/pressing are proxies. The Poisson baseline is deterministic with bounded truncation and swap symmetry; it omits home advantage, lineup, dependence, shrinkage and calibrated league-strength adjustments. These limits remain documented. |
| Test quality | Baseline 200 offline backend cases; final 215, including 15 new snapshot/configuration regressions. Twelve new regressions were first run against old behavior and failed, then passed after fixes. Synthetic tests are independent of downloaded data. |
| Security | Fixed dependency findings; inspected fixed upstream URL construction, identifier restrictions, cache hashes, error sanitization, read-only API and limited localhost CORS. No SQL, user file uploads or dynamic HTML injection in current routes/UI. This is not an exhaustive secret-history scan or deployed penetration test. |
| Performance | Prepared profiles avoid per-request event processing. In-process real-data checks covered metrics, tactics, comparison and simulation for all 20 clubs (80 successful requests); mean 1.5 ms, max 2.7 ms on this machine after upgrade. These measurements exclude browser/network latency and concurrency, and are not a production benchmark. |
| Accessibility | Source inspection found native labeled selects, fieldset/legend pairs, semantic tables, skip link, focus styling, loading/error roles and textual chart equivalents. The running desktop page exposed its controls in the browser accessibility tree. Full screen-reader, contrast and keyboard-flow audits remain open. |
| Responsive design | Inspected breakpoint layouts, wrapping, responsive chart containers and horizontally scrolling tables. No new mobile visual/interaction audit was completed in this review; verify 390px and tablet layouts manually before release. |
| Documentation / ignored files | Updated stale descriptions and startup requirements. Raw cache, prepared snapshot, active environment, retained old environment, npm dependencies and build output are ignored. No such artifacts are staged in the cleanup. |

## Verification

On the rebuilt Python 3.13 environment:

- `python -m pytest -q`: **215 passed**, no skipped tests; one TestClient deprecation warning.
- `python -m ruff check app tests`: passed.
- `python -m compileall -q app`: passed.
- `python -m pip check`: passed.
- `python -m pip_audit`: no known vulnerabilities; the local project itself is not
  a published package and has no external advisory record.
- `npm test`: **8 passed**, no skipped tests.
- `npm run lint`: passed with zero warnings.
- `npm run build`: passed.
- `npm audit --audit-level=low`: zero vulnerabilities.
- `git diff --check`: passed.
- Real prepared Premier League snapshot still loads under the stricter validation;
  all 80 real-data API smoke requests return 200.

Initial failures were not hidden: 12 new regression cases failed before their fixes;
Ruff initially found 19 one-line-statement issues in the preparation tests, resolved
by formatting that file. The initial Python 3.9 compile check could not write to
macOS's external bytecode-cache directory; it passed with a writable cache path,
and subsequently passed normally in the rebuilt environment. The original advisory
audit failed with 25 findings; the final audit has none. No tests were deleted,
skipped or marked expected failures to obtain a green result.

The old `.venv-python39/` files are retained locally and ignored; the supported
active environment is `backend/.venv/`. The local backend was restarted on port
8000 with the new environment. No data refresh, score-formula change, deployment or
GitHub push is part of this cleanup commit.
