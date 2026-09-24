#!/usr/bin/env python3
from pathlib import Path
import hashlib, sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26698.py BASE26697 CANDIDATE')
b=Path(sys.argv[1]); c=Path(sys.argv[2]); pkg=Path(__file__).resolve().parent
def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def H(root): return {'app/'+str(p.relative_to(root/'app')):h(p) for p in sorted((root/'app').rglob('*')) if p.is_file()}
def t(rel): return (c/rel).read_text()
B=H(b); C=H(c); exp=[x.strip() for x in (pkg/'26698_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x.strip()]
changed=sorted(k for k in set(B)|set(C) if B.get(k)!=C.get(k))
assert len(B)==len(C)==1823,(len(B),len(C)); assert changed==sorted(exp),(changed,exp); assert len(changed)==6
assert not [x for x in (pkg/'26698_ADDED_PATHS_MUST_BE_ABSENT.txt').read_text().splitlines() if x.strip()]
# exact manifest proof
for name,root in [('26698_BASE_26697_FULL_APP.sha256',b),('26698_EXPECTED_CANDIDATE_FULL_APP.sha256',c)]:
 for line in (pkg/name).read_text().splitlines():
  if not line.strip(): continue
  hh,rel=line.split(None,1); assert h(root/rel.strip())==hh,(name,rel)
# protected equality
for rel in B:
 if rel not in exp: assert B[rel]==C[rel],rel
# no shaders modified
SB={k:v for k,v in B.items() if k.startswith('app/src/main/assets/shaders/')}; SC={k:v for k,v in C.items() if k.startswith('app/src/main/assets/shaders/')}
assert len(SB)==271 and SB==SC
# StageTelemetry is pass-through with no active image-stat work and explicit completion boundary
stage=t('app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/StageTelemetry.java'); run=stage[stage.index('public void Run()'):]
assert 'IRIS_26698_STAGE_TELEMETRY_IMAGE_WORK_DISABLED' in run
assert 'histogram.Compute' not in run and 'chromaOriginStats(source)' not in run and 'glFinish()' in run
# Sabre production owners preserved; proof call sites retired
sabre=t('app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
for name in ('logSabreUniversalFusionDecision26651','logSabreUniversalFusionRadiance26651','logSabreExtendedHdrProbe26605'):
 assert sabre.count(name)==1,(name,sabre.count(name))
for token in ('renderSabreDehomogenize(','countSabreShortRestoreMaskFull26595(','readSabreRgb16(','renderSabreNormalMasterShortFusion26651('): assert token in sabre,token
for marker in ('IRIS_26698_LONG_FINAL_WEIGHT_PROOF_DISABLED','IRIS_26698_FUSION_DECISION_READBACK_DISABLED','IRIS_26698_FUSION_RADIANCE_PROBE_DISABLED','IRIS_26698_HDR_PROBE_DISABLED stage=FLOAT_HDR_HANDOFF_PRE_VGN','IRIS_26698_HDR_PROBE_DISABLED stage=POST_VGN_HDR_MASTER'): assert marker in sabre,marker
# post-save decodes no longer execute
img=t('app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java'); m0=img.index('private static void iris26642ScheduleUltraHdrDecodeProof'); m1=img.index('public static boolean saveBitmapAsJPG',m0); method=img[m0:m1]
assert 'decodeFile' not in method and 'execute(' not in method and 'newSingleThreadExecutor' not in img
hdr=t('app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java'); blk=hdr[hdr.index('IRIS_26698_FINAL_DIMENSION_DECODE_PROOF_DISABLED'):hdr.index('processingEventsListener.notifyImageSavedStatus')]
assert 'decodeFile' not in blk and 'BitmapFactory' not in blk
heic=t('app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHeicUltraHdrEncoder.java')
assert 'boolean ok = writeNative(' in heic and 'boolean saved = writeSuperResGridNative(' in heic
assert heic.count('iris26646VerifyPlatformReadback(')==1
# version
ver=t('app/version.properties'); assert 'VERSION_NAME=0.9726698' in ver and 'VERSION_BUILD=26698' in ver
print('PASS validate 26698: exact 6-file cleanup scope, 1817 protected, production owners preserved, 271 shaders invariant')
