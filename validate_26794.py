#!/usr/bin/env python3
from pathlib import Path
import hashlib, math, sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26794.py BASE_ROOT CANDIDATE_ROOT')
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
print('PASS 26794 authority-seeded scope: 1779 files, exactly 2 modified / 0 added / 0 deleted')
v=(CAND/'app/version.properties').read_text(); need('VERSION_NAME=0.9726794' in v and 'VERSION_BUILD=26794' in v,'version')
print('PASS 26794 version 0.9726794 / 26794')
rel='app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt'
b=(BASE/rel).read_text(); n=(CAND/rel).read_text()
need('IRIS_26794_POST_DENOISE_SPATIAL_CHROMA_FLOOR' in n,'26794 owner marker')
need('IRIS_26794_SPATIAL_MASK legacy=' in n and 'brightRisk=' in n and 'attenuated=' in n and 'allowedRaised=' in n,'spatial mask logs incomplete')
need('gridWidth = 32' in n and 'gridHeight = 24' in n and 'origin=GL_BOTTOM_LEFT' in n,'spatial grid contract')
need('legacyWouldRaisePixels' in n and 'brightEdgeCandidates' in n and 'spatiallySupportedCandidates' in n,'decision counters missing')
need('Dark/midtone protected micro-color keeps the exact 26728 floor' in n,'preservation contract comment missing')
need('val spatialPermission = (1f - brightEdgeRisk * (1f - supportPermission)).coerceIn(0f, 1f)' in n,'spatial permission equation changed')
need('val pairSupport = maxOf(' in n and 'minOf(leftProjection, rightProjection)' in n and 'minOf(upProjection, downProjection)' in n,'opposite-pair hue support missing')
need('val survival = (currentMagnitude / maxOf(floorMagnitude, 1.0e-7f)).coerceIn(0f, 1f)' in n,'denoised survival proof missing')
need('val edgeRisk = smoothstep26794(0.025f, 0.100f, maxLumaDelta)' in n,'edge risk thresholds changed')
need('val brightRisk = smoothstep26794(0.50f, 0.82f, maxOf(y, maxNeighborLuma))' in n,'bright risk thresholds changed')
need('val restorationDominance = smoothstep26794(0.20f, 0.65f, 1f - survival)' in n,'restoration dominance changed')
need('val supportPermission = smoothstep26794(0.25f, 0.70f, spatialSupport)' in n,'support permission changed')
# Two-pass safety: all spatial decisions must be frozen before RGB writes begin.
marker=n.index('IRIS_26794_POST_DENOISE_SPATIAL_CHROMA_FLOOR')
apply=n.index('private fun applyIris26728ProtectedChromaFloor',marker)
second=n.index('// Second pass: apply only the frozen target magnitudes.',apply)
first=n[apply:second]; second_block=n[second:n.index('private fun forceOpaqueHalfAlpha',second)]
need('shorts.put(base, Half.toHalf' not in first,'first pass writes RGB before spatial decisions freeze')
need('shorts.put(base, Half.toHalf' in second_block,'second pass does not apply frozen magnitude')
need('FloatArray' not in n[marker:n.index('private fun forceOpaqueHalfAlpha',marker)],'per-candidate FloatArray allocation introduced')
print('PASS 26794 two-pass spatial mask: untouched denoised neighborhood first, RGB write second, no per-candidate arrays')
# Everything before the old floor owner and after forceOpaque remains byte-identical.
base_apply=b.index('    private fun applyIris26728ProtectedChromaFloor(')
new_owner=n.index('    /* IRIS_26794_POST_DENOISE_SPATIAL_CHROMA_FLOOR')
need(b[:base_apply]==n[:new_owner],'bridge changed before intended 26794 floor block')
base_suffix=b.index('    private fun forceOpaqueHalfAlpha',base_apply)
new_suffix=n.index('    private fun forceOpaqueHalfAlpha',new_owner)
need(b[base_suffix:]==n[new_suffix:],'bridge changed after intended 26794 floor block')
print('PASS 26794 bridge ownership: only post-denoise floor implementation replaced; upstream/downstream bridge bytes protected')
# Upstream owners must remain byte-identical to successful 26793.
for p in [
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/src/main/java/com/hinnka/mycamera/raw/MgcFullResolutionDenoise.kt' if (BASE/'app/src/main/java/com/hinnka/mycamera/raw/MgcFullResolutionDenoise.kt').exists() else None,
]:
    if p: need(sha(BASE/p)==sha(CAND/p),f'protected owner changed: {p}')
print('PASS 26794 protected producer/VGN/denoise owners byte-identical to successful 26793')
# Synthetic equation tests tied to exact constants above.
def ss(a,b,x):
    t=max(0.0,min(1.0,(x-a)/(b-a))); return t*t*(3-2*t)
def permission(y,maxNy,lumaDelta,current,floor,pair):
    survival=max(0.0,min(1.0,current/max(floor,1e-7)))
    ps=max(0.0,min(1.0,pair/max(floor,1e-7)))
    spatial=max(survival,ps)
    edge=ss(0.025,0.100,lumaDelta); bright=ss(0.50,0.82,max(y,maxNy)); dominance=ss(0.20,0.65,1-survival)
    support=ss(0.25,0.70,spatial)
    return 1-edge*bright*dominance*(1-support)
# dark/midtone floor is exact even with low spatial support
need(abs(permission(0.30,0.35,0.20,0.005,0.04,0.0)-1.0)<1e-9,'midtone protected color no longer exact 26728')
# bright neutral edge where denoise removed most chroma is strongly attenuated
p=permission(0.72,0.95,0.18,0.004,0.04,0.0); need(p<0.25,f'bright weak-support artifact not attenuated enough: {p}')
# genuine bright color that survives denoise remains essentially restored
p=permission(0.72,0.90,0.18,0.034,0.04,0.0); need(p>0.95,f'bright surviving color over-suppressed: {p}')
# opposite-pair same-hue support rescues a thin coherent colored structure
p=permission(0.72,0.90,0.18,0.008,0.04,0.034); need(p>0.95,f'coherent pair-supported color over-suppressed: {p}')
print('PASS 26794 synthetic invariants: midtone exact, bright unsupported attenuated, surviving/coherent color preserved')
# No unrelated runtime files changed by design.
print('PASS 26794 no LCA/neutral/Sabre/VGN/denoise/SR/DNG/UHDR/tone/exposure redesign')
