"""Render the discrete LZ export as an accessible, progressively enhanced receipt.

Run after scene_export.py. All numbers and curves come from scenes/manifest.json.
This module performs no scientific rate calculation and copies no paper figures.
"""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
COLORS = ("#f19a83", "#9fbfe3")


def escape(value):
    return html.escape(str(value), quote=True)


def number(value, digits=4):
    return "Undefined" if value is None else format(value, f".{digits}g")


def pretty(value):
    return escape(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False))


def observation_values(manifest):
    observation = manifest["observation"]
    return (
        observation["energy_keV"],
        observation["statistical_uncertainty_keV"],
        observation["systematic_uncertainty_keV"],
        observation["exposure_tonne_year"],
    )


def plot(manifest, scenario, maximum):
    event, stat, systematic, _ = observation_values(manifest)
    left, right, top, bottom = 72, 874, 96, 352
    x_max = 450
    x = lambda value: left + value / x_max * (right - left)
    y = lambda value: bottom - value / maximum * (bottom - top)
    label_id = f"plot-{scenario['id']}"
    pieces = [f'<svg class="plot" role="img" aria-labelledby="{label_id}-title {label_id}-desc" viewBox="0 0 920 426" xmlns="http://www.w3.org/2000/svg">',
              f'<title id="{label_id}-title">{escape(scenario["label"])}: calculated spectra and the fixed reported event</title>',
              f'<desc id="{label_id}-desc">Original plot of recorded calculations, normalized to one selected ROI event for each benchmark. The white marker is the reported {number(event)} keV candidate. Statistical and systematic uncertainties are shown separately. All scenario plots use the same axes. Exact metrics follow in the table.</desc>']
    for index in range(5):
        value = maximum * index / 4
        yy = y(value)
        pieces.append(f'<path d="M{left} {yy:.2f}H{right}" stroke="#343138"/>')
        pieces.append(f'<text x="{left - 10}" y="{yy + 4:.2f}" text-anchor="end" fill="#c7c0b8" font-size="12">{number(value, 2)}</text>')
    for value in range(0, 451, 50):
        xx = x(value)
        pieces.append(f'<text x="{xx:.2f}" y="377" text-anchor="middle" fill="#c7c0b8" font-size="12">{value}</text>')
    pieces.append('<text x="473" y="407" text-anchor="middle" fill="#e2ddd5" font-size="14">Reconstructed recoil energy / keV</text>')
    pieces.append('<text x="72" y="24" fill="#c7c0b8" font-size="13">Selected density per ROI event / keV⁻¹</text>')
    for uncertainty, yy, label in ((stat, 47, "stat"), (systematic, 67, "sys")):
        x1, x2 = x(event - uncertainty), x(event + uncertainty)
        pieces.append(f'<path d="M{x1:.2f} {yy}H{x2:.2f} M{x1:.2f} {yy-4}V{yy+4} M{x2:.2f} {yy-4}V{yy+4}" stroke="#f6f3ee" fill="none"/>')
        pieces.append(f'<text x="{x2+9:.2f}" y="{yy+4}" fill="#e2ddd5" font-size="12">±{number(uncertainty)} keV {label}</text>')
    pieces.append(f'<path data-observation-energy="{number(event)}" d="M{x(event):.2f} 88V{bottom}" stroke="#f6f3ee" stroke-dasharray="4 5"/>')
    for index, snapshot in enumerate(scenario["snapshots"]):
        points = []
        for energy, density in zip(snapshot["curve"]["energy_keV"], snapshot["curve"]["selected_density_per_roi_keV"]):
            if 0 <= energy <= x_max and density is not None:
                points.append(f'{x(energy):.3f},{y(density):.3f}')
        if points:
            dash = ' stroke-dasharray="8 4"' if index else ""
            pieces.append(f'<polyline points="{" ".join(points)}" fill="none" stroke="{COLORS[index]}" stroke-width="2.5"{dash}/>')
    pieces.append('</svg>')
    return "\n".join(pieces)


