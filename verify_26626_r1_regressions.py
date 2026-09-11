#!/usr/bin/env python3
from pathlib import Path
import re, sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26626_r1_regressions.py BASE CAND')
B=Path(sys.argv[1]); C=Path(sys.argv[2])
R='app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl'
J='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java'
S='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'
K='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'
r=(C/R).read_text(); j=(C/J).read_text(); k=(C/K).read_text()
# Permanent presentation regressions: exact 26625 baseline first; lower body and >1 HDR headroom fail closed.
for t in ['baseline=EXACT_26625_RECONSTRUCTION','IRIS_26626_SOURCE_PRESERVATION_MAX = 0.30f','IRIS_26626_SOURCE_PRESERVATION_MAX * adaptiveEnable * pressure']:
    if t not in j: raise SystemExit(f'FAIL presentation baseline regression {t}')
for t in ['smoothstep(0.65,0.72,sourceGuide)','1.0-smoothstep(0.98,1.05,sourceGuide)','allowed=min(allowed,0.20)','IRIS_26626_R0=4','IRIS_26626_R1=16','IRIS_26626_R2=32']:
    if t not in r: raise SystemExit(f'FAIL bounded source-structure regression {t}')
# Fail-closed material-boundary contract: both opposite sides required and curvature sign must support delta.
for t in ['min(ax0,ax1)/axMax','min(ay0,ay1)/ayMax','(cx*delta)>0.0','(cy*delta)>0.0']:
    if t not in r: raise SystemExit(f'FAIL one-sided/flat-boundary regression {t}')
# Super Res must consume the same final map; no alternate 26626 SR tone owner.
if 'basePipeline.mParameters.motionV2LocalToneLogMap' not in j or 'motionV2SuperResOutputEnabled' not in j:
    raise SystemExit('FAIL shared true2x appearance-map ownership')
if 'IRIS_26626_SUPER_RES_TONE_OWNER' in j: raise SystemExit('FAIL alternate SR tone owner added')
# Existing Sabre shader sources must remain exact and the three new shaders must be diagnostic only.
def extract_all(text):
    pat=re.compile(r'\bval\s+([A-Za-z_]\w*)\s*=\s*"""(.*?)"""\.trimIndent\(\)',re.S)
    out={}
    for n,raw in pat.findall(text):
        lines=raw.splitlines()
        if lines and not lines[0].strip(): lines=lines[1:]
        if lines and not lines[-1].strip(): lines=lines[:-1]
        non=[len(x)-len(x.lstrip()) for x in lines if x.strip()]; ind=min(non) if non else 0
        out[n]='\n'.join(x[ind:] if x.strip() else '' for x in lines)+'\n'
    return out
old=extract_all((B/S).read_text()); new=extract_all((C/S).read_text())
for name,src in old.items():
    if new.get(name)!=src: raise SystemExit(f'FAIL inherited SHORT/CFA/Sabre shader changed: {name}')
if sorted(set(new)-set(old))!=['shortAccumulatorDelta26626','shortAccumulatorProxy26626','shortComponentDiagnostics26626']:
    raise SystemExit('FAIL diagnostic shader set')
# Semantic contract must not overclaim eligibility as Resolve/output proof.
for t in ['commonAccumulatorInputChanged=','resolveEffective=NOT_DIRECTLY_MEASURED outputPreserved=DEVICE_IMAGE_REQUIRED']:
    if t not in k: raise SystemExit(f'FAIL semantic proof regression {t}')
# No preparation-only Actions success mechanism may be introduced by runtime source.
for forbidden in ['resolveEffective=true','outputPreserved=true','ADRC fallback','single-frame fallback']:
    if forbidden in k: raise SystemExit(f'FAIL forbidden semantic/runtime fallback {forbidden}')
print('PASS 26626 regressions: 26625 baseline/body/UHDR/SR protections intact; one-sided/flat source structure fail-closed; inherited SHORT/CFA/Sabre equations exact; accumulator proof remains non-Resolve telemetry')
