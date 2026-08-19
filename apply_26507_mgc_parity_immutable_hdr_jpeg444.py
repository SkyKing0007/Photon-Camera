#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import argparse,re

ROOT: Path

def fail(msg:str): raise SystemExit('ERROR: '+msg)
def one(src:str, old:str, new:str, label:str)->str:
    n=src.count(old)
    if n!=1: fail(f'{label}: expected one anchor, found {n}')
    return src.replace(old,new,1)
def edit(rel:str, fn):
    p=ROOT/rel
    if not p.is_file(): fail('missing '+rel)
    before=p.read_text()
    after=fn(before)
    if after==before: fail(rel+': no change')
    p.write_text(after)
    print('CHANGED',rel)
def add(rel:str, text:str):
    p=ROOT/rel
    if p.exists(): fail('new file already exists '+rel)
    p.parent.mkdir(parents=True,exist_ok=True); p.write_text(text)
    print('ADDED',rel)

# --- MGC coordinate-contract parity ---
def guide(src:str)->str:
    if 'IRIS_26507_MGC_RAW_HALF_GUIDE_PARITY' in src: fail('guide already 26507')
    src=one(src,
        'float kw(int o){return o==0?0.5:0.25;}\n',
        '''float kw(int o){return o==0?0.5:0.25;}\nint mirrorGuideCoordinate(int coordinate,int extent){\n    const int borderPadding=1;\n    int maximum=max(borderPadding,extent-1-borderPadding);\n    coordinate=coordinate<borderPadding?2*borderPadding-coordinate:coordinate;\n    coordinate=coordinate>maximum?2*maximum-coordinate:coordinate;\n    return clamp(coordinate,0,max(extent-1,0));\n}\n''', 'guide mirror helper')
    src=one(src,
        ' ivec2 center=ivec2(gl_GlobalInvocationID.xy);if(any(greaterThanEqual(center,guideSize)))return;\n vec3 m0=vec3(0.0),m1=vec3(0.0),avg=vec3(0.0);float mg0=0.0,mg1=0.0,centerGreen=0.0;ivec2 base=center*2;\n for(int y=-1;y<=1;y++)for(int x=-1;x<=1;x++){vec4 rggb=canon(calculationQuad(base+ivec2(x,y)));',
        ''' ivec2 center=ivec2(gl_GlobalInvocationID.xy);if(any(greaterThanEqual(center,guideSize)))return;\n /* IRIS_26507_MGC_RAW_HALF_GUIDE_PARITY\n  * One guide texel == one 2x2 Bayer quad, matching current bjzhou/MGC.\n  * Previous Iris used RAW/4 and multiplied the quad coordinate twice.\n  */\n ivec2 mirroredCenter=ivec2(mirrorGuideCoordinate(center.x,guideSize.x),mirrorGuideCoordinate(center.y,guideSize.y));\n vec3 m0=vec3(0.0),m1=vec3(0.0),avg=vec3(0.0);float mg0=0.0,mg1=0.0,centerGreen=0.0;\n for(int y=-1;y<=1;y++)for(int x=-1;x<=1;x++){vec4 rggb=canon(calculationQuad(mirroredCenter+ivec2(x,y)));''', 'guide raw-half geometry')
    src=one(src,' vec4 physical=canon(physicalQuad(base));',
            ' vec4 physical=canon(physicalQuad(mirroredCenter));', 'guide physical center')
    return src

def covariance(src:str)->str:
    if 'IRIS_26507_MGC_RAW_HALF_COVARIANCE_PARITY' in src: fail('covariance already 26507')
    src=one(src,
        'vec4 canon(vec4 v){if(cfaPattern==0)return v;if(cfaPattern==1)return vec4(v.g,v.r,v.a,v.b);if(cfaPattern==2)return vec4(v.b,v.a,v.r,v.g);return vec4(v.a,v.b,v.g,v.r);}\n',
        '''vec4 canon(vec4 v){if(cfaPattern==0)return v;if(cfaPattern==1)return vec4(v.g,v.r,v.a,v.b);if(cfaPattern==2)return vec4(v.b,v.a,v.r,v.g);return vec4(v.a,v.b,v.g,v.r);}\nint mirrorGuideCoordinate(int coordinate,int extent){\n    const int borderPadding=1;\n    int maximum=max(borderPadding,extent-1-borderPadding);\n    coordinate=coordinate<borderPadding?2*borderPadding-coordinate:coordinate;\n    coordinate=coordinate>maximum?2*maximum-coordinate:coordinate;\n    return clamp(coordinate,0,max(extent-1,0));\n}\n''','covariance mirror helper')
    src=src.replace(' * Exact recovered structure-tensor equations at one sample per RAW/4 guide texel.\n',
                    ' * IRIS_26507_MGC_RAW_HALF_COVARIANCE_PARITY\n * Exact recovered structure-tensor equations at one sample per 2x2 Bayer quad (RAW/2).\n')
    src=one(src,
        '    float g0[9],g1[9];float gs=0.0,gs2=0.0;vec3 avg=vec3(0.0);ivec2 base=center*2;\n    for(int y=-1;y<=1;y++)for(int x=-1;x<=1;x++){\n        vec4 rggb=canon(qAt(base+ivec2(x,y)));',
        '''    ivec2 mirroredCenter=ivec2(mirrorGuideCoordinate(center.x,guideSize.x),mirrorGuideCoordinate(center.y,guideSize.y));\n    float g0[9],g1[9];float gs=0.0,gs2=0.0;vec3 avg=vec3(0.0);\n    for(int y=-1;y<=1;y++)for(int x=-1;x<=1;x++){\n        vec4 rggb=canon(qAt(mirroredCenter+ivec2(x,y)));''','covariance raw-half geometry')
    return src

def rejection(src:str)->str:
    if 'IRIS_26507_DYNAMIC_MGC_FLOW_THRESHOLD' in src: fail('rejection already 26507')
    src=one(src,'uniform vec3 currentNoiseRead;\nconst float FLOW_VARIATION_THRESHOLD=9.88235261e-5;\n',
        '''uniform vec3 currentNoiseRead;\nuniform float flowVariationThreshold;\n/* IRIS_26507_DYNAMIC_MGC_FLOW_THRESHOLD\n * Current MGC scales 1e-4 by 2016/guideWidth. The old fixed value assumed\n * a RAW/2 guide while Iris actually allocated RAW/4. Host now owns the exact\n * geometry-derived threshold.\n */\n''','dynamic flow threshold uniform')
    src=src.replace('if(flow.z<FLOW_VARIATION_THRESHOLD)unblocker=0.0;bool motionPrior=flow.z>FLOW_VARIATION_THRESHOLD;',
                    'if(flow.z<flowVariationThreshold)unblocker=0.0;bool motionPrior=flow.z>flowVariationThreshold;')
    return src

