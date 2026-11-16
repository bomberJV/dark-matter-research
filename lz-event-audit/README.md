# One event, many explanations: an audit of the LZ 248 keV interpretations

Working note · 15 November 2026 · AI-assisted · not peer-reviewed

LZ reported one nuclear-recoil candidate at 248 ± 23 (stat) ± 23 (sys) keV in 2.84 tonne-years, 3.4σ local and 2.6σ global (arXiv:2609.02823). About fifty interpretation papers followed in ten weeks. Each picks its own halo, cross-section convention, efficiency, resolution and energy windows, so their benchmark points cannot be compared directly. Single-model sideband checks exist (Rodd et al. 2609.04175; Dent & Newstead 2609.04673; Delepine & Khalil 2609.26698; Langhoff 2609.09385). We found no study that puts the published benchmarks of different papers side by side under one set of assumptions. This note does that for 24 benchmarks from 14 papers.

## What was done

One rate engine (`rates.py`): natural xenon, Helm form factor, Standard Halo Model with an analytic mean inverse speed, spin-independent contact coupling (isoscalar, charge or Z-boson weighting), endothermic and exothermic kinematics.

Common framework for every benchmark:

| Input | Choice |
|---|---|
| Halo | ρ 0.3 GeV/cm³, v₀ 238, v_esc 544 km/s, Earth speed 250.2 ± 14.9 km/s averaged over the year |
| Exposure | 2.84 tonne-years |
| Efficiency | LZ Fig. S2 as a piecewise-linear curve: 50% at 5.4 keV, 96% from 14 to 250 keV, 50% at 269.9 keV (Baer & Barger's approximation; LZ's HEPData record was not reachable from this workspace) |
| Resolution | σ_E = √((23 keV)² E/248 keV + (0.093 E)²) (Rodd et al.) |
| Sideband | 350–590 keV reconstructed, unit acceptance (LZ has not published it); 350–680 keV as a variant |
| Background | neglected (LZ expects about 0.01 events near the candidate) |

Metrics, all independent of the overall cross-section unless stated:

- **Sideband per ROI event**: sideband events expected once the cross-section is set to give one event in the ROI.
- **Δχ² shape + sideband**: 2 ln of the likelihood ratio between an ideal narrow line at 248 keV and the model, for "one event at 248 keV, nothing else in the ROI, empty sideband", with the cross-section profiled. Zero means a perfect line.
- **June-16 rate factor**: event density at 248 keV on the event's date relative to the yearly average. The event time is part of the data, so the combined column subtracts 2 ln of this factor; it can then go below zero.
- **ROI events with the paper's σ**: absolute count when the paper states a cross-section.

