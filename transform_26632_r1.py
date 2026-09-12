#!/usr/bin/env python3
from pathlib import Path
import shutil, sys
if len(sys.argv)!=3: raise SystemExit('usage: transform_26632_r1.py BASE OUT')
base=Path(sys.argv[1]); out=Path(sys.argv[2])
if out.exists(): shutil.rmtree(out)
shutil.copytree(base,out)

def ro(rel,old,new):
 p=out/rel; s=p.read_text(); n=s.count(old)
 if n!=1: raise SystemExit(f'FAIL {rel}: anchor count {n} != 1: {old[:100]!r}')
 p.write_text(s.replace(old,new))
def rc(rel,old,new,nexp):
 p=out/rel; s=p.read_text(); n=s.count(old)
 if n!=nexp: raise SystemExit(f'FAIL {rel}: anchor count {n} != {nexp}: {old[:100]!r}')
 p.write_text(s.replace(old,new))

java='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java'
ro(java,
'''    /* IRIS_26631_CONTINUOUS_INTENT_QUOTIENT_GAINMAP\n     * Motion UHDR keeps the completed SDR as the exact primary. Its HDR rendition is a scalar\n     * luminance quotient in matched linear light, anchored at the existing 0.65 upper-tone entry.\n     * There is no fixed body boost and no nominal-white discontinuity. */\n    private static final float IRIS_26631_HDR_INTENT_MATCH_SOURCE_GUIDE = 0.65f;\n''',
'''    /* IRIS_26632_OUTPUT_REFERRED_HDR_PRESENTATION\n     * Motion UHDR keeps the completed SDR as exact appearance authority. The post-VGN master\n     * supplies only the spatial luminance guide for a continuous output-referred HDR expansion.\n     * No scene-linear/SDR quotient, no single match anchor, no hard threshold, and no RGB gain. */\n    private static final float IRIS_26632_HDR_GAIN_KNEE = 1.50f;\n''')
rc(java,'IRIS_26623_SPARSE_WHITE_ANCHOR = 0.925f','IRIS_26623_SPARSE_WHITE_ANCHOR = 0.945f',1)
rc(java,'IRIS_26623_BROAD_WHITE_ANCHOR = 0.885f','IRIS_26623_BROAD_WHITE_ANCHOR = 0.925f',1)
rc(java,'IRIS_26623_SPARSE_WHITE_SLOPE = 0.270f','IRIS_26623_SPARSE_WHITE_SLOPE = 0.360f',1)
rc(java,'IRIS_26623_BROAD_WHITE_SLOPE = 0.200f','IRIS_26623_BROAD_WHITE_SLOPE = 0.300f',1)
ro(java,
'''                                    + " bodyGainOwner=UNITY_UNTIL_HDR_INTENT_EXCEEDS_FINAL_SDR"\n                                    + " hdrGainSource=MATCHED_LINEAR_HDR_INTENT_OVER_FINAL_SDR_LUMINANCE"\n                                    + " hdrIntentMatchSourceGuide=" + IRIS_26631_HDR_INTENT_MATCH_SOURCE_GUIDE\n                                    + " fixedBodyGain=false nominalWhiteDiscontinuity=false"''',
'''                                    + " bodyGainOwner=CONTINUOUS_OUTPUT_REFERRED_SCALAR_EXPANSION"\n                                    + " hdrGainSource=POST_VGN_LUMINANCE_GUIDED_SDR_DISPLAY_EXPANSION"\n                                    + " hdrGainKnee=" + IRIS_26632_HDR_GAIN_KNEE\n                                    + " singleMatchAnchor=false fixedBodyGain=false nominalWhiteDiscontinuity=false"''')
ro(java,
'''                float actualPeakContentRatio = (float)Math.pow(\n                        Math.max(maxGainRatio, 1.001f), peakCode / 255.0f);\n                float fullHdrDisplayRatio = Math.max(1.02f, actualPeakContentRatio);''',
'''                float actualPeakContentRatio = (float)Math.pow(\n                        Math.max(maxGainRatio, 1.001f), peakCode / 255.0f);\n                /* IRIS_26632_UHDR_CAPACITY_EQUALS_ENCODING_RANGE\n                 * Capacity describes the display range over which the encoded gain map is\n                 * progressively applied; it is not the current scene's measured peak code. */\n                float fullHdrDisplayRatio = maxGainRatio;''')
ro(java,
'''                                    + " fullHdrDisplayRatio=" + fullHdrDisplayRatio''',
'''                                    + " fullHdrDisplayRatio=" + fullHdrDisplayRatio
                                    + " capacityMatchesGainMapMax=true actualPeakContentRatio=" + actualPeakContentRatio''')