def contributor(src:str)->str:
    if 'IRIS_26507_COVARIANCE_QUAD_CENTER_UV' in src: fail('contributor already 26507')
    old='vec2 uv=clamp((sourceRaw+vec2(0.5))/vec2(rawSize),vec2(0.0),vec2(1.0));'
    new='vec2 uv=clamp((sourceRaw+vec2(1.0))/vec2(rawSize),vec2(0.0),vec2(1.0));'
    src=one(src,old,new,'covariance Bayer-quad center UV')
    marker='/* IRIS_26501_WRONSKI_PER_FRAME_SPATIAL_RGB_OWNER'
    src=one(src,marker,
        '/* IRIS_26507_COVARIANCE_QUAD_CENTER_UV\n * RAW/2 covariance texels are centered on sensor coordinates 2*q+1; therefore\n * normalized lookup is (sourceRaw+1)/rawSize.\n */\n\n'+marker,
        'covariance center marker')
    return src

# --- truly immutable auxiliary ownership ---
def motion_batch(src:str)->str:
    if 'IRIS_26507_IMMUTABLE_AUX_FREEZE' in src: fail('MotionBatch already 26507')
    if src.count('frame = candidate;') < 2: fail('MotionBatch slot frame assignment anchors missing')
    src=src.replace('frame = candidate;\n            return true;',
                    'frame = candidate;\n            notifyAll();\n            return true;',2)
    method_anchor='        public synchronized boolean hasFrame() { return frame != null; }\n        public synchronized boolean isSealed() { return sealed; }\n'
    helper='''        /* IRIS_26507_IMMUTABLE_AUX_FREEZE */
        private synchronized void awaitExpectedAndSeal(boolean expected,long deadlineNs) {
            while (expected && frame == null && !sealed) {
                long remainingNs=deadlineNs-System.nanoTime();
                if(remainingNs<=0L) break;
                long millis=remainingNs/1_000_000L;
                int nanos=(int)(remainingNs%1_000_000L);
                try { wait(millis,nanos); } catch (InterruptedException e) {
                    Thread.currentThread().interrupt(); break;
                }
            }
            sealed=true;
            notifyAll();
        }
'''
    idx=src.find(method_anchor)
    if idx<0: fail('ShadowAuxSlot method anchor missing')
    src=src[:idx]+helper+src[idx:]
    idx2=src.find(method_anchor, idx+len(helper)+len(method_anchor))
    if idx2<0: fail('ShortHighlightSlot method anchor missing')
    outer='''        /*
         * IRIS_26507_IMMUTABLE_AUX_FREEZE
         * One processing-side deadline for auxiliaries that were actually requested.
         * Shutter acknowledgement already happened; this does not gate capture response.
         * When this returns the slot contents are permanently immutable.
         */
        public void freezeExpectedAuxiliaries(boolean shortExpected,boolean shadowExpected,long timeoutMs) {
            long safeMs=Math.max(0L,Math.min(timeoutMs,120L));
            long deadlineNs=System.nanoTime()+safeMs*1_000_000L;
            awaitExpectedAndSeal(shortExpected,deadlineNs);
            shadowAuxSlot.awaitExpectedAndSeal(shadowExpected,deadlineNs);
        }
'''
    src=src[:idx2]+helper+outer+src[idx2:]
    return src

def capture_controller(src:str)->str:
    if 'IRIS_26507_FROZEN_AUX_BATCH_BOUNDARY' in src: fail('CaptureController already 26507')
    old='''        if (iris26486ShortTicket != null) scheduleMotion26486ShortDelivery(iris26486ShortTicket);
        final long iris26486ShotId = mMotionDiagnosticShotId;
'''
    new='''        if (iris26486ShortTicket != null) scheduleMotion26486ShortDelivery(iris26486ShortTicket);
        /* IRIS_26507_FROZEN_AUX_BATCH_BOUNDARY
         * Normal Wronski ownership is already frozen. Give only explicitly requested
         * auxiliaries one bounded processing-side completion window, then permanently
         * seal both slots. Any later exact callback is rejected by offer() and closed.
         */
        long iris26507FreezeStartNs=System.nanoTime();
        iris26486ShortSlot.freezeExpectedAuxiliaries(
                iris26480ShortHighlightRequested, iris26505LongRequested, 80L);
        long iris26507FreezeMs=(System.nanoTime()-iris26507FreezeStartNs)/1_000_000L;
        Log.i(TAG,"IRIS_26507_FROZEN_AUX_BATCH_BOUNDARY"
                +" shortExpected="+iris26480ShortHighlightRequested
                +" shortPresent="+iris26486ShortSlot.hasFrame()
                +" longExpected="+iris26505LongRequested
                +" longPresent="+iris26486ShortSlot.shadowAuxSlot.hasFrame()
                +" freezeWaitMs="+iris26507FreezeMs
                +" timeoutMs=80 lateOffersRejectedBySealedSlot=true shutterWait=false");
        final long iris26486ShotId = mMotionDiagnosticShotId;
'''
    return one(src,old,new,'auxiliary freeze at batch boundary')

