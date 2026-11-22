"""Export two bounded LZ investigations from the existing rate engine.

Run ``python scene_export.py`` to regenerate, or ``python scene_export.py --check``
to verify the committed receipt and independently rerun its calculations. No film
code or third-party figure/data files are produced. See scenes/README.md.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import csv
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import platform
import subprocess
import sys

import numpy as np
import scipy
from scipy.stats import norm

import rates
from rates import Model, predict, delta_chi2
from audit import BASE_DET, BASE_HALO, VARIANTS, load_benchmarks

HERE = Path(__file__).resolve().parent
OUT = HERE / 'scenes'
BASELINE = '3bb891e3775fa404e420bdb936e6ca9c656326ba'
SELECTED = ('rodd-higgsino', 'baer-barger-300')
SCENARIOS = ('base', 'vesc600')
SOURCE_PATHS = ('rates.py', 'audit.py', 'validate.py', 'benchmarks.csv',
                'results/benchmarks_common.csv', 'results/validation.txt',
                'scene_export.py')
METRICS = ('N_roi_own_sigma', 'N_sb_own_sigma', 'R_SB', 'dchi2',
           'E_peak_keV', 'p_event_per_roi')
OBSERVATION = {
    'id': 'lz-high-energy-candidate-2023-06-16',
    'status': 'reported observation; candidate, not a discovery',
    'energy_keV': 248.0,
    'statistical_uncertainty_keV': 23.0,
    'systematic_uncertainty_keV': 23.0,
    'uncertainties_combined': False,
    'exposure_tonne_year': 2.84,
    'event_date': '2023-06-16',
    'global_tension_sigma': 2.6,
    'maximum_local_tension_sigma': 3.4,
    'tension_scope': 'background comparison for tested models; not discovery significance',
    'source': {'id': 'lz-2609.02823v1',
               'url': 'https://arxiv.org/abs/2609.02823v1',
               'version': 'v1', 'publication_date': '2026-09-02',
               'sha256': None,
               'hash_unavailable_reason': 'Article bytes are not included in this reproduction bundle.'},
    'measured_event_position': None,
    'position_unavailable_reason': 'No measured event geometry is exported. Any detector location, flashes, paths and timing are illustrations.',
}
LIMITATIONS = [
    'Independent recast of published parameters, not the LZ collaboration likelihood or an event-level reconstruction.',
    'Approximate piecewise-linear efficiency; official HEPData release has not been retrieved or checked.',
    'Helm form factor only; differences from shell-model responses are not included in numerical error bounds.',
    'Sideband acceptance is unpublished; unit acceptance is assumed for every sideband result.',
    'Background is neglected. The signal-only shape statistic is not a discovery test or a best-theory ranking.',
    'Only contact spin-independent scattering with the stated coupling conventions is covered.',
    'Stored-reference reproduction validates this audit calculation, not every original paper claim.',
    'Predictions are two discrete, validated halo snapshots. Interpolation is only graphical and is not a recomputed result.',
    'The reported candidate energy and its separate statistical/systematic uncertainties never change with the halo assumption.',
]


def canonical(value):
    """The declared result-hash encoding: sorted compact UTF-8 JSON, finite only."""
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False).encode('utf-8')


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def file_digest(path):
    # Text source hashes normalize CRLF to LF for a portable Windows/Linux receipt.
    return hashlib.sha256(Path(path).read_bytes().replace(b'\r\n', b'\n')).hexdigest()


def paper_reproduction(row):
    """Carry limitations without promoting audit.py's computational `ok`."""
    key = row['id']
    if key == 'su-yang-yang':
        return {'status': 'not reproduced', 'qualification': 'Stored validation gives 3.44 rather than about 1 event in 225–271 keV under the paper halo; efficiency curve is not stated.'}
    if key == 'dent-newstead-exo':
        return {'status': 'not reproduced', 'qualification': 'Stored validation gives about 0.04 rather than 19 sideband events per ROI event for the illustrated splitting; the best-fit splitting is unstated.'}
    if key == 'gce-simple':
        return {'status': 'inferred parameter; not assessed', 'qualification': 'Exothermic sign was inferred from kinematics. The upstream audit did not read this paper in full.'}
    if key == 'rodd-higgsino':
        return {'status': 'approximate paper comparison', 'qualification': 'Upstream year-averaged validation retunes splitting to 375.3 keV for one event, versus 377 keV reported, with 4.5 versus 4.9 sideband events. This snapshot keeps published delta=377 keV and does not retune to one event.'}
    if key.startswith('baer-barger-'):
        return {'status': 'approximate paper comparison', 'qualification': 'Upstream fixed-vE=254 comparison checks Table I; the scene uses the common year-averaged halo. For the 300 GeV point, stored sigma is 1.45e-45 versus the paper rounded 1.5e-45 cm²; no exact paper reproduction is asserted.'}
    if key == 'delepine-khalil':
        return {'status': 'partial discrepancy', 'qualification': 'Stored validation does not match the published low/high true-energy window ratios; retain the full validation record.'}
    return {'status': 'not assessed for this scene export', 'qualification': 'See the original audit and full validation record; computational success does not establish reproduction of the paper claim.'}


