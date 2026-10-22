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

# IRIS_26868_A_B_ONLY_KOTLIN_EDGE_PROVENANCE
# 26864's old typed-constructor harness expected a now-removed A+B Bridge
# invocation. Current live edges are B Bridge->Fusion->Spatial (direct RAWR)
# and A/Night Bridge->Fusion->Sabre->Spatial. Check *every* named argument
# against the actual Kotlin declaration; retain negative fixtures below.
sabre=read('java/com/hinnka/mycamera/processor/GlesIris26545SabreProcessor.kt')

def kt_params(text,stop):
 header=text[:text.index(stop)]
 return set(re.findall(r'^    (?:private val\s+)?([A-Za-z]\w*)\s*:',header,flags=re.M))

def kt_args(text,begin,end,spaces):
 assert text.count(begin)==1,('constructor call changed',begin,text.count(begin))
 body=text.split(begin,1)[1].split(end,1)[0]
 return set(re.findall(r'^ {'+str(spaces)+r'}([A-Za-z]\w*)\s*=',body,flags=re.M))

def current_kotlin_edges(bridge,fusion,sabre,stack):
 ctors={
  'fusion':kt_params(fusion,'    fun processFrames'),
  'sabre':kt_params(sabre,'    fun processFrames'),
  'spatial':kt_params(stack,'    private data class TextureLevel'),
 }
 edges=[
  ('A-or-B Bridge to Fusion',bridge,'val fusion = GlesMgcRawFusion(','\n            )\n',16,'fusion'),
  ('direct B Fusion to Spatial',fusion,'return GlesMgcRawSpatialStacker(','\n            ).processFrames',16,'spatial'),
  ('A/Night Fusion to Sabre',fusion,'return GlesIris26545SabreProcessor(','\n        ).processFrames',12,'sabre'),
  ('A/Night Sabre to Spatial',sabre,'return GlesMgcRawSpatialStacker(','\n        ).processFrames',12,'spatial'),
 ]
 for label,text,begin,end,spaces,receiver in edges:
  args=kt_args(text,begin,end,spaces)
  assert args and not (args-ctors[receiver]),(label,'invalid kotlin named arguments',sorted(args-ctors[receiver]))
 assert 'iris26864NativeWronski2x' in kt_args(fusion,'return GlesMgcRawSpatialStacker(','\n            ).processFrames',16)
 assert 'iris26864RealRawrOwnsBurstNoise' in kt_args(fusion,'return GlesMgcRawSpatialStacker(','\n            ).processFrames',16)
 assert 'iris26864NativeWronski2x' in kt_args(fusion,'return GlesIris26545SabreProcessor(','\n        ).processFrames',12)
 assert 'if (iris26856BOnlyIndependentPublication && iris26864RealRawrOwnsBurstNoise)' in fusion
 assert fusion.index('return GlesMgcRawSpatialStacker(') < fusion.index('return GlesIris26545SabreProcessor(')
 assert 'Iris26856ABSettings.Mode.BOTH' not in bridge
 assert 'Iris26856ABSettings.Mode.BOTH' not in fusion
 assert 'mode == Mode.BOTH' not in settings
 return True

def negative_kotlin_edges():
 assert current_kotlin_edges(bridge,fusion,sabre,stack)
 for changed in (
     fusion.replace('iris26864NativeWronski2x = iris26864NativeWronski2x,', 'iris26864BROKEN = iris26864NativeWronski2x,',1),
     fusion.replace('iris26864RealRawrOwnsBurstNoise = true,', 'iris26864BROKEN = true,',1),
 ):
  try:current_kotlin_edges(bridge,changed,sabre,stack)
  except AssertionError:continue
  raise AssertionError('B Kotlin edge negative regression failed to reject mutation')
 return True

def exact(s,t,n=1):assert s.count(t)==n,('count',t,s.count(t))
checks={
 'AB_ENUM_RETIRED':lambda:exact(settings,'ORIGINAL_26850("A"), AMAZE_26855("B");'),
 'CURRENT_A_B_KOTLIN_CONSTRUCTOR_EDGES':lambda:current_kotlin_edges(bridge,fusion,sabre,stack),
 'CURRENT_B_KOTLIN_NEGATIVE_FIXTURES':lambda:negative_kotlin_edges(),
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
 'DIRECT_B_WRONSKI_ONE_NATIVE_OWNER':lambda:check_direct_wronski(stack),
 'DIRECT_B_SENSORMASK_FAILS_CLOSED':lambda:check_direct_clip(stack,bridge),
 'PINNED_WRONSKI_B':lambda:exact(stack,'twoX = reconstructIris26864PinnedWronski2x('),
 'DNG_ONLY_A_PRODUCER':lambda:exact(bridge,'exactHistorical26850 = true,'),
 'SABRE_PREWARM_NOT_B':lambda:exact(capture,'IRIS_26868_B_IDLE_NO_SABRE_PREWARM'),
 'NO_FALLBACK_TO_SABRE_B':lambda:exact(fusion,'return GlesMgcRawSpatialStacker('),
}
def direct_b_body(stack):
 begin=stack.index('private fun processIris26868DirectB(')
 end=stack.index('private fun renderIris26868IndependentLongShadowGuide(',begin)
 return stack[begin:end]

def check_direct_wronski(stack):
 body=direct_b_body(stack)
 assert body.count('reconstructIris26864PinnedWronski2x(')==1, 'B direct Wronski must have exactly one true2x owner'
 assert 'reconstructIris26856BTrue2xTiles(' not in body, 'B legacy SR reintroduced'
 assert 'return processSabreFrames(frames)' not in body, 'B must not silently fall back to Sabre'
 assert 'checkNotNull(iris26864NativeWronski2x)' in body, 'native Wronski owner must fail closed'

def check_direct_clip(stack,bridge):
 body=direct_b_body(stack)
 assert 'check(nativeClip > 0)' in body, 'B direct sensor clip must fail closed'
 assert 'nativeSensorClipFullRes26866 = nativeClip' in body, 'B sensor clip evidence not passed to color owner'
 assert 'clipZoneMaskTextureId26836 = nativeClip' in body, 'B sensor clip not transported to publisher'
 assert 'sabreSuperResEnabled &&' in bridge and '"26864 B-only true2x requires original selected-reference native clip mask"' in bridge, '2x selected-reference mask protection removed'

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
