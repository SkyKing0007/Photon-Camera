#!/usr/bin/env python3
"""26898 real compiled-source DNG/JPG routing guard (not device test)."""
from pathlib import Path
import sys
assert len(sys.argv)==2
R=Path(sys.argv[1]);app=R/'app'
B=(app/'src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
H=(app/'src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java').read_text()
N=(app/'src/main/cpp/iris26856/amaze/src/AmazeGlVulkanJni.cpp').read_text()
I=(app/'src/main/cpp/iris26864/Iris26864JniGpuInteropImpl.inc').read_text()
# Three real settings: JPEG-only has no optional Sabre A DNG, DNG-only
# terminates after successful historical DNG publication, paired DNG/JPEG
# keeps B but only after the private A context has been retired.
assert B.count('!parameters.irisNightActive && produceNormalStackedDng')==1
assert B.count('if (nativeB26868 && earlyDngPublisher != null)')==1
assert H.count('saveRAW >= 1 ? originalDng ->')==1
assert H.count('saveRAW == 2);')==1
assert 'IRIS_26898_DNG_ONLY_COMPLETE' in H
assert B.index('val dngEgl = IsolatedDngEgl.enter()')<B.index('earlyDngPublisher.publish(originalDng)')
assert B.index('earlyDngPublisher.publish(originalDng)')<B.index('dngEgl.close()')
assert B.index('dngEgl.close()')<B.index('if (independentDngOnlyDone)')
assert B.index('if (independentDngOnlyDone)')<B.index('val stackB26856 = fusion.processFrames(frames)')
assert 'if (error is DngOnlyPublished) throw error' in B
assert 'dngEgl.close()' in B[B.index('} finally {\n                    aliases.forEach'):]
assert B.count('GlesMgcRawFusion(')>=2
assert 'useCurrentGlContext = true,exportGpuLinearRgbSource = true,' in B
assert 'EGL14.eglGetCurrentContext() == previousContext' in B
assert 'EGL14.eglDestroyContext(display, isolatedContext)' in B
assert B.count('egl?.close()')==2  # Existing historical EglOwner closures, no changes
assert H.count('ImageSaver.Util.saveNormalized16StackedRaw(')>=1
assert H.count('IrisSabreSuperResDngWriter.write(')>=1
assert H.count('mIrisDngIndependentSaved = saved')==1
assert H.count('IRIS_DNG_INDEPENDENT_PRE_B_PUBLISHED')==1
assert H.count('!mIrisDngIndependentAttempted')>=1
assert 'GlBufferImage glRgb(rgbAhb.get(), "B_HDRQ_RGB")' in I
assert 'GlBufferImage glClip(clipAhb.get(), "B_HDRQ_SENSOR_CLIP")' in I
assert 'targetImage(GL_TEXTURE_2D, image)' in N
assert 'assertGl("glEGLImageTargetTexture2DOES")' in N
print('PASS 26898 actual source: JPEG-only untouched, DNG-only no B GPU, JPG+DNG isolated GL handoff, original DNG writer and B native math retained')
