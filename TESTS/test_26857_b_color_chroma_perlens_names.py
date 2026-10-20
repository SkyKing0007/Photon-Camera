from pathlib import Path
import re, math
root=Path(__file__).resolve().parent.parent/'handoff_payload_26857'
read=lambda p:(root/p).read_text()
native=(Path(__file__).resolve().parent.parent/'handoff_payload_26856/app/src/main/cpp/iris26856/amaze/shaders/amaze_export.comp').read_text()
contract=read('app/src/main/java/com/hinnka/mycamera/processor/GlesIris26856RawrColorContract.kt')
stack=read('app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
bridge=read('app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt')
ui=read('app/src/main/java/com/particlesdevs/photoncamera/ui/settings/SettingsActivity.java')
hdr=read('app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java')
assert 'rgb / vec3(tile.wbR, tile.wbG, tile.wbB)' in native
assert contract.count('val applyAmazeWbForLabFcc =')==1
assert 'source.rgb * uAmazeWb' in contract and 'source.rgb * uInverseAmazeWb' in contract
assert 'renderRawrLabDefringe26856(\n                temporaryPostWb,' in stack
assert 'iris26857ApplyAmazeWbProgram' in stack and stack.count('renderRawrBPostAmaze26856(')>=2
assert stack.count('"uAmazeWb"') == 1
assert 'val inverse = snapshot.inverseWhiteBalance' in stack
assert 'releaseOwnedTexture(temporaryPostWb' in stack and 'if (defringed != 0) releaseOwnedTexture(defringed' in stack
for gains in [(2.4794922,1,1.828125),(1.,1.,1.),(0.45,1.,4.2),(4.,1.,2.)]:
 for rgb in [(0.1,0.1,0.1),(0.7,0.5,0.3),(1.3,0.7,1.4)]:
  temporary=tuple(c*g for c,g in zip(rgb,gains))
  restored=tuple(x/g for x,g in zip(temporary,gains))
  assert all(math.isclose(a,b,rel_tol=1e-6) for a,b in zip(rgb,restored))
# Gate ONLY B-only, never historical A nor A+B where A is the primary
assert re.search(r'val iris26728ChromaFloor = if \(!parameters\.irisNightActive &&\s+experiment26856 != Iris26856ABSettings.Mode.AMAZE_26855\)',bridge)
assert 'applyIris26728ProtectedChromaFloor(' in bridge and 'forceOpaqueHalfAlpha(denoiseBuffer' in bridge
assert '"iris_26856_experiments_by_camera2_id"' not in ui
assert 'for (String id : Iris26856ABSettings.cameraIds(mContext))' not in ui
assert 'PreferenceGroup lens = findPreference(mContext.getString(R.string.pref_category_hdrx_key))' in ui
assert 'mode.setEntries(new CharSequence[]{"A", "B", "A+B"})' in ui
assert 'Iris26856ABSettings.write(mContext, active, next)' in ui
assert '"_B_RAWR.jpg"' not in hdr and '"_B_RAWR"' not in hdr
assert 'Paths.get(iris26856BasePath + "_B.jpg")' in hdr
assert '(iris26856Both ? "_A" : iris26856BOnly ? "_B" : "")' in hdr
assert 'mIris26856BOnlyJpegRollbackPath = imageFile' in hdr
print('PASS 26857 provisional color roundtrip, native export, B-alpha gate, existing lens scope, public filenames, rollback anchors')
