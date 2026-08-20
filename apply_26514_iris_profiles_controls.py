#!/usr/bin/env python3
from __future__ import annotations
import argparse, difflib, hashlib
from pathlib import Path

CHANGED = {
    'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNoiseProfileStore.kt',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/IrisMotionToneControls.java',
    'app/src/main/assets/shaders/motionv2/iris_tone_controls.glsl',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/IsoExpoSelector.java',
    'app/src/main/java/com/particlesdevs/photoncamera/ui/settings/SettingsActivity.java',
    'app/src/main/java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java',
    'app/src/main/res/xml/preferences.xml',
    'app/src/main/res/values/strings.xml',
    'app/src/main/res/values/default_prefs.xml',
}

NEW_FILES = {
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java': r'''package com.particlesdevs.photoncamera.processing.processor;

import com.particlesdevs.photoncamera.app.PhotonCamera;
import com.particlesdevs.photoncamera.settings.PreferenceKeys;
import com.particlesdevs.photoncamera.settings.SettingsManager;

import java.util.Locale;

/**
 * IRIS_26514_MOTION_USER_CONTROLS_OWNER
 * One per-lens settings boundary for the stable Motion/MGC runtime. Values are snapped to
 * exact tenths before use so UI drag and manual-entry paths cannot diverge.
 */
public final class IrisMotionSettings {
    public static final String KEY_CUSTOM_NOISE_MODEL = "pref_iris_custom_noise_model";
    public static final String KEY_IMPORT_NOISE_MODEL = "pref_iris_import_noise_model";
    public static final String KEY_PROFILE_ID = "pref_iris_custom_noise_profile_id";
    public static final String KEY_PROFILE_NAME = "pref_iris_custom_noise_profile_name";
    public static final String KEY_LUMA_DENOISE = "pref_iris_luma_denoise";
    public static final String KEY_CHROMA_DENOISE = "pref_iris_chroma_denoise";
    public static final String KEY_EXPOSURE_EV = "pref_iris_exposure_ev";
    public static final String KEY_SHADOWS = "pref_iris_shadows";
    public static final String KEY_CONTRAST = "pref_iris_contrast";

    private IrisMotionSettings() {}

    public static final class Snapshot {
        public final boolean noiseReductionEnabled;
        public final boolean customNoiseModelEnabled;
        public final String profileId;
        public final String profileDisplayName;
        public final float lumaDenoise;
        public final float chromaDenoise;
        public final float exposureEv;
        public final float shadows;
        public final float contrast;

        Snapshot(boolean noiseReductionEnabled,
                 boolean customNoiseModelEnabled,
                 String profileId,
                 String profileDisplayName,
                 float lumaDenoise,
                 float chromaDenoise,
                 float exposureEv,
                 float shadows,
                 float contrast) {
            this.noiseReductionEnabled = noiseReductionEnabled;
            this.customNoiseModelEnabled = customNoiseModelEnabled;
            this.profileId = profileId == null ? "" : profileId;
            this.profileDisplayName = profileDisplayName == null ? "" : profileDisplayName;
            this.lumaDenoise = lumaDenoise;
            this.chromaDenoise = chromaDenoise;
            this.exposureEv = exposureEv;
            this.shadows = shadows;
            this.contrast = contrast;
        }

        public boolean hasToneAdjustment() {
            return Math.abs(exposureEv) >= 0.05f || Math.abs(shadows) >= 0.05f ||
                    Math.abs(contrast) >= 0.05f;
        }
    }

    public static Snapshot current() {
        SettingsManager sm = PhotonCamera.getSettingsManagerStatic();
        if (sm == null) {
            return new Snapshot(true, false, "", "", 1.0f, 1.0f, 0.0f, 0.0f, 0.0f);
        }
        boolean nr = PreferenceKeys.isHdrxNrOn();
        boolean custom = getBoolean(sm, KEY_CUSTOM_NOISE_MODEL, false);
        String id = getString(sm, KEY_PROFILE_ID, "");
        String name = getString(sm, KEY_PROFILE_NAME, "");
        float luma = snap01(getFloat(sm, KEY_LUMA_DENOISE, 1.0f), 0.0f, 2.0f);
        float chroma = snap01(getFloat(sm, KEY_CHROMA_DENOISE, 1.0f), 0.0f, 2.0f);
        float exposure = snap01(getFloat(sm, KEY_EXPOSURE_EV, 0.0f), -1.0f, 1.0f);
        float shadows = snap01(getFloat(sm, KEY_SHADOWS, 0.0f), -1.0f, 1.0f);
        float contrast = snap01(getFloat(sm, KEY_CONTRAST, 0.0f), -1.0f, 1.0f);
        return new Snapshot(nr, custom, id, name, luma, chroma, exposure, shadows, contrast);
    }

    public static float snap01(float value, float min, float max) {
        if (!Float.isFinite(value)) value = 0.0f;
        float clamped = Math.max(min, Math.min(max, value));
        return Math.round(clamped * 10.0f) / 10.0f;
    }

    public static boolean isQuantizedSliderKey(String key) {
        return KEY_LUMA_DENOISE.equals(key) || KEY_CHROMA_DENOISE.equals(key) ||
                KEY_EXPOSURE_EV.equals(key) || KEY_SHADOWS.equals(key) ||
                KEY_CONTRAST.equals(key);
    }

    public static void normalizePersistedSlider(String key) {
        if (!isQuantizedSliderKey(key)) return;
        SettingsManager sm = PhotonCamera.getSettingsManagerStatic();
        if (sm == null) return;
        float min = (KEY_LUMA_DENOISE.equals(key) || KEY_CHROMA_DENOISE.equals(key)) ? 0.0f : -1.0f;
        float max = (KEY_LUMA_DENOISE.equals(key) || KEY_CHROMA_DENOISE.equals(key)) ? 2.0f : 1.0f;
        float def = (KEY_LUMA_DENOISE.equals(key) || KEY_CHROMA_DENOISE.equals(key)) ? 1.0f : 0.0f;
        float snapped = snap01(getFloat(sm, key, def), min, max);
        String normalized = String.format(Locale.ROOT, "%.1f", snapped);
        String current = getString(sm, key, String.format(Locale.ROOT, "%.1f", def));
        if (!normalized.equals(current)) sm.set(SettingsManager.SCOPE_GLOBAL, key, normalized);
    }

    public static void setImportedProfile(String id, String displayName) {
        SettingsManager sm = PhotonCamera.getSettingsManagerStatic();
        if (sm == null) throw new IllegalStateException("Iris settings manager unavailable");
        sm.set(SettingsManager.SCOPE_GLOBAL, KEY_PROFILE_ID, id == null ? "" : id);
        sm.set(SettingsManager.SCOPE_GLOBAL, KEY_PROFILE_NAME, displayName == null ? "" : displayName);
        sm.set(SettingsManager.SCOPE_GLOBAL, KEY_CUSTOM_NOISE_MODEL, true);
    }

    private static float getFloat(SettingsManager sm, String key, float def) {
        try {
            String value = sm.getString(
                    SettingsManager.SCOPE_GLOBAL, key, Float.toString(def));
            return Float.parseFloat(value);
        } catch (Throwable ignored) {
            return def;
        }
    }

    private static boolean getBoolean(SettingsManager sm, String key, boolean def) {
        try { return sm.getBoolean(SettingsManager.SCOPE_GLOBAL, key, def); }
        catch (Throwable ignored) { return def; }
    }

    private static String getString(SettingsManager sm, String key, String def) {
        try { return sm.getString(SettingsManager.SCOPE_GLOBAL, key, def); }
        catch (Throwable ignored) { return def; }
    }
}
''',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNoiseProfileStore.kt': r'''package com.particlesdevs.photoncamera.processing.processor

import android.content.Context
import android.net.Uri
import android.provider.OpenableColumns
import com.hinnka.mycamera.processor.CalibratedRawNoiseProfile
import java.io.ByteArrayOutputStream
import java.io.File
import java.security.MessageDigest

/** IRIS_26514_PRIVATE_GCAM_C_PROFILE_STORE */
object IrisNoiseProfileStore {
    private const val MAX_BYTES = 1024 * 1024
    private const val DIR_NAME = "iris_noise_models"
    private val HEX_ID = Regex("^[0-9a-f]{64}$")

    data class ImportResult(
        val success: Boolean,
        val message: String,
        val displayName: String = "",
    )

    @JvmStatic
    fun importFromUri(context: Context, uri: Uri): ImportResult = runCatching {
        val displayName = resolveDisplayName(context, uri)
        require(displayName.lowercase().endsWith(".c")) { "Select a GCam .c noise-model file" }
        val bytes = context.contentResolver.openInputStream(uri)?.use(::readLimited)
            ?: throw IllegalArgumentException("Unable to open selected file")
        val source = String(bytes, Charsets.UTF_8)
        val id = sha256(bytes)
        // Parse before any setting/file mutation. Invalid imports leave the prior selection intact.
        CalibratedRawNoiseProfile.parseGcamC("iris-custom/$id", source)

        val dir = File(context.filesDir, DIR_NAME)
        require(dir.exists() || dir.mkdirs()) { "Unable to create Iris noise-model storage" }
        val dst = File(dir, "$id.c")
        val tmp = File(dir, ".$id.tmp")
        tmp.writeBytes(bytes)
        if (!tmp.renameTo(dst)) {
            tmp.copyTo(dst, overwrite = true)
            check(tmp.delete()) { "Unable to finalize imported profile" }
        }
        IrisMotionSettings.setImportedProfile(id, displayName)
        ImportResult(true, "Imported $displayName", displayName)
    }.getOrElse { error ->
        ImportResult(false, error.message ?: error.javaClass.simpleName)
    }

    @JvmStatic
    fun hasValidSelectedProfile(context: Context): Boolean =
        runCatching { loadSelectedProfile(context) != null }.getOrDefault(false)

    @JvmStatic
    fun loadSelectedProfile(context: Context): CalibratedRawNoiseProfile? {
        val settings = IrisMotionSettings.current()
        val id = settings.profileId
        if (!HEX_ID.matches(id)) return null
        val file = File(File(context.filesDir, DIR_NAME), "$id.c")
        if (!file.isFile || file.length() <= 0L || file.length() > MAX_BYTES.toLong()) return null
        return file.inputStream().use { input ->
            CalibratedRawNoiseProfile.parseGcamC("iris-custom/$id", input)
        }
    }

    private fun resolveDisplayName(context: Context, uri: Uri): String {
        context.contentResolver.query(
            uri,
            arrayOf(OpenableColumns.DISPLAY_NAME),
            null,
            null,
            null,
        )?.use { cursor ->
            if (cursor.moveToFirst()) {
                val index = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME)
                if (index >= 0) cursor.getString(index)?.takeIf { it.isNotBlank() }?.let { return it }
            }
        }
        return uri.lastPathSegment?.substringAfterLast('/')?.takeIf { it.isNotBlank() }
            ?: "noise_model.c"
    }

    private fun readLimited(input: java.io.InputStream): ByteArray {
        val out = ByteArrayOutputStream()
        val buffer = ByteArray(8192)
        var total = 0
        while (true) {
            val read = input.read(buffer)
            if (read < 0) break
            total += read
            require(total <= MAX_BYTES) { "Noise-model file exceeds 1 MiB" }
            out.write(buffer, 0, read)
        }
        require(total > 0) { "Noise-model file is empty" }
        return out.toByteArray()
    }

    private fun sha256(bytes: ByteArray): String =
        MessageDigest.getInstance("SHA-256").digest(bytes).joinToString("") { "%02x".format(it.toInt() and 0xff) }
}
''',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/IrisMotionToneControls.java': r'''package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
import com.particlesdevs.photoncamera.processing.processor.IrisMotionSettings;
import com.particlesdevs.photoncamera.util.Log;