def inventory():
    rows = load_benchmarks()
    if len(rows) != 24 or len({r['arxiv'] for r in rows}) != 14:
        raise ValueError('Pinned baseline must contain 24 configurations and 14 source papers.')
    return [{**r, 'selected': r['id'] in SELECTED,
             'paper_reproduction': paper_reproduction(r)} for r in rows]


@contextmanager
def annual_samples(count):
    """Refine the existing SHM quadrature only, restoring the engine afterwards.

    rates.eta fixes 48 midpoint phases. Offline convergence probes use its exact
    _eta_shm kernel with 96/192 phases; no model formula or exported API is changed.
    This exporter is intentionally single-threaded.
    """
    original = rates.eta
    if count == 48:
        yield
        return
    def refined(vmin, halo):
        if halo.dvE == 0.0 or halo.phase is not None:
            return original(vmin, halo)
        phases = (np.arange(count) + 0.5) / count
        return np.mean([rates._eta_shm(vmin, halo.v0, halo.vesc,
                       halo.vE + halo.dvE * np.cos(2 * np.pi * t))
                        for t in phases], axis=0)
    rates.eta = refined
    try:
        yield
    finally:
        rates.eta = original


def metrics(pred, det):
    """Zero support has no normalized shape or meaningful argmax location."""
    if pred.N_roi <= 0:
        return {'N_roi_own_sigma': float(pred.N_roi),
                'N_sb_own_sigma': float(pred.N_sb),
                'R_SB': None, 'dchi2': None, 'E_peak_keV': None,
                'p_event_per_roi': None}
    values = dict(N_roi_own_sigma=float(pred.N_roi), N_sb_own_sigma=float(pred.N_sb),
                  R_SB=float(pred.ratio_sb), dchi2=float(delta_chi2(pred, det)),
                  E_peak_keV=float(pred.E_peak),
                  p_event_per_roi=float(pred.p_event / pred.N_roi))
    return {k: v if v is None or math.isfinite(v) else None for k, v in values.items()}


def undefined_reasons(pred, det):
    values = metrics(pred, det)
    reason = ('No positive ROI support: forbidden kinematics, zero cross-section, or zero efficiency. '
              'A normalized ratio, shape statistic and peak are undefined.' if pred.N_roi <= 0 else
              'The event density or required denominator is nonpositive; no finite statistic is defined.')
    return {key: reason for key, value in values.items() if value is None}


def calculate(row, halo, det, n=2400, n_time=48):
    model = Model(row['m_chi_GeV'], row['delta_keV'], row['coupling'], row['sigma_n_cm2'])
    with annual_samples(n_time):
        pred = predict(model, halo, det, n=n, E_max=1200.0)
    return pred, metrics(pred, det)


def rounding_allowance(text):
    """Half of one unit at the last significant digit (audit CSV uses .4g)."""
    value = abs(float(text))
    return 0.5 * 10.0 ** (math.floor(math.log10(value)) - 3) if value else 0.0


def reference_checks(scenario_id, values, numerical_error, reference):
    mapping = {'R_SB': 'R_SB', 'dchi2': 'dchi2'}
    if scenario_id == 'base':
        mapping.update(N_roi_own_sigma='N_roi_own_sigma', E_peak_keV='E_peak_keV')
    checks = {}
    for metric, column in mapping.items():
        if scenario_id != 'base':
            column += '_' + scenario_id
        stored = reference[column]
        half_ulp = rounding_allowance(stored)
        tolerance = half_ulp + numerical_error[metric]
        difference = abs(values[metric] - float(stored))
        passed = difference <= tolerance
        checks[metric] = dict(csv_column=column, stored_text=stored,
                              recomputed=values[metric],
                              source_rounding_allowance=half_ulp,
                              numerical_allowance=numerical_error[metric],
                              absolute_tolerance=tolerance,
                              absolute_difference=difference, passed=passed)
        if not passed:
            raise ValueError(f'Reference mismatch {scenario_id}/{metric}: {checks[metric]}')
    return checks


