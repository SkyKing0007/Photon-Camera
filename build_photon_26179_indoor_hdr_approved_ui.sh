#!/usr/bin/env bash
set -euo pipefail

ROOT=/workspaces/Photon-Camera
cd "$ROOT"

fail() {
  printf '\nERROR: %s\n' "$*" >&2
  exit 1
}

echo "=== PHOTON CAMERA 0.9726179 / BUILD 26179 ==="

[[ "$(git branch --show-current)" == "experimental-effective-stack" ]] \
  || fail "Expected branch experimental-effective-stack"

[[ "$(git rev-parse HEAD)" == "cedc3ab3e39ad49d42523cff7e3711f8baa69a13" ]] \
  || fail "Unexpected checkpoint HEAD"

grep -qx 'VERSION_BUILD=26178' app/version.properties \
  || fail "Expected VERSION_BUILD=26178"

grep -q 'motionChromaCleanupMaximum = 0.45f' \
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionChromaDenoise.java \
  || fail "Motion chroma correction missing"

grep -q 'motionLumaCleanupMaximum = 0.14f' \
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionLumaDenoise.java \
  || fail "Motion luma correction missing"

grep -q 'motionCaptureSharpeningFloor = 0.25f' \
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/CaptureSharpening.java \
  || fail "Capture sharpening correction missing"

grep -q 'motionFinalSharpeningFloor = 0.25f' \
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Sharpen2.java \
  || fail "Final sharpening correction missing"

STAMP="$(date +%Y%m%d_%H%M%S)"
WORK="$ROOT/build_26179_indoor_hdr_approved_ui_${STAMP}"
BACKUP_BRANCH="backup/experimental-effective-stack-before-26179-${STAMP}"

mkdir -p "$WORK/before" "$WORK/after"
git branch "$BACKUP_BRANCH"
git status --short > "$WORK/status-before.txt"
git diff --binary HEAD > "$WORK/working-tree-before.patch"

for file in \
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java \
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/ExposureFusionBayer2.java \
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/AutoExposure.java \
  app/src/main/assets/shaders/autoexposure/apply.glsl \
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/ESD3D2.java \
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionLumaDenoise.java \
  app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java \
  app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/modeswitcher/LiquidModePicker.java \
  app/src/main/res/layout/layout_modeswitcher.xml \
  app/version.properties
do
  mkdir -p "$WORK/before/$(dirname "$file")"
  cp -a "$file" "$WORK/before/$file"
done

echo "Backup branch: $BACKUP_BRANCH"
echo "Backup directory: $WORK"

python3 - <<'PY'
from pathlib import Path
import re

def replace_once(path_str, old, new):
    path = Path(path_str)
    text = path.read_text()
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path_str}: expected 1 match, found {count}")
    path.write_text(text.replace(old, new, 1))

replace_once(
    "app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java",
    "    float softLight = 1.f;\n",
    '''    float softLight = 1.f;

    /*
     * Build 26179:
     * Strength of the Motion indoor bright-window HDR scene gate.
     * Zero preserves the complete existing pipeline, including Night mode.
     */
    float indoorHdrSceneStrength = 0.0f;
'''
)

