#!/usr/bin/env python3
from pathlib import Path
import argparse, ast, base64, gzip, hashlib, re

def load_hash_contract(path):
    rows={}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line=line.strip()
        if not line or line.startswith("#"): continue
        parts=line.split(None,1)
        if len(parts)!=2 or not re.fullmatch(r'[0-9a-f]{64}', parts[0]):
            raise RuntimeError("invalid exact-26532 owner hash contract line: "+line)
        h,rel=parts[0],parts[1].strip()
        if rel in rows:
            raise RuntimeError("duplicate exact-26532 owner hash contract path: "+rel)
        rows[rel]=h
    return rows

REQUIRED_26532_BASE_OWNERS = (
    'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java',
    'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
)

RCD_HASHES = {
 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2RcdDemosaic.java':'754beea951bdea2fbde31988011a36ee1c77bf35fc503b383529c00b9031cd40',
 'app/src/main/assets/shaders/motionv2/rcd26489_diag_direction.glsl':'1bd8f80b12e06f5ab8c19bb65d27e60f31998327557df0e6f551c682bdfc2b0e',
 'app/src/main/assets/shaders/motionv2/rcd26489_diag_residual.glsl':'47e7041976905fb76a54acb36e19d30d4d29d8e4dd9d25012f0515978170a2e3',
 'app/src/main/assets/shaders/motionv2/rcd26489_green.glsl':'4f268056ae8d8f1da8ae5b3936768cbb7d3841f9ac4e4b54ac6f113ca6a55040',
 'app/src/main/assets/shaders/motionv2/rcd26489_green_rb.glsl':'b0476f9e5a7b130d7c3edc58b7ba4a033edc5fa2c55605fd446feea8e1b3e4ca',
 'app/src/main/assets/shaders/motionv2/rcd26489_lpf.glsl':'95dff8fa0f3c4420de8e13346b766c7a2a80f76b08634b3b8135f775cac06a0c',
 'app/src/main/assets/shaders/motionv2/rcd26489_opposite.glsl':'30e732e00e50aeca0d29d08529230c3d043b81e8df87b0c4504768e89fe80392',
 'app/src/main/assets/shaders/motionv2/rcd26489_populate.glsl':'69ecf068e9229e521ba29e033c4bb0ee48d9919e34cd65525b4d9125a30270aa',
 'app/src/main/assets/shaders/motionv2/rcd26489_vh_direction.glsl':'66831dfd1a39a4b5866631f1058a2883dd237961f33cc4c0bd169a7e02a0873e',
 'app/src/main/assets/shaders/motionv2/rcd26489_write.glsl':'0c3b66a45d0bd8288188c9963cf2b1c7abf0341bb08c59136cdbdd3dc458d346',
}

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def one(s, old, new, label):
    n=s.count(old)
    if n!=1: raise RuntimeError(f'{label}: expected 1 anchor, found {n}')
    return s.replace(old,new,1)
def write(root, rel, text):
    p=root/rel; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(text,encoding='utf-8')

def import_rcd(root, historical_transform):
    src=Path(historical_transform).read_text(encoding='utf-8')
    tree=ast.parse(src)
    blobs=None
    for node in tree.body:
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='BLOBS' for t in node.targets):
            blobs=ast.literal_eval(node.value); break
    if not isinstance(blobs,dict): raise RuntimeError('historical RCD BLOBS dictionary missing')
    for rel, expected in RCD_HASHES.items():
        enc=blobs.get(rel)
        if not enc: raise RuntimeError('historical RCD payload missing: '+rel)
        data=gzip.decompress(base64.b64decode(enc))
        got=hashlib.sha256(data).hexdigest()
        if got!=expected: raise RuntimeError(f'RCD payload hash mismatch {rel}: {got}')
        p=root/rel; p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(data)

