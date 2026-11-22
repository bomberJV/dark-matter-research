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
            parts.append(f'<rect class="grid-filled" style="--mark:{i}" x="{x}" y="{y}" width="{12*fraction:.8f}" height="10" rx="0"/>')
    parts.append('</svg>')
    return "\n".join(parts)


def hypotheses(manifest):
    """Before the reveal: explain the energy trade without disclosing sensitivity."""
    cards = []
    for index, shot in enumerate(manifest["scenarios"][0]["snapshots"]):
        bid = shot["benchmark_id"]
        b = next(b for b in manifest["benchmarks"] if b["id"] == bid)
        upward = b["delta_keV"] > 0
        initial, final = (100, 35) if upward else (35, 100)
        key = f"energy-trade-{index}"
        cards.append(f'''<article class="hypothesis" data-hypothesis="{'higgsino' if index == 0 else 'exothermic'}">
<p class="model-kicker">{'A / Endothermic' if upward else 'B / Exothermic'}</p><h3>{NAMES[bid]}</h3>
<svg class="energy-trade" viewBox="0 0 440 148" role="img" aria-labelledby="{key}"><title id="{key}">{'A gains' if upward else 'B releases'} internal energy. Conceptual energy levels, not to scale.</title>
<path d="M20 {initial}H150M270 {final}H420" stroke="currentColor" stroke-width="2" opacity=".8"/><path d="M152 {initial}C205 {initial} 230 {final} 268 {final}" fill="none" stroke="currentColor" stroke-dasharray="3 6"/>
<circle class="energy-before" cx="95" cy="{initial}" r="7" fill="currentColor"/><circle class="energy-after" cx="325" cy="{final}" r="7" fill="currentColor"/>
<text x="20" y="{initial-15}" fill="#c1b4ae" font-size="11">Before</text><text x="360" y="{final-15}" fill="#c1b4ae" font-size="11">After</text>
<text x="220" y="131" text-anchor="middle" fill="currentColor" font-size="12">{'+' if upward else '−'}{num(abs(b['delta_keV']))} keV internal-energy change</text></svg>
<p>{'Kinetic energy must supply a heavier final state. The particle gains internal energy.' if upward else 'A lighter final state releases internal energy into the interaction.'}</p>
<div class="baseline-fact"><span>At the common 544 km/s cutoff</span><strong>{num(shot['metrics']['N_roi_own_sigma'])} <small>expected selected events</small></strong></div>
<p class="fine-print">Energy-level schematic · not to scale</p></article>''')
    return "\n".join(cards)


def halo(manifest):
    low, high = [s["halo"]["vesc"] for s in manifest["scenarios"]]
    x = lambda speed: 32 + speed / 650 * 800
    particles = []
    # These decorative marks illustrate a range, never a sampled halo distribution.
    for index, speed in enumerate([45, 110, 175, 240, 305, 370, 435, 500, 560, 585]):
        extra = ' halo-extra' if speed > low else ''
        yy = 83 + (index % 3) * 19
        particles.append(f'<g class="speed-streak{extra}" style="--delay:{index*.13:.2f}s"><path d="M{x(speed)-17:.2f} {yy}H{x(speed):.2f}" stroke="currentColor"/><circle cx="{x(speed):.2f}" cy="{yy}" r="2" fill="currentColor"/></g>')
    return f'''<svg viewBox="0 0 864 213" class="halo-diagram" role="img" aria-labelledby="halo-title halo-desc"><title id="halo-title">Two discrete Galactic escape-speed cutoffs</title><desc id="halo-desc">The common cutoff is {num(low)} kilometers per second. The changed cutoff is {num(high)}. Only the interval between them is newly permitted. Particle marks are illustrative, not a sampled distribution or a rate calculation.</desc>
<rect x="32" y="62" width="{x(low)-32:.3f}" height="86" fill="#f19a83" fill-opacity=".04"/><rect class="halo-extra" x="{x(low):.3f}" y="62" width="{x(high)-x(low):.3f}" height="86" fill="#f19a83" fill-opacity=".17"/>
{''.join(particles)}
<path d="M32 149H832" stroke="#76615f"/><path class="cutoff-common" d="M{x(low):.3f} 43V153" stroke="#f19a83" stroke-width="2"/><path class="halo-extra" d="M{x(high):.3f} 43V153" stroke="#f5eee5" stroke-width="2"/>
<text x="{x(low)-7:.3f}" y="28" text-anchor="end" fill="#f19a83" font-size="13">{num(low)} km/s</text><text class="halo-extra" x="{x(high)+6:.3f}" y="28" fill="#f5eee5" font-size="13">{num(high)} km/s</text>
{''.join(f'<path d="M{x(v):.3f} 149v5" stroke="#76615f"/><text x="{x(v):.3f}" y="174" text-anchor="middle" fill="#bba49c" font-size="11">{v}</text>' for v in range(0, 651, 100))}
<text x="32" y="202" fill="#bba49c" font-size="11">Particle speed in the Galactic frame / km/s</text><text x="832" y="202" text-anchor="end" fill="#bba49c" font-size="10">RANGE ILLUSTRATION</text></svg>
<p class="halo-caption"><span data-halo-caption="base">The common halo ends at {num(low)} km/s. The changed assumption admits speeds up to {num(high)} km/s. Particle marks illustrate a range, not its abundance.</span><span data-halo-caption="vesc600" hidden>The brighter interval adds speeds from {num(low)} to {num(high)} km/s. Particle marks illustrate the range, not its abundance.</span></p>'''