def kinematic_maximum(row, halo):
    """Largest recoil endpoint over xenon isotopes, using the same vmin kinematics."""
    v = (halo.vesc + halo.vE + abs(halo.dvE)) / rates.C_KMS
    delta = row['delta_keV'] * 1e-6
    energies = []
    for _, _, _, mass_amu in rates.XENON:
        mass = mass_amu * rates.AMU_GEV
        mu = row['m_chi_GeV'] * mass / (row['m_chi_GeV'] + mass)
        term = 1.0 - 2.0 * delta / (mu * v * v)
        if term >= 0:
            energies.append(mu * mu * v * v / (2.0 * mass) * (1 + math.sqrt(term)) ** 2 * 1e6)
    return max(energies, default=0.0)


def snapshot(row, scenario_id, reference):
    halo, det = VARIANTS[scenario_id]
    trials = []
    predictions = []
    for n in (1200, 2400, 4800):
        pred, values = calculate(row, halo, det, n=n)
        trials.append({'n': n, 'n_time': 48, 'metrics': values})
        predictions.append(pred)
        rates._KERNELS.clear()
    annual = []
    for count in (96, 192):
        _, values = calculate(row, halo, det, n=2400, n_time=count)
        annual.append({'n': 2400, 'n_time': count, 'metrics': values})
        rates._KERNELS.clear()
    coarse, standard, fine = [t['metrics'] for t in trials]
    numerical_error = {}
    for key in METRICS:
        grid_error = 2 * max(abs(coarse[key] - standard[key]), abs(standard[key] - fine[key]))
        phase_error = 2 * max(abs(standard[key] - annual[0]['metrics'][key]),
                              abs(annual[0]['metrics'][key] - annual[1]['metrics'][key]))
        if key == 'E_peak_keV':
            # A sampled argmax is quantized; allow one coarse energy bin.
            grid_error = max(grid_error, (1200.0 - 0.5) / 1199)
        numerical_error[key] = grid_error + phase_error
        if key != 'E_peak_keV':
            # Refinement must reach better than 0.1% for these selected scenes.
            # This ceiling is independent of the source-rounding acceptance test.
            scale = max(abs(fine[key]), 1e-12)
            if abs(standard[key] - fine[key]) > 0.001 * scale:
                raise ValueError(f'Grid failed to converge: {row["id"]}/{scenario_id}/{key}')
    checks = reference_checks(scenario_id, standard, numerical_error, reference)
    maximum = kinematic_maximum(row, halo)
    # Exothermic recoils can exceed the 1200 keV grid, although their probability
    # of reconstructing into this sideband is negligible. Integrate that tail
    # explicitly; never claim the cutoff covers support when it does not.
    tail_E = np.arange(1200.125, max(1200.25, maximum + 0.25), 0.25)
    tail_model = Model(row['m_chi_GeV'], row['delta_keV'], row['coupling'], row['sigma_n_cm2'])
    tail_r = rates.dRdE(tail_E, tail_model, halo) * det.exposure_tyr
    a, b = det.sideband
    tail_sig = det.sigma_E(tail_E)
    tail_probability = norm.cdf((b - tail_E) / tail_sig) - norm.cdf((a - tail_E) / tail_sig)
    tail_sb = float(np.sum(tail_r * tail_probability) * 0.25)
    if tail_sb > 1e-10 * standard['N_sb_own_sigma']:
        raise ValueError('Omitted sideband tail exceeds the declared cutoff bound.')
    pred = predictions[1]
    energy = np.unique(np.r_[np.arange(0.5, 600.5, 2.0), 248.0])
    density = np.interp(energy, pred.grid['Erec'], pred.grid['sel_rec']) / pred.N_roi
    # Normalization checks use the full numerical grid, not the decimated plot.
    dE = pred.grid['E'][1] - pred.grid['E'][0]
    integral = float(np.sum(pred.grid['sel_rec']) * dE / pred.N_roi)
    # Gaussian support below the 0.5 keV integration edge is physically tiny here.
    if abs(integral - 1) > 1e-5:
        raise ValueError(f'Selected reconstructed spectrum does not normalize: {integral}')
    result = {
        'benchmark_id': row['id'],
        'status': 'validated stored-audit snapshot',
        'paper_reproduction': row['paper_reproduction'],
        'metrics': standard,
        'undefined_reasons': undefined_reasons(pred, det),
        'curve': {'energy_keV': energy.tolist(),
                  'selected_density_per_roi_keV': density.tolist(),
                  'normalization': 'Selected reconstructed spectrum divided by its ROI count; one expected ROI event, not a refit of published parameters.',
                  'sample_spacing_keV': 2.0,
                  'extra_sample_keV': 248.0,
                  'display_interpolation': 'straight segments between sampled densities; no interpolated halo result'},
        'validation': {'reference': checks,
                       'convergence': {'energy_grids': trials, 'annual_grids': annual,
                                       'absolute_numerical_allowance': numerical_error},
                       'maximum_true_recoil_keV': maximum,
                       'cutoff_covers_true_support': maximum < 1200.0,
                       'omitted_tail': {'method': '0.25 keV midpoint integration above 1200 keV through the analytic isotope endpoint; same halo/response',
                                        'N_sb': tail_sb, 'relative_to_N_sb': tail_sb / standard['N_sb_own_sigma'],
                                        'relative_acceptance_bound': 1e-10,
                                        'N_roi': 0.0, 'roi_reason': 'True-energy efficiency is exactly zero above 285 keV.'},
                       'normalized_full_grid_integral': integral,
                       'normalization_absolute_tolerance': 1e-5},
    }
    result['result_sha256'] = digest(result)
    return result