def render(manifest):
    if manifest.get("schema_version") != "lz-scenes/v1":
        raise ValueError("Unsupported scene manifest")
    event, stat, systematic, exposure = observation_values(manifest)
    benchmark_by_id = {entry["id"]: entry for entry in manifest["benchmarks"]}
    scenarios = manifest["scenarios"]
    maximum = max(value for scene in scenarios for snap in scene["snapshots"]
                  for energy, value in zip(snap["curve"]["energy_keV"], snap["curve"]["selected_density_per_roi_keV"])
                  if 0 <= energy <= 450 and value is not None) * 1.10
    controls = "\n".join(f'<button type="button" data-select="{escape(scene["id"])}" aria-pressed="false" aria-controls="scene-{escape(scene["id"])}">{escape(scene["label"])}</button>' for scene in scenarios)
    panels = []
    for scene in scenarios:
        legend, rows, parameters = [], [], []
        for index, snapshot in enumerate(scene["snapshots"]):
            benchmark = benchmark_by_id[snapshot["benchmark_id"]]
            identifier = escape(benchmark["id"])
            legend.append(f'<li><span class="swatch" style="background:{COLORS[index]}"></span>{identifier}{" · dashed" if index else " · solid"}</li>')
            metrics = snapshot["metrics"]
            cells = "".join(f'<td class="numeric" data-metric="{name}">{number(metrics.get(name))}</td>' for name in ("N_roi_own_sigma", "N_sb_own_sigma", "R_SB", "dchi2"))
            rows.append(f'<tr data-benchmark="{identifier}"><th scope="row">{identifier}</th>{cells}</tr>')
            source = next(item for item in manifest["sources"] if benchmark["arxiv"] in item["url"])
            parameters.append(f'<div><h3>{identifier}</h3><p>{escape(benchmark["authors"])} · <a href="{escape(source["url"])}">arXiv:{escape(benchmark["arxiv"])}{escape(source["version"])}</a></p><ul class="parameter-list"><li>Mass: {number(benchmark["m_chi_GeV"])} GeV</li><li>Splitting: {number(benchmark["delta_keV"])} keV</li><li>Coupling: {escape(benchmark["coupling"])}</li><li>Published cross-section: {number(benchmark["sigma_n_cm2"])} cm²</li></ul><p class="caption">{escape(benchmark.get("note", ""))}</p><pre>{pretty(benchmark.get("paper_reproduction", {}))}</pre></div>')
        panels.append(f'''<section class="scene" id="scene-{escape(scene["id"])}" data-scenario="{escape(scene["id"])}" aria-labelledby="heading-{escape(scene["id"])}">
<h2 id="heading-{escape(scene["id"])}">{escape(scene["label"])}</h2>
<p>Escape speed: <strong>{number(scene["halo"]["vesc"])} km/s</strong>. The published model parameters and reported observation stay fixed.</p>
<div class="plot-wrap" tabindex="0" role="region" aria-label="Recorded spectra; scroll horizontally on small screens">{plot(manifest, scene, maximum)}</div>
<ul class="legend">{"".join(legend)}<li>White marker · reported candidate</li></ul>
<p class="caption">Curves are independently calculated selected spectra, each normalized to one ROI event. Lines connect recorded samples for display; no intermediate assumption values are evaluated. The view shows 0–450 keV. All scenarios use the same energy and density axes.</p>
<div class="table-wrap"><table><caption class="caption">Calculated metrics at the published cross-sections, with normalized metrics identified separately.</caption><thead><tr><th scope="col">Benchmark ID</th><th scope="col">ROI events<br>published σ</th><th scope="col">Sideband events<br>published σ</th><th scope="col">Sideband / ROI<br>unit acceptance assumed</th><th scope="col">Δχ²<br>shape + sideband</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>
<p class="notice">Sideband acceptance is unpublished and assumed to be one. The sideband/ROI ratio is a normalized comparison: a falling ratio does not imply fewer absolute sideband events at the published cross-section. Δχ² uses the audit’s signal-only, profiled likelihood; it is not a discovery significance or a theory ranking.</p>
<details><summary>Published parameters and reproduction qualifications</summary><div class="columns">{"".join(parameters)}</div></details>
<details><summary>Exact settings, results and convergence for this snapshot</summary><pre>{pretty(scene)}</pre></details>
</section>''')
    inventory = "".join(f'<tr><th scope="row">{escape(b["id"])}</th><td>{escape(b["arxiv"])}</td><td>{escape(b.get("note", ""))}<pre>{pretty(b.get("paper_reproduction", {}))}</pre></td></tr>' for b in manifest["benchmarks"])
    serialized = json.dumps(manifest, ensure_ascii=False, separators=(",", ":"), allow_nan=False).replace("<", "\\u003c")
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><title>LZ · One observation, two predictions</title><link rel="stylesheet" href="../web/scene-preview.css"></head>
<body><main>
<p class="eyebrow">LZ investigation · recorded research preview</p>
<h1>One observation.<br>Two competing predictions.</h1>
<p class="intro">What can one candidate distinguish when the predictions depend on an assumed halo? Compare two fixed benchmarks, then change only the escape speed from 544 to 600 km/s.</p>
<section class="observation" aria-labelledby="observation-heading"><p class="eyebrow" id="observation-heading">Reported observation · fixed in every scenario</p><p class="energy">{number(event)} ± {number(stat)} (stat) ± {number(systematic)} (sys) keV</p><p>{number(exposure)} tonne-years exposure · <a href="{escape(manifest["observation"]["source"]["url"])}">LZ collaboration, arXiv:2609.02823v1</a></p><p class="caption">A nuclear-recoil candidate, not a discovery. Statistical and systematic uncertainties remain separate. This page shows no measured event position or detector reconstruction.</p></section>
<div id="scenario-controls" hidden role="group" aria-label="Choose a recorded escape-speed scenario">{controls}</div>
<p id="selection-status" role="status" aria-live="polite">All recorded scenarios are shown below. JavaScript adds discrete selection only.</p>
{"".join(panels)}
<section><h2>What changes—and what does not</h2><p>The endothermic benchmark depends strongly on the fastest halo particles. At its unchanged published cross-section, raising the escape speed can increase the absolute predicted count while reducing the number of sideband events per ROI event. The exothermic benchmark is much less sensitive in this comparison. These are conditional model calculations, not evidence that either model explains the candidate.</p><p class="notice">Both calculations use natural xenon, a Helm form factor, approximate efficiency, the same energy resolution and neglected background. The true-energy efficiency has support from 4 to 285 keV; 5.4 and 269.9 keV are its 50% efficiency points, not hard integration boundaries. The official event-level data release was not checked for this export.</p></section>
<details><summary>Common assumptions and units</summary><pre>{pretty(manifest["common_assumptions"])}</pre><pre>{pretty(manifest.get("units", {}))}</pre></details>
<details><summary>Full benchmark inventory, including qualifications</summary><p>Only two benchmarks are selected for these scenes. Computability and reproduction of the stored audit do not establish reproduction of every paper.</p><div class="table-wrap"><table><thead><tr><th scope="col">Benchmark</th><th scope="col">Paper</th><th scope="col">Source note and reproduction status</th></tr></thead><tbody>{inventory}</tbody></table></div></details>
<details><summary>Complete source and numerical receipt</summary><pre>{pretty(manifest)}</pre></details>
<footer><p><a href="manifest.json">Machine-readable manifest</a> · <a href="scene_report.md">Validation receipt</a> · <a href="README.md">Reproduction instructions</a> · <a href="../web/index.html">Full audit explorer</a></p><p>Original calculations and plots by Brandon Frank Han-Chween Huang. This is a review artifact; homepage film integration is a separate change.</p></footer>
</main><script id="scene-manifest" type="application/json">{serialized}</script><script type="module" src="../web/scene-preview.js"></script></body></html>
'''


def markdown(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_report(manifest):
    """Human receipt of the same exported values; not a new scientific run."""
    observation = manifest["observation"]
    event, stat, systematic, exposure = observation_values(manifest)
    scenarios = manifest["scenarios"]
    snapshots = [snapshot for scenario in scenarios for snapshot in scenario["snapshots"]]
    benchmarks = manifest["benchmarks"]
    reference_pass = all(check["passed"] for snapshot in snapshots for check in snapshot["validation"]["reference"].values())
    normalization_pass = all(abs(snapshot["validation"]["normalized_full_grid_integral"] - 1) <= snapshot["validation"]["normalization_absolute_tolerance"] for snapshot in snapshots)
    tails_pass = all(snapshot["validation"]["omitted_tail"]["relative_to_N_sb"] <= snapshot["validation"]["omitted_tail"]["relative_acceptance_bound"] for snapshot in snapshots)
    finite_pass = "NaN" not in json.dumps(manifest, allow_nan=False)
    selected = manifest["scope"]["selected_benchmark_ids"]
    invariant = all(scenario["detector"]["event_E"] == event for scenario in scenarios)
    qualifiers = {entry["id"]: entry["paper_reproduction"]["status"] for entry in benchmarks}
    qualifications_pass = (qualifiers["su-yang-yang"] == "not reproduced" and qualifiers["dent-newstead-exo"] == "not reproduced"
                           and "inferred" in qualifiers["gce-simple"] and qualifiers["delepine-khalil"] == "partial discrepancy"
                           and manifest["common_assumptions"]["sideband"]["acceptance"] == 1)
    preview = render(manifest)
    embedded = re.search(r'<script id="scene-manifest" type="application/json">(.*?)</script>', preview, re.S)
    rendering_pass = embedded is not None and json.loads(embedded.group(1)) == manifest
    rendering_pass = rendering_pass and all(f'data-scenario="{scenario["id"]}"' in preview for scenario in scenarios)
    markers = re.findall(r'data-observation-energy="([^"]+)" d="([^"]+)"', preview)
    rendering_pass = rendering_pass and len(markers) == len(scenarios) and len(set(markers)) == 1
    lines = ["# LZ scene validation receipt", "",
             "Generated from `manifest.json` by `render_scenes.py`. This receipt records the two selected benchmarks at two discrete halo settings. It does not add a scientific run or certify the original papers, the full catalog, or a homepage film.", "",
             f"- Baseline revision: `{manifest['baseline_revision']}`",
             f"- Experiment: `{manifest['experiment_id']}`",
             f"- Calculation timestamp (UTC): `{manifest['generated_at_utc']}`",
             f"- Selected IDs: {', '.join('`' + identifier + '`' for identifier in selected)}",
             f"- Inventory: {len(benchmarks)} configurations from {len({entry['arxiv'] for entry in benchmarks})} papers.", "",
             "## Fixed observation", "",
             f"Reported candidate: **{number(event)} ± {number(stat)} (stat) ± {number(systematic)} (sys) keV**, in {number(exposure)} tonne-years. Identity: `{observation['id']}`. Source: [LZ collaboration, arXiv:2609.02823v1]({observation['source']['url']}). The two uncertainties are not combined. A candidate is not a discovery; no measured event position is exported.", "",
             "## Selected results", "",
             "Published masses, splittings, couplings and cross-sections remain fixed. Only halo escape speed changes from 544 to 600 km/s. Counts in the first two numerical columns use the published cross-section; the next column divides sideband count by the predicted ROI count.", "",
             "| Scenario | Benchmark | ROI events, published σ | Sideband events, published σ | Sideband / ROI | Δχ² shape + sideband |",
             "| --- | --- | ---: | ---: | ---: | ---: |"]
    for scenario in scenarios:
        for snapshot in scenario["snapshots"]:
            values = snapshot["metrics"]
            cells = " | ".join(number(values[name]) for name in ("N_roi_own_sigma", "N_sb_own_sigma", "R_SB", "dchi2"))
            lines.append(f"| `{scenario['id']}` ({number(scenario['halo']['vesc'])} km/s) | `{snapshot['benchmark_id']}` | {cells} |")
    lines += ["", "**Every sideband result assumes unit acceptance; the acceptance is unpublished.** A declining sideband/ROI ratio does not mean the absolute sideband count falls. The signal-only statistic neglects background and is not a discovery significance or a best-theory ranking.", "",
              "## Common assumptions and normalization", ""]
    assumptions = manifest["common_assumptions"]
    for field in ("target", "form_factor", "interaction", "resolution", "background", "normalization"):
        lines.append(f"- {field.replace('_', ' ').capitalize()}: {assumptions[field]}")
    lines += [f"- Efficiency: {assumptions['efficiency']['roi_definition']} It is a piecewise-linear approximation, not an official-data efficiency reconstruction.",
              f"- Sideband window: {number(assumptions['sideband']['reconstructed_window_keV'][0])}–{number(assumptions['sideband']['reconstructed_window_keV'][1])} keV reconstructed.",
              "- Each displayed curve is divided by that snapshot’s ROI count. The original SVG connects recorded samples; it does not recompute intermediate halo settings.", "",
              "| Scenario | Benchmark | Full-grid normalized integral | Allowed absolute error | Omitted sideband tail / count | Tail bound |",
              "| --- | --- | ---: | ---: | ---: | ---: |"]
    for scenario in scenarios:
        for snapshot in scenario["snapshots"]:
            validation = snapshot["validation"]
            tail = validation["omitted_tail"]
            lines.append(f"| `{scenario['id']}` | `{snapshot['benchmark_id']}` | {number(validation['normalized_full_grid_integral'], 12)} | {number(validation['normalization_absolute_tolerance'])} | {number(tail['relative_to_N_sb'], 8)} | {number(tail['relative_acceptance_bound'])} |")
    protocol = manifest["numerical_protocol"]
    lines += ["", "## Numerical protocol and tolerances", "",
              "The exported calculation uses 2,400 uniformly spaced true/reconstructed energy points from 0.5 to 1,200 keV and 48 midpoint phases over the year. Energy refinement uses 1,200/2,400/4,800 points; annual refinement uses 48/96/192 phases. These refinements reuse the existing rate engine.", "",
              f"Tolerance rule: {protocol['tolerance_rule']}", "",
              f"Convergence ceiling: {protocol['convergence_ceiling']}", "",
              "Numerical allowances quantify grid sensitivity only. They do not include efficiency, halo, nuclear-response, source-model, or background uncertainty. Reference cells absent from the stored CSV are explicitly shown as not available; convergence is still checked for those metrics."]
    for scenario in scenarios:
        for snapshot in scenario["snapshots"]:
            validation = snapshot["validation"]
            convergence = validation["convergence"]
            grids = convergence["energy_grids"] + convergence["annual_grids"]
            lines += ["", f"### {scenario['id']} / {snapshot['benchmark_id']}", "",
                      f"Snapshot status: {snapshot['status']}. Paper comparison: **{snapshot['paper_reproduction']['status']}**. {snapshot['paper_reproduction']['qualification']}", "",
                      "| Metric | n=1200 / t=48 | n=2400 / t=48 | n=4800 / t=48 | n=2400 / t=96 | n=2400 / t=192 | Numerical allowance |",
                      "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
            for name, allowance in convergence["absolute_numerical_allowance"].items():
                values = " | ".join(number(grid["metrics"][name], 8) for grid in grids)
                lines.append(f"| `{name}` | {values} | {number(allowance, 8)} |")
            lines += ["", "| Stored-reference metric | CSV value | Source rounding allowance | Total absolute tolerance | Observed absolute difference | Result |",
                      "| --- | ---: | ---: | ---: | ---: | --- |"]
            for name in snapshot["metrics"]:
                check = validation["reference"].get(name)
                if check:
                    lines.append(f"| `{name}` | {check['stored_text']} | {number(check['source_rounding_allowance'], 8)} | {number(check['absolute_tolerance'], 8)} | {number(check['absolute_difference'], 8)} | {'PASS' if check['passed'] else 'FAIL'} |")
                else:
                    lines.append(f"| `{name}` | Not available | — | — | — | Convergence only |")
            lines += ["", f"Snapshot SHA-256: `{snapshot['result_sha256']}`"]
    acceptance = [
        ("L-01 Scope", len(benchmarks) == 24 and len({b['arxiv'] for b in benchmarks}) == 14, "Pinned inventory is preserved: 24 configurations / 14 papers; no benchmark added."),
        ("L-02 Reproduction", reference_pass, "Every available stored-reference comparison passes its convergence-plus-source-precision tolerance. Upstream validation log is rerun and compared, with discrepancies retained."),
        ("L-03 Numerics", normalization_pass and tails_pass and finite_pass, "Selected grids, annual phases, normalization and omitted tails are checked by the exporter. Separate Python tests exercise zero-support/undefined cases; these are not selectable film snapshots."),
        ("L-04 Invariance", invariant, "All scenario detector settings use the same centrally recorded observation. The read-only adapter tests also check identity, immutable values, uncertainty, and fixed marker coordinates."),
        ("L-05 Limits", qualifications_pass, "Unit sideband acceptance, non-reproductions, the inferred sign and partial discrepancies remain in the export and inventory."),
        ("L-06 Rendering", rendering_pass, "Embedded JSON matches the manifest, every static scenario exists and observation-marker coordinates agree. Adapter tests independently compare displayed table values. No measured event geometry is shown."),
    ]
    lines += ["", "## L-01–L-06 evidence for this scope", "",
              "The statuses below are generated artifact checks for this four-snapshot research preview. Browser interaction, responsive presentation, and a future film’s performance/release are separate review steps. The exporter and test commands below must be rerun after changes.", "",
              "| Requirement | Artifact check | Evidence and boundary |", "| --- | --- | --- |"]
    for requirement, passed, evidence in acceptance:
        lines.append(f"| {requirement} | {'PASS' if passed else 'FAIL'} | {evidence} |")
    lines += ["", "## Source and output hashes", "",
              f"- Numerical result SHA-256: `{manifest['result_sha256']}`",
              f"- Manifest SHA-256: `{manifest['manifest_sha256']}`",
              f"- Validation rerun SHA-256: `{manifest['upstream_validation']['sha256']}`",
              f"- Source hash encoding: {manifest['source_hash_encoding']}", "",
              "| Source file | SHA-256 |", "| --- | --- |"]
    lines += [f"| `{path}` | `{sha}` |" for path, sha in manifest["source_files"].items()]
    lines += ["", "Third-party articles are linked, not bundled. LZ article terms are CC BY-NC-SA 4.0; Rodd and Baer–Barger article terms are CC BY 4.0. Original repository calculations/results keep the repository’s license. The official HEPData release was not retrieved or checked. No figure or measured event geometry was copied.", "",
              "## Run environment", "", "| Component | Recorded value |", "| --- | --- |"]
    for key, value in manifest["environment"].items():
        lines.append(f"| {markdown(key)} | {markdown(value if value is not None else 'Unknown / not recorded')} |")
    lines += ["", "## Reproduce and verify", "", "From the repository root:", "", "```sh",
              "python lz-event-audit/scene_export.py --check",
              "python lz-event-audit/render_scenes.py --check",
              "node --test lz-event-audit/web/test_scene_view.mjs",
              "```", "", "Regenerate with `python lz-event-audit/scene_export.py` followed by `python lz-event-audit/render_scenes.py`. Regeneration updates calculation timestamps and content hashes. The browser preview is a review artifact, and homepage integration remains a separate change.", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if the committed static preview is stale")
    args = parser.parse_args()
    manifest = json.loads((HERE / "scenes" / "manifest.json").read_text(encoding="utf-8"))
    outputs = {"index.html": render(manifest), "scene_report.md": render_report(manifest)}
    if args.check:
        for filename, content in outputs.items():
            destination = HERE / "scenes" / filename
            if not destination.exists() or destination.read_text(encoding="utf-8") != content:
                raise SystemExit(f"Scene artifact {filename} is stale; run python render_scenes.py")
        print("Static scene preview and human receipt match manifest")
    else:
        for filename, content in outputs.items():
            destination = HERE / "scenes" / filename
            destination.write_text(content, encoding="utf-8", newline="\n")
            print(f"Wrote {destination.relative_to(HERE)}")


if __name__ == "__main__":
    main()
