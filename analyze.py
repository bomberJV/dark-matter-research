"""Reproducible, exploratory SPARC profile comparison and synthetic recovery study.

Run python3 analyze.py. Results are profile-fit diagnostics, not a particle-model test.
No distance/inclination marginalization, observational covariance or cosmological priors.
"""
from pathlib import Path
from io import StringIO
from zipfile import ZipFile
import json, hashlib, csv, platform
import numpy as np
import scipy
from scipy.optimize import least_squares
from scipy.integrate import quad
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

BASE=Path(__file__).resolve().parent
OUT=BASE/'results'; OUT.mkdir(exist_ok=True)
G=4.30091e-6 # kpc (km/s)^2 / solar mass
SEED=20261113
LOW=np.array([3.,-1.5]); HIGH=np.array([11.,2.5])
STARTS=[(7.,0.),(6.,1.),(8.,-.3),(5.,2.)]
COLORS={'NFW':'#66d9cb','Burkert':'#ffb784','data':'#edf0e4'}
plt.rcParams.update({'figure.facecolor':'#101914','axes.facecolor':'#101914','savefig.facecolor':'#101914','text.color':'#edf0e4','axes.labelcolor':'#d1d8ca','xtick.color':'#a5b8aa','ytick.color':'#a5b8aa','axes.edgecolor':'#526258','font.size':11,'axes.grid':True,'grid.color':'#33443a','grid.alpha':.55,'font.family':'DejaVu Sans','svg.fonttype':'none'})

def halo_v2(r,p,model):
    rho,rs=10**np.asarray(p);x=np.asarray(r)/rs
    if model=='NFW':
        f=np.log1p(x)-x/(1+x)
        f=np.where(x<1e-3,x*x/2-2*x**3/3+3*x**4/4,f)
        mass=4*np.pi*rho*rs**3*f
    else:
        f=2*np.log1p(x)+np.log1p(x*x)-2*np.arctan(x)
        f=np.where(x<1e-3,4*x**3/3-x**4+4*x**7/7-x**8/2,f)
        mass=np.pi*rho*rs**3*f
    return G*mass/np.asarray(r)

def baryon_v2(a,ml):
    # Negative gas velocities encode outward radial force; retain their sign.
    return a[:,3]*np.abs(a[:,3])+ml*a[:,4]**2+1.4*ml*a[:,5]**2

def fit(r,y,err,b2,model):
    def residual(p):return (np.sqrt(np.maximum(b2+halo_v2(r,p,model),1e-12))-y)/err
    fits=[least_squares(residual,s,bounds=(LOW,HIGH),max_nfev=500,xtol=1e-9,ftol=1e-9,gtol=1e-9) for s in STARTS]
    opt=min(fits,key=lambda q:float(q.fun@q.fun))
    return {'p':opt.x.tolist(),'chi2':float(opt.fun@opt.fun),'bound':bool(np.any(opt.x-LOW<.015)|np.any(HIGH-opt.x<.015)),'success':bool(opt.success)}

def load_data():
    meta={}
    for line in (BASE/'data/SPARC_Lelli2016c.mrt').read_text().splitlines():
        try:
            fields=line.split();q=int(fields[17]);inc=float(fields[5]);name=fields[0]
            meta[name]={'q':q,'inclination':inc,'distance_mpc':float(fields[2]),'rotation_refs':' '.join(fields[18:])}
        except (ValueError,IndexError):continue
    arrays={};selection=[]
    with ZipFile(BASE/'data/Rotmod_LTG.zip') as z:
        for name in sorted(z.namelist()):
            key=name.replace('_rotmod.dat','');a=np.loadtxt(StringIO(z.read(name).decode()))
            valid=np.isfinite(a).all(axis=1)&(a[:,0]>0)&(a[:,1]>0)&(a[:,2]>0)
            a=a[valid];m=meta[key]
            reason='included' if m['q']<=2 and m['inclination']>=30 and len(a)>=12 else 'quality=3' if m['q']>2 else 'inclination<30' if m['inclination']<30 else 'fewer than 12 valid radii'
            selection.append({'galaxy':key,**m,'n':len(a),'selection':reason})
            if reason=='included':arrays[key]=a
    return arrays,selection

def write_csv(path,rows):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def savefig(fig,name):
    fig.savefig(OUT/f'{name}.svg',bbox_inches='tight');fig.savefig(OUT/f'{name}.png',dpi=160,bbox_inches='tight');plt.close(fig)

def verify():
    for model in ['NFW','Burkert']:
        rho,rs=2e7,3.
        density=(lambda r:rho/((r/rs)*(1+r/rs)**2)) if model=='NFW' else (lambda r:rho/((1+r/rs)*(1+(r/rs)**2)))
        for r in [.01,.3,3.,30.]:
            direct=4*np.pi*quad(lambda x:density(x)*x*x,0,r,epsabs=.01)[0]*G/r
            assert np.isclose(direct,halo_v2(r,np.log10([rho,rs]),model),rtol=2e-6)
        r=np.geomspace(.2,30,35);p=np.log10([rho,rs]);y=np.sqrt(halo_v2(r,p,model));f=fit(r,y,np.ones(len(r)),np.zeros(len(r)),model)
        assert f['chi2']<1e-10
    assert baryon_v2(np.array([[1,1,1,-5,0,0,0,0.]]),.5)[0]==-25
    return 'Analytic mass integrals, noiseless parameter recovery and signed gas contribution passed.'

