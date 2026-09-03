#!/usr/bin/env python3
from pathlib import Path
import hashlib,math,sys
OUT=.8; START=.5; LEGACY_TARGET=.97; BROAD_TARGET=.955; COMPACT_TARGET=.965
CS=.002; CF=.025; BNS=.012; BNF=.060; BHS=.0025; BHF=.020; CNS=.004; CNF=.015; LOG=6.; MAXW=12.
GPU='d73cd24452280958f089e9124545a81461939e8fa0c9c95272b2825942e4b43d'
RSH='e0a438e51e12df5e6d8b53dc92892078ba7659791725cee54700869a6bc62b71'
MODEL='bb7f911afd1ac209a27f20b97d6f2d532bb1ffa1231374755859139cb4e30ff7'
NIGHTPROC='d5de1abf9bb42b92715fc1ec028d89d1408ecf6c4853cc95afbffc6bfe766b1e'
def fail(x): raise SystemExit('FAIL: '+x)
def cl(x,a,b): return max(a,min(b,x))
def sm(a,b,x):
 t=cl((x-a)/max(b-a,1e-9),0,1); return t*t*(3-2*t)
def mix(a,b,t): return a+(b-a)*t
def bw(g): return max(1,min(6,.9*max(1,g)))
def mapped_pre(x,w):
 if x<=START:return x
 q=cl((x-START)/max(w-START,1e-6),0,1); sh=math.log(1+LOG*q)/math.log(1+LOG)
 return START+(1/OUT-START)*sh
def proj(src,g,w=None): return cl(mapped_pre(src*g,w if w is not None else bw(g))*OUT,0,1)
def req(g,src,target):
 b=bw(g); post=src*g
 if not math.isfinite(src) or post<=START:return b
 tp=cl(target,.8,.995)/OUT; shape=cl((tp-START)/(1/OUT-START),0,1); x=(math.exp(shape*math.log(1+LOG))-1)/LOG
 return max(b,min(MAXW,START+(post-START)/max(x,1e-4)))
def q(a,p):
 a=sorted(a); return a[round((len(a)-1)*p)]
def floor26583(a,g):
 a=sorted(a); b=bw(g); n=len(a); p99=q(a,.99);p995=q(a,.995);p998=q(a,.998)
 th=b/max(g,1e-6); legacy=sum(v>=th for v in a)/n; ls=sm(CS,CF,legacy); lw=b
 if p99*g>b: lw=b+(req(g,p99,LEGACY_TARGET)-b)*ls
 if lw<=b+1e-6:ls=0
 outs=[proj(v,g,b) for v in a]; bnear=sum(v>=.930 for v in outs)/n; near=sum(v>=.965 for v in outs)/n; hard=sum(v>=.985 for v in outs)/n
 bs=max(sm(BNS,BNF,bnear)*sm(.930,.985,proj(p99,g,b)),.70*sm(BHS,BHF,hard))
 assist=sm(.020,.080,bnear); bg=mix(p99,max(p99,p995),.45*assist); bwht=b+(req(g,bg,BROAD_TARGET)-b)*bs
 broad=max(lw,bwht); broadS=max(ls,bs)
 cs=sm(CNS,CNF,near)*sm(.965,.995,proj(p995,g,b))*(1-sm(.25,.70,broadS))
 ca=sm(.006,.020,near); cg=mix(p995,max(p995,p998),.35*ca); cw=b+(req(g,cg,COMPACT_TARGET)-b)*cs
 return b,max(broad,cw),max(broadS,cs),p99,p995,p998,bnear,near,hard

