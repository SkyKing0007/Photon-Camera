#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26803.py BASE_ROOT CANDIDATE_ROOT')
BASE,CAND=map(Path,sys.argv[1:])
MOD={
'app/src/main/assets/shaders/motionv2/false_color_classify_26800.glsl',
'app/src/main/assets/shaders/motionv2/false_color_propagate_26799.glsl',
'app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/version.properties'}
H26800_CLASSIFIER='0756829d5d3d0de9cabe763fdbd694d7c0c0d7e7b9fec24f06b180263ff7c581'
def need(c,m):
    if not c: raise AssertionError(m)
def sha_bytes(b): return hashlib.sha256(b).hexdigest()
def sha(p): return sha_bytes(p.read_bytes())
def uni(r): return {p.relative_to(r).as_posix():sha(p) for p in (r/'app').rglob('*') if p.is_file()}
a,c=uni(BASE),uni(CAND)
need(len(a)==1782 and len(c)==1782,(len(a),len(c)))
need(set(a)==set(c),'file universe changed')
mods={p for p in a if a[p]!=c[p]}
need(mods==MOD,f'modified allowlist mismatch {sorted(mods)}')
print('PASS 26803 authority-seeded scope: 1782 -> 1782, exactly 5 modified / 0 added / 0 deleted')
v=(CAND/'app/version.properties').read_text()
need('VERSION_NAME=0.9726803' in v and 'VERSION_BUILD=26803' in v,'version')
print('PASS 26803 version 0.9726803 / 26803')

cls='app/src/main/assets/shaders/motionv2/false_color_classify_26800.glsl'
prop='app/src/main/assets/shaders/motionv2/false_color_propagate_26799.glsl'
render='app/src/main/assets/shaders/motionv2/render.glsl'
mv='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java'
s=(CAND/cls).read_text(); bs=(BASE/cls).read_text()
p=(CAND/prop).read_text(); bp=(BASE/prop).read_text()
r=(CAND/render).read_text(); br=(BASE/render).read_text()
j=(CAND/mv).read_text(); bj=(BASE/mv).read_text()

# Exact 26802 failing-condition fixtures must exist in authority and be removed/repaired in candidate.
need('neutralParentFringeOverride=neutralParentFringeSeed>1.0e-5' in bs,'26802 soft-nonzero override fixture missing')
need('float singleHueSeed=max(max(regularSingleHueSeed,highSingleHueSeed),neutralParentFringeSeed);' in bs,'26802 seed-merger fixture missing')
need('vec3 target=iris26799RobustMaterialTarget(sourcePixel,y,guide,centerChroma);' in br,'26802 isotropic-only correction fixture missing')
need('Output=connected?1.0:0.0;' in bp,'26802 connected-mask code-collapse fixture missing')
need('neutralParentFringeOverride=neutralParentFringeSeed>1.0e-5' not in s,'26802 soft-nonzero override survived')
need('IRIS_26802_NEUTRAL_PARENT_EDGE_FRINGE_OWNER' not in j,'stale 26802 runtime owner survived')
print('PASS 26803 permanent regression fixtures: exact 26802 over-admission + near-parent + isotropic-target failure removed')

# Strong direct classifier contract: no soft threshold bypass; far 4..6px parent; isolated-neon subcase; hue-independent code 0.92.
for marker in ('IRIS_26803_STRONG_NEUTRAL_PARENT_FRINGE_REPAIR','IRIS_26803_FAR_ACHROMATIC_PARENT_STRONG_PROOF'):
    need(s.count(marker)==1,f'{marker} count')
for token in (
    'float npBrightParentChroma=mix(negAreaChroma,posAreaChroma,npBrightSideIsPos);',
    'float npFarSameRatio=max(posAreaSupport,negAreaSupport)/max(mag,1.0e-6);',
    'bool npLineFringe=npParentNeutral>0.78&&npParentBright>0.68&&npFarHueAbsent>0.72',
    'bool npNeonIsland=highChroma>0.70&&npParentNeutral>0.84&&npParentBright>0.78',
    'bool neutralParentDirectSeed=npLineFringe||npNeonIsland;',
    'atomicAdd(iris26799Counters[19],1u);',
    'Output=0.92;'):
    need(token in s,f'26803 classifier contract missing: {token}')
need(s.index('if(neutralParentDirectSeed){') < s.index('/* IRIS_26800_STRICT_MATERIAL_PROOF'),'direct proof must precede exact 26800 material gate')
need('if(materialSupport>0.72){' in s,'exact 26800 strict material gate not restored')
# Canonicalize away only 26803 additions: fallback must hash exactly to successful 26800 classifier.
sc=s
a0=sc.index('/* IRIS_26803_STRONG_NEUTRAL_PARENT_FRINGE_REPAIR')
b0=sc.index(' * Extends the successful 26799 mask admission',a0)
sc=sc[:a0]+'/* IRIS_26800_HIGH_CHROMA_BRIGHT_FRINGE_CLASSIFIER\n'+sc[b0:]
a0=sc.index('    /* IRIS_26803_FAR_ACHROMATIC_PARENT_STRONG_PROOF')
b0=sc.index('    /* IRIS_26800_STRICT_MATERIAL_PROOF',a0)
sc=sc[:a0]+sc[b0:]
need(sha_bytes(sc.encode())==H26800_CLASSIFIER,'26800 fallback not byte-exact after removing 26803 direct proof')
print('PASS 26803 classifier: strong far-parent/direct-neon proof only; absent proof canonicalizes byte-exact to successful 26800')

