# SPARC multivariable gravity pilot

## Question
Do radius, surface density, compactness, gas fraction, morphology, or a baryonic-potential proxy improve prediction of observed acceleration beyond baryonic acceleration alone?

## Data
Official SPARC mass-model and galaxy tables. Quality cuts: Q < 3, inclination >= 30 degrees, positive radius/velocity, and fractional velocity uncertainty <= 10%. Final sample: 2,700 radial measurements from 149 galaxies.

## Target and baseline
Target: log10(g_obs), with g_obs = V_obs^2 / R.
Baseline predictor: log10(g_bar), using the SPARC baryonic velocity components with M/L_disk=0.5 and M/L_bulge=0.7.

## Candidate predictors
Radius, radius/Reff, local stellar surface brightness, effective surface brightness, luminosity, HI-to-stellar mass proxy, compactness proxy, density proxy g_bar/R, local baryonic-potential proxy V_bar^2, and Hubble type.

## Validation
10-fold GroupKFold, holding out entire galaxies. Model: regularized histogram gradient boosting with identical hyperparameters for all feature sets.

## Results
| Model | RMSE (dex) | MAE (dex) |
|---|---:|---:|
| gbar only | 0.1381 | 0.1040 |
| gbar + radius | 0.1403 | 0.1064 |
| gbar + all variables | 0.1424 | 0.1101 |
| gbar + potential proxies | 0.1514 | 0.1171 |
| gbar + density/compactness | 0.1532 | 0.1210 |

None of the added variables improved held-out-galaxy prediction in this pilot. One-variable residual-correction tests also failed to improve the baseline.

## Interpretation
Within rotating SPARC galaxies, baryonic acceleration already captures nearly all easily recoverable predictive structure in these observables. This does not test temperature or cluster-scale behavior and does not establish MOND or disprove dark matter. The next decisive stage requires cluster data with lensing-derived acceleration, gas temperature, pressure, entropy, and dynamical-state indicators, plus globular-cluster and dwarf-galaxy samples, all evaluated with object-level holdouts.
