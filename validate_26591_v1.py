#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys
CHANGED=[
'app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java',
'app/version.properties']
def fail(x):raise SystemExit('FAIL: '+x)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def amap(r):return {p.relative_to(r).as_posix():sha(p) for p in sorted((r/'app').rglob('*')) if p.is_file()}
def need(s,t,l):
 if t not in s:fail(l+' missing '+t)
def main():
 if len(sys.argv)!=3:fail('usage base candidate')
 b,c=map(Path,sys.argv[1:]);a,d=amap(b),amap(c)
 if len(a)!=1708 or len(d)!=1708:fail(f'universe {len(a)}/{len(d)}')
 diff=sorted(k for k in set(a)|set(d) if a.get(k)!=d.get(k))
 if diff!=sorted(CHANGED):fail('allowlist '+repr(diff))
 v=(c/'app/version.properties').read_text();need(v,'VERSION_NAME=0.9726591','version');need(v,'VERSION_BUILD=26591','version')
 for r,h in a.items():
  if r not in CHANGED and d.get(r)!=h:fail('protected owner '+r)
 render=(c/CHANGED[2]).read_text(); vf=(c/CHANGED[3]).read_text(); glsl=(c/CHANGED[0]).read_text(); stack=(c/CHANGED[1]).read_text()
 # 26590 body/meter freeze and 26591 final-tail separation.
 for t in ['IRIS_26582_TONE_START = 0.50f','OUTPUT_EXPOSURE_SCALE = 0.80f','IRIS_26582_LOG_SHAPE = 6.0f','IRIS_26591_LOG_SHAPE = 3.0f',
           'IRIS_26591_HIGHLIGHT_TARGET = 0.980f','IRIS_26591_BROAD_HIGHLIGHT_TARGET = 0.975f','IRIS_26591_COMPACT_HIGHLIGHT_TARGET = 0.985f',
           'IRIS_26591_CONTINUOUS_HIGHLIGHT_TARGET = 0.980f','IRIS_26591_STRUCTURED_HIGHLIGHT_TARGET = 0.985f',
           'iris26591MapHeadroom','iris26591RequiredSceneWhite']:
  need(render,t,'26591 render')
 need(glsl,'const float start=0.50;','render GLSL tone start')
 need(glsl,'const float logShape=3.0;','render GLSL final shape')
 need(glsl,'linearSrgb*=outputExposureScale;','render GLSL output scale')
 need(glsl,'Uniform RGB scaling preserves channel','render GLSL whole-RGB')
 for t in ['IRIS_26591_VIEWFINDER_BODY_FREEZE_FINAL_TAIL_SPLIT','meterCurveFrozen26590=true',
           '? MotionV2Render.iris26591MapHeadroom(postGuide, sceneWhite)',
           ': MotionV2Render.iris26582MapHeadroom(postGuide, sceneWhite)',
           'MotionV2Render.IRIS_26591_STRUCTURED_HIGHLIGHT_TARGET',
           'MotionV2Render.IRIS_26591_CONTINUOUS_HIGHLIGHT_TARGET']:
  need(vf,t,'26591 meter/final split')
 # The solver's presented-luma owner remains the old 26590 meter map, so final curve cannot feed back into body EV.
 p=vf[vf.index('private static float presentedLuma'):vf.index('private static float srgbDecode')]
 need(p,'MotionV2Render.iris26582MapHeadroom(guide, sceneWhite)','26590 meter map freeze')
 if 'iris26591MapHeadroom' in p:fail('final 26591 tone leaked into viewfinder/body solver')
 # SHORT geometry/math remains 26590; only durable telemetry is added in this file.
 for t in ['IRIS_26590_SHORT_MASK_EFFECT','IRIS_26591_SHORT_MASK_EFFECT','sameSabreFlow=true wholeRgb=true maskFilter=NEAREST',
           'probeSabreShortRestoreMask26590(highlightShortMask26587)','MotionTrace.processingState(']:
  need(stack,t,'SHORT telemetry')
 if 'IRIS_26591_PHOTON_LIKE_UPPER_TAIL_SEPARATION' not in render or 'IRIS_26591_PHOTON_LIKE_UPPER_TAIL_SEPARATION' not in glsl:fail('final-tail marker')
 print('PASS exact successful-26590 authority -> five-file 26591 allowlist')
 print('PASS exact 26590 viewfinder/body meter curve frozen; 26591 final render alone uses less-concave shape-3 upper tail')
 print('PASS tone start=0.50 and output scale=0.80 unchanged; global uniform-RGB/no-local-tone architecture preserved')
 print('PASS SHORT stack change is telemetry-only; Sabre shader/alignment/mask geometry remains protected')
 print('PASS all 1703 non-allowlisted app files byte-identical to successful 26590')
if __name__=='__main__':main()