replace_once(
    "app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/ExposureFusionBayer2.java",
    '''        overexposure = Math.min(256.f,overexposure);
        underexposure = Math.max(1.f/256.f,underexposure);


        if(useSymmetricExposureFork){
''',
    '''        overexposure = Math.min(256.f,overexposure);
        underexposure = Math.max(1.f/256.f,underexposure);

        float indoorHdrSceneStrength = 0.0f;
        if (com.particlesdevs.photoncamera.app.PhotonCamera
                .getSettings().selectedMode
                == com.particlesdevs.photoncamera.api.CameraMode.MOTION) {
            float motionIso =
                    Math.max(
                            1.0f,
                            basePipeline.mParameters.iso
                    );

            float lowIsoBlend =
                    1.0f
                            - Math2.smoothstep(
                                    500.0f,
                                    1200.0f,
                                    motionIso
                            );

            float shadowLiftNeed =
                    Math2.smoothstep(
                            1.40f,
                            3.50f,
                            overexposure
                    );

            float highlightProtectionNeed =
                    1.0f
                            - Math2.smoothstep(
                                    0.58f,
                                    0.95f,
                                    underexposure
                            );

            indoorHdrSceneStrength =
                    Math2.clamp(
                            lowIsoBlend
                                    * shadowLiftNeed
                                    * highlightProtectionNeed,
                            0.0f,
                            1.0f
                    );

            ((PostPipeline) basePipeline)
                    .indoorHdrSceneStrength =
                    indoorHdrSceneStrength;

            Log.d(
                    Name,
                    "MOTION_26179_INDOOR_HDR_GATE"
                            + " iso=" + motionIso
                            + " overexposure=" + overexposure
                            + " underexposure=" + underexposure
                            + " lowIsoBlend=" + lowIsoBlend
                            + " shadowLiftNeed=" + shadowLiftNeed
                            + " highlightProtectionNeed="
                            + highlightProtectionNeed
                            + " strength=" + indoorHdrSceneStrength
                            + " nightModeAffected=false"
                            + " globalShadowLift=false"
            );
        } else {
            ((PostPipeline) basePipeline)
                    .indoorHdrSceneStrength = 0.0f;
        }


        if(useSymmetricExposureFork){
'''
)

replace_once(
    "app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionLumaDenoise.java",
    '''        float strength =
                motionLumaCleanupMaximum
                        * highIsoBlend;
''',
    '''        float indoorHdrStrength =
                ((PostPipeline) basePipeline)
                        .indoorHdrSceneStrength;

        float strength =
                motionLumaCleanupMaximum
                        * highIsoBlend
                        * (
                                1.0f
                                        - 0.75f
                                        * indoorHdrStrength
                        );
'''
)

replace_once(
    "app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionLumaDenoise.java",
    '''                        + " strength=" + strength
                        + " noiseGain=" + noiseGain
''',
    '''                        + " strength=" + strength
                        + " indoorHdrStrength="
                        + indoorHdrStrength
                        + " sceneGatedLumaReduction="
                        + (0.75f * indoorHdrStrength)
                        + " noiseGain=" + noiseGain
'''
)

replace_once(
    "app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/ESD3D2.java",
    '''            glProg.setDefine("MOIRE", moire);
            glProg.setDefine("LUMA", luma);
            glProg.setDefine("CHROMASTRENGTH", chromaStrength);
''',
    '''            float indoorHdrStrength =
                    ((PostPipeline) basePipeline)
                            .indoorHdrSceneStrength;

            float appliedLuma =
                    Math2.mix(
                            luma,
                            luma * 0.72f,
                            indoorHdrStrength
                    );

            glProg.setDefine("MOIRE", moire);
            glProg.setDefine("LUMA", appliedLuma);
            glProg.setDefine("CHROMASTRENGTH", chromaStrength);
'''
)

replace_once(
    "app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/ESD3D2.java",
    '''            double kernelSize = 1.0f + Math.sqrt(noiseMpy) * noiseToKernelSize;
            int msize = Math.min(minSize + (int)kernelSize - (int)kernelSize%2, maxSize);
            Log.d("ESD3D", "KernelSize: "+kernelSize+" MSIZE: "+msize);
''',
    '''            double kernelSize =
                    1.0f
                            + Math.sqrt(noiseMpy)
                            * noiseToKernelSize;

            kernelSize =
                    Math2.mix(
                            (float) kernelSize,
                            (float) kernelSize * 0.78f,
                            indoorHdrStrength
                    );

            int msize =
                    Math.min(
                            minSize
                                    + (int) kernelSize
                                    - (int) kernelSize % 2,
                            maxSize
                    );

            Log.d(
                    "ESD3D",
                    "MOTION_26179_INDOOR_HDR_DETAIL"
                            + " kernelSize=" + kernelSize
                            + " MSIZE=" + msize
                            + " indoorHdrStrength="
                            + indoorHdrStrength
                            + " lumaConfigured=" + luma
                            + " lumaApplied=" + appliedLuma
                            + " nightModeAffected=false"
            );
'''
)

