#!/usr/bin/env python3
"""Actual 26955 compiled source -> eight-file B HDRQ-only 26956 protection and dispatch safety."""
import re,sys,hashlib,shutil,subprocess,tempfile
from pathlib import Path
from build_26956_incremental import R,fail,scope,exact

def main():
    changed,added,old,new=scope()
    root=R if '--live' in sys.argv else R/'handoff_payload_26956'
    if '--live' in sys.argv:exact(R,'26956_EXPECTED_FULL_APP.sha256','actual compiled 26956 current SHA-universe')
    for p in changed:
        if hashlib.sha256((root/p).read_bytes()).hexdigest()!=new[p]:fail('current native bridge shader or C++ payload wrong '+p)
    if any('/vendor/' in p or '/jniLibs/' in p or '/assets/shaders/motionv2/' in p for p in changed):fail('other modes/render/vendor modified')
    version=(root/'app/version.properties').read_text()
    if 'VERSION_BUILD=26956' not in version or 'VERSION_NAME=0.9726956' not in version:fail('wrong app version')
    b='app/src/main/cpp/iris26864/bridge/'
    merge=(root/(b+'Iris26887BOffHdrqMerge.comp')).read_text()
    mismatch=(root/(b+'Iris26888BOffHdrqMismatch.comp')).read_text()
    executor=(root/(b+'Iris26888BOffVulkanExecutor.cpp')).read_text()
    recorder=(root/(b+'Iris26887BOffHdrqRecorder.cpp')).read_text()
    head=(root/(b+'Iris26888BOffHdrqPrivateHeader.hpp')).read_text()
    coord=(root/(b+'Iris26888BOffHdrqCoordinator.cpp')).read_text()
    owner=(root/'app/src/main/cpp/iris26864/Iris26864RealRawrCoordinator.cpp').read_text()
    for s,label in ((merge,'merge'),(mismatch,'mismatch')):
        # GLSL keywords were actual 26904 coherent and 26952 flat failures.
        clean=re.sub(r'/\*.*?\*/|//[^\n]*','',s,flags=re.S)
        if re.search(r'\b(?:float|int|vec[234]|ivec[234])\s+(?:coherent|flat|restrict|sample|buffer)\b',clean):fail('reserved GLSL identifier in '+label)
        if s.count('void main()')!=1 or not s.startswith('#version 450\n'):fail('incomplete GLSL '+label)
    for token in ('layout(set = 0, binding = 8, r32f) readonly uniform image2D zmap;',
                  'weight=max(weight,gate);','p.shrink*9.0*sigma2','if(gate<1.0)',
                  'p.useMotionGate!=0'):
        if token not in merge:fail('incomplete Rawr matched merge '+token)
    for token in ('layout(set = 0, binding = 4, r32f) writeonly uniform image2D zmap;',
                  'p.noiseSlope','p.noiseOffset','p.energyDead','p.energyScale',
                  'sBlockZ[bi>>2]=score;', 'p.useMotionGate!=0 ? acc/16.0 : 0.0'):
        if token not in mismatch:fail('incomplete Rawr noise-calibrated motion/energy classifier '+token)
    for token in ('add("hdrq_zmap"','rawNoiseMeasured_',
                  'referenceWhite_-refMeanBlack','kGateLow=1.6f, kGateHigh=2.6f, kGateShrink=1.0f',
                  'kEnergyGain=1.0f, kEnergyDead=1.0f, kEnergyScale=0.5f',
                  'ib(4,zmap)','ib(8, zmap)','static_assert(sizeof(MismatchPc)==52u',
                  'static_assert(sizeof(FreqMergePc)==56u','gated?1:0'):
        if token not in recorder:fail('missing or mismatched native Rawr HDRQ dispatch '+token)
    for token in ('setMeasuredRawNoise','setMotionGate(bool enabled)','setNoise(float slope,float offset)','bool motionGateEnabled_=false;'):
        if token not in head:fail('noise fallback/motion ownership missing '+token)
    if 'recorder.setMotionGate(algorithm_==MergeAlgorithm::HdrPlusFrequency)' not in coord or 'recorder.setNoise(alpha*range,beta*range*range)' not in coord:fail('motion gating spilled into other algorithm or fallback not connected')
    if owner.count('if (!sr) hdrq.strength = 11.0f;')!=1 or 'if (!sr) hdrq.strength = 13.0f;' in owner:fail('B OFF and B Night must preserve successful 26955 HDRQ strength 11')
    # 26956 V1 actual Android NDK failure: a float `offset` redeclared in
    # recordCompanionMerge alongside the existing `const auto offset=passOffset()`.
    # Verify the scalar variance intercept has a distinct name and both
    # actual GLSL push constant structures receive the scalar, not the array.
    region=recorder.split('void HdrPlusFrequencyRecorder::recordCompanionMerge(',1)[1].split('void HdrPlusFrequencyRecorder::recordSubstitutionSource(',1)[0]
    for required in ('const auto offset = passOffset();',
                     'float slope=noiseSlope_, noiseVarianceOffset=noiseOffset_;',
                     'noiseVarianceOffset=0.25f*(rawNoiseOffset_',
                     '!std::isfinite(noiseVarianceOffset)',
                     'noiseVarianceOffset=std::max(noiseOffset_,1.0e-10f);',
                     'slope,noiseVarianceOffset,meanBlack,1.0f,',
                     'slope,noiseVarianceOffset,meanBlack,kGateShrink'):
        if required not in region:fail('26956 V1 actual NDK C++ float/array name collision or push constant regression '+required)
    if re.search(r'\bfloat\s+(?:slope\s*=\s*noiseSlope_\s*,\s*)?offset\s*=',region):
        fail('26956 V1 C++ float offset redeclared against align passOffset()')
    # Compile the exact incident-critical C++ noise-calibration block with a
    # real host C++17 compiler. Replaying the original duplicate-name version
    # MUST fail: this catches the 26956 V1 NDK failure before full Gradle.
    compiler=shutil.which('clang++') or shutil.which('g++') or shutil.which('c++')
    if not compiler:fail('C++ compiler absent for original 26956 V1 shadowing regression')
    fragment='float slope=noiseSlope_,'+region.split('float slope=noiseSlope_,',1)[1].split('const float meanBlack=',1)[0]
    def check_cpp(code):
        unit='''#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
int main() {
 const std::array<int,2> offset{0,0};
 const bool rawNoiseMeasured_=true;
 const float noiseSlope_=0.001f,noiseOffset_=0.02f,referenceWhite_=1023.0f;
 const std::array<float,4> referenceBlack_{0.0f,0.0f,0.0f,0.0f};
 const std::array<float,4> rawNoiseSlope_{0.1f,0.1f,0.1f,0.1f};
 const std::array<float,4> rawNoiseOffset_{0.001f,0.001f,0.001f,0.001f};
'''+code+"\n if (!(slope >= 0.0f)) return 1; return 0;\n}\n"
        with tempfile.TemporaryDirectory(prefix='iris26956_cpp_regression_') as folder:
            name=Path(folder)/'actual_noise_calibration.cpp';name.write_text(unit)
            p=subprocess.run([compiler,'-std=c++17','-fsyntax-only',str(name)],text=True,capture_output=True)
        return p.returncode, p.stderr
    status,err=check_cpp(fragment)
    if status!=0:fail('corrected 26956 RAW HDRQ native C++ scope does not compile: '+err[:300])
    negative=fragment.replace('noiseVarianceOffset','offset')
    negstatus,negerr=check_cpp(negative)
    if negstatus==0 or not ('offset' in negerr and ('conflict' in negerr or 'redeclar' in negerr or 'redefinition' in negerr)):
        fail('original 26956 V1 name-collision compiler regression not detected')
    if 'hdrq_merge' not in executor or '{8, VK_DESCRIPTOR_TYPE_STORAGE_IMAGE}' not in executor:fail('shader descriptor binding 8 absent')
    if '--live' in sys.argv:
        # The completed +0.4EV shader, 26940 SDR color/tone and gainmap MUST be bit-identical to published 26955.
        for p in ('app/src/main/assets/shaders/motionv2/render.glsl',
                  'app/src/main/assets/shaders/motionv2/gainmap.glsl',
                  'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
                  'app/src/main/cpp/iris26864/vendor/rawr/native/multiframe/pipeline/src/HdrPlusRecorder.cpp'):
            h=hashlib.sha256((root/p).read_bytes()).hexdigest()
            if h!=old[p] or h!=new[p]:fail('successful 26955 protected SDR/UHDR/vendor source altered '+p)
    print('PASS current 26956 B HDRQ matched upstream motion+energy gate only, original four passes, +0.4EV unchanged, protected source 2047')
if __name__=='__main__':
    try:main()
    except Exception as e:print('26956 SOURCE BLOCKED '+str(e),file=sys.stderr);sys.exit(1)
