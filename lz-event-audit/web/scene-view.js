// Read-only adapter for validated, discrete LZ scene exports. No rate calculation.
const SCHEMA = 'lz-scenes/v1';

function copyAndFreeze(value, path = 'manifest') {
  if (typeof value === 'number' && !Number.isFinite(value)) throw new TypeError(`${path}: non-finite number`);
  if (value === null || typeof value !== 'object') return value;
  const copy = Array.isArray(value) ? value.map((v, i) => copyAndFreeze(v, `${path}[${i}]`))
    : Object.fromEntries(Object.entries(value).map(([k, v]) => [k, copyAndFreeze(v, `${path}.${k}`)]));
  return Object.freeze(copy);
}

function uniqueIds(items, field, label) {
  if (!Array.isArray(items) || items.length === 0) throw new TypeError(`${label}: missing entries`);
  const ids = items.map((item) => item[field]);
  if (ids.some((id) => typeof id !== 'string' || !id) || new Set(ids).size !== ids.length) {
    throw new TypeError(`${label}: missing or duplicate IDs`);
  }
  return new Set(ids);
}

export function createSceneStore(input) {
  if (input?.schema_version !== SCHEMA) throw new TypeError('Unsupported scene schema');
  const manifest = copyAndFreeze(input);
  if (!manifest.observation || !manifest.common_assumptions) throw new TypeError('Missing evidence context');
  const benchmarkIds = uniqueIds(manifest.benchmarks, 'id', 'benchmarks');
  uniqueIds(manifest.scenarios, 'id', 'scenarios');
  const selected = manifest.benchmarks.filter((b) => b.selected).map((b) => b.id).sort();
  if (selected.length !== 2) throw new TypeError('This export requires two selected benchmarks');
  for (const scenario of manifest.scenarios) {
    const snapshotIds = uniqueIds(scenario.snapshots, 'benchmark_id', 'snapshots');
    if ([...snapshotIds].sort().join('|') !== selected.join('|')) throw new TypeError('Scenario benchmark set changed');
    for (const snapshot of scenario.snapshots) {
      if (!benchmarkIds.has(snapshot.benchmark_id)) throw new TypeError('Unknown benchmark');
      const energy = snapshot.curve?.energy_keV;
      const density = snapshot.curve?.selected_density_per_roi_keV;
      if (!Array.isArray(energy) || !Array.isArray(density) || energy.length !== density.length || energy.length < 2) {
        throw new TypeError('Invalid recorded curve');
      }
      if (energy.some((e, i) => !Number.isFinite(e) || (i && e <= energy[i - 1]))
        || density.some((d) => d !== null && (!Number.isFinite(d) || d < 0))) throw new TypeError('Invalid curve values');
    }
  }
  return Object.freeze({
    manifest,
    scenarioIds: Object.freeze(manifest.scenarios.map((s) => s.id)),
    select(scenarioId) {
      const scenario = manifest.scenarios.find((s) => s.id === scenarioId);
      if (!scenario) throw new RangeError(`Unknown recorded scenario: ${scenarioId}`);
      return Object.freeze({
        observation: manifest.observation,
        common_assumptions: manifest.common_assumptions,
        scenario,
        benchmarks: Object.freeze(scenario.snapshots.map((snapshot) =>
          manifest.benchmarks.find((b) => b.id === snapshot.benchmark_id))),
      });
    },
  });
}
