from pathlib import Path
import json, re, html, shutil, zipfile, hashlib
from html.parser import HTMLParser
BASE=Path(__file__).resolve().parent
OUT=BASE/'results'
WEB=BASE/'web'
WEB.mkdir(parents=True,exist_ok=True)
S=json.loads((OUT/'summary.json').read_text())
blocks=[]
def h(title,ident):blocks.append(('heading',title,ident))
def p(text):blocks.append(('paragraph',text))
def eq(text):blocks.append(('equation',text))
def fig(name,caption):blocks.append(('figure',name,caption))
def table(headers,rows):blocks.append(('table',headers,rows))
def cite(n):return f'<a href="#ref-{n}">[{n}]</a>'
refs=[
('Planck Collaboration (2020). Planck 2018 results. VI. Cosmological parameters. A&A 641, A6.','https://arxiv.org/abs/1807.06209','Peer-reviewed; foundational cosmological inference.'),
('Clowe et al. (2006). A direct empirical proof of the existence of dark matter. ApJL 648, L109.','https://arxiv.org/abs/astro-ph/0608407','Peer-reviewed; cluster lensing / gas separation.'),
('Lelli, McGaugh & Schombert (2016). SPARC: Mass Models for 175 Disk Galaxies with Spitzer Photometry and Accurate Rotation Curves. AJ 152, 157.','https://arxiv.org/abs/1606.09251','Peer-reviewed; observational data source, with original rotation-curve references in its catalog.'),
('Navarro, Frenk & White (1997). A Universal Density Profile from Hierarchical Clustering. ApJ 490, 493.','https://arxiv.org/abs/astro-ph/9611107','Peer-reviewed; NFW profile.'),
('Burkert (1995). The Structure of Dark Matter Haloes in Dwarf Galaxies. ApJL 447, L25.','https://arxiv.org/abs/astro-ph/9504041','Peer-reviewed; empirical cored profile. The profile is used here, not all historical interpretations.'),
('Akerib et al., LZ (2026). Search for dark matter particle interactions in an extended nuclear recoil energy window.','https://arxiv.org/abs/2609.02823','Preprint, submitted September 2, 2026; not a dark-matter discovery.'),
('Akerib et al., LZ (2026). Searches for Light Dark Matter and Evidence of Coherent Elastic Neutrino-Nucleus Scattering of Solar Neutrinos. PRL 137, 091806.','https://doi.org/10.1103/jvqf-njpj','Peer-reviewed; 4.5σ solar-neutrino evidence, no significant dark-matter excess in this search.'),
('Aprile et al., XENON (2025). WIMP Dark Matter Search Using a 3.1 Tonne-Year Exposure of the XENONnT Experiment. PRL 135, 221003.','https://doi.org/10.1103/msw4-t342','Peer-reviewed; model-specific elastic-scattering limits.'),
('Verdiani et al. (2026). Constraints on ultralight axions from the DESI DR1 full shape, Planck, and ACT datasets. PRD 114, 083506.','https://doi.org/10.1103/pcl1-6qc1','Peer-reviewed, October 5, 2026; mass-dependent cosmological constraints.'),
('Kong, Nadler & Yu (2026). Strong-lensing perturber signatures in self-interacting dark matter simulations. PRD 114, 043011.','https://doi.org/10.1103/xrqk-1w95','Peer-reviewed; simulation-based mechanism, not a particle detection.'),
('Gilman et al. (2026). Hints of self-interacting dark matter from strong gravitational lensing.','https://arxiv.org/abs/2610.40766','October 29 preprint; abstract-level review only, full text inaccessible during this search.'),
('ESA (November 12, 2026). Euclid lays the foundation for its best-ever 3D map of the Universe.','https://www.esa.int/articles/about-us/directorates/science/euclid/euclid-lays-the-foundation-for-its-best-ever-3d-map-of-the-universe','Official mission release; DR1-Foundation, not full DR1.'),
('Pontzen & Governato (2012). How supernova feedback turns dark matter cusps into cores. MNRAS 421, 3464.','https://arxiv.org/abs/1106.0499','Peer-reviewed; baryonic-feedback mechanism.'),
('Zeng et al. (2025). Diversity and universality: Evolution of dwarf galaxies with self-interacting dark matter. PRD 112, 063008.','https://doi.org/10.1103/x9t4-3zy7','Peer-reviewed; idealized simulations of stars, SIDM and orbital evolution.'),
('Gurian & May (2025). Core Collapse Beyond the Fluid Approximation: The Late Evolution of Self-Interacting Dark Matter Halos. PRL 135, 221001.','https://doi.org/10.1103/2ycz-3fvv','Peer-reviewed; numerical/modeling caveat for late collapse.'),
('Hall et al. (2010). Freeze-In Production of FIMP Dark Matter. JHEP 03, 080.','https://arxiv.org/abs/0911.1120','Peer-reviewed; primary production-mechanism proposal.'),
('ADMX Collaboration (2025). ADMX Axion Dark Matter Bounds around 3.3 μeV with Dine-Fischler-Srednicki-Zhitnitsky Discovery Ability. PRL 134, 111002.','https://doi.org/10.1103/PhysRevLett.134.111002','Peer-reviewed; narrow-band axion search, not all axion masses.'),
('Fan et al. (2026). Inelastic Dark Matter and High-Energy Recoil Signatures in LZ. Chinese Physics Letters 43, 110201.','https://doi.org/10.1088/0256-307X/43/11/110201','Published theoretical interpretation; does not establish the origin of the LZ event.'),
('Kong & Yu (2026). Gravothermal Collapse: Robust Against Baryonic Feedback.','https://arxiv.org/abs/2605.31335','May 29 preprint; controlled, imposed-potential experiment.'),
('Preskill, Wise & Wilczek (1983). Cosmology of the invisible axion. Physics Letters B 120, 127.','https://doi.org/10.1016/0370-2693(83)90637-8','Primary axion-misalignment mechanism paper.'),
]
h('Abstract','abstract')
p(f'Dark matter is well supported as a gravitational component, but its microscopic identity remains unresolved. This working paper asks a narrower question: <strong>which observations discriminate physical mechanisms, and which merely discriminate convenient fitting functions?</strong> A targeted evidence synthesis covers verified experimental and observational results available through November 13, 2026. It is paired with a new, reproducible analysis of {S["sample_n"]} SPARC galaxies ({S["radial_points"]:,} radial measurements), using two-parameter NFW and Burkert halo profiles, and a controlled synthetic-recovery experiment. At the baseline stellar mass-to-light ratio, the cored profile has lower χ² in {S["burkert_lower_chi2"]} galaxies and NFW in {S["nfw_lower_chi2"]}; {S["within_2"]} have |Δχ²| &lt; 2. Changing the assumed disc mass-to-light ratio from 0.3 to 0.7 reverses the preference sign in {S["preference_sign_changes_ml_03_to_07"]} cases. These are conditional fit diagnostics, not evidence for a particular particle or a population-level model probability. The most informative near-term program combines recoil spectra, halo evolution, lensing populations and cosmological structure, while testing their nuisance assumptions explicitly.')
h('1. Evidence of a missing component; uncertainty about its identity','evidence')
p('The attractive part of the dark-matter problem is that the evidence is distributed across very different experiments. In the standard cosmological framework, microwave-background structure requires substantially more matter than baryons supply. Planck infers Ω<sub>c</sub>h² = 0.120 ± 0.001 and Ω<sub>b</sub>h² = 0.0224 ± 0.0001 in its base model; these are cosmological inferences, not a chemical identification. '+cite(1)+' Cluster collisions offer a spatial test: in the Bullet Cluster, the lensing-inferred mass is displaced from much of the hot, X-ray-emitting gas. '+cite(2))
p('Galaxy rotation curves add detailed local structure. They constrain the radial gravitational field, but a circular speed is the combined effect of stars, gas and any halo. Distances, viewing geometry and non-circular motions also enter. A flexible mass model can fit a curve without revealing how its invisible component was produced. A successful explanation must address galaxies, clusters and cosmology consistently. Modified-gravity models are not tested in the numerical work below; this paper therefore does not claim to rule them out.')
h('2. What changed recently','recent')
table(['Result','What it establishes','What remains open'],[
('LZ, September 2026 '+cite(6),'One high-energy candidate recoil; 2.6σ global significance after the look-elsewhere correction.','Independent exposure, background confirmation and repeatable spectral evidence.'),
('LZ solar-neutrino analysis '+cite(7),'4.5σ evidence consistent with boron-8 coherent neutrino scattering in 5.7 tonne-years.','No significant dark-matter excess in this low-mass search.'),
('DESI + CMB, October 2026 '+cite(9),'Tighter limits on selected ultralight-axion fractions; a DESI-only hint disappears with CMB data.','Other masses, couplings and production histories remain different hypotheses.'),
('SIDM lensing work, 2026 '+cite(10)+' '+cite(11),'Simulated dense collapsed structures and a new model-dependent lensing hint.','Uniqueness, selection effects, baryonic degeneracies and independent replication.'),
('Euclid, November 12, 2026 '+cite(12),'DR1-Foundation adds around 15,000 strong-lensing candidates across a much larger survey.','Candidates require vetting; a catalog is not a particle identification.')])
p('The LZ high-energy analysis is especially interesting because it changed the search window. Its 2.84 tonne-year exposure contains one event consistent with a 248 ± 23 (statistical) ± 23 (systematic) keV nuclear recoil. The maximum local significance is 3.4σ; accounting for the tested alternatives reduces it to 2.6σ globally. That statistic quantifies tension with a specified background model. It is not the probability that dark matter caused the event. The result remains a preprint in the source inspected here. '+cite(6))
p('A different LZ analysis finds solar-neutrino scattering, an expected physical signal that increasingly overlaps low-energy dark-matter searches. It demonstrates sensitivity while making the background problem more demanding; it is not a dark-matter detection or an absolute barrier to progress. '+cite(7)+' Independently, XENONnT finds no significant excess in 3.1 tonne-years and reports a 90% confidence upper limit of 1.7 × 10⁻⁴⁷ cm² at a 30 GeV/c² WIMP mass for its specified spin-independent elastic model. That limit cannot be averaged with the LZ high-energy anomaly as though they measured one common effect. '+cite(8))
h('3. Three mechanisms worth following','mechanisms')
p('<strong>Particles with more than one accessible state.</strong> A dark sector can contain a ground state and an excited state. Scattering that absorbs or releases an internal energy splitting changes the recoil spectrum, so the lowest-energy window need not be the most informative one. Fan and colleagues explore endothermic and exothermic interpretations of the LZ high-energy event and the constraints from other searches. Their ability to construct such a model is interesting; it does not establish that the event came from it. '+cite(18))
eq('Elastic scattering: χ + N → χ + N\nInelastic scattering: χ₁ + N → χ₂ + N, with δ = m₂ − m₁')
p('Production history is a separate axis. In thermal freeze-out, initially equilibrated particles stop annihilating efficiently as the Universe expands. In freeze-in, the coupling is so weak that the dark component never equilibrates and is gradually populated by rare processes. Hall and colleagues provide a primary construction of the latter. Neither mechanism determines a unique present-day detection rate without additional assumptions. '+cite(16))
p('<strong>Self-interactions that change halos over time.</strong> Elastic collisions redistribute energy inside a dark halo. Early inward heat flow can produce a low-density core; later outward heat transport can drive gravothermal collapse into a dense central structure. This makes the slogan “self-interactions produce cores” incomplete. Simulations show that orbital evolution, tides and stellar response can broaden the resulting population. '+cite(14)+' Recent lensing-oriented simulations explicitly connect projected density and enclosed mass to expansion and collapse phases. '+cite(10))
p('A late-October preprint analyzes 29 quadruply imaged quasars and reports a preference for core-collapsed halos within a particular self-interacting model. Only its official abstract was available to this review; its detailed likelihood and systematics have not been independently audited here. It is retained as a provisional pointer, not as a quantitative input to our computation. '+cite(11)+' Numerical approximations also matter: kinetic calculations find departures from local thermal equilibrium that can alter late-collapse behavior. '+cite(15))
p('<strong>Fields whose wavelength becomes astrophysical.</strong> A coherent bosonic field can act as matter after it begins oscillating in its potential; misalignment is an early-Universe production mechanism. '+cite(20)+' For sufficiently small mass, wave effects modify clustering on observable scales. In the 2026 DESI-plus-CMB analysis, an ultralight component around 10⁻²⁹ eV is constrained to roughly 0.3% of total matter density. A mild DESI-only preference near 10⁻²⁶ eV vanishes with CMB data. This does not exclude QCD axions: the tested ultralight range is enormously different from the microelectronvolt masses probed by resonant haloscopes such as ADMX. '+cite(9)+' '+cite(17))
h('4. An original test: how much does a halo fit really tell us?','methods')
p('We downloaded the public SPARC rotation-curve archive and metadata catalog, retained their creator attribution, and ran the accompanying Python pipeline. This is a fresh analysis of published observations, not newly collected data. Its question and sample differ from the earlier 149-galaxy multivariable SPARC pilot on this website; it is not a replication of that study. The raw archive contains 175 galaxies. We include quality flags 1 or 2, inclination at least 30°, and at least 12 rows with finite values and positive radius, observed speed and quoted error. The resulting sample has 100 galaxies and 2,742 radial measurements. Selection is documented for every parent-sample galaxy. '+cite(3))
p('The two halo families are a cusped NFW profile and an empirical Burkert core. Both have two fitted parameters: density scale ρ₀ and radius scale rₛ. A Burkert fit is not a simulation of self-interacting dark matter, and an unmodified NFW fit is not a complete prediction of a collisionless galaxy including baryonic feedback. '+cite(4)+' '+cite(5))
eq('ρNFW(r) = ρ₀ / [x(1 + x)²]\nρBurkert(r) = ρ₀ / [(1 + x)(1 + x²)]\nx = r / rₛ;  v²halo(r) = GMhalo(<r) / r')
p('The total circular-speed model combines the SPARC gas, unit-mass-to-light disc and bulge contributions with the halo. Negative gas velocities in the archive encode outward radial force and are kept as signed squared contributions. The baseline stellar mass-to-light ratios at 3.6 μm are 0.5 for the disc and 0.7 for the bulge. Sensitivity runs use disc values 0.3 and 0.7, with the bulge fixed to 1.4 times the disc value. Distances and inclinations remain fixed to their catalog values.')
eq('v²model = vgas |vgas| + Υdisc v²disc + Υbulge v²bulge + v²halo\nχ² = Σi [(vmodel,i − vobs,i) / σeff,i]²\nσeff,i = √(σ²quoted,i + (5 km s⁻¹)²)')
p('The 5 km/s error term is an analyst-chosen sensitivity floor, not a measured intrinsic dispersion. A separate baseline run removes it. We fit log₁₀ρ₀ between 3 and 11 (ρ in M☉ kpc⁻³) and log₁₀rₛ between −1.5 and 2.5 (r in kpc), with four starting positions and bounded least squares. The best of the four is retained. Fits within 0.015 dex of a bound are flagged. Analytic masses are checked against direct numerical integration; noiseless curves recover their generating parameters. No cosmological mass–concentration prior is imposed.')
p('We report Δχ² = χ²NFW − χ²Burkert. Positive values favor the cored profile under these assumptions. Because the two models have equal fitted parameter counts, their AIC difference equals this χ² difference if one adopts our independent Gaussian error model. We do not treat it as a calibrated p-value, posterior odds or a test of particle theories. The radial points share systematic uncertainties; pooling their χ² values into one discovery statistic would be misleading.')
h('5. Results from the observed curves','results')
fig('observed-curves','Figure 1. Four named illustrative galaxies, selected to show varied rotation-curve shapes, not to estimate sample frequencies. White points are published SPARC velocities; bars include the chosen 5 km/s floor. Lines are fits from this analysis with fixed baseline stellar mass-to-light ratios. The full numerical sample is in profile_fits.csv.')
p(f'At the baseline settings, Burkert has lower χ² for {S["burkert_lower_chi2"]}/100 galaxies and NFW for {S["nfw_lower_chi2"]}/100; {S["within_2"]}/100 lie within |Δχ²| &lt; 2. The median Δχ² is {S["median_delta"]:.2f}. A lower χ² means only that one of these two conditional profiles fits better. It does not mean that the fit is acceptable in an absolute sense, that all galaxies share the same mechanism, or that halo particles self-interact.')
table(['Disc M/L','Burkert lower χ²','NFW lower χ²','|Δχ²| < 2'],[(str(x['ml']),str(x['burkert_lower_chi2']),str(x['nfw_lower_chi2']),str(x['within_2'])) for x in S['ml_sensitivity']])
fig('profile-comparison','Figure 2. Left: all 100 galaxies ranked by Δχ². Right: the same galaxies at two fixed stellar mass-to-light ratios; points crossing quadrants change preference sign. Symmetric-log axes retain near-zero differences while displaying the broad tails. These are descriptive diagnostics, not independent probability draws.')
p(f'{S["preference_sign_changes_ml_03_to_07"]} of 100 galaxies reverse the sign of Δχ² between disc M/L = 0.3 and 0.7. In {S["baseline_bound_any"]} baseline cases, at least one profile reaches the declared boundary proximity; their detailed halo parameters deserve particular caution. The optimizer reports {S["optimizer_failures"]} unsuccessful fits across the recorded observed-data configurations. Solver convergence alone does not validate the physical model. Every per-galaxy score, selection flag and fitted baseline parameter is supplied with the paper.')
import csv
fit_rows=list(csv.DictReader((OUT/'profile_fits.csv').open()))
no_floor=[r for r in fit_rows if float(r['disc_ml'])==.5 and float(r['error_floor_kms'])==0]
with_floor={r['galaxy']:float(r['delta_chi2_nfw_minus_burkert']) for r in fit_rows if float(r['disc_ml'])==.5 and float(r['error_floor_kms'])==5}
no_floor_b=sum(float(r['delta_chi2_nfw_minus_burkert'])>0 for r in no_floor)
floor_flips=sum((float(r['delta_chi2_nfw_minus_burkert'])>0)!=(with_floor[r['galaxy']]>0) for r in no_floor)
p(f'Removing the 5 km/s floor while keeping baseline M/L changes the count to {no_floor_b}/100 favoring Burkert and {100-no_floor_b}/100 favoring NFW; {floor_flips} galaxies reverse preference sign relative to the baseline floor. This makes the adopted error model a material assumption rather than a cosmetic plotting choice. Quoted errors alone give high leverage to very precise points, even when unmodeled systematics are shared across radii.')
p('There are two reasons a core cannot identify a particle. First, feedback from ordinary matter can transfer energy to collisionless dark matter and flatten an initially cusped distribution. '+cite(13)+' Second, self-interactions can eventually steepen a halo through collapse. The same observed central structure can therefore arise from different histories, and the same interaction law can produce different structures. Controlled feedback experiments further suggest that collapse resilience depends on initial concentration and the imposed feedback history. '+cite(19))
h('6. Synthetic recovery: the experiment where we know the answer','recovery')
p('We generated two analytic galaxy curves, one NFW and one Burkert, with the halo circular speeds matched at 30 kpc. The Burkert input is ρ₀ = 2 × 10⁷ M☉ kpc⁻³ and rₛ = 3 kpc; the NFW scale radius is 5 kpc and its density is normalized to the matched outer speed. Each uses the same fixed illustrative baryonic term, v²bar = 3200 (r/2)/(1 + r/2)², with r in kpc and v² in (km/s)². Forty radii span 0.3–30 kpc logarithmically. Independent Gaussian noise of 5 km/s is added with seed 20261113.')
p('For each generating profile, 100 noise realizations are fitted with both profile families. Each realization is analyzed at three inner-radius cuts: 0.3, 3 and 8 kpc, keeping the same outer measurements and paired noise. Thus this test removes <strong>both inner coverage and data points</strong>; it does not isolate the effect of spatial resolution at fixed sample size. There are 600 paired profile comparisons. The displayed intervals are 95% Wilson binomial intervals for the recovery fraction under this exact synthetic design; they are not astrophysical confidence intervals.')
fig('synthetic-recovery','Figure 3. Left: the two generating curves used in the controlled experiment. Right: the fraction of 100 realizations selecting the generating profile by lower χ², at each radial cut; intervals are Wilson 95%. Data are fully synthetic and the baryonic component is known exactly. The experiment is intentionally easier than inferring a real galaxy’s history.')
table(['Generating profile','Inner radius','Correct selection','95% interval'],[(x['truth'],f'{x["minimum_radius_kpc"]:g} kpc',f'{x["correct"]}/{x["trials"]}',f'{x["wilson_low"]:.2f}–{x["wilson_high"]:.2f}') for x in S['synthetic_recovery']])
p('The useful lesson is the conditional nature of identification. Even when the two possible answers and the baryons are supplied in advance, removing informative radii can weaken discrimination. Real data add uncertain geometry, correlated errors, non-circular motion and more than two possible density families. Conversely, a clean recovery result in this controlled setting is a check on the inference procedure, not evidence that the Universe chose that model. These simulations evolve no particles and implement no heat transport or cosmological growth.')
trial_rows=list(csv.DictReader((OUT/'synthetic_trials.csv').open()))
if 'optimizer_success' in trial_rows[0]:
    p(f'Synthetic-fit diagnostics: {sum(r["optimizer_success"]!="True" for r in trial_rows)} of 600 comparisons contain an unsuccessful optimizer status; {sum(r["any_bound"]=="True" for r in trial_rows)} contain at least one fitted profile near a parameter bound. Boundary effects are part of this declared fitting procedure and further limit extrapolation beyond this benchmark.')
