# Tactical analysis dashboard

The React application provides a responsive navy/charcoal workspace with a restrained
green accent, hash navigation, and an integrated Analyze page. About Model explains
the assumptions. Compare now provides independent selectors and a complete result
view. Simulate retains an explicit planned-interface state.

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
   Back/Forward to navigate. Simulate must not suggest a completed interface.

## Verification for this stage

- `npm --prefix frontend run build`.
- `backend/.venv/bin/python -m pytest backend/tests -q` (189 tests).
- No lint script is configured in the frontend package.
- Browser checks against FastAPI: dependent selection, sample partial report,
  backend-down error, retry recovery, populated numeric scores using the existing
  synthetic event test provider, selection reset, and desktop/mobile layout.
  The temporary QA provider uses real analytics code and is not shipped as product
  data. These checks do not validate football prediction accuracy.


## Compare experience

`pages/Compare.jsx` owns both submitted selections and the abortable comparison
request. `ComparisonPicker` instances have independent catalog state and unique
accessible labels. Changing either selection clears results and cancels the old
request; changing a competition/season resets only that side's dependent choices.
The centralized API client encodes all six identifiers for `GET /compare`.

Reusable components under `components/comparison/` render the team headers,
Recharts radar, metric/category tables, strongest differences, similarities and
matchup observations. The chart code loads only when Compare is opened. Identities,
statistical values, differences and explanations all come from the backend; no
frontend analytical model or sample-result fallback is added.

The radar has seven fixed dimensions and a fixed 0–100 axis with 25-point ticks,
with green solid A and blue dashed B outlines, legends and tooltips. Short axis
labels are expanded in the caption and category table. Keyboard arrow navigation
also exposes the tooltip. Exact numeric values remain available in a semantic
HTML table, so the chart is not the only way to access the information.

To avoid closing a polygon through invented zeroes or silently changing the axes,
the radar requires all seven differences to be comparable. Missing/constant or
incompatible-reference dimensions yield an explicit explanation; available values
remain in tables. Category emphasis describes the backend delta's direction, not
a win advantage. Strongest differences use the backend's qualified advantage lists
rather than reranking raw cross-season numbers. Normalized and raw metric modes
are visibly distinct; unavailable differences retain reasons and raw coverage is
inspectable. Tables scroll within their cards at narrow viewport widths.

### Compare manual checks

1. Start frontend and backend per README, with prepared and reviewed season data.
   Open Compare, choose each side independently and submit. Check both names,
   seasons, identities and sample/source badges match the selections.
2. Compare the same team-season to itself: all comparable deltas should be zero,
   no strongest advantages should be shown, and radar shapes should overlap.
3. Compare contrasting profiles. Hover the chart or focus it and press arrow keys;
   tooltip values must match the category table and the axis must remain 0–100.
4. Toggle Season percentiles / Raw metrics. Units, description, values and
   differences must switch together. Missing values display dashes, real zeroes
   display 0.0, and excluded reference comparisons carry reasons.
5. Change Team A's competition or season. A's dependent selections and the report
   clear, B stays selected, and Compare is disabled until A is complete again.
6. A missing coverage manifest (including the default tiny demo) should produce
   an explanatory error with retry. Insufficient metric evidence in an otherwise
   accepted comparison should suppress the radar without hiding available tables.
7. Check desktop and a 390px viewport. Cards stack and the page does not overflow;
   wide tables have their own keyboard-focusable horizontal scrolling areas.

Verification: frontend production build, three Node display-rule tests (null/zero,
reference exclusions, signed deltas), and all 189 backend tests pass. Browser QA
with existing clearly labeled synthetic profiles passed the independent selection
and submission flow, two contrasting identities, radar rendering with all axis
ticks, keyboard tooltip values, and the 390px layout after fixing table-induced
page overflow. The temporary test server used the real scoring/comparison engines;
its test fixtures were not added to frontend product data. Raw-mode interaction and selector-reset behavior are included in the manual
checklist above; they were code-reviewed but not browser-verified in this stage.