replace_once(
    "app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/AutoExposure.java",
    '''        glProg.setVar("applyGammaMix", applyGammaMix);
        WorkingTexture = basePipeline.getMain();
''',
    '''        glProg.setVar("applyGammaMix", applyGammaMix);

        float indoorHdrStrength =
                ((PostPipeline) basePipeline)
                        .indoorHdrSceneStrength;

        float lowerMidLift =
                0.22f
                        * indoorHdrStrength;

        float highlightCompression =
                0.32f
                        * indoorHdrStrength;

        glProg.setVar(
                "indoorHdrStrength",
                indoorHdrStrength
        );
        glProg.setVar(
                "lowerMidLift",
                lowerMidLift
        );
        glProg.setVar(
                "highlightCompression",
                highlightCompression
        );

        Log.d(
                "AutoExposure",
                "MOTION_26179_INDOOR_HDR_TONE"
                        + " strength=" + indoorHdrStrength
                        + " lowerMidLift=" + lowerMidLift
                        + " highlightCompression="
                        + highlightCompression
                        + " globalShadowLift=false"
                        + " nightModeAffected=false"
        );

        WorkingTexture = basePipeline.getMain();
'''
)

replace_once(
    "app/src/main/assets/shaders/autoexposure/apply.glsl",
    '''uniform float applyGammaMix;
out vec4 Output;
''',
    '''uniform float applyGammaMix;
uniform float indoorHdrStrength;
uniform float lowerMidLift;
uniform float highlightCompression;
out vec4 Output;
'''
)

replace_once(
    "app/src/main/assets/shaders/autoexposure/apply.glsl",
    '''    Output.rgb = tonemap(mix(inp.rgb,sqrt(inp.rgb), applyGammaMix), mpy);
    Output.rgb = mix(Output.rgb,Output.rgb * Output.rgb, applyGammaMix);
}
''',
    '''    Output.rgb = tonemap(mix(inp.rgb,sqrt(inp.rgb), applyGammaMix), mpy);
    Output.rgb = mix(Output.rgb,Output.rgb * Output.rgb, applyGammaMix);

    float luma =
            dot(
                    Output.rgb,
                    vec3(0.299, 0.587, 0.114)
            );

    float lowerMidMask =
            smoothstep(
                    0.08,
                    0.22,
                    luma
            )
            * (
                    1.0
                            - smoothstep(
                                    0.52,
                                    0.72,
                                    luma
                            )
            );

    Output.rgb *=
            1.0
                    + lowerMidLift
                    * lowerMidMask;

    luma =
            dot(
                    Output.rgb,
                    vec3(0.299, 0.587, 0.114)
            );

    float highlightMask =
            smoothstep(
                    0.52,
                    0.92,
                    luma
            );

    vec3 compressedHighlights =
            Output.rgb
                    / (
                            vec3(1.0)
                                    + 0.55
                                    * Output.rgb
                    );

    Output.rgb =
            mix(
                    Output.rgb,
                    compressedHighlights,
                    highlightCompression
                            * highlightMask
            );

    Output.rgb =
            clamp(
                    Output.rgb,
                    0.0,
                    1.0
            );
}
'''
)

picker = Path(
    "app/src/main/java/com/particlesdevs/photoncamera/ui/camera/"
    "views/modeswitcher/LiquidModePicker.java"
)

