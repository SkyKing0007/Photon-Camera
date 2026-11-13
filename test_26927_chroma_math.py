#!/usr/bin/env python3
"""Bounded synthetic edge and true-color tests; this is not photographic device IQ."""
import math,sys
from pathlib import Path
R=Path(__file__).resolve().parent
P=R/'handoff_payload_26927' if '--payload' in sys.argv else R
j=P/'app/src/main/java/com/hinnka/mycamera/processor'
s=(j/'GlesIris26870PostAmazeChroma.kt').read_text()
assert 'sameSideWeakChroma' in s and 'float gain=0.40*' in s
assert 'if(spread>0.011 || discrepancy<0.065)return c;' in s

def ss(a,b,x):
 t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
def edge(center,donors,structure=.34,clipped=False,b_off=True):
 if not b_off or structure<.14 or clipped or math.hypot(*center)>.33 or len(donors)<4:return center
 mean=tuple(sum(v[i] for v in donors)/len(donors) for i in range(2))
 spread=math.hypot(*(max(0,sum(v[i]**2 for v in donors)/len(donors)-mean[i]**2) for i in range(2)))
 difference=math.dist(center,mean)
 if spread>.011 or difference<.065:return center
 g=.4*(1-ss(.16,.32,math.hypot(*center)))*ss(.065,.2,difference)
 return tuple(center[i]*(1-g)+mean[i]*g for i in range(2))
for illum in (.005,.04,.35,.9):
 donors=[(.006,-.003)]*5
 assert math.dist(edge((.19,-.03),donors),donors[0])<math.dist((.19,-.03),donors[0])
assert edge((.22,.26),[(0,0)]*8)==(.22,.26) # genuine strong color
assert edge((.13,.01),[(.2,-.2),(-.2,.2)]*4)==(.13,.01) # material disagreement
assert edge((.12,.01),[(0,0)]*6,clipped=True)==(.12,.01)
assert edge((.12,.01),[(0,0)]*6,b_off=False)==(.12,.01)
assert edge((.12,.01),[(0,0)]*6,structure=.05)==(.12,.01)
a=(j/'GlesMgcRawSpatialStacker.kt').read_text()
b=a[a.index('private fun renderRawrBPostAmaze26856('):a.index('private fun renderSabreNormalCfaExtract26852(')]
assert b.index('if (srOnMap26927) ensureIris26859BLensMapTexture()')<b.index('bindTexture(applyProgram, "uSensorNeutralAmazeRgb", 0,')
assert b.index('bindTexture(applyProgram,"uSensorNeutralAmazeRgb",0,rgb26927)')<b.index('draw(applyProgram, processingWidth, processingHeight, intArrayOf(temporaryPostWb))')
print('PASS synthetic dark/bright B OFF weak hue outlier and protected real colors + B ON sampler order; device IQ NOT RUN')
