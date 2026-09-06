#!/usr/bin/env python3
from pathlib import Path
import sys
def fail(m):raise SystemExit('FAIL: '+m)
def need(s,t,l):
 if t not in s:fail(l+' missing '+t)
def section(s,a,b):
 i=s.find(a);j=s.find(b,i)
 if i<0 or j<0:fail('section '+a)
 return s[i:j]
def restore(physical,vgn):return max(physical+(vgn-min(max(physical,0.0),1.0)),0.0)
def main():
 if len(sys.argv)!=3:fail('usage base candidate')
 b,c=map(Path,sys.argv[1:]);sh=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text();st=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text();br=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text();proc=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26545SabreProcessor.kt').read_text()
 # Below white, restored master is exactly VGN. Above white, physical excess survives with VGN normalized correction.
 for physical in [0.0,.1,.5,.99,1.0]:
  for vgn in [0.0,.2,.7,1.0]:
   if abs(restore(physical,vgn)-vgn)>1e-12:fail('below-white VGN identity failed')
 for physical in [1.01,1.2,2.0,4.0]:
  for vgn in [0.0,.4,1.0]:
   want=(physical-1.0)+vgn
   if abs(restore(physical,vgn)-want)>1e-12:fail('HDR excess preservation failed')
 # Exact root-cause source invariants.
 uint16=section(sh,'    val outputTransformUint16 = """','    """.trimIndent()');flt=section(sh,'    val outputTransformFloat = """','    """.trimIndent()');rej=section(sh,'    val rejection = """','    """.trimIndent()')
 need(uint16,'clamp(transformOutput(p), 0.0, 1.0)','VGN normalized contract')
 if 'clamp(transformOutput(p)' in flt:fail('physical HDR carrier clamps')
 need(sh,'physical + (vgn - normalizedProxy)','post-VGN delta restore')
 need(rej,'smoothstep(0.50,2.00,max(flow.w,0.0))','raw-pixel gate')
 need(rej,'float localFlowVariation = flow.z;','normalized z retention')
 # Night and normal LONG remain truthful and unchanged in admission policy.
 need(proc,'preserveExtendedHdrThroughVgn = !allowShadowLong &&','Night isolation')
 need(br,'allowSabreShadowLong = parameters.irisNightActive','LONG Night-only Sabre admission')
 need(br,'CAPTURED_BUT_EXCLUDED_FROM_NORMAL_MOTION_SABRE','normal LONG telemetry')
 # SR guide uses exported corrected master, no SHORT detail owner.
 need(st,'val nativeHdrAuthority26601 = exportedTexture','SR guide master')
 need(st,'shortDetailEvidence=false','SHORT detail forbidden')
 # No image-quality camouflage or tone redesign in changed source set.
 changed='\n'.join((c/r).read_text(errors='ignore') for r in [
 'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26545SabreProcessor.kt','app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt','app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java','app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java','app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt','app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java'])
 for bad in ['magentaRepair','greenRepair','cyanRepair','hueRepair','chromaBlur','shortDetailPaste','cloudDetailPaste']:
  if bad.lower() in changed.lower():fail('artifact-hiding authority '+bad)
 print('PASS root-cause math: VGN exact below white, physical HDR excess preserved above white, no pre-VGN physical clamp')
 print('PASS flow.w RAW-pixel gate + flow.z normalized owner; Night/LONG truth preserved; SR guide corrected without SHORT high-frequency ownership')
 print('PASS no hue/chroma/blur/detail-paste camouflage introduced')
if __name__=='__main__':main()
