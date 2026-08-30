#!/usr/bin/env python3
from pathlib import Path
import re, sys
root = Path(sys.argv[1]).resolve()

def path(rel): return root / rel

def read(rel): return path(rel).read_text()

def write(rel, s): path(rel).write_text(s)

def rep(rel, old, new, count=1):
    s=read(rel); n=s.count(old)
    if n != count: raise SystemExit(f'{rel}: anchor count {n} != {count}: {old[:100]!r}')
    write(rel, s.replace(old,new,count))

def regex(rel, pattern, repl, count=1, flags=0):
    s=read(rel); out,n=re.subn(pattern,repl,s,count=count,flags=flags)
    if n != count: raise SystemExit(f'{rel}: regex count {n} != {count}: {pattern[:120]}')
    write(rel,out)

# Target version/build belongs to the same deterministic transform/build sequence.
rep('app/version.properties',
'''VERSION_NAME=0.9726566
VERSION_BUILD=26566
''',
'''VERSION_NAME=0.9726567
VERSION_BUILD=26567
''')

# -----------------------------------------------------------------------------
# JPEG-only working gamut: preserve 26566 camera characterization, add P3 target.
# -----------------------------------------------------------------------------
rel='app/src/main/java/com/particlesdevs/photoncamera/processing/render/IrisJpegColorSolver.java'
rep(rel,
'''    private static final float[] XYZ_D50_TO_LINEAR_SRGB = new float[]{
            3.1338561f, -1.6168667f, -0.4906146f,
            -0.9787684f, 1.9161415f, 0.0334540f,
            0.0719453f, -0.2289914f, 1.4052427f
    };
''',
'''    private static final float[] XYZ_D50_TO_LINEAR_SRGB = new float[]{
            3.1338561f, -1.6168667f, -0.4906146f,
            -0.9787684f, 1.9161415f, 0.0334540f,
            0.0719453f, -0.2289914f, 1.4052427f
    };
    /* IRIS_26567_LINEAR_DISPLAY_P3_WORKING_GAMUT
     * Exact linear-sRGB(D65) -> Display-P3(D65) primary conversion already proven at the
     * 26565 publication boundary. Multiplying it into the JPEG-only profile matrix moves the
     * gamut target before appearance/tone work. Dedicated DNG owners never consume this field.
     */
    private static final float[] LINEAR_SRGB_TO_DISPLAY_P3 = new float[]{
            0.8224619687f, 0.1775380313f, 0.0000000000f,
            0.0331941989f, 0.9668058011f, 0.0000000000f,
            0.0170826307f, 0.0723974407f, 0.9105199286f
    };
''')
rep(rel,'        public final float[] proPhotoToSrgb;\n','        public final float[] proPhotoToSrgb;\n        public final float[] proPhotoToDisplayP3;\n')
rep(rel,
'''        private Solution(float[] sensorToProPhoto, float[] proPhotoToSrgb,
                         float[] sceneWhiteXy, float[] cameraWhite,
''',
'''        private Solution(float[] sensorToProPhoto, float[] proPhotoToSrgb,
                         float[] proPhotoToDisplayP3, float[] sceneWhiteXy, float[] cameraWhite,
''')
rep(rel,'            this.proPhotoToSrgb = proPhotoToSrgb;\n','            this.proPhotoToSrgb = proPhotoToSrgb;\n            this.proPhotoToDisplayP3 = proPhotoToDisplayP3;\n')
rep(rel,
'''            final float[] sensorToProPhoto = multiply(XYZ_D50_TO_PROPHOTO, cameraToD50);
            final float[] proPhotoToSrgb = multiply(XYZ_D50_TO_LINEAR_SRGB, PROPHOTO_TO_XYZ_D50);
            if (!finite9(sensorToProPhoto) || !finite9(proPhotoToSrgb)) {
''',
'''            final float[] sensorToProPhoto = multiply(XYZ_D50_TO_PROPHOTO, cameraToD50);
            final float[] proPhotoToSrgb = multiply(XYZ_D50_TO_LINEAR_SRGB, PROPHOTO_TO_XYZ_D50);
            final float[] proPhotoToDisplayP3 = multiply(LINEAR_SRGB_TO_DISPLAY_P3, proPhotoToSrgb);
            if (!finite9(sensorToProPhoto) || !finite9(proPhotoToSrgb)
                    || !finite9(proPhotoToDisplayP3)) {
''')
rep(rel,
'''                    + " neutralError=" + neutralError
                    + " sensorToProPhoto=" + Arrays.toString(sensorToProPhoto));
            return new Solution(sensorToProPhoto, proPhotoToSrgb, sceneXy, cameraWhite,
                    factor, usedForward, mode, neutralError);
''',
'''                    + " neutralError=" + neutralError
                    + " sensorToProPhoto=" + Arrays.toString(sensorToProPhoto)
                    + " jpegWorkingGamut=LINEAR_DISPLAY_P3");
            return new Solution(sensorToProPhoto, proPhotoToSrgb, proPhotoToDisplayP3,
                    sceneXy, cameraWhite, factor, usedForward, mode, neutralError);
''')

rel='app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java'
rep(rel,'    public float[] irisJpegProPhotoToSRGB = new float[9];\n','    public float[] irisJpegProPhotoToSRGB = new float[9];\n    public float[] irisJpegProPhotoToDisplayP3 = new float[9];\n')
rep(rel,'        irisJpegProPhotoToSRGB = solution.proPhotoToSrgb.clone();\n','        irisJpegProPhotoToSRGB = solution.proPhotoToSrgb.clone();\n        irisJpegProPhotoToDisplayP3 = solution.proPhotoToDisplayP3.clone();\n')
rep(rel,'        params.irisJpegProPhotoToSRGB = irisJpegProPhotoToSRGB.clone();\n','        params.irisJpegProPhotoToSRGB = irisJpegProPhotoToSRGB.clone();\n        params.irisJpegProPhotoToDisplayP3 = irisJpegProPhotoToDisplayP3.clone();\n')

# -----------------------------------------------------------------------------
# Shared Motion/Night profile stage. Use calibrated HueSatMap if genuinely loaded.
# -----------------------------------------------------------------------------
rel='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java'
s=read(rel)
s=s.replace('import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;\n',
'''import android.graphics.Point;
import com.particlesdevs.photoncamera.processing.opengl.GLFormat;
import com.particlesdevs.photoncamera.processing.opengl.GLTexture;
import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
import com.particlesdevs.photoncamera.util.BufferUtils;
import static android.opengl.GLES20.GL_CLAMP_TO_EDGE;
import static android.opengl.GLES20.GL_LINEAR;
''',1)
s=s.replace('public final class MotionV2ColorTransform extends Node {\n',
'''public final class MotionV2ColorTransform extends Node {
    private GLTexture profileHueSatTexture;

    @Override public void AfterRun() {
        if (profileHueSatTexture != null) profileHueSatTexture.close();
        profileHueSatTexture = null;
    }
''',1)
s=s.replace('''        float[] proPhotoToSrgb = irisJpegColor
                ? basePipeline.mParameters.irisJpegProPhotoToSRGB
                : basePipeline.mParameters.proPhotoToSRGB;
''','''        float[] profileToDisplay = irisJpegColor
                ? basePipeline.mParameters.irisJpegProPhotoToDisplayP3
                : basePipeline.mParameters.proPhotoToSRGB;
''',1)
s=s.replace('''                || proPhotoToSrgb == null || proPhotoToSrgb.length != 9) {
''','''                || profileToDisplay == null || profileToDisplay.length != 9) {
''',1)
s=s.replace('        requireFinite9(proPhotoToSrgb, "proPhotoToSRGB");\n','        requireFinite9(profileToDisplay, "profileToDisplay");\n',1)
s=s.replace('''        glProg.useAssetProgram("motionv2/color_transform");
        glProg.setTexture("InputBuffer", previousNode.WorkingTexture);
        setRows("sensorToProfile", sensorToProPhoto);
        setRows("profileToSrgb", proPhotoToSrgb);
''','''        final boolean calibratedHueSat = irisJpegColor
                && basePipeline.mParameters.HSVMap != null
                && basePipeline.mParameters.HSVMapSize != null
                && basePipeline.mParameters.HSVMapSize.length >= 2
                && basePipeline.mParameters.HSVMapSize[0] > 0
                && basePipeline.mParameters.HSVMapSize[1] > 0
                && basePipeline.mParameters.HSVMap.length >=
                        basePipeline.mParameters.HSVMapSize[0]
                                * basePipeline.mParameters.HSVMapSize[1] * 3;
        if (calibratedHueSat) glProg.setDefine("USE_PROFILE_HUESAT", 1);
        glProg.useAssetProgram("motionv2/color_transform");
        glProg.setTexture("InputBuffer", previousNode.WorkingTexture);
        if (calibratedHueSat) {
            profileHueSatTexture = new GLTexture(
                    new Point(basePipeline.mParameters.HSVMapSize[1], basePipeline.mParameters.HSVMapSize[0]),
                    new GLFormat(GLFormat.DataType.FLOAT_32, 3),
                    BufferUtils.getFrom(basePipeline.mParameters.HSVMap), GL_LINEAR, GL_CLAMP_TO_EDGE);
            glProg.setTexture("ProfileHueSatMap", profileHueSatTexture);
        }
        setRows("sensorToProfile", sensorToProPhoto);
        setRows("profileToSrgb", profileToDisplay);
''',1)
s=s.replace('''                + " proPhotoToSrgb=" + java.util.Arrays.toString(proPhotoToSrgb)
                + " irisJpegColor=" + irisJpegColor
''','''                + " profileToDisplay=" + java.util.Arrays.toString(profileToDisplay)
                + " workingGamut=" + (irisJpegColor ? "LINEAR_DISPLAY_P3" : "LEGACY_LINEAR_SRGB")
                + " profileSource=" + (calibratedHueSat ? "CALIBRATED_HUESAT" : "UNIVERSAL")
                + " irisJpegColor=" + irisJpegColor
''',1)
s=s.replace('''                + " neutralAxisNegativeGamutFit=true"
                + " extendedLinearOutput=true");
''','''                + " neutralAxisNegativeGamutFit=true"
                + " extendedLinearOutput=true"
                + " publicationConversionNeeded=" + (!irisJpegColor));
''',1)
write(rel,s)

rel='app/src/main/assets/shaders/motionv2/color_transform.glsl'
s=read(rel)
s=s.replace('uniform sampler2D InputBuffer;\n','uniform sampler2D InputBuffer;\nuniform sampler2D ProfileHueSatMap;\n',1)
s=s.replace('out vec3 Output;\n','''out vec3 Output;

#ifndef USE_PROFILE_HUESAT
#define USE_PROFILE_HUESAT 0
#endif
const float IRIS_26567_EPS = 0.0000001;
vec3 iris26567HslToRgb(vec3 c) {
    vec3 rgb = clamp(abs(mod(c.x * 6.0 + vec3(0.0, 4.0, 2.0), 6.0) - 3.0) - 1.0, 0.0, 1.0);
    return c.z + c.y * (rgb - 0.5) * (1.0 - abs(2.0 * c.z - 1.0));
}
vec3 iris26567RgbToHsl(vec3 col) {
    float minimumChannel = min(col.r, min(col.g, col.b));
    float maximumChannel = max(col.r, max(col.g, col.b));
    vec3 mask = step(col.grr, col.rgb) * step(col.bbg, col.rgb);
    vec3 hueParts = mask * (vec3(0.0, 2.0, 4.0) +
        (col.gbr - col.brg) / (maximumChannel - minimumChannel + IRIS_26567_EPS)) / 6.0;
    return vec3(fract(1.0 + hueParts.x + hueParts.y + hueParts.z),
        (maximumChannel - minimumChannel) /
            (1.0 - abs(minimumChannel + maximumChannel - 1.0) + IRIS_26567_EPS),
        (minimumChannel + maximumChannel) * 0.5);
}
''',1)
s=s.replace('''    vec3 linearSrgb = vec3(
            dot(profileToSrgbRow0, profileRgb),
            dot(profileToSrgbRow1, profileRgb),
            dot(profileToSrgbRow2, profileRgb));
''','''#if USE_PROFILE_HUESAT == 1
    vec3 profileHsl = iris26567RgbToHsl(max(profileRgb, vec3(0.0)));
    vec3 profileAdjustment = texture(ProfileHueSatMap, vec2(profileHsl.y, profileHsl.x)).rgb;
    profileHsl.x = mod(profileHsl.x + profileAdjustment.x * 0.5 + 1.0, 1.0);
    profileHsl.y = max(profileHsl.y * profileAdjustment.y, 0.0);
    profileHsl.z = max(profileHsl.z * profileAdjustment.z, 0.0);
    profileRgb = iris26567HslToRgb(profileHsl);
#endif
    vec3 linearSrgb = vec3(
            dot(profileToSrgbRow0, profileRgb),
            dot(profileToSrgbRow1, profileRgb),
            dot(profileToSrgbRow2, profileRgb));
''',1)
s=s.replace(' * DNG profile construction. Preserve reconstructed values above 1.0 here; highlight headroom is\n',
''' * DNG profile construction. When a calibrated DNG HueSat map is genuinely loaded, the JPEG-only
 * owner applies that profile operation here before the profile-to-display matrix. Preserve reconstructed values above 1.0 here; highlight headroom is
''',1)
write(rel,s)

