# What predicts a galaxy’s acceleration?

A multivariable SPARC pilot: testing the information beyond baryonic acceleration.

Brandon Frank Han-Chween Huang
Draft: 13 November 2026
AI-assisted writing from recorded research notes.

The empirical results are reproduced from the saved pilot note. The analysis has not been independently rerun; this writeup is not peer-reviewed.



## Abstract

This working paper documents a pilot asking whether additional galaxy properties improve prediction of observed acceleration beyond baryonic acceleration alone. The saved analysis reports 2,700 radial measurements from 149 galaxies, with entire galaxies held out during ten-fold cross-validation. A baseline using only baryonic acceleration achieved a reported root-mean-square error of 0.1381 dex. Every tested feature extension produced a larger reported error. This is a narrow predictive result for one selected sample and modeling procedure. It neither establishes modified gravity nor rules out dark matter. The present paper expands the recorded methods and interpretation without adding new measurements or rerunning the analysis. [[1]](#ref-note)


The useful finding is a boundary: the tested extra variables did not improve prediction on unseen galaxies in this pilot.




## 1. The question

What information about a galaxy is needed to predict its radial acceleration? The radial acceleration relation connects the acceleration inferred from rotation curves with that expected from the observed baryonic distribution. McGaugh and colleagues reported this relationship across a sample of rotating galaxies. [[3]](#ref-rar) The pilot asks a conditional question: after supplying baryonic acceleration, do radius, surface-brightness measures, gas proxies, compactness, morphology, or potential proxies help predict what remains?

This framing matters. It tests the incremental predictive value of a specified set of measurements. It does not compare complete cosmological theories, identify a dark-matter particle, or establish a fundamental law.




## 2. Data and selection

The source note identifies the official SPARC mass-model and galaxy tables as its inputs. SPARC provides photometry and rotation curves for 175 disk galaxies; the pilot’s selected set is smaller. [[2]](#ref-sparc) The recorded quality cuts are Q < 3, inclination at least 30 degrees, positive radius and velocity, and fractional velocity uncertainty no greater than 10%. After these cuts, the note reports 149 galaxies and 2,700 radial measurements. [[1]](#ref-note)

The analysis target is log₁₀(gobs), with observed centripetal acceleration defined by:

gobs = Vobs² / R

The baseline input is log₁₀(gbar). Baryonic acceleration was constructed from the SPARC velocity components with fixed stellar mass-to-light ratios of 0.5 for the disk and 0.7 for the bulge, as recorded in the pilot. These are assumptions of this analysis; they were not independently estimated in this writeup.




## 3. Predictors and validation

The candidate set includes physical radius, radius divided by effective radius, local and effective stellar surface brightness, luminosity, an H I-to-stellar-mass proxy, compactness, the density proxy gbar/R, the local baryonic-potential proxy Vbar², and Hubble type. These are candidate descriptors, not direct measurements of temperature or a complete three-dimensional gravitational potential.

The source specifies regularized histogram gradient boosting, identical hyperparameters across feature sets, and ten-fold GroupKFold validation with galaxy identity defining the groups. [[1]](#ref-note) Holding out whole galaxies avoids testing on another radial point from a galaxy already represented in training. It is a more relevant check of cross-galaxy prediction than a random split of radial measurements.

The saved note does not include the numerical hyperparameters, fold assignments, code, per-fold errors, or the full preprocessing procedure. Consequently, this document can report the recorded experiment but cannot serve as a complete reproduction package.




## 4. Recorded results

Lower values are better for both metrics. A dex is a base-10 logarithmic unit. The following values are transcribed from the source note. [[1]](#ref-note)


Held-out-galaxy prediction errors reported in the pilot| Inputs | RMSE (dex) | MAE (dex) |
| --- | --- | --- |
| Baryonic acceleration only | 0.1381 | 0.1040 |
| + Radius | 0.1403 | 0.1064 |
| + All tested variables | 0.1424 | 0.1101 |
| + Potential proxies | 0.1514 | 0.1171 |
| + Density / compactness | 0.1532 | 0.1210 |

The all-variables model has an RMSE 0.0043 dex above the baseline. No uncertainty interval is provided for that difference, so its statistical significance cannot be assessed here. The note also reports unsuccessful one-variable residual-correction tests, but supplies no separate numerical results for them.




## 5. What follows—and what does not

The tested feature additions offered no demonstrated improvement under the recorded procedure. Several explanations remain possible: genuinely limited extra signal, redundant predictors, noisy proxies, limited sample diversity, or a model and regularization choice that does not recover a subtle relationship. The experiment does not distinguish these explanations.

The result should not be generalized to all galaxy properties, all algorithms, or all astrophysical scales. In particular, temperature and cluster-scale behavior were not tested. No inference here establishes MOND or disproves dark matter. Cluster lensing observations address a different evidentiary setting; the Bullet Cluster study, for example, reported a separation between the dominant gaseous baryons and the lensing-inferred mass. [[4]](#ref-clowe) That evidence cannot be settled by adding predictors to this galaxy sample.




## 6. Next steps

A reproducible extension should first recover the original analysis code, record all preprocessing and fold assignments, and calculate paired uncertainty intervals at the galaxy level. Stellar mass-to-light assumptions and data-selection choices should be varied explicitly. A separate, pre-specified study can then examine clusters, dwarfs, and globular clusters with observables appropriate to each system. The [companion proposal](https://brandon-huang-studio.brainyalbatross8.chatgpt.site/curiosities/papers/beyond-rotation-curves.html) develops that direction.




## Provenance and references

This is an AI-assisted editorial expansion of the saved pilot note. All empirical counts and performance values above come from that note. The experiment has not been rerun or independently audited for this website. Methodological recommendations are proposed additions, not claims that those checks were already performed.

Huang research notebook. [SPARC multivariable gravity pilot](https://brandon-huang-studio.brainyalbatross8.chatgpt.site/curiosities/papers/pilot-source.md). Saved source note; unpublished. Results quoted from the note, not recomputed for this writeup.
Lelli, F., McGaugh, S. S., & Schombert, J. M. (2016). [SPARC: Mass Models for 175 Disk Galaxies with Spitzer Photometry and Accurate Rotation Curves](https://ui.adsabs.harvard.edu/abs/2016AJ....152..157L/abstract). The Astronomical Journal, 152, 157. DOI: 10.3847/0004-6256/152/6/157. [Data archive](https://astroweb.cwru.edu/SPARC/).
McGaugh, S. S., Lelli, F., & Schombert, J. M. (2016). [Radial Acceleration Relation in Rotationally Supported Galaxies](https://arxiv.org/abs/1609.05917). Physical Review Letters, 117, 201101. DOI: 10.1103/PhysRevLett.117.201101.
Clowe, D., et al. (2006). [A Direct Empirical Proof of the Existence of Dark Matter](https://arxiv.org/abs/astro-ph/0608407). The Astrophysical Journal Letters, 648, L109–L113. DOI: 10.1086/508162.