h('7. A better next experiment','next')
p('The most promising connection is between mechanisms and observations that respond to different pieces of the model. Rotation curves measure the radial force in gas-rich galaxies. Strong lensing measures projected gravitational structure, including objects with few visible stars. Recoil experiments probe nongravitational interactions directly. Cosmic structure tests the influence of mass and production history over a much larger volume. Agreement across these channels would carry more weight than another excellent fit to one curve.')
p('Euclid’s November 12 DR1-Foundation release, covering about 1,900 square degrees, reports around 15,000 strong-lensing candidates. The immediate opportunity is a well-characterized population with explicit detection and confirmation probabilities. Its novelty is scale and consistency; its release does not settle the nature of dark matter. '+cite(12))
table(['Next test','Primary change','Failure mode to expose'],[
('Galaxy model comparison','Marginalize distance, inclination and stellar M/L; include covariance and concentration priors.','A preference that disappears under realistic nuisance uncertainty.'),
('Lensing population','Forward-model detection, line-of-sight structure and baryonic perturbers.','Dense inferred clumps caused by selection or a restrictive smooth lens model.'),
('SIDM evolution','Simulate tides, assembly and baryons with convergence checks.','Apparent collapse driven by numerics or one imposed assembly history.'),
('Direct detection follow-up','Independent exposure and targets; jointly fit spectral and timing information.','A candidate explained by a previously underrepresented background topology.')])
h('8. Limits, provenance and reproducibility','limits')
p('This is a targeted evidence synthesis, not a systematic review or pooled statistical meta-analysis. Searches emphasized primary experimental papers, collaboration releases and peer-reviewed mechanism studies, with preprints labeled separately. Search terms covered LZ high-energy recoil results, solar-neutrino backgrounds, DESI ultralight axions, SIDM strong lensing, gravothermal collapse and Euclid releases. Sources were checked through November 13, 2026; coverage is selective, and absence from this review is not evidence against a candidate. Abstract-only evidence is identified in the references. Incompatible cross sections, matter fractions and lensing likelihoods were deliberately not combined into a single ranking.')
p('The computation is exploratory and was not preregistered. The profile sample is not volume complete. Fixed stellar mass-to-light values and a chosen error floor are sensitivity settings, not inferred truths. Bounds can shape profile fits. We do not propagate distance or inclination uncertainties, model beam smearing, fit asymmetric drift, include covariance, or impose galaxy-formation priors. The four displayed galaxies are illustrative. The synthetic curves have exactly known baryons and independent noise. No result here identifies dark matter or reanalyzes LZ, DESI or Euclid raw observations.')
p('The source package includes the exact SPARC input files, SHA-256 checksums, all 175 selection outcomes, 400 observed-data configuration rows, 600 synthetic comparison rows, fitted parameters, software versions, numerical checks, plotting code and this paper’s build script. Input observations remain the work of their original creators. SPARC’s metadata catalog lists the underlying rotation-curve publications. The manuscript, code and synthesis were prepared with AI assistance for Brandon Frank Han-Chween Huang’s open notebook; no claim is made that he personally collected these observations or that this draft has undergone peer review.')
h('9. Conclusion','conclusion')
p('The compelling possibility is a dark sector with behavior richer than a passive invisible mass: internal particle states can alter recoil energies, self-interactions can change a halo’s evolutionary path, and very light fields can reshape cosmic structure. These are testable mechanisms, not discoveries. Our SPARC reanalysis demonstrates why a preference for a halo shape cannot close the identification problem. The next convincing step would be a mechanism that makes quantitative predictions across several probes, survives their nuisance uncertainties, and succeeds on new data.')

