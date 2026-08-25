#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent
EXPECTED=[x.strip() for x in (HERE/'26539_RUNTIME_FILES.txt').read_text().splitlines() if x.strip()]
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def manifest(root):
 d={}
 for p in (root/'app/src/main').rglob('*'):
  if p.is_file(): d[str(p.relative_to(root))]=h(p)
 return d
def need(t,x,n):
 if x not in t: raise SystemExit(f'26539 contract missing {n}: {x}')
def forbid(t,x,n):
 if x in t: raise SystemExit(f'26539 forbidden {n}: {x}')
def validate(base:Path,cand:Path):
 mb,mc=manifest(base),manifest(cand); changed=sorted(k for k in set(mb)|set(mc) if mb.get(k)!=mc.get(k))
 if changed!=EXPECTED: raise SystemExit('26539 changed-file allowlist mismatch: '+repr(changed))
 post=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java').read_text()
 night=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java').read_text()
 bridge=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
 saver=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java').read_text()
 jin=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightNeuralEnhancer.java').read_text()
 inp=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/IrisNightRgbInput.java').read_text()
 motion=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2CfaInput.java').read_text()
 # Night remains separate capture/reconstruction/post input.
 need(post,'new IrisNightRgbInput()','Night-specific input')
 forbid(post[post.index('if(mParameters.irisNightActive){'):post.index('/* IRIS_26534_MOTION_RCD_DETOUR_FORBIDDEN */')],'new MotionV2CfaInput()','Motion input in Night graph')
 need(inp,'basePipeline.main3 = null','Night two-buffer contract retained')
 need(motion,'GLFormat.DataType.FLOAT_32, 4','Motion FLOAT32 contract unchanged')
 # Night lifecycle owner must self-close before caller can enter Jin.
 need(post,'IRIS_26539_NIGHT_POST_OWNER_CLOSE_BEFORE_JIN','Night post lifecycle ownership')
 need(post,'irisNightRgba16f = null;','Night carrier reference clear')
 need(post,'try { close(); }','Night EGL/Post owner close')
 need(post,'IRIS_26539_NIGHT_POST_OWNER_CLOSED beforeJin=true','close telemetry')
 need(night,'finally {\n            try{Allocator.free(rgb);}','carrier release in finally')
 need(night,'postOwnerAlreadyClosed=true','caller close proof telemetry')
 # Base publication before native Jin, then atomic Night-owned final replace.
 base_pos=night.index('saveBitmapAsJPGIrisNightCheckpoint')
 jin_pos=night.index('IrisNightNeuralEnhancer.enhanceInPlace')
 final_pos=night.index('saveBitmapAsJPGIrisNightAtomicFinal')
 if not base_pos < jin_pos < final_pos: raise SystemExit('26539 Night save/Jin ordering invalid')
 forbid(night[night.index('private void ApplyIrisNight26533()'):night.index('private void ApplyHdrX()')],'saveBitmapAsJPGMotionV2(','Motion publication policy in Night owner')
 need(night,'IRIS_26539_NIGHT_PUBLICATION_OWNERSHIP','Night publication telemetry')
 need(night,'final boolean imageSaved=iris26539FinalSaved||iris26539BaseSaved;','base survival authority')
 need(saver,'saveBitmapAsJPGIrisNightCheckpoint','Night base encoder')
 need(saver,'saveBitmapAsJPGIrisNightAtomicFinal','Night atomic final encoder')
 need(saver,'StandardCopyOption.ATOMIC_MOVE','atomic final replacement')
 need(saver,'IRIS_26539_NIGHT_BASE_EXIF_NONFATAL','EXIF nonfatal after valid JPEG')
 need(saver,'MotionV2Jpeg444Encoder.write(fileToSave, img, jpgQuality)','stateless 444 codec reuse only')
 need(saver,'encodeIrisNightJpegPortable','Night portable codec owner')
 need(saver,'Bitmap.CompressFormat.JPEG','standard Android JPEG codec fallback')
 owned=saver[saver.index('IRIS_26539_NIGHT_OWNED_JPEG444'):saver.index('IRIS_26432_MOTION_V2_DIRECT_GAINMAP_JPEG')]
 forbid(owned,'UltraHdrSaver','UltraHDR saver in Night-owned publication')
 # Jin remains file-backed CPU optional finishing.
 need(jin,'env.createSession(model.getAbsolutePath(),opts)','file-backed Jin')
 need(jin,'opts.setCPUArenaAllocator(false)','bounded CPU session')
 need(jin,'singleFrameFallback=false','no single-frame fallback')
 # Luma: independent auto floor in native Pecan sigma domain; slider no longer gates it.
 need(bridge,'IRIS_26539_AUTOMATIC_PECAN_LUMA_FLOOR','automatic Pecan floor')
 need(bridge,'val automaticLowLightLuma = if (irisSettings.noiseReductionEnabled)','auto floor master')
 need(bridge,'val userLumaScale = if (irisSettings.noiseReductionEnabled)','independent user luma')
 need(bridge,'maxOf(automaticLowLightLuma, userLumaScale).coerceIn(0f, 1.5f)','max auto/user authority')
 forbid(bridge,'requestedLumaScale * lowLightDemand','26538 slider-times-demand zeroing')
 need(bridge,'tuningSnr = tuningSnr!!','post-merge Pecan tuning authority')
 need(bridge,'lumaSnrSource=referencePreMerge','premerge activation authority')
 need(bridge,'textureClassifier=false','no flat-area classifier')
 print('PASS: 26539 Night owns EGL lifecycle and clears carrier before Jin')
 print('PASS: 26539 commits portable Night JPEG base before Jin and atomically replaces final')
 print('PASS: 26539 automatic native-Pecan luma floor is independent of slider=0')
 print('PASS: 26539 exact changed files='+str(len(changed)))
def self_test():
 assert len(EXPECTED)==4 and EXPECTED==sorted(EXPECTED) and len(set(EXPECTED))==4
 print('PASS: 26539 validator self-test inventory/contracts loaded')
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--base'); ap.add_argument('--candidate'); ap.add_argument('--self-test',action='store_true'); a=ap.parse_args()
 if a.self_test:self_test();return
 if not a.base or not a.candidate:ap.error('--base and --candidate required')
 validate(Path(a.base).resolve(),Path(a.candidate).resolve())
if __name__=='__main__':main()