/**
 * IRIS_26514_LINEAR_PRESENTATION_CONTROLS
 * Optional post-reconstruction/pre-render photographic controls. This node is never inserted at
 * neutral 0/0/0, preserving the exact 26513 render input when the new controls are untouched.
 */
public final class IrisMotionToneControls extends Node {
    private final float exposureEv;
    private final float shadows;
    private final float contrast;

    public IrisMotionToneControls(IrisMotionSettings.Snapshot settings) {
        super("", "IrisMotionToneControls");
        exposureEv = settings.exposureEv;
        shadows = settings.shadows;
        contrast = settings.contrast;
    }

    @Override public void Compile() {}

    @Override
    public void Run() {
        if (!basePipeline.mParameters.motionV2Active) {
            throw new IllegalStateException("IrisMotionToneControls used outside Motion");
        }
        glProg.useAssetProgram("motionv2/iris_tone_controls");
        glProg.setTexture("InputBuffer", previousNode.WorkingTexture);
        glProg.setVar("exposureEv", exposureEv);
        glProg.setVar("shadowsControl", shadows);
        glProg.setVar("contrastControl", contrast);
        WorkingTexture = basePipeline.getMain();
        glProg.drawBlocks(WorkingTexture);
        glProg.closed = true;
        Log.d(Name, "IRIS_26514_PRESENTATION exposureEv=" + exposureEv
                + " shadows=" + shadows + " contrast=" + contrast
                + " beforeMotionRender=true sdrUhDrCommonSource=true");
    }
}
''',
'app/src/main/assets/shaders/motionv2/iris_tone_controls.glsl': r'''precision highp float;
precision mediump sampler2D;
uniform sampler2D InputBuffer;
uniform float exposureEv;
uniform float shadowsControl;
uniform float contrastControl;
out vec3 Output;