def sidebands(manifest):
    obs_energy = manifest["observation"]["energy_keV"]
    low, high = manifest["common_assumptions"]["sideband"]["reconstructed_window_keV"]
    x = lambda energy: 40 + energy / 650 * 800
    result = []
    for scenario in manifest["scenarios"]:
        sid = scenario["id"]
        key = f"sideband-map-{sid}"
        result.append(f'''<div class="sideband-state" data-sideband-scenario="{sid}">
<div class="state-heading"><h3>{esc(scenario['label'])}</h3><span class="state-badge">Same exposure and published cross-sections</span></div>
<svg class="sideband-map" viewBox="0 0 880 150" role="img" aria-labelledby="{key}"><title id="{key}">Reported candidate energy {num(obs_energy)} keV and the {num(low)} to {num(high)} keV reconstructed-energy sideband. Uncertainties remain in the fixed observation strip.</title>
<rect x="{x(low):.3f}" y="49" width="{x(high)-x(low):.3f}" height="49" fill="#f19a83" fill-opacity=".15"/><path d="M40 98H840" stroke="#76615f"/>
<path data-fixed-energy="{num(obs_energy)}" d="M{x(obs_energy):.3f} 49V102" stroke="#f5eee5" stroke-width="2"/>
<text x="{x(obs_energy):.3f}" y="28" text-anchor="middle" fill="#f5eee5" font-size="12">Candidate / {num(obs_energy)} keV</text><text x="{(x(low)+x(high))/2:.3f}" y="28" text-anchor="middle" fill="#f19a83" font-size="12">Higher-energy check / {num(low)}–{num(high)} keV</text>
{''.join(f'<text x="{x(v):.3f}" y="121" text-anchor="middle" fill="#bba49c" font-size="10">{v}</text>' for v in range(0, 651, 100))}
<text x="40" y="146" fill="#bba49c" font-size="10">Reconstructed recoil energy / keV</text></svg>
<div class="sideband-pair">''')
        for shot in scenario["snapshots"]:
            count = shot["metrics"]["N_sb_own_sigma"]
            if count is None or not 0 <= count <= 50:
                raise ValueError("Sideband display requires reviewed expectations between 0 and 50")
            bid = shot["benchmark_id"]
            result.append(f'''<article class="sideband-model" data-sideband-benchmark="{bid}"><h3>{NAMES[bid]}</h3><p class="sideband-number"><strong>{num(count)}</strong><span>expected sideband events</span></p>
<svg viewBox="0 0 500 38" class="sideband-bar" role="img" aria-label="{num(count)} expected sideband events on a zero to fifty event scale"><rect width="500" height="4" y="5" fill="#45373c"/><rect data-sideband-count="{count}" width="{count*10:.8f}" height="4" y="5" fill="currentColor"/><text x="0" y="33" fill="#bba49c" font-size="10">0</text><text x="500" y="33" text-anchor="end" fill="#bba49c" font-size="10">50 expected events</text></svg></article>''')
        result.append('</div><p class="fine-print">Expected counts, not observed counts. Both bars share a linear scale. No high-energy event data are plotted here.</p></div>')
    return "\n".join(result)


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
            line = 'At the common cutoff, both predictions are of order one selected event. The higher-cutoff snapshot tests the effect of admitting faster particles.'
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
    if [s["halo"]["vesc"] for s in manifest["scenarios"]] != [544, 600]:
        raise ValueError("The narrative controls require the reviewed 544/600 km/s settings")
    observation = manifest["observation"]
    energy, stat, systematic = [num(observation[k]) for k in ("energy_keV", "statistical_uncertainty_keV", "systematic_uncertainty_keV")]
    adapter = (WEB / "scene-view.js").read_text(encoding="utf-8").replace("export function ", "function ")
    controller = (WEB / "experience.js").read_text(encoding="utf-8")
    controller = re.sub(r"^import .*?;\n", "", controller).replace("export function ", "function ")
    script = "(() => {\n'use strict';\n" + adapter + "\n" + controller + "\nmountExperience(document);\n})();"
    values = {
        "STYLE": "\n".join((WEB / name).read_text(encoding="utf-8") for name in ("experience.css", "experience-journey.css")),
        "MEASUREMENT": f'<div class="measurement-line"><strong>{energy}</strong><span class="unit">keV</span></div><p class="uncertainties">± {stat} statistical &nbsp; ± {systematic} systematic</p><p class="measurement-context">Reported candidate · {num(observation["exposure_tonne_year"])} tonne-years of exposure</p>',
        "LOCK": f'<b>{energy} keV</b> &nbsp; ± {stat} stat &nbsp; ± {systematic} sys &nbsp; / &nbsp; one reported candidate',
        "STATES": states(manifest),
        "HYPOTHESES": hypotheses(manifest),
        "HALO": halo(manifest),
        "SIDEBANDS": sidebands(manifest),
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
