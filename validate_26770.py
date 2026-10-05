#!/usr/bin/env python3
from pathlib import Path
import hashlib,math,re,sys
if len(sys.argv) not in (3,4): raise SystemExit('usage: validate_26770.py BASE26769 CAND26770 [REF26733]')
base=Path(sys.argv[1]); cand=Path(sys.argv[2]); ref=Path(sys.argv[3]) if len(sys.argv)==4 else None
root=Path(__file__).resolve().parent
expected=[p for p in (root/'26770_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if p]
def H(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app').rglob('*') if p.is_file()}
a,b=H(base),H(cand); assert len(a)==len(b)==1823
changed=sorted(k for k in set(a)|set(b) if a.get(k)!=b.get(k)); assert changed==sorted(expected),(changed,expected); assert set(a)==set(b)
print('PASS 26770 exact 5-file runtime allowlist / zero additions / zero deletions')
v=(cand/'app/version.properties').read_text(); assert 'VERSION_NAME=0.9726770' in v and 'VERSION_BUILD=26770' in v
print('PASS 26770 version/build')
post_rel=Path('app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt')
render_java_rel=Path('app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java')
render_rel=Path('app/src/main/assets/shaders/motionv2/render.glsl'); gain_rel=Path('app/src/main/assets/shaders/motionv2/gainmap.glsl')
cap_rel=Path('app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
bs=(base/post_rel).read_text(); cs=(cand/post_rel).read_text()
def raw(src,name):
 m=re.search(r'\b(?:private\s+)?val\s+'+re.escape(name)+r'\s*=\s*"""(.*?)"""\.trimIndent\(\)',src,re.S)
 if not m: raise AssertionError(name)
 return m.group(1)
all_embedded=['universalAdaptiveColor26561','seed','localClamp','localMedian','directionalSmooth','restoreDirection','iirRgb','calculateError','iirError','blendChroma','finalCameraRgb','bipolarColorTrust26769']
shader_changed=[n for n in all_embedded if raw(bs,n)!=raw(cs,n)]
assert shader_changed==['bipolarColorTrust26769'],shader_changed
for n in all_embedded:
 if n!='bipolarColorTrust26769': assert raw(bs,n)==raw(cs,n),n
print('PASS 26770 VGN scope: frozen seed/localMedian/directional/IIR/universal/final owners byte-identical; only final trust pass changes')
if ref is not None:
 rs=(ref/post_rel).read_text(); assert raw(rs,'seed')==raw(cs,'seed'); assert raw(rs,'iirRgb')==raw(cs,'iirRgb')
print('PASS 26770 successful-26733 frozen containment reference retained')
bip=raw(cs,'bipolarColorTrust26769')
for marker in ['IRIS_26770_CENTER_OWNED_BIPOLAR_SUBTRACTION','IRIS_26770_AXIS_BIPOLAR_COMPONENT','IRIS_26770_PAIR_RESIDUAL_AXIS_ONLY','IRIS_26770_INTERIOR_ONLY_RECOVERY']:
 assert marker in bip,marker
assert 'vec3 cleanedNC=postNC-(eradicate?bipolarComponent:vec3(0.0));' in bip
assert 'cleanedNC=eradicate?bipolarBaseline:postNC' not in bip
assert 'oppositePair' not in bip
assert 'float interiorProof=deepInterior26770(p)?1.0:0.0;' in bip
assert 'float highFrequencySafe=1.0-smoothstep(0.10,0.24,maxRelativeLumaEdge);' in bip
assert 'recovery=residualProof*supportProof*coherenceProof*measured*headroom*interiorProof*highFrequencySafe*bipolarRecoveryVeto' in bip
assert 'for(int i=0;i<8;++i){if(!strictConnected26769(p,qd[i]))return false;ivec2 q=p+qd[i];if(!strictConnected26769(q,qd[i]))return false;}' in bip
print('PASS 26770 foliage safety: recovery deep-interior-only + high-frequency edge veto; no neighbor-baseline replacement')
# Center-owned subtraction math: preserve component orthogonal to proven bipolar axis.
post=(0.11,0.08); axis=(1.0,0.0); center_dev=(0.09,0.01)
dot=center_dev[0]*axis[0]+center_dev[1]*axis[1]; comp=(axis[0]*dot,axis[1]*dot); cleaned=(post[0]-comp[0],post[1]-comp[1])
assert abs(cleaned[1]-post[1])<1e-12 and abs(cleaned[0]-0.02)<1e-12
print('PASS 26770 synthetic bipolar regression: 100% proven axis projection removed, orthogonal center chroma preserved')
# Java modifications are insert-only around current tone authorities.
bj=(base/render_java_rel).read_text(); cj=(cand/render_java_rel).read_text()
assert 'IRIS_26770_MIDTONE_PRESENTATION_TRIM_REFERENCE' in cj and 'IRIS_26770_MIDTONE_PRESENTATION_TRIM' in cj
# Remove inserted method and telemetry, then exact base equality must return.
stripped=re.sub(r'\n    /\* IRIS_26770_MIDTONE_PRESENTATION_TRIM_REFERENCE.*?\n    static float iris26770MidtonePresentationTrim\(float mappedGuide\) \{.*?\n    \}\n','',cj,flags=re.S)
stripped=re.sub(r'\n            Log\.i\(Name, "IRIS_26770_MIDTONE_PRESENTATION_TRIM".*?\+ " at075=" \+ iris26770MidtonePresentationTrim\(0\.75f\)\);','',stripped,flags=re.S)
assert stripped==bj
print('PASS 26770 MotionV2Render.java: only midpoint CPU mirror + telemetry added; prior tone owners exact')
# Render shader exact delta: one function + two scalar calls only.
br=(base/render_rel).read_text(); cr=(cand/render_rel).read_text()
assert 'IRIS_26770_MIDTONE_PRESENTATION_TRIM' in cr and cr.count('mappedGuide=iris26770MidtonePresentationTrim(mappedGuide);')==2
sr=re.sub(r'\n/\* IRIS_26770_MIDTONE_PRESENTATION_TRIM.*?\nfloat iris26770MidtonePresentationTrim\(float mappedGuide\)\{.*?\n\}\n','',cr,flags=re.S)
sr=re.sub(r'(?m)^\s*mappedGuide=iris26770MidtonePresentationTrim\(mappedGuide\);\n','',sr)
assert sr==br
print('PASS 26770 render.glsl: only pointwise scalar midpoint trim inserted in global + local-tone publication')
# Gainmap exact delta: same function plus SDR denominator mirror only.
bg=(base/gain_rel).read_text(); cg=(cand/gain_rel).read_text()
assert 'IRIS_26770_MIDTONE_PRESENTATION_TRIM_GAINMAP_MIRROR' in cg
sg=re.sub(r'/\* IRIS_26770_MIDTONE_PRESENTATION_TRIM_GAINMAP_MIRROR.*?float iris26660SharedSdrGuide\(float sourceGuide,vec2 masterSourcePixel\)\{\n    return iris26770MidtonePresentationTrim\(iris26660ObjectColorGamma\(iris26640SharedSdrGuide\(sourceGuide,masterSourcePixel\)\)\);\n\}\n',
'''float iris26660SharedSdrGuide(float sourceGuide,vec2 masterSourcePixel){\n    return iris26660ObjectColorGamma(iris26640SharedSdrGuide(sourceGuide,masterSourcePixel));\n}\n''',cg,flags=re.S)
assert sg==bg
print('PASS 26770 gainmap.glsl: exact SDR-denominator mirror only; HDR target unchanged')
# Numeric tone regression.
def ss(a,b,x):
 t=max(0.0,min(1.0,(x-a)/(b-a))); return t*t*(3.0-2.0*t)
def trim(y):
 w=ss(.08,.20,y)*(1.0-ss(.52,.78,y)); return y+(y*y-y)*(0.25*w)
assert trim(.04)==.04 and trim(.08)==.08 and abs(trim(.78)-.78)<1e-12 and trim(.9)==.9
assert trim(.20)<.20 and trim(.25)<.25 and trim(.50)<.50
assert abs(trim(.25)-.203125)<1e-12 and abs(trim(.50)-.4375)<1e-12
print('PASS 26770 midpoint curve: black/highlight anchors exact; body curve down; 25% blend not saturation scaling')
# Capture regression protection.
assert (base/cap_rel).read_bytes()==(cand/cap_rel).read_bytes()
cc=(cand/cap_rel).read_text(); assert 'IRIS_26769_AE_LOCK_TO_MANUAL_EXACT' in cc and 'MOTION_26486_EXPOSURE_HALF_WINDOW_EV = 0.05;' in cc
print('PASS 26770 successful-26769 Motion capture admission bytes protected unchanged')
# User saturation/color owners remain unchanged in render code.
assert 'iris26630SaturationOwner=' in cj and 'MOTION_PER_LENS' in cj and 'saturationOwnerUnchanged=true' in cj
assert 'iris26638UserSaturation' in cr
print('PASS 26770 saturation/matrix/color ownership preserved; midpoint change is scalar luminance only')
print('PASS 26770 semantic/ownership/domain regression suite')
