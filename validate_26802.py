#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26802.py BASE_ROOT CANDIDATE_ROOT')
BASE,CAND=map(Path,sys.argv[1:])
MOD={
'app/src/main/assets/shaders/motionv2/false_color_classify_26800.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/version.properties'}
def need(c,m):
    if not c: raise AssertionError(m)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def uni(r): return {p.relative_to(r).as_posix():sha(p) for p in (r/'app').rglob('*') if p.is_file()}
a,c=uni(BASE),uni(CAND)
need(len(a)==1782 and len(c)==1782,(len(a),len(c)))
need(set(a)==set(c),'file universe changed')
mods={p for p in a if a[p]!=c[p]}
need(mods==MOD,f'modified allowlist mismatch {sorted(mods)}')
print('PASS 26802 authority-seeded scope: 1782 -> 1782, exactly 3 modified / 0 added / 0 deleted')
v=(CAND/'app/version.properties').read_text()
need('VERSION_NAME=0.9726802' in v and 'VERSION_BUILD=26802' in v,'version')
print('PASS 26802 version 0.9726802 / 26802')

mv='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java'
cls='app/src/main/assets/shaders/motionv2/false_color_classify_26800.glsl'
j=(CAND/mv).read_text(); bj=(BASE/mv).read_text(); s=(CAND/cls).read_text(); bs=(BASE/cls).read_text()
# Preserve successful 26801 buffer ownership and 26800/26799 architecture.
need('iris26798Stats = new GLBuffer(12' in j and 'iris26798Stats.uploadBuffer(new int[12], 12);' in j,'26798 12-counter allocation changed')
need('iris26799Stats = new GLBuffer(28' in j and 'iris26799Stats.uploadBuffer(new int[28], 28);' in j,'26799/26800 28-counter allocation changed')
b98=j.index('if (basePipeline.mParameters.motionV2Active && iris26798Stats != null) {', j.index('glMemoryBarrier'))
e98=j.index('if (basePipeline.mParameters.motionV2Active && iris26799Stats != null) {',b98)
blk98=j[b98:e98]
idx98=[int(x) for x in re.findall(r'stats\[(\d+)\]',blk98)]
need(idx98 and max(idx98)<=11,'26798 telemetry ownership regression')
need('stats.length >= 12' in blk98,'26798 runtime guard missing')
b99=e98; e99=j.index('        } finally {',b99); blk99=j[b99:e99]
idx99=[int(x) for x in re.findall(r'stats\[(\d+)\]',blk99)]
need(idx99 and max(idx99)<=27,'26799 telemetry exceeds 28-entry owner')
need('stats.length >= 28' in blk99,'26799 runtime guard missing')
need('IRIS_26801_TELEMETRY_BUFFER_OWNERSHIP_REPAIR' in blk99,'26801 telemetry repair missing')
need('IRIS_26802_NEUTRAL_PARENT_EDGE_FRINGE_DECISIONS' in blk99,'26802 telemetry log missing')
need('neutralParentFringeSeed=" + stats[19]' in blk99,'26802 counter 19 not read from 28-entry owner')
need('IRIS_26800_HIGH_CHROMA_FALSE_COLOR_ADMISSION_OWNER' not in j,'stale 26800 runtime owner still active')
need(j.count('IRIS_26802_NEUTRAL_PARENT_EDGE_FRINGE_OWNER')==1,'26802 runtime owner marker count')
for marker in ('useAssetProgram("motionv2/false_color_classify_26800")','useAssetProgram("motionv2/false_color_propagate_26799")','IRIS_26799_PROPAGATION_ITERATIONS = 8'):
    need(marker in j,f'inherited false-color architecture missing: {marker}')
print('PASS 26802 Java ownership: exact 26801 buffers + 26799 8-pass propagation retained; counter 19 owned by 28-entry SSBO')

# New classifier is narrow, hue-independent and does not alter correction strength.
for marker in ('IRIS_26802_NEUTRAL_PARENT_EDGE_FRINGE_ADMISSION','IRIS_26802_ACHROMATIC_CORE_EDGE_NORMAL_PROOF','IRIS_26802_NARROW_OVERRIDE'):
    need(s.count(marker)==1,f'{marker} count')
need('atomicAdd(iris26799Counters[19],1u);' in s,'26802 admission telemetry missing')
need('if(materialSupport>0.72&&!neutralParentFringeOverride)' in s,'strict material threshold weakened rather than narrowly overridden')
need('float brightParentNeutral=1.0-smoothstep(0.050,0.145,brightNearChroma);' in s,'achromatic parent proof missing')
need('float darkHueAbsent=1.0-smoothstep(0.22,0.52,darkOuterSame/max(mag,1.0e-6));' in s,'opposite-material persistence veto missing')
need('float singleHueSeed=max(max(regularSingleHueSeed,highSingleHueSeed),neutralParentFringeSeed);' in s,'26802 seed not routed into existing propagation')
# Exact inherited thresholds/codes from 26800 remain.
for token in ('float highChroma=smoothstep(0.26,0.38,mag);','float weak=smoothstep(0.07,0.24,weakStrength);',
              'float highWeak=smoothstep(0.10,0.34,highStrength);','if(phaseSeed>1.0e-5||highPlateauSeed>1.0e-5){Output=1.0;return;}',
              'if(singleHueSeed>1.0e-5){Output=0.85;return;}','if(max(weak,highWeak)>1.0e-5){Output=0.55;return;}','if(plateau>1.0e-5){Output=0.40;return;}'):
    need(token in s,f'26800 inherited classifier token changed: {token}')
need('IRIS_26802_NEUTRAL_PARENT_EDGE_FRINGE_ADMISSION' not in bs,'26801 authority already contains 26802 marker')
need('if(materialSupport>0.72){' in bs,'26801 strict material fixture missing')
print('PASS 26802 classifier semantics: hue-independent neutral-parent edge-normal override only; 26800 admissions and codes retained')

# Correction, propagation, UI, cleanup, UHDR/DNG/native/vendor and all other runtime files must remain byte-identical.
for rel in [
'app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/assets/shaders/motionv2/false_color_classify_26799.glsl',
'app/src/main/assets/shaders/motionv2/false_color_propagate_26799.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java']:
    need(sha(BASE/rel)==sha(CAND/rel),f'frozen successful behavior changed: {rel}')
for rel in a:
    if rel in MOD: continue
    need(a[rel]==c[rel],f'unexpected protected change {rel}')
print('PASS 26802 frozen behavior: render correction strength, 26799 propagation, 26801 cleanup/UI, Sabre/VGN/tone/UHDR/DNG/SR/native/vendor byte-invariant')

# Permanent regression fixtures.
need('IRIS_26801_TELEMETRY_BUFFER_OWNERSHIP_REPAIR' in bj,'26801 telemetry authority missing')
need('IRIS_26802_NEUTRAL_PARENT_EDGE_FRINGE_OWNER' not in bj,'26801 fixture contaminated by 26802 owner')
need('atomicAdd(iris26799Counters[19],1u);' not in bs,'26801 classifier fixture already uses 26802 counter')
print('PASS 26802 regressions: successful 26801 remains exact prior fixture; new admission cannot silently pre-exist')
