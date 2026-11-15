# Beyond rotation curves.

A proposed next test of acceleration, gas physics, and astrophysical scale.

Brandon Frank Han-Chween Huang
Draft: 13 November 2026
AI-assisted writing from recorded research notes.

A new proposal developed from the pilot’s stated next steps. It reports no new empirical results and is not peer-reviewed.



## Abstract

The SPARC multivariable pilot found no recorded improvement from adding its tested galaxy descriptors to a baryonic-acceleration baseline. It did not measure gas temperature or test cluster-scale behavior. [[1]](#ref-note) This companion paper proposes a next-stage design: evaluate additional physical information within clearly separated astrophysical populations, hold out whole objects, and compare paired prediction errors with uncertainty estimates. The aim is to define a useful test, not to declare an explanation in advance. No new data have been collected or analyzed for this proposal.


A prediction that works within rotating galaxies is a starting point. The next question is where it transfers, where it fails, and which measurements explain the difference.




## 1. From a pilot result to a testable question

The initial question was whether a limited set of galaxy descriptors adds predictive information once baryonic acceleration is known. The recorded negative result narrows that particular search; it does not make other variables irrelevant. The source note identifies lensing-derived acceleration, gas temperature, pressure, entropy, and dynamical state as possible ingredients for cluster studies, with dwarf and globular-cluster samples as additional settings. [[1]](#ref-note)

A next study should ask whether these quantities improve prediction within an explicitly defined population, then assess transfer between populations. This separates three tasks: predicting a measured target, checking a physical model, and deciding whether an explanation generalizes. They require different evidence.




## 2. Keep the astrophysical settings separate

A rotating disk, a pressure-supported dwarf, a globular cluster, and a merging galaxy cluster do not offer interchangeable measurements. The SPARC dataset was assembled around disk-galaxy photometry and rotation curves. [[2]](#ref-sparc) A direct extension must specify which observable plays the role of the target in each new population and which assumptions are needed to construct it.


Proposed measurement plan; no new results| Population | Candidate measurements | Key control |
| --- | --- | --- |
| Galaxy clusters | Lensing mass, baryonic mass, gas temperature, pressure, entropy, dynamical state | Projection, mass reconstruction, correlated uncertainties |
| Dwarf galaxies | Stellar kinematics and baryonic structure | Equilibrium assumptions, orbital anisotropy, tides |
| Globular clusters | Stellar kinematics and mass profiles | Stellar remnants, binaries, tides, equilibrium assumptions |

These are proposed design considerations, not a claim that every quantity is available in a chosen catalogue. A catalogue audit must come before model fitting.




## 3. Define the target without hiding assumptions

For rotating galaxies, V²/R provides the familiar centripetal-acceleration target. Lensing instead constrains projected mass through its effect on background light. Converting a lensing reconstruction into a radial acceleration estimate requires geometric and mass-model assumptions; it is not a direct substitution of a measured circular velocity.

A lensing-based target would nevertheless provide a useful comparison to one inferred from gas equilibrium. Gas temperature should not be used casually as a predictor of a target that was itself constructed using the same temperature measurements. That would risk circularity. The study should document every shared input and covariance before claiming extra predictive power.




## 4. Proposed validation protocol


- Freeze the scientific question. State the target, baseline, feature groups, exclusion rules, and primary error metric before looking at final test performance.

- Split by physical object. Keep every radial measurement of an object in the same fold. Where catalogues or measurement pipelines differ, reserve additional catalogue-level checks.

- Separate selection from evaluation. Fit transformations and choose hyperparameters inside training data only. Use nested validation when tuning models.

- Compare paired errors. Evaluate baseline and extended models on the same held-out objects. Bootstrap whole objects to estimate uncertainty in the difference; do not treat every radius as independent.

- Test robustness. Repeat under plausible mass-to-light ratios, distance and inclination uncertainties where applicable, quality cuts, and dynamical-state selections. Report failures as well as improvements.

- Test transfer explicitly. Report within-population results separately from results obtained by training on one population and evaluating on another.



## 5. What would an informative outcome look like?

A stable improvement on untouched objects would indicate that the added measurements contain predictive information beyond the chosen baseline. It would not, by itself, establish why that information matters. A lack of improvement would constrain the selected measurements and procedure, rather than prove the absence of additional physics.

Physical interpretation requires comparing explicit competing models against multiple observables. The radial acceleration relation motivates a strong galaxy-scale baseline. [[3]](#ref-rar) Merging-cluster lensing provides a distinct test: Clowe and colleagues found that the inferred mass distribution was displaced from the dominant hot-gas component and approximately followed the galaxies. [[4]](#ref-clowe) A successful account has to confront such observations as well as rotation curves.




## 6. Deliverables before any conclusion

The minimum useful package would contain a versioned data dictionary, provenance for each catalogue, a table of cuts, the target-construction code, fixed holdout assignments, per-object predictions, and uncertainty-aware comparisons. The first milestone is therefore a reproducible dataset and protocol. A claim about dark matter or modified gravity comes later, only if the evidence supports it.




## Provenance and references

This AI-assisted working proposal develops the next-study directions recorded in the SPARC pilot note. The validation protocol and cautions are proposed methodological elaborations. No cluster, dwarf, or globular-cluster analysis is reported as completed here. This manuscript is not peer-reviewed.

Huang research notebook. [SPARC multivariable gravity pilot](https://brandon-huang-studio.brainyalbatross8.chatgpt.site/curiosities/papers/pilot-source.md). Saved source note; unpublished. Results quoted from the note, not recomputed for this writeup.
Lelli, F., McGaugh, S. S., & Schombert, J. M. (2016). [SPARC: Mass Models for 175 Disk Galaxies with Spitzer Photometry and Accurate Rotation Curves](https://ui.adsabs.harvard.edu/abs/2016AJ....152..157L/abstract). The Astronomical Journal, 152, 157. DOI: 10.3847/0004-6256/152/6/157. [Data archive](https://astroweb.cwru.edu/SPARC/).
McGaugh, S. S., Lelli, F., & Schombert, J. M. (2016). [Radial Acceleration Relation in Rotationally Supported Galaxies](https://arxiv.org/abs/1609.05917). Physical Review Letters, 117, 201101. DOI: 10.1103/PhysRevLett.117.201101.
Clowe, D., et al. (2006). [A Direct Empirical Proof of the Existence of Dark Matter](https://arxiv.org/abs/astro-ph/0608407). The Astrophysical Journal Letters, 648, L109–L113. DOI: 10.1086/508162.