def main():
    verification=verify();arrays,selection=load_data();rows=[];fits={}
    for i,(name,a) in enumerate(arrays.items()):
        for ml in [.3,.5,.7]:
            for floor in ([5.,0.] if ml==.5 else [5.]):
                err=np.sqrt(a[:,2]**2+floor**2);fs={m:fit(a[:,0],a[:,1],err,baryon_v2(a,ml),m) for m in ['NFW','Burkert']}
                rows.append({'galaxy':name,'n':len(a),'disc_ml':ml,'bulge_ml':round(1.4*ml,2),'error_floor_kms':floor,'chi2_nfw':fs['NFW']['chi2'],'chi2_burkert':fs['Burkert']['chi2'],'delta_chi2_nfw_minus_burkert':fs['NFW']['chi2']-fs['Burkert']['chi2'],'nfw_bound':fs['NFW']['bound'],'burkert_bound':fs['Burkert']['bound'],'nfw_success':fs['NFW']['success'],'burkert_success':fs['Burkert']['success']})
                if ml==.5 and floor==5:fits[name]=fs
        if i%25==0:print('Fitted',i+1,'/',len(arrays),flush=True)
    write_csv(OUT/'profile_fits.csv',rows);write_csv(OUT/'sample_selection.csv',selection)
    base=[r for r in rows if r['disc_ml']==.5 and r['error_floor_kms']==5]
    delta=np.array([r['delta_chi2_nfw_minus_burkert'] for r in base]);meds=[]
    for ml in [.3,.5,.7]:
        sub=[r for r in rows if r['disc_ml']==ml and r['error_floor_kms']==5]
        vals=np.array([r['delta_chi2_nfw_minus_burkert'] for r in sub]);meds.append({'ml':ml,'burkert_lower_chi2':int((vals>0).sum()),'nfw_lower_chi2':int((vals<0).sum()),'within_2':int((abs(vals)<2).sum()),'median_delta':float(np.median(vals))})
    sensitivity={r['galaxy']:r['delta_chi2_nfw_minus_burkert'] for r in rows if r['disc_ml']==.3 and r['error_floor_kms']==5}
    high={r['galaxy']:r['delta_chi2_nfw_minus_burkert'] for r in rows if r['disc_ml']==.7 and r['error_floor_kms']==5}
    flips=int(sum(np.sign(sensitivity[n])!=np.sign(high[n]) for n in arrays))
    fig,axs=plt.subplots(1,2,figsize=(12,4.8));order=np.argsort(delta);axs[0].scatter(np.arange(len(delta)),delta[order],c=np.where(delta[order]>0,COLORS['Burkert'],COLORS['NFW']),s=24);axs[0].axhline(0,c='#eeeecc',lw=.8);axs[0].set_yscale('symlog',linthresh=2);axs[0].set(xlabel='Galaxies ordered by fit difference',ylabel='χ²(NFW) − χ²(Burkert)',title='Profile preference is not particle identity')
    axs[1].scatter(list(sensitivity.values()),[high[n] for n in sensitivity],c='#c5d4a2',s=24,alpha=.75);axs[1].axhline(0,c='#eeeecc',lw=.8);axs[1].axvline(0,c='#eeeecc',lw=.8);axs[1].set_xscale('symlog',linthresh=2);axs[1].set_yscale('symlog',linthresh=2);axs[1].set(xlabel='Δχ² at disc M/L = 0.3',ylabel='Δχ² at disc M/L = 0.7',title=f'{flips} / {len(arrays)} change preference sign');fig.tight_layout();savefig(fig,'profile-comparison')
    examples=['NGC2403','DDO154','NGC3198','IC2574'];fig,axs=plt.subplots(2,2,figsize=(12,8));example_payload={}
    for ax,name in zip(axs.flat,examples):
        a=arrays[name];ax.errorbar(a[:,0],a[:,1],np.sqrt(a[:,2]**2+25),fmt='.',color=COLORS['data'],alpha=.65,label='SPARC + 5 km/s floor');b2=baryon_v2(a,.5)
        ax.plot(a[:,0],np.sqrt(np.maximum(b2,0)),ls=':',color='#a2b5a6',label='Baryonic contribution')
        preds={}
        for m in ['NFW','Burkert']:
            pred=np.sqrt(np.maximum(b2+halo_v2(a[:,0],fits[name][m]['p'],m),0));ax.plot(a[:,0],pred,c=COLORS[m],label=m);preds[m]=pred.tolist()
        ax.set(title=f'{name} · Δχ² = {fits[name]["NFW"]["chi2"]-fits[name]["Burkert"]["chi2"]:.1f}',xlabel='Radius / kpc',ylabel='Circular speed / km s⁻¹')
        example_payload[name]={'r':a[:,0].tolist(),'v':a[:,1].tolist(),'err':np.sqrt(a[:,2]**2+25).tolist(),'baryonic':np.sqrt(np.maximum(b2,0)).tolist(),'predictions':preds,'fits':fits[name]}
    axs[0,0].legend(fontsize=8);fig.tight_layout();savefig(fig,'observed-curves')
    # A deliberately controlled recovery benchmark. Paired noise for full/truncated curves.
    rng=np.random.default_rng(SEED);rad=np.geomspace(.3,30,40);vb2=3200*(rad/2)/(1+rad/2)**2
    params={'Burkert':np.log10([2e7,3.])};rs=5.;unit=halo_v2(np.array([30.]),np.log10([1.,rs]),'NFW')[0];rho=halo_v2(np.array([30.]),params['Burkert'],'Burkert')[0]/unit;params['NFW']=np.log10([rho,rs])
    trials=[];N=100
    for truth in ['NFW','Burkert']:
        mean=np.sqrt(vb2+halo_v2(rad,params[truth],truth))
        for rep in range(N):
            y=mean+rng.normal(0,5,len(rad))
            for cut in [.3,3.,8.]:
                mask=rad>=cut;fs={m:fit(rad[mask],y[mask],np.full(mask.sum(),5.),vb2[mask],m) for m in ['NFW','Burkert']};d=fs['NFW']['chi2']-fs['Burkert']['chi2'];picked='Burkert' if d>0 else 'NFW'
                trials.append({'truth':truth,'repetition':rep,'minimum_radius_kpc':cut,'n':int(mask.sum()),'delta_chi2':d,'correct':picked==truth,'strong_correct':(d>10 if truth=='Burkert' else d<-10),'optimizer_success':all(f['success'] for f in fs.values()),'any_bound':any(f['bound'] for f in fs.values())})
    write_csv(OUT/'synthetic_trials.csv',trials);recovery=[]
    for truth in ['NFW','Burkert']:
        for cut in [.3,3.,8.]:
            sub=[x for x in trials if x['truth']==truth and x['minimum_radius_kpc']==cut];k=sum(x['correct'] for x in sub);p=k/N;z=1.96;den=1+z*z/N;center=(p+z*z/(2*N))/den;half=z*np.sqrt(p*(1-p)/N+z*z/(4*N*N))/den
            recovery.append({'truth':truth,'minimum_radius_kpc':cut,'trials':N,'correct':k,'fraction':p,'wilson_low':center-half,'wilson_high':center+half,'strong_correct':sum(x['strong_correct'] for x in sub)})
    fig,axs=plt.subplots(1,2,figsize=(12,4.7))
    for m in ['NFW','Burkert']:
        axs[0].plot(rad,np.sqrt(vb2+halo_v2(rad,params[m],m)),c=COLORS[m],lw=2,label=f'{m} generating model');sub=[x for x in recovery if x['truth']==m];ys=np.array([x['fraction'] for x in sub]);axs[1].errorbar([x['minimum_radius_kpc'] for x in sub],ys,yerr=[ys-np.array([x['wilson_low'] for x in sub]),np.array([x['wilson_high'] for x in sub])-ys],marker='o',c=COLORS[m],capsize=4,label=f'{m} truth')
    axs[0].set(xscale='log',xlabel='Radius / kpc',ylabel='Speed / km s⁻¹',title='Synthetic curves: same halo speed at 30 kpc');axs[1].set(xlabel='Innermost retained radius / kpc',ylabel='Fraction selecting generating profile',ylim=(0,1.05),title='100 noise realizations per truth / cutoff');axs[1].axhline(.5,ls=':',c='#a3b8a5');axs[0].legend(fontsize=9);axs[1].legend(fontsize=9);fig.tight_layout();savefig(fig,'synthetic-recovery')
    summary={'date':'2026-11-13','seed':SEED,'sample_n':len(arrays),'radial_points':sum(len(a) for a in arrays.values()),'parent_n':len(selection),'selection':'Q≤2; inclination≥30 degrees; at least 12 positive, finite radius/speed/error rows','baseline_disc_ml':.5,'baseline_bulge_ml':.7,'error_floor_kms':5,'nfw_lower_chi2':int((delta<0).sum()),'burkert_lower_chi2':int((delta>0).sum()),'within_2':int((abs(delta)<2).sum()),'median_delta':float(np.median(delta)),'preference_sign_changes_ml_03_to_07':flips,'baseline_bound_any':sum(r['nfw_bound'] or r['burkert_bound'] for r in base),'optimizer_failures':sum(not r['nfw_success'] or not r['burkert_success'] for r in rows),'ml_sensitivity':meds,'synthetic_recovery':recovery,'validation':verification,'versions':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__,'matplotlib':matplotlib.__version__},'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (BASE/'data').iterdir() if p.is_file()}}
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2));(OUT/'curves.json').write_text(json.dumps(example_payload));(OUT/'fits.json').write_text(json.dumps(fits,indent=2));print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