picker.write_text('''package com.particlesdevs.photoncamera.ui.camera.views.modeswitcher;

import android.animation.ValueAnimator;
import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.RectF;
import android.util.AttributeSet;
import android.util.TypedValue;
import android.view.MotionEvent;
import android.view.ViewGroup;
import android.view.animation.AccelerateDecelerateInterpolator;

import com.particlesdevs.photoncamera.ui.camera.views.modeswitcher.wefika.horizontalpicker.HorizontalPicker;

public class LiquidModePicker extends HorizontalPicker {
    private static final int SELECTED_YELLOW = 0xFFFFCC00;
    private static final int UNSELECTED_WHITE = 0xFFFFFFFF;
    private static final int COLLAPSED_WIDTH_DP = 154;
    private static final int EXPANDED_WIDTH_DP = 338;

    private final Paint fillPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint strokePaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint textPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final RectF pill = new RectF();
    private final RectF selection = new RectF();

    private boolean expanded = false;
    private int selectedIndex = 0;
    private float downX;

    public LiquidModePicker(Context context) {
        this(context, null);
    }

    public LiquidModePicker(Context context, AttributeSet attrs) {
        super(context, attrs);
        setSideItems(0);
        setOverScrollMode(OVER_SCROLL_NEVER);
        setWillNotDraw(false);

        fillPaint.setStyle(Paint.Style.FILL);
        fillPaint.setColor(0xB0141414);

        strokePaint.setStyle(Paint.Style.STROKE);
        strokePaint.setStrokeWidth(dp(1.0f));
        strokePaint.setColor(0x55FFFFFF);

        textPaint.setTextAlign(Paint.Align.CENTER);
        textPaint.setTypeface(
                android.graphics.Typeface.create(
                        android.graphics.Typeface.DEFAULT,
                        android.graphics.Typeface.BOLD
                )
        );
        textPaint.setTextSize(sp(10.5f));
    }

    public void collapseToIndex(int index) {
        CharSequence[] labels = getValues();
        if (labels == null || labels.length == 0) return;

        selectedIndex =
                Math.max(
                        0,
                        Math.min(
                                labels.length - 1,
                                index
                        )
                );

        setSelectedItem(selectedIndex);
        setExpanded(false);
        invalidate();
    }

    private void setExpanded(boolean value) {
        if (expanded == value) return;
        expanded = value;

        int start = getLayoutParams().width;
        int end =
                (int) dp(
                        expanded
                                ? EXPANDED_WIDTH_DP
                                : COLLAPSED_WIDTH_DP
                );

        ValueAnimator animator = ValueAnimator.ofInt(start, end);
        animator.setDuration(240L);
        animator.setInterpolator(new AccelerateDecelerateInterpolator());
        animator.addUpdateListener(animation -> {
            ViewGroup.LayoutParams params = getLayoutParams();
            params.width = (Integer) animation.getAnimatedValue();
            setLayoutParams(params);
            invalidate();
        });
        animator.start();
    }

    @Override
    protected void onDraw(Canvas canvas) {
        CharSequence[] labels = getValues();
        int width = getWidth();
        int height = getHeight();

        if (labels == null || labels.length == 0 || width <= 0 || height <= 0) {
            return;
        }

        float pad = dp(2.5f);
        float radius = height / 2.0f;
        pill.set(pad, pad, width - pad, height - pad);

        canvas.drawRoundRect(pill, radius, radius, fillPaint);
        canvas.drawRoundRect(pill, radius, radius, strokePaint);

        float baseline =
                height / 2.0f
                        - (textPaint.ascent() + textPaint.descent()) / 2.0f;

        if (!expanded) {
            float half = width / 2.0f;
            selection.set(pad, pad, half - pad, height - pad);

            Paint selectedFill = new Paint(fillPaint);
            selectedFill.setColor(0x22FFFFFF);

            canvas.drawRoundRect(selection, radius, radius, selectedFill);
            canvas.drawRoundRect(selection, radius, radius, strokePaint);

            drawLabel(
                    canvas,
                    labels[selectedIndex].toString(),
                    half * 0.5f,
                    baseline,
                    SELECTED_YELLOW
            );

            int videoIndex = labels.length > 1 ? 1 : selectedIndex;

            drawLabel(
                    canvas,
                    labels[videoIndex].toString(),
                    half * 1.5f,
                    baseline,
                    selectedIndex == videoIndex
                            ? SELECTED_YELLOW
                            : UNSELECTED_WHITE
            );
            return;
        }

        float itemWidth = width / (float) labels.length;
        selection.set(
                selectedIndex * itemWidth + pad,
                pad,
                (selectedIndex + 1) * itemWidth - pad,
                height - pad
        );

        Paint selectedFill = new Paint(fillPaint);
        selectedFill.setColor(0x22FFFFFF);

        canvas.drawRoundRect(selection, radius, radius, selectedFill);
        canvas.drawRoundRect(selection, radius, radius, strokePaint);

        for (int i = 0; i < labels.length; i++) {
            drawLabel(
                    canvas,
                    labels[i].toString(),
                    itemWidth * (i + 0.5f),
                    baseline,
                    i == selectedIndex
                            ? SELECTED_YELLOW
                            : UNSELECTED_WHITE
            );
        }
    }

    @Override
    public boolean onTouchEvent(MotionEvent event) {
        CharSequence[] labels = getValues();
        if (labels == null || labels.length == 0) return false;

        if (event.getAction() == MotionEvent.ACTION_DOWN) {
            downX = event.getX();
            return true;
        }

        if (event.getAction() == MotionEvent.ACTION_UP) {
            if (Math.abs(event.getX() - downX) > dp(18.0f)) {
                return true;
            }

            if (!expanded) {
                if (event.getX() < getWidth() / 2.0f) {
                    setExpanded(true);
                } else {
                    collapseToIndex(Math.min(1, labels.length - 1));
                }
                return true;
            }

            int index =
                    Math.max(
                            0,
                            Math.min(
                                    labels.length - 1,
                                    (int) (
                                            event.getX()
                                                    / (
                                                            getWidth()
                                                                    / (float) labels.length
                                                    )
                                    )
                            )
                    );

            collapseToIndex(index);
            return true;
        }

        return true;
    }

    private void drawLabel(
            Canvas canvas,
            String label,
            float x,
            float baseline,
            int color
    ) {
        textPaint.setColor(color);
        canvas.drawText(label, x, baseline, textPaint);
    }

    private float dp(float value) {
        return TypedValue.applyDimension(
                TypedValue.COMPLEX_UNIT_DIP,
                value,
                getResources().getDisplayMetrics()
        );
    }

    private float sp(float value) {
        return TypedValue.applyDimension(
                TypedValue.COMPLEX_UNIT_SP,
                value,
                getResources().getDisplayMetrics()
        );
    }
}
''')

