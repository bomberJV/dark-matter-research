# One observation, two predictions

This review package exports two existing audit benchmarks under the common halo
and under one declared change: escape speed 544 to 600 km/s. It is an independent
calculation, not an LZ collaboration result, discovery claim or theory ranking.
The reported observation remains fixed. Homepage film integration is a separate
change in `brandon-studio`.

## Read the result

The standalone LZ investigation has one editable source in this repository.
Both preview titles, *Before the Discovery* and *LZ Investigation*, refer to
`scenes/experience.html`. Edit the template and controller under `web/`,
then regenerate the page with `python lz-event-audit/build_experience.py`.

The higher-energy chapter calculates how often zero events would occur
under either benchmark. It exposes the two halo settings, normalization
and assumed acceptance. A separate Dent and Newstead comparison uses
the validation routine's 350–680 keV window and records the unresolved
mass splitting for the 42 GeV example.

Open `experience.html` for the guided standalone experience: an illustrative
S1 / drift / S2 sequence with pause and replay, a prediction-before-reveal choice,
the fixed observation, two predictions on the same 100-event grid, and the discrete
544 / 600 km/s assumption change. A speed-range schematic makes the changed input
visible; the next stage compares absolute high-energy sideband expectations.
Choices only affect the narrative and never change the calculated outputs.
Visitors may skip the prediction, inspect all evidence at any time, and reset.
Reduced motion skips timed signal playback; hidden tabs pause it. It includes
all scripts, styles, SVG charts and the complete manifest in one offline-capable
file. Both scenarios remain readable without JavaScript. The illustration is
not measured geometry; expected-event marks are not observed events.

The energy-level diagrams are conceptual and not to scale. Speed-range particle
marks are illustrative, not a sampled halo or abundance plot. Sideband bars share
a linear 0–50 expected-event scale; no observed high-energy counts are plotted.
Unit sideband acceptance remains an explicit approximation. The visitor predicts
sensitivity to a changed assumption, not which physical theory is true.

Open `index.html` through a local HTTP server. Both scenarios and their source
details remain readable without JavaScript. With JavaScript, the buttons select
one of the two recorded scenarios. They do not interpolate or recompute science.

- `manifest.json`: machine-readable inputs, outputs, assumptions and validation.
- `scene_report.md`: generated numerical receipt.
- `validation-rerun.txt`: fresh output of the original upstream validation script.
- `SOURCE_REVIEW.md`: primary-source checks and asset-use decisions.

The chosen IDs are `rodd-higgsino` (1,100 GeV, +377 keV, neutron weak-charge
coupling) and `baer-barger-300` (300 GeV, -300 keV, charge coupling). They were
selected to contrast endothermic tail sensitivity with exothermic behavior, not
as the best explanations. The full 24-configuration / 14-paper catalog is
preserved with its original claims, notes and qualifications.

## Interpret the axes and counts

The curves are the selected reconstructed-energy density divided by that
configuration's predicted ROI count, in inverse keV per ROI event. Each scenario
is normalized independently for shape comparison. The table separately reports
absolute expected counts at the unchanged published cross-section and exposure.
A decrease in sideband events **per ROI event** does not mean that the absolute
sideband count decreases. The higgsino example demonstrates this distinction.

The ROI is the engine's efficiency-weighted true-energy selection. Efficiency
rolls to zero at 4 and 285 keV; 5.4 and 269.9 keV are the 50% efficiency points,
not hard integration cutoffs. The sideband is 350-590 keV in reconstructed
energy, evaluated without the ROI efficiency and with unit acceptance because
the relevant acceptance is unpublished. These are different selections.

The statistical and systematic observation uncertainties are displayed
separately. The engine's assumed Gaussian response combines terms in its own
declared resolution formula; it does not replace those two reported error bars.
Background is neglected, xenon uses Helm form factors, and the efficiency is an
approximation. The official data release was not retrieved or checked.

## Reproduce

From the repository root, with the dependencies in `requirements.txt` installed:

```sh
python lz-event-audit/scene_export.py
python lz-event-audit/render_scenes.py
python lz-event-audit/build_experience.py
python -m unittest discover -s lz-event-audit -p test_scene_export.py
node --test lz-event-audit/web/test_engine.mjs lz-event-audit/web/test_scene_view.mjs lz-event-audit/web/test_experience.mjs
python lz-event-audit/scene_export.py --check
python lz-event-audit/render_scenes.py --check
python lz-event-audit/build_experience.py --check
python -m http.server 8000 --directory lz-event-audit
```

Then open `http://localhost:8000/scenes/`. The receipt records the environment
actually used for the checked-in generation, which may differ from the repository
dependency pins. Numerical comparisons use recorded convergence and source
rounding tolerances rather than equating different platforms byte for byte.
Hashes identify source and artifact contents; numerical agreement does not prove
that a physical model or the approximations are correct.

The existing `validate.py` prints comparisons. Its successful exit alone is not
a scientific pass: the export also checks its output against the stored record
and preserves the mismatches already present there. Reproducing a stored audit
output is separate from reproducing a paper's original result. In particular,
the selected Rodd point remains at its published 377 keV splitting; it is not
silently retuned to force one expected event.

## Scope of L-01 through L-06

| Gate | Evidence in this slice |
| --- | --- |
| L-01 | Pinned complete catalog, 24 unique IDs and 14 distinct paper IDs |
| L-02 | Two selected baseline references, scenario references where stored, convergence and rounding allowances, fresh upstream validation record |
| L-03 | Grid refinement, dimensional labels, normalization checks, forbidden/zero-ROI states represented as unavailable rather than Infinity |
| L-04 | Read-only observation shared by both scenarios; only escape speed changes |
| L-05 | Approximate efficiency, unit sideband acceptance, omitted background, non-reproductions and inferred-sign notes survive export |
| L-06 | Static tables and discrete interactive selection use the same manifest; no detector or event-position reconstruction is supplied |

This does not certify a full cinematic integration, live continuous parameter
exploration or every paper in the catalog. Any later detector picture must be
labeled an illustration; an authored event point is not measured event geometry.
