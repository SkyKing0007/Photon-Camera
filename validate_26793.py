#!/usr/bin/env python3
from pathlib import Path
import hashlib, random, re, sys, textwrap
if len(sys.argv)!=3: raise SystemExit('usage: validate_26793.py BASE_ROOT CANDIDATE_ROOT')
BASE,CAND=map(Path,sys.argv[1:])
ALLOW={'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt','app/version.properties'}
S='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'
def need(c,m):
    if not c: raise AssertionError(m)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def uni(root): return {p.relative_to(root).as_posix():sha(p) for p in (root/'app').rglob('*') if p.is_file()}
def shader(root,name,rel=S):
    t=(root/rel).read_text(); m=re.search(r'^\s*(?:private\s+)?val\s+'+re.escape(name)+r'\s*=\s*"""',t,re.M)
    need(m is not None,f'{name}: declaration missing'); b=t.find('""".trimIndent()',m.end()); need(b>=0,f'{name}: terminator missing')
    return textwrap.dedent(t[m.end():b]).strip('\n')+'\n'
def segment(src,a,b):
    i=src.index(a); j=src.index(b,i); return src[i:j]
a,c=uni(BASE),uni(CAND); need(len(a)==len(c)==1779,(len(a),len(c))); need(set(a)==set(c),'file universe')
mod={p for p in a if a[p]!=c[p]}; need(mod==ALLOW,f'changed allowlist {sorted(mod)}')
print('PASS 26793 authority-seeded scope: 1779 files, exactly 2 modified / 0 added / 0 deleted')
need(sha(BASE/S)=='6918f5ed69b813cf3fb2602c041b31682d414c5418d3240f7dcad4122423a0cf','26792 prior Sabre hash')
need(sha(CAND/S)=='b6e81869e3ceb29dd02f6d83772be41bfc53031ea1158344694ca5704a825812','26793 Sabre hash')
v=(CAND/'app/version.properties').read_text(); need('VERSION_NAME=0.9726793' in v and 'VERSION_BUILD=26793' in v,'version')
print('PASS 26793 version 0.9726793 / 26793')

bt=(BASE/S).read_text(); ct=(CAND/S).read_text()
def names(txt): return re.findall(r'^\s*(?:private\s+)?val\s+([A-Za-z_]\w*)\s*=\s*"""',txt,re.M)
bn,cn=names(bt),names(ct); need(bn==cn,'shader declaration universe')
for name in bn:
    if name not in {'merge','universalNormalMasterShortFusion26651'}:
        need(shader(BASE,name)==shader(CAND,name),f'protected Sabre shader changed: {name}')
print(f'PASS 26793 protected Sabre shader bodies unchanged: {len(bn)-2}; guide/covariance + Super Res direct/detail frozen')
merge,bmerge=shader(CAND,'merge'),shader(BASE,'merge'); short,bshort=shader(CAND,'universalNormalMasterShortFusion26651'),shader(BASE,'universalNormalMasterShortFusion26651')
need(merge.count('IRIS_26793_SAME_LOCATION_CFA_COLOR_DIFFERENCE_OWNER')==1,'main owner count')
need(short.count('IRIS_26793_SAME_LOCATION_CFA_COLOR_DIFFERENCE_OWNER')==1,'SHORT owner count')
need(segment(merge,'float neutralBoundedRawCode26792(','void correctedCfaScalar26792(')==segment(bmerge,'float neutralBoundedRawCode26792(','void correctedCfaScalar26792('),'neutral scalar owner changed')
need(segment(merge,'void correctedCfaScalar26792(','void fillCorrectedCfaNeighborhood26792(')==segment(bmerge,'void correctedCfaScalar26792(','void fillCorrectedCfaNeighborhood26792('),'continuous LCA scalar owner changed')
req=['int relativeCfaGroup26793(int sx, int sy)','void buildCalculationCfa26793(','float predictSameLocationGreen26793(','void sameLocationChroma26793(',
'float horizontalGreenWeight = kernelWeight(vec2(1.0, 0.0), covariance);','float verticalGreenWeight = kernelWeight(vec2(0.0, 1.0), covariance);',
'float difference = calculationCfa[sx][sy] - predictedGreen;','float legacyLuma26793 = dot(legacyRgb26793, vec3(0.25, 0.50, 0.25));',
'float correctedG26793 = legacyLuma26793 - 0.25 * (dR26793 + dB26793);','accumulatedIntensities = correctedRgb26793 * accumulatedWeights;']
for src,label in [(merge,'main'),(short,'SHORT')]:
    for tok in req: need(tok in src,f'{label} missing {tok}')