# -----------------------------------------------------------------------------
# Normal Photo: Iris JPEG owner must suppress legacy cube/matrix override and target P3.
# -----------------------------------------------------------------------------
rel='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Initial.java'
s=read(rel)
anchor='''        float[][] cube = null;
        ColorCorrectionTransform.CorrectionMode mode =  basePipeline.mParameters.CCT.correctionMode;
        if(mode == ColorCorrectionTransform.CorrectionMode.CUBES || mode == ColorCorrectionTransform.CorrectionMode.CUBE){
'''
replace='''        float[][] cube = null;
        ColorCorrectionTransform.CorrectionMode mode =  basePipeline.mParameters.CCT.correctionMode;
        if(!irisJpegColor && (mode == ColorCorrectionTransform.CorrectionMode.CUBES || mode == ColorCorrectionTransform.CorrectionMode.CUBE)){
'''
if s.count(anchor)!=1: raise SystemExit('Initial pre-mode anchor')
s=s.replace(anchor,replace,1)
s=s.replace('''        float minP = (WP[0]+WP[1]+WP[2])/3.f;
''','''        float minP = (WP[0]+WP[1]+WP[2])/3.f;
        final boolean irisJpegColor = basePipeline.mParameters.irisJpegColorValid
                && !basePipeline.mParameters.irisJpegCustomColorOverride;
        final boolean calibratedIrisHueSat = irisJpegColor
                && basePipeline.mParameters.HSVMap != null
                && basePipeline.mParameters.HSVMapSize != null
                && basePipeline.mParameters.HSVMapSize.length >= 2
                && basePipeline.mParameters.HSVMapSize[0] > 0
                && basePipeline.mParameters.HSVMapSize[1] > 0
                && basePipeline.mParameters.HSVMap.length >=
                        basePipeline.mParameters.HSVMapSize[0]
                                * basePipeline.mParameters.HSVMapSize[1] * 3;
        final boolean useHsvMap = (!irisJpegColor && basePipeline.mParameters.HSVMap != null)
                || calibratedIrisHueSat;
''',1)
s=s.replace('''        if (basePipeline.mParameters.HSVMap != null)
            glProg.setDefine("USE_HSV", 1);
''','''        if (useHsvMap)
            glProg.setDefine("USE_HSV", 1);
''',1)
s=s.replace('''        final boolean irisJpegColor = basePipeline.mParameters.irisJpegColorValid
                && !basePipeline.mParameters.irisJpegCustomColorOverride;
        float[] cct = irisJpegColor
                ? basePipeline.mParameters.irisJpegProPhotoToSRGB
''','''        float[] cct = irisJpegColor
                ? basePipeline.mParameters.irisJpegProPhotoToDisplayP3
''',1)
s=s.replace('''        if(mode == ColorCorrectionTransform.CorrectionMode.MATRIXES){
            cct = basePipeline.mParameters.CCT.combineMatrix(basePipeline.mParameters.whitePoint);
''','''        if(!irisJpegColor && mode == ColorCorrectionTransform.CorrectionMode.MATRIXES){
            cct = basePipeline.mParameters.CCT.combineMatrix(basePipeline.mParameters.whitePoint);
''',1)
s=s.replace('Log.d(Name,"intermediateToSRGB: "+ Arrays.toString(cct));',
'''Log.d(Name,"intermediateToDisplay: "+ Arrays.toString(cct)
                + " workingGamut=" + (irisJpegColor ? "LINEAR_DISPLAY_P3" : "LEGACY"));''',1)
s=s.replace('''        if(mode == ColorCorrectionTransform.CorrectionMode.CUBE || mode == ColorCorrectionTransform.CorrectionMode.CUBES){
            glProg.setVar("CUBE0",cube[0]);
''','''        if(!irisJpegColor && (mode == ColorCorrectionTransform.CorrectionMode.CUBE || mode == ColorCorrectionTransform.CorrectionMode.CUBES)){
            glProg.setVar("CUBE0",cube[0]);
''',1)
s=s.replace('''        glProg.useAssetProgram("initial");
''','''        glProg.setDefine("IRIS_26567_P3_WORKING", irisJpegColor ? 1 : 0);
        glProg.setDefine("IRIS_26567_UNIVERSAL_COLOR",
                irisJpegColor && !calibratedIrisHueSat ? 1 : 0);
        glProg.useAssetProgram("initial");
''',1)
s=s.replace('''        if (basePipeline.mParameters.HSVMap != null) {
            HSVTexture = new GLTexture(new Point(basePipeline.mParameters.HSVMapSize[1], basePipeline.mParameters.HSVMapSize[0]), new GLFormat(GLFormat.DataType.FLOAT_32, 3), BufferUtils.getFrom(basePipeline.mParameters.HSVMap), GL_LINEAR, GL_CLAMP_TO_EDGE);
            glProg.setTexture("HSVMap", HSVTexture);
        }
''','''        if (useHsvMap) {
            HSVTexture = new GLTexture(new Point(basePipeline.mParameters.HSVMapSize[1], basePipeline.mParameters.HSVMapSize[0]), new GLFormat(GLFormat.DataType.FLOAT_32, 3), BufferUtils.getFrom(basePipeline.mParameters.HSVMap), GL_LINEAR, GL_CLAMP_TO_EDGE);
            glProg.setTexture("HSVMap", HSVTexture);
        }
''',1)
write(rel,s)

# Normal Photo uses the same P3 luminance axis and universal hue-preserving fallback when no calibrated HueSat map exists.
rel='app/src/main/assets/shaders/initial.glsl'
s=read(rel)
s=s.replace('''#define luminocity(x) dot(x.rgb, vec3(0.299, 0.587, 0.114))
''','''#ifndef IRIS_26567_P3_WORKING
#define IRIS_26567_P3_WORKING 0
#endif
#ifndef IRIS_26567_UNIVERSAL_COLOR
#define IRIS_26567_UNIVERSAL_COLOR 0
#endif
#if IRIS_26567_P3_WORKING == 1
#define luminocity(x) dot(x.rgb, vec3(0.22897456, 0.69173852, 0.07928691))
#else
#define luminocity(x) dot(x.rgb, vec3(0.299, 0.587, 0.114))
#endif
''',1)
# Add center-pixel universal perceptual colorfulness in linear P3 before tone/gamut; calibrated HSV bypasses it.
insert='''
vec3 iris26567UniversalP3Color(vec3 rgb) {
    float y = dot(rgb, vec3(0.22897456, 0.69173852, 0.07928691));
    vec3 chroma = rgb - vec3(y);
    float magnitude = length(chroma);
    float relativeChroma = magnitude / max(y, 0.08);
    float neutralActivation = smoothstep(0.0035, 0.018, magnitude);
    float chromaRolloff = 1.0 - smoothstep(0.08, 0.45, relativeChroma);
    float shadowGate = smoothstep(0.015, 0.075, y);
    float peak = max(rgb.r, max(rgb.g, rgb.b));
    float highlightGate = 1.0 - smoothstep(0.72, 0.98, peak);
    float requested = 1.0 + 0.32 * neutralActivation * chromaRolloff * shadowGate * highlightGate;
    float limitGain = 4.0;
    for (int k = 0; k < 3; ++k) {
        float c = chroma[k];
        if (c > 1.0e-7) limitGain = min(limitGain, max(1.0, (1.0 - y) / c));
        else if (c < -1.0e-7) limitGain = min(limitGain, max(1.0, (0.0 - y) / c));
    }
    float gain = clamp(min(requested, limitGain), 1.0, 1.32);
    return vec3(y) + chroma * gain;
}
''';
marker='''vec3 applyColorSpace(vec3 pRGB,float tonemapGain, float gainsVal){
'''
if s.count(marker)!=1: raise SystemExit('initial applyColorSpace anchor')
s=s.replace(marker,insert+marker,1)
s=s.replace('''    #endif
    float br = (pRGB.r+pRGB.g+pRGB.b)/3.0;
''','''    #endif
    #if IRIS_26567_UNIVERSAL_COLOR == 1
    pRGB = iris26567UniversalP3Color(max(pRGB, vec3(0.0)));
    #endif
    float br = (pRGB.r+pRGB.g+pRGB.b)/3.0;
''',1)
write(rel,s)

# PostPipeline output pixels are P3 when Iris JPEG solver owns color.
rel='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java'
s=read(rel)
s=s.replace('import android.graphics.Bitmap;\n','import android.graphics.Bitmap;\nimport android.graphics.ColorSpace;\nimport android.os.Build;\n',1)
s=s.replace('''        Bitmap res = resImg.getBufferedImage();

        /*
''','''        Bitmap res = resImg.getBufferedImage();
        /* IRIS_26567_INTERNAL_DISPLAY_P3_BITMAP_TAG
         * Iris JPEG pixels have already been rendered in Display-P3 primaries. Tag them at the
         * bitmap boundary so publication/Jin adapters cannot apply the old sRGB->P3 transform twice.
         */
        if (mParameters.irisJpegColorValid && Build.VERSION.SDK_INT >= 26
                && res != null && !res.isRecycled()) {
            res.setColorSpace(ColorSpace.get(ColorSpace.Named.DISPLAY_P3));
            Log.i("PostPipeline", "IRIS_26567_JPEG_WORKING_GAMUT bitmap=DISPLAY_P3 dngAffected=false");
        }

        /*
''',1)
write(rel,s)

# -----------------------------------------------------------------------------
# P3 luminance ownership after the color transform only.
# -----------------------------------------------------------------------------
rel='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java'
s=read(rel)
old='''    private static float luma(float r, float g, float b) {
        return 0.2126f * r + 0.7152f * g + 0.0722f * b;
    }
'''
new='''    private static float luma(float r, float g, float b) {
        // Candidate samples are already linear Display-P3. Preview sampling above remains
        // explicitly decoded sRGB/Rec.709 so the meter compares each source in its own primaries.
        return 0.22897456f * r + 0.69173852f * g + 0.07928691f * b;
    }
'''
if s.count(old)!=1: raise SystemExit('Viewfinder candidate luma anchor')
s=s.replace(old,new,1)
write(rel,s)
for rel in [
'app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/assets/shaders/motionv2/gainmap.glsl',
'app/src/main/assets/shaders/motionv2/iris_tone_controls.glsl']:
    s=read(rel)
    old=s
    s=s.replace('vec3(0.2126,0.7152,0.0722)','vec3(0.22897456,0.69173852,0.07928691)')
    s=s.replace('vec3(0.2126, 0.7152, 0.0722)','vec3(0.22897456, 0.69173852, 0.07928691)')
    if s==old: raise SystemExit(f'{rel} no luma weights')
    write(rel,s)

