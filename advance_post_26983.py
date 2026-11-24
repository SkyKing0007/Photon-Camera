from pathlib import Path
import re,json
root=Path(__file__).resolve().parent
base=root/'actual/app/src/main';cand=root/'candidate/app/src/main'
java='java/com/particlesdevs/photoncamera/processing/'
post=java+'opengl/postpipeline/'
rename={
 'MotionV2CfaInput':'Iris26983COnRgbInput',
 'MotionV2PhotonHighlightCompression':'Iris26983COnHighlightAnalysis',
 'MotionV2ColorTransform':'Iris26983COnColorTransform',
 'MotionV2ViewfinderExposureMatcher':'Iris26983COnExposureMatcher',
 'MotionV2PreviewHueMatch':'Iris26983COnPreviewHueMatch',
 'MotionV2PreviewHueCalibration':'Iris26983COnPreviewHueCalibration',
 'MotionV2DisplayExposure':'Iris26983COnDisplayExposure',
 'IrisMotionToneControls':'Iris26983COnToneControls',
 'MotionV2Render':'Iris26983COnRender',
 'MotionV2GainMapNative':'Iris26983COnGainMapNative',
 'RotateWatermark':'Iris26983COnRotateWatermark',
 'MotionV2UltraHdr':'Iris26983COnUltraHdr',
 'MotionV2Acr3Curve':'Iris26983COnAcr3Curve',
 'MotionV2SharedRgba16fCarrier':'Iris26983COnRgba16fCarrier',
 'PostPipeline':'Iris26983COnPostPipeline',
 'iris26906ExperimentBSelected':'iris26983COnSelected',
 'iris26903NightB':'iris26983COnNight',
 'MOTION_V2_RECONSTRUCTION_RAWR_AMAZE':'MOTION_V2_RECONSTRUCTION_C_LKR_26983',
}
# Full exact copies of graph nodes, including their inactive branches; C post graph itself
# admits only C Motion SR ON. Do not edit original B nodes or assets.
classes=list(rename)[:12]
assets={}
records=[]
def transformed(text):
 text=re.sub(r'\b('+'|'.join(rename)+r')\b',lambda m:rename[m.group()],text)
 def shader(m):
  source=m.group(1);dest='iris26983/con_post/'+source.replace('motionv2/','')
  assets[source]=dest
  return 'useAssetProgram("'+dest+'")'
 text=re.sub(r'useAssetProgram\("([^"\n]+)"\)',shader,text)
 return text
for n in classes:
 folder=java+'ultrahdr/' if n=='MotionV2UltraHdr' else post
 src=folder+n+'.java';dst=folder+rename[n]+'.java';s=transformed((base/src).read_text())
 if n=='MotionV2GainMapNative':s=s.replace('System.loadLibrary("motionv2jpeg")','System.loadLibrary("iris26983conjpeg")')
 if n=='MotionV2CfaInput':
  # format values are a wire ABI, not an A/B merger dependency
  s=s.replace('import com.particlesdevs.photoncamera.processing.processor.MotionV2Merger;\n','').replace('MotionV2Merger.Result.LINEAR_RGB_CARRIER_', 'Iris26983COnPostPipeline.LINEAR_RGB_CARRIER_')
  s=s.replace('if (basePipeline.mParameters.motionV2Active\n                && basePipeline.mParameters.motionV2ReconstructionOwner\n                != com.particlesdevs.photoncamera.processing.render.Parameters.MOTION_V2_RECONSTRUCTION_SABRE\n                && basePipeline.mParameters.motionV2ReconstructionOwner', 'if (!basePipeline.mParameters.iris26983COnSelected || basePipeline.mParameters.iris26906ExperimentBSelected\n                || !basePipeline.mParameters.motionV2SuperResOutputEnabled\n                || basePipeline.mParameters.motionV2ReconstructionOwner')
 (cand/dst).write_text(s);records.append({'source':src,'copy':dst})
