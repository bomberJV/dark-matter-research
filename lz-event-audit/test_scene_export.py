"""Acceptance checks for the recorded LZ investigation, independent of rendering.

Run: python -m unittest discover -s lz-event-audit -p test_scene_export.py
The exporter --check separately repeats the expensive full-grid convergence run.
"""
from __future__ import annotations

from copy import deepcopy
import csv
from dataclasses import asdict, replace
import hashlib
import json
import math
from pathlib import Path
import unittest

import numpy as np
from scipy.stats import norm

import rates
import scene_export as export
from audit import VARIANTS


HERE = Path(__file__).resolve().parent


def independent_digest(value):
    data = json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False).encode('utf-8')
    return hashlib.sha256(data).hexdigest()


def rehash(manifest):
    """Allow negative tests to reach semantic validation, beyond byte integrity."""
    manifest['result_sha256'] = independent_digest({
        'observation': manifest['observation'], 'scenarios': manifest['scenarios']})
    body = {k: v for k, v in manifest.items() if k != 'manifest_sha256'}
    manifest['manifest_sha256'] = independent_digest(body)
    return manifest


class SceneExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        def reject_nonfinite(token):
            raise ValueError('Non-standard JSON numeric token: ' + token)
        cls.manifest = json.loads((HERE / 'scenes/manifest.json').read_text(encoding='utf-8'),
                                  parse_constant=reject_nonfinite)
        with (HERE / 'benchmarks.csv').open(encoding='utf-8', newline='') as file:
            cls.catalog = {row['id']: row for row in csv.DictReader(file)}
        with (HERE / 'results/benchmarks_common.csv').open(encoding='utf-8', newline='') as file:
            cls.references = {row['id']: row for row in csv.DictReader(file)}

    def snapshots(self):
        for scenario in self.manifest['scenarios']:
            for snapshot in scenario['snapshots']:
                yield scenario, snapshot

    def test_l01_complete_pinned_catalog_and_unchanged_parameters(self):
        catalog = self.manifest['benchmarks']
        self.assertEqual(len(catalog), 24)
        self.assertEqual(len({b['arxiv'] for b in catalog}), 14)
        self.assertEqual({b['id'] for b in catalog}, set(self.catalog))
        self.assertEqual(self.manifest['scope']['configuration_count'], 24)
        self.assertEqual(self.manifest['scope']['paper_count'], 14)
        self.assertEqual({b['id'] for b in catalog if b['selected']},
                         {'rodd-higgsino', 'baer-barger-300'})
        for b in catalog:
            source = self.catalog[b['id']]
            for field in ('arxiv', 'authors', 'coupling', 'claim', 'paper_halo', 'note'):
                self.assertEqual(b[field], source[field], (b['id'], field))
            for field in ('m_chi_GeV', 'delta_keV', 'sigma_n_cm2'):
                self.assertEqual(b[field], float(source[field]) if source[field] else None)

    def test_l02_reference_tolerances_follow_recorded_protocol(self):
        """Recompute the allowance from the raw trial values and CSV precision."""
        for scenario, snapshot in self.snapshots():
            validation = snapshot['validation']
            conv = validation['convergence']
            trials = conv['energy_grids']
            annual = conv['annual_grids']
            self.assertEqual([t['n'] for t in trials], [1200, 2400, 4800])
            self.assertEqual([t['n_time'] for t in annual], [96, 192])
            for metric, check in validation['reference'].items():
                with self.subTest(benchmark=snapshot['benchmark_id'], scenario=scenario['id'], metric=metric):
                    stored = self.references[snapshot['benchmark_id']][check['csv_column']]
                    self.assertEqual(check['stored_text'], stored)
                    value = abs(float(stored))
                    rounding = 0.5 * 10 ** (math.floor(math.log10(value)) - 3) if value else 0
                    coarse, standard, fine = [t['metrics'][metric] for t in trials]
                    grid_error = 2 * max(abs(coarse - standard), abs(standard - fine))
                    if metric == 'E_peak_keV':
                        grid_error = max(grid_error, 1199.5 / 1199)
                    phase_a, phase_b = [t['metrics'][metric] for t in annual]
                    phase_error = 2 * max(abs(standard - phase_a), abs(phase_a - phase_b))
                    allowance = rounding + grid_error + phase_error
                    self.assertAlmostEqual(check['absolute_tolerance'], allowance, places=13)
                    self.assertEqual(check['recomputed'], snapshot['metrics'][metric])
                    self.assertLessEqual(abs(snapshot['metrics'][metric] - float(stored)), allowance)
                    self.assertTrue(check['passed'])
            self.assertEqual(set(validation['reference']),
                             {'R_SB', 'dchi2', 'N_roi_own_sigma', 'E_peak_keV'}
                             if scenario['id'] == 'base' else {'R_SB', 'dchi2'})

    def test_l03_finite_json_and_explicit_units(self):
        json.dumps(self.manifest, allow_nan=False)
        units = self.manifest['units']
        self.assertEqual(units['energy'], 'keV')
        self.assertEqual(units['mass'], 'GeV')
        self.assertEqual(units['cross_section'], 'cm^2')
        self.assertEqual(units['speed'], 'km/s')
        self.assertEqual(units['selected_density_per_roi_keV'], '1/keV')
        for _, snapshot in self.snapshots():
            m = snapshot['metrics']
            self.assertGreater(m['N_roi_own_sigma'], 0)
            self.assertAlmostEqual(m['R_SB'], m['N_sb_own_sigma'] / m['N_roi_own_sigma'])
            check = snapshot['validation']
            self.assertLessEqual(abs(check['normalized_full_grid_integral'] - 1),
                                 check['normalization_absolute_tolerance'])

    def test_l03_curve_uses_roi_normalization_not_visible_range(self):
        """An O(n) Gaussian convolution checks the exported 248-keV sample.

        This uses the existing differential rate, without predict's full kernel
        or the exporter's plot interpolation and without renormalizing the curve.
        """
        protocol = self.manifest['numerical_protocol']['true_and_reconstructed_grid']
        energies = np.linspace(protocol['minimum_keV'], protocol['maximum_keV'], protocol['n'])
        step = energies[1] - energies[0]
        for scenario, snapshot in self.snapshots():
            row = self.catalog[snapshot['benchmark_id']]
            model = rates.Model(float(row['m_chi_GeV']), float(row['delta_keV']),
                                row['coupling'], float(row['sigma_n_cm2']))
            halo = rates.Halo(**scenario['halo'])
            detector = rates.Detector(**scenario['detector'])
            selected = (rates.dRdE(energies, model, halo) * detector.exposure_tyr
                        * detector.efficiency(energies))
            roi = float(np.sum(selected) * step)
            density = float(np.sum(selected * norm.pdf(248.0,
                            loc=detector.energy_scale * energies,
                            scale=detector.energy_scale * detector.sigma_E(energies))) * step / roi)
            index = snapshot['curve']['energy_keV'].index(248.0)
            actual = snapshot['curve']['selected_density_per_roi_keV'][index]
            self.assertTrue(math.isclose(actual, density, rel_tol=2e-12, abs_tol=1e-15))
            self.assertTrue(math.isclose(snapshot['metrics']['N_roi_own_sigma'], roi, rel_tol=2e-12))
            self.assertTrue(math.isclose(snapshot['metrics']['p_event_per_roi'], density, rel_tol=2e-12))

    def test_l03_zero_roi_and_forbidden_have_no_shape_or_peak(self):
        cases = (
            rates.Model(50, 1000, 'Z'),
            rates.Model(300, -300, 'Z', 0.0),
        )
        for model in cases:
            with self.subTest(model=model):
                pred = rates.predict(model, VARIANTS['base'][0], VARIANTS['base'][1], n=120)
                values = export.metrics(pred, VARIANTS['base'][1])
                reasons = export.undefined_reasons(pred, VARIANTS['base'][1])
                self.assertEqual(values['N_roi_own_sigma'], 0)
                for metric in ('R_SB', 'dchi2', 'E_peak_keV', 'p_event_per_roi'):
                    self.assertIsNone(values[metric], metric)
                    self.assertIn('undefined', reasons[metric])
                json.dumps(values, allow_nan=False)
        no_event_density = rates.Prediction(1, 0, 0, 0, 0, 100, 0)
        self.assertIsNone(export.metrics(no_event_density, VARIANTS['base'][1])['dchi2'])
        self.assertIn('density', export.undefined_reasons(no_event_density, VARIANTS['base'][1])['dchi2'])
        rates._KERNELS.clear()

    def test_l03_cross_section_and_halo_density_scale_rates(self):
        energies = np.linspace(4.0, 285.0, 600)
        model = rates.Model(300, -300, 'Z', 1.5e-45)
        halo, _ = VARIANTS['base']
        base = rates.dRdE(energies, model, halo)
        doubled = rates.dRdE(energies, replace(model, sigma_n=3e-45), halo)
        np.testing.assert_allclose(doubled, 2 * base, rtol=1e-13, atol=0)
        np.testing.assert_allclose(rates.dRdE(energies, model, replace(halo, rho=0.6)),
                                   2 * base, rtol=1e-13, atol=0)

    def test_l03_exothermic_tail_is_bounded_not_declared_absent(self):
        for _, snapshot in self.snapshots():
            validation = snapshot['validation']
            tail = validation['omitted_tail']
            if snapshot['benchmark_id'] == 'baer-barger-300':
                self.assertGreater(validation['maximum_true_recoil_keV'], 1200)
                self.assertFalse(validation['cutoff_covers_true_support'])
                self.assertGreater(tail['N_sb'], 0)
            else:
                self.assertLess(validation['maximum_true_recoil_keV'], 1200)
                self.assertTrue(validation['cutoff_covers_true_support'])
                self.assertEqual(tail['N_sb'], 0)
            self.assertEqual(tail['N_roi'], 0)
            self.assertIn('285', tail['roi_reason'])
            self.assertLessEqual(tail['relative_to_N_sb'], tail['relative_acceptance_bound'])

    def test_l04_only_escape_speed_changes_and_observation_is_fixed(self):
        observation = self.manifest['observation']
        self.assertEqual(observation['id'], 'lz-high-energy-candidate-2023-06-16')
        self.assertEqual(observation['energy_keV'], 248)
        self.assertEqual(observation['statistical_uncertainty_keV'], 23)
        self.assertEqual(observation['systematic_uncertainty_keV'], 23)
        self.assertIs(observation['uncertainties_combined'], False)
        self.assertEqual(observation['source']['version'], 'v1')
        scenarios = self.manifest['scenarios']
        self.assertEqual([s['id'] for s in scenarios], ['base', 'vesc600'])
        base, changed = scenarios
        self.assertEqual(base['detector'], changed['detector'])
        self.assertEqual({k for k in base['halo'] if base['halo'][k] != changed['halo'][k]}, {'vesc'})
        self.assertEqual(base['halo']['vesc'], 544)
        self.assertEqual(changed['halo']['vesc'], 600)
        self.assertEqual(changed['changed_assumptions'],
                         [{'path': 'halo.vesc', 'from': 544.0, 'to': 600.0, 'unit': 'km/s'}])
        for scenario in scenarios:
            self.assertEqual(scenario['halo'], asdict(VARIANTS[scenario['id']][0]))
            self.assertEqual({s['benchmark_id'] for s in scenario['snapshots']}, set(export.SELECTED))
            self.assertNotIn('observation', scenario, 'One shared immutable observation belongs to the manifest.')

    def test_l05_qualifications_and_approximations_survive(self):
        catalog = {b['id']: b for b in self.manifest['benchmarks']}
        for key in ('su-yang-yang', 'dent-newstead-exo'):
            self.assertEqual(catalog[key]['paper_reproduction']['status'], 'not reproduced')
        self.assertIn('inferred', catalog['gce-simple']['paper_reproduction']['status'])
        self.assertIn('sign inferred', catalog['gce-simple']['note'])
        self.assertIn('converted', catalog['fan-he-bestfit']['note'])
        self.assertEqual(catalog['delepine-khalil']['paper_reproduction']['status'], 'partial discrepancy')
        common = self.manifest['common_assumptions']
        self.assertEqual(common['efficiency']['status'], 'approximation')
        self.assertEqual(common['efficiency']['support_keV'], [4, 285])
        self.assertEqual(common['sideband']['acceptance'], 1)
        self.assertIn('unpublished', common['sideband']['status'])
        self.assertIn('Neglected', common['background'])
        self.assertIn('Helm', common['form_factor'])
        self.assertTrue(any('HEPData' in s and 'not been retrieved' in s for s in self.manifest['limitations']))
        for _, snapshot in self.snapshots():
            self.assertEqual(snapshot['paper_reproduction'], catalog[snapshot['benchmark_id']]['paper_reproduction'])
            self.assertEqual(snapshot['paper_reproduction']['status'], 'approximate paper comparison')

    def test_l06_candidate_and_geometry_disclosures(self):
        observation = self.manifest['observation']
        self.assertIn('not a discovery', observation['status'])
        self.assertIsNone(observation['measured_event_position'])
        self.assertIn('illustrations', observation['position_unavailable_reason'])
        self.assertIsNone(observation['source']['sha256'])
        self.assertTrue(observation['source']['hash_unavailable_reason'])
        self.assertTrue(all(snapshot['curve']['display_interpolation'] for _, snapshot in self.snapshots()))

    def test_all_recorded_source_and_result_hashes(self):
        export.verify_artifact(self.manifest)
        for path, recorded in self.manifest['source_files'].items():
            actual = hashlib.sha256((HERE / path).read_bytes().replace(b'\r\n', b'\n')).hexdigest()
            self.assertEqual(actual, recorded, path)
        for _, snapshot in self.snapshots():
            body = {k: v for k, v in snapshot.items() if k != 'result_sha256'}
            self.assertEqual(independent_digest(body), snapshot['result_sha256'])
        body = {k: v for k, v in self.manifest.items() if k != 'manifest_sha256'}
        self.assertEqual(independent_digest(body), self.manifest['manifest_sha256'])

    def test_corrupt_result_is_rejected(self):
        damaged = deepcopy(self.manifest)
        damaged['scenarios'][0]['snapshots'][0]['metrics']['R_SB'] += 1
        with self.assertRaises(ValueError):
            export.verify_artifact(damaged)

    def test_rehashed_observation_change_is_rejected(self):
        damaged = deepcopy(self.manifest)
        damaged['observation']['energy_keV'] = 249
        with self.assertRaises(ValueError):
            export.verify_artifact(rehash(damaged))

    def test_rehashed_second_assumption_change_is_rejected(self):
        damaged = deepcopy(self.manifest)
        damaged['scenarios'][1]['halo']['v0'] = 220
        with self.assertRaises(ValueError):
            export.verify_artifact(rehash(damaged))

    def test_rehashed_lost_qualification_is_rejected(self):
        damaged = deepcopy(self.manifest)
        row = next(b for b in damaged['benchmarks'] if b['id'] == 'gce-simple')
        row['paper_reproduction'] = {'status': 'validated', 'qualification': ''}
        with self.assertRaises(ValueError):
            export.verify_artifact(rehash(damaged))

    def test_changed_source_hash_is_rejected(self):
        damaged = deepcopy(self.manifest)
        damaged['source_files']['rates.py'] = '0' * 64
        with self.assertRaises(ValueError):
            export.verify_artifact(rehash(damaged))


if __name__ == '__main__':
    unittest.main()