def cfa_host(src:str)->str:
    if 'IRIS_26506_OPPONENT_CONFIDENCE_REFERENCE_CHROMA' not in src: fail('26507 host requires final 26506 candidate')
    if 'IRIS_26507_MGC_RAW_HALF_GUIDE_PARITY' in src: fail('host already 26507')
    src=one(src,
        'final Point iris26487GuideSize = new Point(Math.max(1,rawHalf.x/2),Math.max(1,rawHalf.y/2));',
        'final Point iris26487GuideSize = new Point(Math.max(1,rawHalf.x),Math.max(1,rawHalf.y));\n        /* IRIS_26507_MGC_RAW_HALF_GUIDE_PARITY */\n        final float iris26507FlowVariationThreshold = 2016.0f / Math.max(1.0f, iris26487GuideSize.x) * 1.0e-4f;',
        'MGC guide/covariance raw-half geometry')
    bind='                            glProg.setVar("currentNoiseRead",new float[]{iris26487WbNoise[3],iris26487WbNoise[4],iris26487WbNoise[5]});\n'
    src=one(src,bind,bind+'                            glProg.setVar("flowVariationThreshold",iris26507FlowVariationThreshold);\n',
            'normal dynamic MGC flow threshold bind')

    short_anchor='''                    glProg.setTexture("highlightProvenance",iris26492RecoveredProvenance);
                    glProg.setTextureCompute("outWeight",iris26501ShortWeight,true);
                    glProg.computeAutoDeferred(rawHalf,1);
'''
    short_mgc='''                    glProg.setTexture("highlightProvenance",iris26492RecoveredProvenance);
                    glProg.setTextureCompute("outWeight",iris26501ShortWeight,true);
                    glProg.computeAutoDeferred(rawHalf,1);

                    /* IRIS_26507_SHORT_A_SHARED_MGC_PRECHROMA_GATE */
                    float[] iris26507ShortGreenPhysicalNoise=iris26487GreenPhysicalNoise(
                            iris26501ShortSensorNoise,(int)parameters.cfaPattern);
                    glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/mfsr_bjzhou_guide",true);
                    glProg.setVar("rawSize",raw);glProg.setVar("guideSize",iris26487GuideSize);glProg.setVar("cfaPattern",(int)parameters.cfaPattern);
                    glProg.setVar("blackLevel",iris26490ShortBlack);glProg.setVar("whiteLevel",iris26490ShortWhite);glProg.setVar("exposureScale",iris26490ShortAlignmentScale);
                    glProg.setVar("wbR",r);glProg.setVar("wbB",b);
                    glProg.setVar("noiseShot",new float[]{iris26501ShortWbNoise[0],iris26501ShortWbNoise[1],iris26501ShortWbNoise[2]});
                    glProg.setVar("noiseRead",new float[]{iris26501ShortWbNoise[3],iris26501ShortWbNoise[4],iris26501ShortWbNoise[5]});
                    glProg.setTexture("rawTexture",iris26480ShortRaw);glProg.setTextureCompute("outputGuide",iris26487GuideScratch,true);glProg.computeAutoDeferred(iris26487GuideSize,1);
                    glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/mfsr_bjzhou_unblocker",true);
                    glProg.setVar("rawHalf",rawHalf);glProg.setVar("unblockerSize",iris26487UnblockerSize);glProg.setVar("cfaPattern",(int)parameters.cfaPattern);glProg.setVar("physicalExposureScale",iris26490ShortAlignmentScale);
                    glProg.setVar("greenShot",iris26507ShortGreenPhysicalNoise[0]);glProg.setVar("greenRead",iris26507ShortGreenPhysicalNoise[1]);
                    glProg.setTexture("physicalCfa",iris26480ShortCfa);glProg.setTextureCompute("outUnblocker",iris26487UnblockerScratch,true);glProg.computeAutoDeferred(iris26487UnblockerSize,1);
                    glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/mfsr_bjzhou_rejection_base",true);
                    glProg.setVar("rawHalf",rawHalf);glProg.setVar("guideSize",iris26487GuideSize);
                    glProg.setVar("referenceNoiseShot",new float[]{iris26487ReferenceWbNoise[0],iris26487ReferenceWbNoise[1],iris26487ReferenceWbNoise[2]});
                    glProg.setVar("referenceNoiseRead",new float[]{iris26487ReferenceWbNoise[3],iris26487ReferenceWbNoise[4],iris26487ReferenceWbNoise[5]});
                    glProg.setVar("currentNoiseShot",new float[]{iris26501ShortWbNoise[0],iris26501ShortWbNoise[1],iris26501ShortWbNoise[2]});
                    glProg.setVar("currentNoiseRead",new float[]{iris26501ShortWbNoise[3],iris26501ShortWbNoise[4],iris26501ShortWbNoise[5]});
                    glProg.setVar("flowVariationThreshold",iris26507FlowVariationThreshold);
                    glProg.setTexture("referenceGuide",wronskiReferenceGuide);glProg.setTexture("currentGuide",iris26487GuideScratch);
                    glProg.setTexture("flowTexture",iris26480ShortAlignment.flowTexture);glProg.setTexture("unblockerTexture",iris26487UnblockerScratch);
                    glProg.setTextureCompute("outReverseWeight",iris26487RejectFullA,true);glProg.setTextureCompute("outPixelDifference",iris26487RejectFullB,true);glProg.computeAutoDeferred(rawHalf,1);
                    glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/mfsr_bjzhou_clipped_gaussian_h",true);glProg.setVar("size",rawHalf);glProg.setTexture("inputEvidence",iris26487RejectFullB);glProg.setTextureCompute("outEvidence",iris26487RejectFullC,true);glProg.computeAutoDeferred(rawHalf,1);
                    glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/mfsr_bjzhou_clipped_gaussian_v",true);glProg.setVar("size",rawHalf);glProg.setTexture("inputEvidence",iris26487RejectFullC);glProg.setTextureCompute("outEvidence",iris26487RejectFullB,true);glProg.computeAutoDeferred(rawHalf,1);
                    glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/mfsr_bjzhou_rejection_reduce4",true);glProg.setVar("inputSize",rawHalf);glProg.setVar("outputSize",iris26487RejectSmallSize);glProg.setTexture("referenceGray",iris26488ReferenceGray);glProg.setTexture("inputRejection",iris26487RejectFullA);glProg.setTextureCompute("outLuma",iris26487RejectSmallLuma,true);glProg.setTextureCompute("outRejection",iris26487RejectSmallRaw,true);glProg.computeAutoDeferred(iris26487RejectSmallSize,1);
                    glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/mfsr_bjzhou_rejection_bilateral",true);glProg.setVar("smallSize",iris26487RejectSmallSize);glProg.setTexture("inputLuma",iris26487RejectSmallLuma);glProg.setTexture("inputRejection",iris26487RejectSmallRaw);glProg.setTextureCompute("outFiltered",iris26487RejectSmallFiltered,true);glProg.computeAutoDeferred(iris26487RejectSmallSize,1);
                    glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/mfsr_bjzhou_rejection_postprocess",true);glProg.setVar("fullSize",rawHalf);glProg.setVar("smallSize",iris26487RejectSmallSize);glProg.setTexture("originalRejection",iris26487RejectFullA);glProg.setTexture("filteredRejection",iris26487RejectSmallFiltered);glProg.setTexture("pixelDifference",iris26487RejectFullB);glProg.setTextureCompute("outRejection",iris26487RejectFullC,true);glProg.computeAutoDeferred(rawHalf,1);
                    glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/mfsr_bjzhou_rejection_dilate",true);glProg.setVar("inputSize",rawHalf);glProg.setVar("outputSize",iris26487MergeWeightSize);glProg.setTexture("inputRejection",iris26487RejectFullC);glProg.setTextureCompute("outWeight",iris26487FinalWeightScratch,true);glProg.computeAutoDeferred(iris26487MergeWeightSize,1);
'''
    src=one(src,short_anchor,short_mgc,'Short-A shared MGC rejection dispatch')
    src=one(src,
        '''                            iris26480ShortAlignment.flowTexture,iris26501ShortWeight,iris26501ShortCov,
                            iris26501ShortWeight,
                            (int)parameters.cfaPattern,iris26490ShortBlack,iris26490ShortWhite,
                            iris26490ShortAlignmentScale,r,b,
                            iris26501ShortWbNoise[1],iris26501ShortWbNoise[4],
                            false,false,true);''',
        '''                            iris26480ShortAlignment.flowTexture,iris26487FinalWeightScratch,iris26501ShortCov,
                            iris26501ShortWeight,
                            (int)parameters.cfaPattern,iris26490ShortBlack,iris26490ShortWhite,
                            iris26490ShortAlignmentScale,r,b,
                            iris26501ShortWbNoise[1],iris26501ShortWbNoise[4],
                            false,true,true);''',
        'Short-A MGC frame weight enabled')

    long_anchor='''                        irisV13ShadowFuseDispatchMs=(System.nanoTime()-irisV13FuseStart)/1000000L;
'''
    long_mgc=long_anchor+'''\n                        /* IRIS_26507_LONG_A_SHARED_MGC_PRECHROMA_GATE */
                        float[] iris26507ShadowGreenPhysicalNoise=iris26487GreenPhysicalNoise(
                                iris26501ShadowSensorNoise,(int)parameters.cfaPattern);
                        glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/mfsr_bjzhou_guide",true);
                        glProg.setVar("rawSize",raw);glProg.setVar("guideSize",iris26487GuideSize);glProg.setVar("cfaPattern",(int)parameters.cfaPattern);
                        glProg.setVar("blackLevel",shadowBlack);glProg.setVar("whiteLevel",shadowWhite);glProg.setVar("exposureScale",alignmentScale);
                        glProg.setVar("wbR",rr);glProg.setVar("wbB",bb);
                        glProg.setVar("noiseShot",new float[]{iris26501ShadowWbNoise[0],iris26501ShadowWbNoise[1],iris26501ShadowWbNoise[2]});
                        glProg.setVar("noiseRead",new float[]{iris26501ShadowWbNoise[3],iris26501ShadowWbNoise[4],iris26501ShadowWbNoise[5]});
                        glProg.setTexture("rawTexture",irisV13ShadowRaw);glProg.setTextureCompute("outputGuide",iris26487GuideScratch,true);glProg.computeAutoDeferred(iris26487GuideSize,1);
                        glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/mfsr_bjzhou_unblocker",true);
                        glProg.setVar("rawHalf",rawHalf);glProg.setVar("unblockerSize",iris26487UnblockerSize);glProg.setVar("cfaPattern",(int)parameters.cfaPattern);glProg.setVar("physicalExposureScale",alignmentScale);
                        glProg.setVar("greenShot",iris26507ShadowGreenPhysicalNoise[0]);glProg.setVar("greenRead",iris26507ShadowGreenPhysicalNoise[1]);
                        glProg.setTexture("physicalCfa",irisV13ShadowCfa);glProg.setTextureCompute("outUnblocker",iris26487UnblockerScratch,true);glProg.computeAutoDeferred(iris26487UnblockerSize,1);
                        glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/mfsr_bjzhou_rejection_base",true);
                        glProg.setVar("rawHalf",rawHalf);glProg.setVar("guideSize",iris26487GuideSize);
                        glProg.setVar("referenceNoiseShot",new float[]{iris26487ReferenceWbNoise[0],iris26487ReferenceWbNoise[1],iris26487ReferenceWbNoise[2]});
                        glProg.setVar("referenceNoiseRead",new float[]{iris26487ReferenceWbNoise[3],iris26487ReferenceWbNoise[4],iris26487ReferenceWbNoise[5]});
                        glProg.setVar("currentNoiseShot",new float[]{iris26501ShadowWbNoise[0],iris26501ShadowWbNoise[1],iris26501ShadowWbNoise[2]});
                        glProg.setVar("currentNoiseRead",new float[]{iris26501ShadowWbNoise[3],iris26501ShadowWbNoise[4],iris26501ShadowWbNoise[5]});
                        glProg.setVar("flowVariationThreshold",iris26507FlowVariationThreshold);
                        glProg.setTexture("referenceGuide",wronskiReferenceGuide);glProg.setTexture("currentGuide",iris26487GuideScratch);
                        glProg.setTexture("flowTexture",irisV13ShadowAlignment.flowTexture);glProg.setTexture("unblockerTexture",iris26487UnblockerScratch);
                        glProg.setTextureCompute("outReverseWeight",iris26487RejectFullA,true);glProg.setTextureCompute("outPixelDifference",iris26487RejectFullB,true);glProg.computeAutoDeferred(rawHalf,1);
                        glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/mfsr_bjzhou_clipped_gaussian_h",true);glProg.setVar("size",rawHalf);glProg.setTexture("inputEvidence",iris26487RejectFullB);glProg.setTextureCompute("outEvidence",iris26487RejectFullC,true);glProg.computeAutoDeferred(rawHalf,1);
                        glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/mfsr_bjzhou_clipped_gaussian_v",true);glProg.setVar("size",rawHalf);glProg.setTexture("inputEvidence",iris26487RejectFullC);glProg.setTextureCompute("outEvidence",iris26487RejectFullB,true);glProg.computeAutoDeferred(rawHalf,1);
                        glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/mfsr_bjzhou_rejection_reduce4",true);glProg.setVar("inputSize",rawHalf);glProg.setVar("outputSize",iris26487RejectSmallSize);glProg.setTexture("referenceGray",iris26488ReferenceGray);glProg.setTexture("inputRejection",iris26487RejectFullA);glProg.setTextureCompute("outLuma",iris26487RejectSmallLuma,true);glProg.setTextureCompute("outRejection",iris26487RejectSmallRaw,true);glProg.computeAutoDeferred(iris26487RejectSmallSize,1);
                        glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/mfsr_bjzhou_rejection_bilateral",true);glProg.setVar("smallSize",iris26487RejectSmallSize);glProg.setTexture("inputLuma",iris26487RejectSmallLuma);glProg.setTexture("inputRejection",iris26487RejectSmallRaw);glProg.setTextureCompute("outFiltered",iris26487RejectSmallFiltered,true);glProg.computeAutoDeferred(iris26487RejectSmallSize,1);
                        glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/mfsr_bjzhou_rejection_postprocess",true);glProg.setVar("fullSize",rawHalf);glProg.setVar("smallSize",iris26487RejectSmallSize);glProg.setTexture("originalRejection",iris26487RejectFullA);glProg.setTexture("filteredRejection",iris26487RejectSmallFiltered);glProg.setTexture("pixelDifference",iris26487RejectFullB);glProg.setTextureCompute("outRejection",iris26487RejectFullC,true);glProg.computeAutoDeferred(rawHalf,1);
                        glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/mfsr_bjzhou_rejection_dilate",true);glProg.setVar("inputSize",rawHalf);glProg.setVar("outputSize",iris26487MergeWeightSize);glProg.setTexture("inputRejection",iris26487RejectFullC);glProg.setTextureCompute("outWeight",iris26487FinalWeightScratch,true);glProg.computeAutoDeferred(iris26487MergeWeightSize,1);
'''
    src=one(src,long_anchor,long_mgc,'Long-A shared MGC rejection dispatch')
    src=one(src,
        '''                                irisV13ShadowAlignment.flowTexture,iris26501ShadowWeight,iris26501ShadowCov,
                                iris26501ShadowWeight,
                                (int)parameters.cfaPattern,shadowBlack,shadowWhite,alignmentScale,rr,bb,
                                iris26501ShadowWbNoise[1],iris26501ShadowWbNoise[4],
                                false,false,true);''',
        '''                                irisV13ShadowAlignment.flowTexture,iris26487FinalWeightScratch,iris26501ShadowCov,
                                iris26501ShadowWeight,
                                (int)parameters.cfaPattern,shadowBlack,shadowWhite,alignmentScale,rr,bb,
                                iris26501ShadowWbNoise[1],iris26501ShadowWbNoise[4],
                                false,true,true);''',
        'Long-A MGC frame weight enabled')

    geo='''        final int frameCount = images.size();
        final int tile = 8;
'''
    src=one(src,geo,
        '''        final int frameCount = images.size();
        final int tile = 8;
        Log.i(TAG,"IRIS_26507_MGC_GEOMETRY"
                +" raw="+raw.x+"x"+raw.y
                +" guide="+iris26487GuideSize.x+"x"+iris26487GuideSize.y
                +" rejection="+rawHalf.x+"x"+rawHalf.y
                +" mergeWeight="+iris26487MergeWeightSize.x+"x"+iris26487MergeWeightSize.y
                +" flowVariationThreshold="+iris26507FlowVariationThreshold
                +" guideContract=oneTexelPerBayerQuad"
                +" shortLongUseSameMgcPreChromaGate=true");
''','MGC geometry telemetry')
    return src