# Universal appearance: stronger but bounded P3-luma hue-preserving treatment.
rel='app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl'
s=read(rel)
s=s.replace('Common extended linear-sRGB appearance stage.','Common extended linear-Display-P3 appearance stage.',1)
s=s.replace('alter Rec.709 linear luminance','alter Display-P3 linear luminance',1)
s=s.replace('const vec3 LUMA_WEIGHTS = vec3(0.2126, 0.7152, 0.0722);','const vec3 LUMA_WEIGHTS = vec3(0.22897456, 0.69173852, 0.07928691);',1)
s=s.replace('''    float requestedGain = 1.0 + 0.22
''','''    float requestedGain = 1.0 + 0.32
''',1)
s=s.replace('clamp(min(requestedGain, gamutGainLimit), 1.0, 1.22)','clamp(min(requestedGain, gamutGainLimit), 1.0, 1.32)',1)
s=s.replace('own Rec.709 luminance','own Display-P3 luminance',1)
write(rel,s)
rel='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2AdaptiveColorAppearance.java'
s=read(rel)
s=s.replace('common extended linear-sRGB','common extended linear-Display-P3',1)
s=s.replace('private static final float MAX_WEAK_CHROMA_GAIN = 1.22f;','private static final float MAX_WEAK_CHROMA_GAIN = 1.32f;',1)
s=s.replace('''        Log.i(Name, "IRIS_26563_UNIVERSAL_ADAPTIVE_COLOR_APPEARANCE"
                + " commonLinearSrgb=true"
''','''        final boolean calibratedProfile = basePipeline.mParameters.HSVMap != null;
        Log.i(Name, "IRIS_26567_SHARED_JPEG_COLOR_APPEARANCE"
                + " commonLinearDisplayP3=true"
                + " profileSource=" + (calibratedProfile ? "CALIBRATED_HUESAT" : "UNIVERSAL")
''',1)
write(rel,s)
# Calibrated HueSat is the appearance owner when loaded; universal gain must not double-stack it.
rel='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2AdaptiveColorAppearance.java'
s=read(rel)
s=s.replace('''        glProg.useAssetProgram("motionv2/adaptive_color_appearance_26563");
''','''        final boolean calibratedProfile = basePipeline.mParameters.HSVMap != null
                && basePipeline.mParameters.HSVMapSize != null
                && basePipeline.mParameters.HSVMapSize.length >= 2
                && basePipeline.mParameters.HSVMapSize[0] > 0
                && basePipeline.mParameters.HSVMapSize[1] > 0
                && basePipeline.mParameters.HSVMap.length >=
                        basePipeline.mParameters.HSVMapSize[0]
                                * basePipeline.mParameters.HSVMapSize[1] * 3;
        if (calibratedProfile) glProg.setDefine("CALIBRATED_PROFILE", 1);
        glProg.useAssetProgram("motionv2/adaptive_color_appearance_26563");
''',1)
s=s.replace('''        final boolean calibratedProfile = basePipeline.mParameters.HSVMap != null;
        Log.i(Name, "IRIS_26567_SHARED_JPEG_COLOR_APPEARANCE"
''','''        Log.i(Name, "IRIS_26567_SHARED_JPEG_COLOR_APPEARANCE"
''',1)
write(rel,s)
rel='app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl'
s=read(rel)
s=s.replace('''out vec3 Output;
''','''out vec3 Output;
#ifndef CALIBRATED_PROFILE
#define CALIBRATED_PROFILE 0
#endif
''',1)
s=s.replace('''    vec3 centerRgb = rgbAt(position, imageSize);
''','''    vec3 centerRgb = rgbAt(position, imageSize);
#if CALIBRATED_PROFILE == 1
    Output = centerRgb;
    return;
#endif
''',1)
write(rel,s)

# -----------------------------------------------------------------------------
# Publication: already-P3 bitmaps are encoded/tagged without a second conversion.
# -----------------------------------------------------------------------------
rel='app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java'
s=read(rel)
s=s.replace('''    public static Bitmap toDisplayP3BitmapCopy(Bitmap source) {
        if (source == null || source.isRecycled() || Build.VERSION.SDK_INT < 26) return null;
        Bitmap out = null;
        try {
            out = source.copy(Bitmap.Config.ARGB_8888, true);
            if (out != null && convertSrgbToDisplayP3Native(out)) {
''','''    private static boolean isDisplayP3Bitmap(Bitmap source) {
        if (source == null || source.isRecycled() || Build.VERSION.SDK_INT < 26) return false;
        ColorSpace cs = source.getColorSpace();
        return cs != null && cs.equals(ColorSpace.get(ColorSpace.Named.DISPLAY_P3));
    }

    public static Bitmap toDisplayP3BitmapCopy(Bitmap source) {
        if (source == null || source.isRecycled() || Build.VERSION.SDK_INT < 26) return null;
        Bitmap out = null;
        try {
            out = source.copy(Bitmap.Config.ARGB_8888, true);
            if (out != null && isDisplayP3Bitmap(source)) {
                out.setColorSpace(ColorSpace.get(ColorSpace.Named.DISPLAY_P3));
                Log.i(TAG, "IRIS_26567_DISPLAY_P3_COPY alreadyP3=true conversion=false");
                return out;
            }
            if (out != null && convertSrgbToDisplayP3Native(out)) {
''',1)
s=s.replace('''                boolean ok=writeNative(bitmap,output.toString(),Math.max(1,Math.min(100,quality)));
''','''                boolean ok=writeNative(bitmap,output.toString(),Math.max(1,Math.min(100,quality)),isDisplayP3Bitmap(bitmap));
''',1)
s=s.replace('''            if(!writeNative(bitmap,base.toString(),Math.max(1,Math.min(100,quality))))return false;
''','''            if(!writeNative(bitmap,base.toString(),Math.max(1,Math.min(100,quality)),isDisplayP3Bitmap(bitmap)))return false;
''',1)
s=s.replace('''            final float[] proPhotoToSrgb = parameters.irisJpegColorValid
                    ? parameters.irisJpegProPhotoToSRGB : parameters.proPhotoToSRGB;
''','''            final float[] profileToDisplay = parameters.irisJpegColorValid
                    ? parameters.irisJpegProPhotoToDisplayP3 : parameters.proPhotoToSRGB;
''',1)
s=s.replace('''                    sensorToProPhoto, proPhotoToSrgb,
''','''                    sensorToProPhoto, profileToDisplay,
''',1)
s=s.replace('private static native boolean writeNative(Bitmap bitmap,String path,int quality);',
'''private static native boolean writeNative(Bitmap bitmap,String path,int quality,boolean sourceDisplayP3);''',1)
write(rel,s)

# -----------------------------------------------------------------------------
# Preserve Jin's learned sRGB contract while base bitmap is P3.
# -----------------------------------------------------------------------------
rel='app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightNeuralEnhancer.java'
s=read(rel)
s=s.replace('import android.graphics.Bitmap;\n','import android.graphics.Bitmap;\nimport android.graphics.Canvas;\nimport android.graphics.ColorSpace;\n',1)
s=s.replace('''        Bitmap small = null;
        try {
            ensureCpuSession();
            small = Bitmap.createScaledBitmap(base, N, N, true);
''','''        Bitmap small = null;
        Bitmap inferenceSource = null;
        try {
            ensureCpuSession();
            ColorSpace baseColorSpace = base.getColorSpace();
            final boolean baseDisplayP3 = baseColorSpace != null
                    && baseColorSpace.equals(ColorSpace.get(ColorSpace.Named.DISPLAY_P3));
            if (baseDisplayP3) {
                inferenceSource = Bitmap.createBitmap(base.getWidth(), base.getHeight(),
                        Bitmap.Config.ARGB_8888, true, ColorSpace.get(ColorSpace.Named.SRGB));
                new Canvas(inferenceSource).drawBitmap(base, 0.0f, 0.0f, null);
            }
            Bitmap jinSource = inferenceSource != null ? inferenceSource : base;
            small = Bitmap.createScaledBitmap(jinSource, N, N, true);
''',1)
s=s.replace('''            if (!applyReferenceResidualNative(base, residual, px, N, N)) {
''','''            if (!applyReferenceResidualNative(base, residual, px, N, N, baseDisplayP3)) {
''',1)
s=s.replace('''            if (small != null && small != base && !small.isRecycled()) small.recycle();
''','''            if (small != null && small != base && !small.isRecycled()) small.recycle();
            if (inferenceSource != null && inferenceSource != base && !inferenceSource.isRecycled()) inferenceSource.recycle();
''',1)
s=s.replace('''            int residualWidth, int residualHeight);
''','''            int residualWidth, int residualHeight, boolean baseDisplayP3);
''',1)
write(rel,s)

# -----------------------------------------------------------------------------
# True2x contracts: retain exact DNG carrier; add phase-support sidecar for JPEG gating.
# -----------------------------------------------------------------------------
rel='app/src/main/java/com/hinnka/mycamera/processor/RawStackContracts.kt'
rep(rel,'    val true2xNativeVgnGuidePath: String? = null,\n','''    val true2xNativeVgnGuidePath: String? = null,
    /* One unsigned byte per true-2x pixel: exact accepted distinct 2x2 phase count 0..4.
     * JPEG-only reliability evidence; never consumed by DNG.
     */
    val true2xPhaseSupportPath: String? = null,
''')
rep(rel,'    val true2xPhaseSupportMean: Float = 1f,\n    val true2xPhaseSupportP10: Float = 1f,\n','    val true2xPhaseSupportMean: Float = 0f,\n    val true2xPhaseSupportP10: Float = 0f,\n')

