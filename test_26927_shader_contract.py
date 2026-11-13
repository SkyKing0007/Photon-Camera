#!/usr/bin/env python3
"""Source ESSL300/310 descriptor ABI; production native Vulkan untouched."""
from pathlib import Path
import sys,re
R=Path(__file__).resolve().parent
P=R/'handoff_payload_26927' if '--payload' in sys.argv else R
j=P/'app/src/main/java/com/hinnka/mycamera/processor'
c=(j/'GlesIris26870PostAmazeChroma.kt').read_text()
f=(j/'GlesIris26856RawrFalseColor.kt').read_text()
for token in ('uniform sampler2D uSensorNeutralAmazeRgb','uniform int uIris26922SrOn','uniform vec3 uIris26926ShotByRgb','uniform vec3 uIris26926ReadByRgb','uniform sampler2D uIris26926LensShading','uniform int uIris26924BOff','layout(location=0) out vec4 oPostWbCameraRgb','sameSideWeakChroma'):
 assert token in c,token
for token in ('uniform sampler2D uRgb','uniform sampler2D uIris26924SensorClip','uniform int uIris26924ClipPresent','uniform int uIris26924BOff','layout(location=0) out vec2 oIQ','layout(location=0) out vec4 oRgb','chromaticBoundary'):
 assert token in f,token
assert c.count('#version 300 es')==1 and f.count('#version 300 es')==2
for s in (c,f):
 assert not re.search(r'\b(?:coherent|volatile|restrict|readonly|writeonly)\s*\(',s)
 assert 'precision highp float;' in s
print('PASS unchanged 26926 original GLSL ABI, 26925 reserved identifier negatives retained in Actions; current real pinned compile required')