def short_weight(src:str)->str:
    if 'IRIS_26506_SHORT_A_SPATIAL_PROVENANCE_COHERENCE' not in src:
        fail('26507 Short topology requires final 26506 shader')
    if 'IRIS_26507_GPU_LOCAL_8_CONNECTED_SHORT_TOPOLOGY' in src:
        fail('Short weight already 26507')
    helper_anchor='''bool packedHasCensored(ivec2 p){
    for(int q=0;q<4;++q)if(abs(phaseState(p,q)-1.0)<0.25)return true;
    return false;
}
'''
    helper_new=helper_anchor+'''bool packedHasShortValidated(ivec2 p){
    for(int q=0;q<4;++q)if(abs(phaseState(p,q)-2.0)<0.25)return true;
    return false;
}
'''
    src=one(src,helper_anchor,helper_new,'Short validated pack helper')
    old='''    if(!packedHasCensored(p)){
        float boundaryRisk=smoothstep(
                0.04,0.40,neighborhoodCensoredFraction(p));
        float coherence=1.0-0.85*boundaryRisk;
        for(int q=0;q<4;++q){
            float state=mod(floor(code/phaseDivisor(q)),3.0);
            weight[q]=abs(state-2.0)<0.25?coherence:0.0;
        }
    }
'''
    new='''    if(!packedHasCensored(p)){
        /* IRIS_26507_GPU_LOCAL_8_CONNECTED_SHORT_TOPOLOGY */
        float connectedShortNeighbors=0.0;
        float unresolvedNeighbors=0.0;
        for(int oy=-1;oy<=1;++oy){
            for(int ox=-1;ox<=1;++ox){
                if(ox==0&&oy==0)continue;
                ivec2 q=p+ivec2(ox,oy);
                if(any(lessThan(q,ivec2(0)))||any(greaterThanEqual(q,packedSize)))continue;
                if(packedHasCensored(q))unresolvedNeighbors+=1.0;
                else if(packedHasShortValidated(q))connectedShortNeighbors+=1.0;
            }
        }
        float topologyGate=smoothstep(0.5,2.5,connectedShortNeighbors);
        float unresolvedGate=1.0-smoothstep(2.0,6.0,unresolvedNeighbors);
        float boundaryRisk=smoothstep(
                0.04,0.40,neighborhoodCensoredFraction(p));
        float coherence=(1.0-0.85*boundaryRisk)*topologyGate*unresolvedGate;
        for(int q=0;q<4;++q){
            float state=mod(floor(code/phaseDivisor(q)),3.0);
            weight[q]=abs(state-2.0)<0.25?coherence:0.0;
        }
    }
'''
    return one(src,old,new,'GPU local 8-connected Short topology')

