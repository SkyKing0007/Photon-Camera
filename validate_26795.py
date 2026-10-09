#!/usr/bin/env python3
from pathlib import Path
import hashlib, math, sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26795.py BASE_ROOT CANDIDATE_ROOT')
BASE,CAND=map(Path,sys.argv[1:])
ALLOW={
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/version.properties',
}
def need(c,m):
    if not c: raise AssertionError(m)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def uni(root): return {p.relative_to(root).as_posix():sha(p) for p in (root/'app').rglob('*') if p.is_file()}
a,c=uni(BASE),uni(CAND)
need(len(a)==len(c)==1779,(len(a),len(c))); need(set(a)==set(c),'candidate universe changed')
mod={p for p in a if a[p]!=c[p]}; need(mod==ALLOW,f'changed allowlist mismatch {sorted(mod)}')
print('PASS 26795 authority-seeded scope: 1779 files, exactly 2 modified / 0 added / 0 deleted')
v=(CAND/'app/version.properties').read_text(); need('VERSION_NAME=0.9726795' in v and 'VERSION_BUILD=26795' in v,'version')
print('PASS 26795 version 0.9726795 / 26795')
rel='app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt'
b=(BASE/rel).read_text(); n=(CAND/rel).read_text()
need('IRIS_26795_SCENE_RELATIVE_BRIGHT_EDGE_CHROMA_VALIDITY' in n,'26795 owner marker')
need('histogramSamples=' in n and 'sceneP90=' in n and 'sceneP98=' in n and 'sceneP995=' in n,'scene-relative histogram proof missing')
for k in ('legacy=','sceneRisk=','externalSupport=','floorBlocked=','residualReduced=','allowedRaised='):
    need('IRIS_26795_SPATIAL_MASK '+k in n,f'spatial mask missing {k}')
need('gridWidth = 64' in n and 'gridHeight = 48' in n and 'origin=GL_BOTTOM_LEFT' in n,'64x48 spatial grid contract')
need('IRIS_26795_TOP_RISK' in n and 'externalSupportRatio=' in n and 'targetMagnitude=' in n,'bounded exact-coordinate proof missing')
need('val upperTailScore = smoothstep26795(upperTailStart, upperTailEnd, localPeakLuma)' in n,'scene-relative upper-tail score changed')
need('val relativeGradient = maxLumaDelta / maxOf(localPeakLuma, sceneP90, 0.02f)' in n,'relative-gradient normalization changed')
need('val gradientScore = smoothstep26795(0.08f, 0.30f, relativeGradient)' in n,'relative-gradient thresholds changed')
need('val correctionStrength = sceneRisk * unsupported' in n,'risk/support correction equation changed')
need('val externalSupportRatio = (externalMagnitude / supportReference).coerceIn(0f, 1f)' in n,'external support ratio missing')
need('fun sideDepth(p1: Float, p2: Float): Float = maxOf(minOf(p1, p2), 0.35f * p1)' in n,'two-pixel external depth support changed')
need('val survival =' not in n[n.index('IRIS_26795_SCENE_RELATIVE_BRIGHT_EDGE_CHROMA_VALIDITY'):n.index('private fun forceOpaqueHalfAlpha')], 'self-surviving chroma reintroduced as permission')
need('currentMagnitude * 0.08f' in n,'unsupported residual minimum changed')
# Two-pass safety: no RGB write before all classifications freeze.
marker=n.index('IRIS_26795_SCENE_RELATIVE_BRIGHT_EDGE_CHROMA_VALIDITY')
apply=n.index('private fun applyIris26728ProtectedChromaFloor',marker)
second=n.index('// Second pass: apply frozen up/down chroma targets;',apply)
first=n[apply:second]; second_block=n[second:n.index('private fun forceOpaqueHalfAlpha',second)]
need('shorts.put(base, Half.toHalf' not in first,'first pass writes RGB before decisions freeze')
need('shorts.put(base, Half.toHalf' in second_block,'second pass does not apply frozen target')
print('PASS 26795 two-pass spatial validity: untouched post-denoise classification first, chroma write second')
# Only the 26794 floor block is replaced; everything around it remains identical.
base_owner=b.index('    /* IRIS_26794_POST_DENOISE_SPATIAL_CHROMA_FLOOR')
new_owner=n.index('    /* IRIS_26795_SCENE_RELATIVE_BRIGHT_EDGE_CHROMA_VALIDITY')
need(b[:base_owner]==n[:new_owner],'bridge changed before intended 26795 owner block')
base_suffix=b.index('    private fun forceOpaqueHalfAlpha',base_owner)
new_suffix=n.index('    private fun forceOpaqueHalfAlpha',new_owner)
need(b[base_suffix:]==n[new_suffix:],'bridge changed after intended 26795 owner block')
print('PASS 26795 bridge ownership: only 26794 post-denoise floor block replaced; surrounding bridge bytes protected')
# Upstream owners must remain byte-identical to successful 26794.
for p in [
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/src/main/java/com/hinnka/mycamera/raw/MgcFullResolutionDenoise.kt' if (BASE/'app/src/main/java/com/hinnka/mycamera/raw/MgcFullResolutionDenoise.kt').exists() else None,
]:
    if p: need(sha(BASE/p)==sha(CAND/p),f'protected owner changed: {p}')