ro(java,
'''                        + " motionHdrIntentMatchSourceGuide=" + IRIS_26631_HDR_INTENT_MATCH_SOURCE_GUIDE\n                        + " motionHdrGainIsScalarLuminanceOnly=true"\n                        + " motionHdrGainEquation=LINEAR_HDR_INTENT_OVER_FINAL_LINEAR_SDR"\n                        + " motionHdrFixedBodyGain=false motionHdrNominalWhiteGate=false"\n                        + " IRIS_26631_CONTINUOUS_INTENT_QUOTIENT_GAINMAP=true");''',
'''                        + " motionHdrGainKnee=" + IRIS_26632_HDR_GAIN_KNEE\n                        + " motionHdrGainIsScalarLuminanceOnly=true"\n                        + " motionHdrGainEquation=OUTPUT_REFERRED_SDR_TIMES_SOURCE_GUIDED_SCALAR_GAIN"\n                        + " motionHdrSingleMatchAnchor=false motionHdrFixedBodyGain=false motionHdrNominalWhiteGate=false"\n                        + " IRIS_26632_OUTPUT_REFERRED_HDR_PRESENTATION=true");''')
ro(java,
'''                + " hdrIntentMatchSourceGuide=" + IRIS_26631_HDR_INTENT_MATCH_SOURCE_GUIDE\n                + " uhdrLuminanceOnly=true uhdrContinuousIntentQuotient=true"''',
'''                + " hdrGainKnee=" + IRIS_26632_HDR_GAIN_KNEE\n                + " uhdrLuminanceOnly=true uhdrOutputReferredContinuousExpansion=true"''')
ro(java,
'''                    + " uhdrBodyGainOwner=UNITY_UNTIL_HDR_INTENT_EXCEEDS_FINAL_SDR"\n                    + " uhdrGainOwner=CONTINUOUS_LINEAR_INTENT_QUOTIENT"''',
'''                    + " uhdrBodyGainOwner=CONTINUOUS_OUTPUT_REFERRED_SCALAR_EXPANSION"\n                    + " uhdrGainOwner=POST_VGN_LUMINANCE_GUIDED_DISPLAY_EXPANSION"''')

# Same smoother global upper continuation in both 1x presentation owners.
for rel in ['app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/assets/shaders/motionv2/local_laplacian_global_log_26621.glsl']:
 rc(rel,'float targetWhite=mix(0.925,0.885,pressure);','float targetWhite=mix(0.945,0.925,pressure);',1)
 rc(rel,'float targetSlope=mix(0.270,0.200,pressure);','float targetSlope=mix(0.360,0.300,pressure);',1)
 rc(rel,'/* IRIS_26623_SCENE_ADAPTIVE_UPPER_TONE','/* IRIS_26632_SMOOTHER_UPPER_TONE\n * 26632 preserves the same pointwise/global owner and 0.65 entry but reserves more ordered SDR\n * range through source white. No spatial mask, edge boost, or local-protection change.\n *\n * IRIS_26623_SCENE_ADAPTIVE_UPPER_TONE',1)

gain='app/src/main/assets/shaders/motionv2/gainmap.glsl'
old='''    if(motionHdrHandoff!=0){\n        /* IRIS_26631_CONTINUOUS_INTENT_QUOTIENT_GAINMAP\n         * The gain map is the scalar luminance ratio between a registered HDR rendition intent\n         * and the exact completed SDR primary, both evaluated in linear light. The HDR intent is\n         * normalized at the unchanged source-guide 0.65 upper-tone entry, where the adaptive SDR\n         * map still equals its inherited body map. Above that point real scene radiance may exceed\n         * the compressed SDR continuously, including bright ceiling structure below source white.\n         * No fixed 1.25 floor, no nominal-white gate, no RGB gain, and no spatial smoothing. */\n        const float matchGuide=0.65;\n        float requested=max(displayGain,1.0e-6)*max(hdrExposureScale,1.0e-6);\n        float whiteAnchor=min(0.95,requested);\n        float bodyGain=requested;\n        if(requested>whiteAnchor)bodyGain=min(requested,4.0*whiteAnchor-1.0e-4);\n        float bodyRatio=max(bodyGain/max(whiteAnchor,1.0e-6)-1.0,0.0);\n        float oneMinus=1.0-matchGuide;\n        float cubic=whiteAnchor*matchGuide\n                +(bodyGain-whiteAnchor)*matchGuide*oneMinus*oneMinus;\n        float rational=bodyGain*matchGuide/(1.0+bodyRatio*matchGuide);\n        float mappedMatch=0.5*(cubic+rational);\n        float hdrIntentScale=mappedMatch/matchGuide;\n        float hdr=max(luminance(hdrPositive)*hdrIntentScale,0.0);\n        ratio=clamp((hdr+UHDR_OFFSET)/(sdr+UHDR_OFFSET),1.0,safeMax);\n    }else{'''
new='''    if(motionHdrHandoff!=0){\n        /* IRIS_26632_OUTPUT_REFERRED_HDR_PRESENTATION\n         * The completed SDR remains exact appearance authority. The post-VGN master contributes\n         * only a registered scalar luminance guide. A smooth log-domain display expansion builds\n         * the HDR rendition as SDR * gain(sourceY), so local SDR tone/detail can never create an\n         * accidental unity island. Gain is exactly 1 at black, continuous everywhere, approaches\n         * maxGainRatio asymptotically, and never changes RGB chromaticity or spatial geometry. */\n        const float gainKnee=1.50;\n        float sourceY=max(luminance(hdrPositive),0.0);\n        float weight=sourceY/(sourceY+gainKnee);\n        float logGain=log2(safeMax)*weight;\n        ratio=clamp(exp2(logGain),1.0,safeMax);\n    }else{'''
ro(gain,old,new)

