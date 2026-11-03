#!/usr/bin/env python3
"""Real compiled-candidate source-domain DNG toggle regression; runtime Pixel still required."""
from pathlib import Path
import sys
R=Path(sys.argv[1])
B=(R/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
H=(R/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java').read_text()
assert B.index('earlyDngPublisher.publish(originalDng)')<B.index('fusion.processFrames(frames)')
assert B.count('if (nativeB26868 && earlyDngPublisher != null)')==1
assert 'if (nativeB26868 && isolatedADng26868 != null)' in B
assert 'IRIS_DNG_A_TO_B_PRIOR_GL_ERROR' in B
assert 'IRIS_DNG_A_TO_B_GL_HANDOFF' in B
assert 'ownedIndependentDngForCleanup?.let' in B
assert H.count('saveRAW >= 1 ? originalDng ->')==1
assert H.count('mIrisDngIndependentAttempted = true;')==1
assert H.count('mIrisDngIndependentSaved = saved;')==1
assert H.count('IRIS_DNG_INDEPENDENT_RAW_ONLY_B_FAILURE_IGNORED')==1
assert H.count('IRIS_DNG_INDEPENDENT_PRE_B_PUBLISHED')==1
assert 'if (saveRAW == 2)' in H and 'if (mIrisDngIndependentAttempted)' in H
assert 'if (!mIrisDngIndependentAttempted)' in H
assert 'iris26826DeferredDngTask = () ->' in H
assert 'processingEventsListener.notifyImageSavedStatus(saved, dngFile)' in H
assert 'getNormalStackedDngNoiseProfile()' in H and 'getTrue2xLinearRgbPath()' in H
print('PASS 26897 real 26895-source two DNG toggles (RAW only, JPG+DNG), B-GL exception isolation, no duplicate publication')