float irisLuma(vec3 c) {
    return dot(max(c, vec3(0.0)), vec3(0.2126, 0.7152, 0.0722));
}

vec3 scaleToLuma(vec3 rgb, float sourceY, float targetY) {
    if (sourceY <= 1.0e-7) return vec3(max(targetY, 0.0));
    return max(rgb, vec3(0.0)) * (max(targetY, 0.0) / sourceY);
}

vec3 applyShadows(vec3 rgb, float amount) {
    if (abs(amount) < 0.0001) return rgb;
    float y = irisLuma(rgb);
    float mask = 1.0 - smoothstep(0.08, 0.55, y);
    float targetY = y;
    if (amount < 0.0) {
        // User convention: negative opens shadows. Maximum lift is deliberately bounded.
        targetY = y + (-amount) * 0.08 * mask * (1.0 - clamp(y, 0.0, 1.0));
    } else {
        // Positive deepens shadows while leaving mid/high tones progressively untouched.
        targetY = y * (1.0 - 0.75 * amount * mask);
    }
    return scaleToLuma(rgb, y, targetY);
}

vec3 applyContrast(vec3 rgb, float amount) {
    if (abs(amount) < 0.0001) return rgb;
    float y = irisLuma(rgb);
    if (y <= 1.0e-7) return rgb;
    const float pivot = 0.18;
    float slope = 1.0 + 0.25 * amount;
    float targetY = pivot * exp2(log2(max(y / pivot, 1.0e-6)) * slope);
    return scaleToLuma(rgb, y, targetY);
}

