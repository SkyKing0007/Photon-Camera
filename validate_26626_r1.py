#!/usr/bin/env python3
from pathlib import Path
import difflib, hashlib, re, sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26626_r1.py BASE CAND')
B=Path(sys.argv[1]); C=Path(sys.argv[2])
CHANGED=[
'app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/version.properties',
]
PINS={
'app/src/main/assets/shaders/motionv2/local_laplacian_global_log_26621.glsl':'041b85efd6acdc7760a60b8628330647e59841f5e65f996bb39a141fc9dcbee2',
'app/src/main/assets/shaders/motionv2/local_laplacian_downsample_26621.glsl':'c8e5c0287bbe84a6e9b060466d7e0e72bcc685ee2441d12d58f244b424e21745',
'app/src/main/assets/shaders/motionv2/local_laplacian_accumulate_26621.glsl':'02889c3e74a45868aa08916bac157cb4913c0afe03a5ee56d417d11175f072cd',
'app/src/main/assets/shaders/motionv2/local_laplacian_reconstruct_26621.glsl':'ae3f320fb05c5e7c54937f6f6f3d831c0f3f177f48e908bacf940981da856a1d',
'app/src/main/assets/shaders/motionv2/render.glsl':'5df19f79d7aad14f8eec7f215f5d402302dac888776713fb29571b77a8b031f6',
}
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def universe(root):
    return {str(p.relative_to(root)):sha(p) for p in sorted((root/'app').rglob('*')) if p.is_file()}
b=universe(B); c=universe(C)
if len(b)!=1713 or len(c)!=1713: raise SystemExit(f'FAIL app universe count {len(b)} {len(c)}')
diff=sorted(k for k in set(b)|set(c) if b.get(k)!=c.get(k))
if diff!=sorted(CHANGED): raise SystemExit(f'FAIL runtime changed-file allowlist: {diff}')
for rel,h in PINS.items():
    if sha(C/rel)!=h: raise SystemExit(f'FAIL protected presentation owner changed: {rel}')
# Version must be the only version semantic change.
v=(C/'app/version.properties').read_text()
for t in ['VERSION_NAME=0.9726626','VERSION_BUILD=26626']:
    if t not in v: raise SystemExit(f'FAIL version token {t}')
# Java presentation owner is insertion-only: every successful-26625 line remains in order.
def ordered_subsequence(old,new):
    j=0
    for line in new:
        if j<len(old) and line==old[j]: j+=1
    return j==len(old)
render_rel=CHANGED[3]
if not ordered_subsequence((B/render_rel).read_text().splitlines(),(C/render_rel).read_text().splitlines()):
    raise SystemExit('FAIL MotionV2Render is not additive-only over successful 26625')
# Kotlin shader carrier: all pre-existing embedded shaders must be byte-identical; exactly 3 diagnostic shaders added.
def extract_all(text):
    pat=re.compile(r'\bval\s+([A-Za-z_]\w*)\s*=\s*"""(.*?)"""\.trimIndent\(\)',re.S)
    out={}
    for name,raw in pat.findall(text):
        lines=raw.splitlines()
        if lines and not lines[0].strip(): lines=lines[1:]
        if lines and not lines[-1].strip(): lines=lines[:-1]
        non=[len(x)-len(x.lstrip()) for x in lines if x.strip()]; ind=min(non) if non else 0
        out[name]='\n'.join(x[ind:] if x.strip() else '' for x in lines)+'\n'
    return out
sabre_rel=CHANGED[1]
old=extract_all((B/sabre_rel).read_text()); new=extract_all((C/sabre_rel).read_text())
added=sorted(set(new)-set(old)); removed=sorted(set(old)-set(new)); altered=sorted(k for k in old.keys()&new.keys() if old[k]!=new[k])
want=['shortAccumulatorDelta26626','shortAccumulatorProxy26626','shortComponentDiagnostics26626']
if added!=want or removed or altered: raise SystemExit(f'FAIL Sabre shader inheritance added={added} removed={removed} altered={altered}')
if len(old)!=45: raise SystemExit(f'FAIL expected 45 inherited Sabre shaders, got {len(old)}')
# Stacker changes are additive except the single data-class constructor expansion needed to carry read-only diagnostics.
stack_rel=CHANGED[2]
a=(B/stack_rel).read_text().splitlines(); z=(C/stack_rel).read_text().splitlines()
removed_lines=[]
for d in difflib.ndiff(a,z):
    if d.startswith('- '): removed_lines.append(d[2:])