rel='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'
s=read(rel)
s=s.replace('''        val useFrameWeight: Boolean,
    )

    private data class True2xResult(
        val linearRgbPath: String,
        val nativeVgnGuidePath: String,
''','''        val useFrameWeight: Boolean,
        val dominantPhaseBin: Int,
        val qualityScore: Float,
    )

    private data class True2xPhaseStats(
        val mean: Float,
        val p10: Float,
        val percentages: FloatArray,
    )

    private data class True2xResult(
        val linearRgbPath: String,
        val nativeVgnGuidePath: String,
        val phaseSupportPath: String,
''',1)
s=s.replace('''        val true2xEvidence = ArrayList<True2xFrameEvidence>()
''','''        val true2xEvidence = ArrayList<True2xFrameEvidence>()
        /* IRIS_26567_FAST_JPEG_TRUE2X_PHASE_SELECTION
         * DNG requests retain the exact full 26566 NORMAL evidence population. JPEG-only SR
         * retains the strongest accepted frame for each of the four subpixel phase bins.
         */
        val true2xFastPhaseSlots: Array<True2xFrameEvidence?>? =
            if (enableSabreSuperRes && !exportNormalStackedDng) arrayOfNulls(4) else null
''',1)
# Replace reference persistence block.
old='''            if (enableSabreSuperRes) {
                true2xEvidence += persistTrue2xEvidence(
                    frameIndex = 0,
                    calibration = referenceCalibration,
                    flow = zeroFlow,
                    covariance = referenceCovariance,
                    rejection = identityWeight,
                    covarianceWidth = extractedWidth,
                    covarianceHeight = extractedHeight,
                    rejectionWidth = coverageWidth,
                    rejectionHeight = coverageHeight,
                    useFrameWeight = false,
                )
            }
'''
new='''            if (enableSabreSuperRes) {
                val referenceEvidence = persistTrue2xEvidence(
                    frameIndex = 0,
                    calibration = referenceCalibration,
                    flow = zeroFlow,
                    covariance = referenceCovariance,
                    rejection = identityWeight,
                    covarianceWidth = extractedWidth,
                    covarianceHeight = extractedHeight,
                    rejectionWidth = coverageWidth,
                    rejectionHeight = coverageHeight,
                    useFrameWeight = false,
                    existingPhaseEvidence = true2xFastPhaseSlots,
                )
                if (true2xFastPhaseSlots == null) true2xEvidence += referenceEvidence
            }
'''
if s.count(old)!=1: raise SystemExit('reference evidence anchor')
s=s.replace(old,new,1)
old='''                if (enableSabreSuperRes && frame.role == RawBurstFrameRole.NORMAL) {
                    true2xEvidence += persistTrue2xEvidence(
                        frameIndex = index,
                        calibration = calibration,
                        flow = flow,
                        covariance = currentCovariance,
                        rejection = frameWeight,
                        covarianceWidth = extractedWidth,
                        covarianceHeight = extractedHeight,
                        rejectionWidth = coverageWidth,
                        rejectionHeight = coverageHeight,
                        useFrameWeight = true,
                    )
                }
'''
new='''                if (enableSabreSuperRes && frame.role == RawBurstFrameRole.NORMAL) {
                    val candidateEvidence = persistTrue2xEvidence(
                        frameIndex = index,
                        calibration = calibration,
                        flow = flow,
                        covariance = currentCovariance,
                        rejection = frameWeight,
                        covarianceWidth = extractedWidth,
                        covarianceHeight = extractedHeight,
                        rejectionWidth = coverageWidth,
                        rejectionHeight = coverageHeight,
                        useFrameWeight = true,
                        existingPhaseEvidence = true2xFastPhaseSlots,
                    )
                    if (true2xFastPhaseSlots == null) true2xEvidence += candidateEvidence
                }
'''
if s.count(old)!=1: raise SystemExit('loop evidence anchor')
s=s.replace(old,new,1)
# Reconstruction selects full list for DNG, four slots only for JPEG.
s=s.replace('''                    val rawResult = reconstructTrue2x(frames, images, true2xEvidence)
''','''                    val reconstructionEvidence = true2xFastPhaseSlots
                        ?.filterNotNull()
                        ?: true2xEvidence
                    PLog.i(SABRE_TAG, "IRIS_26567_TRUE2X_EVIDENCE_POLICY dngRequested=$exportNormalStackedDng " +
                        "normalFrames=$normalFrameCount retained=${reconstructionEvidence.size} " +
                        "jpegPhaseCap=${true2xFastPhaseSlots != null}")
                    val rawResult = reconstructTrue2x(frames, images, reconstructionEvidence)
''',1)
s=s.replace('''                    cleanupTrue2xEvidence(true2xEvidence)
                    true2xEvidence.clear()
''','''                    cleanupTrue2xEvidence(true2xFastPhaseSlots?.filterNotNull() ?: true2xEvidence)
                    true2xEvidence.clear()
                    true2xFastPhaseSlots?.fill(null)
''',1)
# Result fields.
s=s.replace('''                true2xNativeVgnGuidePath = true2xResult?.nativeVgnGuidePath,
                true2xWidth = true2xResult?.width ?: 0,
''','''                true2xNativeVgnGuidePath = true2xResult?.nativeVgnGuidePath,
                true2xPhaseSupportPath = true2xResult?.phaseSupportPath,
                true2xWidth = true2xResult?.width ?: 0,
''',1)
s=s.replace('''                true2xPhaseSupportMean = true2xResult?.phaseSupportMean ?: 1f,
                true2xPhaseSupportP10 = true2xResult?.phaseSupportP10 ?: 1f,
''','''                true2xPhaseSupportMean = true2xResult?.phaseSupportMean ?: 0f,
                true2xPhaseSupportP10 = true2xResult?.phaseSupportP10 ?: 0f,
''',1)
# finally cleanup phase support if not returned.
s=s.replace('''                runCatching { true2xResult?.nativeVgnGuidePath?.takeIf { it.isNotEmpty() }?.let { File(it).delete() } }
''','''                runCatching { true2xResult?.nativeVgnGuidePath?.takeIf { it.isNotEmpty() }?.let { File(it).delete() } }
                runCatching { true2xResult?.phaseSupportPath?.takeIf { it.isNotEmpty() }?.let { File(it).delete() } }
''',1)
# Refactor read flow: add dominant phase helper and quality helper.
anchor='''    private fun persistTrue2xEvidence(
        frameIndex: Int,
'''
insert='''    private fun dominantTrue2xPhaseBin(flowData: ByteBuffer, flowWidth: Int, flowHeight: Int): Int {
        val values = flowData.duplicate().order(ByteOrder.nativeOrder()).asShortBuffer()
        val bins = IntArray(4)
        val pixels = flowWidth * flowHeight
        val step = max(1, pixels / 2048)
        var index = 0
        while (index < pixels) {
            val fx = Half.toFloat(values.get(index * 4)) * width
            val fy = Half.toFloat(values.get(index * 4 + 1)) * height
            if (fx.isFinite() && fy.isFinite()) {
                val px = fx - kotlin.math.floor(fx)
                val py = fy - kotlin.math.floor(fy)
                val bin = (if (px >= 0.5f) 1 else 0) + (if (py >= 0.5f) 2 else 0)
                bins[bin]++
            }
            index += step
        }
        return bins.indices.maxByOrNull { bins[it] } ?: 0
    }

    private fun true2xRejectionQuality(bytes: ByteArray?): Float {
        if (bytes == null || bytes.isEmpty()) return 1f
        var sum = 0L
        for (value in bytes) sum += value.toInt() and 0xff
        return (sum.toDouble() / (bytes.size.toDouble() * 255.0)).toFloat().coerceIn(0f, 1f)
    }

'''+anchor
if s.count(anchor)!=1: raise SystemExit('persist anchor')
s=s.replace(anchor,insert,1)
# Replace whole persist function up to next readTrue2xFileRegion.
pattern=r'''    private fun persistTrue2xEvidence\(\n        frameIndex: Int,.*?\n    \}\n\n    private fun readTrue2xFileRegion'''
replacement='''    private fun persistTrue2xEvidence(
        frameIndex: Int,
        calibration: FrameCalibration,
        flow: SabreConvertedAlignment,
        covariance: Int,
        rejection: Int,
        covarianceWidth: Int,
        covarianceHeight: Int,
        rejectionWidth: Int,
        rejectionHeight: Int,
        useFrameWeight: Boolean,
        existingPhaseEvidence: Array<True2xFrameEvidence?>?,
    ): True2xFrameEvidence {
        val directory = checkNotNull(sabreSuperResTempDir) { "True2x temp directory is absent" }
        require(directory.exists() || directory.mkdirs()) { "Unable to create ${directory.absolutePath}" }
        val (flowData, maxX, maxY) = readTrue2xFlow(flow)
        val spec = checkNotNull(textureSpecs[flow.texture])
        val phaseBin = dominantTrue2xPhaseBin(flowData, spec.width, spec.height)
        val rejectionBytes = if (useFrameWeight) readR8Mask(
            rejection, "IRIS26567 rejection quality frame=$frameIndex", rejectionWidth, rejectionHeight,
        ) else null
        val quality = true2xRejectionQuality(rejectionBytes)
        val old = existingPhaseEvidence?.get(phaseBin)
        if (old != null && old.qualityScore >= quality) {
            LargeDirectBuffer.free(flowData)
            PLog.i(SABRE_TAG, "IRIS_26567_TRUE2X_PHASE_SKIP frame=$frameIndex phase=$phaseBin " +
                "quality=$quality retained=${old.frameIndex}:${old.qualityScore}")
            return old
        }
        val covarianceFile = File(directory, "iris26564_cov_${frameIndex}_${System.nanoTime()}.rgb10a2")
        persistTrue2xTexture(
            covariance, covarianceWidth, covarianceHeight,
            GLES30.GL_RGBA, GLES30.GL_UNSIGNED_INT_2_10_10_10_REV, 4,
            covarianceFile, "IRIS26564 covariance frame=$frameIndex",
        )
        val rejectionFile = rejectionBytes?.let { bytes ->
            File(directory, "iris26564_rej_${frameIndex}_${System.nanoTime()}.r8").also { file ->
                file.outputStream().use { it.write(bytes) }
                require(file.length() == bytes.size.toLong())
            }
        }
        val result = True2xFrameEvidence(
            frameIndex = frameIndex,
            calibration = calibration,
            flowData = flowData,
            flowWidth = spec.width,
            flowHeight = spec.height,
            flowScaleX = flow.scaleX,
            flowScaleY = flow.scaleY,
            flowOffsetX = flow.offsetX,
            flowOffsetY = flow.offsetY,
            covarianceFile = covarianceFile,
            covarianceWidth = covarianceWidth,
            covarianceHeight = covarianceHeight,
            rejectionFile = rejectionFile,
            rejectionWidth = rejectionWidth,
            rejectionHeight = rejectionHeight,
            maxAbsFlowPixelsX = maxX,
            maxAbsFlowPixelsY = maxY,
            useFrameWeight = useFrameWeight,
            dominantPhaseBin = phaseBin,
            qualityScore = quality,
        )
        if (existingPhaseEvidence != null) {
            if (old != null && old !== result) cleanupTrue2xEvidence(listOf(old))
            existingPhaseEvidence[phaseBin] = result
            PLog.i(SABRE_TAG, "IRIS_26567_TRUE2X_PHASE_RETAIN frame=$frameIndex phase=$phaseBin quality=$quality")
        }
        return result
    }

    private fun readTrue2xFileRegion'''
