#!/usr/bin/env python3
"""Preserve 26955 completed +0.4 EV source and HDR gain-map denominator exactly."""
import hashlib,sys
from build_26958_incremental import R,scope,fail
changed,added,old,new=scope()
for p in ('app/src/main/assets/shaders/motionv2/render.glsl',
          'app/src/main/assets/shaders/motionv2/gainmap.glsl',
          'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java'):
    if old[p]!=new[p]:fail('SDR/UHDR source modified '+p)
if '--live' in sys.argv:
    r=(R/'app/src/main/assets/shaders/motionv2/render.glsl').read_text()
    g=(R/'app/src/main/assets/shaders/motionv2/gainmap.glsl').read_text()
    if 'const float iris26954SdrExposureScale=1.3195079107728942;' not in r:fail('+0.4 EV no longer present')
    if 'float hdrIntentY=sdr+matchedIntentDelta;' not in g:fail('UHDR denominator lost')
    if 'ratio=clamp((hdrIntentY+UHDR_OFFSET)/(sdr+UHDR_OFFSET),1.0,safeMax);' not in g:fail('HDR relative to new SDR lost')
print('PASS original 26955 published +0.4EV SDR/UHDR byte-exact retained')
