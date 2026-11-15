const canvas=document.querySelector('#curve-canvas'),select=document.querySelector('#galaxy'),status=document.querySelector('#curve-status');
let curves=null,pointer=null;
const colors={NFW:'#66d9cb',Burkert:'#ffb784',baryonic:'#a5b8aa'};
function draw(){
 if(!curves)return;const a=curves[select.value],dpr=Math.min(devicePixelRatio||1,2),w=canvas.clientWidth,h=canvas.clientHeight;
 canvas.width=Math.round(w*dpr);canvas.height=Math.round(h*dpr);const c=canvas.getContext('2d');c.scale(dpr,dpr);c.clearRect(0,0,w,h);
 const L=50,R=15,T=15,B=45,xmax=Math.max(...a.r)*1.03,ymax=Math.max(...a.v.map((v,i)=>v+a.err[i]),...a.predictions.NFW,...a.predictions.Burkert)*1.08;
 const X=x=>L+x/xmax*(w-L-R),Y=y=>h-B-y/ymax*(h-T-B);
 c.font='10px Arial';c.lineWidth=1;
 for(let i=0;i<=4;i++){const y=ymax*i/4;c.strokeStyle='#34473a';c.beginPath();c.moveTo(L,Y(y));c.lineTo(w-R,Y(y));c.stroke();c.fillStyle='#a5b8aa';c.textAlign='right';c.fillText(Math.round(y),L-8,Y(y)+3);const x=xmax*i/4;c.textAlign='center';c.fillText(x.toFixed(xmax<10?1:0),X(x),h-B+18)}
 c.textAlign='center';c.fillText('Radius / kpc',(w+L)/2,h-5);c.save();c.translate(12,h/2);c.rotate(-Math.PI/2);c.fillText('Speed / km s⁻¹',0,0);c.restore();
 function line(vals,color,dashed=false){c.strokeStyle=color;c.lineWidth=2;c.setLineDash(dashed?[3,4]:[]);c.beginPath();a.r.forEach((r,i)=>i?c.lineTo(X(r),Y(vals[i])):c.moveTo(X(r),Y(vals[i])));c.stroke();c.setLineDash([])}
 if(document.querySelector('#show-baryons').checked)line(a.baryonic,colors.baryonic,true);
 if(document.querySelector('#show-nfw').checked)line(a.predictions.NFW,colors.NFW);
 if(document.querySelector('#show-burkert').checked)line(a.predictions.Burkert,colors.Burkert);
 c.strokeStyle='#edf0e499';c.fillStyle='#edf0e4';c.lineWidth=1;
 a.r.forEach((r,i)=>{const x=X(r),y=Y(a.v[i]);c.beginPath();c.moveTo(x,Y(a.v[i]-a.err[i]));c.lineTo(x,Y(a.v[i]+a.err[i]));c.stroke();c.beginPath();c.arc(x,y,2.5,0,Math.PI*2);c.fill()});
 const delta=a.fits.NFW.chi2-a.fits.Burkert.chi2;
 status.textContent=`${select.value} · ${a.r.length} measured radii · Δχ² = ${delta.toFixed(2)} (${delta>0?'Burkert':'NFW'} lower). Hover or tap the plot to inspect a measurement.`;
 if(pointer!==null){let i=0;for(let j=1;j<a.r.length;j++)if(Math.abs(X(a.r[j])-pointer)<Math.abs(X(a.r[i])-pointer))i=j;c.strokeStyle='#edf0e4';c.setLineDash([3,4]);c.beginPath();c.moveTo(X(a.r[i]),T);c.lineTo(X(a.r[i]),h-B);c.stroke();c.setLineDash([]);status.textContent=`${select.value} · radius ${a.r[i].toFixed(2)} kpc · observed ${a.v[i].toFixed(1)} ± ${a.err[i].toFixed(1)} km/s · NFW ${a.predictions.NFW[i].toFixed(1)} · Burkert ${a.predictions.Burkert[i].toFixed(1)} km/s.`}
}
select.addEventListener('change',()=>{pointer=null;draw()});document.querySelectorAll('.toggles input').forEach(x=>x.addEventListener('change',draw));
canvas.addEventListener('pointermove',e=>{pointer=e.clientX-canvas.getBoundingClientRect().left;draw()});canvas.addEventListener('pointerdown',e=>{pointer=e.clientX-canvas.getBoundingClientRect().left;draw()});canvas.addEventListener('pointerleave',()=>{pointer=null;draw()});
canvas.addEventListener('keydown',e=>{if(!['ArrowLeft','ArrowRight'].includes(e.key))return;e.preventDefault();select.selectedIndex=(select.selectedIndex+(e.key==='ArrowRight'?1:select.options.length-1))%select.options.length;pointer=null;draw()});
new ResizeObserver(draw).observe(canvas);
fetch('curves.json').then(r=>{if(!r.ok)throw new Error('Unavailable data');return r.json()}).then(x=>{curves=x;draw()}).catch(()=>{status.textContent='The interactive data could not load. Figure 1 and the source download contain the same observations and fits.'});