out,n=re.subn(pattern,replacement,s,count=1,flags=re.S)
if n!=1: raise SystemExit(f'persist regex {n}')
s=out
# Phase histogram zero support and stats object.
s=s.replace('''            val count = Integer.bitCount(bits).coerceIn(1, 4)
            histogram[count]++
''','''            val count = Integer.bitCount(bits).coerceIn(0, 4)
            histogram[count]++
''',1)
s=s.replace('histogram[count.coerceIn(1, 4)]++','histogram[count.coerceIn(0, 4)]++',1)
old='''    private fun true2xPhaseStats(histogram: LongArray): Pair<Float, Float> {
        val total = (1..4).sumOf { histogram[it] }.coerceAtLeast(1L)
        val mean = (1..4).sumOf { it.toDouble() * histogram[it] }.div(total).toFloat()
        val target = kotlin.math.ceil(total * 0.10).toLong().coerceAtLeast(1L)
        var cumulative = 0L
        var p10 = 1
        for (support in 1..4) {
            cumulative += histogram[support]
            if (cumulative >= target) { p10 = support; break }
        }
        return mean to p10.toFloat()
    }
'''
new='''    private fun true2xPhaseStats(histogram: LongArray): True2xPhaseStats {
        val total = (0..4).sumOf { histogram[it] }.coerceAtLeast(1L)
        val mean = (0..4).sumOf { it.toDouble() * histogram[it] }.div(total).toFloat()
        val target = kotlin.math.ceil(total * 0.10).toLong().coerceAtLeast(1L)
        var cumulative = 0L
        var p10 = 0
        for (support in 0..4) {
            cumulative += histogram[support]
            if (cumulative >= target) { p10 = support; break }
        }
        val percentages = FloatArray(5) { support ->
            (100.0 * histogram[support].toDouble() / total.toDouble()).toFloat()
        }
        PLog.i(SABRE_TAG, "IRIS_26567_TRUE2X_PHASE_SUPPORT zero=${percentages[0]} one=${percentages[1]} " +
            "two=${percentages[2]} three=${percentages[3]} four=${percentages[4]} mean=$mean p10=$p10")
        return True2xPhaseStats(mean, p10.toFloat(), percentages)
    }

    private fun writeTrue2xPhaseSupportTile(
        output: RandomAccessFile, support: ByteBuffer, left: Int, top: Int,
        tileWidth: Int, tileHeight: Int, fullWidth: Int, rgbaMask: Boolean,
    ) {
        val row = ByteArray(tileWidth)
        for (y in 0 until tileHeight) {
            for (x in 0 until tileWidth) {
                val index = y * tileWidth + x
                val count = if (rgbaMask) {
                    var value = 0
                    for (channel in 0 until 4) if ((support.get(index * 4 + channel).toInt() and 0xff) > 0) value++
                    value
                } else Integer.bitCount(support.get(index).toInt() and 0x0f)
                row[x] = count.coerceIn(0, 4).toByte()
            }
            output.seek(((top + y).toLong() * fullWidth + left).toLong())
            output.write(row)
        }
    }
'''
if s.count(old)!=1: raise SystemExit('phase stats anchor')
s=s.replace(old,new,1)
# run CPU/GPU support output parameter and open file alongside output.
s=s.replace('''        outputFile: File,
        fullOutputWidth: Int,
''','''        outputFile: File,
        phaseSupportFile: File,
        fullOutputWidth: Int,
''',1)
s=s.replace('''        RandomAccessFile(outputFile, "rw").use { out ->
            out.setLength(fullOutputWidth.toLong() * fullOutputHeight * TRUE2X_RGB16F_BYTES_PER_PIXEL)
''','''        RandomAccessFile(outputFile, "rw").use { out ->
            RandomAccessFile(phaseSupportFile, "rw").use { phaseOut ->
            out.setLength(fullOutputWidth.toLong() * fullOutputHeight * TRUE2X_RGB16F_BYTES_PER_PIXEL)
            phaseOut.setLength(fullOutputWidth.toLong() * fullOutputHeight)
''',1)
s=s.replace('''                    phase.position(0)
                    updateTrue2xPhaseHistogram(phase, pixelCount, phaseHistogram)
''','''                    phase.position(0)
                    updateTrue2xPhaseHistogram(phase, pixelCount, phaseHistogram)
                    writeTrue2xPhaseSupportTile(
                        phaseOut, phase, left, top, tileWidth, tileHeight, fullOutputWidth, false,
                    )
''',1)
# close extra RandomAccessFile before return: target sequence just before expected check in CPU.
# Find first occurrence after runTrue2xCpu where two braces currently close loops/use.
needle='''                top += tileHeight
            }
        }
        return true2xPhaseStats(phaseHistogram)
'''
replace='''                top += tileHeight
            }
            phaseOut.fd.sync()
            }
        }
        return true2xPhaseStats(phaseHistogram)
'''
if s.count(needle)!=1: raise SystemExit('CPU close anchor')
s=s.replace(needle,replace,1)
# GPU signature second occurrence.
start=s.index('    private fun runTrue2xGpu(')
pos=s.index('        outputFile: File,',start)
s=s[:pos]+s[pos:].replace('        outputFile: File,\n        fullOutputWidth: Int,','        outputFile: File,\n        phaseSupportFile: File,\n        fullOutputWidth: Int,',1)
# GPU RandomAccess open.
pos=s.index('    private fun runTrue2xGpu(')
segment=s[pos:]
old='''        RandomAccessFile(outputFile, "rw").use { out ->
            out.setLength(fullOutputWidth.toLong() * fullOutputHeight * TRUE2X_RGB16F_BYTES_PER_PIXEL)
'''
new='''        RandomAccessFile(outputFile, "rw").use { out ->
            RandomAccessFile(phaseSupportFile, "rw").use { phaseOut ->
            out.setLength(fullOutputWidth.toLong() * fullOutputHeight * TRUE2X_RGB16F_BYTES_PER_PIXEL)
            phaseOut.setLength(fullOutputWidth.toLong() * fullOutputHeight)
'''
if segment.count(old)!=1: raise SystemExit('GPU RAF anchor')
segment=segment.replace(old,new,1)
segment=segment.replace('''                        updateTrue2xGpuPhaseHistogram(
                            phaseRead, tileWidth * tileHeight, phaseHistogram,
                        )
''','''                        updateTrue2xGpuPhaseHistogram(
                            phaseRead, tileWidth * tileHeight, phaseHistogram,
                        )
                        writeTrue2xPhaseSupportTile(
                            phaseOut, phaseRead, left, top, tileWidth, tileHeight, fullOutputWidth, true,
                        )
''',1)
needle='''                top += tileHeight
            }
        }
        if (lensTexture != 0 && textures.contains(lensTexture)) {
'''
replace='''                top += tileHeight
            }
            phaseOut.fd.sync()
            }
        }
        if (lensTexture != 0 && textures.contains(lensTexture)) {
'''
if segment.count(needle)!=1: raise SystemExit('GPU close anchor')
segment=segment.replace(needle,replace,1)
s=s[:pos]+segment
# reconstruct creates sidecar, new stats fields.
old='''        val gpuFile = File(directory, "iris26564_true2x_${System.nanoTime()}.rgb16f")
        val gpuAttempt = runCatching {
            val phase = runTrue2xGpu(images, evidence, gpuFile, outputWidth, outputHeight)
            True2xResult(
                gpuFile.absolutePath, "", outputWidth, outputHeight, "GPU",
                phase.first, phase.second, elapsedMs(start),
            )
        }
'''
new='''        val gpuFile = File(directory, "iris26564_true2x_${System.nanoTime()}.rgb16f")
        val gpuPhaseFile = File(directory, "iris26567_true2x_phase_${System.nanoTime()}.u8")
        val gpuAttempt = runCatching {
            val phase = runTrue2xGpu(images, evidence, gpuFile, gpuPhaseFile, outputWidth, outputHeight)
            True2xResult(
                gpuFile.absolutePath, "", gpuPhaseFile.absolutePath, outputWidth, outputHeight, "GPU",
                phase.mean, phase.p10, elapsedMs(start),
            )
        }
'''
if s.count(old)!=1: raise SystemExit('gpu reconstruct anchor')
s=s.replace(old,new,1)
s=s.replace('''        runCatching { gpuFile.delete() }
        val cpuStart = System.nanoTime()
        val cpuFile = File(directory, "iris26564_true2x_cpu_${System.nanoTime()}.rgb16f")
        val phase = runTrue2xCpu(frames, images, evidence, cpuFile, outputWidth, outputHeight)
        return True2xResult(
            cpuFile.absolutePath, "", outputWidth, outputHeight, "CPU",
            phase.first, phase.second, elapsedMs(cpuStart),
        )
''','''        runCatching { gpuFile.delete() }
        runCatching { gpuPhaseFile.delete() }
        val cpuStart = System.nanoTime()
        val cpuFile = File(directory, "iris26564_true2x_cpu_${System.nanoTime()}.rgb16f")
        val cpuPhaseFile = File(directory, "iris26567_true2x_phase_cpu_${System.nanoTime()}.u8")
        val phase = runTrue2xCpu(frames, images, evidence, cpuFile, cpuPhaseFile, outputWidth, outputHeight)
        return True2xResult(
            cpuFile.absolutePath, "", cpuPhaseFile.absolutePath, outputWidth, outputHeight, "CPU",
            phase.mean, phase.p10, elapsedMs(cpuStart),
        )
''',1)
# Source-CFA clipping reliability belongs to phase eligibility only; accumulation/DNG bytes stay untouched.
s=s.replace('''                                    uniform2f(program, "uCovRangeB", COV_MIN_B, COV_MAX_B - COV_MIN_B)
                                    GLES30.glEnable(GLES30.GL_BLEND)
''','''                                    uniform2f(program, "uCovRangeB", COV_MIN_B, COV_MAX_B - COV_MIN_B)
                                    uniform1f(program, "uRawClipThreshold", sensorWhiteLevel * 0.985f)
                                    GLES30.glEnable(GLES30.GL_BLEND)
''',1)
# CPU fallback gets the identical source-domain clipping threshold for phase support only.
s=s.replace('''                                        ev.useFrameWeight,
                                    )
''','''                                        ev.useFrameWeight, sensorWhiteLevel * 0.985f,
                                    )
''',1)
# rawResult.copy now keeps phase path automatically. Ensure constructor raw positions fixed above.
write(rel,s)

rel='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'
s=read(rel)
merge_start=s.index('    val true2xMerge26564 = \"\"\"')
merge_end=s.index('    val true2xResolve26564 = \"\"\"', merge_start)
block=s[merge_start:merge_end]
old='        uniform vec2 uCovRangeB;\n'
new='        uniform vec2 uCovRangeB;\n        uniform float uRawClipThreshold;\n'
if block.count(old)!=1: raise SystemExit(f'{rel}: true2x uCovRangeB count {block.count(old)}')
block=block.replace(old,new,1)
old='        void sampleRbf(vec2 sensorCoordinate, vec3 covariance,\n                       out vec3 accumulatedColor, out vec3 accumulatedWeight) {\n'
new='        void sampleRbf(vec2 sensorCoordinate, vec3 covariance,\n                       out vec3 accumulatedColor, out vec3 accumulatedWeight,\n                       out float sourceRawPeak) {\n'
if block.count(old)!=1: raise SystemExit(f'{rel}: true2x sampleRbf signature count {block.count(old)}')
block=block.replace(old,new,1)
old='            int type = (((position.y + bayerOffset.y) & 1) << 1) +\n                ((position.x + bayerOffset.x) & 1);\n            vec4 cornerWeights = vec4(weights[0][0], weights[0][2], weights[2][0], weights[2][2]);\n'
new='            int type = (((position.y + bayerOffset.y) & 1) << 1) +\n                ((position.x + bayerOffset.x) & 1);\n            sourceRawPeak = 0.0;\n            for (int sx = 0; sx < 3; ++sx) {\n                for (int sy = 0; sy < 3; ++sy) sourceRawPeak = max(sourceRawPeak, bayerValue[sx][sy]);\n            }\n            vec4 cornerWeights = vec4(weights[0][0], weights[0][2], weights[2][0], weights[2][2]);\n'
if block.count(old)!=1: raise SystemExit(f'{rel}: true2x source peak anchor count {block.count(old)}')
block=block.replace(old,new,1)
old='            vec3 color;\n            vec3 weights;\n            sampleRbf(sampleUv * vec2(uRawFullSize), covariance, color, weights);\n'
new='            vec3 color;\n            vec3 weights;\n            float sourceRawPeak;\n            sampleRbf(sampleUv * vec2(uRawFullSize), covariance, color, weights, sourceRawPeak);\n'
if block.count(old)!=1: raise SystemExit(f'{rel}: true2x sampleRbf call count {block.count(old)}')
block=block.replace(old,new,1)
old='            if (frameWeight > 0.08) {\n'
new='            if (frameWeight > 0.08 && sourceRawPeak < uRawClipThreshold) {\n'
if block.count(old)!=1: raise SystemExit(f'{rel}: true2x phase gate count {block.count(old)}')
block=block.replace(old,new,1)
# 26567 permanent GLSL reserved-identifier regression: `packed` is reserved in the applicable
# GLSL/GLSL ES union. Rename only this true2x local; covariance math is unchanged.
old='            vec3 packed = sampleCovariancePacked(sampleUv);\n'
new='            vec3 packedCovariance = sampleCovariancePacked(sampleUv);\n'
if block.count(old)!=1: raise SystemExit(f'{rel}: true2x reserved packed declaration count {block.count(old)}')
block=block.replace(old,new,1)
for axis in ('x','y','z'):
    old=f'packed.{axis}'
    new=f'packedCovariance.{axis}'
    if block.count(old)!=1: raise SystemExit(f'{rel}: true2x reserved packed.{axis} count {block.count(old)}')
    block=block.replace(old,new,1)
