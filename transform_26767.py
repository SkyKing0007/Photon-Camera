#!/usr/bin/env python3
from pathlib import Path
import shutil,sys,hashlib
if len(sys.argv)!=4: raise SystemExit('usage: transform_26767.py BASE OUT PAYLOAD')
base,out,payload=map(Path,sys.argv[1:])
expected=['app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt', 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt', 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java', 'app/src/main/java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java', 'app/src/main/java/com/particlesdevs/photoncamera/ui/settings/SettingsActivity.java', 'app/src/main/res/xml/preferences.xml', 'app/src/main/res/values/strings.xml', 'app/src/main/res/values/default_prefs.xml', 'app/version.properties']
prior={'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt': 'c2434cbeeaeeb266c83f39ef5cb58b6271718c927da3f47f59dc8de3b4e6a757', 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt': '7e3eececd4add6b3dce3e3498926f0ae55d81a6c2ef135f006ac22026f174be5', 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java': 'b1dd7e060c1dc96860198dfa0b0c4f6a9744f6e5db76363f99bff5e7d4cedba2', 'app/src/main/java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java': 'c86d19a86f86a165e41585e2d27f403ea91083a706e87c93b77600661247d23f', 'app/src/main/java/com/particlesdevs/photoncamera/ui/settings/SettingsActivity.java': 'fed7483ccf69ecf9aa53326088d0630bba5d8e3633a672d466a77e470225cdb3', 'app/src/main/res/xml/preferences.xml': 'a57ff1606d4fc6bcdcbc08adc13767d69887996a06dfad041c8b6363f5bfc8c1', 'app/src/main/res/values/strings.xml': 'e4522f820b25876e22c7b719a4429f145b83a439e16638485cf04ea1bb796b6f', 'app/src/main/res/values/default_prefs.xml': '867230d90ea5415f8b93894a2d8d8ac8622c3e1e0d55a6b2ecf09ec865005da2', 'app/version.properties': 'bbd6274afe660155cc0824e2f353d39b820a3d2046a60dc115095ef3754d98d9'}
if out.exists(): shutil.rmtree(out)
shutil.copytree(base,out)
for rel in expected:
 p=base/rel; got=hashlib.sha256(p.read_bytes()).hexdigest(); assert got==prior[rel],f'26766 prior hash mismatch {rel}: {got}'
 src=payload/rel; assert src.is_file(),f'missing payload {rel}'
 dst=out/rel; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
def H(root): return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'app').rglob('*') if p.is_file()}
a,b=H(base),H(out); assert len(a)==len(b)==1823
changed=sorted(k for k in set(a)|set(b) if a.get(k)!=b.get(k)); assert changed==sorted(expected),(changed,expected)
print('PASS 26767 deterministic candidate transform; exact 9-file runtime allowlist')