def rerun_upstream():
    run = subprocess.run([sys.executable, str(HERE / 'validate.py')], cwd=HERE,
                         check=True, capture_output=True, text=True, encoding='utf-8')
    log = run.stdout.replace('\r\n', '\n')
    stored = (HERE / 'results/validation.txt').read_text(encoding='utf-8')
    normalize = lambda s: '\n'.join(line.rstrip() for line in s.splitlines()).strip()
    if normalize(log) != normalize(stored):
        raise ValueError('Upstream validate.py output differs from the stored validation record.')
    return log


def build_manifest():
    rows = inventory()
    with (HERE / 'results/benchmarks_common.csv').open(encoding='utf-8', newline='') as file:
        references = {row['id']: row for row in csv.DictReader(file)}
    log = rerun_upstream()
    scenarios = []
    for name in SCENARIOS:
        halo, det = VARIANTS[name]
        scenarios.append({
            'id': name,
            'label': 'Common halo: escape speed 544 km/s' if name == 'base' else 'Assumption change: escape speed 600 km/s',
            'changed_assumptions': [] if name == 'base' else [{'path': 'halo.vesc', 'from': 544.0, 'to': 600.0, 'unit': 'km/s'}],
            'halo': asdict(halo), 'detector': asdict(det),
            'snapshots': [snapshot(next(r for r in rows if r['id'] == key), name, references[key]) for key in SELECTED],
        })
    manifest = {
        'schema_version': 'lz-scenes/v1',
        'project': 'dark-matter-research/lz-event-audit',
        'experiment_id': 'two-benchmarks-one-halo-change-v1',
        'baseline_revision': BASELINE,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(),
        'environment': {'python': platform.python_version(), 'numpy': np.__version__, 'scipy': scipy.__version__, 'platform': platform.platform(), 'hardware': None,
                        'hardware_unavailable_reason': 'No runtime-performance or device-comparison claim is made.'},
        'reproduce': 'cd lz-event-audit && python scene_export.py --check',
        'observation': OBSERVATION,
        'scope': {'configuration_count': 24, 'paper_count': 14, 'selected_benchmark_ids': list(SELECTED), 'scenario_ids': list(SCENARIOS),
                  'selection_reason': 'A tail-sensitive endothermic higgsino and a heavy exothermic charge-coupled benchmark; selected for contrasting sensitivity, not ranking.',
                  'change_log': [{'version': 1, 'change': 'Export two existing benchmark IDs at base and vesc600; no added benchmark or altered published parameter.'}]},
        'benchmarks': rows,
        'common_assumptions': {
            'halo': asdict(BASE_HALO), 'detector': asdict(BASE_DET),
            'target': 'Natural xenon, nine isotopes with mass-fraction weighting',
            'form_factor': 'Helm; Lewin and Smith parameterization in rates.py',
            'interaction': 'Spin-independent contact; delta>0 endothermic, delta<0 exothermic; QW weak-charge weighting or Z charge weighting',
            'efficiency': {'status': 'approximation', 'definition': 'Piecewise linear in true recoil energy with linear tails',
                           'support_keV': [4.0, 285.0], 'fifty_percent_points_keV': [5.4, 269.9],
                           'roi_definition': 'Integral of true-energy rate times efficiency over its full 4–285 keV support; 5.4 and 269.9 are not hard bounds.'},
            'resolution': 'sigma_E(E)=sqrt(23^2 * E/248 + (0.093*E)^2) keV, Gaussian reconstructed response',
            'sideband': {'reconstructed_window_keV': [350.0, 590.0], 'acceptance': 1.0,
                         'status': 'assumed; unpublished acceptance; approximation applies to every sideband metric'},
            'background': 'Neglected in signal-only shape statistic',
            'normalization': 'Published cross-section stays fixed for absolute counts; curves and R_SB divided by the same predicted ROI count.',
        },
        'units': {'energy': 'keV', 'mass': 'GeV', 'cross_section': 'cm^2', 'speed': 'km/s', 'density': 'GeV/cm^3', 'exposure': 'tonne year',
                  'N_roi_own_sigma': 'events at published cross-section', 'N_sb_own_sigma': 'events at published cross-section; unit sideband acceptance',
                  'R_SB': 'sideband events per ROI event; unit sideband acceptance', 'dchi2': 'dimensionless signal-only shape-plus-sideband statistic',
                  'E_peak_keV': 'keV, sampled argmax', 'p_event_per_roi': '1/keV', 'selected_density_per_roi_keV': '1/keV'},
        'numerical_protocol': {
            'engine': 'rates.py predict; no new rate formula', 'true_and_reconstructed_grid': {'minimum_keV': 0.5, 'maximum_keV': 1200.0, 'n': 2400, 'spacing_keV': 0.5, 'quadrature': 'uniform endpoint sum, as in the original audit'},
            'annual_samples': 48, 'annual_quadrature': 'equally spaced midpoint phases over one year',
            'refinement_energy_n': [1200, 2400, 4800], 'refinement_annual_n': [48, 96, 192],
            'reference_precision': 'Stored CSV rounded with .4g; half of last significant-digit unit.',
            'tolerance_rule': 'Before acceptance: CSV half-rounding unit + 2*max successive energy-grid differences + 2*max successive annual-grid differences; sampled peak also allows one coarse energy bin.',
            'convergence_ceiling': '2400-to-4800 difference <=0.1% for smooth metrics; numerical allowance is not a scientific uncertainty.',
            'normalization': 'Full selected reconstructed grid integral / true-efficiency ROI integral within 1e-5 of unity for selected scope.',
            'cutoff_check': 'Analytic largest true recoil endpoint over nine xenon isotopes; integrate any omitted sideband tail above 1200 keV with 0.25 keV midpoint bins. Tail must be <1e-10 of sideband count; selected ROI has no tail above 285 keV.',
            'undefined_policy': 'Zero ROI / forbidden / zero density => normalized metrics and peak null with explicit reasons; never publish Infinity or a zero-grid argmax as a finding.',
        },
        'sources': [
            {'id': 'lz-2609.02823v1', 'owner': 'LZ Collaboration', 'url': 'https://arxiv.org/abs/2609.02823v1', 'version': 'v1', 'license': 'CC BY-NC-SA 4.0', 'terms_url': 'https://creativecommons.org/licenses/by-nc-sa/4.0/', 'decision': 'link-only', 'included_material': 'Bibliographic metadata and attributed reported facts; no paper figure or article bytes.', 'sha256': None, 'hash_unavailable_reason': 'Third-party article is not bundled.'},
            {'id': 'rodd-2609.04175', 'owner': 'Rodd, Safdi, Slatyer and Xu', 'url': 'https://arxiv.org/abs/2609.04175v1', 'version': 'v1', 'license': 'CC BY 4.0', 'terms_url': 'https://creativecommons.org/licenses/by/4.0/', 'decision': 'link-only', 'included_material': 'Parameters already transcribed in the pinned audit; no third-party figure or article bytes.', 'sha256': None, 'hash_unavailable_reason': 'Third-party article is not bundled.'},
            {'id': 'baer-barger-2609.06153', 'owner': 'Baer and Barger', 'url': 'https://arxiv.org/abs/2609.06153v1', 'version': 'v1', 'license': 'CC BY 4.0', 'terms_url': 'https://creativecommons.org/licenses/by/4.0/', 'decision': 'link-only', 'included_material': 'Parameters already transcribed in the pinned audit; no third-party figure or article bytes.', 'sha256': None, 'hash_unavailable_reason': 'Third-party article is not bundled.'},
            {'id': 'official-hepdata', 'owner': 'LZ Collaboration / HEPData', 'url': 'https://doi.org/10.17182/hepdata.182472.v1', 'version': 'v1', 'license': None, 'decision': 'not included', 'retrieval_status': 'Not retrieved; not checked; approximation retained.', 'sha256': None, 'hash_unavailable_reason': 'Release unavailable to this audit.'},
            {'id': 'independent-audit', 'owner': 'Brandon Frank Han-Chween Huang', 'url': 'https://github.com/bomberJV/dark-matter-research/tree/' + BASELINE + '/lz-event-audit', 'version': BASELINE, 'license': 'Code Apache-2.0; original writing/results CC BY 4.0', 'terms_url': 'https://github.com/bomberJV/dark-matter-research/blob/' + BASELINE + '/README.md', 'decision': 'cleared for intended repository use', 'included_material': 'Original independently computed numerical output; original implementation.'},
        ],
        'limitations': LIMITATIONS,
        'scenarios': scenarios,
        'source_files': {path: file_digest(HERE / path) for path in SOURCE_PATHS},
        'source_hash_encoding': 'SHA-256 of UTF-8 text bytes, CRLF normalized to LF',
        'upstream_validation': {'command': 'python validate.py', 'status': 'rerun matches stored report', 'log_path': 'validation-rerun.txt',
                                'sha256': hashlib.sha256(log.encode('utf-8')).hexdigest(),
                                'comparison': 'Normalize line endings and trailing whitespace only; contains non-reproductions and discrepancies, not a universal pass.'},
    }
    manifest['result_sha256'] = digest({'observation': manifest['observation'], 'scenarios': scenarios})
    manifest['manifest_sha256'] = digest(manifest)
    return manifest, log


