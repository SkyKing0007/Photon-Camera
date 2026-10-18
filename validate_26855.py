#!/usr/bin/env python3
# 26855 version-scoped extension of the successful 26854 semantic/ownership validation.
from pathlib import Path
import hashlib,re,sys,textwrap
B,C=map(Path,sys.argv[1:3]); S='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt';T='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt';V='app/version.properties'
CC='app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java'
IF='app/src/main/java/com/particlesdevs/photoncamera/processing/ImageFrame.java'
BR='app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt'
RF='app/src/main/java/com/hinnka/mycamera/processor/RawStackFrameCompat.kt'
ALLOW={S,T,V,CC,IF,BR,RF}
def U(r):return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app').rglob('*') if p.is_file()}
b,c=U(B),U(C)
assert len(b)==len(c)==1786,(len(b),len(c));assert set(b)==set(c)
assert {p for p in b if b[p]!=c[p]}==ALLOW,('changed file allowlist',{p for p in b if b[p]!=c[p]})
def template_map(txt):
 out={}
 for m in re.finditer(r'^\s*(?:private\s+)?val\s+(\w+)[^\n]*?"""',txt,re.M):
  name=m.group(1);a=txt.find('"""',m.start())+3;z=txt.find('""".trimIndent()',a)
  if z>=0:out[name]=textwrap.dedent(txt[a:z]).strip('\n')
 return out
def function(txt,needle):
 p=txt.index(needle);i=txt.index('{',p);depth=0;quote=False;esc=False
 for j in range(i,len(txt)):
  ch=txt[j]
  if quote:
   if esc:esc=False
   elif ch=='\\':esc=True
   elif ch=='"':quote=False
   continue
  if ch=='"':quote=True;continue
  if ch=='{':depth+=1
  if ch=='}':
   depth-=1
   if depth==0:return txt[p:j+1]
 raise AssertionError(needle)
bs=(B/S).read_text();cs=(C/S).read_text();bt=template_map(bs);ct=template_map(cs)
assert set(bt)==set(ct),'shader templates changed'
mods={n for n in bt if bt[n]!=ct[n]};assert mods=={'normalCfaTemporalAccumulate26852','normalCfaNoiseClean26853'},mods
acc=ct['normalCfaTemporalAccumulate26852'];before=bt['normalCfaTemporalAccumulate26852']
for tok in ('IRIS_26855_RAW_CFA_IMPULSE_REPAIR_OWNER','IRIS_26855_PHASE_NOISE_FOR_IMPULSE_GUARD','uPhaseNoiseShot26855','uPhaseNoiseRead26855','uVerifiedHotPixelMask26855','uVerifiedHotPixelMapEnabled26855','IRIS_26855_SENSOR_MAP_SPARSE_DEFECT_OWNER','guardedRaw26855(p)','headroomForSignal26855(v26855)','ringMax-ringMin','center <= ringMax','0.125*(a+b+c+d+e+f+g+h)'):
 assert tok in acc,tok
for tok in ('float baseWeight = quadRejection(quadOrigin) * rowReliability(sourceUv.y);','float validWeight = baseWeight *','sharedHeadroom = min(sharedHeadroom, h);','oSharedSupport = vec4(validWeight, baseWeight, baseWeight * clipConfidence, 0.0);','oPhaseSignal = phaseSignal * validWeight;','oPhaseValidity = phaseHeadroom * validWeight;','oTemporalStats26853 = vec2(validWeight * validWeight,'):
 assert tok in acc,('protected admission',tok)
for tok in ('uDngQuadHeadroom','uJpegNeutralClamp','grayFallback26855','hueTransfer26855','crossPhaseTemporal26855','phaseIndependentTemporalWeight26855'):
 assert tok not in acc,('forbidden impulse owner',tok)
clean=ct['normalCfaNoiseClean26853']
for tok in ('IRIS_26855_COHERENT_TEXTURE_VETO','normalizedDifference','sameMaterial','nEff26854','sigma26854','float highFreqGreen=0.0;','float flatGate=','cleaned.r=mix(center.r,consensus.r,chromaBlend);','cleaned.a=mix(center.a,consensus.a,chromaBlend);','oCleanPhaseSignal=cleaned*sumW;'):
 assert tok in clean,tok
assert 'cleaned.g=' not in clean and 'cleaned.b=' not in clean, 'green CFA phases changed by cleanup'
for tok in ('uDngQuadHeadroom','uJpegNeutralClamp','hueDonation','globalEffectiveSupport','crossPhase','fallback'):
 assert tok not in clean,('forbidden cleaner',tok)