path = Path(
    "app/src/main/java/com/particlesdevs/photoncamera/ui/camera/"
    "CameraUIViewImpl.java"
)
text = path.read_text()

text = text.replace(
    "import com.particlesdevs.photoncamera.ui.camera.views.modeswitcher.wefika.horizontalpicker.HorizontalPicker;\n",
    "import com.particlesdevs.photoncamera.ui.camera.views.modeswitcher.LiquidModePicker;\n"
)

text = text.replace(
    '''    private static final CameraMode[] MODE_DISPLAY_ORDER = {
            CameraMode.MOTION,
            CameraMode.VIDEO,
            CameraMode.PHOTO,
            CameraMode.NIGHT,
            CameraMode.RAWVIDEO,
            CameraMode.UNLIMITED
    };
''',
    '''    private static final String[] MODE_DISPLAY_LABELS = {
            "MOTION",
            "VIDEO",
            "PHOTO",
            "PORTRAIT",
            "NIGHT",
            "PRO"
    };

    private static final CameraMode[] MODE_ACTION_ORDER = {
            CameraMode.MOTION,
            CameraMode.VIDEO,
            CameraMode.PHOTO,
            CameraMode.PHOTO,
            CameraMode.NIGHT,
            CameraMode.UNLIMITED
    };
'''
)