for src,dst in assets.items():
 p=base/'assets/shaders'/(src+'.glsl'); q=cand/'assets/shaders'/(dst+'.glsl');q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(p.read_bytes());records.append({'source':str(p.relative_to(base)),'copy':str(q.relative_to(cand))})
# C JNI exact byte traversal on its own native library.
source=(base/'cpp/motionv2_jpeg444_jni.cpp').read_text();i=source.index('/* IRIS_26827_GAINMAP_NATIVE_EXACT_REMAP');j=source.index('extern "C" JNIEXPORT jboolean JNICALL Java_com_particlesdevs_photoncamera_processing_ultrahdr_MotionV2Jpeg444Encoder_writeNative',i)
p=cand/'cpp/iris26983_con_jpeg_writer.cpp';s=p.read_text();assert 'Iris26983COnGainMapNative_scanNative' not in s;p.write_text(s+'\n'+source[i:j].replace('MotionV2GainMapNative','Iris26983COnGainMapNative'))
# Add a distinct reconstruction owner. Reproduce B's true2x parameter clearing without referencing its optional B/OFF detail record.
p=cand/(java+'render/Parameters.java');s=p.read_text();s=s.replace('    public int motionV2ReconstructionOwner = MOTION_V2_RECONSTRUCTION_NONE;', '    public static final int MOTION_V2_RECONSTRUCTION_C_LKR_26983 = 4;\n    public int motionV2ReconstructionOwner = MOTION_V2_RECONSTRUCTION_NONE;');i=s.index('        motionV2ReconstructionOwner = MOTION_V2_RECONSTRUCTION_RAWR_AMAZE;',s.index('public void prepareRawrBPublication26856(boolean'));j=s.index('        /* IRIS_26856_B_NATIVE_ZOOM_POST_CONSUMER',i);body=s[i:j].replace('MOTION_V2_RECONSTRUCTION_RAWR_AMAZE','MOTION_V2_RECONSTRUCTION_C_LKR_26983');idx=s.index('    protected Parameters Build()');s=s[:idx]+'''    /** C ON distinct owner, equivalent to the B true2x-only parameter cleanup. */
    public void prepareCOnPublication26983() {
        if (!iris26983COnSelected || iris26906ExperimentBSelected || !motionV2Active || irisNightActive || !motionV2SuperResOutputEnabled)
            throw new IllegalStateException("26983 non-C ON publication admission");
'''+body+'''        motionV2SuperResOutputEnabled = true;
        motionV2SuperResOutputScale = 2.0f;
    }

'''+s[idx:];p.write_text(s)
# Build only the B ON reachable post graph. All tone and output geometry controls are caller-frozen.
old=(base/(post+'PostPipeline.java')).read_text()
header=old[:old.index('public class PostPipeline')]
header=transformed(header).replace('import com.particlesdevs.photoncamera.processing.processor.MotionV2Merger;\n','')
# The fields required by copied nodes are separate C instances, not inherited from original PostPipeline.
fields='''public final class Iris26983COnPostPipeline extends GLBasePipeline {
    static final int LINEAR_RGB_CARRIER_NONE=0, LINEAR_RGB_CARRIER_RGBA16F=1, LINEAR_RGB_CARRIER_RGBA32F=2;
    public ByteBuffer motionV2FloatCfa;
    public Iris26983COnRgba16fCarrier motionV2SharedRgba16fCarrier;
    public int motionV2LinearRgbCarrierFormat=LINEAR_RGB_CARRIER_RGBA16F;
    public boolean motionV2DirectRgbCarrier=true;
    public ByteBuffer motionV2HighlightProvenance;
    public GLTexture motionV2HighlightProvenanceTexture;
    public boolean motionV2PhotonHighlightCompressionEnabled=false;
    public float motionV2PhotonAdaptiveWhitePoint=1f, motionV2PhotonHighlightKnee=1f, motionV2PhotonHighlightClippedFraction=0f;
    public Bitmap motionV2GainMapBitmap;
    public float motionV2GainMapMaxRatio=1f, motionV2GainMapFullHdrDisplayRatio=1f;
    public IrisMotionSettings.Snapshot motionV2ToneSettingsSnapshot;
    public boolean motionV2WatermarkEnabled;
    public Point cropSize;
    private boolean used;
    // Preserve the same legacy neutral GL tuning-file namespace as the proven B graph.
    public Iris26983COnPostPipeline() { super("PostPipeline"); }
    public int getRotation() { return mParameters.cameraRotation; }
'''
rot=old[old.index('    @SuppressWarnings("SuspiciousNameCombination")'):old.index('    float constShift')]
body='''    /** Takes ownership of exactly one 1x RGBA16F sidecar. No B or C OFF nodes can enter. */
    public Bitmap runCOn(ByteBuffer source, Iris26983COnRgba16fCarrier shared,
            Parameters parameters, IrisMotionSettings.Snapshot tone, boolean highlightCompression,
            boolean watermark, boolean aspect169, boolean energySaving) {
        if (used || (source==null)==(shared==null) || parameters==null || tone==null ||
                !parameters.iris26983COnSelected || parameters.iris26906ExperimentBSelected ||
                !parameters.motionV2Active || parameters.irisNightActive || parameters.iris26983COnNight ||
                !parameters.motionV2SuperResOutputEnabled || parameters.motionV2SuperResOutputScale!=2f ||
                parameters.motionV2ReconstructionOwner!=Parameters.MOTION_V2_RECONSTRUCTION_C_LKR_26983 ||
                parameters.rawSize==null || parameters.rawSize.x<=0 || parameters.rawSize.y<=0 ||
                (parameters.rawSize.x&1)!=0 || (parameters.rawSize.y&1)!=0 || parameters.cfaPattern<0 || parameters.cfaPattern>3 ||
                Math.abs(parameters.motionV2ReconstructionZoom-1f)>1e-5f ||
                Math.abs(parameters.motionV2SpatialReconstructionZoom-1f)>1e-5f ||
                Math.abs(parameters.motionV2MgcSourceExposureGain-1f)>1e-5f || parameters.motionV2HighZoomRgbPrepared)
            throw new IllegalArgumentException("26983 invalid C ON 1x post admission");
        used=true;
        motionV2FloatCfa=source;
        motionV2SharedRgba16fCarrier=shared;
        motionV2ToneSettingsSnapshot=tone;
        motionV2WatermarkEnabled=watermark;
        Bitmap res=null;
        boolean complete=false;
        try {
            mParameters=parameters;
            mSettings=PhotonCamera.getSettings(); // neutral GL infrastructure only; presentation is frozen above
            workSize=new Point(parameters.rawSize.x,parameters.rawSize.y);
            noiseS=0f;noiseO=0f;
            Point rawSliced=parameters.rawSize;
            cropSize=new Point(parameters.rawSize);
            if(aspect169) {
                if(rawSliced.x>rawSliced.y) rawSliced=new Point(rawSliced.x,rawSliced.x*9/16);
                else rawSliced=new Point(rawSliced.y*9/16,rawSliced.y);
                cropSize=new Point(rawSliced);
            }
            Point rotatedSize=getRotatedCoords(rawSliced);
            GLDrawParams.TileSize=(energySaving||parameters.rawSize.x*parameters.rawSize.y<ResolutionSolution.smallRes)?8:256;
            GLFormat format=new GLFormat(GLFormat.DataType.SIMPLE_8,4);
            GLImage output=new GLImage(rotatedSize,format,false);
            GLCoreBlockProcessing glproc=new GLCoreBlockProcessing(rotatedSize,output,format,GLDrawParams.Allocate.Direct);
            glint=new GLInterface(glproc);
            glint.parameters=parameters;
            buildCOnGraph(highlightCompression);
            GLImage resImg=runAll();
            try { res=resImg.getBufferedImage(); }
            finally { Allocator.free(resImg.byteBuffer); }
            if(parameters.irisJpegColorValid && Build.VERSION.SDK_INT>=26 && res!=null && !res.isRecycled())
                res.setColorSpace(ColorSpace.get(ColorSpace.Named.DISPLAY_P3));
            if(motionV2GainMapBitmap!=null) {
                Iris26983COnUltraHdr.attachMotion(res,motionV2GainMapBitmap,getRotation(),motionV2GainMapMaxRatio,
                    motionV2GainMapFullHdrDisplayRatio,parameters.mirror,parameters.rawSize.x,parameters.rawSize.y,cropSize.x,cropSize.y);
                motionV2GainMapBitmap=null;
            }
            GLTexture.closeAll();
            complete=true;
            return res;
        } catch(RuntimeException|Error failure) {
            try { GLTexture.closeAll(); } catch(Throwable cleanup) {failure.addSuppressed(cleanup);}
            try { close(); } catch(Throwable cleanup) {failure.addSuppressed(cleanup);}
            throw failure;
        } finally {
            // The input node releases the transferred carrier immediately after upload. If it was
            // never reached, this owner retires it instead. No duplicate free on the caller side.
            if(motionV2FloatCfa!=null){ByteBuffer b=motionV2FloatCfa;motionV2FloatCfa=null;Allocator.free(b);}
            if(motionV2SharedRgba16fCarrier!=null){Iris26983COnRgba16fCarrier b=motionV2SharedRgba16fCarrier;motionV2SharedRgba16fCarrier=null;b.close();}
            if(!complete){if(res!=null&&!res.isRecycled())res.recycle();if(motionV2GainMapBitmap!=null&&!motionV2GainMapBitmap.isRecycled())motionV2GainMapBitmap.recycle();motionV2GainMapBitmap=null;}
        }
    }
    private void buildCOnGraph(boolean highlightCompression) {
        add(new Iris26983COnRgbInput());
        add(new StageTelemetry("V2_POST_PROPER_PER_FRAME_RGB"));
        add(new Iris26983COnHighlightAnalysis(highlightCompression));
        add(new StageTelemetry("IRIS_26653_PHOTON_HIGHLIGHT_ANALYSIS_FINAL_TONE_OWNER"));
        add(new Iris26983COnColorTransform());
        add(new StageTelemetry("V2_POST_DNG_PROFILE_COLOR_TRANSFORM"));
        add(new Iris26983COnExposureMatcher());
        add(new StageTelemetry("V2_POST_VIEWFINDER_EXPOSURE_SOLVE"));
        add(new Iris26983COnPreviewHueMatch()); // identical SR-ON bypass
        add(new StageTelemetry("IRIS_26638_MOTION_ACR3_COLOR_APPEARANCE"));
        add(new Iris26983COnDisplayExposure());
        add(new StageTelemetry("V2_POST_VIEWFINDER_PRESENTATION_EXPOSURE"));
        add(new Iris26983COnToneControls(motionV2ToneSettingsSnapshot)); // B native owner always adds this node
        add(new StageTelemetry("IRIS_26514_LINEAR_PRESENTATION_CONTROLS"));
        add(new Iris26983COnRender());
        add(new StageTelemetry("V2_POST_RENDER"));
        add(new Iris26983COnRotateWatermark(getRotation(),motionV2WatermarkEnabled));
    }
}
'''
(cand/(post+'Iris26983COnPostPipeline.java')).write_text(header+fields+rot+body)
(root/'26983_post_copy_records.json').write_text(json.dumps({'copies':records,'shader_assets':assets,'notes':'Copied nodes and independent GLSL assets. C-only post graph not wired to shutter. Native byte traversal copied to C JPEG library.'},indent=2)+'\n')
print('Post source copies:',len(classes),'independent shader assets:',len(assets))
