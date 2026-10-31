#!/usr/bin/env python3
"""26891 EXACT active-owner and rollback semantics: no new shader or LONG changes."""
from pathlib import Path
import sys,re,hashlib
assert len(sys.argv)==3,'BASE CAND'
B=Path(sys.argv[1])/'app';C=Path(sys.argv[2])/'app'
def txt(root,rel):return (root/rel).read_text()
def sha(root,rel):return hashlib.sha256((root/rel).read_bytes()).hexdigest()
# 26890 compiled source is baseline; four rejected tone shaders/Java are restored
# to *exact successful 26889* hashes, never replaced with hand-written curves.
reverted={
 'src/main/assets/shaders/motionv2/gainmap.glsl':'',
 'src/main/assets/shaders/motionv2/local_laplacian_global_log_26621.glsl':'',
 'src/main/assets/shaders/motionv2/render.glsl':'',
 'src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java':'',
}
for path in reverted:
 assert sha(C,path)!=sha(B,path),('toe not reverted',path)
 assert 'IRIS_26890_B_ONLY_USER_EXPORTED_SHADOW_TOE' not in txt(C,path),('toe still exists',path)
# Version and private B OFF C++ operand are the only *new* intentional logic.
p='src/main/cpp/iris26864/bridge/Iris26887BOffHdrqRecorder.cpp'
a=txt(B,p);b=txt(C,p)
old='''    MismatchNormPc np{std::int32_t(tx), std::int32_t(ty),
                      1.0f / float(frameCount), uniformExposure_ ? 1 : 0};'''
new='''    // IRIS_26891_B_OFF_RESTORE_RAWR_MISMATCH_DOMAIN:
    // The Fourier merger's motion thresholds expect the original RAWR/Liba
    // mean-normalized mismatch (~0.12 in static tiles). In 26889 the B-only
    // uniform path passed 1 here, leaving raw noise-corrected mismatch near
    // order one and disabling almost every independent temporal contribution.
    // Pass zero ONLY to the mismatch-normalization shader: its sole branch
    // controls scale, not the separate B uniform RAW support or Fourier merge.
    // All existing per-tile motion vetoes and LONG reference policies remain.
    MismatchNormPc np{std::int32_t(tx), std::int32_t(ty),
                      1.0f / float(frameCount), 0};'''
assert a.count(old)==1 and b.count(new)==1 and b.replace(new,old)==a, 'B OFF C++ call changed outside exact mismatch-domain operand'
shader='src/main/cpp/iris26864/bridge/Iris26887BOffHdrqMismatchNorm.comp'
s=txt(C,shader)
assert sha(C,shader)==sha(B,shader),'B OFF matching compiled shader changed'
assert 'float scale = p.uniformExposure != 0 ? 1.0 : upstreamScale;' in s
assert '0.12 / (mean.v[0] + 1e-12)' in s
assert 'float m = clamp(imageLoad(mismatch, g).x * scale, 0.0, 1.0);' in s
assert s.count('p.uniformExposure')==1,'mismatch push constant has other consumer'
for path in ('src/main/cpp/iris26864/bridge/Iris26887BOffHdrqMerge.comp',
             'src/main/cpp/iris26864/bridge/Iris26888BOffHdrqMismatch.comp',
             'src/main/cpp/iris26864/bridge/Iris26888BOffHdrqCoordinator.cpp',
             'src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java',
             'src/main/java/com/particlesdevs/photoncamera/settings/Iris26856ABSettings.java'):
 assert sha(B,path)==sha(C,path),('protected processing or 26890 feature modified',path)
assert 'strength115ReadNoise = 16.0;' in txt(C,'src/main/cpp/iris26864/bridge/Iris26887BOffHdrqMerge.comp')
assert 'java.nio.file.Files.exists(imageFile)' in txt(C,'src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java')
assert 'return Mode.AMAZE_26855;' in txt(C,'src/main/java/com/particlesdevs/photoncamera/settings/Iris26856ABSettings.java')
assert txt(C,'version.properties').endswith('VERSION_NAME=0.9726891\nVERSION_BUILD=26891\n')
print('PASS 26891: exact 26889 tone rollback, normalizer C++ only, no GLSL/merge/LONG change, B default/JPEG/strength 11.5 preserved')
