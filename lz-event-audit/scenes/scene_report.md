# LZ scene validation receipt

Generated from `manifest.json` by `render_scenes.py`. This receipt records the two selected benchmarks at two discrete halo settings. It does not add a scientific run or certify the original papers, the full catalog, or a homepage film.

- Baseline revision: `3bb891e3775fa404e420bdb936e6ca9c656326ba`
- Experiment: `two-benchmarks-one-halo-change-v1`
- Calculation timestamp (UTC): `2026-11-22T00:02:32.362621+00:00`
- Selected IDs: `rodd-higgsino`, `baer-barger-300`
- Inventory: 24 configurations from 14 papers.

## Fixed observation

Reported candidate: **248 ± 23 (stat) ± 23 (sys) keV**, in 2.84 tonne-years. Identity: `lz-high-energy-candidate-2023-06-16`. Source: [LZ collaboration, arXiv:2609.02823v1](https://arxiv.org/abs/2609.02823v1). The two uncertainties are not combined. A candidate is not a discovery; no measured event position is exported.

## Selected results

Published masses, splittings, couplings and cross-sections remain fixed. Only halo escape speed changes from 544 to 600 km/s. Counts in the first two numerical columns use the published cross-section; the next column divides sideband count by the predicted ROI count.

| Scenario | Benchmark | ROI events, published σ | Sideband events, published σ | Sideband / ROI | Δχ² shape + sideband |
| --- | --- | ---: | ---: | ---: | ---: |
| `base` (544 km/s) | `rodd-higgsino` | 0.6515 | 3.751 | 5.758 | 4.254 |
| `base` (544 km/s) | `baer-barger-300` | 1.036 | 0.03546 | 0.03424 | 4.72 |
| `vesc600` (600 km/s) | `rodd-higgsino` | 93.74 | 47.48 | 0.5065 | 2.725 |
| `vesc600` (600 km/s) | `baer-barger-300` | 1.042 | 0.03542 | 0.03399 | 4.741 |

**Every sideband result assumes unit acceptance; the acceptance is unpublished.** A declining sideband/ROI ratio does not mean the absolute sideband count falls. The signal-only statistic neglects background and is not a discovery significance or a best-theory ranking.

## Common assumptions and normalization

- Target: Natural xenon, nine isotopes with mass-fraction weighting
- Form factor: Helm; Lewin and Smith parameterization in rates.py
- Interaction: Spin-independent contact; delta>0 endothermic, delta<0 exothermic; QW weak-charge weighting or Z charge weighting
- Resolution: sigma_E(E)=sqrt(23^2 * E/248 + (0.093*E)^2) keV, Gaussian reconstructed response
- Background: Neglected in signal-only shape statistic
- Normalization: Published cross-section stays fixed for absolute counts; curves and R_SB divided by the same predicted ROI count.
- Efficiency: Integral of true-energy rate times efficiency over its full 4–285 keV support; 5.4 and 269.9 are not hard bounds. It is a piecewise-linear approximation, not an official-data efficiency reconstruction.
- Sideband window: 350–590 keV reconstructed.
- Each displayed curve is divided by that snapshot’s ROI count. The original SVG connects recorded samples; it does not recompute intermediate halo settings.

| Scenario | Benchmark | Full-grid normalized integral | Allowed absolute error | Omitted sideband tail / count | Tail bound |
| --- | --- | ---: | ---: | ---: | ---: |
| `base` | `rodd-higgsino` | 1 | 1e-05 | 0 | 1e-10 |
| `base` | `baer-barger-300` | 0.999999721587 | 1e-05 | 1.5170347e-14 | 1e-10 |
| `vesc600` | `rodd-higgsino` | 0.999999999999 | 1e-05 | 0 | 1e-10 |
| `vesc600` | `baer-barger-300` | 0.999999607325 | 1e-05 | 1.072272e-13 | 1e-10 |

## Numerical protocol and tolerances

The exported calculation uses 2,400 uniformly spaced true/reconstructed energy points from 0.5 to 1,200 keV and 48 midpoint phases over the year. Energy refinement uses 1,200/2,400/4,800 points; annual refinement uses 48/96/192 phases. These refinements reuse the existing rate engine.

Tolerance rule: Before acceptance: CSV half-rounding unit + 2*max successive energy-grid differences + 2*max successive annual-grid differences; sampled peak also allows one coarse energy bin.

Convergence ceiling: 2400-to-4800 difference <=0.1% for smooth metrics; numerical allowance is not a scientific uncertainty.

Numerical allowances quantify grid sensitivity only. They do not include efficiency, halo, nuclear-response, source-model, or background uncertainty. Reference cells absent from the stored CSV are explicitly shown as not available; convergence is still checked for those metrics.

### base / rodd-higgsino

Snapshot status: validated stored-audit snapshot. Paper comparison: **approximate paper comparison**. Upstream year-averaged validation retunes splitting to 375.3 keV for one event, versus 377 keV reported, with 4.5 versus 4.9 sideband events. This snapshot keeps published delta=377 keV and does not retune to one event.

| Metric | n=1200 / t=48 | n=2400 / t=48 | n=4800 / t=48 | n=2400 / t=96 | n=2400 / t=192 | Numerical allowance |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `N_roi_own_sigma` | 0.65153971 | 0.65154227 | 0.65154159 | 0.65154226 | 0.65154228 | 5.1877215e-06 |
| `N_sb_own_sigma` | 3.7513807 | 3.7513807 | 3.7513807 | 3.7513793 | 3.7513793 | 2.8386528e-06 |
| `R_SB` | 5.7577162 | 5.7576935 | 5.7576995 | 5.7576914 | 5.7576913 | 4.9464931e-05 |
| `dchi2` | 4.2543857 | 4.2542316 | 4.2542461 | 4.2542309 | 4.2542309 | 0.00030943781 |
| `E_peak_keV` | 228.59508 | 229 | 228.95239 | 229 | 229 | 1.000417 |
| `p_event_per_roi` | 0.009863586 | 0.0098643128 | 0.00986425 | 0.009864313 | 0.0098643129 | 1.4539375e-06 |

| Stored-reference metric | CSV value | Source rounding allowance | Total absolute tolerance | Observed absolute difference | Result |
| --- | ---: | ---: | ---: | ---: | --- |
| `N_roi_own_sigma` | 0.6515 | 5e-05 | 5.5187721e-05 | 4.2273938e-05 | PASS |
| `N_sb_own_sigma` | Not available | — | — | — | Convergence only |
| `R_SB` | 5.758 | 0.0005 | 0.00054946493 | 0.0003065117 | PASS |
| `dchi2` | 4.254 | 0.0005 | 0.00080943781 | 0.00023159012 | PASS |
| `E_peak_keV` | 229 | 0.05 | 1.050417 | 0 | PASS |
| `p_event_per_roi` | Not available | — | — | — | Convergence only |

Snapshot SHA-256: `7aa22878f4a49cfb1b84dc8894d09a2e6bdbc98705ca249372877e27925cc59d`

### base / baer-barger-300

Snapshot status: validated stored-audit snapshot. Paper comparison: **approximate paper comparison**. Upstream fixed-vE=254 comparison checks Table I; the scene uses the common year-averaged halo. For the 300 GeV point, stored sigma is 1.45e-45 versus the paper rounded 1.5e-45 cm²; no exact paper reproduction is asserted.

| Metric | n=1200 / t=48 | n=2400 / t=48 | n=4800 / t=48 | n=2400 / t=96 | n=2400 / t=192 | Numerical allowance |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `N_roi_own_sigma` | 1.0357432 | 1.0357438 | 1.0357436 | 1.0357438 | 1.0357438 | 1.3173391e-06 |
| `N_sb_own_sigma` | 0.035459194 | 0.035459194 | 0.035459194 | 0.035459194 | 0.035459194 | 3.4083847e-14 |
| `R_SB` | 0.034235508 | 0.034235486 | 0.034235494 | 0.034235486 | 0.034235486 | 4.3543355e-08 |
| `dchi2` | 4.7198227 | 4.7200926 | 4.720085 | 4.7200926 | 4.7200926 | 0.00053966106 |
| `E_peak_keV` | 154.56422 | 154.5 | 154.71786 | 154.5 | 154.5 | 1.000417 |
| `p_event_per_roi` | 0.0011961509 | 0.0011959895 | 0.001195994 | 0.0011959895 | 0.0011959895 | 3.227866e-07 |

| Stored-reference metric | CSV value | Source rounding allowance | Total absolute tolerance | Observed absolute difference | Result |
| --- | ---: | ---: | ---: | ---: | --- |
| `N_roi_own_sigma` | 1.036 | 0.0005 | 0.00050131734 | 0.00025615431 | PASS |
| `N_sb_own_sigma` | Not available | — | — | — | Convergence only |
| `R_SB` | 0.03424 | 5e-06 | 5.0435434e-06 | 4.5142229e-06 | PASS |
| `dchi2` | 4.72 | 0.0005 | 0.0010396611 | 9.2567103e-05 | PASS |
| `E_peak_keV` | 154.5 | 0.05 | 1.050417 | 0 | PASS |
| `p_event_per_roi` | Not available | — | — | — | Convergence only |

Snapshot SHA-256: `bc984e5c8913ec76126c06909e75d2fa1ab16d6fac8e68919615689a92bf5a1c`

### vesc600 / rodd-higgsino

Snapshot status: validated stored-audit snapshot. Paper comparison: **approximate paper comparison**. Upstream year-averaged validation retunes splitting to 375.3 keV for one event, versus 377 keV reported, with 4.5 versus 4.9 sideband events. This snapshot keeps published delta=377 keV and does not retune to one event.

| Metric | n=1200 / t=48 | n=2400 / t=48 | n=4800 / t=48 | n=2400 / t=96 | n=2400 / t=192 | Numerical allowance |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `N_roi_own_sigma` | 93.739695 | 93.740013 | 93.739899 | 93.740013 | 93.740013 | 0.00063682955 |
| `N_sb_own_sigma` | 47.48201 | 47.48201 | 47.48201 | 47.48201 | 47.48201 | 1.6939339e-11 |
| `R_SB` | 0.50653045 | 0.50652873 | 0.50652935 | 0.50652873 | 0.50652873 | 3.4411511e-06 |
| `dchi2` | 2.7249415 | 2.7250214 | 2.7250228 | 2.7250214 | 2.7250214 | 0.00015978988 |
| `E_peak_keV` | 196.58173 | 197 | 196.95905 | 197 | 197 | 1.000417 |
| `p_event_per_roi` | 0.0047241902 | 0.0047239961 | 0.0047239948 | 0.0047239961 | 0.0047239961 | 3.8822171e-07 |

| Stored-reference metric | CSV value | Source rounding allowance | Total absolute tolerance | Observed absolute difference | Result |
| --- | ---: | ---: | ---: | ---: | --- |
| `N_roi_own_sigma` | Not available | — | — | — | Convergence only |
| `N_sb_own_sigma` | Not available | — | — | — | Convergence only |
| `R_SB` | 0.5065 | 5e-05 | 5.3441151e-05 | 2.8732236e-05 | PASS |
| `dchi2` | 2.725 | 0.0005 | 0.00065978988 | 2.1413358e-05 | PASS |
| `E_peak_keV` | Not available | — | — | — | Convergence only |
| `p_event_per_roi` | Not available | — | — | — | Convergence only |

Snapshot SHA-256: `66e797ef2be75905f4beb43fdaaacb5e8d705afe440c3f33f4e6f65e485d75fe`

### vesc600 / baer-barger-300

Snapshot status: validated stored-audit snapshot. Paper comparison: **approximate paper comparison**. Upstream fixed-vE=254 comparison checks Table I; the scene uses the common year-averaged halo. For the 300 GeV point, stored sigma is 1.45e-45 versus the paper rounded 1.5e-45 cm²; no exact paper reproduction is asserted.

| Metric | n=1200 / t=48 | n=2400 / t=48 | n=4800 / t=48 | n=2400 / t=96 | n=2400 / t=192 | Numerical allowance |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `N_roi_own_sigma` | 1.0420646 | 1.0420652 | 1.042065 | 1.0420652 | 1.0420652 | 1.3168264e-06 |
| `N_sb_own_sigma` | 0.035423108 | 0.035423108 | 0.035423108 | 0.035423108 | 0.035423108 | 1.7569279e-14 |
| `R_SB` | 0.033993198 | 0.033993177 | 0.033993185 | 0.033993177 | 0.033993177 | 4.295619e-08 |
| `dchi2` | 4.7411634 | 4.7414333 | 4.7414256 | 4.7414333 | 4.7414333 | 0.00053968695 |
| `E_peak_keV` | 154.56422 | 154.5 | 154.71786 | 154.5 | 154.5 | 1.000417 |
| `p_event_per_roi` | 0.0011831781 | 0.0011830185 | 0.001183023 | 0.0011830185 | 0.0011830185 | 3.193005e-07 |

| Stored-reference metric | CSV value | Source rounding allowance | Total absolute tolerance | Observed absolute difference | Result |
| --- | ---: | ---: | ---: | ---: | --- |
| `N_roi_own_sigma` | Not available | — | — | — | Convergence only |
| `N_sb_own_sigma` | Not available | — | — | — | Convergence only |
| `R_SB` | 0.03399 | 5e-06 | 5.0429562e-06 | 3.1769817e-06 | PASS |
| `dchi2` | 4.741 | 0.0005 | 0.0010396869 | 0.00043325957 | PASS |
| `E_peak_keV` | Not available | — | — | — | Convergence only |
| `p_event_per_roi` | Not available | — | — | — | Convergence only |

Snapshot SHA-256: `1ac43879cc4e03450ce828c965cfc5790d87fc3b177893cf65350c770e38f420`

## L-01–L-06 evidence for this scope

The statuses below are generated artifact checks for this four-snapshot research preview. Browser interaction, responsive presentation, and a future film’s performance/release are separate review steps. The exporter and test commands below must be rerun after changes.

| Requirement | Artifact check | Evidence and boundary |
| --- | --- | --- |
| L-01 Scope | PASS | Pinned inventory is preserved: 24 configurations / 14 papers; no benchmark added. |
| L-02 Reproduction | PASS | Every available stored-reference comparison passes its convergence-plus-source-precision tolerance. Upstream validation log is rerun and compared, with discrepancies retained. |
| L-03 Numerics | PASS | Selected grids, annual phases, normalization and omitted tails are checked by the exporter. Separate Python tests exercise zero-support/undefined cases; these are not selectable film snapshots. |
| L-04 Invariance | PASS | All scenario detector settings use the same centrally recorded observation. The read-only adapter tests also check identity, immutable values, uncertainty, and fixed marker coordinates. |
| L-05 Limits | PASS | Unit sideband acceptance, non-reproductions, the inferred sign and partial discrepancies remain in the export and inventory. |
| L-06 Rendering | PASS | Embedded JSON matches the manifest, every static scenario exists and observation-marker coordinates agree. Adapter tests independently compare displayed table values. No measured event geometry is shown. |

## Source and output hashes

- Numerical result SHA-256: `d538edf7a820a99ab5519a25294f8c954b6b72288e325d18421a5b2615a99b17`
- Manifest SHA-256: `92284d4e5cf2f2d1ed9b1f7108d3fed90148048b8ddd13324f2bbe94ea015331`
- Validation rerun SHA-256: `b42f0add974847759ff2522935876b380e8e29f4920e2c21c6bce72ec5661fdb`
- Source hash encoding: SHA-256 of UTF-8 text bytes, CRLF normalized to LF

| Source file | SHA-256 |
| --- | --- |
| `rates.py` | `64141aad7a9643a1fadcb24e1016b0cd79e9f8e1625b00ab144e66c7e6cc1b8d` |
| `audit.py` | `174897a8d2e359d9b1f525ab126e5853ca507f22a856ed08b56090192dbe7c6c` |
| `validate.py` | `d25205ed0183974f3f1d08ab77fc387ecf68a762490db1a01064ab75e21088a0` |
| `benchmarks.csv` | `8d37498e36baaedd7c4a7f4d2ca3e2f1054c45eed352657661ae28566a5925fd` |
| `results/benchmarks_common.csv` | `ee865269bce78e123ee1d2bdd9be663a099612a02571db7421ed4ad449f15fed` |
| `results/validation.txt` | `b42f0add974847759ff2522935876b380e8e29f4920e2c21c6bce72ec5661fdb` |
| `scene_export.py` | `e17c62b983740675c4df7cd9887abae2b6a04ef40648986be27c367e1c913bfe` |

Third-party articles are linked, not bundled. LZ article terms are CC BY-NC-SA 4.0; Rodd and Baer–Barger article terms are CC BY 4.0. Original repository calculations/results keep the repository’s license. The official HEPData release was not retrieved or checked. No figure or measured event geometry was copied.

## Run environment

| Component | Recorded value |
| --- | --- |
| python | 3.12.9 |
| numpy | 1.26.4 |
| scipy | 1.16.0 |
| platform | Windows-11-10.0.26300-SP0 |
| hardware | Unknown / not recorded |
| hardware_unavailable_reason | No runtime-performance or device-comparison claim is made. |

## Reproduce and verify

From the repository root:

```sh
python lz-event-audit/scene_export.py --check
python lz-event-audit/render_scenes.py --check
node --test lz-event-audit/web/test_scene_view.mjs
```

Regenerate with `python lz-event-audit/scene_export.py` followed by `python lz-event-audit/render_scenes.py`. Regeneration updates calculation timestamps and content hashes. The browser preview is a review artifact, and homepage integration remains a separate change.