void main() {
    ivec2 xy = ivec2(gl_FragCoord.xy);
    vec3 rgb = max(texelFetch(InputBuffer, xy, 0).rgb, vec3(0.0));
    rgb *= exp2(exposureEv);
    rgb = applyShadows(rgb, shadowsControl);
    rgb = applyContrast(rgb, contrastControl);
    Output = max(rgb, vec3(0.0));
}
''',
}


def one(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise AssertionError(f'{label}: expected exactly one anchor, found {n}')
    return text.replace(old, new, 1)


def expected_text(rel: str, base: str) -> str:
    if rel in NEW_FILES:
        if base:
            raise AssertionError(f'{rel}: new file unexpectedly exists in 26513 base')
        return NEW_FILES[rel]

    s = base
    if rel.endswith('PhotonMotionMgc1271Bridge.kt'):
        s = one(s,
            'import com.hinnka.mycamera.processor.RawNoiseProfileSelection\n',
            'import com.hinnka.mycamera.processor.RawNoiseProfileSelection\nimport com.hinnka.mycamera.processor.RawNoiseModel\n',
            'bridge RawNoiseModel import')
        anchor = '''            orderedPhysical.forEachIndexed { index, (frame, role) ->\n                validateFrame(frame, size, role, reference.motionV2ExposureEnergy, index)\n            }\n\n            parameters.motionCanonicalExposureGain = 1.0f'''
        replacement = '''            orderedPhysical.forEachIndexed { index, (frame, role) ->\n                validateFrame(frame, size, role, reference.motionV2ExposureEnergy, index)\n            }\n\n            // IRIS_26514_STRICT_NOISE_AUTHORITY: no Camera2 base-frame, Pixel, or custom->Camera2 fallback.\n            val irisSettings = IrisMotionSettings.current()\n            val noiseSelection: RawNoiseProfileSelection\n            val noiseAuthority: String\n            if (irisSettings.customNoiseModelEnabled) {\n                val profile = IrisNoiseProfileStore.loadSelectedProfile(\n                    PhotonCamera.getApplicationContextStatic())\n                    ?: throw IllegalStateException(\n                        "IRIS_26514 custom noise model selected but stored profile is unavailable")\n                orderedPhysical.forEachIndexed { index, (frame, _) ->\n                    val iso = frame.motionV2ActualIso\n                    val model = profile.evaluate(iso)\n                        ?: throw IllegalStateException(\n                            "IRIS_26514 custom noise model cannot evaluate frame=$index iso=$iso")\n                    if (model.shotNoise.any { !it.isFinite() || it <= 0f } ||\n                        model.readNoise.any { !it.isFinite() } || model.readNoise.none { it > 0f }) {\n                        throw IllegalStateException(\n                            "IRIS_26514 custom noise model invalid at frame=$index iso=$iso")\n                    }\n                }\n                noiseSelection = RawNoiseProfileSelection.Calibrated(profile)\n                noiseAuthority = "CUSTOM:" +\n                    irisSettings.profileDisplayName.ifBlank { irisSettings.profileId }\n            } else {\n                orderedPhysical.forEachIndexed { index, (frame, _) ->\n                    if (frame.motionV2NoiseProfileSource != "CAMERA2_PER_FRAME") {\n                        throw IllegalStateException(\n                            "IRIS_26514 strict Camera2 noise requires per-frame metadata; " +\n                                "frame=$index source=${frame.motionV2NoiseProfileSource}")\n                    }\n                    val model = RawNoiseModel.fromCamera2NoiseProfile(frame.motionV2NoiseProfile)\n                    if (!model.hasValidCamera2Profile) {\n                        throw IllegalStateException(\n                            "IRIS_26514 invalid Camera2 SENSOR_NOISE_PROFILE frame=$index")\n                    }\n                }\n                noiseSelection = RawNoiseProfileSelection.Camera2\n                noiseAuthority = "CAMERA2_PER_FRAME"\n            }\n            PLog.i(TAG, "IRIS_26514_NOISE_AUTHORITY source=$noiseAuthority " +\n                "frames=${orderedPhysical.size} baseFallback=0 pixelFallback=0 " +\n                "crossSourceFallback=false")\n\n            parameters.motionCanonicalExposureGain = 1.0f'''
        s = one(s, anchor, replacement, 'strict noise authority insertion')
        s = one(s,
            '''                    channelNoiseProfile = if (frame.motionV2NoiseProfileSource == "CAMERA2_BASE_FRAME") {\n                        null\n                    } else {\n                        frame.motionV2NoiseProfile.copyOf()\n                    },''',
            '''                    channelNoiseProfile = if (irisSettings.customNoiseModelEnabled) {\n                        null\n                    } else {\n                        frame.motionV2NoiseProfile.copyOf()\n                    },''',
            'per-frame/custom channel profile')
        s = one(s,
            '                noiseProfileSelection = RawNoiseProfileSelection.Camera2,',
            '                noiseProfileSelection = noiseSelection,',
            'selected noise profile wiring')
        s = one(s,
            '''                noiseProfileLayout = RawNoiseProfileLayout.CAMERA2_CFA,\n                channelNoiseProfile = reference.motionV2NoiseProfile.copyOf(),''',
            '''                noiseProfileLayout = if (irisSettings.customNoiseModelEnabled)\n                    RawNoiseProfileLayout.CANONICAL_BAYER else RawNoiseProfileLayout.CAMERA2_CFA,\n                channelNoiseProfile = if (irisSettings.customNoiseModelEnabled)\n                    floatArrayOf() else reference.motionV2NoiseProfile.copyOf(),''',
            'denoise metadata source identity')
        old = '''            requireParity(MgcFullResolutionDenoise.ensureInitialized(\n                PhotonCamera.getApplicationContextStatic()),\n                "MGC denoise tuning assets failed initialization")\n            requireParity(MgcFullResolutionDenoise.denoise(\n                rgba16f = denoiseBuffer,\n                width = size.x,\n                height = size.y,\n                globalOriginX = 0,\n                globalOriginY = 0,\n                fullWidth = size.x,\n                fullHeight = size.y,\n                outputScale = 1f,\n                inputLayout = MgcFullResolutionDenoise.InputLayout.CAMERA_RGBA16F,\n                applyLensShadingInBayerAot = false,\n                metadata = denoiseMetadata,\n                preparedYuvNoiseModel = null,\n                applyLensShadingToDenoiseStrength = false,\n                tuningSnr = tuningSnr!!,\n                pass = MgcFullResolutionDenoise.Pass.SPATIAL_DEFAULT,\n                lumaStrengthScale = 1.0f,\n                chromaStrengthScale = 1.0f,\n            ), "MGC SPATIAL_DEFAULT denoise rejected its propagated state")'''
        new = '''            val lumaScale = irisSettings.lumaDenoise\n            val chromaScale = irisSettings.chromaDenoise\n            val runFullResolutionDenoise = irisSettings.noiseReductionEnabled &&\n                (lumaScale > 0f || chromaScale > 0f)\n            if (runFullResolutionDenoise) {\n                requireParity(MgcFullResolutionDenoise.ensureInitialized(\n                    PhotonCamera.getApplicationContextStatic()),\n                    "MGC denoise tuning assets failed initialization")\n                requireParity(MgcFullResolutionDenoise.denoise(\n                    rgba16f = denoiseBuffer,\n                    width = size.x,\n                    height = size.y,\n                    globalOriginX = 0,\n                    globalOriginY = 0,\n                    fullWidth = size.x,\n                    fullHeight = size.y,\n                    outputScale = 1f,\n                    inputLayout = MgcFullResolutionDenoise.InputLayout.CAMERA_RGBA16F,\n                    applyLensShadingInBayerAot = false,\n                    metadata = denoiseMetadata,\n                    preparedYuvNoiseModel = null,\n                    applyLensShadingToDenoiseStrength = false,\n                    tuningSnr = tuningSnr!!,\n                    pass = MgcFullResolutionDenoise.Pass.SPATIAL_DEFAULT,\n                    lumaStrengthScale = lumaScale,\n                    chromaStrengthScale = chromaScale,\n                ), "MGC SPATIAL_DEFAULT denoise rejected its propagated state")\n            }\n            PLog.i(TAG, "IRIS_26514_DENOISE master=${irisSettings.noiseReductionEnabled} " +\n                "luma=$lumaScale chroma=$chromaScale executed=$runFullResolutionDenoise " +\n                "legacyPhotonNr=false")'''
        s = one(s, old, new, 'MGC luma/chroma/master wiring')
        return s

    if rel.endswith('PostPipeline.java'):
        s = one(s,
            'import com.particlesdevs.photoncamera.processing.render.NoiseModeler;\n',
            'import com.particlesdevs.photoncamera.processing.render.NoiseModeler;\nimport com.particlesdevs.photoncamera.processing.processor.IrisMotionSettings;\n',
            'PostPipeline Iris settings import')
        anchor = '''            add(new MotionV2ColorTransform());\n            add(new StageTelemetry("V2_POST_CAMERA2_COLOR_TRANSFORM"));\n\n            /*\n             * IRIS_26477_WRONSKI_PRIMARY_DENOISE_ONLY'''
        replacement = '''            add(new MotionV2ColorTransform());\n            add(new StageTelemetry("V2_POST_CAMERA2_COLOR_TRANSFORM"));\n\n            /* IRIS_26514_OPTIONAL_LINEAR_PRESENTATION_CONTROLS\n             * Neutral settings add no node/pass at all, preserving exact 26513 input to render.\n             * Non-neutral exposure/shadows/contrast operate on the common extended-linear source\n             * before MotionV2Render derives both SDR and UHDR.\n             */\n            IrisMotionSettings.Snapshot irisMotionSettings = IrisMotionSettings.current();\n            if (irisMotionSettings.hasToneAdjustment()) {\n                add(new IrisMotionToneControls(irisMotionSettings));\n                add(new StageTelemetry("IRIS_26514_LINEAR_PRESENTATION_CONTROLS"));\n            }\n\n            /*\n             * IRIS_26477_WRONSKI_PRIMARY_DENOISE_ONLY'''
        s = one(s, anchor, replacement, 'optional tone node insertion')
        return s

    if rel.endswith('IsoExpoSelector.java'):
        old = '        double compensation = Math.pow(2.0,PhotonCamera.getSettings().exposureCompensation);'
        new = '''        // IRIS_26514_MOTION_POST_EXPOSURE_ONLY: the legacy Photon exposure-compensation\n        // preference must not alter Motion capture energy. Iris Exposure is applied later in\n        // extended-linear RGB, after reconstruction/color and before the common SDR/UHDR render.\n        double compensation = PhotonCamera.getSettings().selectedMode == CameraMode.MOTION\n                ? 1.0\n                : Math.pow(2.0,PhotonCamera.getSettings().exposureCompensation);'''
        s = one(s, old, new, 'disable legacy Motion exposure compensation')
        return s

    if rel.endswith('PreferenceKeys.java'):
        s = one(s,
            '''        settingsManager.setInitial(SCOPE_GLOBAL, Key.KEY_RAWVIDEO_CROP_169, true);

        settingsManager.setDefaults(Key.CAMERA_ID''',
            '''        settingsManager.setInitial(SCOPE_GLOBAL, Key.KEY_RAWVIDEO_CROP_169, true);

        // IRIS_26514_PER_LENS_DEFAULT_SEED: regular (non-common) keys participate in the
        // existing settings_for_camera_<id> JSON ownership. Seed them before lens JSONs are made.
        settingsManager.setInitial(SCOPE_GLOBAL, "pref_iris_custom_noise_model", "0");
        settingsManager.setInitial(SCOPE_GLOBAL, "pref_iris_custom_noise_profile_id", "");
        settingsManager.setInitial(SCOPE_GLOBAL, "pref_iris_custom_noise_profile_name", "");
        settingsManager.setInitial(SCOPE_GLOBAL, "pref_iris_luma_denoise", "1.0");
        settingsManager.setInitial(SCOPE_GLOBAL, "pref_iris_chroma_denoise", "1.0");
        settingsManager.setInitial(SCOPE_GLOBAL, "pref_iris_exposure_ev", "0.0");
        settingsManager.setInitial(SCOPE_GLOBAL, "pref_iris_shadows", "0.0");
        settingsManager.setInitial(SCOPE_GLOBAL, "pref_iris_contrast", "0.0");

        settingsManager.setDefaults(Key.CAMERA_ID''',
            'seed Iris defaults before per-lens JSON creation')
        s = one(s,
            '        HashMap<String, ?> map = GSON.fromJson(alreadySavedJSON, HashMap.class);',
            '        HashMap<String, Object> map = GSON.fromJson(alreadySavedJSON, HashMap.class);',
            'mutable per-lens map for 26514 defaults')
        s = one(s,
            '''        for (Map.Entry<String, ?> e : map.entrySet()) {
            String key = e.getKey();''',
            '''        // IRIS_26514_PER_LENS_LEGACY_JSON_DEFAULTS: old lens JSONs predate these keys.
        // Add missing defaults to the selected lens's in-memory map before applying it. This
        // prevents values from the previously active lens leaking into an old per-lens JSON.
        map.putIfAbsent("pref_iris_custom_noise_model", "0");
        map.putIfAbsent("pref_iris_custom_noise_profile_id", "");
        map.putIfAbsent("pref_iris_custom_noise_profile_name", "");
        map.putIfAbsent("pref_iris_luma_denoise", "1.0");
        map.putIfAbsent("pref_iris_chroma_denoise", "1.0");
        map.putIfAbsent("pref_iris_exposure_ev", "0.0");
        map.putIfAbsent("pref_iris_shadows", "0.0");
        map.putIfAbsent("pref_iris_contrast", "0.0");
        for (Map.Entry<String, Object> e : map.entrySet()) {
            String key = e.getKey();''',
            'legacy per-lens Iris default isolation')
        return s

    if rel.endswith('SettingsActivity.java'):
        s = one(s,
            'import androidx.preference.PreferenceFragmentCompat;\n',
            'import androidx.preference.PreferenceFragmentCompat;\nimport androidx.preference.PreferenceGroup;\n',
            'PreferenceGroup import')
        s = one(s,
            'import com.particlesdevs.photoncamera.pro.SupportedDevice;\n',
            'import com.particlesdevs.photoncamera.pro.SupportedDevice;\nimport com.particlesdevs.photoncamera.processing.processor.IrisMotionSettings;\nimport com.particlesdevs.photoncamera.processing.processor.IrisNoiseProfileStore;\n',
            'Iris settings UI imports')
        s = one(s,
            '        private ActivityResultLauncher<String[]> lutImportLauncher;\n',
            '        private ActivityResultLauncher<String[]> lutImportLauncher;\n        private ActivityResultLauncher<String[]> irisNoiseModelImportLauncher;\n',
            'noise profile launcher field')
        anchor = '''            TunablePngPreference.setImportLauncher(lutImportLauncher);\n            \n            // Check if we're opening the tunable submenu specifically'''
        replacement = '''            TunablePngPreference.setImportLauncher(lutImportLauncher);\n\n            irisNoiseModelImportLauncher = registerForActivityResult(\n                    new ActivityResultContracts.OpenDocument(),\n                    uri -> {\n                        if (uri == null) return;\n                        IrisNoiseProfileStore.ImportResult result =\n                                IrisNoiseProfileStore.importFromUri(mContext, uri);\n                        PhotonCamera.showToast(result.getMessage());\n                        refreshIrisNoiseProfileUi();\n                    });\n            \n            // Check if we're opening the tunable submenu specifically'''
        s = one(s, anchor, replacement, 'noise import launcher registration')
        s = one(s,
            '            filterPreferencesByMode();\n            showHideHdrxSettings();',
            '            filterPreferencesByMode();\n            setupIrisMotionPreferences();\n            showHideHdrxSettings();',
            'setup Iris Motion UI')
        old_else = '''            } else {\n                // Photo modes: hide all video-specific settings\n                removePreferenceFromScreen(mContext.getString(R.string.pref_category_video_key));\n                removePreferenceFromScreen(mContext.getString(R.string.pref_category_rawvideo_key));\n            }\n        }\n\n        private void showHideHdrxSettings()'''
        new_else = '''            } else {\n                // Photo modes: hide all video-specific settings\n                removePreferenceFromScreen(mContext.getString(R.string.pref_category_video_key));\n                removePreferenceFromScreen(mContext.getString(R.string.pref_category_rawvideo_key));\n                if (cameraMode == CameraMode.MOTION) {\n                    // Stable Motion bypasses these legacy Photon controls; do not present dead or\n                    // capture-affecting knobs beside the real Iris/MGC controls.\n                    removePreferenceAnywhere(PreferenceKeys.Key.KEY_SHARPNESS_SEEKBAR.mValue);\n                    removePreferenceAnywhere(PreferenceKeys.Key.KEY_SATURATION_SEEKBAR.mValue);\n                    removePreferenceAnywhere(PreferenceKeys.Key.KEY_CONTRAST_SEEKBAR.mValue);\n                    removePreferenceAnywhere(PreferenceKeys.Key.KEY_EXPOCOMPENSATE_SEEKBAR.mValue);\n                    removePreferenceAnywhere(PreferenceKeys.Key.KEY_NOISESTR_SEEKBAR.mValue);\n                    removePreferenceAnywhere(PreferenceKeys.Key.KEY_MERGE_SEEKBAR.mValue);\n                    removePreferenceAnywhere(PreferenceKeys.Key.KEY_SHADOWS_SEEKBAR.mValue);\n                    removePreferenceAnywhere(PreferenceKeys.Key.KEY_COMPRESSOR_SEEKBAR.mValue);\n                } else {\n                    removePreferenceAnywhere(IrisMotionSettings.KEY_CUSTOM_NOISE_MODEL);\n                    removePreferenceAnywhere(IrisMotionSettings.KEY_IMPORT_NOISE_MODEL);\n                    removePreferenceAnywhere(IrisMotionSettings.KEY_LUMA_DENOISE);\n                    removePreferenceAnywhere(IrisMotionSettings.KEY_CHROMA_DENOISE);\n                    removePreferenceAnywhere(IrisMotionSettings.KEY_EXPOSURE_EV);\n                    removePreferenceAnywhere(IrisMotionSettings.KEY_SHADOWS);\n                    removePreferenceAnywhere(IrisMotionSettings.KEY_CONTRAST);\n                }\n            }\n        }\n\n        private void setupIrisMotionPreferences() {\n            CameraMode cameraMode = CameraMode.valueOf(\n                    sCameraMode == -1 ? PreferenceKeys.getCameraModeOrdinal() : sCameraMode);\n            if (cameraMode != CameraMode.MOTION) return;\n\n            Preference importPref = findPreference(IrisMotionSettings.KEY_IMPORT_NOISE_MODEL);\n            if (importPref != null) {\n                importPref.setOnPreferenceClickListener(preference -> {\n                    irisNoiseModelImportLauncher.launch(new String[]{"*/*"});\n                    return true;\n                });\n            }\n            Preference custom = findPreference(IrisMotionSettings.KEY_CUSTOM_NOISE_MODEL);\n            if (custom != null) {\n                custom.setOnPreferenceChangeListener((preference, newValue) -> {\n                    boolean enable = Boolean.TRUE.equals(newValue);\n                    if (enable && !IrisNoiseProfileStore.hasValidSelectedProfile(mContext)) {\n                        PhotonCamera.showToast("Import a valid .c noise model first");\n                        irisNoiseModelImportLauncher.launch(new String[]{"*/*"});\n                        return false;\n                    }\n                    return true;\n                });\n            }\n            refreshIrisNoiseProfileUi();\n        }\n\n        private void refreshIrisNoiseProfileUi() {\n            Preference importPref = findPreference(IrisMotionSettings.KEY_IMPORT_NOISE_MODEL);\n            if (importPref == null) return;\n            String name = IrisMotionSettings.current().profileDisplayName;\n            String base = mContext.getString(R.string.iris_import_noise_model);\n            importPref.setTitle(name == null || name.isEmpty() ? base : base + " — " + name);\n            importPref.setSummary(mContext.getString(R.string.iris_import_noise_model_summary));\n        }\n\n        private void showHideHdrxSettings()'''
        s = one(s, old_else, new_else, 'Motion-only settings filtering')
        anchor = '''        private void removePreferenceFromScreen(String preferenceKey) {\n            PreferenceScreen parentScreen = findPreference(SettingsFragment.KEY_MAIN_PARENT_SCREEN);'''
        replacement = '''        private void removePreferenceAnywhere(String preferenceKey) {\n            Preference preference = findPreference(preferenceKey);\n            PreferenceGroup hdrx = findPreference(mContext.getString(R.string.pref_category_hdrx_key));\n            if (preference != null && hdrx != null) hdrx.removePreference(preference);\n        }\n\n        private void removePreferenceFromScreen(String preferenceKey) {\n            PreferenceScreen parentScreen = findPreference(SettingsFragment.KEY_MAIN_PARENT_SCREEN);'''
        s = one(s, anchor, replacement, 'nested preference removal helper')
        s = one(s,
            '            Log.d("SettingsFragment", "onSharedPreferenceChanged: key=" + key);\n            \n            if (key.equals(PreferenceKeys.Key.KEY_SAVE_PER_LENS_SETTINGS.mValue)) {',
            '            Log.d("SettingsFragment", "onSharedPreferenceChanged: key=" + key);\n            IrisMotionSettings.normalizePersistedSlider(key);\n            \n            if (key.equals(PreferenceKeys.Key.KEY_SAVE_PER_LENS_SETTINGS.mValue)) {',
            'slider tenth normalization')
        return s

    if rel.endswith('preferences.xml'):
        anchor = '        <com.particlesdevs.photoncamera.ui.settings.custompreferences.ManagedSwitchPreference ns0:key="@string/pref_hdrx_nr_key" ns0:defaultValue="@bool/pref_hdrx_nr_default" ns0:layout="@layout/preference_with_margin" ns0:title="@string/hdrxNR" ns0:summary="" ns0:icon="@drawable/ic_gradient_black_24dp" />'
        insertion = anchor + '''\n        <com.particlesdevs.photoncamera.ui.settings.custompreferences.ManagedSwitchPreference ns0:key="pref_iris_custom_noise_model" ns0:defaultValue="false" ns0:layout="@layout/preference_with_margin" ns0:title="@string/iris_custom_noise_model" ns0:summary="@string/iris_custom_noise_model_summary" ns0:icon="@drawable/ic_gradient_black_24dp" />\n        <Preference ns0:key="pref_iris_import_noise_model" ns0:layout="@layout/preference_with_margin" ns0:title="@string/iris_import_noise_model" ns0:summary="@string/iris_import_noise_model_summary" ns0:icon="@drawable/ic_save" />\n        <com.particlesdevs.photoncamera.ui.settings.custompreferences.UniversalSeekBarPreference ns0:key="pref_iris_luma_denoise" ns0:layout="@layout/preference_seekbar" ns0:title="@string/iris_luma_denoise" ns0:summary="" ns0:defaultValue="@string/pref_iris_luma_denoise_default" ns1:maxValue="2.0" ns1:minValue="0.0" ns1:isFloat="true" ns1:stepPerUnit="10" ns0:icon="@drawable/ic_grain_black_24dp" />\n        <com.particlesdevs.photoncamera.ui.settings.custompreferences.UniversalSeekBarPreference ns0:key="pref_iris_chroma_denoise" ns0:layout="@layout/preference_seekbar" ns0:title="@string/iris_chroma_denoise" ns0:summary="" ns0:defaultValue="@string/pref_iris_chroma_denoise_default" ns1:maxValue="2.0" ns1:minValue="0.0" ns1:isFloat="true" ns1:stepPerUnit="10" ns0:icon="@drawable/ic_gradient_black_24dp" />\n        <com.particlesdevs.photoncamera.ui.settings.custompreferences.UniversalSeekBarPreference ns0:key="pref_iris_exposure_ev" ns0:layout="@layout/preference_seekbar" ns0:title="@string/iris_exposure" ns0:summary="" ns0:defaultValue="@string/pref_iris_exposure_default" ns1:maxValue="1.0" ns1:minValue="-1.0" ns1:isFloat="true" ns1:stepPerUnit="10" ns0:icon="@drawable/ic_saturation" />\n        <com.particlesdevs.photoncamera.ui.settings.custompreferences.UniversalSeekBarPreference ns0:key="pref_iris_shadows" ns0:layout="@layout/preference_seekbar" ns0:title="@string/iris_shadows" ns0:summary="" ns0:defaultValue="@string/pref_iris_shadows_default" ns1:maxValue="1.0" ns1:minValue="-1.0" ns1:isFloat="true" ns1:stepPerUnit="10" ns0:icon="@drawable/ic_compressor" />\n        <com.particlesdevs.photoncamera.ui.settings.custompreferences.UniversalSeekBarPreference ns0:key="pref_iris_contrast" ns0:layout="@layout/preference_seekbar" ns0:title="@string/iris_contrast" ns0:summary="" ns0:defaultValue="@string/pref_iris_contrast_default" ns1:maxValue="1.0" ns1:minValue="-1.0" ns1:isFloat="true" ns1:stepPerUnit="10" ns0:icon="@drawable/ic_saturation" />'''
        s = one(s, anchor, insertion, 'Iris Motion preferences insertion')
        return s

    if rel.endswith('strings.xml'):
        anchor = '    <string name="hdrxNR">Noise Reduction</string>\n'
        insertion = anchor + '''    <string name="iris_custom_noise_model">Custom Noise Model</string>\n    <string name="iris_custom_noise_model_summary">Use the imported per-lens GCam .c model instead of Camera2 metadata</string>\n    <string name="iris_import_noise_model">Import Noise Model</string>\n    <string name="iris_import_noise_model_summary">Tap to choose a validated .c file</string>\n    <string name="iris_luma_denoise">Luma Denoise</string>\n    <string name="iris_chroma_denoise">Chroma Denoise</string>\n    <string name="iris_exposure">Exposure (EV)</string>\n    <string name="iris_shadows">Shadows</string>\n    <string name="iris_contrast">Contrast</string>\n'''
        s = one(s, anchor, insertion, 'Iris Motion strings insertion')
        return s

    if rel.endswith('default_prefs.xml'):
        anchor = '    <bool name="pref_hdrx_nr_default">true</bool>\n'
        insertion = anchor + '''    <string name="pref_iris_luma_denoise_default" translatable="false">1.0</string>\n    <string name="pref_iris_chroma_denoise_default" translatable="false">1.0</string>\n    <string name="pref_iris_exposure_default" translatable="false">0.0</string>\n    <string name="pref_iris_shadows_default" translatable="false">0.0</string>\n    <string name="pref_iris_contrast_default" translatable="false">0.0</string>\n'''
        s = one(s, anchor, insertion, 'Iris Motion defaults insertion')
        return s

    raise AssertionError(f'unhandled changed path: {rel}')


