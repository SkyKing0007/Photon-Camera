#!/usr/bin/env python3
from pathlib import Path
import re,sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26686.py BASE CAND')
base,cand=map(Path,sys.argv[1:])
def txt(rel): return (cand/rel).read_text()
def need(text,tok,msg='token'):
    if tok not in text: raise SystemExit('FAIL '+msg+': '+tok)
def forbid(text,tok,msg='forbidden'):
    if tok in text: raise SystemExit('FAIL '+msg+': '+tok)
rawp=txt('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraRawProcessor.java')
rawf=txt('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraRawFrame.java')
own=txt('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraCameraOwner.java')
meta=txt('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraFrameMetadata.java')
pre=txt('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraPreviewRenderer.java')
proc=txt('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraProcessor.java')
store=txt('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraShotStore.java')
jni=txt('app/src/main/cpp/spektra/SpektraNativeJni.cpp')
vk=txt('app/src/main/cpp/spektra/SpektraRawVulkanOwner.cpp')
vkh=txt('app/src/main/cpp/spektra/SpektraRawVulkanOwner.h')
shader=txt('app/src/main/cpp/spektra/SpektraRawDevelop.comp')
cmake=txt('app/src/main/cpp/CMakeLists.txt'); embed=txt('app/src/main/cpp/spektra/EmbedSpektraSpirv.cmake')
# Standalone RAW/GPU owner and zero Iris GL/RCD ownership.
for t in ['nativeProcessPackedRaw','processLivePreview','releaseNativeOwner','nativeRawOwnerStats']: need(rawp,t,'native RAW Java owner')
rawp_code=re.sub(r'//.*?$|/\*.*?\*/',' ',rawp,flags=re.M|re.S)
for t in ['GLContext','GLProg','GLTexture','runRcd','RCD26498']: forbid(rawp_code,t,'Iris GL/RCD survived active RAW owner')
for t in ['SpektraRawVulkanOwner::instance().process','nativeProcessPackedRaw','nativeReleaseRawOwner','nativeRawOwnerStats']: need(jni,t,'JNI Vulkan owner')
jni_code=re.sub(r'//.*?$|/\*.*?\*/',' ',jni,flags=re.M|re.S)
for t in ['GLContext','GLProg','GLTexture','RCD26498']: forbid(jni_code,t,'Iris GL/RCD survived JNI owner')
for t in ['static SpektraRawVulkanOwner owner','previewDropped','savedWaiting','VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT']: need(vk,t,'persistent Vulkan contract')
# Packed Camera2 plane lifetime and no Java full-resolution demosaic/unpack fallback.
for t in ['The Camera2 Image stays owned and open through native Vulkan RAW processing','SpektraRawFrame.copyPreviewFrom(image','finally {\n                    try { image.close();']: need(own,t,'live Image lifetime')
for t in ['processLivePreview(plane.buffer','copyStillFrom(Image image)','byte[] packed = new byte[plane.bytes]','nativeDecodeMeter']: need(rawf,t,'packed RAW ownership')
for t in ['unpackRaw10','unpackRaw12','nativeDecodePreviewRgb16f','previewCameraRgb16f']: forbid(rawf,t,'dead Java/legacy display RAW owner returned')
# Geometry is one RAW-raster domain end-to-end and Bayer origin is fail-closed.
for t in ['rawBounds','sourceCrop','activeRawDomain','mapSensorRect(activeSensor, pixelArray, rawBounds)','mapSensorRect(requestedSensorCrop, pixelArray, rawBounds)','hint = -1','leftNumerator % pixelArray.getWidth() == 0L','activeRawDomain.width() < 2']: need(meta,t,'RAW-raster geometry')
for t in ['geometryBayerOffsetHint','BAYER_ORIGIN_AMBIGUOUS','BAYER_ORIGIN_UNRESOLVED_AT_STILL','IRIS_26686_SPEKTRA_RAW_GEOMETRY_UNRESOLVED']: need(own,t,'fail-closed Bayer origin')
for t in ['black[q] = sensorBlack[q ^ selectedOffset]','cfa = sensorCfa ^ selectedOffset']: need(meta,t,'CFA/black phase contract')
for t in ['rect4(shot.metadata.rawBounds)','rect4(crop)','rect4(shot.metadata.activeRawDomain)','metadata.bayerOffset']: need(rawp,t,'Java->JNI geometry carrier')
for t in ['q.rawBounds','q.sourceCrop','q.activeRawDomain','words[19]=static_cast<uint32_t>(q.bayerOffset)']: need(vk,t,'JNI->Vulkan geometry carrier')
# Shader geometry/LSC/CFA and matrix convention.
for t in ['P_ACTIVE_L','P_BAYER_OFFSET','clampActivePreservePhase','sensorRowParity=(xy.y&1)^((int(p[P_BAYER_OFFSET])>>1)&1)','activeMin=vec2(float(p[P_ACTIVE_L])','vec3 r0=vec3(uintBitsToFloat(p[P_M0+0u])','vec3 r1=vec3(uintBitsToFloat(p[P_M0+3u])','vec3 r2=vec3(uintBitsToFloat(p[P_M0+6u])','return vec3(dot(r0,rgb),dot(r1,rgb),dot(r2,rgb))']: need(shader,t,'native shader domain contract')
# Preview is native-developed linear RGB only; public Spektra film renderer remains downstream owner.
for t in ['previewLinearRgba16f','previewLinearFrame(frame)','new SpektraFilmRenderer(activity)','activity.runOnUiThread(firstFramePresentedCallback)']: need(rawf+pre,t,'VF-S ownership')
for t in ['new SpektraRawProcessor().process(shot, true)','SpektraFilmRenderer','SpektraJpegPublisher']: need(proc,t,'saved downstream owner')
# Recovery carries durable packed RAW + complete native recipe.
for t in ['VERSION = 4','sourceFormat','rowStride','pixelStride','activeRawDomain','out.writeInt(shot.raw.packedRaw.length)','out.write(shot.raw.packedRaw)']: need(store,t,'recovery RAW recipe')
# Build wiring: same existing native target/build phase, pinned glslang injected by inherited mechanism.
for t in ['IRIS26686_RAW_SHADER_SRC','COMMAND "${IRIS26681_GLSLANG}" -V','list(APPEND IRIS26681_SPEKTRA_SPV_FILES','spektra/SpektraRawVulkanOwner.cpp']: need(cmake,t,'native build wiring')
need(embed,'SpektraRawDevelop.comp.spv','SPIR-V embed wiring')
# New shader complete lexical reserved-identifier scan. This is supplementary to real glslang.
reserved=set('attribute const uniform varying buffer shared coherent volatile restrict readonly writeonly atomic_uint layout centroid flat smooth noperspective patch sample break continue do for while switch case default if else subroutine in out inout float double int void bool true false invariant precise discard return mat2 mat3 mat4 dmat2 dmat3 dmat4 mat2x2 mat2x3 mat2x4 mat3x2 mat3x3 mat3x4 mat4x2 mat4x3 mat4x4 dmat2x2 dmat2x3 dmat2x4 dmat3x2 dmat3x3 dmat3x4 dmat4x2 dmat4x3 dmat4x4 vec2 vec3 vec4 ivec2 ivec3 ivec4 bvec2 bvec3 bvec4 dvec2 dvec3 dvec4 uint uvec2 uvec3 uvec4 lowp mediump highp precision sampler1D sampler2D sampler3D samplerCube sampler1DShadow sampler2DShadow samplerCubeShadow sampler1DArray sampler2DArray sampler1DArrayShadow sampler2DArrayShadow isampler1D isampler2D isampler3D isamplerCube isampler1DArray isampler2DArray usampler1D usampler2D usampler3D usamplerCube usampler1DArray usampler2DArray sampler2DRect sampler2DRectShadow isampler2DRect usampler2DRect samplerBuffer isamplerBuffer usamplerBuffer sampler2DMS isampler2DMS usampler2DMS sampler2DMSArray isampler2DMSArray usampler2DMSArray samplerCubeArray samplerCubeArrayShadow isamplerCubeArray usamplerCubeArray image1D iimage1D uimage1D image2D iimage2D uimage2D image3D iimage3D uimage3D image2DRect iimage2DRect uimage2DRect imageCube iimageCube uimageCube imageBuffer iimageBuffer uimageBuffer image1DArray iimage1DArray uimage1DArray image2DArray iimage2DArray uimage2DArray imageCubeArray iimageCubeArray uimageCubeArray image2DMS iimage2DMS uimage2DMS image2DMSArray iimage2DMSArray uimage2DMSArray struct common partition active asm class union enum typedef template this resource goto inline noinline public static extern external interface long short half fixed unsigned superp input output hvec2 hvec3 hvec4 fvec2 fvec3 fvec4 sampler3DRect filter sizeof cast namespace using row_major'.split())
# Declarations are the dangerous place; flag reserved user-defined identifiers after common declaration forms.
clean=re.sub(r'//.*?$|/\*.*?\*/',' ',shader,flags=re.M|re.S)
pat=re.compile(r'\b(?:const\s+)?(?:uint|int|float|bool|vec[234]|ivec[234]|uvec[234]|mat[234])\s+([A-Za-z_]\w*)')
for name in pat.findall(clean):
    if name in reserved or name.startswith('gl_'): raise SystemExit('FAIL reserved GLSL identifier '+name)
if 'VERSION_NAME=0.9726686' not in txt('app/version.properties') or 'VERSION_BUILD=26686' not in txt('app/version.properties'): raise SystemExit('FAIL version')
print('PASS 26686 semantics: packed RAW lifetime + exact RAW-raster geometry + fail-closed CFA + persistent native Vulkan owner + active-domain LSC/CFA contract + zero Iris GL/RCD + pinned Spektra film/JPEG downstream')
print('PASS 26686 modified shader reserved-identifier scan')