def decision26584(grid,g):
 # grid contains source max-channel guide or NaN; flatten valid values exactly like matcher sorted guide list.
 vals=[v for row in grid for v in row if math.isfinite(v)]
 b,floorw,floors,p99,p995,p998,bnear,near,hard=floor26583(vals,g)
 projected=[[proj(v,g,b) if math.isfinite(v) else float('nan') for v in row] for row in grid]
 qs=[]
 for row in projected:
  for v in row:
   if math.isfinite(v):
    z=sm(.885,.995,v);qs.append(z*z)
 pressure=sum(qs)/len(qs) if qs else 0
 cts=sm(.0015,.024,pressure)
 cg=p99
 cg=mix(cg,max(cg,p995),.70*sm(.0015,.010,pressure))
 cg=mix(cg,max(cg,p998),.45*sm(.003,.020,pressure))
 cw=b+(req(g,cg,.958)-b)*cts
 gh=len(grid);gw=len(grid[0]); cell=8; cx=(gw+cell-1)//cell;cy=(gh+cell-1)//cell; cc=[0]*(cx*cy); guides=[];sp=0
 for y in range(1,gh-1):
  for x in range(1,gw-1):
   v=projected[y][x]
   if not math.isfinite(v) or v<.945:continue
   nn=0
   for dx,dy in [(-1,0),(1,0),(0,-1),(0,1)]:
    n=projected[y+dy][x+dx]
    if math.isfinite(n) and n>=.925:nn+=1
   if nn<1:continue
   sp+=1;cc[(y//cell)*cx+(x//cell)]+=1;guides.append(grid[y][x])
 sc=sum(v>=2 for v in cc); ss=0;sg=float('nan')
 if guides:
  guides=sorted(guides); sg=guides[math.ceil(len(guides)*.90)-1]
  ss=max(sm(2,18,sp),sm(1,5,sc))
 sw=b+(req(g,sg,.965)-b)*ss if ss>0 and math.isfinite(sg) else b
 return dict(base=b,floor=floorw,adaptive=max(floorw,cw,sw),pressure=pressure,continuous=cts,structuredPixels=sp,structuredCells=sc,structuredGuide=sg,structured=ss,p99=p99,p995=p995,p998=p998,bnear=bnear,near=near,hard=hard)

def grid(w,h,base=.25): return [[base for _ in range(w)] for _ in range(h)]
def put(g,coords,v):
 for x,y in coords:g[y][x]=v
 return g
# Jin reference model regression helpers.
def luma(v): return .2126*v[0]+.7152*v[1]+.0722*v[2]
def crms(v,y=None):
 if y is None:y=luma(v)
 return math.sqrt(sum((c-y)**2 for c in v)/3)
def cap(v,lc,cc):
 y=luma(v);cy=cl(y,-lc,lc);ch=[c-y for c in v];cm=math.sqrt(sum(x*x for x in ch)/3);s=cc/cm if cm>cc and cm>1e-8 else 1
 return [cy+x*s for x in ch]
def cleanup(res,ref,w,h):
 n=w*h;means=[sum(res[i][c] for i in range(n))/n for c in range(3)];cent=[]
 for i in range(n):
  row=[]
  for c in range(3):
   b=res[i][c];z=b-means[c]
   if b==0 or b*z<=0:z=0
   elif abs(z)>abs(b):z=b
   row.append(z)
  cent.append(row)
 low=[]
 for y in range(h):
  for x in range(w):
   ids=[yy*w+xx for yy in range(max(0,y-1),min(h-1,y+1)+1) for xx in range(max(0,x-1),min(w-1,x+1)+1)]
   low.append([sum(cent[j][c] for j in ids)/len(ids) for c in range(3)])
 out=[]
 for y in range(h):
  for x in range(w):
   i=y*w+x;rgb=ref[i];by=luma(rgb);peak=max(rgb);edge=0
   for dx,dy in [(-1,0),(1,0),(0,-1),(0,1)]:
    xx=x+dx;yy=y+dy
    if 0<=xx<w and 0<=yy<h:
     nr=ref[yy*w+xx];ny=luma(nr);d=math.sqrt(sum((rgb[c]-nr[c])**2 for c in range(3))/3);edge=max(edge,abs(by-ny),.60*d)
   dg=sm(.015,.085,edge);hg=sm(.72,.95,peak);basec=crms(rgb,by)/max(by,.08);ng=1-sm(.045,.18,basec);sg=1-sm(.12,.35,by);nsg=ng*sg*(1-dg)
   lp=cap(low[i],.012+.043*hg,.006+.012*hg+.006*nsg);hi=[cent[i][c]-low[i][c] for c in range(3)];hp=cap(hi,.020+.030*hg,.010+.012*hg+.010*nsg);ds=1-.78*dg*(1-.35*hg);row=[]
   for c in range(3):
    b=cent[i][c];a=(lp[c]+hp[c])*ds
    if b==0 or b*a<=0:a=0
    elif abs(a)>abs(b):a=b
    row.append(a)
   out.append(row)
 return cent,out
def rms(a):return math.sqrt(sum(x*x for x in a)/max(1,len(a)))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 if len(sys.argv)!=2: fail('usage candidate')
 r=Path(sys.argv[1])
 # No-tail identity: 26584 must equal exact 26583 floor.
 g=grid(96,72,.30);d=decision26584(g,4.0)
 if abs(d['adaptive']-d['floor'])>1e-7 or d['continuous']!=0 or d['structured']!=0:fail('no-tail changed')
 # Isolated sparkle / 2-pixel glint cannot move global tone.
 g=grid(96,72,.30);put(g,[(48,36)],1.6);d=decision26584(g,4.0)
 if d['adaptive']>d['floor']+1e-7 or d['structuredPixels']!=0:fail('isolated sparkle protected globally')
 g=grid(96,72,.30);put(g,[(48,36),(49,36)],1.6);d=decision26584(g,4.0)
 if d['structured']!=0 or d['adaptive']>d['floor']+1e-4:fail('two-pixel glint moved global tone')
 # Small coherent practical light: below 26583 population floor but spatially real -> additional headroom.
 g=grid(96,72,.30);coords=[(45+i%6,34+i//6) for i in range(18)];put(g,coords,.90);d=decision26584(g,4.70)
 if not (d['structuredPixels']>=18 and d['structured']>.95 and d['adaptive']>d['floor']*1.02):fail('structured practical light not protected')
 if proj(.90,4.70,d['adaptive'])>.975:fail('structured practical light still at ceiling')
 # Broad window/cloud tail gets continuous pressure and can never lose 26583 protection.
 g=grid(96,72,.34);coords=[(x,y) for y in range(18,42) for x in range(40,72)];put(g,coords,.78);d=decision26584(g,4.5)
 if not (d['continuous']>.8 and d['adaptive']+1e-7>=d['floor'] and d['floor']>d['base']):fail('broad tail not protected')
 # Compact sunset band remains at least 26583 and spatial path may add, never subtract.
 g=grid(96,72,.34);coords=[(x,y) for y in range(31,35) for x in range(36,58)];put(g,coords,.86);d=decision26584(g,5.2)
 if d['adaptive']+1e-7<d['floor'] or d['structured']<=0:fail('compact sunset regressed')
 # Midtone mapping <= .50 source-domain post-gain threshold remains exact because render shader is frozen.
 if abs(mapped_pre(.45,8)-.45)>1e-12:fail('midtone identity')
 # Jin global repaint removal.
 w=h=24;n=w*h;ref=[[.28,.28,.28] for _ in range(n)];res=[[.08,.04,-.02] for _ in range(n)];cent,out=cleanup(res,ref,w,h)
 if max(abs(x) for row in out for x in row)>2e-6:fail('global Jin style survived')
 # Local cleanup remains; highlight latitude > midtone; edge suppresses correction.
 res=[]
 for y in range(h):
  for x in range(w):
   broad=.018+.004*(x/max(w-1,1));spot=.030 if abs(x-w//2)<=1 and abs(y-h//2)<=1 else 0;res.append([broad+spot,.010+spot*.4,-.006])
 _,out=cleanup(res,ref,w,h);far=[abs(out[y*w+x][0]) for y in range(h) for x in range(w) if abs(x-w//2)>5 or abs(y-h//2)>5];spot=[abs(out[y*w+x][0]) for y in range(h) for x in range(w) if abs(x-w//2)<=1 and abs(y-h//2)<=1]
 if sum(spot)/len(spot)<4*max(sum(far)/len(far),1e-8):fail('local Jin cleanup lost')
 prop=[[.04,.04,.04] if i<n//2 else [-.04,-.04,-.04] for i in range(n)];mid=[[.35]*3 for _ in range(n)];hi=[[.96]*3 for _ in range(n)];_,om=cleanup([x[:] for x in prop],mid,w,h);_,oh=cleanup([x[:] for x in prop],hi,w,h)
 if rms([x for row in oh for x in row])<=1.5*rms([x for row in om for x in row]):fail('highlight Jin latitude lost')
 # Runtime byte/ownership invariants.
 if sha(r/'app/src/main/assets/shaders/motionv2/render.glsl')!=RSH:fail('render shader changed')
 if sha(r/'app/src/main/cpp/motionv2_jpeg444_jni.cpp')!=GPU:fail('native/GPU publication changed')
 if sha(r/'app/src/main/assets/models/iris_night_jin_lol_512.onnx')!=MODEL:fail('Jin model changed')
 if sha(r/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightProcessor.java')!=NIGHTPROC:fail('Night capture owner changed')
 matcher=(r/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java').read_text();jin=(r/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightNeuralEnhancer.java').read_text()
 for t in ['IRIS_26584_CONTINUOUS_SPATIAL_HIGHLIGHT_OWNER','IRIS_26584_ALL_SCENE_HIGHLIGHT_DECISION','floor26583SceneWhite','structuredPixels','continuousTailPressure','spatialPopulationIndependent=true continuousTail=true','localToneMap=false','NIGHT_DARK_ADVANTAGE_EV = 0.40f','NIGHT_BRIGHT_ADVANTAGE_EV = 0.30f']:
  if t not in matcher:fail('matcher contract '+t)
 for t in ['IRIS_26584_JIN_CLEANUP_ONLY_OWNER','constrainCleanupResidual(residual, px)','globalStyleAuthority=false','highlightCleanupRetained=true','nativeSabreGuidedTransferUnchanged=true']:
  if t not in jin:fail('Jin contract '+t)
 if 'presentedLuma(s, 1.0f)' in matcher:fail('26582 Java signature regression')
 print('PASS no-tail identity; successful 26583 broad+compact result is strict floor')
 print('PASS isolated sparkle/two-pixel glint ignored; coherent practical light protected independent of global population')
 print('PASS broad window/cloud continuous pressure + compact sunset structured protection')
 print('PASS body/midtones and uniform-RGB render ownership unchanged; render shader frozen')
 print('PASS Night +0.30..0.40 EV advantage preserved; Jin retained cleanup-only with global repaint suppression')
 print('PASS Jin ONNX, Night capture owner, native guided transfer and GPU publication frozen')
if __name__=='__main__':main()