def verify_artifact(manifest):
    if manifest.get('schema_version') != 'lz-scenes/v1':
        raise ValueError('Unsupported scene schema')
    copy = dict(manifest)
    recorded = copy.pop('manifest_sha256')
    if digest(copy) != recorded:
        raise ValueError('Manifest content hash mismatch')
    if digest({'observation': manifest['observation'], 'scenarios': manifest['scenarios']}) != manifest['result_sha256']:
        raise ValueError('Result hash mismatch')
    if manifest['observation'] != OBSERVATION:
        raise ValueError('Reported observation changed')
    if tuple(s['id'] for s in manifest['scenarios']) != SCENARIOS:
        raise ValueError('Unsupported scenario set')
    if manifest['benchmarks'] != inventory():
        raise ValueError('Benchmark catalog or qualifications changed')
    if manifest['scope']['selected_benchmark_ids'] != list(SELECTED):
        raise ValueError('Selected benchmark IDs changed')
    if manifest['scope']['configuration_count'] != 24 or manifest['scope']['paper_count'] != 14:
        raise ValueError('Benchmark/paper scope changed')
    if set(manifest['source_files']) != set(SOURCE_PATHS):
        raise ValueError('Required source hash entries changed')
    by_id = {row['id']: row for row in manifest['benchmarks']}
    for scene in manifest['scenarios']:
        halo, det = VARIANTS[scene['id']]
        if canonical(scene['halo']) != canonical(asdict(halo)) or canonical(scene['detector']) != canonical(asdict(det)):
            raise ValueError('Unsupported halo or detector setting')
        expected_change = [] if scene['id'] == 'base' else [{'path': 'halo.vesc', 'from': 544.0, 'to': 600.0, 'unit': 'km/s'}]
        if scene['changed_assumptions'] != expected_change:
            raise ValueError('Assumption-change record changed')
        if [item['benchmark_id'] for item in scene['snapshots']] != list(SELECTED):
            raise ValueError('Snapshot selection changed')
        for item in scene['snapshots']:
            payload = dict(item)
            recorded_hash = payload.pop('result_sha256')
            if digest(payload) != recorded_hash:
                raise ValueError('Snapshot content hash mismatch')
            if item['paper_reproduction'] != by_id[item['benchmark_id']]['paper_reproduction']:
                raise ValueError('Snapshot qualification changed')
    for path, expected in manifest['source_files'].items():
        if file_digest(HERE / path) != expected:
            raise ValueError('Source changed; regenerate receipt: ' + path)
    log = (OUT / manifest['upstream_validation']['log_path']).read_bytes().replace(b'\r\n', b'\n')
    if hashlib.sha256(log).hexdigest() != manifest['upstream_validation']['sha256']:
        raise ValueError('Validation log hash mismatch')


