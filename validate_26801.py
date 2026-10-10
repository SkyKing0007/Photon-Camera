#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26801.py BASE_ROOT CANDIDATE_ROOT')
BASE,CAND=map(Path,sys.argv[1:])
MOD={
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
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
print('PASS 26801 authority-seeded scope: 1782 -> 1782, exactly 3 modified / 0 added / 0 deleted')
v=(CAND/'app/version.properties').read_text()
need('VERSION_NAME=0.9726801' in v and 'VERSION_BUILD=26801' in v,'version')
print('PASS 26801 version 0.9726801 / 26801')

mv='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java'
pp='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java'
j=(CAND/mv).read_text(); p=(CAND/pp).read_text(); bj=(BASE/mv).read_text(); bp=(BASE/pp).read_text()
# Exact telemetry allocation contracts.
need('iris26798Stats = new GLBuffer(12' in j and 'iris26798Stats.uploadBuffer(new int[12], 12);' in j,'26798 12-counter allocation changed')
need('iris26799Stats = new GLBuffer(28' in j and 'iris26799Stats.uploadBuffer(new int[28], 28);' in j,'26799/26800 28-counter allocation changed')
# Parse each read block and prove max Java index does not exceed its runtime guard/allocation.
b98=j.index('if (basePipeline.mParameters.motionV2Active && iris26798Stats != null) {', j.index('glMemoryBarrier'))
e98=j.index('if (basePipeline.mParameters.motionV2Active && iris26799Stats != null) {',b98)
blk98=j[b98:e98]
idx98=[int(x) for x in re.findall(r'stats\[(\d+)\]',blk98)]
need(idx98 and max(idx98)<=11,f'iris26798Stats out-of-bounds access survived: max={max(idx98) if idx98 else None}')
need('stats.length >= 12' in blk98,'26798 runtime length guard missing')
b99=e98; e99=j.index('        } finally {',b99); blk99=j[b99:e99]
idx99=[int(x) for x in re.findall(r'stats\[(\d+)\]',blk99)]
need(idx99 and max(idx99)<=27,f'iris26799Stats access exceeds 28 entries: max={max(idx99) if idx99 else None}')
need('stats.length >= 28' in blk99,'26799 runtime length guard missing')
for idx in range(20,28): need(f'stats[{idx}]' in blk99,f'26800 telemetry counter {idx} not owned by 28-entry buffer')
need('IRIS_26801_TELEMETRY_BUFFER_OWNERSHIP_REPAIR' in blk99,'26801 telemetry repair marker missing')
need('IRIS_26800_HIGH_CHROMA_FALSE_COLOR_DECISIONS' in blk99,'26800 high-chroma decision log missing')
need('highChromaRelevant=' not in blk98,'high-chroma telemetry still attached to 12-entry block')
print('PASS 26801 telemetry ownership: 12-entry stats max index 11; 28-entry stats owns counters 20..27')

# Failure cleanup must be Motion-only, preserve original exception, and run texture cleanup before owner close.
for s in ('IRIS_26801_MOTION_POST_EXCEPTION_GL_CLEANUP','catch (RuntimeException | Error failure)',
          'GLTexture.closeAll();','failure.addSuppressed(cleanupFailure);','close();',
          'failure.addSuppressed(closeFailure);','throw failure;'):
    need(s in p,f'exception cleanup contract missing: {s}')
segment=p[p.index('try {\n            return Run(null, parameters);'):p.index('    public Bitmap RunIrisNightRgb')]
need(segment.index('GLTexture.closeAll();') < segment.index('close();') < segment.index('throw failure;'),'failure cleanup order incorrect')
need('return Run(null, parameters);' in segment,'normal Motion Run entry changed')
# Success-only Run path itself stays unchanged; failure repair is wrapper-local.
run_start=p.index('    public Bitmap Run(ByteBuffer inBuffer, Parameters parameters)')
need(p[run_start:].count('GLTexture.closeAll();')>=1,'normal success cleanup missing')
print('PASS 26801 Motion exception cleanup: tracked textures cleared while context current, failed owner closed, original failure rethrown')

# Freeze 26800 IQ and UI corrections byte-identically.
for rel in [
'app/src/main/assets/shaders/motionv2/false_color_classify_26800.glsl',
'app/src/main/assets/shaders/motionv2/false_color_classify_26799.glsl',
'app/src/main/assets/shaders/motionv2/false_color_propagate_26799.glsl',
'app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java']:
    need(sha(BASE/rel)==sha(CAND/rel),f'26800 IQ/UI frozen file changed: {rel}')
# Ensure MotionV2Render only changes telemetry output, not classifier/propagation/render bindings.
for s in ('IRIS_26800_HIGH_CHROMA_FALSE_COLOR_ADMISSION_OWNER','useAssetProgram("motionv2/false_color_classify_26800")',
          'useAssetProgram("motionv2/false_color_propagate_26799")','IRIS_26799_PROPAGATION_ITERATIONS = 8'):
    need(s in j,f'26800 IQ Java owner missing: {s}')
# Protected universe exact except allowlist.
for rel in a:
    if rel in MOD: continue
    need(a[rel]==c[rel],f'unexpected protected change {rel}')
print('PASS 26801 frozen behavior: 26800 high-chroma IQ + UI stability + 26799 propagation byte-invariant')

# Permanent exact failing-condition regression.
need('stats[20]' in bj and 'stats.length >= 12' in bj,'26800 authority no longer reproduces telemetry failure fixture')
need(max(int(x) for x in re.findall(r'stats\[(\d+)\]',bj[bj.index('if (basePipeline.mParameters.motionV2Active && iris26798Stats != null) {',bj.index('glMemoryBarrier')):bj.index('if (basePipeline.mParameters.motionV2Active && iris26799Stats != null) {',bj.index('glMemoryBarrier'))]))==27,
     '26800 exact out-of-bounds fixture not present')
need('return Run(null, parameters);' in bp and 'IRIS_26801_MOTION_POST_EXCEPTION_GL_CLEANUP' not in bp,'26800 cleanup-gap fixture not present')
print('PASS 26801 permanent regressions: exact 26800 length=12/index=20+ telemetry crash removed; Motion failure cleanup gap closed')