s=s[:merge_start]+block+s[merge_end:]
write(rel,s)
# -----------------------------------------------------------------------------
# Bridge consumes support sidecar and removes redundant full-50MP denoise for JPEG derivative.
# -----------------------------------------------------------------------------
rel='app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt'
s=read(rel)
s=s.replace('''        var true2xNativeVgnGuidePathForCleanup: String? = null
        var true2xRenderRgbPathForCleanup: String? = null
''','''        var true2xNativeVgnGuidePathForCleanup: String? = null
        var true2xPhaseSupportPathForCleanup: String? = null
        var true2xRenderRgbPathForCleanup: String? = null
''',1)
s=s.replace('''            true2xLinearRgbPathForCleanup = stacked.true2xLinearRgbPath
''','''            true2xLinearRgbPathForCleanup = stacked.true2xLinearRgbPath
            true2xPhaseSupportPathForCleanup = stacked.true2xPhaseSupportPath
''',1)
s=s.replace('''                val guidePath = stacked.true2xNativeVgnGuidePath
                requireParity(rawPath != null && guidePath != null &&
''','''                val guidePath = stacked.true2xNativeVgnGuidePath
                val phaseSupportPath = stacked.true2xPhaseSupportPath
                requireParity(rawPath != null && guidePath != null && phaseSupportPath != null &&
''',1)
s=s.replace('''                val runTrue2xFullResolutionMgc = runFullResolutionDenoise && lumaScale > 0f
                resultTrue2xRenderRgbPath = buildTrue2xRenderCarrier(
                    rawPath = checkNotNull(rawPath),
                    guidePath = checkNotNull(guidePath),
''','''                /* IRIS_26567_SABRE_GUIDED_DETAIL_ONLY
                 * Native Sabre/VGN is already denoised and now owns every output RGB ratio. Do not
                 * run another 50MP spatial denoiser over the color-neutral detail derivative.
                 */
                val runTrue2xFullResolutionMgc = false
                resultTrue2xRenderRgbPath = buildTrue2xRenderCarrier(
                    rawPath = checkNotNull(rawPath),
                    guidePath = checkNotNull(guidePath),
                    phaseSupportPath = checkNotNull(phaseSupportPath),
''',1)
s=s.replace('''                runCatching { File(guidePath).delete() }
                true2xNativeVgnGuidePathForCleanup = null
''','''                runCatching { File(guidePath).delete() }
                true2xNativeVgnGuidePathForCleanup = null
                runCatching { File(phaseSupportPath).delete() }
                true2xPhaseSupportPathForCleanup = null
''',1)
s=s.replace('''                    "vgnGuideConsumed=true residualDenoise=$runTrue2xFullResolutionMgc " +
''','''                    "sabreRgbChromaOwner=true phaseSupportConsumed=true scalarDetailOnly=true " +
                    "vgnGuideConsumed=true residualDenoise=$runTrue2xFullResolutionMgc " +
''',1)
s=s.replace('''                stacked.true2xPhaseSupportMean.isFinite() &&
                        stacked.true2xPhaseSupportMean in 1f..4f &&
                        stacked.true2xPhaseSupportP10.isFinite() &&
                        stacked.true2xPhaseSupportP10 in 1f..4f,
''','''                stacked.true2xPhaseSupportMean.isFinite() &&
                        stacked.true2xPhaseSupportMean in 0f..4f &&
                        stacked.true2xPhaseSupportP10.isFinite() &&
                        stacked.true2xPhaseSupportP10 in 0f..4f,
''',1)
s=s.replace('''                true2xNativeVgnGuidePathForCleanup?.let { path -> runCatching { File(path).delete() } }
                true2xRenderRgbPathForCleanup?.let { path -> runCatching { File(path).delete() } }
''','''                true2xNativeVgnGuidePathForCleanup?.let { path -> runCatching { File(path).delete() } }
                true2xPhaseSupportPathForCleanup?.let { path -> runCatching { File(path).delete() } }
                true2xRenderRgbPathForCleanup?.let { path -> runCatching { File(path).delete() } }
''',1)
# Build carrier signature and native call/stats.
s=s.replace('''    private fun buildTrue2xRenderCarrier(
        rawPath: String,
        guidePath: String,
''','''    private fun buildTrue2xRenderCarrier(
        rawPath: String,
        guidePath: String,
        phaseSupportPath: String,
''',1)
s=s.replace('''        val guideFile = File(guidePath)
        val expectedBytes = width.toLong() * height * 3L * Short.SIZE_BYTES
''','''        val guideFile = File(guidePath)
        val phaseFile = File(phaseSupportPath)
        val expectedBytes = width.toLong() * height * 3L * Short.SIZE_BYTES
''',1)
s=s.replace('''        requireParity(guideFile.isFile && guideFile.length() == expectedBytes / 4L,
            "26564 true2x VGN guide size mismatch")
''','''        requireParity(guideFile.isFile && guideFile.length() == expectedBytes / 4L,
            "26564 true2x VGN guide size mismatch")
        requireParity(phaseFile.isFile && phaseFile.length() == width.toLong() * height,
            "26567 true2x phase support size mismatch")
''',1)
s=s.replace('''        try {
            var top = 0
''','''        val detailStats = LongArray(4)
        try {
            var top = 0
''',1)
s=s.replace('''                                rawPath, width, height, guidePath, width / 2, height / 2,
                                regionLeft, regionTop, regionWidth, regionHeight, rgba,
''','''                                rawPath, width, height, guidePath, width / 2, height / 2,
                                phaseSupportPath, regionLeft, regionTop, regionWidth, regionHeight,
                                rgba, detailStats,
''',1)
s=s.replace('''            requireParity(renderFile.length() == expectedBytes,
                "26564 true2x render derivative byte count mismatch")
            return renderFile.absolutePath
''','''            requireParity(renderFile.length() == expectedBytes,
                "26564 true2x render derivative byte count mismatch")
            val acceptedPct = if (detailStats[0] > 0L) 100.0 * detailStats[1] / detailStats[0] else 0.0
            val clippedPct = if (detailStats[0] > 0L) 100.0 * detailStats[2] / detailStats[0] else 0.0
            val disagreementPct = if (detailStats[0] > 0L) 100.0 * detailStats[3] / detailStats[0] else 0.0
            PLog.i(TAG, "IRIS_26567_TRUE2X_DETAIL_ACCEPTANCE acceptedPct=$acceptedPct " +
                "clippingRejectedPct=$clippedPct disagreementRejectedPct=$disagreementPct " +
                "sabreRgbChromaOwner=true scalarDetail=true")
            return renderFile.absolutePath
''',1)
write(rel,s)

# Java native signature for guided detail tile.
rel='app/src/main/java/com/particlesdevs/photoncamera/processing/IrisTrue2xSrNative.java'
s=read(rel)
s=s.replace('''     * Build one bounded RGBA16F render tile from the pristine direct-CFA true2x carrier plus the
     * native Sabre/VGN low-frequency chroma guide. The source file is never modified, preserving
     * the pre-VGN LinearRaw DNG boundary.
''','''     * Build one bounded RGBA16F render tile whose RGB/chroma/highlight authority is exclusively
     * the native Sabre/VGN guide. Direct-CFA true2x contributes only a phase/support-gated scalar
     * luminance-detail factor applied equally to R/G/B. The pristine DNG source is never modified.
''',1)
s=s.replace('''            String nativeVgnRgb16fPath, int nativeWidth, int nativeHeight,
            int regionX, int regionY, int regionWidth, int regionHeight,
            ByteBuffer outputRgba16f);
''','''            String nativeVgnRgb16fPath, int nativeWidth, int nativeHeight,
            String phaseSupportPath, int regionX, int regionY, int regionWidth, int regionHeight,
            ByteBuffer outputRgba16f, long[] detailStats);
''',1)
write(rel,s)
# CPU true2x fallback phase eligibility mirrors the GPU source-CFA clip gate.
rel='app/src/main/java/com/particlesdevs/photoncamera/processing/IrisTrue2xSrNative.java'
rep(rel,
'''            float[] covarianceRangeRg,
            float[] covarianceRangeB,
            boolean useFrameWeight);
''',
'''            float[] covarianceRangeRg,
            float[] covarianceRangeB,
            boolean useFrameWeight, float rawClipThreshold);
''')

# -----------------------------------------------------------------------------
# Native: P3 publication + Sabre-guided scalar SR detail + P3-safe Jin boundary.
# -----------------------------------------------------------------------------
rel='app/src/main/cpp/motionv2_jpeg444_jni.cpp'
s=read(rel)
# CPU fallback phase-support clipping reliability; RGB accumulation itself is unchanged.
s=s.replace('jfloatArray gainsArray,jfloatArray blackArray,jfloatArray covRgArray,jfloatArray covBArray,jboolean useWeight){',
'''jfloatArray gainsArray,jfloatArray blackArray,jfloatArray covRgArray,jfloatArray covBArray,jboolean useWeight,jfloat rawClipThreshold){''',1)
s=s.replace('''float color[3],weights[3];iris26564::sampleRbf(raw,rawW,rawH,rawRowStrideSamples,rawX,rawY,fullRawW,fullRawH,su*(float)fullRawW,sv*(float)fullRawH,cfa,gains,black,c,color,weights);float fw=useWeight==JNI_TRUE?iris26564::rejectionSample(rej,rejW,rejH,rejX,rejY,rejFullW,rejFullH,refU,refV):1.f;''',
'''float color[3],weights[3];iris26564::sampleRbf(raw,rawW,rawH,rawRowStrideSamples,rawX,rawY,fullRawW,fullRawH,su*(float)fullRawW,sv*(float)fullRawH,cfa,gains,black,c,color,weights);float fw=useWeight==JNI_TRUE?iris26564::rejectionSample(rej,rejW,rejH,rejX,rejY,rejFullW,rejFullH,refU,refV):1.f;
        int centerX=iris26564::clampi((int)floorf(su*(float)fullRawW),0,fullRawW-1),centerY=iris26564::clampi((int)floorf(sv*(float)fullRawH),0,fullRawH-1);float sourceRawPeak=0.f;for(int ry=-1;ry<=1;ry++)for(int rx=-1;rx<=1;rx++){int xx=iris26564::clampi(centerX+rx,0,fullRawW-1),yy=iris26564::clampi(centerY+ry,0,fullRawH-1);int localX=iris26564::clampi(xx-rawX,0,rawW-1),localY=iris26564::clampi(yy-rawY,0,rawH-1);sourceRawPeak=std::max(sourceRawPeak,(float)raw[(size_t)localY*rawRowStrideSamples+localX]);}''',1)
