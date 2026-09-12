#!/usr/bin/env python3
from pathlib import Path
import shutil, sys
if len(sys.argv)!=3: raise SystemExit('usage: transform_26631_r1.py BASE OUT')
base=Path(sys.argv[1]); out=Path(sys.argv[2])
if out.exists(): shutil.rmtree(out)
shutil.copytree(base,out)

def replace_once(rel, old, new):
    p=out/rel; s=p.read_text(); n=s.count(old)
    if n!=1: raise SystemExit(f'FAIL {rel}: anchor count {n} != 1 for {old[:120]!r}')
    p.write_text(s.replace(old,new))
def replace_count(rel, old, new, expected):
    p=out/rel; s=p.read_text(); n=s.count(old)
    if n!=expected: raise SystemExit(f'FAIL {rel}: anchor count {n} != {expected} for {old[:120]!r}')
    p.write_text(s.replace(old,new))

java='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java'
replace_once(java,
'''    /* IRIS_26629_ANDROID_UHDR_LUMINANCE_ONLY_BODY_POP\n     * Android UHDR changes display luminance only. The SDR base remains byte/pixel/detail authority;\n     * 1.25 is the full-HDR recovery of the existing 0.80 SDR presentation scale. */\n    static final float IRIS_26629_MOTION_UHDR_BODY_LUMINANCE_RATIO = 1.25f;\n''',
'''    /* IRIS_26631_CONTINUOUS_INTENT_QUOTIENT_GAINMAP\n     * Motion UHDR keeps the completed SDR as the exact primary. Its HDR rendition is a scalar\n     * luminance quotient in matched linear light, anchored at the existing 0.65 upper-tone entry.\n     * There is no fixed body boost and no nominal-white discontinuity. */\n    private static final float IRIS_26631_HDR_INTENT_MATCH_SOURCE_GUIDE = 0.65f;\n''')
replace_once(java,
'''                                    + " bodyGainOwner=UHDR_SCALAR_LUMINANCE_ONLY"\n                                    + " hdrGainSource=SDR_BASE_PLUS_BODY_LUMINANCE_PLUS_SOURCE_HEADROOM"\n                                    + " sdrExposureScale=" + OUTPUT_EXPOSURE_SCALE\n                                    + " hdrExposureScale=" + HDR_EXPOSURE_SCALE);''',
'''                                    + " bodyGainOwner=UNITY_UNTIL_HDR_INTENT_EXCEEDS_FINAL_SDR"\n                                    + " hdrGainSource=MATCHED_LINEAR_HDR_INTENT_OVER_FINAL_SDR_LUMINANCE"\n                                    + " hdrIntentMatchSourceGuide=" + IRIS_26631_HDR_INTENT_MATCH_SOURCE_GUIDE\n                                    + " fixedBodyGain=false nominalWhiteDiscontinuity=false"\n                                    + " sdrExposureScale=" + OUTPUT_EXPOSURE_SCALE\n                                    + " hdrExposureScale=" + HDR_EXPOSURE_SCALE);''')
replace_once(java,
'''                        + " motionHdrBodyGainRatio=" + IRIS_26629_MOTION_UHDR_BODY_LUMINANCE_RATIO\n                        + " motionHdrGainIsScalarLuminanceOnly=true"\n                        + " motionHdrAdditionalHeadroomStartsAboveBodyRatio=true"\n                        + " IRIS_26629_ANDROID_UHDR_LUMINANCE_ONLY_BODY_POP=true");''',
'''                        + " motionHdrIntentMatchSourceGuide=" + IRIS_26631_HDR_INTENT_MATCH_SOURCE_GUIDE\n                        + " motionHdrGainIsScalarLuminanceOnly=true"\n                        + " motionHdrGainEquation=LINEAR_HDR_INTENT_OVER_FINAL_LINEAR_SDR"\n                        + " motionHdrFixedBodyGain=false motionHdrNominalWhiteGate=false"\n                        + " IRIS_26631_CONTINUOUS_INTENT_QUOTIENT_GAINMAP=true");''')
replace_once(java,
'''                + " nominalHdrBodyRecoveryRatio="\n                    + IRIS_26629_MOTION_UHDR_BODY_LUMINANCE_RATIO\n                + " uhdrLuminanceOnly=true uhdrSdrDetailOneToOne=true"''',
'''                + " hdrIntentMatchSourceGuide=" + IRIS_26631_HDR_INTENT_MATCH_SOURCE_GUIDE\n                + " uhdrLuminanceOnly=true uhdrContinuousIntentQuotient=true"''')
replace_once(java,
'''                    + " uhdrBodyGainOwner=SCALAR_GAINMAP_ONLY"\n                    + " uhdrSdrDetailOneToOne=true"''',
'''                    + " uhdrBodyGainOwner=UNITY_UNTIL_HDR_INTENT_EXCEEDS_FINAL_SDR"\n                    + " uhdrGainOwner=CONTINUOUS_LINEAR_INTENT_QUOTIENT"''')