class Plain(HTMLParser):
    def __init__(self):super().__init__();self.text=[]
    def handle_data(self,x):self.text.append(x)
def plain(s):q=Plain();q.feed(s);return ''.join(q.text)

title='Dark Matter, by Its Consequences'
subtitle='Mechanisms, new constraints, and what galaxy curves can tell us'
byline='Prepared for Brandon Frank Han-Chween Huang · AI-assisted working paper · November 13, 2026'
body=[];md=[f'# {title}\n\n{subtitle}\n\n{byline}\n\nNot peer-reviewed. Evidence synthesis + original exploratory reanalysis.\n']
for b in blocks:
    if b[0]=='heading':body.append(f'<h2 id="{b[2]}">{b[1]}</h2>');md.append('\n## '+b[1]+'\n')
    elif b[0]=='paragraph':body.append('<p>'+b[1]+'</p>');md.append(plain(b[1])+'\n')
    elif b[0]=='equation':body.append('<pre class="equation">'+html.escape(b[1])+'</pre>');md.append('```text\n'+b[1]+'\n```\n')
    elif b[0]=='figure':
        body.append(f'<figure><a href="{b[1]}.svg" target="_blank" rel="noopener"><img src="{b[1]}.svg" alt="{html.escape(b[2])}" loading="lazy"></a><figcaption>{b[2]}</figcaption></figure>');md.append(f'![{b[2]}]({b[1]}.svg)\n')
    elif b[0]=='table':
        body.append('<div class="table-scroll" tabindex="0"><table><thead><tr>'+''.join('<th>'+x+'</th>' for x in b[1])+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+x+'</td>' for x in row)+'</tr>' for row in b[2])+'</tbody></table></div>');md.append('| '+' | '.join(b[1])+' |\n| '+' | '.join('---' for _ in b[1])+' |\n'+'\n'.join('| '+' | '.join(plain(x) for x in row)+' |' for row in b[2])+'\n')
