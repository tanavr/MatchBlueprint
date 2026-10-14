# Tactical analysis dashboard

The React application provides a responsive navy/charcoal workspace with a restrained
green accent, hash navigation, and an integrated Analyze page. About Model explains
the assumptions. Compare and Simulate have explicit planned-interface states; this
stage does not implement their forms or result screens.

## Structure

- `src/api.js`: centralized base URL, path encoding, fetch, abort handling and API errors.
- `src/hooks/useCatalog.js`: competition/season/team discovery and request cancellation.
- `src/components/TeamSelector.jsx`: dependent selectors, submit, discovery retry.
- `src/pages/Analyze.jsx`: analysis request lifecycle, cancellation and partial success.
- `src/components/AnalysisResults.jsx`: source/season header, backend identity,
  explanation, secondary traits and limitations.
- `src/components/TacticalScores.jsx`: seven score bars with numeric text, proxy
  labels, reference cohort size and expandable availability/interpretation details.
- `src/components/MetricGrid.jsx`: raw statistics with units and coverage.
- `src/components/Feedback.jsx`: accessible error/status feedback and retry.
- `src/pages/About.jsx`: plain-language model explanation.
- `src/App.jsx`: navigation shell; `src/styles.css`: responsive layout and styling.

Selection labels and all analytics results come from FastAPI. Frontend constants
only define presentation labels and explanatory copy. No scoring or classification
formulas are implemented in the browser. “Strengths & tendencies” displays the
backend's secondary traits, explicitly as stylistic emphasis rather than quality.
Missing values remain dashes; actual zero values render as zero. Samples are labeled
in selectors and results. Bars use simple CSS with adjacent accessible text, so no
chart dependency is needed. Typography uses Google Fonts with local sans-serif
fallbacks if unavailable.

Changing a competition resets season/team; changing season resets team. Every
selection change cancels in-flight analysis and clears old results. Effect cleanup
cancels obsolete catalog requests. Unmounting the page cancels requests. Metrics and
tactical requests run independently via Promise.allSettled, preserving raw statistics
when scoring lacks coverage, and showing an error instead of fabricated scores.
Retry uses the submitted selection. Empty catalogs and offline connections have
separate visible feedback. Analyze is disabled until selection is complete.

## Manual verification

1. Follow README startup instructions. In sample mode, select Sample League,
   Sample Season and Sample North. Analyze shows a sample badge, known score-based
   rates and missing-data/coverage messages. This is the expected partial-success flow.
2. For a complete report, run the standard app with a locally prepared season and
   independently reviewed coverage manifest as described in API.md. Select a team
   satisfying the cohort and match thresholds. Check the identity, description,
   seven dimensions, raw metrics, backend secondary traits and coverage disclosures.
3. Change the selected team: the old report must disappear until Analyze is clicked.
   Change competition/season and verify dependent selectors reset. Rapidly change
   selections while a response loads; an older response must not reappear.
4. Stop the backend and retry. Expect a readable connection error. Restart and retry
   without refreshing the frontend; the request should recover. An unprepared real
   backend should explain missing local data rather than show sample results.
5. Use an empty fixture catalog when testing the empty-catalog state. Expect a
   no-records message and disabled Analyze button, not an endless loader.
6. Resize to approximately 390px and a desktop width. Controls and cards stack on
   mobile without horizontal scrolling. Navigate using keyboard Tab/Enter; check
   visible focus, labels, disclosures, skip link, and active navigation state.
7. Open About Model, Compare, and Simulate; verify their content and use browser
   Back/Forward to navigate. Compare/Simulate must not suggest completed tools.

## Verification for this stage

- `npm --prefix frontend run build`.
- `backend/.venv/bin/python -m pytest backend/tests -q` (189 tests).
- No lint script is configured in the frontend package.
- Browser checks against FastAPI: dependent selection, sample partial report,
  backend-down error, retry recovery, populated numeric scores using the existing
  synthetic event test provider, selection reset, and desktop/mobile layout.
  The temporary QA provider uses real analytics code and is not shipped as product
  data. These checks do not validate football prediction accuracy.
