#!/usr/bin/env python3
"""26969 fail-closed source and B-off ownership regressions; based exclusively on successful 26968 manifest."""
import pathlib,sys,hashlib,re
R=pathlib.Path(__file__).resolve().parent
payload='--payload' in sys.argv
root=R/'handoff_payload_26969' if payload else R
parse=lambda p:dict((path,h) for h,path in (line.split('  ',1) for line in (R/p).read_text().splitlines()))
base=parse('26969_BASE_26968_FULL_APP.sha256');after=parse('26969_EXPECTED_FULL_APP.sha256')
changed=set((R/'26969_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines())
added=set((R/'26969_ADDED_RUNTIME_PATHS.txt').read_text().splitlines())
assert (len(base),len(after),len(changed),len(added))==(2055,2059,10,4)
assert not set((R/'26969_DELETED_RUNTIME_PATHS.txt').read_text().splitlines())
assert added==set(after)-set(base)
assert changed=={p for p in base if p in after and base[p]!=after[p]}
assert {p:h for p,h in base.items() if p not in changed}==parse('26969_PROTECTED_SOURCE.sha256')
assert all(p.endswith(('.kt','.java','.properties')) for p in added|changed)
for path in changed|added:
 p=root/path
 assert p.is_file(),path
 assert hashlib.sha256(p.read_bytes()).hexdigest()==after[path],path
if not payload:
 paths={p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in [*list((root/'app/src').rglob('*')),root/'app/build.gradle',root/'app/version.properties'] if p.is_file()}
 assert paths==after,'26969 compiled source deviates from sealed 2059-file candidate'
shader=(root/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26870PostAmazeChroma.kt').read_text()
stack=(root/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
controller=(root/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text()
for a in ('IRIS_26969_B_OFF_HDRQ_NEIGHBOUR_LUMA_CHROMA_NOISE_EVENING','vec3 iris26969Even','uIris26969NoiseVariance','if(uIris26924BOff!=0)','sourceRgb=iris26969Even(p,sourceRgb)'):
 assert a in shader,a
for a in ('GlesIris26969HdrqNoiseEven.measure','uIris26969NoiseEven','iris26969HdrqBOff','rawrNativeReceipt26864 != null','createTexture'):
 assert a in stack,a
for a in ('iris26969DriveAeFromExactRawResult','iris26969AuditAeResult','Iris26969RawrAeLoop','Iris26969RawrAeMath.DEFAULT_MAX_STILL_SHUTTER_NS','iris26969RawrAeSelected','mZslResultMap','iris26969PhotoDigitalGainAt','recordMotion26662PreviewProtection'):
 assert a in controller,a
assert 'mIris26909ManualActive' in controller and 'mIsRecordingVideo' in controller
for p in ('app/src/main/java/com/particlesdevs/photoncamera/capture/Iris26969RawrAeMath.java','app/src/main/java/com/particlesdevs/photoncamera/capture/Iris26969RawrAeMetering.java','app/src/main/java/com/particlesdevs/photoncamera/capture/Iris26969RawrAeLoop.java'):
 assert '26969' in (root/p).read_text()
assert 'VERSION_BUILD=26969' in (root/'app/version.properties').read_text()
assert 'VERSION_NAME=0.9726969' in (root/'app/version.properties').read_text()
assert all('app/src/main/cpp/' not in p and 'app/src/main/jniLibs/' not in p and 'app/src/main/assets/' not in p for p in changed|added)
print('PASS 26969 exact 2055->2059 scope 10 changed/4 added/2045 protected, B OFF shader/AE ownership, no native/vendor changes')