body.append('<h2 id="references">References</h2><ol class="references">');md.append('\n## References\n')
for i,(name,url,note) in enumerate(refs,1):body.append(f'<li id="ref-{i}"><a href="{url}" target="_blank" rel="noopener">{name}</a><small>{note}</small></li>');md.append(f'{i}. [{name}]({url}) {note}\n')
body.append('</ol>')
toc=''.join(f'<a href="#{b[2]}">{b[1]}</a>' for b in blocks if b[0]=='heading')+'<a href="#references">References</a>'
interactive='''<section class="curve-lab" aria-labelledby="curve-title"><div class="lab-top"><div><span class="eyebrow">LOOK AT THE ACTUAL FITS</span><h3 id="curve-title">One galaxy. Two explanations of its shape.</h3></div><label>Galaxy <select id="galaxy"><option>NGC2403</option><option>DDO154</option><option>NGC3198</option><option>IC2574</option></select></label></div><div class="toggles"><label><input id="show-nfw" type="checkbox" checked> NFW fit</label><label><input id="show-burkert" type="checkbox" checked> Burkert fit</label><label><input id="show-baryons" type="checkbox" checked> Baryonic contribution</label></div><canvas id="curve-canvas" role="img" aria-label="Observed SPARC rotation curve and fitted halo models" tabindex="0"></canvas><p id="curve-status" aria-live="polite">Loading the published data and computed fits…</p><p class="small">These controls reveal precomputed fits; they do not refit or change the data. All values are available in the downloadable JSON. Error bars include the declared 5 km/s floor.</p><noscript><p>The same curves are shown in Figure 1 below.</p></noscript></section>'''
body_html='\n'.join(body).replace('<h2 id="results">',interactive+'<h2 id="results">')
page=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#101914"><title>{title} — Brandon Frank Han-Chween Huang</title><meta name="description" content="A current evidence synthesis, reproducible analysis of 100 SPARC galaxies and 600 synthetic profile comparisons. Dark matter mechanisms, with explicit limits."><link rel="stylesheet" href="paper.css"><script src="paper.js" defer></script></head><body><a class="skip" href="#abstract">Skip to paper</a><header class="top"><a class="brand" href="https://brandonfhuang.com/projects/">B. <span>PROJECTS</span></a><a href="https://brandonfhuang.com/projects/#papers">All papers ↗</a></header><main><section class="hero"><p class="eyebrow">RESEARCH NOTE 03 / NOVEMBER 13, 2026</p><h1>Dark Matter,<br><em>by Its Consequences.</em></h1><p class="dek">{subtitle}.</p><p class="byline">Prepared for Brandon Frank Han-Chween Huang<br>AI-assisted synthesis and computation · Working paper, not peer-reviewed</p><div class="hero-bottom"><div class="stats"><span><strong>100</strong>GALAXIES REANALYZED</span><span><strong>600</strong>SYNTHETIC COMPARISONS</span><span><strong>20</strong>PRIMARY REFERENCES</span></div><div class="downloads"><a href="dark-matter-2026.pdf" download>Download PDF ↓</a><a href="../README.md">Code + data ↓</a><a href="manuscript.md" download>Manuscript ↓</a></div></div></section><div class="paper-layout"><aside><p class="eyebrow">IN THIS PAPER</p><nav aria-label="Paper contents">{toc}</nav><a class="small" href="summary.json">Machine-readable results ↗</a></aside><article>{body_html}</article></div><footer><p>There’s so much more to explore.</p><a href="https://brandonfhuang.com/projects/">Back to projects ↗</a></footer></main></body></html>'''
(WEB/'index.html').write_text(page);(WEB/'manuscript.md').write_text('\n'.join(md));(BASE/'manuscript.md').write_text(re.sub(r'\]\(([^/]+\.svg)\)',r'](results/\1)','\n'.join(md)))
for pth in OUT.iterdir():
    if pth.is_file():shutil.copy2(pth,WEB/pth.name)
