#!/usr/bin/env python3
"""Fail-closed 26957 two-Rawr-commit Iris bridge + opt-in chroma, source ownership, shader and NDK arity."""
import hashlib,re,sys,shutil,subprocess,tempfile
from pathlib import Path
from build_26957_incremental import R,fail,scope,exact

def require(s,parts,label):
 for p in parts:
  if p not in s:fail(label+' absent '+p)
def main():
 changed,added,old,new=scope()
 root=R if '--live' in sys.argv else R/'handoff_payload_26957'
 if '--live' in sys.argv:exact(R,'26957_EXPECTED_FULL_APP.sha256','live current candidate')
 for p in changed:
  if hashlib.sha256((root/p).read_bytes()).hexdigest()!=new[p]:fail('payload hash mismatch '+p)
 if any(x in p for p in changed for x in ('/vendor/','/jniLibs/','/assets/shaders/motionv2/','/assets/shaders/iris26876/')):fail('protected vendor/SR ON/render changed')
 if len(changed)!=14 or len(old)-len(changed)!=2041:fail('wrong source scope')
 version=(root/'app/version.properties').read_text()
 require(version,['VERSION_BUILD=26957','VERSION_NAME=0.9726957'],'version')
 base='app/src/main/cpp/iris26864/'
 coord=(root/(base+'bridge/Iris26888BOffHdrqCoordinator.cpp')).read_text()
 rec=(root/(base+'bridge/Iris26887BOffHdrqRecorder.cpp')).read_text()
 m=(root/(base+'bridge/Iris26887BOffHdrqMismatchNorm.comp')).read_text()
 head=(root/(base+'bridge/Iris26888BOffHdrqPrivateHeader.hpp')).read_text()
 execute=(root/(base+'bridge/Iris26888BOffVulkanExecutor.cpp')).read_text()
 owner=(root/(base+'Iris26864RealRawrCoordinator.cpp')).read_text()
 jni=(root/(base+'Iris26864JniGpuInteropImpl.inc')).read_text()
 java=(root/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26864NativeRawr.java').read_text()
 kotlin=(root/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
 sharp=(root/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26870GpuSharpest.kt').read_text()
 settings=(root/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java').read_text()
 xml=(root/'app/src/main/res/xml/preferences.xml').read_text()
 ui=(root/'app/src/main/java/com/particlesdevs/photoncamera/ui/settings/SettingsActivity.java').read_text()
 require(owner,['if (!sr) { hdrq.strength = 13.0f; hdrq.tileSize = 32u; }'],'fixed 13/32 B-OFF-only')
 require(rec,['add("hdrq_neff", tiles, PixelStorage::R32Float, Lifetime::Output);',
 'static_assert(sizeof(MismatchNormPc)==24u','vkCmdClearColorImage(c, arena_.image("hdrq_neff").image',
 'ib(3, zmap), ib(4, arena_.image("hdrq_neff"))',
 'recordEffectiveFramesCopy(VkCommandBuffer c, VkBuffer host)','vkCmdCopyImageToBuffer',
 'kGateLow=1.6f, kGateHigh=2.6f, kGateShrink=1.0f',
 'kEnergyGain=1.0f, kEnergyDead=1.0f, kEnergyScale=0.5f','rawNoiseMeasured_',
 'noiseVarianceOffset','std::isfinite(noiseVarianceOffset)'],'matched motion+energy+effective recording')
 require(m,['#version 450','layout(set = 0, binding = 3, r32f) readonly uniform image2D zmap;',
 'layout(set = 0, binding = 4, r32f) uniform image2D neffAcc;',
 'float gateLo;','float gateHi;','int useMotionGate;',
 'float contribution = 1.0 - smoothstep(p.gateLo, p.gateHi, imageLoad(zmap, g).x);',
 'imageStore(neffAcc, g, vec4(imageLoad(neffAcc, g).x + contribution));'],'motion gate Neff GLSL')
 require(execute,['{"hdrq_mismatch_norm",','{4, VK_DESCRIPTOR_TYPE_STORAGE_IMAGE}'],'descriptor binding 4')
 require(head,['void recordEffectiveFramesCopy(VkCommandBuffer command, VkBuffer host);','tileCount() const noexcept','setMotionGate(bool enabled)','setNoise(float slope,float offset)'],'native ABI')
 require(coord,['thread_local float iris26957HdrqEffectiveFrames = 0.0f;',
 'recorder.setMotionGate(algorithm_==MergeAlgorithm::HdrPlusFrequency)',
 'recorder.recordEffectiveFramesCopy(command_, noiseStats_.buffer);',
 'const float accepted = support[tile];','1.0 / (1.0 + double(std::max(accepted, 0.0f)))',
 'hdrqEffectiveFrames = float(double(tileCount) / inverse)',
 'result.estimatedNoise = *hdrqMeasuredProfile;', 'result.noiseEstimated = true;',
 'iris26957HdrqEffectiveFrames = hdrqEffectiveFrames;','vkWaitForFences'],'tile Neff harmonic mean and measured fit')
 if coord.count('if (pass == 3u && algorithm_ == MergeAlgorithm::HdrPlusFrequency)')!=1:fail('Neff copy outside final B OFF only')
 require(jni,['extern thread_local float iris26957HdrqEffectiveFrames;',
 'jboolean hdrqEffectiveChroma','if(sr == JNI_FALSE && hdrqEffectiveChroma == JNI_TRUE)',
 'const float effective=rawr::raw_gpu_pipeline::iris26957HdrqEffectiveFrames;',
 'std::max(effective,1.0f)','result.noiseEstimated && std::isfinite(effective)',
 'params.maxScale=7;params.forceY=0.f;params.forceUv=.75f;',
 'bWavelet->record(cmd,rgb.view(),result.outputView,outWidth,outHeight,params);',
 'bWaveletCopy->record(cmd,bindings,&args,sizeof(args),outWidth,outHeight)',
 'args','pinnedSpv(iris26880_wavelet_copy_spv'],'original Rawr optional wavelet after AMaZE')
 # Absolutely no SR ON wavelet by accident, default OFF, 26956+ 0.4EV protected.
 if 'if(hdrqEffectiveChroma == JNI_TRUE)' in jni:fail('unguarded optional wavelet in SR ON route')
 require(java,['boolean hdrqEffectiveChroma','hdrqEffectiveChroma'],'Java JNI arity')
 require(kotlin,['IrisMotionSettings.isHdrqChromaDenoiseEnabled()',
 'pressWindow26957=true','GlesIris26870GpuSharpest.select('],'B OFF Kotlin route')
 require(sharp,['pressWindow26957:Boolean=false','age<=250_000_000L','val ageWeight=1.0-0.05*ageNs.toDouble()/250_000_000.0'],'press-window GPU score')
 require(settings,['KEY_HDRQ_CHROMA_DENOISE = "pref_iris_hdrq_effective_chroma"','isHdrqChromaDenoiseEnabled()','getBoolean(manager, KEY_HDRQ_CHROMA_DENOISE, false)'],'default-OFF user flag')
 require(xml,['ns0:key="pref_iris_hdrq_effective_chroma"','ns0:defaultValue="false"'],'settings XML')
 require(ui,['removePreferenceAnywhere(IrisMotionSettings.KEY_HDRQ_CHROMA_DENOISE);'],'non-Motion UI protection')
 for s,label in ((m,'mismatch norm'),):
  stripped=re.sub(r'/\*.*?\*/|//[^\n]*','',s,flags=re.S)
  if re.search(r'\b(?:float|int|vec[234]|ivec[234]|uint)\s+(?:coherent|flat|restrict|sample|buffer)\b',stripped):fail('GLSL reserved name '+label)
 if 'void main()' not in m:fail('incomplete current GLSL')
 # Fail closed against 26956 V1 actual NDK duplicate offset error with a real C++17 compiler.
 region=rec.split('void HdrPlusFrequencyRecorder::recordCompanionMerge(',1)[1].split('void HdrPlusFrequencyRecorder::recordSubstitutionSource(',1)[0]
 if re.search(r'\bfloat\s+(?:slope\s*=\s*noiseSlope_\s*,\s*)?offset\s*=',region):fail('actual native scalar offset shadow collision')
 compiler=shutil.which('clang++') or shutil.which('g++')
 if not compiler:fail('no local C++ compiler for 26956 V1 regression')
 fragment='float slope=noiseSlope_,'+region.split('float slope=noiseSlope_,',1)[1].split('const float meanBlack=',1)[0]
 unit='''#include <algorithm>\n#include <array>\n#include <cmath>\n#include <cstdint>\nint main(){const std::array<int,2> offset{0,0};const bool rawNoiseMeasured_=true;const float noiseSlope_=0.001f,noiseOffset_=0.02f,referenceWhite_=1023.0f;const std::array<float,4> referenceBlack_{0.f,0.f,0.f,0.f},rawNoiseSlope_{0.1f,0.1f,0.1f,0.1f},rawNoiseOffset_{0.001f,0.001f,0.001f,0.001f};\n'''
 def cpp(code):
  with tempfile.TemporaryDirectory(prefix='26957_native_offset_') as d:
   f=Path(d)/'regress.cpp';f.write_text(unit+code+'\nreturn slope<0.f;}\n')
   return subprocess.run([compiler,'-std=c++17','-fsyntax-only',str(f)],capture_output=True,text=True)
 good=cpp(fragment)
 if good.returncode:fail('real local corrected C++17 scope failure '+good.stderr[-450:])
 bad=cpp(fragment.replace('noiseVarianceOffset','offset'))
 if bad.returncode==0 or 'offset' not in bad.stderr:fail('26956 V1 real C++ duplicate-offset regression not detected')
 # Source-protected all modal render/gainmap/Native vendor.
 if '--live' in sys.argv:
  for p in ('app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/assets/shaders/motionv2/gainmap.glsl','app/src/main/cpp/iris26864/vendor/rawr/native/multiframe/pipeline/src/HdrPlusRecorder.cpp'):
   if hashlib.sha256((root/p).read_bytes()).hexdigest()!=old[p]:fail('protected +0.4EV/vendor changed '+p)
 print('PASS 26957 matched Rawr 56c1/44e4 motion-energy, harmonic Neff, opt-in wavelet, 13/32, GPU press-window and protected 2041; NDK collision negative')
if __name__=='__main__':
 try:main()
 except Exception as e:print('26957 SOURCE BLOCKED '+str(e),file=sys.stderr);sys.exit(1)
