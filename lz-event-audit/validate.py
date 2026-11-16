"""Check the shared rate engine against numbers published by other groups.

Run: python validate.py
Each check prints our value next to the published one.
"""

from dataclasses import replace

import numpy as np
from scipy.optimize import brentq

from rates import (Detector, Halo, Model, XENON, AMU_GEV, predict,
                   sigma_for_one_event, vmin_kms)

DET = Detector()


def higgsino_delta_one_event(halo, det=DET, m=1100.0, sigma_n=7.3e-39):
    """Splitting that gives one selected ROI event for a pure higgsino."""
    f = lambda d: predict(Model(m, d, "QW", sigma_n), halo, det).N_roi - 1.0
    return brentq(f, 250.0, 520.0, xtol=0.05)


def check_rodd():
    print("\n[1] Rodd, Safdi, Slatyer & Xu (2609.04175), Table I, Helm form factor")
    print("    1.1 TeV higgsino, sigma_n = 7.3e-39 cm^2; delta_1 gives one ROI event; sideband 350-590 keV")
    published = {544: (377, 8.3, 4.9), 567: (393, 10.3, 6.6), 610: (423, 12.7, 8.8)}
    for vE_label, kw in [("fixed vE = 254", dict(vE=254.0)),
                         ("year-averaged vE = 250.2 +/- 14.9", dict(vE=250.2, dvE=14.9))]:
        print(f"    halo: {vE_label}")
        for vesc, (d_pub, Nabove_pub, Nsb_pub) in published.items():
            h = Halo(vesc=vesc, **kw)
            d1 = higgsino_delta_one_event(h)
            p = predict(Model(1100.0, d1, "QW", 7.3e-39), h, DET)
            print(f"      vesc {vesc}: delta_1 {d1:6.1f} (pub {d_pub})   "
                  f"N_>270 {p.N_above:5.1f} (pub {Nabove_pub})   N_SB {p.N_sb:5.1f} (pub {Nsb_pub})")


def check_baer_barger():
    print("\n[2] Baer & Barger (2609.06153), Table I: exothermic, charge-coupled, LZ halo")
    rows = [(300, -300, 1.5e-45, 155, 0.106), (500, -275, 2.2e-45, 155, 0.188),
            (500, -350, 3.8e-45, 163, 0.011), (800, -350, 6.7e-45, 164, 0.009),
            (1000, -400, 1.3e-44, 172, 0.000)]
    h = Halo()
    for m, d, s_pub, peak_pub, ratio_pub in rows:
        mod = Model(m, d, "Z")
        s1 = sigma_for_one_event(mod, h)
        p = predict(mod, h, DET, sigma_n=s1)
        E, sel = p.grid["E"], p.grid["sel_true"]
        dE = E[1] - E[0]
        lo = np.sum(sel[(E >= 5.4) & (E < 70)]) * dE
        hi = np.sum(sel[(E >= 70) & (E <= 269.9)]) * dE
        peak_true = E[np.argmax(sel)]
        print(f"    m {m:5d} d {d:5d}: sigma_p {s1:.2e} (pub {s_pub:.1e})  "
              f"peak {peak_true:5.0f} (pub {peak_pub})  N<70/N>70 {lo/hi:.3f} (pub {ratio_pub:.3f})")


def check_vmin():
    print("\n[3] 2609.13038: v_min at 248 keV on Xe-131 for its benchmarks (pub 786-797 km/s)")
    mA = 130.905082 * AMU_GEV
    for m, d in [(744.04, 361.327), (997.57, 370.0), (1479.37, 380.0)]:
        print(f"    m {m:8.2f} delta {d:7.3f}: v_min {float(vmin_kms(248.0, m, d, mA)):6.1f} km/s")
    print(f"    halo cutoff vesc + vE = {544 + 254} km/s (pub 798)")


def check_mahapatra_paul():
    print("\n[4] Mahapatra & Paul (2609.14799): 1 TeV, delta 300 keV, contact SI;"
          " share of events below 150 keV (pub 17.44%)")
    h = Halo(v0=220.0, vesc=540.0, vE=232.0)
    det = replace(DET, res_a=1.46 * np.sqrt(248.0), res_b=0.0)
    p = predict(Model(1000.0, 300.0, "A"), h, det)
    E, sel = p.grid["E"], p.grid["sel_true"]
    true_frac = np.sum(sel[E < 150]) / np.sum(sel)
    print(f"    ours: {100*p.frac_below_150:.2f}% (reconstructed E), {100*true_frac:.2f}% (true E)")


def check_kinematics():
    print("\n[5] Elastic reach: heaviest-speed recoil at 248 keV needs m >~ 74 GeV (Kannike et al. 2609.07742)")
    mA = 131.29 * AMU_GEV
    vmax = 544.0 + 254.0
    f = lambda m: float(vmin_kms(248.0, m, 0.0, mA)) - vmax
    print(f"    ours (Xe mean mass, vmax {vmax:.0f}): m_min = {brentq(f, 10, 1e4):.1f} GeV")