(BASE/'requirements.txt').write_text('numpy==2.3.5\nscipy==1.17.0\nmatplotlib==3.10.8\nreportlab==4.4.9\n')
(BASE/'REPRODUCING.md').write_text('''# Dark Matter, by Its Consequences

AI-assisted working paper prepared for Brandon Frank Han-Chween Huang, November 13, 2026. Not peer-reviewed.

## Reproduce numerical results

Use Python 3.11+ and the versions in requirements.txt (Python 3.11.8 was used here). Install into your own environment, then run `python3 analyze.py`. No network is required: the exact public SPARC source files are included with SHA-256 checksums in results/summary.json. The run performs analytic-integral and noiseless-recovery checks before fitting. Runtime is a few minutes on a typical CPU.

## Outputs

- results/profile_fits.csv: 100 selected galaxies × 4 configurations (disc M/L 0.3, 0.5, 0.7 with 5 km/s floor; M/L 0.5 with zero floor).
- results/sample_selection.csv: selection decision for all 175 parent galaxies.
- results/synthetic_trials.csv: 100 realizations × 2 generating profiles × 3 radius cuts.
- results/fits.json: baseline halo parameters, χ², optimizer and boundary flags.
- results/summary.json: analysis summary, software versions, seed and input hashes.
- results/curves.json: the four illustrative galaxies and their baseline fits.
- SVG/PNG figures: generated directly from these computations.

The web edition contains an interactive viewer of precomputed fits. It does not refit in the browser. Serve `web/` with `python3 -m http.server 8000 --directory web` to read it locally; the notebook navigation links lead to the original hosted site in the standalone edition. The computation and figures work independently of the site. The build_paper.py script regenerates the manuscript and PDF within the website repository; for a standalone copy it writes a local web/ directory.

## Scope

This is an exploratory profile-fit diagnostic, not a particle-physics likelihood, an N-body simulation, a preregistered analysis, a systematic review or a statistical pooling of heterogeneous experiments. Fixed geometry/M/L, independent Gaussian errors and broad halo bounds limit interpretation. The synthetic cutoff removes both inner coverage and points. It does not model an equal-sample-size observing program. Neither cored fits nor fit preference establish self-interactions. This study does not replicate the earlier 149-galaxy multivariate pilot.

## Provenance and rights

Public SPARC data by Lelli, McGaugh & Schombert (2016), AJ 152, 157, https://arxiv.org/abs/1606.09251 . Primary archive https://astroweb.cwru.edu/SPARC/Rotmod_LTG.zip and metadata https://astroweb.cwru.edu/SPARC/SPARC_Lelli2016c.mrt retrieved November 13, 2026 US Eastern. An identical rotation archive was checked against https://zenodo.org/records/16284118/files/Rotmod_LTG.zip . The metadata includes references to original HI/H-alpha observations. The input creators retain their rights; no new license is asserted for their data. All figures in this package are newly generated from the included analysis. No copyrighted paper figures are copied.

Literature search log: targeted searches for LZ 2026 high-energy recoil, LZ solar neutrinos, DESI ultralight axions, SIDM gravothermal collapse and strong lenses, and Euclid DR1-Foundation. Evidence cutoff November 13, 2026. The bibliography records publication status and abstract-only limitations. No cross-experiment significance is pooled. Main numerical analysis is independent of the review sources.
''')