print('PASS 26795 Sabre/VGN/residual-denoise owners byte-identical to successful 26794')
# Synthetic equations tied to the exact constants above.
def ss(a,b,x):
    t=max(0.0,min(1.0,(x-a)/(b-a))); return t*t*(3-2*t)
def decision(p90,p98,local_peak,max_delta,current,floor,external):
    start=max(p90,0.01); end=min(1.0,max(p98,start+0.02))
    rel=max_delta/max(local_peak,p90,0.02)
    risk=ss(start,end,local_peak)*ss(0.08,0.30,rel)
    support_ref=max(floor,current,1e-7)
    ext_ratio=max(0.0,min(1.0,external/support_ref))
    ext_perm=ss(0.15,0.60,ext_ratio)
    strength=risk*(1-ext_perm)
    supported=min(current,max(external,current*0.08))
    residual=current+(supported-current)*strength
    floor_perm=1-strength
    legacy=max(current,floor)
    target=residual+max(legacy-residual,0)*floor_perm
    return risk,ext_perm,residual,target
# Midtone: below scene upper tail -> exact inherited floor.
r,e,res,t=decision(.30,.55,.25,.15,.010,.040,0.0); need(abs(t-.040)<1e-9 and abs(res-.010)<1e-9,f'midtone changed {(r,e,res,t)}')
# Bright unsupported: floor blocked and surviving residual strongly reduced.
r,e,res,t=decision(.08,.18,.35,.18,.012,.050,0.0); need(r>.95 and e<.01 and t<.004,f'bright unsupported not removed {(r,e,res,t)}')
# Bright coherent material: two-pixel external support preserves old floor.
r,e,res,t=decision(.08,.18,.35,.18,.020,.050,.050); need(e>.99 and abs(t-.050)<1e-6,f'externally supported real color not preserved {(r,e,res,t)}')
# No candidate self-survival term exists: same current/floor with zero external evidence must remain unsupported.
r,e,res,t=decision(.08,.18,.35,.18,.045,.050,0.0); need(e<.01 and t<.010,f'self-survival still rescues candidate {(r,e,res,t)}')
# Chroma scaling around Y preserves weighted luma exactly.
R,G,B=.62,.50,.38; Y=.25*R+.5*G+.25*B; cr,cg,cb=R-Y,G-Y,B-Y
for scale in (0.08,.35,1.7):
    rr,gg,bb=Y+cr*scale,Y+cg*scale,Y+cb*scale
    need(abs((.25*rr+.5*gg+.25*bb)-Y)<1e-12,'luma invariance failed')
print('PASS 26795 synthetic invariants: midtone exact; unsupported bright-edge floor blocked/residual reduced; external material support preserved; luma invariant')
print('PASS 26795 no LCA/neutral/Sabre/VGN/denoise/SR/DNG/UHDR/tone/exposure redesign')
