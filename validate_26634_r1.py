#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26634_r1.py BASE CANDIDATE')
base=Path(sys.argv[1]); cand=Path(sys.argv[2]); root=Path(__file__).resolve().parent
changed=[x for x in (root/'R1_26634_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
expected={
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/hinnka/mycamera/raw/MgcFullResolutionDenoise.kt',
'app/src/main/java/com/particlesdevs/photoncamera/api/ParseExif.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightProcessor.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/particlesdevs/photoncamera/util/Log.java','app/version.properties'}
assert set(changed)==expected and len(changed)==8

def H(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def files(r): return {str(p.relative_to(r)):H(p) for p in sorted((r/'app').rglob('*')) if p.is_file()}
b=files(base); c=files(cand)
assert len(b)==1713==len(c), (len(b),len(c))
actual={p for p in b if b[p]!=c[p]} | (set(b)^set(c))
assert actual==expected, sorted(actual^expected)
# exact candidate manifest
for line in (root/'R1_26634_EXPECTED_CANDIDATE_FULL_APP.sha256').read_text().splitlines():
    d,rel=line.split('  ',1); assert H(cand/rel)==d, rel
# version
v=(cand/'app/version.properties').read_text(); assert 'VERSION_NAME=0.9726634' in v and 'VERSION_BUILD=26634' in v
# local residual-noise owner
s=(cand/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
for token in ['IRIS_26634_LOCAL_RESIDUAL_NOISE_SUPPORT','readSabreResidualNoiseSupport','coerceIn(0.75f, 1.0f)','coerceIn(192, 256)','mgcSpatialStrengthMap = sabreResidualStrengthMap26634']:
    assert token in s, token
assert 'readSabreAverageMergeFactor(' not in s
m=(cand/'app/src/main/java/com/hinnka/mycamera/raw/MgcFullResolutionDenoise.kt').read_text()
assert 'useSpatialModel || useSabreModel' in m and 'IRIS_26634_LOCAL_RESIDUAL_NOISE_SUPPORT' in m
br=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
for token in ['IRIS_26634_LOCAL_RESIDUAL_NOISE_SUPPORT','in 192..256','mgcSpatialStrengthMap']:
    assert token in br, token
# preserve 26633 bounded luma owner / no increase in its maximum
assert '0.35f * supportGate26633' in br
# lifecycle persistence retired, normal file log remains
lg=(cand/'app/src/main/java/com/particlesdevs/photoncamera/util/Log.java').read_text()
for forbidden in ['new java.io.File(app.getFilesDir(), "iris-process-lifecycle")','getFD().sync()','mirrorPrivateProcessLogs()','setProcessStateSummary(state)']:
    assert forbidden not in lg, forbidden
for keep in ['writeToFile(', 'getLogFolderDocumentFile', 'log-']:
    assert keep in lg, keep
assert re.search(r'public static void critical\(String tag, String message\)\s*\{\s*i\(tag, message\);\s*\}',lg,re.S)
# EXIF debug payload removed, photographic fields preserved
hx=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java').read_text(); nx=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightProcessor.java').read_text(); px=(cand/'app/src/main/java/com/particlesdevs/photoncamera/api/ParseExif.java').read_text()
assert 'exifData.IMAGE_DESCRIPTION = null;' in hx
assert 'exif.IMAGE_DESCRIPTION = null;' in nx
for keep in ['TAG_PHOTOGRAPHIC_SENSITIVITY','TAG_F_NUMBER','TAG_FOCAL_LENGTH','TAG_EXPOSURE_TIME','TAG_DATETIME','TAG_MAKE','TAG_MODEL']:
    assert keep in px, keep
for cleared in ['TAG_IMAGE_DESCRIPTION, null','TAG_COPYRIGHT, null','TAG_SENSITIVITY_TYPE, null','TAG_APERTURE_VALUE, null','TAG_COMPRESSION, null','TAG_COLOR_SPACE, null','TAG_EXIF_VERSION, null']:
    assert cleared in px, cleared
# no modified shader/native/DNG/UHDR owner by exact changed path domain
assert not any('/assets/shaders/' in x or x.endswith('.glsl') for x in changed)
assert not any('/cpp/' in x for x in changed)
assert not any('Dng' in x or 'dng' in x for x in changed)
assert not any('UltraHdr' in x or 'GainMap' in x or 'ultrahdr' in x.lower() for x in changed)
print('PASS 26634 semantics: bounded local Sabre residual variance + lifecycle/EXIF cleanup; 8-file exact scope')