text = text.replace(
    "    private final HorizontalPicker mModePicker;\n",
    "    private final LiquidModePicker mModePicker;\n"
)

old_method = '''    private void initModeSwitcher() {
        Integer[] modeNameIds = CameraMode.nameIds();
        String[] displayNames = Arrays.stream(MODE_DISPLAY_ORDER)
                .map(mode -> cameraFragment.activity.getString(modeNameIds[mode.ordinal()]))
                .toArray(String[]::new);
        this.mModePicker.setValues(displayNames);
        this.mModePicker.setSideItems(0);
        this.mModePicker.setOverScrollMode(View.OVER_SCROLL_NEVER);
        this.mModePicker.setOnItemSelectedListener(index -> {
            if (index >= 0 && index < MODE_DISPLAY_ORDER.length) {
                switchToMode(MODE_DISPLAY_ORDER[index]);
            }
        });
        this.mModePicker.setSelectedItem(indexOfMode(CameraMode.valueOf(PreferenceKeys.getCameraModeOrdinal())));
    }

    private int indexOfMode(CameraMode mode) {
        for (int i = 0; i < MODE_DISPLAY_ORDER.length; i++) {
            if (MODE_DISPLAY_ORDER[i] == mode) return i;
        }
        return 0;
    }
'''

new_method = '''    private void initModeSwitcher() {
        this.mModePicker.setValues(MODE_DISPLAY_LABELS);
        this.mModePicker.setSideItems(0);
        this.mModePicker.setOverScrollMode(View.OVER_SCROLL_NEVER);
        this.mModePicker.setOnItemSelectedListener(index -> {
            if (index >= 0 && index < MODE_ACTION_ORDER.length) {
                this.mModePicker.collapseToIndex(index);
                switchToMode(MODE_ACTION_ORDER[index]);
            }
        });
        this.mModePicker.collapseToIndex(
                indexOfMode(
                        CameraMode.valueOf(
                                PreferenceKeys.getCameraModeOrdinal()
                        )
                )
        );
    }

    private int indexOfMode(CameraMode mode) {
        for (int i = 0; i < MODE_ACTION_ORDER.length; i++) {
            if (MODE_ACTION_ORDER[i] == mode) return i;
        }
        return 0;
    }
'''

if old_method not in text:
    raise SystemExit("CameraUIViewImpl initModeSwitcher context not found")

text = text.replace(old_method, new_method, 1)
text = text.replace("import java.util.Arrays;\n", "")
path.write_text(text)

layout = Path("app/src/main/res/layout/layout_modeswitcher.xml")
layout_text = layout.read_text()
layout_text = re.sub(
    r'android:layout_width="[^"]+"',
    'android:layout_width="154dp"',
    layout_text,
    count=1
)
layout.write_text(layout_text)

version = Path("app/version.properties")
version_text = version.read_text()
version.write_text(
    re.sub(
        r"(?m)^VERSION_BUILD=\d+$",
        "VERSION_BUILD=26179",
        version_text,
        count=1
    )
)
PY

grep -q 'indoorHdrSceneStrength = 0.0f' \
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java \
  || fail "Indoor HDR shared gate missing"

grep -q 'MOTION_26179_INDOOR_HDR_GATE' \
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/ExposureFusionBayer2.java \
  || fail "Indoor HDR scene detector missing"

grep -q 'MOTION_26179_INDOOR_HDR_TONE' \
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/AutoExposure.java \
  || fail "Indoor HDR tone handoff missing"

grep -q 'lowerMidMask' app/src/main/assets/shaders/autoexposure/apply.glsl \
  || fail "Selective lower-mid lift missing"

grep -q 'highlightCompression' app/src/main/assets/shaders/autoexposure/apply.glsl \
  || fail "Highlight compression missing"

grep -q 'MOTION_26179_INDOOR_HDR_DETAIL' \
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/ESD3D2.java \
  || fail "Scene-gated detail preservation missing"

grep -q 'PORTRAIT' \
  app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java \
  || fail "Approved Portrait UI choice missing"