def clone_night_bridge(root):
    srcp=root/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt'
    src=srcp.read_text(encoding='utf-8')
    if 'object PhotonMotionMgc1271Bridge' not in src: raise RuntimeError('Motion MGC bridge object missing')
    if src.count('outputMode = MgcSpatialOutputMode.RGB')!=1: raise RuntimeError('Motion bridge RGB output anchor mismatch')
    if src.count('mergeMethod = MgcMergeMethod.SPATIAL_RGB')!=1: raise RuntimeError('Motion bridge SPATIAL_RGB anchor mismatch')
    night=src.replace('object PhotonMotionMgc1271Bridge','object IrisNightMgc1271Bridge',1)
    night=night.replace('IRIS_26512_MGC1271_SPATIAL_RGB_PARITY_OWNER','IRIS_26533_NIGHT_MGC1271_SPATIAL_BAYER_OWNER')
    night=night.replace('outputMode = MgcSpatialOutputMode.RGB','outputMode = MgcSpatialOutputMode.BAYER',1)
    night=night.replace('mergeMethod = MgcMergeMethod.SPATIAL_RGB','mergeMethod = MgcMergeMethod.SPATIAL_BAYER',1)
    # Native 12MP Night never requests the 2x Spatial RGB detail branch. It still requests
    # the validated normal RAW16 sidecar, which is the RCD/DNG authority.
    night=night.replace('fixedOutputScale = requestedOutputScale', 'fixedOutputScale = 1.0f') if 'fixedOutputScale = requestedOutputScale' in night else night
    write(root,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightMgc1271Bridge.kt',night)

def add_parameters(root):
    p=root/'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java'
    s=p.read_text(encoding='utf-8')
    anchor='public boolean motionV2Active = false;'
    if anchor not in s:
        # candidate variants may initialize without explicit false
        anchor='public boolean motionV2Active;'
    if anchor not in s: raise RuntimeError('Parameters motionV2Active anchor missing')
    s=one(s,anchor,anchor+'\n    /* IRIS_26533_NIGHT_DOMAIN_OWNER */\n    public boolean irisNightActive = false;','Parameters Night flag')
    p.write_text(s,encoding='utf-8')

def add_night_exposure(root):
    text=r'''package com.particlesdevs.photoncamera.processing.parameters;

import android.hardware.camera2.CaptureRequest;
import android.hardware.camera2.CaptureResult;
import com.particlesdevs.photoncamera.api.CameraMode;
import com.particlesdevs.photoncamera.app.PhotonCamera;
import com.particlesdevs.photoncamera.capture.CaptureController;
import com.particlesdevs.photoncamera.util.Log;
import java.util.ArrayList;
import java.util.List;

/** IRIS_26533_NIGHT_EXPOSURE_SOLE_OWNER
 * Iris Night uses HAL preview metering only as scene measurement. Photon Night's
 * GenerateExpoPair/night shutter curve/fullpairs are not used.
 */
public final class IrisNightExposureSelector {
    private static final String TAG="IrisNightExposure";
    private static final ArrayList<IsoExpoSelector.ExpoPair> PAIRS=new ArrayList<>();
    public static volatile long lastSelectedExposure=0L;
    public static volatile String diagnostics="";
    private IrisNightExposureSelector(){}
    public static synchronized List<IsoExpoSelector.ExpoPair> snapshotPairs(){
        ArrayList<IsoExpoSelector.ExpoPair> out=new ArrayList<>();
        for(IsoExpoSelector.ExpoPair p:PAIRS)out.add(new IsoExpoSelector.ExpoPair(p));
        return out;
    }
    private static long clamp(long v,long lo,long hi){return Math.max(lo,Math.min(hi,v));}
    private static long motionCap(){
        if(PhotonCamera.getGyro()==null)return ExposureIndex.sec/15;
        int s=Math.max(0,PhotonCamera.getGyro().getFilteredShakiness());
        if(s<=30)return ExposureIndex.sec/4;
        if(s<=70)return ExposureIndex.sec/8;
        if(s<=150)return ExposureIndex.sec/15;
        return ExposureIndex.sec/30;
    }
    private static long antiFlicker(long desired,long cap){
        CaptureResult r=CaptureController.mPreviewCaptureResult;
        Integer ab=r==null?null:r.get(CaptureResult.CONTROL_AE_ANTIBANDING_MODE);
        long q=(ab!=null&&ab==CaptureResult.CONTROL_AE_ANTIBANDING_MODE_50HZ)?ExposureIndex.sec/100:ExposureIndex.sec/120;
        desired=Math.min(desired,cap); if(desired<q)return desired;
        long n=Math.max(1,Math.round((double)desired/q));
        while(n*q>cap&&n>1)n--;
        return n*q;
    }
    public static synchronized void setExpo(CaptureRequest.Builder b,int step,CaptureController c){
        if(step==0)PAIRS.clear();
        long lo=IsoExpoSelector.getEXPLOW(), hi=IsoExpoSelector.getEXPHIGH();
        int isoLo=IsoExpoSelector.getISOLOW(), isoHi=IsoExpoSelector.getISOHIGH();
        int analog=IsoExpoSelector.getISOAnalog();
        double comp=Math.pow(2.0,PhotonCamera.getSettings().exposureCompensation);
        // Protect point lights by metering about 0.70 EV below HAL preview energy; multiframe
        // accumulation + neural illumination recovery restores dark regions without brackets.
        double energy=Math.max(1.0,c.mPreviewExposureTime*(double)Math.max(1,c.mPreviewIso))*comp/Math.pow(2.0,0.70);
        boolean tripod=PhotonCamera.getGyro()!=null&&PhotonCamera.getGyro().getTripod();
        long cap=tripod?Math.min(hi,ExposureIndex.sec*2):Math.min(hi,motionCap());
        long desired=(long)Math.round(energy/Math.max(100,isoLo));
        long exposure=clamp(antiFlicker(clamp(desired,lo,cap),cap),lo,hi);
        int iso=(int)Math.round(energy/Math.max(1.0,exposure)); iso=Math.max(isoLo,Math.min(isoHi,iso));
        double manE=c.getParamController().getCurrentExposureValue();
        double manI=c.getParamController().getCurrentISOValue();
        if(manE!=0)exposure=clamp((long)manE,lo,hi); if(manI!=0)iso=Math.max(isoLo,Math.min(isoHi,(int)manI));
        IsoExpoSelector.ExpoPair p=new IsoExpoSelector.ExpoPair(exposure,lo,hi,iso,isoLo,isoHi,analog);
        p.curlayer=IsoExpoSelector.ExpoPair.exposureLayer.Normal; p.layerMpy=1.0f;
        PAIRS.add(p); lastSelectedExposure=exposure;
        b.set(CaptureRequest.CONTROL_AE_MODE,CaptureRequest.CONTROL_AE_MODE_OFF);
        b.set(CaptureRequest.SENSOR_EXPOSURE_TIME,exposure); b.set(CaptureRequest.SENSOR_SENSITIVITY,iso);
        diagnostics="IRIS_26533_NIGHT_EXPOSURE requestedNs="+exposure+" iso="+iso+" capNs="+cap+" tripod="+tripod+" equalExposure=true photonNightCurve=false";
        Log.i(TAG,diagnostics);
    }
}
'''
    write(root,'app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/IrisNightExposureSelector.java',text)
    text2=r'''package com.particlesdevs.photoncamera.processing.parameters;
import com.particlesdevs.photoncamera.app.PhotonCamera;
/** IRIS_26533_NIGHT_FRAMECOUNT_SOLE_OWNER */
public final class IrisNightFrameSelector {
    private IrisNightFrameSelector(){}
    public static int getFrames(){
        int max=Math.max(2,PhotonCamera.getSettings().frameCount);
        int iso=Math.max(100,PhotonCamera.getCaptureController().mPreviewIso);
        int wanted=iso>=3200?15:iso>=1600?13:iso>=800?11:9;
        int n=Math.max(2,Math.min(max,wanted));
        FrameNumberSelector.frameCount=n; FrameNumberSelector.throwCount=0;
        return n;
    }
}
'''
    write(root,'app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/IrisNightFrameSelector.java',text2)

def patch_capture(root):
    p=root/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java'; s=p.read_text(encoding='utf-8')
    imp='import com.particlesdevs.photoncamera.processing.parameters.IsoExpoSelector;'
    s=one(s,imp,imp+'\nimport com.particlesdevs.photoncamera.processing.parameters.IrisNightExposureSelector;','Capture Night import')
    # First call is under a one-line RAWVIDEO if; replace the whole construct to avoid dangling-else.
    first='''if(!PhotonCamera.getSettings().selectedMode.equals(CameraMode.RAWVIDEO))
                        IsoExpoSelector.setExpo(captureBuilder, i, this);
                    else {'''
    first_new='''if(!PhotonCamera.getSettings().selectedMode.equals(CameraMode.RAWVIDEO)) {
                        if (PhotonCamera.getSettings().selectedMode == CameraMode.NIGHT) {
                            IrisNightExposureSelector.setExpo(captureBuilder, i, this);
                        } else {
                            IsoExpoSelector.setExpo(captureBuilder, i, this);
                        }
                    } else {'''
    s=one(s,first,first_new,'Capture first Night/RAWVIDEO exposure routing')
    # Second call is the ordinary finite burst loop and can be replaced directly.
    second='''                    IsoExpoSelector.setExpo(captureBuilder, i, this);
                    times[i] = IsoExpoSelector.lastSelectedExposure;'''
    second_new='''                    if (PhotonCamera.getSettings().selectedMode == CameraMode.NIGHT) {
                        IrisNightExposureSelector.setExpo(captureBuilder, i, this);
                    } else {
                        IsoExpoSelector.setExpo(captureBuilder, i, this);
                    }
                    times[i] = PhotonCamera.getSettings().selectedMode == CameraMode.NIGHT
                            ? IrisNightExposureSelector.lastSelectedExposure
                            : IsoExpoSelector.lastSelectedExposure;'''
    s=one(s,second,second_new,'Capture finite-burst Night exposure routing')
    if s.count('IrisNightExposureSelector.setExpo(captureBuilder, i, this);') != 2:
        raise RuntimeError('Night exposure routing must have exactly two call sites')
    p.write_text(s,encoding='utf-8')

def patch_frame_selector(root):
    p=root/'app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/FrameNumberSelector.java'; s=p.read_text(encoding='utf-8')
    anchor='public static int getFrames() {'
    s=one(s,anchor,anchor+'\n        if (PhotonCamera.getSettings().selectedMode == CameraMode.NIGHT) return IrisNightFrameSelector.getFrames();','Frame selector Night dispatch')
    p.write_text(s,encoding='utf-8')

def clone_current_rcd(root):
    srcp=root/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2RcdDemosaic.java'
    src=srcp.read_text(encoding='utf-8')
    required=('IRIS_26498_PROVENANCE_INSIDE_RCD_AND_TRUE_MIRRORED_BOUNDARY','motionv2/rcd26498_populate','motionv2/rcd26498_write','motionv2/rcd26489_diag_direction')
    for tok in required:
        if tok not in src: raise RuntimeError('successful-26532 provenance-aware RCD contract missing: '+tok)
    for rel in ('rcd26498_populate.glsl','rcd26498_vh_direction.glsl','rcd26498_lpf.glsl','rcd26498_green.glsl','rcd26498_diag_residual.glsl','rcd26489_diag_direction.glsl','rcd26498_opposite.glsl','rcd26498_green_rb.glsl','rcd26498_write.glsl'):
        if not (root/'app/src/main/assets/shaders/motionv2'/rel).is_file(): raise RuntimeError('successful-26532 RCD shader missing: '+rel)
    clone=src.replace('public final class MotionV2RcdDemosaic','public final class IrisRcdDemosaic',1)
    clone=clone.replace('public MotionV2RcdDemosaic()','public IrisRcdDemosaic()',1)
    clone=clone.replace('super("", "MotionV2RcdDemosaic")','super("", "IrisRcdDemosaic")',1)
    clone=one(clone,'if (!basePipeline.mParameters.motionV2Active) {','if (!(basePipeline.mParameters.motionV2Active || basePipeline.mParameters.irisNightActive)) {','shared RCD capability')
    clone=clone.replace('MotionV2RcdDemosaic used outside Motion V2','IrisRcdDemosaic used outside Iris Motion/Night')
    write(root,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/IrisRcdDemosaic.java',clone)

def add_night_input(root):
    java=r'''package com.particlesdevs.photoncamera.processing.opengl.postpipeline;
import android.graphics.Point;
import com.particlesdevs.photoncamera.processing.opengl.GLDrawParams;
import com.particlesdevs.photoncamera.processing.opengl.GLFormat;
import com.particlesdevs.photoncamera.processing.opengl.GLTexture;
import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import static android.opengl.GLES20.GL_CLAMP_TO_EDGE;
import static android.opengl.GLES20.GL_LINEAR;
import static android.opengl.GLES20.GL_NEAREST;
/** IRIS_26533_SHARED_FUSED_BAYER_INPUT */
public final class IrisRcdBayerInput extends Node {
 public IrisRcdBayerInput(){super("","IrisRcdBayerInput");}
 @Override public void Compile(){}
 @Override public void Run(){
  PostPipeline p=(PostPipeline)basePipeline; Point raw=new Point(basePipeline.mParameters.rawSize); Point packed=new Point(raw.x/2,raw.y/2);
  if(p.stackFrame==null||raw.x<=0||raw.y<=0||(raw.x&1)!=0||(raw.y&1)!=0)throw new IllegalStateException("26533 fused RAW16 Bayer bridge invalid");
  ByteBuffer rv=p.stackFrame.duplicate();rv.position(0); GLTexture in=new GLTexture(raw,new GLFormat(GLFormat.DataType.UNSIGNED_16),rv,GL_NEAREST,GL_CLAMP_TO_EDGE);
  glProg.useAssetProgram("irisnight/raw16_to_packed_linear_bayer"); glProg.setTexture("InputBuffer",in); glProg.setVar("blackLevel",basePipeline.mParameters.blackLevel); glProg.setVar("whiteLevel",(float)basePipeline.mParameters.whiteLevel);
  WorkingTexture=new GLTexture(packed,new GLFormat(GLFormat.DataType.FLOAT_32,4),null,GL_NEAREST,GL_CLAMP_TO_EDGE); glProg.drawBlocks(WorkingTexture); in.close();
  ByteBuffer prov;
  if(p.motionV2HighlightProvenance!=null){prov=p.motionV2HighlightProvenance.duplicate();prov.position(0);}else{prov=ByteBuffer.allocateDirect(packed.x*packed.y*4).order(ByteOrder.nativeOrder());while(prov.remaining()>=4)prov.putFloat(0f);prov.position(0);}
  p.motionV2HighlightProvenanceTexture=new GLTexture(packed,new GLFormat(GLFormat.DataType.FLOAT_32,1),prov,GL_NEAREST,GL_CLAMP_TO_EDGE);
  if(p.irisMotionDirectRgbAuxiliary!=null){ByteBuffer rgb=p.irisMotionDirectRgbAuxiliary.duplicate();rgb.position(0);p.irisMotionDirectRgbTexture=new GLTexture(raw,new GLFormat(GLFormat.DataType.FLOAT_32,4),rgb,GL_NEAREST,GL_CLAMP_TO_EDGE);}
  GLFormat wf=new GLFormat(GLFormat.DataType.FLOAT_16,GLDrawParams.WorkDim); basePipeline.main1=new GLTexture(raw,wf,null,GL_LINEAR,GL_CLAMP_TO_EDGE);basePipeline.main2=new GLTexture(raw,wf,null,GL_LINEAR,GL_CLAMP_TO_EDGE);basePipeline.main3=new GLTexture(raw,wf,null,GL_LINEAR,GL_CLAMP_TO_EDGE);basePipeline.texnum=0;glProg.closed=true;
 }
}
'''
    shader=r'''precision highp float; precision highp usampler2D;
uniform highp usampler2D InputBuffer; uniform vec4 blackLevel; uniform float whiteLevel; out vec4 Output;
float n(ivec2 p,int q){float v=float(texelFetch(InputBuffer,p,0).r);float b=q==0?blackLevel.r:(q==1?blackLevel.g:(q==2?blackLevel.b:blackLevel.a));return max((v-b)/max(whiteLevel-b,1.0),0.0);}
void main(){ivec2 p=ivec2(gl_FragCoord.xy)*2;Output=vec4(n(p,0),n(p+ivec2(1,0),1),n(p+ivec2(0,1),2),n(p+ivec2(1,1),3));}
'''
    overlay_java=r'''package com.particlesdevs.photoncamera.processing.opengl.postpipeline;
import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
/** IRIS_26533_MOTION_RCD_SHORT_CHROMA_BRIDGE */
public final class IrisMotionRcdShortChromaOverlay extends Node {
 public IrisMotionRcdShortChromaOverlay(){super("","IrisMotionRcdShortChromaOverlay");}@Override public void Compile(){}
 @Override public void Run(){PostPipeline p=(PostPipeline)basePipeline;if(previousNode==null||previousNode.WorkingTexture==null||p.irisMotionDirectRgbTexture==null||p.motionV2HighlightProvenanceTexture==null)throw new IllegalStateException("26533 Motion RCD Short-A bridge missing input");glProg.useAssetProgram("irisnight/motion_rcd_short_chroma_overlay");glProg.setTexture("RcdRgb",previousNode.WorkingTexture);glProg.setTexture("DirectRgb",p.irisMotionDirectRgbTexture);glProg.setTexture("HighlightProvenance",p.motionV2HighlightProvenanceTexture);glProg.setVar("rawSize",basePipeline.mParameters.rawSize);glProg.setVar("packedSize",new android.graphics.Point(basePipeline.mParameters.rawSize.x/2,basePipeline.mParameters.rawSize.y/2));WorkingTexture=basePipeline.getMain();glProg.drawBlocks(WorkingTexture);}
}
'''
    overlay_shader=r'''precision highp float;precision highp int;uniform highp sampler2D RcdRgb;uniform highp sampler2D DirectRgb;uniform highp sampler2D HighlightProvenance;uniform ivec2 rawSize;uniform ivec2 packedSize;out vec3 Output;
float dv(int q){return q==0?1.0:(q==1?3.0:(q==2?9.0:27.0));}float sf(ivec2 p){p=clamp(p,ivec2(0),packedSize-ivec2(1));float c=texelFetch(HighlightProvenance,p,0).r,n=0.0;for(int q=0;q<4;++q){float s=mod(floor(c/dv(q)),3.0);n+=abs(s-2.0)<0.25?1.0:0.0;}return .25*n;}float sm(ivec2 p){vec2 x=.5*vec2(p)-vec2(.5);ivec2 a=ivec2(floor(x)),b=a+ivec2(1);vec2 f=fract(x);return mix(mix(sf(a),sf(ivec2(b.x,a.y)),f.x),mix(sf(ivec2(a.x,b.y)),sf(b),f.x),f.y);}float l(vec3 v){return dot(max(v,vec3(0)),vec3(.2126,.7152,.0722));}void main(){ivec2 p=ivec2(gl_FragCoord.xy);vec3 r=max(texelFetch(RcdRgb,p,0).rgb,vec3(0)),d=max(texelFetch(DirectRgb,p,0).rgb,vec3(0));float rl=l(r),dl=l(d);vec3 hue=dl>1e-6?d*(rl/dl):r;float m=smoothstep(.10,.65,sm(p))*smoothstep(.50,.90,max(max(d.r,d.g),d.b));Output=mix(r,hue,.90*m);}
'''
    write(root,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/IrisRcdBayerInput.java',java)
    write(root,'app/src/main/assets/shaders/irisnight/raw16_to_packed_linear_bayer.glsl',shader)
    write(root,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/IrisMotionRcdShortChromaOverlay.java',overlay_java)
    write(root,'app/src/main/assets/shaders/irisnight/motion_rcd_short_chroma_overlay.glsl',overlay_shader)

def patch_post(root):
    p=root/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java'; s=p.read_text(encoding='utf-8')
    fa='public ByteBuffer motionV2HighlightProvenance;'
    s=one(s,fa,fa+'\n    /* IRIS_26533_MOTION_RCD_CARRIER */\n    public boolean irisMotionRcdActive=false;\n    public ByteBuffer irisMotionDirectRgbAuxiliary;\n    public GLTexture irisMotionDirectRgbTexture;','Post Motion RCD fields')
    anchor='public Bitmap Run(ByteBuffer inBuffer, Parameters parameters) {'
    methods='''public Bitmap RunIrisNightBayer(ByteBuffer fusedBayer, Parameters parameters) {
        if(fusedBayer==null)throw new IllegalArgumentException("26533 Iris Night fused Bayer is null"); parameters.irisNightActive=true;parameters.motionV2Active=false;irisMotionRcdActive=false;irisMotionDirectRgbAuxiliary=null;motionV2HighlightProvenance=null;return Run(fusedBayer,parameters);
    }
    public Bitmap RunMotionV2FusedBayerRcd(ByteBuffer fusedBayer,ByteBuffer directRgb,ByteBuffer provenance,Parameters parameters){
        if(fusedBayer==null||directRgb==null)throw new IllegalArgumentException("26533 Motion RCD carrier missing");parameters.motionV2Active=true;parameters.irisNightActive=false;irisMotionRcdActive=true;irisMotionDirectRgbAuxiliary=directRgb;motionV2HighlightProvenance=provenance;return Run(fusedBayer,parameters);
    }

    '''
    s=one(s,anchor,methods+anchor,'Post shared RCD entries')
    s=s.replace('if (mParameters.motionV2Active) {','if (mParameters.motionV2Active || mParameters.irisNightActive) {',1)
    build='private void BuildDefaultPipeline() {'
    graph='''private void BuildDefaultPipeline() {
        /* IRIS_26533_NIGHT_ISOLATED_POST_GRAPH */
        if(mParameters.irisNightActive){add(new IrisRcdBayerInput());add(new StageTelemetry("IRIS_NIGHT_FUSED_BAYER_INPUT"));add(new IrisRcdDemosaic());add(new StageTelemetry("IRIS_NIGHT_RCD_26498"));add(new MotionV2DisplayExposure());add(new MotionV2ColorTransform());add(new MotionV2Render());add(new RotateWatermark(getRotation()));return;}
        /* IRIS_26533_MOTION_FUSED_BAYER_RCD_POST_GRAPH */
        if(mParameters.motionV2Active&&irisMotionRcdActive){add(new IrisRcdBayerInput());add(new StageTelemetry("V2_POST_FUSED_BAYER_CANONICAL_26533"));add(new IrisRcdDemosaic());add(new StageTelemetry("V2_POST_RCD26498_AFTER_MGC_SPATIAL"));add(new IrisMotionRcdShortChromaOverlay());add(new StageTelemetry("V2_POST_SHORT_A_CHROMA_AFTER_RCD"));add(new MotionV2DisplayExposure());add(new MotionV2ColorTransform());add(new MotionV2Render());add(new RotateWatermark(getRotation()));return;}
'''
    s=one(s,build,graph,'Post shared Motion/Night RCD graphs')
    s=s.replace('if (mParameters.motionV2Active && motionV2GainMapBitmap != null) {','if ((mParameters.motionV2Active || mParameters.irisNightActive) && motionV2GainMapBitmap != null) {',1)
    p.write_text(s,encoding='utf-8')

def neural_java():
    return r'''package com.particlesdevs.photoncamera.processing.processor;

import android.graphics.Bitmap;
import com.particlesdevs.photoncamera.app.PhotonCamera;
import com.particlesdevs.photoncamera.util.Log;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.nio.FloatBuffer;
import java.util.Collections;
import ai.onnxruntime.OnnxTensor;
import ai.onnxruntime.OnnxValue;
import ai.onnxruntime.OrtEnvironment;
import ai.onnxruntime.OrtSession;

/** IRIS_26533_JIN_NEURAL_OWNER
 * Runs the pinned Jin et al. LOL generator only at 512x512. The network result is reduced to
 * a 32x32 RGB gain field and applied in native code to the native-resolution base bitmap.
 * The 50MP path reuses that enhanced base plus 26532's streamed detail: no 50MP neural tensor.
 */
public final class IrisNightNeuralEnhancer {
    private static final String TAG="IrisNightNeural";
    private static final int N=512, GRID=32;
    private static OrtEnvironment env; private static OrtSession session; private static String inputName;
    static { System.loadLibrary("motionv2jpeg"); }
    private IrisNightNeuralEnhancer(){}
    private static synchronized void ensure() throws Exception {
        if(session!=null)return;
        env=OrtEnvironment.getEnvironment();
        OrtSession.SessionOptions opts=new OrtSession.SessionOptions();
        try { opts.addNnapi(); Log.i(TAG,"IRIS_26533_NNAPI_REGISTERED"); }
        catch(Throwable t){ Log.w(TAG,"IRIS_26533_NNAPI_UNAVAILABLE CPU fallback: "+t.getClass().getSimpleName()); }
        byte[] model;
        try(InputStream in=PhotonCamera.getAssetLoader().getInputStream("models/iris_night_jin_lol_512.onnx"); ByteArrayOutputStream o=new ByteArrayOutputStream()){
            byte[] b=new byte[1<<16]; for(int r;(r=in.read(b))>0;)o.write(b,0,r); model=o.toByteArray();
        }
        session=env.createSession(model,opts); inputName=session.getInputNames().iterator().next();
    }
    public static Bitmap enhanceInPlace(Bitmap base){
        if(base==null||base.isRecycled())return base;
        long t0=System.nanoTime(); Bitmap small=null;
        try{
            ensure(); small=Bitmap.createScaledBitmap(base,N,N,true); int[] px=new int[N*N]; small.getPixels(px,0,N,0,0,N,N);
            float[] f=new float[3*N*N]; int plane=N*N;
            for(int i=0;i<plane;i++){int c=px[i]; f[i]=(((c>>16)&255)/127.5f)-1f; f[plane+i]=(((c>>8)&255)/127.5f)-1f; f[2*plane+i]=((c&255)/127.5f)-1f;}
            float[] gains=new float[GRID*GRID*3]; int cell=N/GRID;
            try(OnnxTensor in=OnnxTensor.createTensor(env,FloatBuffer.wrap(f),new long[]{1,3,N,N}); OrtSession.Result rr=session.run(Collections.singletonMap(inputName,in))){
                OnnxValue ov=rr.get(0); Object value=ov.getValue();
                if(!(value instanceof float[][][][]))throw new IllegalStateException("26533 Jin ONNX output is not NCHW float");
                float[][][][] y=(float[][][][])value;
                for(int gy=0;gy<GRID;gy++)for(int gx=0;gx<GRID;gx++)for(int ch=0;ch<3;ch++){
                    double sum=0; int count=0;
                    for(int yy=gy*cell;yy<(gy+1)*cell;yy+=2)for(int xx=gx*cell;xx<(gx+1)*cell;xx+=2){
                        int i=yy*N+xx; float src=(f[ch*plane+i]+1f)*0.5f; float dst=(y[0][ch][yy][xx]+1f)*0.5f;
                        float g=dst/Math.max(src,0.035f); float highlight=src>0.72f?Math.max(0f,1f-(src-0.72f)/0.25f):1f;
                        g=1f+(g-1f)*highlight; sum+=Math.max(0.55f,Math.min(1.85f,g)); count++;
                    }
                    gains[(gy*GRID+gx)*3+ch]=(float)(sum/Math.max(1,count));
                }
            }
            if(!applyGainFieldNative(base,gains,GRID,GRID))throw new IllegalStateException("26533 native neural field apply failed");
            Log.i(TAG,"IRIS_26533_JIN_INFERENCE ms="+((System.nanoTime()-t0)/1_000_000L)+" tensor=512x512 fullResInference=false");
            return base;
        }catch(Throwable t){ throw new IllegalStateException("26533 Iris Night neural inference failed closed",t); }
        finally{ if(small!=null&&small!=base&&!small.isRecycled())small.recycle(); }
    }
    private static native boolean applyGainFieldNative(Bitmap base,float[] gains,int gridW,int gridH);
}
'''

def patch_native(root):
    p=root/'app/src/main/cpp/motionv2_jpeg444_jni.cpp'; s=p.read_text(encoding='utf-8')
    anchor='extern "C" JNIEXPORT jboolean JNICALL Java_com_particlesdevs_photoncamera_processing_ultrahdr_MotionV2Jpeg444Encoder_isJpegRNative'
    if anchor not in s: raise RuntimeError('native JPEG-R anchor missing')
    code=r'''
extern "C" JNIEXPORT jboolean JNICALL Java_com_particlesdevs_photoncamera_processing_processor_IrisNightNeuralEnhancer_applyGainFieldNative(
        JNIEnv*e,jclass,jobject bitmap,jfloatArray gains,jint gw,jint gh){
    if(!bitmap||!gains||gw<2||gh<2||e->GetArrayLength(gains)!=(jsize)(gw*gh*3))return JNI_FALSE;
    AndroidBitmapInfo info{}; if(AndroidBitmap_getInfo(e,bitmap,&info)!=ANDROID_BITMAP_RESULT_SUCCESS||info.format!=ANDROID_BITMAP_FORMAT_RGBA_8888)return JNI_FALSE;
    std::vector<float> g((size_t)gw*gh*3); e->GetFloatArrayRegion(gains,0,(jsize)g.size(),g.data()); if(e->ExceptionCheck())return JNI_FALSE;
    void*p=nullptr;if(AndroidBitmap_lockPixels(e,bitmap,&p)!=ANDROID_BITMAP_RESULT_SUCCESS||!p)return JNI_FALSE;
    for(uint32_t y=0;y<info.height;y++){auto*row=(uint8_t*)p+(size_t)y*info.stride;float fy=((float)y+0.5f)*(float)gh/(float)info.height-0.5f;int y0=std::max(0,std::min(gh-1,(int)floorf(fy))),y1=std::min(y0+1,gh-1);float ty=std::max(0.f,std::min(1.f,fy-y0));
      for(uint32_t x=0;x<info.width;x++){float fx=((float)x+0.5f)*(float)gw/(float)info.width-0.5f;int x0=std::max(0,std::min(gw-1,(int)floorf(fx))),x1=std::min(x0+1,gw-1);float tx=std::max(0.f,std::min(1.f,fx-x0));uint8_t*q=row+x*4;
        for(int c=0;c<3;c++){auto at=[&](int xx,int yy){return g[((size_t)yy*gw+xx)*3+c];};float a=at(x0,y0)+(at(x1,y0)-at(x0,y0))*tx,b=at(x0,y1)+(at(x1,y1)-at(x0,y1))*tx,gg=a+(b-a)*ty;float v=(q[c]/255.f)*gg;q[c]=(uint8_t)lrintf(std::max(0.f,std::min(1.f,v))*255.f);} }
    }
    AndroidBitmap_unlockPixels(e,bitmap); return JNI_TRUE;
}

'''
    s=s.replace(anchor,code+anchor,1); p.write_text(s,encoding='utf-8')

def patch_gradle(root):
    p=root/'app/build.gradle'; s=p.read_text(encoding='utf-8')
    dep="    implementation 'com.microsoft.onnxruntime:onnxruntime-android:1.29.0' // IRIS_26533_PINNED_ORT_ANDROID\n"
    if 'onnxruntime-android' in s: raise RuntimeError('unexpected existing ONNX Runtime dependency')
    anchor='dependencies {\n'
    s=one(s,anchor,anchor+'\n'+dep,'Gradle ONNX dependency')
    p.write_text(s,encoding='utf-8')

def patch_hdrx(root):
    p=root/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java'; s=p.read_text(encoding='utf-8')
    # New imports are fully qualified in method to minimize import churn.
    anchor='private void ApplyHdrX() {'
    entry='''private void ApplyHdrX() {
        if (cameraMode == CameraMode.NIGHT) {
            ApplyIrisNight26533();
            return;
        }
'''
    s=one(s,anchor,entry,'Hdrx Night isolated dispatch')
    # Add dedicated method before ApplyHdrX. It deliberately does not invoke PyramidMerging,
    # ImageFrameDeblur, generic PostPipeline or IsoExpoSelector.fullpairs.
    method=r'''
    /* IRIS_26533_NIGHT_PROCESSING_SOLE_OWNER */
    private void ApplyIrisNight26533() {
        callback.onStarted();
        processingEventsListener.onProcessingStarted("Iris Night");
        if (mImageFramesToProcess == null || mImageFramesToProcess.size() < 2)
            throw new IllegalStateException("26533 Iris Night requires at least two RAW frames");
        mImageFramesToProcess.sort(Comparator.comparingLong(ImageFrame::getTimestamp));
        final int width=mImageFramesToProcess.get(0).width, height=mImageFramesToProcess.get(0).height;
        final Parameters p=new Parameters(); p.FillConstParameters(characteristics,new Point(width,height));
        java.util.List<com.particlesdevs.photoncamera.processing.parameters.IsoExpoSelector.ExpoPair> pairs=
                com.particlesdevs.photoncamera.processing.parameters.IrisNightExposureSelector.snapshotPairs();
        if(pairs.size()<mImageFramesToProcess.size())throw new IllegalStateException("26533 Night exposure metadata population mismatch pairs="+pairs.size()+" frames="+mImageFramesToProcess.size());
        ArrayList<ImageFrame> images=new ArrayList<>(); int isoSum=0;
        for(int i=0;i<mImageFramesToProcess.size();i++){
            ImageFrame f=mImageFramesToProcess.get(i); f.number=i;
            f.pair=new com.particlesdevs.photoncamera.processing.parameters.IsoExpoSelector.ExpoPair(pairs.get(i));
            f.pair.curlayer=com.particlesdevs.photoncamera.processing.parameters.IsoExpoSelector.ExpoPair.exposureLayer.Normal; f.pair.layerMpy=1.0f;
            if(BurstShakiness!=null&&!BurstShakiness.isEmpty())f.frameGyro=BurstShakiness.get(i%BurstShakiness.size());
            images.add(f); isoSum+=f.pair.iso;
        }
        p.FillDynamicParameters(captureResult,captureRequest,Math.max(1,isoSum/images.size())); p.cameraRotation=cameraRotation;
        /* Reuse only Iris' strict Camera2 sensor/color authority; no Photon Night algorithm. */
        configureStrictWronskiSensorAuthority(p);
        p.irisNightActive=true; p.motionV2Active=false;
        /* Night V1 starts from the selected physical-lens field of view; SR changes output sampling, not FOV. */
        p.motionV2GlobalZoom=1.0f; p.motionV2OpticalZoomAnchor=1.0f; p.motionV2OutputZoom=1.0f;
        p.motionV2SpatialReconstructionZoom=1.0f; p.motionV2RenderResidualZoom=1.0f;
        p.motionV2SuperResOutputEnabled=com.particlesdevs.photoncamera.settings.PreferenceKeys.isIrisSuperResOn();
        p.motionV2SuperResOutputScale=p.motionV2SuperResOutputEnabled?2.0f:1.0f;
        Long ts=captureResult==null?null:captureResult.get(CaptureResult.SENSOR_TIMESTAMP); long target=ts!=null?ts:images.get(images.size()/2).getTimestamp(); long ref=images.get(0).getTimestamp(),best=Long.MAX_VALUE;
        for(ImageFrame f:images){long d=Math.abs(f.getTimestamp()-target);if(d<best){best=d;ref=f.getTimestamp();}}
        final MotionV2Merger.Result r;
        if(p.motionV2SuperResOutputEnabled){
            r=PhotonMotionMgc1271Bridge.reconstruct(new Point(width,height),images,ref,p,null,true);
        }else{
            r=IrisNightMgc1271Bridge.reconstruct(new Point(width,height),images,ref,p,null,true);
        }
        if(r==null||r.stackedDngRaw16==null)throw new IllegalStateException("26533 Night MGC fused Bayer missing");
        if(r.dngStackFrames!=images.size())throw new IllegalStateException("26533 Night contributed frame mismatch contributed="+r.dngStackFrames+" expected="+images.size());
        ByteBuffer bayer=r.stackedDngRaw16; bayer.position(0);
        exifData.IMAGE_DESCRIPTION=p.toString()+"\n"+com.particlesdevs.photoncamera.processing.parameters.IrisNightExposureSelector.diagnostics+
                "\nIRIS_26533_NIGHT photonNight=false mgc=true rcd=true neural=jin512 superRes="+p.motionV2SuperResOutputEnabled;
        com.particlesdevs.photoncamera.processing.opengl.postpipeline.PostPipeline pipeline=new com.particlesdevs.photoncamera.processing.opengl.postpipeline.PostPipeline();
        Bitmap img=pipeline.RunIrisNightBayer(bayer,p);
        img=IrisNightNeuralEnhancer.enhanceInPlace(img);
        boolean imageSaved=ImageSaver.Util.saveBitmapAsJPGMotionV2(imageFile,img,ImageSaver.JPG_QUALITY,exifData,
                r.superResDetailPath,r.superResDetailWidth,r.superResDetailHeight,p,pipeline.cropSize);
        processingEventsListener.notifyImageSavedStatus(imageSaved,imageFile);
        if(saveRAW>=1){
            boolean rawSaved;
            if(p.motionV2SuperResOutputEnabled&&r.superResLinearRawPath!=null&&r.superResLinearRawWidth>0&&r.superResLinearRawHeight>0){
                rawSaved=com.particlesdevs.photoncamera.processing.IrisMotionSuperResDngWriter.write(dngFile,java.nio.file.Paths.get(r.superResLinearRawPath),r.superResLinearRawWidth,r.superResLinearRawHeight,p,r.dngNoiseProfile,r.dngStackFrames,r.dngSupportMin,r.dngSupportP01,r.dngSupportP10,r.dngSupportMedian,r.dngSupportMean,r.dngSupportMax,r.dngNoiseEquivalentSupport);
            }else{
                bayer.position(0); rawSaved=ImageSaver.Util.saveNormalized16StackedRaw(dngFile,bayer,p,r.dngNoiseProfile,r.dngStackFrames,r.dngSupportMin,r.dngSupportP01,r.dngSupportP10,r.dngSupportMedian,r.dngSupportMean,r.dngSupportMax,r.dngNoiseEquivalentSupport);
            }
            processingEventsListener.notifyImageSavedStatus(rawSaved,dngFile);
        }
        for(ImageFrame f:images)if(f!=null)f.close();
        processingEventsListener.onProcessingFinished("Iris Night Processing Finished"); callback.onFinished();
    }

'''
    # Insert method immediately before entry method to keep class structure simple.
    idx=s.index(entry)
    s=s[:idx]+method+s[idx:]
    result_decl='ByteBuffer motionV2HighlightProvenance = null;'
    s=one(s,result_decl,result_decl+'\n        MotionV2Merger.Result iris26533MotionRcdResult = null;','Motion RCD result carrier')
    prov='motionV2HighlightProvenance = iris26409V2.highlightProvenance;'
    s=one(s,prov,prov+'\n            iris26533MotionRcdResult = iris26409V2;','Motion RCD sidecar capture')
    old='''img = pipeline.RunMotionV2FloatCfa(
                    output,
                    motionV2HighlightProvenance,
                    processingParameters);
            output = null;'''
    new='''if (processingParameters.cfaPattern >= 0 && processingParameters.cfaPattern <= 3) {
                if (iris26533MotionRcdResult == null || iris26533MotionRcdResult.stackedDngRaw16 == null) throw new IllegalStateException("26533 Motion fused Bayer sidecar missing");
                ByteBuffer iris26533Bayer=iris26533MotionRcdResult.stackedDngRaw16; iris26533Bayer.position(0);
                img=pipeline.RunMotionV2FusedBayerRcd(iris26533Bayer,output,motionV2HighlightProvenance,processingParameters);
                try{Allocator.free(output);}catch(Throwable ignored){} output=null;
            } else {
                img=pipeline.RunMotionV2FloatCfa(output,motionV2HighlightProvenance,processingParameters); output=null;
            }'''
    s=one(s,old,new,'Motion standard Bayer RCD handoff')
    p.write_text(s,encoding='utf-8')

def patch_iris_post_nodes(root):
    specs=[
        ('app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java',
         'if (!basePipeline.mParameters.motionV2Active) {',
         'if (!(basePipeline.mParameters.motionV2Active || basePipeline.mParameters.irisNightActive)) {'),
        ('app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java',
         'if (!basePipeline.mParameters.motionV2Active) {',
         'if (!(basePipeline.mParameters.motionV2Active || basePipeline.mParameters.irisNightActive)) {'),
        ('app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
         'if (!basePipeline.mParameters.motionV2Active) {',
         'if (!(basePipeline.mParameters.motionV2Active || basePipeline.mParameters.irisNightActive)) {'),
    ]
    for rel,old,new in specs:
        p=root/rel; text=p.read_text(encoding='utf-8')
        text=one(text,old,new,'Iris Night capability guard '+rel)
        p.write_text(text,encoding='utf-8')

def add_neural(root): write(root,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightNeuralEnhancer.java',neural_java())

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('root'); ap.add_argument('--historical-rcd-transform',required=True); ap.add_argument('--base-owner-hashes',required=True); a=ap.parse_args(); root=Path(a.root)
    exact=load_hash_contract(a.base_owner_hashes)
    missing=[rel for rel in REQUIRED_26532_BASE_OWNERS if rel not in exact]
    if missing: raise RuntimeError('exact-26532 owner hash contract missing: '+', '.join(missing))
    for rel in REQUIRED_26532_BASE_OWNERS:
        h=exact[rel]
        p=root/rel
        if not p.exists(): raise RuntimeError('required 26532 file missing: '+rel)
        got=sha(p)
        if got!=h: raise RuntimeError(f'26532 base hash mismatch {rel}: {got} != {h}')
    clone_current_rcd(root)
    clone_night_bridge(root); add_parameters(root); add_night_exposure(root); patch_capture(root); patch_frame_selector(root); add_night_input(root); patch_post(root); patch_iris_post_nodes(root); add_neural(root); patch_native(root); patch_gradle(root); patch_hdrx(root)
    print('IRIS_26533_TRANSFORM_APPLIED')
if __name__=='__main__': main()