def ultrahdr_java(src:str)->str:
    if 'IRIS_26507_FULL_HDR_DISPLAY_CAPACITY_PARITY' in src:
        fail('MotionV2UltraHdr already 26507')
    src=one(src,
        '    private static final float MIN_HDR_TRANSITION = 1.00f;\n',
        '''    private static final float MIN_HDR_TRANSITION = 1.00f;
    /* IRIS_26507_FULL_HDR_DISPLAY_CAPACITY_PARITY */
    private static final float DEFAULT_FULL_HDR_DISPLAY_RATIO = 1.6033f;
''',
        'full HDR display ratio constant')
    src=one(src,
        '            float safeMax = Math.max(1.50f, Math.min(2.5f, maxRatio));\n            Gainmap gainmap = new Gainmap(oriented);\n',
        '''            float safeMax = Math.max(1.50f, Math.min(2.5f, maxRatio));
            float fullHdrDisplayRatio = Math.max(
                    MIN_HDR_TRANSITION,
                    Math.min(safeMax, DEFAULT_FULL_HDR_DISPLAY_RATIO));
            Gainmap gainmap = new Gainmap(oriented);
''',
        'full HDR display capacity resolution')
    src=one(src,
        '            gainmap.setDisplayRatioForFullHdr(safeMax);\n',
        '            gainmap.setDisplayRatioForFullHdr(fullHdrDisplayRatio);\n',
        'full HDR display ratio metadata')
    src=one(src,
        '                    + " fullHdrDisplayRatio=" + safeMax\n',
        '                    + " fullHdrDisplayRatio=" + fullHdrDisplayRatio\n                    + " ratioMaxIndependentFromFullDisplayRatio=" + safeMax\n                    + " IRIS_26507_FULL_HDR_DISPLAY_CAPACITY_PARITY=true"\n',
        'UHDR telemetry')
    return src

def normalizer(src:str)->str:
    if 'IRIS_26506_SHORT_A_PHYSICAL_COLOR_PRIORITY' not in src:
        fail('26507 normalizer requires final 26506 candidate')
    if 'IRIS_26507_NO_STALE_SHORT_CHROMA_IMMUNITY' in src:
        fail('normalizer already 26507')
    old='''    bool centerShortProven=packedHasShortValidated(parentPacked)
            && !packedHasCensored(parentPacked);
    /* IRIS_26506_SHORT_A_PHYSICAL_COLOR_PRIORITY
     * A fully measured NORMAL/SHORT_VALIDATED quad is real sensor color. Do not
     * let the generic windy-foliage fallback override it. Mixed/censored Short-A
     * boundaries are handled by the dedicated Short semantic-coherence rule and
     * the 26504 post-LSC neutral exhaustion below.
     */
    float genericChromaPermission=centerShortProven?0.0:1.0;
'''
    new='''    /* IRIS_26507_NO_STALE_SHORT_CHROMA_IMMUNITY */
    float genericChromaPermission=1.0;
'''
    return one(src,old,new,'retire stale Short provenance chroma immunity')

