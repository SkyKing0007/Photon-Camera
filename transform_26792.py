#!/usr/bin/env python3
from pathlib import Path
import hashlib, shutil, sys
if len(sys.argv) != 4: raise SystemExit('usage: transform_26792.py BASE_ROOT CANDIDATE_ROOT PAYLOAD_ROOT')
BASE, OUT, PAYLOAD = map(Path, sys.argv[1:])
ALLOW = [
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java',
'app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/assets/shaders/motionv2/gainmap.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java',
'app/src/main/res/xml/preferences.xml',
'app/src/main/res/values/strings.xml',
'app/src/main/res/values/default_prefs.xml',
'app/version.properties',
]
PRIOR = {
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt':'6e4778566c872febe7f857c7dce522439059f4416b717965a3c31b15110989be',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt':'b73d0f8b924314160b56091a569c5e639710a9fa7dfbd35dc90009090b9d4ccf',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java':'d1dbacb177c3f0f7cab6166ec9f497d0128056760f4d0a05ae1ead34c2ea6e42',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt':'5b3e0c9214da4e5d139919f12c695e7b7f26f0a9883946ebb8a889b551aabb45',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java':'b0005e2c64b8efedcbaa0a60c47598d8619e027cc819deb15fb10b9b87f448fa',
'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java':'2bf72de7f231cd4496374d4830d51f79886aef4cb3817551993a4c890830e2df',
'app/src/main/assets/shaders/motionv2/render.glsl':'739776e781e119d770f6434e0a59b51cd59553dd9ba72c27d56ac689a014646e',
'app/src/main/assets/shaders/motionv2/gainmap.glsl':'6ce314085982d412e5212ae86ac7bbc619bf50eb616d91174099a1cbb299a710',
'app/src/main/java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java':'f407b87a0ec39c1ca9b647090f41e8d2620359b8133ca1e9592a6d34177a0d87',
'app/src/main/res/xml/preferences.xml':'6fdc5043b655764033c9373fa55ae0462d01c354f8f9ced0cb69392340d8a1a2',
'app/src/main/res/values/strings.xml':'fb739abbfaf188426f182a92d9c5033bdfb05f99a1caa6ea14ee7c9428d80e98',
'app/src/main/res/values/default_prefs.xml':'baac958e65a92bfed5f275ddda1a456d887c8d106cdba94a80c34569a86c453d',
'app/version.properties':'e6137ad917219dafcfc3a6912b84cbaf196bc89f92bf92bc46e375a2f31098d3',
}
EXPECTED = {
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt':'6918f5ed69b813cf3fb2602c041b31682d414c5418d3240f7dcad4122423a0cf',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt':'e082d4c8f51454b8a8578bf124992a9b3f807a0af634a5533645bf836bf4d2e0',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java':'e334b54fbb079f27af6da2f0cca239867a9113d2a45bb1aa1fb65fd75051f1b7',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt':'06ae8fada422c9589ecd459d1fda78095d940ce5fcbaa559ee8772d85e00ddba',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java':'5333e4316b0b96aaa56b153bb962e56b3d94c66211b6be91a561bed26ae488a8',
'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java':'c617294f8efe14c1da8779858b47ad078a649d0b2506306573fa3e6738729019',
'app/src/main/assets/shaders/motionv2/render.glsl':'f2146c6862795054dcfda40dbaa9dceef6fcac37801ca4bdd3619eddc540c316',
'app/src/main/assets/shaders/motionv2/gainmap.glsl':'45a2cc6f9fd821e3a9873bf3a25595024fd98a4fddde930ca0c9cf9b6520d405',
'app/src/main/java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java':'fb378b9c9dce0f44fb28ba9e70e3726f799cd48ff6ef31b1f3ee3bc1ed0e643a',
'app/src/main/res/xml/preferences.xml':'831c12354d80ff0083f31cf8be39d4c80189d0e7fb1b1839de3770eca2eb496e',
'app/src/main/res/values/strings.xml':'db0d5e8adfb563b2e12259053eded0780fae318bb6ec435a0537a9b4463b2ff4',
'app/src/main/res/values/default_prefs.xml':'5ea5ada5527f966f3cd78e184de84cb07f480fcd54fa415a2dacccf1d1a5152d',
'app/version.properties':'5893f7d56b88e4f48ce661f7de4929e54c6f662426364ee21b3c0f1c28b5f1d9',
}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
base_files = sorted(str(p.relative_to(BASE)) for p in (BASE/'app').rglob('*') if p.is_file())
if len(base_files) != 1779: raise SystemExit(f'base file count {len(base_files)} != 1779')
payload_files = sorted(str(p.relative_to(PAYLOAD)) for p in PAYLOAD.rglob('*') if p.is_file())
if payload_files != sorted(ALLOW): raise SystemExit(f'payload allowlist mismatch: {payload_files}')
for rel,h in PRIOR.items():
    if sha(BASE/rel) != h: raise SystemExit(f'26791 prior hash mismatch: {rel}')
for rel,h in EXPECTED.items():
    if sha(PAYLOAD/rel) != h: raise SystemExit(f'26792 payload hash mismatch: {rel}')
if OUT.exists(): shutil.rmtree(OUT)
shutil.copytree(BASE, OUT)
for rel in ALLOW:
    (OUT/rel).parent.mkdir(parents=True,exist_ok=True)
    (OUT/rel).write_bytes((PAYLOAD/rel).read_bytes())
    if sha(OUT/rel) != EXPECTED[rel]: raise SystemExit(f'candidate output mismatch: {rel}')
out_files = sorted(str(p.relative_to(OUT)) for p in (OUT/'app').rglob('*') if p.is_file())
if out_files != base_files: raise SystemExit('candidate file universe changed')
print('PASS 26792 deterministic authority-seeded candidate reconstruction: 1779 files; exact 13-file payload overlay')
