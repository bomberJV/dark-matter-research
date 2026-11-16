"""Nuclear-recoil rates in xenon for elastic and inelastic dark matter.

One shared engine for the LZ 248 keV audit. Every published benchmark is
evaluated here with the same halo, form factor, efficiency, resolution and
energy windows, so differences between papers come from the physics inputs
(mass, splitting, coupling) and not from each paper's own conventions.

Conventions
- Natural xenon, nine isotopes, Helm form factor (Lewin & Smith 1996).
- Standard Halo Model: truncated Maxwellian, analytic mean inverse speed.
- Spin-independent, momentum-independent coupling. The coupling choice sets
  the per-isotope weight: A^2 (isoscalar), Z^2 (charge, dark photon) or
  Q_W^2 (Z boson, higgsino-like). Shapes barely depend on it.
- delta > 0 is endothermic (up-scattering), delta < 0 is exothermic.
- Energies in keV, speeds in km/s, cross-sections in cm^2.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.special import erf, spherical_jn
from scipy.stats import norm

# Physical constants
C_KMS = 299792.458                 # speed of light, km/s
AMU_GEV = 0.93149410242            # atomic mass unit, GeV
M_P_GEV = 0.93827208816
M_N_GEV = 0.93956542052
HBARC_GEV_FM = 0.1973269804        # GeV fm
GEV_TO_KG = 1.78266192e-27
KEV_TO_J = 1.602176634e-16
SIN2_THETA_W = 0.2312

# Natural xenon: (A, Z, mole fraction, atomic mass in u)
XENON = [
    (124, 54, 0.000952, 123.905893),
    (126, 54, 0.000890, 125.904274),
    (128, 54, 0.019102, 127.903531),
    (129, 54, 0.264006, 128.904779),
    (130, 54, 0.040710, 129.903508),
    (131, 54, 0.212324, 130.905082),
    (132, 54, 0.269086, 131.904154),
    (134, 54, 0.104357, 133.905395),
    (136, 54, 0.088573, 135.907219),
]

SECONDS_PER_YEAR = 365.25 * 86400.0
KG_PER_TONNE = 1000.0


@dataclass(frozen=True)
class Halo:
    """Standard Halo Model. Defaults are the LZ / Baxter et al. (2021) values."""
    rho: float = 0.3          # GeV / cm^3
    v0: float = 238.0         # km/s
    vesc: float = 544.0       # km/s
    vE: float = 254.0         # km/s, Earth speed in the Galactic frame
    # Annual modulation: if dvE > 0, eta is averaged over a year with
    # vE(t) = vE + dvE cos(2 pi t).  If `phase` is set (fraction of a year
    # after the June 2 peak), eta is evaluated at that single time instead.
    dvE: float = 0.0
    phase: float | None = None
    label: str = "SHM (LZ)"


@dataclass(frozen=True)
class Detector:
    """LZ high-energy analysis (arXiv:2609.02823) as used in the public recasts."""
    exposure_tyr: float = 2.84
    # Efficiency vs true NR energy, piecewise linear (Baer & Barger 2609.06153
    # approximation of LZ Fig. S2): 50% at 5.4 keV, 96% from 14 to 250 keV,
    # 50% at 269.9 keV.
    eff_knots_E: tuple = (5.4, 14.0, 250.0, 269.9)
    eff_knots_v: tuple = (0.50, 0.96, 0.96, 0.50)
    eff_floor_E: float = 4.0     # below this, zero
    eff_ceil_E: float = 285.0    # above this, zero
    # Resolution sigma_E(E) = sqrt(a^2 E/248 + (b E)^2)  (Rodd et al. 2609.04175)
    res_a: float = 23.0
    res_b: float = 0.093
    # High-energy sideband in reconstructed energy, unit acceptance.
    sideband: tuple = (350.0, 590.0)
    # Standard low-energy WIMP window (where LZ sees no excess).
    low_window: tuple = (5.4, 55.0)
    event_E: float = 248.0
    energy_scale: float = 1.0    # coherent calibration shift of reconstructed E

    def efficiency(self, E):
        E = np.asarray(E, dtype=float)
        eff = np.interp(E, self.eff_knots_E, self.eff_knots_v)
        lo_E, hi_E = self.eff_knots_E[0], self.eff_knots_E[-1]
        lo_v, hi_v = self.eff_knots_v[0], self.eff_knots_v[-1]
        # Linear roll-off to zero outside the 50% points.
        below = E < lo_E
        eff = np.where(below, lo_v * np.clip((E - self.eff_floor_E) / (lo_E - self.eff_floor_E), 0, 1), eff)
        above = E > hi_E
        eff = np.where(above, hi_v * np.clip((self.eff_ceil_E - E) / (self.eff_ceil_E - hi_E), 0, 1), eff)
        return eff

    def sigma_E(self, E):
        E = np.asarray(E, dtype=float)
        return np.sqrt(self.res_a ** 2 * E / 248.0 + (self.res_b * E) ** 2)


@dataclass(frozen=True)
class Model:
    m_chi: float                 # GeV
    delta: float                 # keV, >0 endothermic, <0 exothermic
    coupling: str = "QW"         # "A" (isoscalar), "Z" (charge), "QW" (Z boson), "N" (neutron)
    sigma_n: float | None = None  # per-nucleon cross-section, cm^2 (see coupling)
    q_power: int = 0             # extra (q/q_ref)^(2*q_power) factor; 0 = contact SI
    label: str = ""


# --- Nuclear physics -------------------------------------------------------

def helm_ff2(E_keV, A, m_A_GeV):
    """Squared Helm form factor, Lewin & Smith parameters."""
    E_GeV = np.asarray(E_keV, dtype=float) * 1e-6
    q = np.sqrt(2.0 * m_A_GeV * E_GeV) / HBARC_GEV_FM          # fm^-1
    s, a = 0.9, 0.52
    c = 1.23 * A ** (1.0 / 3.0) - 0.60
    rn = np.sqrt(c ** 2 + (7.0 / 3.0) * np.pi ** 2 * a ** 2 - 5.0 * s ** 2)
    qr = np.maximum(q * rn, 1e-9)
    F = 3.0 * spherical_jn(1, qr) / qr * np.exp(-(q * s) ** 2 / 2.0)
    return F ** 2


def coupling_weight(coupling, A, Z):
    N = A - Z
    if coupling == "A":
        return float(A) ** 2
    if coupling == "Z":
        return float(Z) ** 2
    if coupling == "N":
        return float(N) ** 2
    if coupling == "QW":
        return (N - (1.0 - 4.0 * SIN2_THETA_W) * Z) ** 2
    raise ValueError(coupling)


def reference_nucleon_mass(coupling):
    return M_P_GEV if coupling == "Z" else (M_N_GEV if coupling in ("N", "QW") else AMU_GEV)


# --- Halo ------------------------------------------------------------------

def _eta_shm(vmin, v0, vesc, vE):
    """Mean inverse speed (s/km) for a truncated Maxwellian, lab frame."""
    x = np.asarray(vmin, dtype=float) / v0
    y, z = vE / v0, vesc / v0
    Nesc = erf(z) - 2.0 * z / np.sqrt(np.pi) * np.exp(-z ** 2)
    pref = 1.0 / (2.0 * Nesc * v0 * y)
    ez = np.exp(-z ** 2)
    out = np.zeros_like(x)
    r1 = x < z - y
    r2 = (x >= z - y) & (x < z + y)
    out[r1] = pref * (erf(x[r1] + y) - erf(x[r1] - y) - 4.0 * y / np.sqrt(np.pi) * ez)
    out[r2] = pref * (erf(z) - erf(x[r2] - y) - 2.0 * (z + y - x[r2]) / np.sqrt(np.pi) * ez)
    return np.clip(out, 0.0, None)


def eta(vmin, halo: Halo):
    if halo.dvE == 0.0:
        return _eta_shm(vmin, halo.v0, halo.vesc, halo.vE)
    if halo.phase is not None:
        vE = halo.vE + halo.dvE * np.cos(2 * np.pi * halo.phase)
        return _eta_shm(vmin, halo.v0, halo.vesc, vE)
    ts = (np.arange(48) + 0.5) / 48.0
    return np.mean([_eta_shm(vmin, halo.v0, halo.vesc, halo.vE + halo.dvE * np.cos(2 * np.pi * t)) for t in ts], axis=0)


def vmin_kms(E_keV, m_chi, delta_keV, m_A_GeV):
    """Minimum lab speed for a recoil E (keV) with splitting delta (keV)."""
    E = np.asarray(E_keV, dtype=float) * 1e-6     # GeV
    d = delta_keV * 1e-6
    mu = m_chi * m_A_GeV / (m_chi + m_A_GeV)
    with np.errstate(divide="ignore", invalid="ignore"):
        v = np.abs(m_A_GeV * E / mu + d) / np.sqrt(2.0 * m_A_GeV * E)
    return v * C_KMS


# --- Rates -----------------------------------------------------------------

def dRdE(E_keV, model: Model, halo: Halo, sigma_n=None):
    """Differential rate, events / (tonne yr keV), true recoil energy.

    If sigma_n is None and model.sigma_n is None, uses 1e-40 cm^2 (shape only).
    """
    s_n = sigma_n if sigma_n is not None else (model.sigma_n if model.sigma_n is not None else 1e-40)
    E = np.asarray(E_keV, dtype=float)
    m_ref = reference_nucleon_mass(model.coupling)
    mu_ref = model.m_chi * m_ref / (model.m_chi + m_ref)
    masses = np.array([iso[3] * AMU_GEV for iso in XENON])
    fracs = np.array([iso[2] for iso in XENON])
    wmass = fracs * masses / np.sum(fracs * masses)      # mass fractions
    total = np.zeros_like(E)
    rho_kg_m3 = halo.rho * GEV_TO_KG * 1e6
    for (A, Z, _, mu_amu), w, mA in zip(XENON, wmass, masses):
        mu_A = model.m_chi * mA / (model.m_chi + mA)
        sigma_A = s_n * (mu_A / mu_ref) ** 2 * coupling_weight(model.coupling, A, Z)   # cm^2
        F2 = helm_ff2(E, A, mA)
        if model.q_power:
            q2 = 2.0 * mA * E * 1e-6                       # GeV^2
            q2_ref = (0.1) ** 2                            # 100 MeV reference
            F2 = F2 * (q2 / q2_ref) ** model.q_power
        et = eta(vmin_kms(E, model.m_chi, model.delta, mA), halo) * 1e-3   # s/m
        # dR/dE = rho sigma F^2 eta / (2 m_chi mu^2), SI units -> 1/(J kg s)
        r = (rho_kg_m3 * sigma_A * 1e-4 * F2 * et
             / (2.0 * model.m_chi * GEV_TO_KG * (mu_A * GEV_TO_KG) ** 2))
        total += w * r
    # 1/(J kg s) -> 1/(keV tonne yr)
    return total * KEV_TO_J * KG_PER_TONNE * SECONDS_PER_YEAR


@dataclass
class Prediction:
    N_roi: float                 # selected events in the LZ ROI (true-energy efficiency)
    N_low: float                 # selected events in the 5.4-55 keV standard window
    N_sb: float                  # events in the high-energy sideband (reconstructed, unit acceptance)
    N_above: float               # events with true E above 270 keV (no efficiency)
    p_event: float               # selected event density at the observed energy, per keV
    E_peak: float                # peak of the selected, smeared spectrum (keV)
    frac_below_150: float        # fraction of ROI events with reconstructed E < 150 keV
    grid: dict = field(default_factory=dict, repr=False)

    @property
    def ratio_sb(self):
        return self.N_sb / self.N_roi if self.N_roi > 0 else np.inf

    @property
    def shape_score(self):
        """p(E_event) / (N_roi + N_sb): normalisation-free; per keV."""
        tot = self.N_roi + self.N_sb
        return self.p_event / tot if tot > 0 else 0.0


_KERNELS: dict = {}


def _kernel(det: Detector, E_max, n):
    key = (type(det).__name__, det.res_a, det.res_b, det.energy_scale, E_max, n)
    if key not in _KERNELS:
        E = np.linspace(0.5, E_max, n)
        sig = det.sigma_E(E)
        k = det.energy_scale
        _KERNELS[key] = norm.pdf(E[:, None], loc=k * E[None, :], scale=k * sig[None, :])
    return _KERNELS[key]


def predict(model: Model, halo: Halo = Halo(), det: Detector = Detector(),
            sigma_n=None, E_max=1200.0, n=2400) -> Prediction:
    E = np.linspace(0.5, E_max, n)
    dE = E[1] - E[0]
    r = dRdE(E, model, halo, sigma_n) * det.exposure_tyr      # events / keV, true E
    eff = det.efficiency(E)
    sel = r * eff
    sig = det.sigma_E(E)
    k = det.energy_scale
    # Reconstructed-energy density of selected events (efficiency applied on true E).
    Erec = E
    kern = _kernel(det, E_max, n)
    sel_rec = kern @ (sel * dE)
    all_rec = kern @ (r * dE)

    N_roi = float(np.sum(sel) * dE)
    lo, hi = det.low_window
    N_low = float(np.sum(sel[(E >= lo) & (E <= hi)]) * dE)
    a, b = det.sideband
    sb_prob = norm.cdf((b - k * E) / (k * sig)) - norm.cdf((a - k * E) / (k * sig))
    N_sb = float(np.sum(r * sb_prob) * dE)
    N_above = float(np.sum(r[E > 270.0]) * dE)
    p_event = float(np.interp(det.event_E, Erec, sel_rec))
    E_peak = float(Erec[np.argmax(sel_rec)])
    frac150 = float(np.sum(sel_rec[Erec < 150.0]) / max(np.sum(sel_rec), 1e-300))
    return Prediction(N_roi, N_low, N_sb, N_above, p_event, E_peak, frac150,
                      grid={"E": E, "sel_true": sel, "Erec": Erec, "sel_rec": sel_rec, "all_rec": all_rec})


def sigma_for_one_event(model: Model, halo: Halo = Halo(), det: Detector = Detector()):
    """Per-nucleon cross-section that gives exactly one selected ROI event."""
    p = predict(model, halo, det, sigma_n=1e-40)
    return 1e-40 / p.N_roi if p.N_roi > 0 else np.inf


# Normalisation-free penalties (signal-only likelihood, background ~0.01 neglected).
# With mu = s*(a, b) in (ROI, sideband) and one event at E*, the extended
# likelihood is maximised at s = 1/(a+b), giving
#   ln L_max = -1 + ln[ p(E*) / (a + b) ].
# Reference: a narrow line at E* smeared by the resolution, p/(a+b) = 1/(sqrt(2 pi) sigma_E).

def delta_chi2(pred: Prediction, det: Detector = Detector()):
    ref = 1.0 / (np.sqrt(2 * np.pi) * float(det.sigma_E(det.event_E)) * det.energy_scale)
    sc = pred.shape_score
    return 2.0 * np.log(ref / sc) if sc > 0 else np.inf


def delta_chi2_roi_only(pred: Prediction, det: Detector = Detector()):
    ref = 1.0 / (np.sqrt(2 * np.pi) * float(det.sigma_E(det.event_E)) * det.energy_scale)
    sc = pred.p_event / pred.N_roi if pred.N_roi > 0 else 0.0
    return 2.0 * np.log(ref / sc) if sc > 0 else np.inf