def image_saver(src:str)->str:
    if 'IRIS_26507_MOTION_JPEG444' in src: fail('ImageSaver already 26507')
    imp='import com.particlesdevs.photoncamera.processing.ultrahdr.UltraHdrSaver;\n'
    src=one(src,imp,imp+'import com.particlesdevs.photoncamera.processing.ultrahdr.MotionV2Jpeg444Encoder;\n','JPEG444 import')
    old='''            try {\n                boolean saved;\n                try (OutputStream outputStream = Files.newOutputStream(fileToSave)) {\n                    saved = img.compress(\n                            Bitmap.CompressFormat.JPEG,\n                            jpgQuality,\n                            outputStream);\n                    outputStream.flush();\n                }\n                if (!saved) return false;\n\n                img.recycle();\n'''
    new='''            try {\n                /* IRIS_26507_MOTION_JPEG444\n                 * Encode the full-resolution RGB primary with TurboJPEG TJSAMP_444. If a\n                 * gain map is attached, package that already-compressed 4:4:4 base as JPEG_R\n                 * rather than asking Bitmap.compress() to re-encode it as 4:2:0.\n                 */\n                boolean saved = MotionV2Jpeg444Encoder.write(fileToSave, img, jpgQuality);\n                if (!saved) return false;\n\n                img.recycle();\n'''
    return one(src,old,new,'Motion JPEG 4:4:4 saver')

CMAKE_APPEND=r'''

# IRIS_26507_TRUE_JPEG444_JPEGR
set(IRIS26507_THIRD_PARTY ${CMAKE_CURRENT_SOURCE_DIR}/third_party_26507)
set(IRIS26507_JPEG ${IRIS26507_THIRD_PARTY}/libjpeg-turbo)
set(IRIS26507_UHDR ${IRIS26507_THIRD_PARTY}/libultrahdr)
if(NOT EXISTS ${IRIS26507_JPEG}/CMakeLists.txt)
    message(FATAL_ERROR "26507 pinned libjpeg-turbo source missing")
endif()
if(NOT EXISTS ${IRIS26507_UHDR}/lib/include/ultrahdr_api.h)
    message(FATAL_ERROR "26507 pinned libultrahdr source missing")
endif()
set(ENABLE_SHARED OFF CACHE BOOL "" FORCE)
set(ENABLE_STATIC ON CACHE BOOL "" FORCE)
set(WITH_TURBOJPEG ON CACHE BOOL "" FORCE)
set(REQUIRE_SIMD ON CACHE BOOL "" FORCE)
set(WITH_SIMD ON CACHE BOOL "" FORCE)
add_subdirectory(${IRIS26507_JPEG} ${CMAKE_CURRENT_BINARY_DIR}/iris26507-libjpeg-turbo)
find_package(Threads REQUIRED)
file(GLOB IRIS26507_UHDR_CORE "${IRIS26507_UHDR}/lib/src/*.cpp")
file(GLOB IRIS26507_UHDR_NEON "${IRIS26507_UHDR}/lib/src/dsp/arm/*.cpp")
file(GLOB_RECURSE IRIS26507_UHDR_IMAGE_IO "${IRIS26507_UHDR}/third_party/image_io/src/*.cc")
add_library(iris26507-ultrahdr STATIC ${IRIS26507_UHDR_CORE} ${IRIS26507_UHDR_NEON} ${IRIS26507_UHDR_IMAGE_IO})
set_target_properties(iris26507-ultrahdr PROPERTIES CXX_STANDARD 17 CXX_STANDARD_REQUIRED ON)
target_include_directories(iris26507-ultrahdr PRIVATE
    ${IRIS26507_UHDR}/lib/include
    ${IRIS26507_UHDR}/third_party/image_io/includes
    ${IRIS26507_UHDR}/third_party/image_io/src/modp_b64
    ${IRIS26507_UHDR}/third_party/image_io/src/modp_b64/modp_b64
    ${IRIS26507_JPEG}/src
    ${CMAKE_CURRENT_BINARY_DIR}/iris26507-libjpeg-turbo
    PUBLIC ${IRIS26507_UHDR})
target_compile_definitions(iris26507-ultrahdr PRIVATE UHDR_ENABLE_INTRINSICS UHDR_WRITE_ISO UHDR_WRITE_XMP)
target_compile_options(iris26507-ultrahdr PRIVATE -O3 -fno-lax-vector-conversions)
target_link_libraries(iris26507-ultrahdr PRIVATE jpeg-static Threads::Threads log z)
add_library(motionv2jpeg SHARED motionv2_jpeg444_jni.cpp motionv2_jpeg_r_encoder.cpp)
set_target_properties(motionv2jpeg PROPERTIES CXX_STANDARD 17 CXX_STANDARD_REQUIRED ON)
target_include_directories(motionv2jpeg PRIVATE
    ${IRIS26507_JPEG}/src
    ${CMAKE_CURRENT_BINARY_DIR}/iris26507-libjpeg-turbo
    ${IRIS26507_UHDR}/lib/include
    ${CMAKE_CURRENT_SOURCE_DIR})
target_link_libraries(motionv2jpeg PRIVATE turbojpeg-static iris26507-ultrahdr log jnigraphics android z)
'''

def cmake(src:str)->str:
    if 'IRIS_26507_TRUE_JPEG444_JPEGR' in src: fail('CMake already 26507')
    return src.rstrip()+CMAKE_APPEND+'\n'