expected_removed=['                current, effectiveFlow, seedCells, finalCells, fallbackTrustedCells, passes,']
if removed_lines!=expected_removed: raise SystemExit(f'FAIL unexpected deletion/modification in SpatialStacker: {removed_lines[:20]}')
stack=(C/stack_rel).read_text()
for token in [
'componentMembershipCells=', 'untrustedComponentCells=', 'hardBarrierFrontierCells=', 'openFrontierCells=',
'commonAccumulatorTargetProbeCells=', 'commonAccumulatorChangedProbeCells=', 'commonAccumulatorInputChanged=',
'resolveEffective=NOT_DIRECTLY_MEASURED outputPreserved=DEVICE_IMAGE_REQUIRED',
'IRIS_26626_SHORT_ACCUMULATOR_PROOF_SNAPSHOT', 'IRIS_26626_SHORT_COMPONENT_PROPAGATION_PROOF',
]:
    if token not in stack: raise SystemExit(f'FAIL SHORT proof token missing: {token}')
# Presentation contract: current 26625 remains baseline; source-domain preservation is bounded and fail-closed by measured source structure.
r=(C/CHANGED[0]).read_text(); j=(C/render_rel).read_text()
for token in [
'iris26626Mode==1','iris26626Mode==2','iris26626Mode==3','iris26626Mode==4','iris26626Mode==5',
'const int IRIS_26626_R0=4','const int IRIS_26626_R1=16','const int IRIS_26626_R2=32',
'float bx=axMax>0.003 ? min(ax0,ax1)/axMax : 0.0',
'float by=ayMax>0.003 ? min(ay0,ay1)/ayMax : 0.0',
'float sx=(cx*delta)>0.0 ? bx*abs(cx) : 0.0',
'float sy=(cy*delta)>0.0 ? by*abs(cy) : 0.0',
'allowed=min(allowed,0.20)',
'smoothstep(0.65,0.72,sourceGuide)',
'(1.0-smoothstep(0.98,1.05,sourceGuide))',
'clamp(iris26626PreservationStrength,0.0,0.30)',
'Output=current+upperGate*clamp(iris26626PreservationStrength,0.0,0.30)*correction',
'Output=referenceLog+irisRemapDelta(x,referenceLog)',
]:
    if token not in r: raise SystemExit(f'FAIL presentation token missing: {token}')
for token in [
'IRIS_26626_SOURCE_PRESERVATION_MAX = 0.30f',
'IRIS_26626_SOURCE_PRESERVATION_MAX * adaptiveEnable * pressure',
'baseline=EXACT_26625_RECONSTRUCTION',
'iris26626ApplyBoundedSourceDomainPreservation',
'iris26626PreservationStrength > 1.0e-7f',
'motionV2SuperResOutputEnabled',
]:
    if token not in j: raise SystemExit(f'FAIL Java presentation token missing: {token}')
# No new semantic scene detector, alternate UHDR/SR owner, or legacy local-contrast path.
for forbidden in ['ceilingDetector','shelfDetector','skyDetector','treeDetector','chandelierDetector','IRIS_26626_UHDR_OWNER','IRIS_26626_SUPER_RES_TONE_OWNER']:
    if forbidden in r or forbidden in j: raise SystemExit(f'FAIL forbidden scene/owner token {forbidden}')
print('PASS 26626 semantic/ownership/domain: exact 5-path delta; 26625 baseline preserved; bounded source-structure highlight preservation + read-only SHORT proof only')
print('PASS 26626 inheritance: 45 pre-existing Sabre shader strings byte-identical; exactly 3 diagnostics added; protected global tone/Local-Laplacian reduce-accumulate-reconstruct/render unchanged')
