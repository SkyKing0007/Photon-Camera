#!/usr/bin/env python3
"""Exact 26965 app-source allowlist, owners, and frozen mode routing."""
import pathlib,hashlib,re,sys
R=pathlib.Path(__file__).resolve().parent;P=R if '--live' in sys.argv else R/'handoff_payload_26967'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def manifest(name):
 d={}
 for l in (R/name).read_text().splitlines():
  h,p=l.split('  ',1);assert re.fullmatch('[0-9a-f]{64}',h) and p not in d;d[p]=h
 return d
b=manifest('26967_BASE_26965_FULL_APP.sha256');c=manifest('26967_EXPECTED_FULL_APP.sha256');protected=manifest('26967_PROTECTED_SOURCE.sha256')
changed=set((R/'26967_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines())
expected=set('''app/src/main/assets/shaders/motionv2/gainmap.glsl
app/src/main/assets/shaders/motionv2/render.glsl
app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java
app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/Iris26876BGpuFinalRenderer.java
app/version.properties'''.splitlines())
assert len(b)==len(c)==2055 and len(protected)==2050 and changed==expected=={p for p in b if b[p]!=c[p]}
assert set(b)==set(c) and protected=={p:h for p,h in b.items() if p not in expected}
assert (R/'26967_ADDED_RUNTIME_PATHS.txt').read_text()==(R/'26967_DELETED_RUNTIME_PATHS.txt').read_text()==''
assert all(sha(P/p)==c[p] for p in expected)
if '--live' in sys.argv:
 from importlib.machinery import SourceFileLoader
 m=SourceFileLoader('b26967',str(R/'build_26967_incremental.py')).load_module();assert m.scan(R)==c
S=(P/'app/src/main/assets/shaders/motionv2/render.glsl').read_text()
G=(P/'app/src/main/assets/shaders/motionv2/gainmap.glsl').read_text()
J=(P/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text()
N=(P/'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/Iris26876BGpuFinalRenderer.java').read_text()
V=(P/'app/version.properties').read_text()
assert 'VERSION_BUILD=26967' in V and 'VERSION_NAME=0.9726967' in V
assert S.count('uniform int iris26967AOption2Enabled;')==1 and S.count('iris26967Option2Encoded(')==4
assert 'Output=iris26967EncodedSdr;' in S
assert 'iris26966AShadowFalseColor' not in S and 'IRIS_26966_A_RAWLENS' not in S
assert J.count('glProg.setVar("iris26967AOption2Enabled"')==1
assert J.count('glProg.setVar("iris26967PhotoHighlightsOnly"')==1
assert G.count('uniform int iris26967PhotoHighlightsOnly;')==1
assert G.count('if(iris26967PhotoHighlightsOnly!=0)')==1
assert 'float hdrIntentY=sdr+matchedIntentDelta;' in G
assert 'float genuineBright=smoothstep(0.32,0.65,sourceGuide);' in G
assert 'float hdrBright=smoothstep(0.62,0.96,linearTargetY);' in G
assert 'ratio=1.0+(ratio-1.0)*highlightOnly;' in G
assert 'iris26967Option2Encoded' not in G
assert 'return selectedPhotoBOff ? 0.23f' in J
assert 'iris26936SaturationScale = iris26936BOffSaturation ? 1.00f' in J
assert 'iris26936BOffSaturation ? 1.00f' in N and 'iris26932BOn ? 1.00f' in N
assert 'float toe=x*(1.0-0.495*toeGate);' in S and 'float toe=x*(1.0-0.495*toeGate);' in G
assert 'float mid=0.25*(x-0.230)*clamp(midLow*midHigh,0.0,1.0);' in S and 'float mid=0.25*(x-0.230)*clamp(midLow*midHigh,0.0,1.0);' in G
A=J[J.index('final boolean iris26967PhotoAOption2'):J.index('glProg.setVar("iris26967AOption2Enabled"')]
U=J[J.index('final boolean iris26967PhotoHighlightsOnly'):J.index('glProg.setVar("iris26967PhotoHighlightsOnly"')]
for n in ('.motionV2Active','!basePipeline.mParameters.iris26906ExperimentBSelected','!basePipeline.mParameters.irisNightActive','!basePipeline.mParameters.iris26903NightB'):assert n in A
for n in ('.motionV2Active','!basePipeline.mParameters.iris26906ExperimentBSelected','!basePipeline.mParameters.motionV2SuperResOutputEnabled','!basePipeline.mParameters.irisNightActive','!basePipeline.mParameters.iris26903NightB'):assert n in U
assert (R/'26965_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml').is_file()
assert all(p not in changed for p in b if '/cpp/' in p or '/spektra/' in p.lower() or 'night' in p.lower() or 'GlesMgcRawSpatialStacker' in p or 'PhotonMotionMgc1271Bridge' in p)
print('PASS 26967 source from 26965 2055 files, 5 changed, 2050 protected; photo A Option2, B OFF 1.00 toe 30 mid 25, highlight UHDR')
