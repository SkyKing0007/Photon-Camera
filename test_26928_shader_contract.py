#!/usr/bin/env python3
"""Source and sampler ABI guard; no substitute for pinned real shader compilation."""
from pathlib import Path
import sys,re
R=Path(__file__).resolve().parent
P=R/'handoff_payload_26928' if '--payload' in sys.argv else R
c=(P/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26870PostAmazeChroma.kt').read_text()
for token in ('uniform sampler2D uSensorNeutralAmazeRgb;', 'uniform ivec2 uSize;',
 'uniform int uIris26922SrOn;', 'uniform vec3 uIris26926ShotByRgb;',
 'uniform vec3 uIris26926ReadByRgb;', 'uniform sampler2D uIris26926LensShading;',
 'uniform int uIris26924BOff;', 'uniform sampler2D uIris26924SensorClip;',
 'uniform int uIris26924ClipPresent;', 'layout(location=0) out vec4 oPostWbCameraRgb;',
 'vec3 bOffMaterialOutlier(', 'if(uIris26924BOff==0 || rawClipped(p)',
 'rawrHighlightOff(repaired)'):
 assert token in c,token
assert c.count('#version 300 es')==1 and 'precision highp float;' in c and 'precision highp int;' in c
assert not re.search(r'\b(?:coherent|volatile|restrict|readonly|writeonly)\s*\(',c)
assert c.count('vec2 donor[8];bool valid[8];')==1
print('PASS shader GLSL ES300/310 source/sampler ABI exact, real pinned compilation mandatory in Actions')