grep -q 'EXPANDED_WIDTH_DP = 338' \
  app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/modeswitcher/LiquidModePicker.java \
  || fail "Expandable picker animation missing"

grep -qx 'VERSION_BUILD=26179' app/version.properties \
  || fail "Build number was not incremented"

grep -q 'motionChromaCleanupMaximum = 0.45f' \
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionChromaDenoise.java \
  || fail "Motion chroma correction lost"

grep -q 'motionLumaCleanupMaximum = 0.14f' \
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionLumaDenoise.java \
  || fail "Motion luma correction lost"

grep -q 'motionCaptureSharpeningFloor = 0.25f' \
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/CaptureSharpening.java \
  || fail "Capture sharpening correction lost"

grep -q 'motionFinalSharpeningFloor = 0.25f' \
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Sharpen2.java \
  || fail "Final sharpening correction lost"

grep -A4 'android:id="@+id/gallery_image_button"' \
  app/src/main/res/layout/layout_bottombuttons.xml \
  | grep -q 'android:layout_width="30dp"' \
  || fail "Thumbnail is not 30dp"

grep -A4 'android:id="@+id/flip_camera_button"' \
  app/src/main/res/layout/layout_bottombuttons.xml \
  | grep -q 'android:layout_width="30dp"' \
  || fail "Camera switch is not 30dp"

git diff --check || fail "git diff --check failed"

for file in \
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java \
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/ExposureFusionBayer2.java \
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/AutoExposure.java \
  app/src/main/assets/shaders/autoexposure/apply.glsl \
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/ESD3D2.java \
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionLumaDenoise.java \
  app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java \
  app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/modeswitcher/LiquidModePicker.java \
  app/src/main/res/layout/layout_modeswitcher.xml \
  app/version.properties
do
  mkdir -p "$WORK/after/$(dirname "$file")"
  cp -a "$file" "$WORK/after/$file"
done

git diff --binary HEAD > "$WORK/working-tree-after.patch"
git status --short > "$WORK/status-after.txt"

echo
echo "Building signed debug APK..."
./gradlew --no-daemon clean assembleDebug 2>&1 | tee "$WORK/build-26179.log"

APK="$(find app/build/outputs/apk/debug -type f -name '*.apk' -printf '%T@ %p\n' \
  | sort -nr | head -1 | cut -d' ' -f2-)"

[[ -n "$APK" && -f "$APK" ]] || fail "No debug APK found"

OUT="$ROOT/PhotonCamera-0.9726179-build26179-indoor-hdr-approved-ui-debug.apk"
cp -f "$APK" "$OUT"

APKSIGNER=""
for candidate in \
  "$ANDROID_HOME"/build-tools/*/apksigner \
  "$ANDROID_SDK_ROOT"/build-tools/*/apksigner
do
  [[ -x "$candidate" ]] && APKSIGNER="$candidate"
done

[[ -n "$APKSIGNER" ]] || fail "apksigner not found"

"$APKSIGNER" verify --verbose --print-certs "$OUT" \
  | tee "$WORK/apk-signing.txt"

sha256sum "$OUT" | tee "$WORK/PhotonCamera-0.9726179-build26179.sha256"

echo
echo "=== BUILD 26179 COMPLETE ==="
echo "Build: 0.9726179 / 26179"
echo "Processing:"
echo "  - Motion-only low-ISO indoor HDR scene gate"
echo "  - selective lower-mid lift"
echo "  - earlier highlight compression"
echo "  - scene-gated Motion luma/ESD detail preservation"
echo "  - Night behavior unchanged"
echo "  - merge contribution logic unchanged"
echo "UI:"
echo "  - collapsed selected mode + Video"
echo "  - tap selected mode expands all choices"
echo "  - selecting Portrait collapses to Portrait + Video"
echo "  - thumbnail and camera switch remain 30dp"
echo "APK: $OUT"
echo "Backup: $WORK"
