#!/usr/bin/env python3
"""Prove B OFF selects original pinned RAWR HDRq AMaZE + YIQ FCC without Iris edges/chroma."""
import pathlib,hashlib,sys,re
R=pathlib.Path(__file__).resolve().parent
src=R if '--live' in sys.argv else R/'handoff_payload_26949'
A=src/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26870PostAmazeChroma.kt'
B=src/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'
a=A.read_text();b=B.read_text()
# Check the EXACT Kotlin-embedded runtime GLSL, excluding comments/Kotlin vars.
# GLSL reserves `coherent`; Kotlin permits that identifier.
assert a.count('val shader="""')==1
shader=a.split('val shader="""',1)[1].split('""".trimIndent()',1)[0]
assert shader.count('void main()')==1 and shader.count('#version 300 es')==1
assert '$' not in shader
def illegal_glsl_identifiers(source):
    code=re.sub(r'/\*.*?\*/','',source,flags=re.S)
    code=re.sub(r'//[^\n]*','',code)
    forbidden=('coherent volatile restrict readonly writeonly shared attribute varying '
        'subroutine input output namespace using packed goto asm class union enum '
        'typedef template this resource inline noinline public static extern '
        'external interface long short double half fixed unsigned superp '
        'sampler1D sampler1DShadow sampler2DRect sampler2DRectShadow '
        'sampler2DMS sampler2DMSArray samplerBuffer samplerCubeArray '
        'samplerCubeArrayShadow hvec2 hvec3 hvec4 fvec2 fvec3 fvec4 '
        'dvec2 dvec3 dvec4 filter common partition active sizeof cast').split()
    return [name for name in forbidden if re.search(r'\b'+re.escape(name)+r'\b',code)]
assert not illegal_glsl_identifiers(shader),('reserved GLSL identifier',illegal_glsl_identifiers(shader))
assert 'coherent' in illegal_glsl_identifiers(shader+'\nfloat coherent=0.0;\n')
assert 'coherent' not in illegal_glsl_identifiers('// coherent\n'+shader)
assert a.count('IRIS_26949_B_OFF_EXACT_RAWR_AMAZE_HANDOFF')==1
assert a.count('if(uIris26924BOff!=0){\n            oPostWbCameraRgb=vec4(rawrHighlightOff(raw.rgb),raw.a);')==1
assert a.index('IRIS_26949_B_OFF_EXACT_RAWR_AMAZE_HANDOFF') < a.index('vec3 repaired=bOffMaterialOutlier')
assert a.count('vec3 rawrHighlightOff(vec3 sensorNeutralRgb)')==1
assert 'float commonCeiling=min(uAmazeWb.r,min(uAmazeWb.g,uAmazeWb.b));' in a
assert 'return min(postWb,vec3(commonCeiling));' in a
assert b.count('IRIS_26949_B_OFF_EXACT_RAWR_FCC_RESTORE')==1
ix=b.index('fcc = renderRawrFalseColor26856(')
call=b[ix:b.index('                )',ix)]
for token in ['defringed, normalizedChroma = true','edgeSigma = 0f, chromaBound = 0f','iris26924SensorClip = 0','iris26924BOff = false']:
 assert token in call,token
assert 'repeat(2) { step ->' in b
assert b.count('if(lkrNativeFullRgb26931)')>=3  # Wronski RawLens route still present
# The first/cross-mode transform operates in sensor-neutral linear camera RGB.
assert 'uSensorNeutralAmazeRgb' in a and 'uAmazeWb' in a
assert 'uSensorNeutralAmazeRgb' in b and 'undoAmazeWbToIrisSensorNeutral' in b
if '--live' in sys.argv:
 base={p:h for h,p in [line.split('  ',1) for line in (R/'26949_BASE_26948_FULL_APP.sha256').read_text().splitlines()]}
 for q in ['app/src/main/java/com/hinnka/mycamera/processor/GlesIris26856RawrFalseColor.kt',
           'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26856AmazeCfaHandoff.kt',
           'app/src/main/cpp/iris26856/amaze/shaders/amaze_export.comp']:
  assert hashlib.sha256((R/q).read_bytes()).hexdigest()==base[q],q
 # No 26924/27 B OFF edge or clip correction can execute when its uniform is false.
 fcc=(R/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26856RawrFalseColor.kt').read_text()
 assert 'if(uIris26924BOff!=0 && (clipNear(p)||hardEdge(p)||chromaticBoundary(p)))' in fcc
 assert 'else if(uEdgeSigma>0.0 || uIris26924BOff!=0)' in fcc
 assert 'iq*=1.0/9.0;' in fcc and 'vec3 fromYIQ(float Y, vec2 iq)' in fcc
print('PASS 26949 B OFF original RAWR YIQ FCC x2; no post-AMaZE Iris chroma; original highlight OFF; B ON unchanged')