cpp='app/src/main/cpp/motionv2_jpeg444_jni.cpp'
oldcpu='''if(p.motionHdrHandoff){/* IRIS_26631_CONTINUOUS_INTENT_QUOTIENT_GAINMAP_TRUE2X_CPU */const float matchGuide=0.65f;float mappedMatch=iris26621MapMotionSdrFinalGuide(matchGuide,p.displayGain);float hdrIntentScale=mappedMatch/matchGuide;float hdrY=std::max(luma(clampNonnegative(hdr))*hdrIntentScale,0.f),sdrY=std::max(luma(clampNonnegative(sdr)),0.f);ratio=clampf((hdrY+off)/(sdrY+off),1.f,contentMax);}else{'''
newcpu='''if(p.motionHdrHandoff){/* IRIS_26632_OUTPUT_REFERRED_HDR_PRESENTATION_TRUE2X_CPU */const float gainKnee=1.50f;float sourceY=std::max(luma(clampNonnegative(hdr)),0.f);float weight=sourceY/(sourceY+gainKnee);float logGain=std::log2(contentMax)*weight;ratio=clampf(std::exp2(logGain),1.f,contentMax);}else{'''
rc(cpp,oldcpu,newcpu,2)
oldgpu='''        if(uMotionHdrHandoff!=0){\n            /* IRIS_26631_CONTINUOUS_INTENT_QUOTIENT_GAINMAP_TRUE2X_GPU */\n            const float matchGuide=0.65;\n            float mappedMatch=iris26621MapMotionSdrFinalGuide(matchGuide);\n            float hdrIntentScale=mappedMatch/matchGuide;\n            float hdrY=max(irisLuma(irisClampNonnegative(hdr))*hdrIntentScale,0.0);\n            float sdrY=max(irisLuma(irisClampNonnegative(sdr)),0.0);\n            ratio=clamp((hdrY+off)/(sdrY+off),1.0,contentMax);\n        }else{'''
newgpu='''        if(uMotionHdrHandoff!=0){\n            /* IRIS_26632_OUTPUT_REFERRED_HDR_PRESENTATION_TRUE2X_GPU */\n            const float gainKnee=1.50;\n            float sourceY=max(irisLuma(irisClampNonnegative(hdr)),0.0);\n            float weight=sourceY/(sourceY+gainKnee);\n            float logGain=log2(contentMax)*weight;\n            ratio=clamp(exp2(logGain),1.0,contentMax);\n        }else{'''
ro(cpp,oldgpu,newgpu)

ultra='app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java'
ro(ultra,
'''            float fullHdrDisplayRatio = Math.max(\n                    1.02f, Math.min(safeMax, requestedFullHdrDisplayRatio));''',
'''            /* IRIS_26632_UHDR_CAPACITY_EQUALS_ENCODING_RANGE\n             * Motion advertises the same full-HDR display capacity as the gain-map encoding range.\n             * The scene's current peak gain remains content, not metadata capacity. Night retains\n             * its frozen requested-capacity policy. */\n            float fullHdrDisplayRatio = motionCapacityAuthority\n                    ? safeMax\n                    : Math.max(1.02f, Math.min(safeMax, requestedFullHdrDisplayRatio));''')
rc(ultra,'capacityMatchesActualGainPeak=true','capacityMatchesGainMapMax=true',1)
rc(ultra,'capacityMatchesActualGainPeak=" + motionCapacityAuthority','capacityMatchesGainMapMax=" + motionCapacityAuthority',1)
rc(ultra,'IRIS_26596_UHDR_ACTUAL_CONTENT_CAPACITY=','IRIS_26632_UHDR_ENCODING_CAPACITY_AUTHORITY=',1)

post='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java'
rc(post,'capacityMatchesActualGainPeak=true','capacityMatchesGainMapMax=true',1)

ro('app/version.properties','VERSION_NAME=0.9726631\nVERSION_BUILD=26631\n','VERSION_NAME=0.9726632\nVERSION_BUILD=26632\n')
print('PASS transform 26632 exact output-referred HDR + smoother global upper tone')