def check_recomputed(recorded, fresh):
    # Presentation/provenance fields must regenerate exactly. Runtime metadata
    # and numerical payloads are handled separately to permit portable reruns.
    volatile = {'generated_at_utc', 'environment', 'scenarios', 'manifest_sha256', 'result_sha256'}
    for key in set(recorded) | set(fresh):
        if key not in volatile and canonical(recorded.get(key)) != canonical(fresh.get(key)):
            raise ValueError('Recomputed manifest metadata differs: ' + key)
    def compare_receipt(old, new, path='snapshot'):
        # Numerical evidence is itself reproduced. An old, edited tolerance must
        # never become the authority for accepting a later result. This guard
        # permits only tiny cross-runtime floating-point differences, not the
        # much larger grid-error allowances used for rounded source comparisons.
        if isinstance(new, dict):
            if set(old) != set(new):
                raise ValueError('Receipt fields differ: ' + path)
            for key in new:
                if key != 'result_sha256':
                    compare_receipt(old[key], new[key], path + '/' + key)
        elif isinstance(new, list):
            if len(old) != len(new):
                raise ValueError('Receipt array length differs: ' + path)
            for index, (a, b) in enumerate(zip(old, new, strict=True)):
                compare_receipt(a, b, path + '/' + str(index))
        elif isinstance(new, (float, int)) and not isinstance(new, bool):
            if not math.isclose(old, new, rel_tol=1e-8, abs_tol=1e-14):
                raise ValueError('Receipt numerical evidence differs: ' + path)
        elif old != new:
            raise ValueError('Receipt value differs: ' + path)
    for old_s, new_s in zip(recorded['scenarios'], fresh['scenarios'], strict=True):
        if canonical(old_s['halo']) != canonical(new_s['halo']) or canonical(old_s['detector']) != canonical(new_s['detector']):
            raise ValueError('Scene settings changed')
        for old, new in zip(old_s['snapshots'], new_s['snapshots'], strict=True):
            if old['benchmark_id'] != new['benchmark_id']:
                raise ValueError('Benchmark changed')
            for key in METRICS:
                allowance = new['validation']['convergence']['absolute_numerical_allowance'][key]
                # A tiny floating-point guard applies to same-grid recomputation.
                guard = 1e-10 * max(abs(old['metrics'][key]), 1e-12)
                if abs(old['metrics'][key] - new['metrics'][key]) > allowance + guard:
                    raise ValueError(f'Recomputed metric differs: {old["benchmark_id"]}/{key}')
            np.testing.assert_allclose(old['curve']['energy_keV'], new['curve']['energy_keV'], rtol=0, atol=0)
            np.testing.assert_allclose(old['curve']['selected_density_per_roi_keV'], new['curve']['selected_density_per_roi_keV'], rtol=1e-8, atol=1e-14)
            compare_receipt(old, new)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='verify committed hashes, rerun validation, and recompute the selected scenes')
    args = parser.parse_args()
    if args.check:
        old = json.loads((OUT / 'manifest.json').read_text(encoding='utf-8'))
        verify_artifact(old)
        fresh, _ = build_manifest()
        check_recomputed(old, fresh)
        print('LZ scene export: committed hashes, upstream validation, convergence, normalization and four snapshots pass.')
    else:
        manifest, log = build_manifest()
        OUT.mkdir(exist_ok=True)
        (OUT / 'validation-rerun.txt').write_text(log, encoding='utf-8', newline='\n')
        (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf-8', newline='\n')
        print('Wrote scenes/manifest.json and scenes/validation-rerun.txt; result ' + manifest['result_sha256'])


if __name__ == '__main__':
    main()