s=s.replace('''if(fw>0.08f){float fx=fv.x*(float)fullRawW,fy=fv.y*(float)fullRawH;''',
'''if(fw>0.08f&&std::isfinite(rawClipThreshold)&&sourceRawPeak<rawClipThreshold){float fx=fv.x*(float)fullRawW,fy=fv.y*(float)fullRawH;''',1)
# conditional bitmap publication conversion
s=s.replace('''bool encodeRgbaBitmapP3(const char*path,const AndroidBitmapInfo&i,const uint8_t*p,int quality){
''','''bool encodeRgbaBitmapP3(const char*path,const AndroidBitmapInfo&i,const uint8_t*p,int quality,bool sourceDisplayP3){
''',1)
s=s.replace('''    while(ok&&c.next_scanline<c.image_height){const uint8_t*src=p+(size_t)c.next_scanline*i.stride;for(size_t x=0;x<i.width;x++)lut.convert(src[x*4],src[x*4+1],src[x*4+2],&row[x*3]);JSAMPROW rp=row.data();ok=jpeg_write_scanlines(&c,&rp,1)==1;}
''','''    while(ok&&c.next_scanline<c.image_height){const uint8_t*src=p+(size_t)c.next_scanline*i.stride;for(size_t x=0;x<i.width;x++){if(sourceDisplayP3){row[x*3]=src[x*4];row[x*3+1]=src[x*4+1];row[x*3+2]=src[x*4+2];}else lut.convert(src[x*4],src[x*4+1],src[x*4+2],&row[x*3]);}JSAMPROW rp=row.data();ok=jpeg_write_scanlines(&c,&rp,1)==1;}
''',1)
s=s.replace('''extern "C" JNIEXPORT jboolean JNICALL Java_com_particlesdevs_photoncamera_processing_ultrahdr_MotionV2Jpeg444Encoder_writeNative(JNIEnv*e,jclass,jobject bitmap,jstring path,jint quality){AndroidBitmapInfo i{};if(!bitmap||!path||AndroidBitmap_getInfo(e,bitmap,&i)!=ANDROID_BITMAP_RESULT_SUCCESS||i.format!=ANDROID_BITMAP_FORMAT_RGBA_8888)return JNI_FALSE;void*p=nullptr;if(AndroidBitmap_lockPixels(e,bitmap,&p)!=ANDROID_BITMAP_RESULT_SUCCESS||!p)return JNI_FALSE;U u(e,path);bool ok=u.c&&encodeRgbaBitmapP3(u.c,i,(const uint8_t*)p,(int)quality);AndroidBitmap_unlockPixels(e,bitmap);return ok?JNI_TRUE:JNI_FALSE;}
''','''extern "C" JNIEXPORT jboolean JNICALL Java_com_particlesdevs_photoncamera_processing_ultrahdr_MotionV2Jpeg444Encoder_writeNative(JNIEnv*e,jclass,jobject bitmap,jstring path,jint quality,jboolean sourceDisplayP3){AndroidBitmapInfo i{};if(!bitmap||!path||AndroidBitmap_getInfo(e,bitmap,&i)!=ANDROID_BITMAP_RESULT_SUCCESS||i.format!=ANDROID_BITMAP_FORMAT_RGBA_8888)return JNI_FALSE;void*p=nullptr;if(AndroidBitmap_lockPixels(e,bitmap,&p)!=ANDROID_BITMAP_RESULT_SUCCESS||!p)return JNI_FALSE;U u(e,path);bool ok=u.c&&encodeRgbaBitmapP3(u.c,i,(const uint8_t*)p,(int)quality,sourceDisplayP3==JNI_TRUE);AndroidBitmap_unlockPixels(e,bitmap);return ok?JNI_TRUE:JNI_FALSE;}
''',1)
# Replace prepare VGN function whole block.
pattern=r'''/\* IRIS_26564_TRUE2X_BOUNDED_VGN_RENDER_TILE.*?\nextern "C" JNIEXPORT jboolean JNICALL Java_com_particlesdevs_photoncamera_processing_IrisTrue2xSrNative_writeRenderTileInterior'''
replacement=r'''/* IRIS_26567_SABRE_GUIDED_CHROMA_NEUTRAL_TRUE2X
 * Native Sabre Resolve + VGN is the sole RGB/chroma/highlight owner. The direct-CFA true2x file is
 * read only to estimate a bounded high-frequency luminance ratio. Per-pixel accepted phase support,
 * shadows, highlights, low-frequency guide agreement and chroma disagreement gate that scalar.
 * Unsafe support produces factor 1.0 exactly, so no SR stage can invent an RGB ratio.
 */
extern "C" JNIEXPORT jboolean JNICALL Java_com_particlesdevs_photoncamera_processing_IrisTrue2xSrNative_prepareVgnGuidedRenderTile(
        JNIEnv*e,jclass,jstring truePath,jint trueW,jint trueH,jstring guidePath,jint guideW,jint guideH,
        jstring phasePath,jint regionX,jint regionY,jint regionW,jint regionH,jobject outputBuffer,jlongArray detailStats){
    if(!truePath||!guidePath||!phasePath||!outputBuffer||!detailStats||e->GetArrayLength(detailStats)<4||
       trueW<=1||trueH<=1||guideW<=0||guideH<=0||trueW!=guideW*2||trueH!=guideH*2||
       regionX<0||regionY<0||regionW<=0||regionH<=0||regionX>trueW-regionW||regionY>trueH-regionH)return JNI_FALSE;
    auto*out=(uint16_t*)e->GetDirectBufferAddress(outputBuffer);jlong cap=e->GetDirectBufferCapacity(outputBuffer);
    const jlong required=(jlong)regionW*regionH*4*(jlong)sizeof(uint16_t);if(!out||cap<required)return JNI_FALSE;
    U tp(e,truePath),gp(e,guidePath),pp(e,phasePath);if(!tp.c||!gp.c||!pp.c)return JNI_FALSE;
    int tfd=open(tp.c,O_RDONLY),gfd=open(gp.c,O_RDONLY),pfd=open(pp.c,O_RDONLY);
    if(tfd<0||gfd<0||pfd<0){if(tfd>=0)close(tfd);if(gfd>=0)close(gfd);if(pfd>=0)close(pfd);return JNI_FALSE;}
    struct stat ts{},gs{},ps{};const uint64_t tBytes=(uint64_t)trueW*(uint64_t)trueH*6ull,
        gBytes=(uint64_t)guideW*(uint64_t)guideH*6ull,pBytes=(uint64_t)trueW*(uint64_t)trueH;
    if(fstat(tfd,&ts)!=0||fstat(gfd,&gs)!=0||fstat(pfd,&ps)!=0||(uint64_t)ts.st_size!=tBytes||
       (uint64_t)gs.st_size!=gBytes||(uint64_t)ps.st_size!=pBytes){close(tfd);close(gfd);close(pfd);return JNI_FALSE;}
    auto readExact=[](int fd,void*dst,size_t bytes,off_t offset)->bool{auto*p=(uint8_t*)dst;size_t done=0;while(done<bytes){ssize_t n=pread(fd,p+done,bytes-done,offset+(off_t)done);if(n<=0)return false;done+=(size_t)n;}return true;};
    const int ex0=std::max(0,regionX-2),ey0=std::max(0,regionY-2),ex1=std::min((int)trueW,regionX+regionW+2),ey1=std::min((int)trueH,regionY+regionH+2);
    const int ew=ex1-ex0,eh=ey1-ey0;std::vector<uint16_t>direct((size_t)ew*eh*3);std::vector<uint8_t>support((size_t)regionW*regionH);
    for(int y=0;y<eh;y++)if(!readExact(tfd,direct.data()+(size_t)y*ew*3,(size_t)ew*6,((off_t)(ey0+y)*trueW+ex0)*6)){close(tfd);close(gfd);close(pfd);return JNI_FALSE;}
    for(int y=0;y<regionH;y++)if(!readExact(pfd,support.data()+(size_t)y*regionW,(size_t)regionW,(off_t)(regionY+y)*trueW+regionX)){close(tfd);close(gfd);close(pfd);return JNI_FALSE;}
    const int gx0=std::max(0,(regionX/2)-2),gy0=std::max(0,(regionY/2)-2),gx1=std::min((int)guideW,(regionX+regionW+1)/2+2),gy1=std::min((int)guideH,(regionY+regionH+1)/2+2);
    const int gw=gx1-gx0,gh=gy1-gy0;std::vector<uint16_t>guide((size_t)gw*gh*3);
    for(int y=0;y<gh;y++)if(!readExact(gfd,guide.data()+(size_t)y*gw*3,(size_t)gw*6,((off_t)(gy0+y)*guideW+gx0)*6)){close(tfd);close(gfd);close(pfd);return JNI_FALSE;}
    auto dAt=[&](int x,int y)->std::array<float,3>{x=iris26564::clampi(x,0,trueW-1);y=iris26564::clampi(y,0,trueH-1);size_t q=((size_t)(y-ey0)*ew+(x-ex0))*3;return {iris26564::halfToFloat(direct[q]),iris26564::halfToFloat(direct[q+1]),iris26564::halfToFloat(direct[q+2])};};
    auto gAt=[&](int x,int y)->std::array<float,3>{x=iris26564::clampi(x,0,guideW-1);y=iris26564::clampi(y,0,guideH-1);size_t q=((size_t)(y-gy0)*gw+(x-gx0))*3;return {iris26564::halfToFloat(guide[q]),iris26564::halfToFloat(guide[q+1]),iris26564::halfToFloat(guide[q+2])};};
    auto lum=[](const std::array<float,3>&v){return 0.25f*v[0]+0.50f*v[1]+0.25f*v[2];};
    auto peak3=[](const std::array<float,3>&v){return std::max(v[0],std::max(v[1],v[2]));};
    auto chroma=[&](const std::array<float,3>&v){float sum=std::max(v[0]+v[1]+v[2],1.0e-5f);return std::array<float,3>{v[0]/sum,v[1]/sum,v[2]/sum};};
    auto bilGuide=[&](int ox,int oy){float sx=clampf(((float)ox+0.5f)*0.5f-0.5f,0.f,(float)(guideW-1)),sy=clampf(((float)oy+0.5f)*0.5f-0.5f,0.f,(float)(guideH-1));int x0=(int)floorf(sx),y0=(int)floorf(sy),x1=std::min(x0+1,guideW-1),y1=std::min(y0+1,guideH-1);float fx=sx-x0,fy=sy-y0;auto a=gAt(x0,y0),b=gAt(x1,y0),c=gAt(x0,y1),d=gAt(x1,y1);std::array<float,3>o{};for(int k=0;k<3;k++)o[k]=(a[k]+(b[k]-a[k])*fx)*(1.f-fy)+(c[k]+(d[k]-c[k])*fx)*fy;return o;};
    jlong stats[4]={0,0,0,0};bool ok=true;
    for(int ly=0;ok&&ly<regionH;ly++)for(int lx=0;lx<regionW;lx++){
        int ox=regionX+lx,oy=regionY+ly;auto directRgb=dAt(ox,oy),guideRgb=bilGuide(ox,oy);for(int k=0;k<3;k++)if(!std::isfinite(directRgb[k])||!std::isfinite(guideRgb[k])){ok=false;break;}if(!ok)break;
        int bx=(ox/2)*2,by=(oy/2)*2;auto b00=dAt(bx,by),b10=dAt(std::min(bx+1,(int)trueW-1),by),b01=dAt(bx,std::min(by+1,(int)trueH-1)),b11=dAt(std::min(bx+1,(int)trueW-1),std::min(by+1,(int)trueH-1));
        float directY=std::max(lum(directRgb),0.f),lowY=std::max(0.25f*(lum(b00)+lum(b10)+lum(b01)+lum(b11)),0.f),guideY=std::max(lum(guideRgb),0.f);
        int phaseCount=std::min(4,(int)support[(size_t)ly*regionW+lx]);float phaseGate=phaseCount>=4?1.f:(phaseCount==3?0.68f:(phaseCount==2?0.32f:0.f));
        float signalGate=iris26564::smooth01((guideY-0.020f)/0.080f);float directPeak=peak3(directRgb),guidePeak=peak3(guideRgb);float highlightGate=1.f-iris26564::smooth01((std::max(directPeak,guidePeak)-0.72f)/0.20f);
        auto dc=chroma(directRgb),gc=chroma(guideRgb);float cd=std::sqrt((dc[0]-gc[0])*(dc[0]-gc[0])+(dc[1]-gc[1])*(dc[1]-gc[1])+(dc[2]-gc[2])*(dc[2]-gc[2]));float chromaGate=1.f-iris26564::smooth01((cd-0.015f)/0.055f);
        float agreement=std::fabs(std::log2((lowY+0.01f)/(guideY+0.01f)));float agreementGate=1.f-iris26564::smooth01((agreement-0.08f)/0.27f);
        float confidence=clampf(phaseGate*signalGate*highlightGate*chromaGate*agreementGate,0.f,1.f);float rawLog=std::log2((directY+0.004f)/(lowY+0.004f));rawLog=clampf(rawLog,-0.25f,0.25f);float factor=std::exp2(rawLog*confidence);
        size_t dst=((size_t)ly*regionW+lx)*4;for(int k=0;k<3;k++)out[dst+k]=iris26564::floatToHalf(std::max(guideRgb[k]*factor,0.f));out[dst+3]=iris26564::floatToHalf(1.f);
        stats[0]++;if(confidence>0.02f)stats[1]++;if(highlightGate<=0.001f)stats[2]++;if(chromaGate<=0.001f||agreementGate<=0.001f)stats[3]++;
    }
    close(tfd);close(gfd);close(pfd);if(ok){jlong previous[4];e->GetLongArrayRegion(detailStats,0,4,previous);if(e->ExceptionCheck())return JNI_FALSE;for(int k=0;k<4;k++)previous[k]+=stats[k];e->SetLongArrayRegion(detailStats,0,4,previous);if(e->ExceptionCheck())return JNI_FALSE;}return ok?JNI_TRUE:JNI_FALSE;
}

extern "C" JNIEXPORT jboolean JNICALL Java_com_particlesdevs_photoncamera_processing_IrisTrue2xSrNative_writeRenderTileInterior'''
out,n=re.subn(pattern,replacement,s,count=1,flags=re.S)
if n!=1: raise SystemExit(f'native prepare replace {n}')
s=out
# P3 luma and names in true2x renderer; remove final P3 conversion.
s=s.replace('inline float luma(Vec3 c){return 0.2126f*c.r+0.7152f*c.g+0.0722f*c.b;}',
'''inline float luma(Vec3 c){return 0.22897456f*c.r+0.69173852f*c.g+0.07928691f*c.b;}''',1)
s=s.replace('float profileToSrgb[9]{};','float profileToDisplay[9]{};',1)
s=s.replace('Vec3 profile=mat(p.sensorToProfile,camera);Vec3 linear=mat(p.profileToSrgb,profile);',
'''Vec3 profile=mat(p.sensorToProfile,camera);Vec3 linear=mat(p.profileToDisplay,profile);''',1)
s=s.replace('''inline bool renderTile(int sourceFd,int outFd,int gainFd,float gainMax,const Params&p,const Watermark&w,const Jin&j,const SrgbLut&lut,int outW,int outH,int left,int top,int coreW,int coreH){
    int extW=coreW+(left+coreW<outW?1:0),extH=coreH+(top+coreH<outH?1:0);SourceRegion src;if(!readRegion(sourceFd,p,left,top,left+extW-1,top+extH-1,&src))return false;std::vector<uint8_t>base((size_t)extW*extH*3),row((size_t)coreW*3),gainBase,gainRow;const auto&p3=displayP3Lut();if(gainFd>=0){gainBase.resize((size_t)extW*extH);gainRow.resize((size_t)coreW);}
''','''inline bool renderTile(int sourceFd,int outFd,int gainFd,float gainMax,const Params&p,const Watermark&w,const Jin&j,const SrgbLut&lut,int outW,int outH,int left,int top,int coreW,int coreH){
    int extW=coreW+(left+coreW<outW?1:0),extH=coreH+(top+coreH<outH?1:0);SourceRegion src;if(!readRegion(sourceFd,p,left,top,left+extW-1,top+extH-1,&src))return false;std::vector<uint8_t>base((size_t)extW*extH*3),row((size_t)coreW*3),gainBase,gainRow;if(gainFd>=0){gainBase.resize((size_t)extW*extH);gainRow.resize((size_t)coreW);}
''',1)
s=s.replace('''applyJinPixel(j,c,r,d,left+x,top+y,outW,outH,&row[(size_t)x*3]);p3.convertInPlace(&row[(size_t)x*3]);if(gainFd>=0)''','''applyJinPixel(j,c,r,d,left+x,top+y,outW,outH,&row[(size_t)x*3]);if(gainFd>=0)''',1)
old='auto yl=[](const uint8_t*q){return (0.2126f*q[0]+0.7152f*q[1]+0.0722f*q[2])/255.f;};'
new='auto yl=[](const uint8_t*q){return (0.22897456f*q[0]+0.69173852f*q[1]+0.07928691f*q[2])/255.f;};'
if s.count(old)!=1: raise SystemExit(f'true2x P3 Jin luma anchor count {s.count(old)}')
s=s.replace(old,new,1)
# true2x JNI parameter name and matrix field.
s=s.replace('jfloatArray sensorToProfile,jfloatArray profileToSrgb,jfloat displayGain',
'''jfloatArray sensorToProfile,jfloatArray profileToDisplay,jfloat displayGain''',1)
old='if(!sensorToProfile||!profileToSrgb||e->GetArrayLength(sensorToProfile)!=9||e->GetArrayLength(profileToSrgb)!=9)return JNI_FALSE;e->GetFloatArrayRegion(sensorToProfile,0,9,p.sensorToProfile);e->GetFloatArrayRegion(profileToSrgb,0,9,p.profileToSrgb);if(e->ExceptionCheck())return JNI_FALSE;for(float v:p.sensorToProfile)if(!std::isfinite(v))return JNI_FALSE;for(float v:p.profileToSrgb)if(!std::isfinite(v))return JNI_FALSE;'
new='if(!sensorToProfile||!profileToDisplay||e->GetArrayLength(sensorToProfile)!=9||e->GetArrayLength(profileToDisplay)!=9)return JNI_FALSE;e->GetFloatArrayRegion(sensorToProfile,0,9,p.sensorToProfile);e->GetFloatArrayRegion(profileToDisplay,0,9,p.profileToDisplay);if(e->ExceptionCheck())return JNI_FALSE;for(float v:p.sensorToProfile)if(!std::isfinite(v))return JNI_FALSE;for(float v:p.profileToDisplay)if(!std::isfinite(v))return JNI_FALSE;'
if s.count(old)!=1: raise SystemExit(f'native true2x stale profile initializer count {s.count(old)}')
s=s.replace(old,new,1)
# Watermark bitmap is encoded sRGB; true2x base is now encoded Display-P3 at blend time.
s=s.replace('''inline Vec3 sampleWatermark(const Watermark&w,float u,float v){
    if(!w.enabled())return {0.f,0.f,0.f};u=clampf(u,0.f,1.f);v=clampf(v,0.f,1.f);float x=u*(float)w.w-0.5f,y=v*(float)w.h-0.5f;x=clampf(x,0.f,(float)(w.w-1));y=clampf(y,0.f,(float)(w.h-1));int x0=(int)floorf(x),y0=(int)floorf(y),x1=std::min(x0+1,w.w-1),y1=std::min(y0+1,w.h-1);float fx=x-x0,fy=y-y0;auto p=[&](int xx,int yy,int c){return (float)w.rgba[((size_t)yy*w.w+xx)*4+c]/255.f;};Vec3 a{},b{};for(int c=0;c<3;c++){float r0=p(x0,y0,c)+(p(x1,y0,c)-p(x0,y0,c))*fx,r1=p(x0,y1,c)+(p(x1,y1,c)-p(x0,y1,c))*fx;float z=r0+(r1-r0)*fy;if(c==0)a.r=z;else if(c==1)a.g=z;else a.b=z;}return a;
}
''','''inline Vec3 sampleWatermark(const Watermark&w,float u,float v){
    if(!w.enabled())return {0.f,0.f,0.f};u=clampf(u,0.f,1.f);v=clampf(v,0.f,1.f);float x=u*(float)w.w-0.5f,y=v*(float)w.h-0.5f;x=clampf(x,0.f,(float)(w.w-1));y=clampf(y,0.f,(float)(w.h-1));int x0=(int)floorf(x),y0=(int)floorf(y),x1=std::min(x0+1,w.w-1),y1=std::min(y0+1,w.h-1);float fx=x-x0,fy=y-y0;auto p=[&](int xx,int yy,int c){return (float)w.rgba[((size_t)yy*w.w+xx)*4+c]/255.f;};Vec3 a{},b{};for(int c=0;c<3;c++){float r0=p(x0,y0,c)+(p(x1,y0,c)-p(x0,y0,c))*fx,r1=p(x0,y1,c)+(p(x1,y1,c)-p(x0,y1,c))*fx;float z=r0+(r1-r0)*fy;if(c==0)a.r=z;else if(c==1)a.g=z;else a.b=z;}auto p3=displayP3Lut().convertEncoded(a.r,a.g,a.b);return {p3[0],p3[1],p3[2]};
}
''',1)
# Jin P3 conversion helpers + true2x initialization arrays.
# Add float encoded conversion method to DisplayP3Lut.
s=s.replace('''    void convertInPlace(uint8_t*rgb)const{uint8_t o[3];convert(rgb[0],rgb[1],rgb[2],o);rgb[0]=o[0];rgb[1]=o[1];rgb[2]=o[2];}
''','''    void convertInPlace(uint8_t*rgb)const{uint8_t o[3];convert(rgb[0],rgb[1],rgb[2],o);rgb[0]=o[0];rgb[1]=o[1];rgb[2]=o[2];}
    std::array<float,3> convertEncoded(float r,float g,float b)const{
        auto dec=[](float x){x=std::max(0.f,std::min(1.f,x));return x<=0.04045f?x/12.92f:std::pow((x+0.055f)/1.055f,2.4f);};
        float lr=dec(r),lg=dec(g),lb=dec(b);return {enc(0.8224619687f*lr+0.1775380313f*lg),enc(0.0331941989f*lr+0.9668058011f*lg),enc(0.0170826307f*lr+0.0723974407f*lg+0.9105199286f*lb)};
    }
''',1)
# Jin struct add p3 guide and convert residual once after load.
s=s.replace('''    std::vector<jint> guide;
    bool enabled()const{return w>1&&h>1&&residual.size()==(size_t)w*h*3&&guide.size()==(size_t)w*h;}
''','''    std::vector<jint> guide;
    std::vector<float> guideP3;
    bool enabled()const{return w>1&&h>1&&residual.size()==(size_t)w*h*3&&guide.size()==(size_t)w*h&&guideP3.size()==(size_t)w*h*3;}
''',1)
s=s.replace('''inline float guideRgb(const Jin&j,int x,int y,int c){jint argb=j.guide[(size_t)y*j.w+x];int shift=c==0?16:(c==1?8:0);return (float)((argb>>shift)&255)/255.f;}
''','''inline float guideRgb(const Jin&j,int x,int y,int c){return j.guideP3[((size_t)y*j.w+x)*3+c];}
''',1)
old='''jin.w=jinW;jin.h=jinH;jin.residual.resize((size_t)jinW*jinH*3);jin.guide.resize((size_t)jinW*jinH);e->GetFloatArrayRegion(jinResidual,0,(jsize)jin.residual.size(),jin.residual.data());e->GetIntArrayRegion(jinReference,0,(jsize)jin.guide.size(),jin.guide.data());if(e->ExceptionCheck()){close(sourceFd);return JNI_FALSE;}for(float v:jin.residual)if(!std::isfinite(v)){close(sourceFd);return JNI_FALSE;}}
'''
new='''jin.w=jinW;jin.h=jinH;jin.residual.resize((size_t)jinW*jinH*3);jin.guide.resize((size_t)jinW*jinH);e->GetFloatArrayRegion(jinResidual,0,(jsize)jin.residual.size(),jin.residual.data());e->GetIntArrayRegion(jinReference,0,(jsize)jin.guide.size(),jin.guide.data());if(e->ExceptionCheck()){close(sourceFd);return JNI_FALSE;}for(float v:jin.residual)if(!std::isfinite(v)){close(sourceFd);return JNI_FALSE;}const auto&p3=displayP3Lut();jin.guideP3.resize((size_t)jinW*jinH*3);for(int i=0;i<jinW*jinH;i++){jint argb=jin.guide[(size_t)i];float sr=(float)((argb>>16)&255)/255.f,sg=(float)((argb>>8)&255)/255.f,sb=(float)(argb&255)/255.f;auto baseP3=p3.convertEncoded(sr,sg,sb);auto outP3=p3.convertEncoded(clampf(sr+jin.residual[(size_t)i*3],0.f,1.f),clampf(sg+jin.residual[(size_t)i*3+1],0.f,1.f),clampf(sb+jin.residual[(size_t)i*3+2],0.f,1.f));for(int c=0;c<3;c++){jin.guideP3[(size_t)i*3+c]=baseP3[(size_t)c];jin.residual[(size_t)i*3+c]=outP3[(size_t)c]-baseP3[(size_t)c];}}}
'''
if s.count(old)!=1: raise SystemExit('Jin init anchor')
s=s.replace(old,new,1)
# Non-SR Jin residual native gets baseDisplayP3 and converts reference/residual arrays once.
s=s.replace('''        JNIEnv*e,jclass,jobject bitmap,jfloatArray residual,jintArray referenceRgb,jint rw,jint rh){
''','''        JNIEnv*e,jclass,jobject bitmap,jfloatArray residual,jintArray referenceRgb,jint rw,jint rh,jboolean baseDisplayP3){
''',1)
# After finite check, convert arrays if P3.
s=s.replace('''    for(float v:r)if(!std::isfinite(v))return JNI_FALSE;

    auto guideRgb=[&](int x,int y,int c)->float{
''','''    for(float v:r)if(!std::isfinite(v))return JNI_FALSE;
    std::vector<float> guideP3;
    if(baseDisplayP3==JNI_TRUE){const auto&p3=displayP3Lut();guideP3.resize((size_t)rw*rh*3);for(int i=0;i<rw*rh;i++){jint argb=guide[(size_t)i];float sr=(float)((argb>>16)&255)/255.f,sg=(float)((argb>>8)&255)/255.f,sb=(float)(argb&255)/255.f;auto bp=p3.convertEncoded(sr,sg,sb);auto op=p3.convertEncoded(clampf(sr+r[(size_t)i*3],0.f,1.f),clampf(sg+r[(size_t)i*3+1],0.f,1.f),clampf(sb+r[(size_t)i*3+2],0.f,1.f));for(int c=0;c<3;c++){guideP3[(size_t)i*3+c]=bp[(size_t)c];r[(size_t)i*3+c]=op[(size_t)c]-bp[(size_t)c];}}}

    auto guideRgb=[&](int x,int y,int c)->float{
        if(baseDisplayP3==JNI_TRUE)return guideP3[((size_t)y*rw+x)*3+c];
''',1)
# P3 luma for non-SR native if base p3.
s=s.replace('''    auto luma=[](const uint8_t*q)->float{
        return (0.2126f*(float)q[0]+0.7152f*(float)q[1]+0.0722f*(float)q[2])/255.f;
    };
''','''    auto luma=[&](const uint8_t*q)->float{
        if(baseDisplayP3==JNI_TRUE)return (0.22897456f*(float)q[0]+0.69173852f*(float)q[1]+0.07928691f*(float)q[2])/255.f;
        return (0.2126f*(float)q[0]+0.7152f*(float)q[1]+0.0722f*(float)q[2])/255.f;
    };
''',1)
write(rel,s)

print('PASS transform_26567_v1')