def build_pdf():
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, KeepTogether
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.enums import TA_LEFT
    from matplotlib import get_data_path
    fonts = Path(get_data_path()) / "fonts" / "ttf"
    for name,file in [('D','DejaVuSans.ttf'),('DB','DejaVuSans-Bold.ttf'),('DI','DejaVuSans-Oblique.ttf')]:
        pdfmetrics.registerFont(TTFont(name, str(fonts / file)))
    pdfmetrics.registerFontFamily('D',normal='D',bold='DB',italic='DI',boldItalic='DB')
    styles=getSampleStyleSheet();styles.add(ParagraphStyle('BodyX',fontName='D',fontSize=9,leading=14,spaceAfter=9,textColor=colors.HexColor('#25362b')));styles.add(ParagraphStyle('HeadX',fontName='DB',fontSize=15,leading=19,spaceBefore=17,spaceAfter=10,keepWithNext=True,textColor=colors.HexColor('#18372b')));styles.add(ParagraphStyle('SmallX',fontName='D',fontSize=7.5,leading=11,spaceAfter=8,textColor=colors.HexColor('#526258')));styles.add(ParagraphStyle('TitleX',fontName='DB',fontSize=30,leading=34,spaceAfter=15,textColor=colors.HexColor('#18372b')))
    def clean(s):return re.sub(r'<a href="[^"]+">(.*?)</a>',r'\1',s).replace('<strong>','<b>').replace('</strong>','</b>').replace('−','-').replace('–','-').replace('—','-')
    story=[Paragraph(title,styles['TitleX']),Paragraph(subtitle,styles['HeadX']),Paragraph(byline.replace('·',' / '),styles['SmallX']),Paragraph('Evidence synthesis + original exploratory reanalysis. Not peer-reviewed.',styles['SmallX']),Spacer(1,8)]
    for b in blocks:
        if b[0]=='heading':story.append(Paragraph(clean(b[1]),styles['HeadX']))
        elif b[0]=='paragraph':story.append(Paragraph(clean(b[1]),styles['BodyX']))
        elif b[0]=='equation':story.append(Paragraph(clean(html.escape(b[1])).replace('\n','<br/>'),styles['SmallX']))
        elif b[0]=='figure':
            from PIL import Image as PILImage
            im=PILImage.open(OUT/f'{b[1]}.png');w,h=im.size;story.append(KeepTogether([Image(str(OUT/f'{b[1]}.png'),width=483,height=483*h/w),Spacer(1,6),Paragraph(clean(b[2]),styles['SmallX'])]))
        elif b[0]=='table':
            data=[[Paragraph(clean(x),styles['SmallX']) for x in b[1]]]+[[Paragraph(clean(x),styles['SmallX']) for x in row] for row in b[2]];n=len(b[1]);t=Table(data,colWidths=[483/n]*n,repeatRows=1,hAlign='LEFT');t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e6ede4')),('LINEBELOW',(0,0),(-1,0),.5,colors.HexColor('#74927b')),('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),('LINEBELOW',(0,1),(-1,-1),.3,colors.HexColor('#ccd6cc'))]));story.extend([t,Spacer(1,12)])
    story.append(Paragraph('References',styles['HeadX']))
    for i,(name,url,note) in enumerate(refs,1):story.append(Paragraph(clean(f'{i}. {name}<br/>{note}<br/><link href="{html.escape(url)}" color="#39735b">{html.escape(url)}</link>'),styles['SmallX']))
    def footer(c,d):
        c.setFont('D',7);c.setFillColor(colors.HexColor('#526258'));c.drawString(56,32,'DARK MATTER, BY ITS CONSEQUENCES / WORKING PAPER');c.drawRightString(539,32,str(d.page))
    doc=SimpleDocTemplate(str(WEB/'dark-matter-2026.pdf'),pagesize=(595,842),leftMargin=56,rightMargin=56,topMargin=48,bottomMargin=49,title=title,author='Prepared for Brandon Frank Han-Chween Huang; AI-assisted research synthesis')
    doc.build(story,onFirstPage=footer,onLaterPages=footer)

build_pdf()
(BASE/'REPRODUCING.md').write_text((BASE/'REPRODUCING.md').read_text().replace('Python 3.11.8',f'Python {S["versions"]["python"]}'))