gain='app/src/main/assets/shaders/motionv2/gainmap.glsl'
replace_once(gain,'float max3(vec3 v){return max(v.r,max(v.g,v.b));}\n','')
old='''    if(motionHdrHandoff!=0){\n        /* IRIS_26629_ANDROID_UHDR_LUMINANCE_ONLY_BODY_POP\n         * The completed SDR base remains the sole detail/color/tone authority. Android Ultra HDR\n         * receives only a single-channel scalar display-luminance gain: recover the intentional\n         * 1.00/0.80 = 1.25 body headroom at full HDR display capacity, while genuine >1.25\n         * scene headroom may rise farther. No alternate HDR detail image is divided by SDR and\n         * no RGB-channel-specific gain is introduced. */\n        const float bodyLuminanceRatio=1.25;\n        const float nominalWhiteEpsilon=1.0e-4;\n        float sourceGuide=max(max3(hdrPositive),luminance(hdrPositive));\n        /* IRIS_26630_UHDR_BLACK_UNITY_EPSILON\n         * Canonical SDR remains exact through nominal source white. Only proven extended-linear\n         * headroom above 1.0+epsilon may receive Motion HDR gain; black/body pixels therefore\n         * encode exact zero gain instead of the old unconditional 1.25 floor. */\n        ratio=sourceGuide<=1.0+nominalWhiteEpsilon\n                ?1.0\n                :clamp(max(sourceGuide,bodyLuminanceRatio),1.0,safeMax);\n    }else{'''
new='''    if(motionHdrHandoff!=0){\n        /* IRIS_26631_CONTINUOUS_INTENT_QUOTIENT_GAINMAP\n         * The gain map is the scalar luminance ratio between a registered HDR rendition intent\n         * and the exact completed SDR primary, both evaluated in linear light. The HDR intent is\n         * normalized at the unchanged source-guide 0.65 upper-tone entry, where the adaptive SDR\n         * map still equals its inherited body map. Above that point real scene radiance may exceed\n         * the compressed SDR continuously, including bright ceiling structure below source white.\n         * No fixed 1.25 floor, no nominal-white gate, no RGB gain, and no spatial smoothing. */\n        const float matchGuide=0.65;\n        float requested=max(displayGain,1.0e-6)*max(hdrExposureScale,1.0e-6);\n        float whiteAnchor=min(0.95,requested);\n        float bodyGain=requested;\n        if(requested>whiteAnchor)bodyGain=min(requested,4.0*whiteAnchor-1.0e-4);\n        float bodyRatio=max(bodyGain/max(whiteAnchor,1.0e-6)-1.0,0.0);\n        float oneMinus=1.0-matchGuide;\n        float cubic=whiteAnchor*matchGuide\n                +(bodyGain-whiteAnchor)*matchGuide*oneMinus*oneMinus;\n        float rational=bodyGain*matchGuide/(1.0+bodyRatio*matchGuide);\n        float mappedMatch=0.5*(cubic+rational);\n        float hdrIntentScale=mappedMatch/matchGuide;\n        float hdr=max(luminance(hdrPositive)*hdrIntentScale,0.0);\n        ratio=clamp((hdr+UHDR_OFFSET)/(sdr+UHDR_OFFSET),1.0,safeMax);\n    }else{'''
replace_once(gain,old,new)

cpp='app/src/main/cpp/motionv2_jpeg444_jni.cpp'
oldcpu='''if(p.motionHdrHandoff){Vec3 hp=clampNonnegative(hdr);float sourceGuide=std::max(peak(hp),luma(hp));ratio=sourceGuide<=1.0f+1.0e-4f?1.f:clampf(std::max(sourceGuide,1.25f),1.f,contentMax);}else{'''
newcpu='''if(p.motionHdrHandoff){/* IRIS_26631_CONTINUOUS_INTENT_QUOTIENT_GAINMAP_TRUE2X_CPU */const float matchGuide=0.65f;float mappedMatch=iris26621MapMotionSdrFinalGuide(matchGuide,p.displayGain);float hdrIntentScale=mappedMatch/matchGuide;float hdrY=std::max(luma(clampNonnegative(hdr))*hdrIntentScale,0.f),sdrY=std::max(luma(clampNonnegative(sdr)),0.f);ratio=clampf((hdrY+off)/(sdrY+off),1.f,contentMax);}else{'''
replace_count(cpp,oldcpu,newcpu,2)
oldgpu='''        if(uMotionHdrHandoff!=0){\n            vec3 hp=irisClampNonnegative(hdr);\n            float sourceGuide=max(irisPeak(hp),irisLuma(hp));\n            ratio=sourceGuide<=1.0+1.0e-4?1.0:clamp(max(sourceGuide,1.25),1.0,contentMax);\n        }else{'''
newgpu='''        if(uMotionHdrHandoff!=0){\n            /* IRIS_26631_CONTINUOUS_INTENT_QUOTIENT_GAINMAP_TRUE2X_GPU */\n            const float matchGuide=0.65;\n            float mappedMatch=iris26621MapMotionSdrFinalGuide(matchGuide);\n            float hdrIntentScale=mappedMatch/matchGuide;\n            float hdrY=max(irisLuma(irisClampNonnegative(hdr))*hdrIntentScale,0.0);\n            float sdrY=max(irisLuma(irisClampNonnegative(sdr)),0.0);\n            ratio=clamp((hdrY+off)/(sdrY+off),1.0,contentMax);\n        }else{'''
replace_once(cpp,oldgpu,newgpu)
replace_once('app/version.properties','VERSION_NAME=0.9726630\nVERSION_BUILD=26630\n','VERSION_NAME=0.9726631\nVERSION_BUILD=26631\n')
print('PASS transform 26631 exact 4-file deterministic correction')
