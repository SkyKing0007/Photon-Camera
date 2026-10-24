#!/usr/bin/env python3
"""Byte-match actual candidate GLSL shader string sources to frozen expanded GLSL."""
import pathlib,re,sys
p=pathlib.Path(__file__).resolve().parent
app=pathlib.Path(sys.argv[1])/'app'
cpp=(app/'src/main/cpp/motionv2_jpeg444_jni.cpp').read_text()
kt=(app/'src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
raw=re.search(r'static const char\*kIris26876BPublicationCompute=R"GLSL\((.*?)\)GLSL";',cpp,re.S)
assert raw and raw.group(1)==(p/'26876_NATIVE_B_GPU_FINAL_RENDER.comp').read_text()
for key,fn in [('iris26876BDownsampleNativeRgb','26876_B_GUIDE_1X_RGB.frag'),('iris26876BDownsampleSensorClip','26876_B_SENSOR_CLIP_OR.frag')]:
 match=re.search(r'private val '+key+r' = """\s*(#version 300 es.*?)\s*"""\.trimIndent\(\)',kt,re.S)
 assert match,key
 shader='\n'.join(z.strip() for z in match.group(1).splitlines())+'\n'
 assert shader==(p/fn).read_text(),key
for fn in ('26876_NATIVE_B_GPU_FINAL_RENDER.comp','26876_B_GUIDE_1X_RGB.frag','26876_B_SENSOR_CLIP_OR.frag'):
 shader=(p/fn).read_text()
 assert len(shader)>100 and shader.lstrip().startswith('#version '),fn
 # complete GLSL ES reserved words check on user-defined declaration names
 keywords=set('attribute varying uniform layout centroid flat smooth noperspective patch sample subroutine coherent volatile restrict readonly writeonly buffer shared atomic_uint precision highp mediump lowp input output common partition active asm class union enum typedef template this resource goto inline noinline public static extern external interface long short half fixed unsigned superp invariant packed namespace using sizeof cast double dvec2 dvec3 dvec4 sampler3DRect'.split())
 declared=re.findall(r'\b(?:float|vec[234]|ivec[234]|uvec[234]|int|uint|bool|mat[234]|sampler2D|image2D)\s+([A-Za-z_][A-Za-z0-9_]*)',re.sub(r'/\*.*?\*/|//[^\n]*','',shader,flags=re.S))
 assert not(set(declared)&keywords),f'{fn} reserved identifiers {set(declared)&keywords}'
print('26876 ACTUAL RUNTIME GLSL-EXPANDED SOURCE + RESERVED IDENTIFIERS: PASS')
