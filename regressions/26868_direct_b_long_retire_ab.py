"""Read-only source regressions; not equivalent to Android/GLSL/NDK execution."""
from pathlib import Path
import re
import sys
root=Path(sys.argv[1])/'src/main'
assert root.is_dir(),root
read=lambda p:(root/p).read_text()
stack=read('java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
bridge=read('java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt')
fusion=read('java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt')
publish=read('java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java')
capture=read('java/com/particlesdevs/photoncamera/capture/CaptureController.java')
settings=read('java/com/particlesdevs/photoncamera/settings/Iris26856ABSettings.java')
long=read('java/com/hinnka/mycamera/processor/GlesIris26868DirectLong.kt')
def exact(s,t,n=1):assert s.count(t)==n,('count',t,s.count(t))
checks={
 'AB_ENUM_RETIRED':lambda:exact(settings,'ORIGINAL_26850("A"), AMAZE_26855("B");'),
 'AB_PREFERENCE_MIGRATES_B':lambda:exact(settings,'if ("AB".equals(id)) return AMAZE_26855;'),
 'DIRECT_B_BEFORE_SABRE':lambda:assert_earlier(stack,'return processIris26868DirectB(frames)','return processSabreFrames(frames)'),
 'NATIVE_HDRQ_NORMAL_DIRECT':lambda:exact(stack,'iris26856AmazeCfaConsumer)(\n                0, nativeRgb'),
 'ONLY_A_OPTIONAL_DNG':lambda:exact(bridge,'IRIS_26868_B_EXISTING_A_DNG_ONLY'),
 'DIRECT_B_NEVER_SABRE_DNG':lambda:exact(bridge,'exportNormalStackedDng = produceNormalStackedDng &&\n                    experiment26856 != Iris26856ABSettings.Mode.AMAZE_26855,'),
 'FROZEN_REFERENCE':lambda:exact(stack,'it.sensorTimestampNs == iris26868ReferenceTimestampNs'),
 'BRIDGE_B_NATIVE_OWNER':lambda:exact(bridge,'Parameters.MOTION_V2_RECONSTRUCTION_RAWR_AMAZE',2),
 'PUBLISHER_B_NATIVE_OWNER':lambda:exact(publish,'? Parameters.MOTION_V2_RECONSTRUCTION_RAWR_AMAZE'),
 'SABRE_STATS_VETO_B':lambda:exact(bridge,'26868 B received forbidden Sabre statistics despite direct dispatch'),
 'NATIVE_B_SUPPORT_NOT_FABRICATED':lambda:exact(bridge,'supportDiagnostic=MINIMUM_CONFIRMED_NORMAL'),
 'LONG_SEPARATE_RAW_UPLOAD':lambda:exact(stack,'uploadRaw(long.image,longRaw,"26868 independent physical LONG")'),
 'LONG_REAL_AMAZE':lambda:exact(stack,'"26868 independent LONG AMaZE confidence"'),
 'LONG_INVALID_DROPS_SCALAR':lambda:exact(stack,'IRIS_26868_LONG_EXPOSURE_VETO'),
 'LONG_NO_COLOR_TRANSFER':lambda:exact(long,'oShadowGain=vec4(gain,trust,0.0,1.0);'),
 'BLACK_SHADOW_VETO':lambda:exact(long,'float measuredLight=smoothstep(0.008,0.035,max(longLow,normalLow));'),
 'NIGHT_NOT_B':lambda:exact(bridge,'val nativeB26868 = experiment26856 == Iris26856ABSettings.Mode.AMAZE_26855 &&'),
 'B_ZOOM_STILL_TO_A':lambda:exact(bridge,'val experiment26856 = if (iris26864BHighZoomExactA)'),
 'SHORT_EXPLICITLY_RETIRED':lambda:exact(stack,'frames.none { it.role == RawBurstFrameRole.HIGHLIGHT_SHORT }'),
 'PINNED_WRONSKI_B':lambda:exact(stack,'twoX = reconstructIris26864PinnedWronski2x('),
 'DNG_ONLY_A_PRODUCER':lambda:exact(bridge,'exactHistorical26850 = true,'),
 'SABRE_PREWARM_NOT_B':lambda:exact(capture,'IRIS_26868_B_IDLE_NO_SABRE_PREWARM'),
 'NO_FALLBACK_TO_SABRE_B':lambda:exact(fusion,'return GlesMgcRawSpatialStacker('),
}
def assert_earlier(text,a,b):assert text.index(a)<text.index(b)
for name,action in checks.items():
 try:action();print('PASS',name)
 except Exception as e:raise RuntimeError(f'{name} failed: {e}') from e
# GLSL identifier lexical scan (not a real shader compiler/expander).
reserved=set('asm class union enum typedef template this packed goto inline noinline public static extern external interface long short half fixed unsigned lowp mediump highp input output common partition active filter resource superp cast sizeof namespace using'.split())
for name in ['packCalibratedLong','trustedShadowGain']:
 shader=re.search(r'val '+name+r' = """(.*?)"""',long,re.S)
 assert shader is not None,name
 body=shader.group(1)
 assert '#version 300 es' in body and 'void main()' in body
 # Declarations of names after type tokens; allow built-in type qualifiers.
 types='float int vec2 vec3 vec4 ivec2 ivec3 ivec4 uint sampler2D usampler2D'
 pattern=r'\b(?:'+ '|'.join(types.split()) +r')\s+([a-zA-Z_][a-zA-Z_0-9]*)\b'
 names=set(re.findall(pattern,body))
 assert not reserved.intersection(names),(name,names&reserved)
 print('PASS',name,'static_identifiers',len(names),'NOTE real glslangValidator NOT RUN')
print('SOURCE_REGRESSIONS_PASS',len(checks),'real Android/Kotlin/Java/GLSL/native build NOT RUN')