JAVA_ENCODER=r'''package com.particlesdevs.photoncamera.processing.ultrahdr;

import android.graphics.Bitmap;
import android.graphics.Gainmap;
import android.os.Build;
import com.particlesdevs.photoncamera.util.Log;
import java.nio.file.Path;
import java.nio.file.Files;

/** IRIS_26507_TRUE_JPEG444_JPEGR */
public final class MotionV2Jpeg444Encoder {
    private static final String TAG="MotionV2Jpeg444Encoder";
    private static final int GAINMAP_QUALITY=95;
    static { System.loadLibrary("motionv2jpeg"); }
    private MotionV2Jpeg444Encoder(){}
    public static boolean write(Path output, Bitmap bitmap, int quality){
        if(output==null||bitmap==null||bitmap.isRecycled())return false;
        Path base=null,gain=null;
        try{
            boolean hasGain=Build.VERSION.SDK_INT>=34&&bitmap.hasGainmap();
            if(!hasGain){
                boolean ok=writeNative(bitmap,output.toString(),Math.max(1,Math.min(100,quality)));
                Log.i(TAG,"IRIS_26507_JPEG444 encoded="+ok+" gainmap=false subsampling=444");return ok;
            }
            Gainmap gm=bitmap.getGainmap(); if(gm==null)return false;
            base=output.resolveSibling("."+output.getFileName()+".26507.base.jpg");
            gain=output.resolveSibling("."+output.getFileName()+".26507.gain.jpg");
            Files.deleteIfExists(base);Files.deleteIfExists(gain);Files.deleteIfExists(output);
            if(!writeNative(bitmap,base.toString(),Math.max(1,Math.min(100,quality))))return false;
            Bitmap contents=gm.getGainmapContents();
            if(contents==null||contents.isRecycled()||!encodeGainmapNative(contents,gain.toString(),GAINMAP_QUALITY))return false;
            boolean ok=packageJpegRNative(base.toString(),gain.toString(),output.toString(),0,
                    gm.getRatioMin(),gm.getRatioMax(),gm.getGamma(),gm.getEpsilonSdr(),gm.getEpsilonHdr(),
                    gm.getMinDisplayRatioForHdrTransition(),gm.getDisplayRatioForFullHdr(),true)
                    && isJpegRNative(output.toString());
            Log.i(TAG,"IRIS_26507_JPEG444 encoded="+ok+" gainmap=true subsampling=444 jpegR="+ok);
            return ok;
        }catch(Throwable t){Log.e(TAG,"IRIS_26507_JPEG444_FAILED "+Log.getStackTraceString(t));return false;}
        finally{try{if(base!=null)Files.deleteIfExists(base);}catch(Throwable ignored){}try{if(gain!=null)Files.deleteIfExists(gain);}catch(Throwable ignored){}}
    }
    private static native boolean writeNative(Bitmap bitmap,String path,int quality);
    private static native boolean encodeGainmapNative(Bitmap bitmap,String path,int quality);
    private static native boolean packageJpegRNative(String base,String gain,String output,int gamut,
            float[] ratioMin,float[] ratioMax,float[] gamma,float[] epsSdr,float[] epsHdr,
            float displaySdr,float displayHdr,boolean useBaseColorSpace);
    private static native boolean isJpegRNative(String path);
}
'''

CPP_HEADER=r'''#pragma once
#include <array>
#include <string>
namespace iris26507 {
struct GainmapMetadata { std::array<float,3> ratioMin,ratioMax,gamma,epsilonSdr,epsilonHdr; float displaySdr=1.f,displayHdr=2.f; bool useBaseColorSpace=true; };
bool packageJpegR(const char* base,const char* gain,const char* out,int gamut,const GainmapMetadata& m,std::string* error);
bool isJpegR(const char* path);
}
'''

CPP_R=r'''#include "motionv2_jpeg_r_encoder.h"
#include <cstdio>
#include <limits>
#include <memory>
#include <vector>
#include <ultrahdr_api.h>
namespace iris26507 { namespace {
struct D{void operator()(uhdr_codec_private_t*p)const{if(p)uhdr_release_encoder(p);}}; using H=std::unique_ptr<uhdr_codec_private_t,D>;
bool readFile(const char*p,std::vector<unsigned char>*d){FILE*f=fopen(p,"rb");if(!f)return false;fseek(f,0,SEEK_END);long n=ftell(f);if(n<=0||fseek(f,0,SEEK_SET)){fclose(f);return false;}d->resize((size_t)n);size_t r=fread(d->data(),1,d->size(),f);int c=fclose(f);return r==d->size()&&c==0;}
bool writeFile(const char*p,const void*d,size_t n){FILE*f=fopen(p,"wb");if(!f)return false;size_t w=fwrite(d,1,n,f);int a=fflush(f),b=fclose(f);return w==n&&a==0&&b==0;}
bool status(const uhdr_error_info_t&s,const char*op,std::string*e){if(s.error_code==UHDR_CODEC_OK)return true;if(e){*e=op;if(s.has_detail&&s.detail[0]){*e+=": ";*e+=s.detail;}}return false;}
uhdr_color_gamut_t gamut(int g){switch(g){case UHDR_CG_BT_709:return UHDR_CG_BT_709;case UHDR_CG_DISPLAY_P3:return UHDR_CG_DISPLAY_P3;case UHDR_CG_BT_2100:return UHDR_CG_BT_2100;default:return UHDR_CG_UNSPECIFIED;}}
}
bool packageJpegR(const char*bp,const char*gp,const char*out,int cg,const GainmapMetadata&m,std::string*e){std::vector<unsigned char>b,g;if(!readFile(bp,&b)||!readFile(gp,&g)){if(e)*e="read JPEG failed";return false;}H h(uhdr_create_encoder());if(!h)return false;uhdr_compressed_image_t base{};base.data=b.data();base.data_sz=base.capacity=b.size();base.cg=gamut(cg);base.ct=UHDR_CT_SRGB;base.range=UHDR_CR_FULL_RANGE;uhdr_compressed_image_t gm{};gm.data=g.data();gm.data_sz=gm.capacity=g.size();gm.cg=UHDR_CG_UNSPECIFIED;gm.ct=UHDR_CT_UNSPECIFIED;gm.range=UHDR_CR_UNSPECIFIED;uhdr_gainmap_metadata_t md{};for(int i=0;i<3;i++){md.min_content_boost[i]=m.ratioMin[i];md.max_content_boost[i]=m.ratioMax[i];md.gamma[i]=m.gamma[i];md.offset_sdr[i]=m.epsilonSdr[i];md.offset_hdr[i]=m.epsilonHdr[i];}md.hdr_capacity_min=m.displaySdr;md.hdr_capacity_max=m.displayHdr;md.use_base_cg=m.useBaseColorSpace?1:0;if(!status(uhdr_enc_set_compressed_image(h.get(),&base,UHDR_BASE_IMG),"set base",e)||!status(uhdr_enc_set_gainmap_image(h.get(),&gm,&md),"set gain",e)||!status(uhdr_enc_set_output_format(h.get(),UHDR_CODEC_JPG),"set output",e)||!status(uhdr_encode(h.get()),"encode",e))return false;auto*enc=uhdr_get_encoded_stream(h.get());return enc&&enc->data&&enc->data_sz>0&&enc->data_sz<=(size_t)std::numeric_limits<int>::max()&&is_uhdr_image(enc->data,(int)enc->data_sz)&&writeFile(out,enc->data,enc->data_sz);}
bool isJpegR(const char*p){std::vector<unsigned char>d;return readFile(p,&d)&&d.size()<=(size_t)std::numeric_limits<int>::max()&&is_uhdr_image(d.data(),(int)d.size());}
}
'''