# Propagation: boolean connectivity expression remains exact; only direct 0.92 code is preserved.
need('bool connected=seed||(candidate&&(already||neighbor));' in p,'26799 boolean connectivity changed')
need('bool neutralParentDirect=cls>=0.90&&cls<=0.94;' in p,'0.92 class preservation missing')
need('Output=connected?(neutralParentDirect?0.92:1.0):0.0;' in p,'direct class code not preserved')
pc=p
a0=pc.index('    /* IRIS_26803_PRESERVE_NEUTRAL_PARENT_DIRECT_CODE')
b0=pc.index('    float prev=',a0)
pc=pc[:a0]+pc[b0:]
pc=pc.replace('    Output=connected?(neutralParentDirect?0.92:1.0):0.0;\n','    Output=connected?1.0:0.0;\n')
need(sha_bytes(pc.encode())==sha(BASE/prop),'propagation changed beyond 0.92 code preservation')
print('PASS 26803 propagation: exact 26799 boolean topology/8-pass connectivity; only direct code 0.92 survives')

# Render: only direct code gets far edge-normal parent target; every other connected pixel keeps exact 26799 target.
for marker in ('IRIS_26803_NEUTRAL_PARENT_CORRECTION_TARGET','iris26803NeutralParentTarget'):
    need(marker in r,f'render parent target missing: {marker}')
need('bool iris26803NeutralParentDirect=connected>=0.90&&connected<=0.94;' in r,'render direct-code gate missing')
need('?iris26803NeutralParentTarget(sourcePixel,y,guide,centerChroma)' in r,'direct parent target branch missing')
need(':iris26799RobustMaterialTarget(sourcePixel,y,guide,centerChroma);' in r,'legacy 26799 fallback target missing')
need(r.index('linearSrgb=iris26799ApplyConnectedCorrection') < r.index('linearSrgb=mapExtendedLinearHeadroom(linearSrgb);'),'correction moved after presentation tone')
rc=r
a0=rc.index('/* IRIS_26803_NEUTRAL_PARENT_CORRECTION_TARGET')
b0=rc.index('void iris26799TelemetryMagnitude',a0)
rc=rc[:a0]+rc[b0:]
new='''    bool iris26803NeutralParentDirect=connected>=0.90&&connected<=0.94;\n    vec3 target=iris26803NeutralParentDirect\n            ?iris26803NeutralParentTarget(sourcePixel,y,guide,centerChroma)\n            :iris26799RobustMaterialTarget(sourcePixel,y,guide,centerChroma);\n'''
rc=rc.replace(new,'    vec3 target=iris26799RobustMaterialTarget(sourcePixel,y,guide,centerChroma);\n')
need(sha_bytes(rc.encode())==sha(BASE/render),'render changed beyond direct neutral-parent target')
print('PASS 26803 render: direct proven fringe -> far neutral parent; all legacy connected correction byte-exact 26799')

# Java: ownership/telemetry strings only; buffers, texture counts, lifecycle, bindings remain 26802 exact.
need(j.count('IRIS_26803_STRICT_NEUTRAL_PARENT_FRINGE_REPAIR_OWNER')==1,'26803 runtime owner marker count')
need(j.count('IRIS_26803_STRICT_NEUTRAL_PARENT_FRINGE_DECISIONS')==1,'26803 telemetry marker count')
need('strongDirectNeutralParentSeed=" + stats[19]' in j,'counter 19 read missing')
for token in ('iris26798Stats = new GLBuffer(12','iris26799Stats = new GLBuffer(28','IRIS_26799_PROPAGATION_ITERATIONS = 8',
              'peakMasks=3 renderRetainedMasks=1','useAssetProgram("motionv2/false_color_classify_26800")','useAssetProgram("motionv2/false_color_propagate_26799")'):
    need(token in j,f'Java frozen architecture changed: {token}')
# Replace the two new log blocks with base blocks and prove byte identity.
jc=j
cs=jc.index('            Log.i(Name, "IRIS_26803_STRICT_NEUTRAL_PARENT_FRINGE_REPAIR_OWNER"')
ce=jc.index('            Log.i(Name, "IRIS_26799_MULTI_PASS_CONNECTED_FALSE_COLOR_OWNER"',cs)
bs0=bj.index('            Log.i(Name, "IRIS_26802_NEUTRAL_PARENT_EDGE_FRINGE_OWNER"')
be0=bj.index('            Log.i(Name, "IRIS_26799_MULTI_PASS_CONNECTED_FALSE_COLOR_OWNER"',bs0)
jc=jc[:cs]+bj[bs0:be0]+jc[ce:]
cs=jc.index('                    Log.i(Name, "IRIS_26803_STRICT_NEUTRAL_PARENT_FRINGE_DECISIONS"')
ce=jc.index('                }\n            }\n        } finally {',cs)
bs0=bj.index('                    Log.i(Name, "IRIS_26802_NEUTRAL_PARENT_EDGE_FRINGE_DECISIONS"')
be0=bj.index('                }\n            }\n        } finally {',bs0)
jc=jc[:cs]+bj[bs0:be0]+jc[ce:]
need(sha_bytes(jc.encode())==sha(BASE/mv),'Java changed beyond owner/telemetry text')
print('PASS 26803 Java ownership: no allocation/binding/lifecycle delta; only active owner and minimal telemetry advanced')

# All other runtime files protected byte-exact.
for rel in a:
    if rel in MOD: continue
    need(a[rel]==c[rel],f'unexpected protected change {rel}')
print('PASS 26803 protected runtime: 1777 files byte-invariant, including Sabre/VGN/tone/UHDR/DNG/SR/native/vendor/UI/cleanup')
