#!/usr/bin/env python3
"""26928 exact B OFF-only source audit; no unapproved source files changed."""
from pathlib import Path
import sys,re
R=Path(__file__).resolve().parent
P=R/'handoff_payload_26928' if '--payload' in sys.argv else R
c=(P/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26870PostAmazeChroma.kt').read_text()
v=(P/'app/version.properties').read_text()
assert 'VERSION_NAME=0.9726928\nVERSION_BUILD=26928' in v
for token in ('IRIS_26928_B_OFF_SOURCE_DOMAIN_MATERIAL_CHROMA',
              'vec3 bOffMaterialOutlier(',
              'if(uIris26924BOff==0 || rawClipped(p)',
              'if(uIris26924BOff!=0){\n            vec3 repaired=bOffMaterialOutlier(p,c,y,structure);',
              'if(n<4.0)return c;','if(cleanN<4.0)return c;',
              'if(scatter>0.085)return c;',
              'if(displaced>=2.0 || firstScatter>0.092)return c;',
              'if(saturation>0.20 && peers>=2.0)return c;',
              'vec2 corrected=mix(center,consensus,clamp(gain,0.0,0.57));',
              'oPostWbCameraRgb=vec4(rawrHighlightOff(repaired),raw.a);return;'):
 assert token in c,token
assert 'sameSideWeakChroma' not in c and c.count('vec3 bOffMaterialOutlier(')==1
assert 'if(uIris26924BOff!=0 && ring>=2) continue;' in c
assert 'float protectedStructure=1.0-smoothstep(0.04,0.14,structure);' in c
assert c.index('vec3 repaired=bOffMaterialOutlier(p,c,y,structure)')<c.index('if(protectedStructure<=0.0)')
assert c.count('uniform int uIris26922SrOn;')==1
assert c.count('uniform int uIris26924BOff;')==1
assert c.count('#version 300 es')==1
from build_26928_incremental import scope,parse,sha
changes,added,original,target=scope()
assert changes=={'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26870PostAmazeChroma.kt','app/version.properties'} and not added
assert len(original)==len(target)==2041
for name in original:
 if name not in changes:assert target[name]==original[name],name
# Important: the HDRq frequency owner, AMaZE, FCC, A, ON, Spektra, native,
# vendor, shader ABI, DNG and UHDR runtime bytes are *all* SHA-protected.
for name in ('app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
             'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26856RawrFalseColor.kt'):
 assert target[name]==original[name],name
if '--live' in sys.argv:
 for name in changes:assert sha(R/name)==target[name],name
print('PASS exact 26928 2 changed files / 2039 protected, only B OFF sensor-neutral chroma repair, unchanged ON/A/native/FCC and WB')