Each benchmark was rerun with v_esc 500 and 600 km/s, v₀ 220 km/s, the energy scale shifted by ±9.3% (LZ's calibration systematic) and stat-only resolution.

## Validation before any benchmark was run

`validate.py`, output in `results/validation.txt`. All against numbers published by other groups:

- Baer & Barger Table I (exothermic): cross-sections, peaks and low/high ratios within about 1%.
- Rodd et al. Table I (higgsino): splitting for one event within 2 keV, sideband counts within about 10%.
- Seesaw benchmarks of 2609.13038: event counts within 6%.
- Di Mauro: 0.94 events (published 0.99), N(55–200 keV) 0.73 (0.73).
- Mahapatra & Paul: 17.2% of events below 150 keV (17.44%).
- Kannike et al.: elastic scattering reaches 248 keV only above 74.4 GeV (74).
- Dent & Newstead, endothermic: 0.65 sideband events per signal event (0.6).

Not reproduced: Su, Yang & Yang's best fit gives 3.4 events in 225–271 keV under their own halo, not 1 (their efficiency curve is not stated). Dent & Newstead's exothermic sideband yields (19 per event at 42 GeV) could not be matched; their best-fit splitting is not stated, and between 1.0 and 1.5 MeV the ratio runs from 0.03 to 375.

## Findings

**1. A quoted (mass, splitting) pair means little without its halo.** Most endothermic explanations sit where the fastest halo particles barely clear the threshold, so the count depends on the tail of the speed distribution. Moving a benchmark from its own halo to the common one changes the predicted count by large factors:

- Fan & Reece (1.1 TeV, 350 keV), events in their 215–270 keV window: 1.0 in their halo → 24 in the common halo.
- Su, Yang & Yang, events in 225–271 keV: 3.4 in their halo → 660.
- Seesaw B0045, events in the ROI: 0.98 at a fixed Earth speed of 254 km/s → 2.4 when the speed is averaged over the year.

The same model, a pure 1.1 TeV higgsino, is quoted at δ = 350 keV (Fan & Reece), 377 keV (Rodd et al.) and 375 keV here. The spread comes from conventions, not physics.

**2. The higgsino cross-section has two conventions in print, a factor of 4 apart.** Fan & Reece and Rodd et al. use 7.4 × 10⁻³⁹ cm² per neutron (G_F²μ²/2π). Freese & Theodosopoulos use 1.86 × 10⁻³⁹ cm² (G_F²μ²/8π). Retuning δ to give one event, the factor of 4 moves δ by only 6–9 keV but roughly halves the sideband expectation:

| v_esc | σ convention | δ for one event | Sideband events | P(empty sideband) |
|---|---|---|---|---|
| 544 | /2π | 375.4 keV | 4.55 | 1.1% |
| 544 | /8π | 368.9 keV | 2.10 | 12% |
| 610 | /2π | 421.3 keV | 8.05 | 0.03% |
| 610 | /8π | 412.4 keV | 3.35 | 3.5% |

(1.1 TeV; the full table at 1.0 and 1.1 TeV and three escape speeds is in `results/table_higgsino.md`.) At the fiducial escape speed, whether the empty sideband disfavours the thermal higgsino at about 2.3σ or only about 1.2σ (one-sided) therefore depends on a factor that should not be in dispute. This note does not settle which convention is right.

**3. The sideband splits the benchmarks into two groups.** Endothermic points with δ ≈ 360–380 keV and an electroweak cross-section expect 1.2–5.8 sideband events per signal event. Everything else, endothermic δ ≤ 350 keV and all exothermic points, expects 0.03–0.5. For fixed-δ points in the first group the expectation is fragile: it falls to 0.3–0.6 at v_esc = 600 km/s, and at 500 km/s these models give no ROI events at all. The ±9.3% energy-scale shift moves it by a factor of 1.3–1.7.

**4. The single event barely discriminates.** Δχ² from shape and sideband spans 1.7–4.9 across all 24 benchmarks, a likelihood ratio of at most about 12. Best: light exothermic dark matter (50 GeV, −1 MeV: 1.7; the best exothermic point on the map is near 30 GeV at 0.9) and endothermic points at the kinematic edge (500 GeV, 348 keV: 1.3, but needing a large cross-section and very sensitive to the escape speed). Worst: heavy exothermic dark matter (Baer & Barger: 3.7–4.9), whose spectrum peaks at 155–170 keV, so the event sits in its upper tail.

**5. The date of the event matters about as much as its energy.** Endothermic models predict a rate on June 16 that is 1.3–3.9 times the yearly average, highest for the tail-driven points (up to 2.7 in Δχ²). Exothermic models modulate by 3% or less. Including the date reorders the table: the seesaw points and the 350 keV higgsino-type points move to the top, and heavy exothermic points stay at the bottom. Two more events would change this ranking far more than any refinement of the present one.

Full table: `results/table_benchmarks.md`. Figures: `results/benchmark-map.png`, `results/benchmark-spectra.png`, `results/sideband-robustness.png`.

## Limits

- Helm form factor only. Its second zero sits at 279 keV, just above the event, where shell-model responses differ. Rodd et al. find a shell-model response lowers sideband counts by about 25%. Our Helm rate at 1 TeV, 350 keV is about three times what LZ's published interval implies, consistent with that difference but not confirmed.
- The efficiency is an approximation; the edge at 250–270 keV matters for the ROI shape (Di Mauro's fraction above 200 keV: 0.23 here, 0.26 published).
- Sideband acceptance is unpublished; unit acceptance favours the sideband test.
- Contact spin-independent couplings only. Boosted dark matter, momentum-dependent operators, absorption, neutron disappearance and neutrino up-scattering are not covered.
- Benchmarks were read from the papers' text by an AI reader and cross-checked where a reproduction was possible. 2609.26570 could not be read in full; its exothermic sign is inferred from kinematics.
- 24 benchmarks from 14 of about 50 papers.

## Reproduce

```
pip install numpy scipy matplotlib
python validate.py      # checks against published numbers
python audit.py         # about 2 minutes; writes results/
python figures.py
python summarize.py     # Markdown tables
```

Edit `benchmarks.csv` to add a paper.
