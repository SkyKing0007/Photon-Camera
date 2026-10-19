from pathlib import Path
R=Path(__file__).resolve().parents[1]/'handoff_payload_26856/app/src/main/java'
bridge=(R/'com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
merger=(R/'com/particlesdevs/photoncamera/processing/processor/MotionV2Merger.java').read_text()
hdr=(R/'com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java').read_text()
stack=(R/'com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
assert 'enableSabreSuperRes = sabreSuperResEnabled &&\n                    experiment26856 == Iris26856ABSettings.Mode.ORIGINAL_26850' in bridge
assert 'iris26856BTrue2x = sabreSuperResEnabled && !parameters.irisNightActive' in bridge
assert 'require(!iris26856BTrue2x || (!enableSabreSuperRes && !enableHighZoomDetail' in stack
assert 'iris26856BTrue2xRgbPath = stackB26856.iris26856BTrue2xRgbPath' in bridge
assert 'iris26856BTrue2xOutputHandedOff = result.iris26856BTrue2xRgbPath != null' in bridge
assert 'if (!iris26856BTrue2xOutputHandedOff)' in bridge
assert 'b2x26856.length() == stacked.iris26856BTrue2xWidth.toLong() *' in bridge
assert 'public String iris26856BTrue2xRgbPath = null;' in merger
assert 'mIris26856BTrue2xPathForCleanup = iris26856BTrue2xRgbPath;' in hdr
assert 'if (mIris26856BTrue2xPathForCleanup != null)' in hdr
assert 'final String iris26856Primary2x = iris26856BOnly' in hdr
assert 'iris26856BTrue2xRgbPath, iris26856BTrue2xWidth,\n                        iris26856BTrue2xHeight, iris26856BPostParameters,' in hdr
assert '"26856 B-only true2x cannot consume A SR"' in hdr
assert '"26856 B 2x requires complete independent sensor-neutral RGB16F"' in bridge
assert 'IRIS_26856_B_TRUE2X_GUARDED_ACTIVATION' in bridge
assert '26856 B/A+B with Super Res requires independent RAWR 2x output; forbidden until implemented' not in bridge
# FULL production activation remains closed; no false success before SHORT/gain-map proof.
assert hdr.count('saveBitmapAsJPGMotionV2(')>=2
assert 'mIris26856BTrue2xPathForCleanup = null;' in hdr
assert 'File(path).delete()' in bridge
print('PASS B2x independent A/B/A+B transport, explicit 2x JPEG, strict capability and cleanup')