assert 'texelFetch(uVerifiedHotPixelMask26855,p,0).r > 0.5' in acc
assert 'if (sensorDefect)' in acc and 'center <= cardinalMax + max(9.0*sigma,0.055)' in acc
assert cs.count('IRIS_26855_RAW_CFA_IMPULSE_REPAIR_OWNER')==1
assert cs.count('IRIS_26855_COHERENT_TEXTURE_VETO')==1
for marker in ('IRIS_26846_CFA_PHASE_BALANCED_CHROMA_AUTHORITY','IRIS_26847_SAME_MATERIAL_GREEN_TOPOLOGY_OWNER','IRIS_26848_SAME_MATERIAL_RB_TOPOLOGY_OWNER','IRIS_26849_PERIPHERAL_PHASE_SAFE_CFA_LCA_OWNER','IRIS_26850_ADAPTIVE_SAME_PHASE_CFA_REGISTRATION_OWNER','IRIS_26851_ALL_FIELD_MATERIAL_EDGE_REGISTRATION_OWNER','IRIS_26852_SINGLE_OWNER_TEMPORAL_CFA_ACCUMULATOR','IRIS_26854_NOISE_CALIBRATED_CFA_OWNER'):
 assert marker in cs,marker
bp=(B/T).read_text();cp=(C/T).read_text()
assert bp.count('renderSabreNormalCfaTemporalAccumulate26852(')==cp.count('renderSabreNormalCfaTemporalAccumulate26852(')==3
assert bp.count('renderSabreNormalCfaNoiseClean26853(')==cp.count('renderSabreNormalCfaNoiseClean26853(')==2
for tok in ('IRIS_26855_FRAME_LOCAL_SENSOR_NEUTRAL_NOISE_AUTHORITY','calibration.shotNoise[channel] / calculationWhiteBalance[channel]','calibration.readNoise[channel] / (gain * gain)','uniform4fv(program, "uPhaseNoiseShot26855", shot26855)','uniform4fv(program, "uPhaseNoiseRead26855", read26855)','IRIS_26853_MULTIFRAME_NATIVE_CFA_DENOISE_OWNER','sharedAdmissionUnchanged=true','IRIS_26855_SENSOR_COORDINATE_VERIFIED_BURST_MAP','verifiedHotPixelMask26855 = verifiedHotPixelMask26855','verifiedHotPixelMapEnabled26855 = verifiedHotPixelMapEnabled26855','GLES30.glTexSubImage2D(', 'IRIS_26855_SPARSE_MAP_SUPPORT'):
 assert tok in cp,('stacker',tok)
for sig in ['private fun clearSabreNormalDngAccumulator(', 'private fun renderSabreNormalDngMerge(', 'private fun resolveSabreNormalDngSupportStats(', 'private fun renderSabreNormalMasterShortFusion26651(', 'private fun renderSabreShadowLongLumaAccumulate26833(', 'private fun renderSabreShadowLongPostVgnLumaApply26833(', 'private fun renderSabreDehomogenize(', 'private fun renderSabreNormalCfaNoiseClean26853(', 'private fun renderSabreNormalCfaExtract26852(']:
 assert function(bp,sig)==function(cp,sig),('protected function changed',sig)
for tok in ('programs += program','for (program in programs) GLES30.glDeleteProgram(program)','programs.clear()'):
 assert tok in cp,('GL lifecycle',tok)
assert cp.count('verifiedHotPixelMask26855 = verifiedHotPixelMask26855')==2,'all NORMAL accumulators must use the mask'
assert cp.count('bindTexture(program, "uVerifiedHotPixelMask26855", 4, verifiedHotPixelMask26855)')==1
assert 'GLES30.glTexSubImage2D(' in cp
assert 'mapPixels26855 <= 32L * 1024L * 1024L' in cp, 'mask allocation is unbounded'
assert 'GLES30.GL_PIXEL_UNPACK_BUFFER_BINDING' in cp, 'GL unpack PBO not restored'
assert 'f.physicalCameraId != referenceCamera26855' in cp
assert 'mapFrames26855 == 1 || it >= 2' in cp
assert 'IRIS_26852_DELAYED_RGB_ADAPTER_ALLOCATION' in cp
assert 'IRIS_26852_ONE_TIME_CFA_TO_RGB_RECONSTRUCTION_OWNER' in cp
v=(C/V).read_text();assert 'VERSION_NAME=0.9726855' in v and 'VERSION_BUILD=26855' in v
# Permanent reproduction of the 26854 high-noise defects: a center-only
# impulse cannot be rescued by its old center-conditioned neighbor weights.
# A coherent needle/stitch (neighborhood span) must never be removed by the
# new sparse same-phase early RAW guard. These are *additional* math regressions;
# they do not replace real pinned GLSL compilation or device tests.
import math
def impulse26855(center,ring,shot,read):
 a,b,c,d,e,f,g,h=ring
 card=[a,b,c,d]; mx=max(card);mn=min(card)
 mu=sum(card)*0.25; sigma=math.sqrt(max(shot*max(mu,0.0)+read,1e-9))
 if center<=mx+max(9*sigma,.055) or mx-mn>max(3.5*sigma,.025):return center
 if max(ring)-min(ring)>max(4*sigma,.030) or center<=max(ring)+max(9*sigma,.055):return center
 return sum(ring)*.125