need('calculationCfa26793, weights, sourceValidity, type, covariance, 0,' in merge,'main call contract')
need('calculationCfa26793, validWeights, sourceValidity, type, covariance, 1,' in short,'SHORT call contract')
need(merge.index('sameLocationChroma26793(')<merge.index('float frameWeight = uUseFrameWeight != 0'),'main insertion not before frame weighting')
def uniforms(src): return set(re.findall(r'\buniform\s+(?:(?:highp|mediump|lowp)\s+)?[A-Za-z_]\w*\s+(u[A-Za-z0-9_]+)',src))
need(uniforms(merge)==uniforms(bmerge),'main uniform contract changed'); need(uniforms(short)==uniforms(bshort),'SHORT uniform contract changed')
print('PASS 26793 insertion point: full CFA/RBF geometry -> same-location chroma -> inherited temporal frame weighting; no new uniforms/buffers')
for rel in ['app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt','app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt','app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt','app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/assets/shaders/motionv2/gainmap.glsl']:
    need(sha(BASE/rel)==sha(CAND/rel),f'protected owner changed {rel}')
print('PASS 26793 VGN/residual/floor/Night routing/SDR/UHDR ownership byte-frozen')

# Permanent numerical regression model matching 26793 shader math.
def kw(dx,dy,cov): return 2**(-0.5*(dx*dx*cov[0]+dy*dy*cov[1]+2*dx*dy*cov[2]))+0.00005
def grp(x,y):
    if x==1 and y==1:return 3
    if x==1:return 1
    if y==1:return 2
    return 0
def sw(v,t):
    if t==0:return [v[0],v[1],v[2],v[3]]
    if t==1:return [v[1],v[0],v[3],v[2]]
    if t==2:return [v[2],v[3],v[0],v[1]]
    return [v[3],v[2],v[1],v[0]]
def model(calc,t,sub,cov):
    w=[[kw((x-1)+sub[0],(y-1)+sub[1],cov) for y in range(3)] for x in range(3)]
    vals=[0.0]*4; ws=[0.0]*4
    for x in range(3):
      for y in range(3):
        g=grp(x,y); vals[g]+=calc[x][y]*w[x][y]; ws[g]+=w[x][y]
    vals=sw(vals,t); ws=sw(ws,t); old=[vals[0]/ws[0],(vals[1]+vals[2])/(ws[1]+ws[2]),vals[3]/ws[3]]
    rg,bg=t,3-t; h,vv=kw(1,0,cov),kw(0,1,cov); sums={rg:[0.0,0.0],bg:[0.0,0.0]}
    for x in range(3):
      for y in range(3):
        g=grp(x,y)
        if g not in (rg,bg): continue
        num=den=0.0
        for dx,dy in ((-1,0),(1,0),(0,-1),(0,1)):
          qx,qy=x+dx,y+dy
          if not(0<=qx<3 and 0<=qy<3): continue
          qg=grp(qx,qy)
          if qg in (rg,bg): continue
          ww=h if dx else vv; num+=calc[qx][qy]*ww; den+=ww
        pred=num/den; sums[g][0]+=(calc[x][y]-pred)*w[x][y]; sums[g][1]+=w[x][y]
    dr=sums[rg][0]/sums[rg][1]; db=sums[bg][0]/sums[bg][1]; Y=.25*old[0]+.5*old[1]+.25*old[2]; G=Y-.25*(dr+db); return old,[G+dr,G,G+db]
random.seed(26793); mx=0.0
for _ in range(1000):
    t=random.randrange(4); sub=(random.uniform(-.5,.5),random.uniform(-.5,.5)); cov=(random.uniform(.2,5),random.uniform(.2,5),0.0); R,G,B=[random.uniform(.02,2) for _ in range(3)]; rg,bg=t,3-t
    calc=[[R if grp(x,y)==rg else B if grp(x,y)==bg else G for y in range(3)] for x in range(3)]; old,new=model(calc,t,sub,cov); mx=max(mx,max(abs(old[i]-new[i]) for i in range(3)))
need(mx<1e-12,f'uniform-color identity {mx}'); print(f'PASS 26793 uniform genuine-color identity maxerr={mx:.3e}')
for orientation,cov in [('vertical',(9.0,.35,0.0)),('horizontal',(.35,9.0,0.0))]:
    oc=[]; nc=[]; le=[]
    for t in range(4):
      for si in range(21):
        sub=(-.5+si/20,.17) if orientation=='vertical' else (.17,-.5+si/20); calc=[[.12 if ((x-1) if orientation=='vertical' else (y-1))<0 else 1.0 for y in range(3)] for x in range(3)]; old,new=model(calc,t,sub,cov)
        oc.append(abs(old[0]-old[1])+abs(old[2]-old[1])); nc.append(abs(new[0]-new[1])+abs(new[2]-new[1])); le.append(abs((.25*old[0]+.5*old[1]+.25*old[2])-(.25*new[0]+.5*new[1]+.25*new[2])))
    ratio=sum(nc)/sum(oc); need(ratio<.35,f'{orientation} neutral-edge ratio {ratio}'); need(max(le)<1e-12,f'{orientation} luma drift'); print(f'PASS 26793 {orientation} neutral-edge false-chroma ratio={ratio:.6f}; legacy luma exact')
print('PASS 26793 semantic/ownership/permanent-regression validation')