def make_patch(root: Path, before: dict[str, str], after: dict[str, str]) -> str:
    chunks = []
    for rel in sorted(CHANGED):
        a = before.get(rel, '')
        b = after[rel]
        if a == b:
            raise AssertionError(f'{rel}: transform produced no change')
        chunks.extend(difflib.unified_diff(
            a.splitlines(True), b.splitlines(True),
            fromfile=f'a/{rel}', tofile=f'b/{rel}', n=3,
        ))
    return ''.join(chunks)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('root', type=Path)
    ap.add_argument('--patch-out', type=Path, required=True)
    ap.add_argument('--patch-sha-out', type=Path, required=True)
    ns = ap.parse_args()
    root = ns.root.resolve()

    before: dict[str, str] = {}
    after: dict[str, str] = {}
    for rel in sorted(CHANGED):
        p = root / rel
        old = p.read_text() if p.exists() else ''
        before[rel] = old
        after[rel] = expected_text(rel, old)

    # Rollback/audit patch is created and hashed before any runtime write.
    patch = make_patch(root, before, after)
    ns.patch_out.parent.mkdir(parents=True, exist_ok=True)
    ns.patch_out.write_text(patch)
    digest = hashlib.sha256(ns.patch_out.read_bytes()).hexdigest()
    ns.patch_sha_out.write_text(f'{digest}  {ns.patch_out.name}\n')
    print(f'PASS: 26514 rollback/audit patch generated before runtime writes SHA256={digest}')

    for rel in sorted(CHANGED):
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(after[rel])
    print(f'PASS: applied exact 26514 transform to {len(CHANGED)} runtime paths')


if __name__ == '__main__':
    main()