CPP_JNI=r'''#include <algorithm>
#include <android/bitmap.h>
#include <android/log.h>
#include <array>
#include <jni.h>
#include <cstdio>
#include <string>
#include <turbojpeg.h>
#include "motionv2_jpeg_r_encoder.h"
#define TAG "MotionV2Jpeg444"
namespace { struct U{JNIEnv*e;jstring s;const char*c;U(JNIEnv*e,jstring s):e(e),s(s),c(s?e->GetStringUTFChars(s,nullptr):nullptr){}~U(){if(c)e->ReleaseStringUTFChars(s,c);}};
bool write(const char*p,const unsigned char*d,size_t n){FILE*f=fopen(p,"wb");if(!f)return false;size_t w=fwrite(d,1,n,f);int a=fflush(f),b=fclose(f);return w==n&&a==0&&b==0;}
bool f3(JNIEnv*e,jfloatArray a,std::array<float,3>*o){if(!a||e->GetArrayLength(a)!=3)return false;e->GetFloatArrayRegion(a,0,3,o->data());return !e->ExceptionCheck();}}
extern "C" JNIEXPORT jboolean JNICALL Java_com_particlesdevs_photoncamera_processing_ultrahdr_MotionV2Jpeg444Encoder_writeNative(JNIEnv*e,jclass,jobject bitmap,jstring path,jint quality){AndroidBitmapInfo i{};if(!bitmap||!path||AndroidBitmap_getInfo(e,bitmap,&i)!=ANDROID_BITMAP_RESULT_SUCCESS||i.format!=ANDROID_BITMAP_FORMAT_RGBA_8888)return JNI_FALSE;void*p=nullptr;if(AndroidBitmap_lockPixels(e,bitmap,&p)!=ANDROID_BITMAP_RESULT_SUCCESS||!p)return JNI_FALSE;tjhandle h=tj3Init(TJINIT_COMPRESS);if(!h){AndroidBitmap_unlockPixels(e,bitmap);return JNI_FALSE;}int q=std::clamp((int)quality,1,100);bool cfg=tj3Set(h,TJPARAM_QUALITY,q)>=0&&tj3Set(h,TJPARAM_SUBSAMP,TJSAMP_444)>=0&&tj3Set(h,TJPARAM_OPTIMIZE,1)>=0;unsigned char*out=nullptr;size_t n=0;int rc=cfg?tj3Compress8(h,(const unsigned char*)p,(int)i.width,(int)i.stride,(int)i.height,TJPF_RGBA,&out,&n):-1;AndroidBitmap_unlockPixels(e,bitmap);U u(e,path);bool ok=rc>=0&&out&&n&&u.c&&write(u.c,out,n);if(out)tj3Free(out);tj3Destroy(h);return ok?JNI_TRUE:JNI_FALSE;}
extern "C" JNIEXPORT jboolean JNICALL Java_com_particlesdevs_photoncamera_processing_ultrahdr_MotionV2Jpeg444Encoder_encodeGainmapNative(JNIEnv*e,jclass,jobject bitmap,jstring path,jint quality){AndroidBitmapInfo i{};if(!bitmap||!path||AndroidBitmap_getInfo(e,bitmap,&i)!=ANDROID_BITMAP_RESULT_SUCCESS||(i.format!=ANDROID_BITMAP_FORMAT_A_8&&i.format!=ANDROID_BITMAP_FORMAT_RGBA_8888))return JNI_FALSE;void*p=nullptr;if(AndroidBitmap_lockPixels(e,bitmap,&p)!=ANDROID_BITMAP_RESULT_SUCCESS||!p)return JNI_FALSE;tjhandle h=tj3Init(TJINIT_COMPRESS);int pf=i.format==ANDROID_BITMAP_FORMAT_A_8?TJPF_GRAY:TJPF_RGBA;int ss=i.format==ANDROID_BITMAP_FORMAT_A_8?TJSAMP_GRAY:TJSAMP_444;int q=std::clamp((int)quality,1,100);bool cfg=h&&tj3Set(h,TJPARAM_QUALITY,q)>=0&&tj3Set(h,TJPARAM_SUBSAMP,ss)>=0&&tj3Set(h,TJPARAM_OPTIMIZE,1)>=0;unsigned char*out=nullptr;size_t n=0;int rc=cfg?tj3Compress8(h,(const unsigned char*)p,(int)i.width,(int)i.stride,(int)i.height,pf,&out,&n):-1;AndroidBitmap_unlockPixels(e,bitmap);U u(e,path);bool ok=rc>=0&&out&&n&&u.c&&write(u.c,out,n);if(out)tj3Free(out);if(h)tj3Destroy(h);return ok?JNI_TRUE:JNI_FALSE;}
extern "C" JNIEXPORT jboolean JNICALL Java_com_particlesdevs_photoncamera_processing_ultrahdr_MotionV2Jpeg444Encoder_packageJpegRNative(JNIEnv*e,jclass,jstring b,jstring g,jstring o,jint gamut,jfloatArray rmin,jfloatArray rmax,jfloatArray gamma,jfloatArray es,jfloatArray eh,jfloat ds,jfloat dh,jboolean use){U ub(e,b),ug(e,g),uo(e,o);if(!ub.c||!ug.c||!uo.c)return JNI_FALSE;iris26507::GainmapMetadata m;if(!f3(e,rmin,&m.ratioMin)||!f3(e,rmax,&m.ratioMax)||!f3(e,gamma,&m.gamma)||!f3(e,es,&m.epsilonSdr)||!f3(e,eh,&m.epsilonHdr))return JNI_FALSE;m.displaySdr=ds;m.displayHdr=dh;m.useBaseColorSpace=use==JNI_TRUE;std::string err;return iris26507::packageJpegR(ub.c,ug.c,uo.c,gamut,m,&err)?JNI_TRUE:JNI_FALSE;}
extern "C" JNIEXPORT jboolean JNICALL Java_com_particlesdevs_photoncamera_processing_ultrahdr_MotionV2Jpeg444Encoder_isJpegRNative(JNIEnv*e,jclass,jstring p){U u(e,p);return u.c&&iris26507::isJpegR(u.c)?JNI_TRUE:JNI_FALSE;}
'''

def main():
    global ROOT
    ap=argparse.ArgumentParser();ap.add_argument('root',type=Path);a=ap.parse_args();ROOT=a.root
    edit('app/src/main/assets/shaders/motionv2/mfsr_bjzhou_guide.glsl',guide)
    edit('app/src/main/assets/shaders/motionv2/mfsr_mgc_covariance.glsl',covariance)
    edit('app/src/main/assets/shaders/motionv2/mfsr_bjzhou_rejection_base.glsl',rejection)
    edit('app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_contribute_26501.glsl',contributor)
    edit('app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_short_weight_26501.glsl',short_weight)
    edit('app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_normalize_26501.glsl',normalizer)
    edit('app/src/main/java/com/particlesdevs/photoncamera/processing/MotionBatch.java',motion_batch)
    edit('app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',capture_controller)
    edit('app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java',cfa_host)
    edit('app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java',ultrahdr_java)
    edit('app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java',image_saver)
    edit('app/src/main/cpp/CMakeLists.txt',cmake)
    add('app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',JAVA_ENCODER)
    add('app/src/main/cpp/motionv2_jpeg_r_encoder.h',CPP_HEADER)
    add('app/src/main/cpp/motionv2_jpeg_r_encoder.cpp',CPP_R)
    add('app/src/main/cpp/motionv2_jpeg444_jni.cpp',CPP_JNI)
    print('PASS: 26507 root-fix transform applied: RAW/2 MGC + immutable auxiliaries + shared Short/Long pre-chroma rejection + GPU Short topology + UHDR capacity parity + JPEG444')
if __name__=='__main__':main()
