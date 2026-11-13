#!/usr/bin/env python3
"""Exact 26927 B-only source ownership / sampler order / immutable protected code."""
from pathlib import Path
import sys
R=Path(__file__).resolve().parent
P=R/'handoff_payload_26927' if '--payload' in sys.argv else R
j=P/'app/src/main/java/com/hinnka/mycamera/processor'
a=(j/'GlesMgcRawSpatialStacker.kt').read_text();c=(j/'GlesIris26870PostAmazeChroma.kt').read_text();f=(j/'GlesIris26856RawrFalseColor.kt').read_text()
assert 'VERSION_NAME=0.9726927\nVERSION_BUILD=26927' in (P/'app/version.properties').read_text()
b=a[a.index('private fun renderRawrBPostAmaze26856('):a.index('private fun renderSabreNormalCfaExtract26852(')]
assert b.count('if (srOnMap26927) ensureIris26859BLensMapTexture()')==1
assert b.index('if (srOnMap26927) ensureIris26859BLensMapTexture()')<b.index('bindTexture(applyProgram, "uSensorNeutralAmazeRgb", 0,')
assert b.index('bindTexture(applyProgram,"uSensorNeutralAmazeRgb",0,rgb26927)')<b.index('draw(applyProgram, processingWidth, processingHeight, intArrayOf(temporaryPostWb))')
assert 'rgb26927 in textures' in b and 'processingWidth == width * 2' in b
assert 'if(uIris26924BOff==0 || structure<0.14 || rawClipped(p))return c;' in c
assert 'if(length(center)>0.33)return c;' in c and 'if(spread>0.011 || discrepancy<0.065)return c;' in c
assert 'if(uIris26924BOff!=0 && ring>=2) continue;' in c
assert 'if(uIris26924BOff!=0 && material>0.005' in c
assert 'if(uIris26924BOff!=0 && (clipNear(p)||hardEdge(p)||chromaticBoundary(p)))' in f
assert 'w*=1.0-smoothstep(0.14,0.38,length(c0-c1));' in f
assert b.index('renderRawrLabDefringe26856(')<b.index('renderRawrFalseColor26856(')
from build_26927_incremental import scope
changes,added,_,_=scope()
assert len(changes)==4 and not added
print('PASS 26927 B ON RGB texture binding / B OFF same-material color boundary / true 2-pass FCC / exact runtime scope')
