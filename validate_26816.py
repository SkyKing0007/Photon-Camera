#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys,re,xml.etree.ElementTree as ET
if len(sys.argv)!=3: raise SystemExit('usage: validate_26816.py BASE_ROOT CANDIDATE_ROOT')
B,C=map(Path,sys.argv[1:])
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def uni(root): return {p.relative_to(root).as_posix():p for p in (root/'app').rglob('*') if p.is_file()}
b,c=uni(B),uni(C)
mods=sorted(k for k in b.keys()&c.keys() if sha(b[k])!=sha(c[k])); adds=sorted(c.keys()-b.keys()); dels=sorted(b.keys()-c.keys())
allow=Path('26816_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines()
assert sorted(mods+adds)==sorted(allow),(mods,adds,allow)
assert len(mods)==19 and adds==['app/src/main/res/drawable/ic_logging_document.xml'] and not dels
assert len(b)==1782 and len(c)==1783
# Version/build.
ver=(C/'app/version.properties').read_text(); assert 'VERSION_NAME=0.9726816' in ver and 'VERSION_BUILD=26816' in ver
# 26815 VGN owner preserved; only independent magnitude proof tightened.
vgn=(C/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt').read_text()
assert 'IRIS_26815_INDEPENDENT_NEIGHBOR_CHROMA_RESTORE_PROOF' in vgn
assert 'IRIS_26816_STRICTER_INDEPENDENT_CHROMA_MAGNITUDE_PROOF' in vgn
assert 'smoothstep(0.60, 0.85,' in vgn and 'smoothstep(0.45, 0.80,' not in vgn
assert 'smoothstep(0.80, 0.94,' in vgn and 'smoothstep(0.35, 0.80,' in vgn
assert 'strictPhysicalProof * independentNeighborRestoreProof' in vgn
# Successful 26813 Sabre weighting remains exact; failed 26814 experiment remains absent.
sabre=C/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'
assert sha(sabre)=='b6e81869e3ceb29dd02f6d83772be41bfc53031ea1158344694ca5704a825812'
assert 'IRIS_26814_UNIFIED_RGB_SHARED_CONFIDENCE_OWNER' not in sabre.read_text()
# 26809 expensive diagnostic retired, no carrier algorithm replacement.
stack=(C/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
assert 'logSabreResolveHueProbe26809' not in stack and 'IRIS_26809_RESOLVE_RGB_HUE_PROBE' not in stack
assert 'IRIS_26816_RETIRE_RESOLVE_RGB_HUE_PROBE' in stack
# 26803 correction remains active while its telemetry SSBO/readback is retired.
mvr=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text()
assert 'IRIS_26803_STRICT_NEUTRAL_PARENT_FRINGE_REPAIR_OWNER' in mvr
assert 'IRIS_26816_RETIRE_FALSE_COLOR_DECISION_TELEMETRY' in mvr
assert 'iris26798Stats' not in mvr and 'iris26799Stats' not in mvr and 'readBufferIntegers(false)' not in mvr
assert 'IRIS_26702_THERMAL_SNAPSHOT' not in mvr and 'iris26702LogThermal' not in mvr
for rel in ['app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/assets/shaders/motionv2/false_color_classify_26800.glsl','app/src/main/assets/shaders/motionv2/false_color_propagate_26799.glsl']:
    t=(C/rel).read_text(); assert 'iris26798Counters' not in t and 'iris26799Counters' not in t and 'atomicAdd(' not in t and 'atomicMax(' not in t
# 26813 no-raise and actual residual correction remain.
bridge=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
assert 'IRIS_26813_POST_DENOISE_CHROMA_NO_RAISE_OWNER' in bridge
assert 'IRIS_26728_PROTECTED_CHROMA_POST_RESIDUAL_DENOISE' in bridge and 'IRIS_26795_SCENE_RELATIVE_BRIGHT_EDGE_CHROMA' in bridge
assert 'IRIS_26795_SPATIAL_MASK' not in bridge and 'IRIS_26795_TOP_RISK' not in bridge
# Logging files retained, default OFF, no per-event MotionTrace flush.
log=(C/'app/src/main/java/com/particlesdevs/photoncamera/util/Log.java').read_text()
assert 'private static volatile boolean logEnabled = false;' in log
assert 'log-' in log and 'motion-trace-' in log and 'public static void setLogEnabled(boolean enabled)' in log
w=log[log.index('public static void writeMotionTrace('):log.index('private static void cleanupOldLogs()',log.index('public static void writeMotionTrace('))]
assert 'motionBufferedWriter.flush();' not in w
trace=(C/'app/src/main/java/com/particlesdevs/photoncamera/util/MotionTrace.java').read_text()
wi=trace[trace.index('private static void writeInfo'):trace.index('private static String sanitize',trace.index('private static void writeInfo'))]
assert 'flushNow()' not in wi and 'flushMotionNow()' not in wi
assert trace.count('Log.flushNow();')>=2 and trace.count('Log.flushMotionNow();')>=2
# Spam collapsed/throttled.
zoom=(C/'app/src/main/java/com/particlesdevs/photoncamera/control/IrisZoomController.java').read_text(); assert 'IRIS_26816_HAL_TELEMETRY_CHANGE_ONLY' in zoom
cap=(C/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text(); assert 'IRIS_26816_REFERENCE_METER_CHANGE' in cap and '"FRAME_META"' not in cap and '"FRAME_META_SUMMARY"' in cap
hdr=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java').read_text(); assert 'IRIS_26816_FRAME_NOISE_SUMMARY' in hdr and 'IRIS_26480_FRAME_NOISE_SOURCE' not in hdr
# About toggle/UI exact style; default OFF.
prefs=(C/'app/src/main/res/xml/preferences.xml').read_text(); assert 'pref_enable_logging_key' in prefs and 'ManagedSwitchPreference' in prefs and '@layout/preference_with_margin' in prefs and 'defaultValue="false"' in prefs and '@drawable/ic_logging_document' in prefs
keys=(C/'app/src/main/java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java').read_text(); assert 'KEY_ENABLE_LOGGING' in keys and 'isLoggingEnabled()' in keys
app=(C/'app/src/main/java/com/particlesdevs/photoncamera/app/PhotonCamera.java').read_text(); assert 'IRIS_26816_DEFAULT_OFF_LOGGING_OWNER' in app and 'PreferenceKeys.isLoggingEnabled()' in app
settings=(C/'app/src/main/java/com/particlesdevs/photoncamera/ui/settings/SettingsActivity.java').read_text(); assert 'setupLoggingPreference()' in settings and 'Log.setLogFolder(mContext.getApplicationContext())' in settings
icon=C/'app/src/main/res/drawable/ic_logging_document.xml'; ET.parse(icon); assert '?colorControlNormal' in icon.read_text()
for rel in ['app/src/main/res/values/preference_keys.xml','app/src/main/res/values/strings.xml','app/src/main/res/xml/preferences.xml']: ET.parse(C/rel)
print('PASS 26816 semantic/runtime validation: 19 modified + 1 added, VGN-only IQ delta, production logging default-off, correction owners preserved')
