#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,re
from pathlib import Path
HERE=Path(__file__).resolve().parent
EXPECTED=[x.strip() for x in (HERE/'26538_RUNTIME_FILES.txt').read_text().splitlines() if x.strip()]
def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def manifest(root):
 d={}
 for p in (root/'app/src/main').rglob('*'):
  if p.is_file(): d[str(p.relative_to(root))]=h(p)
 return d
def need(t,x,n):
 if x not in t: raise SystemExit(f'26538 contract missing {n}: {x}')
def forbid(t,x,n):
 if x in t: raise SystemExit(f'26538 forbidden {n}: {x}')
def validate(base:Path,cand:Path):
 mb,mc=manifest(base),manifest(cand); changed=sorted(k for k in set(mb)|set(mc) if mb.get(k)!=mc.get(k))
 if changed!=EXPECTED: raise SystemExit('26538 changed-file allowlist mismatch: '+repr(changed))
 post=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java').read_text()
 inp=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/IrisNightRgbInput.java').read_text()
 night=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java').read_text()
 bridge=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
 motion_in=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2CfaInput.java').read_text()
 render=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text()
 jin=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightNeuralEnhancer.java').read_text()
 glbase=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLBasePipeline.java').read_text()
 # Dedicated Night input and graph.
 need(post,'public ByteBuffer irisNightRgba16f;','dedicated Night half carrier')
 need(post,'IRIS_26538_NIGHT_SPATIAL_RGB_POST_ENTRY carrier=RGBA16F','Night half-float post entry')
 block=post[post.index('if(mParameters.irisNightActive){'):post.index('/* IRIS_26534_MOTION_RCD_DETOUR_FORBIDDEN */')]
 need(block,'new IrisNightRgbInput()','dedicated Night input node')
 forbid(block,'new MotionV2CfaInput()','Motion FLOAT32 input in Night graph')
 for x in ('ExposureFusion','ESD3D','AutoExposure','new Initial(','Pyramid','DemosaicQUAD','Demosaic3','MotionV2ViewfinderExposureMatcher'):
  forbid(block,x,'legacy/incorrect Night node')
 for x in ('MotionV2MgcSourceExposure','MotionV2HighlightChromaReliability','MotionV2ColorTransform','MotionV2DisplayExposure','MotionV2Render'):
  need(block,x,'validated shared RGB primitive')
 # Two-buffer contract: input uploads RGBA16F, allocates main1/main2, no third allocation.
 need(inp,'GLFormat.DataType.FLOAT_16, 4','RGBA16F upload')
 need(inp,'basePipeline.main1 = new GLTexture','main1 allocation')
 need(inp,'basePipeline.main2 = new GLTexture','main2 allocation')
 need(inp,'basePipeline.main3 = null','explicit no-main3 contract')
 forbid(inp,'basePipeline.main3 = new GLTexture','main3 allocation')
 need(inp,'float32Expansion=false rcd=false demosaic=false photonNight=false','no FLOAT32/legacy route telemetry')
 need(glbase,'if(texnum == 1)','two-buffer getMain selector')
 need(glbase,'return main2;','main2 getMain path')
 need(glbase,'return main1;','main1 getMain path')
 # Active Night nodes after input do not consume main3/swap3.
 active=['MotionV2MgcSourceExposure.java','MotionV2HighlightChromaReliability.java','MotionV2ColorTransform.java','MotionV2DisplayExposure.java','MotionV2Render.java','StageTelemetry.java','RotateWatermark.java']
 pd=cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline'
 for f in active:
  t=(pd/f).read_text(); forbid(t,'swap3()','active Night swap3 in '+f); forbid(t,'basePipeline.main3','active Night main3 in '+f)
 # MGC keeps Motion FLOAT32 but transfers native half carrier only for Night.
 need(bridge,'IRIS_26538_NIGHT_NATIVE_RGBA16F_HANDOFF','native Night half handoff')
 need(bridge,'val nightNativeHalfCarrier = parameters.irisNightActive','Night-only carrier switch')
 need(bridge,'halfBuffer = null // ownership transfers to the returned Night result','half carrier ownership transfer')
 need(bridge,'convertHalfRgbaToFloatRgba(denoiseBuffer, size.x, size.y)','Motion FLOAT32 conversion retained')
 need(motion_in,'GLFormat.DataType.FLOAT_32, 4','Motion FLOAT32 contract retained')
 # Hdrx expects half-float bytes and releases them before Jin.
 need(night,'4L*2L','Night expected 2-byte channels')
 need(night,'jpegCarrier=MGC_SPATIAL_RGB_RGBA16F','Night production half carrier')
 need(night,'IRIS_26538_NIGHT_RGBA16F_CARRIER_RELEASED_BEFORE_JIN','half carrier release before Jin')
 need(night,'img=IrisNightNeuralEnhancer.enhanceInPlace(img);','Jin after release')
 # Luma: 26537 evidence gates remain, but native calibrated sigma scale is no longer artificially capped at .45/.30.
 need(bridge,'val lumaSnrRisk = ((24f - referenceSnr!!) / 20f)','source-SNR activation')
 need(bridge,'val lumaSupportRisk = ((7f - noiseEquivalentSupport) / 5f)','effective-support activation')
 need(bridge,'val lowLightDemand =','low-light demand')
 need(bridge,'requestedLumaScale * lowLightDemand','native Pecan sigma admission')
 need(bridge,'nativePecanSigmaScale=true','native-scale telemetry')
 need(bridge,'tuningSnr = tuningSnr!!','propagated post-merge tuning authority')
 forbid(bridge,'adaptiveLowLightFloor','rejected 26537 tiny luma floor')
 forbid(bridge,'userLumaContribution','rejected 26537 quarter-scale user luma')
 need(bridge,'textureClassifier=false','no flat-area classifier')
 # Existing no-fallback + Jin lifecycle remain locked and unchanged.
 need(render,'IRIS_26537_NIGHT_ULTRAHDR_DEFERRED','pre-Jin Night UHDR still disabled')
 need(jin,'env.createSession(model.getAbsolutePath(),opts)','file-backed Jin retained')
 need(jin,'opts.setMemoryPatternOptimization(false)','Jin bounded-memory option retained')
 need(jin,'opts.setCPUArenaAllocator(false)','Jin CPU arena disabled')
 for x in ('photonFallback=false','adrcFallback=false','singleFrameFallback=false'): need(jin,x,'no old fallback')
 print('PASS: 26538 dedicated RGBA16F Night input + two-buffer post graph proven')
 print('PASS: 26538 Motion FLOAT32 path unchanged; no Night main3/RCD/demosaic/old Photon route')
 print('PASS: 26538 native-scale Pecan luma admission uses source SNR + noise-equivalent support')
 print('PASS: 26538 exact changed files='+str(len(changed)))
def self_test():
 assert len(EXPECTED)==4 and EXPECTED==sorted(EXPECTED) and len(set(EXPECTED))==4
 print('PASS: 26538 validator self-test inventory and contracts loaded')
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--base'); ap.add_argument('--candidate'); ap.add_argument('--self-test',action='store_true'); a=ap.parse_args()
 if a.self_test: self_test(); return
 if not a.base or not a.candidate: ap.error('--base and --candidate required')
 validate(Path(a.base).resolve(),Path(a.candidate).resolve())
if __name__=='__main__': main()