def check_delepine_khalil():
    print("\n[6] Delepine & Khalil (2609.26698), Table I: 1 TeV, true-energy windows, no efficiency,"
          " vE = 232 fixed")
    h = Halo(vE=232.0)
    for d, lo_pub, hi_pub in [(325.0, 4.04, 1.34), (339.2, 1.77, 1.77), (355.0, 0.40, 6.18)]:
        E = np.linspace(0.5, 1200, 2400)
        dE = E[1] - E[0]
        from rates import dRdE
        r = dRdE(E, Model(1000.0, d, "A"), h)
        win = lambda a, b: np.sum(r[(E >= a) & (E < b)]) * dE
        sig = win(225, 271)
        print(f"    delta {d:5.1f}: N(14-225)/N_sig {win(14,225)/sig:5.2f} (pub {lo_pub})   "
              f"N(271-800)/N_sig {win(271,800)/sig:5.2f} (pub {hi_pub})")


def check_di_mauro():
    print("\n[7] Di Mauro (2609.02608): 1 TeV pseudo-Dirac, delta 297.05 keV, sigma_N 6.5e-43 isoscalar,"
          " year-averaged halo")
    h = Halo(vE=250.2, dvE=14.9)
    p = predict(Model(1000.0, 297.05, "A", 6.5e-43), h, DET)
    E, sel = p.grid["E"], p.grid["sel_true"]
    dE = E[1] - E[0]
    n55_200 = np.sum(sel[(E >= 55) & (E < 200)]) * dE
    f200 = np.sum(sel[E >= 200]) * dE / p.N_roi
    print(f"    N_ROI {p.N_roi:.2f} (pub ~0.99)   N(55-200) {n55_200:.2f} (pub 0.73)   "
          f"f(>200) {f200:.3f} (pub 0.262)")


def check_dent_newstead():
    print("\n[8] Dent & Newstead (2609.04673): sideband events per search-window event;"
          " sigma_E = 23 keV, v_lab 250, sideband 350-680 keV")
    # Constant 23 keV resolution, as in that paper.
    from rates import Detector as D
    class Flat(D):
        def sigma_E(self, E):
            return np.full_like(np.asarray(E, dtype=float), 23.0)
    det = Flat(sideband=(350.0, 680.0))
    h = Halo(vE=250.0)
    for m, d, pub in [(1000.0, 350.0, 0.6), (42.0, -1000.0, 19.0)]:
        p = predict(Model(m, d, "Z"), h, det)
        print(f"    m {m:6.0f} delta {d:6.0f}: N_SB/N_ROI {p.ratio_sb:6.2f} (pub {pub})")


def _win(p, a, b):
    E, s = p.grid["E"], p.grid["sel_true"]
    return float(np.sum(s[(E >= a) & (E < b)]) * (E[1] - E[0]))


def check_own_halos():
    print("\n[9] Benchmarks under each paper's own halo (does the paper's claim reproduce?)")
    p = predict(Model(1100, 350, "QW", 7.4e-39), Halo(rho=0.4, v0=220, vesc=540, vE=232))
    print(f"    Fan & Reece 1.1 TeV/350 keV, rho 0.4, v0 220, vesc 540, vE 232 (not stated):"
          f" N(215-270) {_win(p, 215, 270):.2f} (claim 1)")
    p = predict(Model(1105, 350, "A", 1e-37), Halo(v0=220, vesc=544, vE=220))
    print(f"    Su, Yang & Yang 1.105 TeV/350 keV, sigma 1e-37, v0 220, vE 220:"
          f" N(160-200) {_win(p, 160, 200):.3f} (claim ~0), N(225-271) {_win(p, 225, 271):.2f} (claim ~1)")
    for name, m, d, pub in [("B0045", 744.04, 361.327, 1.039), ("C0893", 814.61, 361.137, 2.682),
                            ("B0461", 1192.44, 373.809, 1.130), ("B0581", 1479.37, 380.0, 0.591)]:
        p = predict(Model(m, d, "QW", 7.443e-39), Halo())
        print(f"    seesaw {name}, vlab 254: N_ROI {p.N_roi:.3f} (pub N_WS {pub})")
    for s in (1.09e-40, 1.92e-39):
        p = predict(Model(1000, 350, "QW", s), Halo())
        print(f"    LZ two-sided 90% interval edge sigma_V {s:.2e} (1 TeV, 350 keV): N_ROI {p.N_roi:.2f}"
              f"  (a Poisson interval for one event spans roughly 0.1-4.4)")


if __name__ == "__main__":
    check_own_halos()
    check_kinematics()
    check_vmin()
    check_baer_barger()
    check_mahapatra_paul()
    check_rodd()
    check_delepine_khalil()
    check_di_mauro()
    check_dent_newstead()