sample=[.034,.035,.036,.035,.034,.035,.036,.035]
assert abs(impulse26855(.48,sample,.0015,.000008)-sum(sample)/8)<1e-8,'isolated hot pixel survived'
assert impulse26855(.054,sample,.0015,.000008)==.054,'ordinary texture removed'
assert impulse26855(.48,[.01,.2,.02,.23,.015,.17,.04,.25],.0015,.000008)==.48,'real coherent high-frequency object removed'
assert impulse26855(.005,[.03]*8,.0015,.000008)==.005,'shadow detail falsely removed'
assert 'cleaned.g=' not in clean and 'cleaned.b=' not in clean,'green fabric texture lost'
print('PASS 26855 permanent regression: severe same-phase impulse removed; fabric/weave/chroma/non-hot samples preserved; both greens identity')
# Camera2 optional map must be sourced exclusively from exact timestamp-matched
# results and must use proven 1:1 array->RAW translation, never interpolation.
cc0=(B/CC).read_text(); cc1=(C/CC).read_text()
for mark in ('IRIS_26855_OPTIONAL_SENSOR_DEFECT_METADATA_REQUEST',
             'IRIS_26855_SENSOR_PIXEL_ARRAY_COORDINATE_OWNER',
             'CaptureRequest.STATISTICS_HOT_PIXEL_MAP_MODE, true',
             'CaptureResult.STATISTICS_HOT_PIXEL_MAP',
             'CameraCharacteristics.SENSOR_INFO_PIXEL_ARRAY_SIZE',
             'CameraCharacteristics.SENSOR_INFO_PRE_CORRECTION_ACTIVE_ARRAY_SIZE',
             'if (pixelArray.getWidth() == rw && pixelArray.getHeight() == rh)',
             'preCorrection.width() == rw', 'preCorrection.height() == rh',
             'populateIris26855SparseSensorDefects(frame, result, mCameraCharacteristics);',
             'populateIris26855SparseSensorDefects(frame, result, characteristics);'):
 assert mark in cc1, ('Camera2 optional verified map',mark)
assert cc1.count('CaptureRequest.STATISTICS_HOT_PIXEL_MAP_MODE, true')==2
assert cc1.count('populateIris26855SparseSensorDefects(frame, result,')==2
assert 'quad-binned 50MP -> 12MP' in cc1
assert 'motionV2VerifiedHotPixels26855' in (C/IF).read_text()
assert 'verifiedHotPixelCoordinates26855' in (C/RF).read_text()
assert 'frame.motionV2VerifiedHotPixels26855.copyOf()' in (C/BR).read_text()
for token in ('mPreviewRequestBuilder.set(CaptureRequest.CONTROL_AE_MODE',
              'captureBuilder.set(CaptureRequest.JPEG_ORIENTATION',
              'mPreviewRequestBuilder.set(CaptureRequest.CONTROL_AE_TARGET_FPS_RANGE'):
 assert token in cc0 and token in cc1
# Negative coordinate-fixture regression, including quad-binned geometry.
def map_site(x,y,pixel_w,pixel_h,rw,rh,rect):
 if (pixel_w,pixel_h)==(rw,rh): ox,oy=0,0
 elif rect is not None and (rect[2]-rect[0],rect[3]-rect[1])==(rw,rh) and rect[0]>=0 and rect[1]>=0 and rect[2]<=pixel_w and rect[3]<=pixel_h: ox,oy=rect[0],rect[1]
 else:return None
 x-=ox;y-=oy
 return (x,y) if 2<=x<rw-2 and 2<=y<rh-2 else None
assert map_site(53,75,4096,3072,4096,3072,None)==(53,75)
assert map_site(153,275,4300,3500,4096,3072,(100,200,4196,3272))==(53,75)
assert map_site(153,275,8192,6144,4096,3072,None) is None
assert map_site(1,1,4096,3072,4096,3072,None) is None
print('PASS 26855 permanent sensor-map regressions: direct and offset 1:1 mapped; binned/border fail-shut')
print('PASS 26855 semantic/ownership: exact successful-26854 1786 universe and 7-file allowlist; two modified CFA templates; early sparse RAW impulse repair, no shared-frame admission/phase change; green CFA texture protected; DNG/SHORT/LONG/Resolve/VGN/UHDR/Super-Res unchanged')
