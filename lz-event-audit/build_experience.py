"""Build a self-contained guided experience from the validated LZ snapshots.

No rate calculation, figure copying, interpolation, fitting or network access.
The complete manifest is embedded unchanged; both scenarios work without JS.
"""
from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path

from render_scenes import plot

HERE = Path(__file__).resolve().parent
WEB = HERE / "web"
OUTPUT = HERE / "scenes" / "experience.html"
NAMES = {"rodd-higgsino": "Higgsino", "baer-barger-300": "Exothermic dark matter"}
COPY = {
    "rodd-higgsino": ("A / Endothermic", "The particle must gain internal energy in the interaction. This benchmark relies on the fast tail of the assumed particle distribution."),
    "baer-barger-300": ("B / Exothermic", "The interaction releases internal energy. This benchmark changes little under the same escape-speed adjustment."),
}
esc = lambda value: html.escape(str(value), quote=True)
num = lambda value: format(value, ".4g") if value is not None else "Undefined"


def expectation_grid(count, key):
    """100 equal squares. Width encodes the exact fractional expected count."""
    if count is None or not 0 <= count <= 100:
        raise ValueError("The reviewed count display supports finite expectations from 0 to 100")
    parts = [f'<svg class="expectation-grid" viewBox="0 0 398 88" role="img" aria-labelledby="{key}-grid-title" data-expected-count="{count}">',
             f'<title id="{key}-grid-title">{num(count)} expected selected events. Each full square represents one expected event; partial squares represent fractions. These are predictions, not observed events.</title>']
    for i in range(100):
        x, y = (i % 20) * 20, (i // 20) * 18
        parts.append(f'<rect class="grid-empty" x="{x}" y="{y}" width="12" height="10" rx="1"/>')
        fraction = min(1, max(0, count - i))
        if fraction:
            parts.append(f'<rect class="grid-filled" x="{x}" y="{y}" width="{12*fraction:.8f}" height="10" rx="0"/>')
    parts.append('</svg>')
    return "\n".join(parts)


def states(manifest):
    max_density = max(d for s in manifest["scenarios"] for shot in s["snapshots"]
                      for e, d in zip(shot["curve"]["energy_keV"], shot["curve"]["selected_density_per_roi_keV"])
                      if e <= 450 and d is not None) * 1.08
    base = manifest["scenarios"][0]["snapshots"]
    pieces = []
    for scenario in manifest["scenarios"]:
        sid = scenario["id"]
        pieces.append(f'<section class="snapshot-state" data-recorded-scenario="{sid}" aria-labelledby="state-{sid}">')
        pieces.append(f'<div class="state-heading"><h3 id="state-{sid}">{esc(scenario["label"])}</h3><span class="state-badge">Recorded calculation / {sid}</span></div><div class="models">')
        for index, snapshot in enumerate(scenario["snapshots"]):
            bid = snapshot["benchmark_id"]
            count = snapshot["metrics"]["N_roi_own_sigma"]
            tag, description = COPY[bid]
            before = base[index]["metrics"]["N_roi_own_sigma"]
            change = "Baseline expectation" if sid == "base" else f'{num(before)} → {num(count)} expected events'
            pieces.append(f'''<article class="model" data-benchmark="{bid}">
<p class="model-kicker">{tag}</p><h4>{NAMES[bid]}</h4><p class="model-description">{description}</p>
<div class="expected-value"><strong data-metric="N_roi_own_sigma">{num(count)}</strong><span>expected<br>selected events</span></div>
<p class="count-caption">{num(manifest['observation']['exposure_tonne_year'])} tonne-years · unchanged cross-section</p>
{expectation_grid(count, f'{sid}-{bid}')}
<div class="model-foot"><span>{change}</span><b>{'544 km/s' if sid == 'base' else '600 km/s'}</b></div></article>''')
        pieces.append('</div><p class="grid-note">One full square = one expected selected event. Partial squares show fractions. Each grid holds 100 on the same scale. These marks represent expectations, not detected particles.</p>')
        if sid == "base":
            line = 'At the common cutoff, both predictions are of order one selected event. <strong>Select 600 km/s above</strong> to see what one changed assumption does.'
        else:
            first, second = scenario["snapshots"]
            factor = first["metrics"]["N_roi_own_sigma"] / base[0]["metrics"]["N_roi_own_sigma"]
            percent = (second["metrics"]["N_roi_own_sigma"] / base[1]["metrics"]["N_roi_own_sigma"] - 1) * 100
            line = f'The higgsino expectation is now <strong>about {factor:.0f} times larger</strong>. The exothermic expectation changes by <strong class="second">{percent:.2f}%</strong>. The reported candidate stays at {num(manifest["observation"]["energy_keV"])} keV.'
        pieces.append(f'<p class="result-line">{line}</p>')
        pieces.append(f'<details class="spectra-details"><summary>Inspect the energy spectra and sideband predictions</summary><div class="plot-legend"><span>Higgsino</span><span>Exothermic dark matter</span><span>Reported candidate</span></div><div class="plot-container">{plot(manifest, scenario, max_density)}</div>')
        pieces.append('<p class="plot-note">Shape comparison: each curve is normalized to one predicted selected event. The vertical marker is the same reported energy in both snapshots. Statistical and systematic uncertainties remain separate. Absolute expected counts are shown above and below.</p><div class="table-scroll"><table><caption>Signal-only audit metrics at the unchanged published cross-sections</caption><thead><tr><th scope="col">Benchmark</th><th scope="col">Selected events</th><th scope="col">Sideband events</th><th scope="col">Sideband / selected</th></tr></thead><tbody>')
        for shot in scenario["snapshots"]:
            pieces.append(f'<tr><th scope="row">{NAMES[shot["benchmark_id"]]}</th>' + ''.join(f'<td data-metric="{k}">{num(shot["metrics"][k])}</td>' for k in ("N_roi_own_sigma", "N_sb_own_sigma", "R_SB")) + '</tr>')
        pieces.append('</tbody></table></div><p class="plot-note">The sideband spans 350–590 keV in reconstructed energy. Its acceptance is unpublished and assumed to be one; the ROI efficiency is not applied there. The higgsino’s absolute sideband expectation rises under the change even though its sideband / selected ratio falls.</p></details></section>')
    return "\n".join(pieces)


def evidence(manifest):
    obs = manifest["observation"]
    rows = []
    for b in manifest["benchmarks"]:
        rows.append(f'<tr><th scope="row">{esc(b["id"])}</th><td>{esc(b["paper_reproduction"]["status"])}</td><td>{esc(b["paper_reproduction"]["qualification"])}</td></tr>')
    limitations = ''.join(f'<li>{esc(item)}</li>' for item in manifest["limitations"])
    qualifications = ''.join(f'<p><strong>{NAMES[b["id"]]} — {esc(b["paper_reproduction"]["status"])}</strong><br>{esc(b["paper_reproduction"]["qualification"])}</p>' for b in manifest["benchmarks"] if b["selected"])
    return f'''<details><summary>The reported observation <span>Energy, exposure and primary sources</span></summary><div class="evidence-body">
<p>The reported candidate energy is {num(obs['energy_keV'])} ± {num(obs['statistical_uncertainty_keV'])} (statistical) ± {num(obs['systematic_uncertainty_keV'])} (systematic) keV. These uncertainties are not combined here. The event date is {esc(obs['event_date'])}; the reported exposure is {num(obs['exposure_tonne_year'])} tonne-years.</p>
<p>The paper reports {num(obs['global_tension_sigma'])}σ global tension and a maximum local tension of {num(obs['maximum_local_tension_sigma'])}σ for the tested background comparisons. These are not discovery significance or probabilities that either selected explanation is correct. No measured event position, waveform or detector reconstruction is exported.</p>
<ul><li><a href="{esc(obs['source']['url'])}">LZ primary paper, v1</a> — reported observation and uncertainty.</li><li><a href="https://arxiv.org/abs/2609.04175v1">Rodd, Safdi, Slatyer &amp; Xu, v1</a> — selected higgsino benchmark.</li><li><a href="https://arxiv.org/abs/2609.06153v1">Baer &amp; Barger, v1</a> — selected 300 GeV exothermic benchmark.</li></ul>
<p>The official data release was not retrieved or verified. Article figures are link-only; this experience copies none of them.</p></div></details>
<details><summary>What changed, and what stayed fixed <span>Exactly one input changes</span></summary><div class="evidence-body">
<p>Only the Galactic escape speed changes: <strong>544 → 600 km/s</strong>. This is an assumption comparison, not a fitted value, an uncertainty interval or a measurement of the halo. The observation, exposure, cross-sections, masses, splittings and detector model stay fixed.</p>
<div class="table-scroll"><table><thead><tr><th scope="col">Parameter</th><th scope="col">Higgsino</th><th scope="col">Exothermic dark matter</th></tr></thead><tbody>
<tr><th scope="row">Benchmark ID</th><td>rodd-higgsino</td><td>baer-barger-300</td></tr>
<tr><th scope="row">Mass</th><td>1,100 GeV</td><td>300 GeV</td></tr><tr><th scope="row">Mass splitting</th><td>+377 keV</td><td>−300 keV</td></tr>
<tr><th scope="row">Cross-section</th><td>7.3 × 10⁻³⁹ cm² per neutron</td><td>1.5 × 10⁻⁴⁵ cm² per proton</td></tr><tr><th scope="row">Coupling</th><td>Weak charge (QW)</td><td>Charge (Z); unit excited fraction</td></tr></tbody></table></div>
<p>Both use the year-averaged Standard Halo Model, density 0.3 GeV/cm³, characteristic speed 238 km/s, mean Earth speed 250.2 km/s and annual amplitude 14.9 km/s; natural xenon and Helm form factors.</p></div></details>
<details><summary>Approximations and unresolved differences <span>Numerical reproduction ≠ paper reproduction</span></summary><div class="evidence-body">
<p>The detector efficiency is piecewise linear, with support from 4 to 285 keV. The 5.4 and 269.9 keV points are 50% efficiency points, not hard selection boundaries. The Gaussian resolution is σ(E) = √[23²E/248 + (0.093E)²] keV. Background is neglected. Sideband acceptance is unpublished and assumed to be one.</p>
{qualifications}<ul>{limitations}</ul></div></details>
<details><summary>The full benchmark inventory <span>{manifest['scope']['configuration_count']} configurations / {manifest['scope']['paper_count']} papers, including non-reproductions</span></summary><div class="evidence-body"><p>These flags remain attached to the exported results. A successful software check does not erase an upstream mismatch or an inferred assumption.</p><div class="table-scroll"><table><thead><tr><th scope="col">ID</th><th scope="col">Status</th><th scope="col">Qualification</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div></div></details>
<details><summary>Reproduce and inspect the calculation <span>Settings, source hashes and recorded outputs</span></summary><div class="evidence-body">
<p>Recorded grid checks compare 1,200 / 2,400 / 4,800 energy bins and 48 / 96 / 192 annual samples. Tolerances follow measured convergence and published rounding precision. The manifest contains the integration bounds, omitted-tail checks, source versions, input hashes and result hashes.</p>
<p>Manifest SHA-256: <code>{manifest['manifest_sha256']}</code><br>Result SHA-256: <code>{manifest['result_sha256']}</code></p>
<pre>python lz-event-audit/scene_export.py --check
python lz-event-audit/render_scenes.py --check
python lz-event-audit/build_experience.py --check</pre>
<p><a href="https://github.com/bomberJV/dark-matter-research/blob/research/lz-scene-snapshots/lz-event-audit/scenes/scene_report.md">Read the numerical receipt</a> · <a href="https://github.com/bomberJV/dark-matter-research/blob/research/lz-scene-snapshots/lz-event-audit/scenes/SOURCE_REVIEW.md">Read the source review</a></p>
<p>The download contains the complete manifest embedded in this page, including both scenarios and all qualifications. Presentation controls only select already validated snapshots.</p>
</div></details>'''


def render(manifest):
    if manifest.get("schema_version") != "lz-scenes/v1":
        raise ValueError("Unsupported manifest")
    if [s["id"] for s in manifest["scenarios"]] != ["base", "vesc600"]:
        raise ValueError("This narrative requires the two reviewed snapshots")
    observation = manifest["observation"]
    energy, stat, systematic = [num(observation[k]) for k in ("energy_keV", "statistical_uncertainty_keV", "systematic_uncertainty_keV")]
    adapter = (WEB / "scene-view.js").read_text(encoding="utf-8").replace("export function ", "function ")
    controller = (WEB / "experience.js").read_text(encoding="utf-8")
    controller = re.sub(r"^import .*?;\n", "", controller).replace("export function ", "function ")
    script = "(() => {\n'use strict';\n" + adapter + "\n" + controller + "\nmountExperience(document);\n})();"
    values = {
        "STYLE": (WEB / "experience.css").read_text(encoding="utf-8"),
        "MEASUREMENT": f'<div class="measurement-line"><strong>{energy}</strong><span class="unit">keV</span></div><p class="uncertainties">± {stat} statistical &nbsp; ± {systematic} systematic</p><p class="measurement-context">Reported candidate · {num(observation["exposure_tonne_year"])} tonne-years of exposure</p>',
        "LOCK": f'<b>{energy} keV</b> &nbsp; ± {stat} stat &nbsp; ± {systematic} sys &nbsp; / &nbsp; one reported candidate',
        "STATES": states(manifest),
        "EVIDENCE": evidence(manifest),
        "MANIFEST": json.dumps(manifest, ensure_ascii=False, allow_nan=False, separators=(",", ":")).replace("<", "\\u003c"),
        "SCRIPT": script,
    }
    page = (WEB / "experience.html").read_text(encoding="utf-8")
    for key, value in values.items():
        page = page.replace(f"__{key}__", value)
    if re.search(r"__[A-Z]+__", page):
        raise ValueError("Unresolved template token")
    return page


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    manifest = json.loads((HERE / "scenes" / "manifest.json").read_text(encoding="utf-8"))
    result = render(manifest)
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != result:
            raise SystemExit("Guided experience is stale. Run build_experience.py.")
        print("PASS: self-contained guided experience matches its sources and manifest")
    else:
        OUTPUT.write_text(result, encoding="utf-8", newline="\n")
        print(f"Wrote {OUTPUT.name} ({len(result.encode('utf-8')):,} bytes)")


if __name__ == "__main__":
    main()
