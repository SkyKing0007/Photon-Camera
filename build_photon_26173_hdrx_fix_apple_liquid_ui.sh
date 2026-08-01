#!/usr/bin/env bash
set -Eeuo pipefail

cd /workspaces/Photon-Camera

EXPECTED_BRANCH="experimental-effective-stack"
EXPECTED_HEAD="cedc3ab3e39ad49d42523cff7e3711f8baa69a13"
OLD_BUILD="26172"
NEW_BUILD="26173"
STAMP="$(date +%Y%m%d_%H%M%S)"
WORK="/workspaces/Photon-Camera/build_26173_hdrx_fix_apple_liquid_ui_${STAMP}"
BACKUP_BRANCH="backup-before-hdrx-fix-apple-liquid-ui-26173-${STAMP}"
APK_OUT="$WORK/PhotonCamera-0.9726173-hdrx-fix-apple-liquid-ui-debug.apk"
BUILD_LOG="$WORK/build-26173.log"

VERSION="app/version.properties"
CAMERA_FRAGMENT_XML="app/src/main/res/layout/camera_fragment.xml"
BOTTOMBAR_XML="app/src/main/res/layout/layout_main_bottombar.xml"
BOTTOMBUTTONS_XML="app/src/main/res/layout/layout_bottombuttons.xml"
MODESWITCHER_XML="app/src/main/res/layout/layout_modeswitcher.xml"
TOPBAR_XML="app/src/main/res/layout/layout_main_topbar.xml"

CAMERA_UI="app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java"
CAMERA_CONTROLLER="app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIController.java"
CAMERA_FRAGMENT="app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java"
SETTINGS_PROVIDER="app/src/main/java/com/particlesdevs/photoncamera/ui/camera/viewmodel/SettingsBarEntryProvider.java"
SETTINGS_LAYOUT="app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/settingsbar/SettingsBarLayout.java"
SETTINGS_ENTRY_VIEW="app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/settingsbar/SettingsBarEntryView.java"
CUSTOM_BINDING="app/src/main/java/com/particlesdevs/photoncamera/ui/camera/binding/CustomBinding.java"
LIQUID_MODE_PICKER="app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/modeswitcher/LiquidModePicker.java"

PYRAMID="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/scripts/PyramidMerging.java"
HDRX="app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java"
PARAMS="app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java"
NOISE="app/src/main/java/com/particlesdevs/photoncamera/processing/render/NoiseModeler.java"
POST="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java"
MOTION_SHADER="app/src/main/assets/shaders/merge/motionmerge11.glsl"
INIT_SHADER="app/src/main/assets/shaders/merge/contributioninit.glsl"

mkdir -p "$WORK/before" "$WORK/after"

fail() {
    echo
    echo "============================================================"
    echo " BUILD 26173 STOPPED"
    echo "============================================================"
    echo "Reason: $1"
    echo "No Gradle build was started after this failure."
    exit 1
}

echo "============================================================"
echo " PhotonCamera 0.9726173 — HDRX fix + Apple-inspired liquid UI"
echo "============================================================"
echo "Branch required: $EXPECTED_BRANCH"
echo "Base HEAD:       $EXPECTED_HEAD"
echo "Current build:   $OLD_BUILD"
echo "New build:       $NEW_BUILD"
echo

[ "$(git branch --show-current)" = "$EXPECTED_BRANCH" ] || fail "Wrong branch"
[ "$(git rev-parse HEAD)" = "$EXPECTED_HEAD" ] || fail "Unexpected base HEAD"
grep -q "^VERSION_BUILD=${OLD_BUILD}$" "$VERSION" || fail "Expected VERSION_BUILD=${OLD_BUILD}"

echo "Verifying audited UI source checkpoint..."

verify_hash() {
    local expected="$1"
    local file="$2"
    [ -f "$file" ] || fail "Missing source file: $file"
    local actual
    actual="$(sha256sum "$file" | awk '{print $1}')"
    [ "$actual" = "$expected" ] || fail "Audited source changed: $file"
}

verify_hash "cf10b6a8456a4d437e50a80fd881ff2598e871232901e8f09db6fb6a65fde65f" "$CAMERA_FRAGMENT_XML"
verify_hash "b89479bee738ed3bdf65d7f7bbac940ce7e8a609f3bed92ee15a4576149be86b" "$CAMERA_UI"
verify_hash "fec596bc27be69473b6573733a90e94a868844a91200a3e63bebfa91ccb89b2b" "$CAMERA_CONTROLLER"
verify_hash "50dcc6c5e57f39df924bdb493186ba207d1e3228c6fb262935b4376d3e8b1042" "$CAMERA_FRAGMENT"
verify_hash "424ea56872b7f7775eef3492e232bfcc44b135cd0667bdfdde089f9dee9be6ad" "$SETTINGS_PROVIDER"
verify_hash "01a504a86364a35ca157490f47ab4ecf77918adbb6e748d00fdfe9b831942dba" "$SETTINGS_LAYOUT"
verify_hash "793aac7bb1023016e31ff33bed92e45bfe972e5866c6bf4795a21d820c7b1fc5" "$SETTINGS_ENTRY_VIEW"
verify_hash "e6ec32edb22a72f9e067c44dd30d4a185009ca60feb030fedd66af6ea3fc4831" "$CUSTOM_BINDING"

grep -Fq 'android:id="@+id/layout_bottombar"' "$BOTTOMBAR_XML" || fail "Bottom bar source context missing"
grep -Fq 'android:id="@+id/shutter_button"' "$BOTTOMBUTTONS_XML" || fail "Bottom buttons source context missing"
grep -Fq 'android:id="@+id/mode_picker_view"' "$MODESWITCHER_XML" || fail "Mode switcher source context missing"
grep -Fq 'android:id="@+id/settings_button"' "$TOPBAR_XML" || fail "Top bar source context missing"

echo "Verifying protected 26172 processing payloads..."
verify_hash "c9d04e25111921936faddbfa65a6c48ed6b4b295c6941eaad7d25441597ce75e" "$PYRAMID"
verify_hash "201a7e3938d36c4a42101374c46051b1d0ad7794e65009a653d9219ba3a1ef39" "$HDRX"
verify_hash "1c3f43bcf4733c3fac6fd0dcd88f8e645c9fd122589cdd170cd85ccf8ae1ff1c" "$PARAMS"
verify_hash "7a6c9beba00891bdc19f581e194b3cd1271cfa89b4c73ba3c0d8869d0100519e" "$NOISE"
verify_hash "99ef221fef9dbf1e1781a2fb0701e4fa8a78dba03c103f39e84bbf5ab5e0f8cc" "$POST"
verify_hash "c1bb9bd42df33624a139ac664c71fef9e640fff6064bbb37d2d24f8eb0fc69d8" "$MOTION_SHADER"
verify_hash "4cf84898efa241ffb1fe60daea554ce23b0f91f1f0ae5a00b785525098cb6123" "$INIT_SHADER"

echo "Creating backup branch and complete patch before modification..."
git branch "$BACKUP_BRANCH"
git status --short > "$WORK/status-before.txt"
git diff --binary > "$WORK/working-tree-before-26173.patch"
git diff --cached --binary > "$WORK/index-before-26173.patch"

for file in \
    "$VERSION" \
    "$CAMERA_FRAGMENT_XML" \
    "$BOTTOMBAR_XML" \
    "$BOTTOMBUTTONS_XML" \
    "$MODESWITCHER_XML" \
    "$TOPBAR_XML" \
    "$CAMERA_UI" \
    "$CAMERA_CONTROLLER" \
    "$CAMERA_FRAGMENT" \
    "$SETTINGS_PROVIDER" \
    "$SETTINGS_LAYOUT" \
    "$SETTINGS_ENTRY_VIEW" \
    "$CUSTOM_BINDING" \
    "$PYRAMID" \
    "$HDRX" \
    "$PARAMS" \
    "$NOISE" \
    "$POST" \
    "$MOTION_SHADER" \
    "$INIT_SHADER"; do
    mkdir -p "$WORK/before/$(dirname "$file")"
    cp "$file" "$WORK/before/$file"
done

echo "Backup branch: $BACKUP_BRANCH"
echo "Backup patch:  $WORK/working-tree-before-26173.patch"
echo

echo "Applying GLSL ES 3.10-compatible Motion contribution storage fix..."

python3 - <<'PY'
from pathlib import Path

pyramid_path = Path(
    "app/src/main/java/com/particlesdevs/photoncamera/"
    "processing/opengl/scripts/PyramidMerging.java"
)
motion_shader_path = Path(
    "app/src/main/assets/shaders/merge/motionmerge11.glsl"
)
init_shader_path = Path(
    "app/src/main/assets/shaders/merge/contributioninit.glsl"
)

pyramid = pyramid_path.read_text()

old_texture = '''                            new GLFormat(
                                    GLFormat.DataType.FLOAT_16,
                                    1
                            ),
'''

new_texture = '''                            /*
                             * Build 26173:
                             *
                             * GLSL ES 3.10 does not permit r16f as an image
                             * format qualifier. Use the core-supported r32f
                             * single-channel image format instead.
                             */
                            new GLFormat(
                                    GLFormat.DataType.FLOAT_32,
                                    1
                            ),
'''

if pyramid.count(old_texture) != 1:
    raise SystemExit(
        "ERROR: expected one Motion contribution FLOAT_16 texture block, found "
        + str(pyramid.count(old_texture))
    )

pyramid = pyramid.replace(old_texture, new_texture, 1)

old_marker = '''                            + " adaptiveNoiseSettingUnchanged=true"
'''

new_marker = '''                            + " storageFormat=R32F"
                            + " glslEs310Compatible=true"
                            + " adaptiveNoiseSettingUnchanged=true"
'''

if pyramid.count(old_marker) != 1:
    raise SystemExit(
        "ERROR: expected one contribution tracking marker tail, found "
        + str(pyramid.count(old_marker))
    )

pyramid = pyramid.replace(old_marker, new_marker, 1)
pyramid_path.write_text(pyramid)

motion_shader = motion_shader_path.read_text()
old_motion_layout = "layout(r16f, binding = 4) uniform highp image2D contributionTexture;"
new_motion_layout = "layout(r32f, binding = 4) uniform highp image2D contributionTexture;"

if motion_shader.count(old_motion_layout) != 1:
    raise SystemExit(
        "ERROR: expected one r16f Motion contribution binding, found "
        + str(motion_shader.count(old_motion_layout))
    )

motion_shader_path.write_text(
    motion_shader.replace(
        old_motion_layout,
        new_motion_layout,
        1,
    )
)

init_shader = init_shader_path.read_text()
old_init_layout = "layout(r16f, binding = 0) uniform highp writeonly image2D outTexture;"
new_init_layout = "layout(r32f, binding = 0) uniform highp writeonly image2D outTexture;"

if init_shader.count(old_init_layout) != 1:
    raise SystemExit(
        "ERROR: expected one r16f contribution initializer binding, found "
        + str(init_shader.count(old_init_layout))
    )

init_shader_path.write_text(
    init_shader.replace(
        old_init_layout,
        new_init_layout,
        1,
    )
)
PY

grep -Fq 'GLFormat.DataType.FLOAT_32' "$PYRAMID" \
    || fail "R32F Java texture storage was not applied"

grep -Fq 'storageFormat=R32F' "$PYRAMID" \
    || fail "R32F runtime marker was not added"

grep -Fq 'layout(r32f, binding = 4)' "$MOTION_SHADER" \
    || fail "Motion merge shader was not changed to r32f"

grep -Fq 'layout(r32f, binding = 0)' "$INIT_SHADER" \
    || fail "Contribution initializer was not changed to r32f"

if grep -Fq 'layout(r16f' "$MOTION_SHADER" "$INIT_SHADER"; then
    fail "Invalid GLSL ES r16f image qualifier remains"
fi

cat > "$CAMERA_FRAGMENT_XML" <<'EOF'
<?xml version="1.0" encoding="utf-8"?>
<layout xmlns:android="http://schemas.android.com/apk/res/android"
        xmlns:app="http://schemas.android.com/apk/res-auto"
        xmlns:tools="http://schemas.android.com/tools">
    <data>
        <import type="android.view.View"/>
        <variable
                name="uimodel"
                type="com.particlesdevs.photoncamera.ui.camera.model.CameraFragmentModel" />
        <variable
                name="auxmodel"
                type="com.particlesdevs.photoncamera.ui.camera.model.AuxButtonsModel" />
    </data>

    <androidx.constraintlayout.widget.ConstraintLayout
            android:id="@+id/textureHolder"
            android:layout_width="match_parent"
            android:layout_height="match_parent"
            android:background="#FF000000"
            android:clipChildren="false"
            android:clipToPadding="false">

        <View
                android:id="@+id/top_black_shell"
                android:layout_width="0dp"
                android:layout_height="72dp"
                android:background="#FF000000"
                app:layout_constraintTop_toTopOf="parent"
                app:layout_constraintStart_toStartOf="parent"
                app:layout_constraintEnd_toEndOf="parent" />

        <LinearLayout
                android:id="@+id/format_selector_pill"
                android:layout_width="wrap_content"
                android:layout_height="48dp"
                android:minWidth="72dp"
                android:orientation="horizontal"
                android:gravity="center"
                android:paddingStart="16dp"
                android:paddingEnd="12dp"
                android:background="@drawable/liquid_glass_pill"
                android:clickable="true"
                android:focusable="true"
                android:elevation="8dp"
                android:contentDescription="Image format and Quad Bayer status"
                app:layout_constraintStart_toStartOf="parent"
                app:layout_constraintTop_toTopOf="parent"
                android:layout_marginStart="12dp"
                android:layout_marginTop="12dp">

            <TextView
                    android:id="@+id/format_active_label"
                    android:layout_width="wrap_content"
                    android:layout_height="wrap_content"
                    android:text="JPG"
                    android:textColor="#FFFFFFFF"
                    android:textSize="13sp"
                    android:textStyle="bold"
                    android:letterSpacing="0.04"
                    tools:ignore="HardcodedText" />

            <LinearLayout
                    android:id="@+id/quad_status_container"
                    android:layout_width="wrap_content"
                    android:layout_height="match_parent"
                    android:orientation="horizontal"
                    android:gravity="center"
                    android:visibility="gone"
                    android:layout_marginStart="10dp">

                <ImageView
                        android:layout_width="18dp"
                        android:layout_height="18dp"
                        android:src="@drawable/ic_quad_status"
                        android:contentDescription="Quad Bayer resolution enabled"
                        app:tint="#FFFFD60A" />

                <TextView
                        android:id="@+id/quad_status_label"
                        android:layout_width="wrap_content"
                        android:layout_height="wrap_content"
                        android:layout_marginStart="5dp"
                        android:text="48/64MP"
                        android:textColor="#FFFFD60A"
                        android:textSize="11sp"
                        android:textStyle="bold"
                        tools:ignore="HardcodedText" />
            </LinearLayout>
        </LinearLayout>

        <include
                android:id="@+id/layout_topbar"
                layout="@layout/layout_main_topbar"
                android:layout_width="wrap_content"
                android:layout_height="56dp"
                app:adjustTopBar="@{uimodel.screenAspectRatio}"
                app:layout_constraintTop_toTopOf="parent"
                app:layout_constraintEnd_toEndOf="parent"
                android:layout_marginTop="8dp"
                android:layout_marginEnd="10dp"
                android:visibility="visible" />

        <LinearLayout
                android:id="@+id/format_expanded_panel"
                android:layout_width="152dp"
                android:layout_height="wrap_content"
                android:orientation="vertical"
                android:padding="6dp"
                android:background="@drawable/liquid_glass_panel"
                android:elevation="14dp"
                android:visibility="gone"
                app:layout_constraintTop_toBottomOf="@id/format_selector_pill"
                app:layout_constraintStart_toStartOf="@id/format_selector_pill"
                android:layout_marginTop="8dp">

            <TextView
                    android:id="@+id/format_jpg_button"
                    style="@style/LiquidGlassMenuText"
                    android:text="JPG"
                    tools:ignore="HardcodedText" />

            <TextView
                    android:id="@+id/format_raw_button"
                    style="@style/LiquidGlassMenuText"
                    android:text="RAW"
                    tools:ignore="HardcodedText" />

            <TextView
                    android:id="@+id/format_raw_jpg_button"
                    style="@style/LiquidGlassMenuText"
                    android:text="JPG + RAW"
                    tools:ignore="HardcodedText" />

            <TextView
                    android:id="@+id/quad_status_toggle_button"
                    style="@style/LiquidGlassMenuText"
                    android:text="QUAD 48/64MP"
                    android:visibility="gone"
                    tools:ignore="HardcodedText" />
        </LinearLayout>

        <androidx.constraintlayout.widget.ConstraintLayout
                android:id="@+id/camera_container"
                android:layout_width="0dp"
                android:layout_height="0dp"
                android:background="#FF000000"
                android:clipChildren="false"
                android:clipToPadding="false"
                app:adjustCameraContainer="@{uimodel.screenAspectRatio}"
                app:layout_constraintTop_toBottomOf="@id/top_black_shell"
                app:layout_constraintBottom_toBottomOf="parent"
                app:layout_constraintStart_toStartOf="parent"
                app:layout_constraintEnd_toEndOf="parent">

            <include
                    android:id="@+id/layout_viewfinder"
                    layout="@layout/layout_main_viewfinder"
                    android:layout_width="0dp"
                    android:layout_height="0dp"
                    app:layout_constraintTop_toTopOf="parent"
                    app:layout_constraintBottom_toBottomOf="parent"
                    app:layout_constraintStart_toStartOf="parent"
                    app:layout_constraintEnd_toEndOf="parent" />

            <FrameLayout
                    android:id="@+id/dummy_reference_view"
                    android:layout_width="match_parent"
                    android:layout_height="0dp"
                    android:clickable="false"
                    app:setAspectRatio="@{uimodel.dummyAspectRatio}"
                    app:layout_constraintTop_toTopOf="parent"
                    app:layout_constraintStart_toStartOf="parent"
                    app:layout_constraintEnd_toEndOf="parent" />

            <include
                    android:id="@+id/layout_bottombar"
                    layout="@layout/layout_main_bottombar"
                    android:layout_width="0dp"
                    android:layout_height="160dp"
                    app:layout_constraintBottom_toBottomOf="parent"
                    app:layout_constraintStart_toStartOf="parent"
                    app:layout_constraintEnd_toEndOf="parent" />

            <com.particlesdevs.photoncamera.ui.camera.views.AuxButtonsLayout
                    android:id="@+id/aux_buttons_container"
                    android:layout_width="wrap_content"
                    android:layout_height="48dp"
                    android:orientation="horizontal"
                    android:gravity="center"
                    android:paddingStart="6dp"
                    android:paddingEnd="6dp"
                    android:background="@drawable/liquid_glass_pill"
                    android:elevation="10dp"
                    setAuxButtonModel="@{auxmodel}"
                    setActiveId="@{auxmodel.currentCameraId}"
                    bindViewGroupChildrenRotate="@{uimodel}"
                    app:layout_constraintBottom_toTopOf="@id/layout_bottombar"
                    app:layout_constraintStart_toStartOf="parent"
                    app:layout_constraintEnd_toEndOf="parent"
                    android:layout_marginBottom="4dp" />

            <include
                    android:id="@+id/manual_mode"
                    layout="@layout/manual_palette"
                    android:layout_width="0dp"
                    android:layout_height="wrap_content"
                    app:layout_constraintBottom_toTopOf="@id/layout_bottombar"
                    app:layout_constraintStart_toStartOf="parent"
                    app:layout_constraintEnd_toEndOf="parent"
                    tools:visibility="gone" />

            <ImageView
                    android:id="@+id/open_close_manual"
                    android:layout_width="1dp"
                    android:layout_height="1dp"
                    android:visibility="invisible"
                    android:contentDescription="Manual controls compatibility anchor"
                    app:layout_constraintBottom_toTopOf="@id/layout_bottombar"
                    app:layout_constraintStart_toStartOf="parent"
                    app:layout_constraintEnd_toEndOf="parent" />

            <com.particlesdevs.photoncamera.ui.camera.views.settingsbar.SettingsBarLayout
                    android:id="@+id/settings_bar"
                    android:layout_width="0dp"
                    android:layout_height="0dp"
                    android:layout_marginStart="12dp"
                    android:layout_marginEnd="12dp"
                    android:layout_marginTop="12dp"
                    android:layout_marginBottom="12dp"
                    android:background="@drawable/liquid_glass_panel"
                    android:elevation="18dp"
                    app:layout_constraintHeight_max="420dp"
                    app:layout_constraintTop_toTopOf="parent"
                    app:layout_constraintBottom_toTopOf="@id/layout_bottombar"
                    app:layout_constraintStart_toStartOf="parent"
                    app:layout_constraintEnd_toEndOf="parent"
                    settingsBarVisibility="@{uimodel.settingsBarVisibility}"
                    bindRotate="@{uimodel}" />
        </androidx.constraintlayout.widget.ConstraintLayout>

        <TextView
                android:id="@+id/video_recording_info"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_marginTop="12dp"
                android:layout_marginEnd="12dp"
                android:textColor="@android:color/white"
                android:textSize="13sp"
                android:fontFamily="monospace"
                android:background="@drawable/liquid_glass_pill"
                android:paddingStart="8dp"
                android:paddingEnd="8dp"
                android:paddingTop="4dp"
                android:paddingBottom="4dp"
                android:visibility="gone"
                app:layout_constraintTop_toBottomOf="@id/top_black_shell"
                app:layout_constraintEnd_toEndOf="parent" />

    </androidx.constraintlayout.widget.ConstraintLayout>
</layout>
EOF

cat > "$BOTTOMBAR_XML" <<'EOF'
<?xml version="1.0" encoding="utf-8"?>
<layout xmlns:android="http://schemas.android.com/apk/res/android"
        xmlns:app="http://schemas.android.com/apk/res-auto">

    <androidx.constraintlayout.widget.ConstraintLayout
            android:id="@+id/layout_bottombar"
            android:layout_width="match_parent"
            android:layout_height="160dp"
            android:background="#F6000000"
            android:clipChildren="false"
            android:clipToPadding="false">

        <androidx.constraintlayout.widget.Guideline
                android:id="@+id/mode_start_guide"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:orientation="vertical"
                app:layout_constraintGuide_percent="0.27" />

        <androidx.constraintlayout.widget.Guideline
                android:id="@+id/mode_end_guide"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:orientation="vertical"
                app:layout_constraintGuide_percent="0.73" />

        <include
                android:id="@+id/bottom_buttons"
                layout="@layout/layout_bottombuttons"
                android:layout_width="0dp"
                android:layout_height="0dp"
                app:layout_constraintTop_toTopOf="parent"
                app:layout_constraintBottom_toBottomOf="parent"
                app:layout_constraintStart_toStartOf="parent"
                app:layout_constraintEnd_toEndOf="parent" />

        <include
                android:id="@+id/mode_switcher"
                layout="@layout/layout_modeswitcher"
                android:layout_width="0dp"
                android:layout_height="52dp"
                android:layout_marginBottom="10dp"
                app:layout_constraintStart_toStartOf="@id/mode_start_guide"
                app:layout_constraintEnd_toEndOf="@id/mode_end_guide"
                app:layout_constraintBottom_toBottomOf="parent" />
    </androidx.constraintlayout.widget.ConstraintLayout>
</layout>
EOF

cat > "$BOTTOMBUTTONS_XML" <<'EOF'
<?xml version="1.0" encoding="utf-8"?>
<layout xmlns:android="http://schemas.android.com/apk/res/android"
        xmlns:app="http://schemas.android.com/apk/res-auto"
        xmlns:tools="http://schemas.android.com/tools">

    <data>
        <variable
                name="bottom_bar_click_listener"
                type="android.view.View.OnClickListener"/>
        <variable
                name="uimodel"
                type="com.particlesdevs.photoncamera.ui.camera.model.CameraFragmentModel"/>
        <variable
                name="timermodel"
                type="com.particlesdevs.photoncamera.ui.camera.model.TimerFrameCountModel"/>
    </data>

    <androidx.constraintlayout.widget.ConstraintLayout
            android:layout_width="match_parent"
            android:layout_height="match_parent"
            android:clipChildren="false"
            android:clipToPadding="false">

        <FrameLayout
                android:id="@+id/shutter_button_container"
                android:layout_width="88dp"
                android:layout_height="88dp"
                android:background="@drawable/liquid_shutter_outer"
                android:elevation="12dp"
                app:layout_constraintTop_toTopOf="parent"
                app:layout_constraintStart_toStartOf="parent"
                app:layout_constraintEnd_toEndOf="parent"
                android:layout_marginTop="4dp">

            <ImageButton
                    android:id="@+id/shutter_button"
                    android:layout_width="match_parent"
                    android:layout_height="match_parent"
                    android:layout_gravity="center"
                    android:background="@drawable/roundbutton"
                    android:clickable="true"
                    android:contentDescription="Shutter Button"
                    android:onClick="@{bottom_bar_click_listener}"
                    android:scaleX="0.78"
                    android:scaleY="0.78"
                    tools:ignore="HardcodedText"/>

            <ProgressBar
                    android:id="@+id/processing_progress_bar"
                    style="@style/Widget.AppCompat.ProgressBar.Horizontal"
                    android:layout_width="match_parent"
                    android:layout_height="match_parent"
                    android:indeterminate="false"
                    android:max="100"
                    android:progressDrawable="@drawable/circular_progress_bar2"
                    android:indeterminateDrawable="@drawable/circular_progress_bar2"
                    android:interpolator="@android:anim/accelerate_decelerate_interpolator"
                    android:scaleX="1.18"
                    android:scaleY="1.18"
                    tools:progress="50"/>

            <TextView
                    android:id="@+id/frameCount"
                    android:layout_width="wrap_content"
                    android:layout_height="wrap_content"
                    android:layout_gravity="center"
                    android:text="@{timermodel.frameCount}"
                    android:textColor="@android:color/white"
                    android:textSize="30sp"
                    android:textAlignment="center"
                    android:visibility="visible"
                    tools:text="20"/>
        </FrameLayout>

        <FrameLayout
                android:id="@+id/galery_button_container"
                android:layout_width="52dp"
                android:layout_height="52dp"
                android:background="@drawable/liquid_glass_icon_button"
                android:elevation="8dp"
                app:layout_constraintStart_toStartOf="parent"
                app:layout_constraintBottom_toBottomOf="parent"
                android:layout_marginStart="12dp"
                android:layout_marginBottom="10dp">

            <de.hdodenhof.circleimageview.CircleImageView
                    android:id="@+id/gallery_image_button"
                    android:layout_width="44dp"
                    android:layout_height="44dp"
                    android:layout_gravity="center"
                    android:background="@drawable/round"
                    android:onClick="@{bottom_bar_click_listener}"
                    imageFromBitmap="@{uimodel.bitmap}"
                    bindRotate="@{uimodel}"
                    app:civ_border_color="#AAFFFFFF"
                    app:civ_border_overlay="true"
                    app:civ_border_width="2dp"/>
        </FrameLayout>

        <FrameLayout
                android:id="@+id/camera_switch_container"
                android:layout_width="52dp"
                android:layout_height="52dp"
                android:background="@drawable/liquid_glass_icon_button"
                android:elevation="8dp"
                app:layout_constraintEnd_toEndOf="parent"
                app:layout_constraintBottom_toBottomOf="parent"
                android:layout_marginEnd="12dp"
                android:layout_marginBottom="10dp">

            <ImageButton
                    android:id="@+id/flip_camera_button"
                    android:layout_width="44dp"
                    android:layout_height="44dp"
                    android:layout_gravity="center"
                    android:background="@android:color/transparent"
                    android:clickable="true"
                    android:onClick="@{bottom_bar_click_listener}"
                    android:contentDescription="Lens Switch Button"
                    android:padding="9dp"
                    android:scaleType="centerInside"
                    android:src="@drawable/ic_flip_camera"
                    app:tint="#FFFFFFFF"/>
        </FrameLayout>
    </androidx.constraintlayout.widget.ConstraintLayout>
</layout>
EOF

cat > "$MODESWITCHER_XML" <<'EOF'
<?xml version="1.0" encoding="utf-8"?>
<layout xmlns:android="http://schemas.android.com/apk/res/android">

    <com.particlesdevs.photoncamera.ui.camera.views.modeswitcher.LiquidModePicker
            android:id="@+id/mode_picker_view"
            android:layout_width="match_parent"
            android:layout_height="match_parent"
            android:contentDescription="Camera mode selector"
            android:focusable="true"
            android:clickable="true"/>
</layout>
EOF

cat > "$TOPBAR_XML" <<'EOF'
<?xml version="1.0" encoding="utf-8"?>
<layout xmlns:android="http://schemas.android.com/apk/res/android"
        xmlns:app="http://schemas.android.com/apk/res-auto">

    <data>
        <import type="android.view.View"/>
        <import type="com.particlesdevs.photoncamera.settings.PreferenceKeys"/>

        <variable name="hdrx_visible" type="boolean"/>
        <variable name="eis_visible" type="boolean"/>
        <variable name="fps_visible" type="boolean"/>
        <variable name="quad_visible" type="boolean"/>
        <variable name="flash_visible" type="boolean"/>
        <variable name="timer_visible" type="boolean"/>
        <variable
                name="top_bar_click_listener"
                type="android.view.View.OnClickListener"/>
        <variable
                name="uimodel"
                type="com.particlesdevs.photoncamera.ui.camera.model.CameraFragmentModel"/>
    </data>

    <LinearLayout
            android:layout_width="wrap_content"
            android:layout_height="56dp"
            android:orientation="horizontal"
            android:gravity="center"
            android:clipChildren="false"
            bindViewGroupChildrenRotate="@{uimodel}">

        <FrameLayout
                android:layout_width="48dp"
                android:layout_height="48dp"
                android:layout_marginHorizontal="3dp"
                android:background="@drawable/liquid_glass_icon_button"
                android:visibility="@{timer_visible ? View.VISIBLE : View.GONE}">

            <com.particlesdevs.photoncamera.ui.camera.views.TimerButton
                    android:id="@+id/countdown_timer_button"
                    android:layout_width="40dp"
                    android:layout_height="40dp"
                    android:layout_gravity="center"
                    android:background="@drawable/ic_timer"
                    android:onClick="@{top_bar_click_listener}"
                    android:contentDescription="Countdown timer"/>
        </FrameLayout>

        <FrameLayout
                android:layout_width="48dp"
                android:layout_height="48dp"
                android:layout_marginHorizontal="3dp"
                android:background="@drawable/liquid_glass_icon_button"
                android:visibility="@{flash_visible ? View.VISIBLE : View.GONE}">

            <com.particlesdevs.photoncamera.ui.camera.views.FlashButton
                    android:id="@+id/flash_button"
                    android:layout_width="40dp"
                    android:layout_height="40dp"
                    android:layout_gravity="center"
                    android:background="@drawable/ic_flash"
                    android:onClick="@{top_bar_click_listener}"
                    android:contentDescription="Flash control"/>
        </FrameLayout>

        <FrameLayout
                android:layout_width="48dp"
                android:layout_height="48dp"
                android:layout_marginHorizontal="3dp"
                android:background="@drawable/liquid_glass_icon_button">

            <ImageButton
                    android:id="@+id/settings_button"
                    android:layout_width="40dp"
                    android:layout_height="40dp"
                    android:layout_gravity="center"
                    android:background="@android:color/transparent"
                    android:src="@drawable/ic_settings"
                    android:padding="9dp"
                    android:onClick="@{top_bar_click_listener}"
                    android:contentDescription="More controls"
                    app:tint="#FFFFFFFF"/>
        </FrameLayout>

        <View
                android:id="@+id/hdrx_toggle_button"
                android:layout_width="1dp"
                android:layout_height="1dp"
                android:visibility="@{hdrx_visible ? View.GONE : View.GONE}"/>
        <View
                android:id="@+id/eis_toggle_button"
                android:layout_width="1dp"
                android:layout_height="1dp"
                android:visibility="@{eis_visible ? View.GONE : View.GONE}"/>
        <View
                android:id="@+id/fps_toggle_button"
                android:layout_width="1dp"
                android:layout_height="1dp"
                android:visibility="@{fps_visible ? View.GONE : View.GONE}"/>
        <View
                android:id="@+id/quad_res_toggle_button"
                android:layout_width="1dp"
                android:layout_height="1dp"
                android:visibility="@{quad_visible ? View.GONE : View.GONE}"/>
    </LinearLayout>
</layout>
EOF

mkdir -p app/src/main/res/drawable app/src/main/res/values

cat > app/src/main/res/drawable/liquid_glass_pill.xml <<'EOF'
<?xml version="1.0" encoding="utf-8"?>
<ripple xmlns:android="http://schemas.android.com/apk/res/android"
        android:color="#44FFFFFF">
    <item>
        <shape android:shape="rectangle">
            <gradient
                    android:angle="270"
                    android:startColor="#C42C3038"
                    android:centerColor="#B51A1D23"
                    android:endColor="#99101216"/>
            <stroke
                    android:width="1dp"
                    android:color="#66FFFFFF"/>
            <corners android:radius="28dp"/>
            <padding
                    android:left="1dp"
                    android:top="1dp"
                    android:right="1dp"
                    android:bottom="1dp"/>
        </shape>
    </item>
</ripple>
EOF

cat > app/src/main/res/drawable/liquid_glass_icon_button.xml <<'EOF'
<?xml version="1.0" encoding="utf-8"?>
<ripple xmlns:android="http://schemas.android.com/apk/res/android"
        android:color="#55FFFFFF">
    <item>
        <shape android:shape="oval">
            <gradient
                    android:angle="270"
                    android:startColor="#C7373B45"
                    android:centerColor="#B5242830"
                    android:endColor="#9913161B"/>
            <stroke
                    android:width="1dp"
                    android:color="#70FFFFFF"/>
        </shape>
    </item>
</ripple>
EOF

cat > app/src/main/res/drawable/liquid_glass_panel.xml <<'EOF'
<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android"
       android:shape="rectangle">
    <gradient
            android:angle="270"
            android:startColor="#EA262A32"
            android:centerColor="#E31B1E24"
            android:endColor="#DD0C0E12"/>
    <stroke
            android:width="1dp"
            android:color="#66FFFFFF"/>
    <corners android:radius="26dp"/>
    <padding
            android:left="8dp"
            android:top="8dp"
            android:right="8dp"
            android:bottom="8dp"/>
</shape>
EOF

cat > app/src/main/res/drawable/liquid_shutter_outer.xml <<'EOF'
<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android"
       android:shape="oval">
    <solid android:color="#22000000"/>
    <stroke
            android:width="4dp"
            android:color="#F2FFFFFF"/>
</shape>
EOF

cat > app/src/main/res/drawable/ic_quad_status.xml <<'EOF'
<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
        android:width="24dp"
        android:height="24dp"
        android:viewportWidth="24"
        android:viewportHeight="24">
    <path android:fillColor="#FFFFFFFF" android:pathData="M3,3h7v7h-7z"/>
    <path android:fillColor="#FFFFFFFF" android:pathData="M14,3h7v7h-7z"/>
    <path android:fillColor="#FFFFFFFF" android:pathData="M3,14h7v7h-7z"/>
    <path android:fillColor="#FFFFFFFF" android:pathData="M14,14h7v7h-7z"/>
</vector>
EOF

python3 - <<'PY'
from pathlib import Path

styles = Path("app/src/main/res/values/styles.xml")
text = styles.read_text()
marker = "</resources>"
addition = r'''
    <style name="LiquidGlassMenuText">
        <item name="android:layout_width">match_parent</item>
        <item name="android:layout_height">44dp</item>
        <item name="android:gravity">center_vertical</item>
        <item name="android:paddingStart">14dp</item>
        <item name="android:paddingEnd">14dp</item>
        <item name="android:textColor">#FFFFFFFF</item>
        <item name="android:textSize">13sp</item>
        <item name="android:textStyle">bold</item>
        <item name="android:letterSpacing">0.03</item>
        <item name="android:background">@drawable/liquid_glass_pill</item>
        <item name="android:layout_marginBottom">5dp</item>
        <item name="android:clickable">true</item>
        <item name="android:focusable">true</item>
    </style>
'''
if 'name="LiquidGlassMenuText"' in text:
    raise SystemExit("LiquidGlassMenuText already exists")
if marker not in text:
    raise SystemExit("styles.xml resources close marker missing")
styles.write_text(text.replace(marker, addition + "\n" + marker))
PY

mkdir -p "$(dirname "$LIQUID_MODE_PICKER")"
cat > "$LIQUID_MODE_PICKER" <<'EOF'
package com.particlesdevs.photoncamera.ui.camera.views.modeswitcher;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.RectF;
import android.util.AttributeSet;
import android.util.TypedValue;

import com.particlesdevs.photoncamera.ui.camera.views.modeswitcher.wefika.horizontalpicker.HorizontalPicker;

/**
 * Compact Motion/Video-first mode selector.
 *
 * The inherited HorizontalPicker still provides all scrolling, snapping,
 * accessibility and haptic behavior. This class only replaces the drawing
 * layer with a compact glass strip that shows Motion and Video at rest while
 * the remaining modes stay reachable by horizontal swiping.
 */
public class LiquidModePicker extends HorizontalPicker {
    private final Paint glassPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint borderPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint selectionPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint textPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final RectF bounds = new RectF();
    private final RectF selection = new RectF();

    public LiquidModePicker(Context context) {
        this(context, null);
    }

    public LiquidModePicker(Context context, AttributeSet attrs) {
        super(context, attrs);
        setSideItems(0);
        setOverScrollMode(OVER_SCROLL_NEVER);
        setLayerType(LAYER_TYPE_SOFTWARE, null);

        glassPaint.setColor(Color.argb(206, 24, 27, 33));
        glassPaint.setShadowLayer(dp(10), 0, dp(3), Color.argb(105, 0, 0, 0));

        borderPaint.setStyle(Paint.Style.STROKE);
        borderPaint.setStrokeWidth(dp(1));
        borderPaint.setColor(Color.argb(105, 255, 255, 255));

        selectionPaint.setColor(Color.argb(225, 255, 255, 255));

        textPaint.setTextAlign(Paint.Align.CENTER);
        textPaint.setTypeface(android.graphics.Typeface.create(
                android.graphics.Typeface.DEFAULT, android.graphics.Typeface.BOLD));
        textPaint.setTextSize(sp(12));
    }

    @Override
    protected void onDraw(Canvas canvas) {
        final int width = getWidth();
        final int height = getHeight();
        if (width <= 0 || height <= 0) return;

        float inset = dp(1);
        float radius = height / 2f;
        bounds.set(inset, inset, width - inset, height - inset);
        canvas.drawRoundRect(bounds, radius, radius, glassPaint);
        canvas.drawRoundRect(bounds, radius, radius, borderPaint);

        CharSequence[] labels = getValues();
        if (labels == null || labels.length == 0) return;

        float rawPosition = (float) getScrollX() / Math.max(1, width);
        int selected = Math.max(0, Math.min(labels.length - 1, Math.round(rawPosition)));
        float baseline = height / 2f - (textPaint.ascent() + textPaint.descent()) / 2f;

        if (rawPosition <= 1.15f && labels.length >= 2) {
            float progress = Math.max(0f, Math.min(1f, rawPosition));
            float half = width / 2f;
            float pad = dp(4);
            float selectedLeft = pad + progress * half;
            selection.set(selectedLeft, pad, selectedLeft + half - pad * 2f, height - pad);
            canvas.drawRoundRect(selection, radius, radius, selectionPaint);

            drawLabel(canvas, labels[0].toString(), half * 0.5f, baseline,
                    progress < 0.5f ? 0xFFFFD60A : 0xD9FFFFFF);
            drawLabel(canvas, labels[1].toString(), half * 1.5f, baseline,
                    progress >= 0.5f ? 0xFFFFD60A : 0xD9FFFFFF);
        } else {
            float pad = dp(4);
            selection.set(pad, pad, width - pad, height - pad);
            canvas.drawRoundRect(selection, radius, radius, selectionPaint);
            drawLabel(canvas, labels[selected].toString(), width / 2f, baseline, 0xFFFFD60A);

            textPaint.setTextSize(sp(15));
            textPaint.setColor(0x99FFFFFF);
            canvas.drawText("‹", dp(14), baseline, textPaint);
            canvas.drawText("›", width - dp(14), baseline, textPaint);
            textPaint.setTextSize(sp(12));
        }
    }

    private void drawLabel(Canvas canvas, String text, float x, float baseline, int color) {
        textPaint.setColor(color);
        canvas.drawText(text, x, baseline, textPaint);
    }

    private float dp(float value) {
        return TypedValue.applyDimension(
                TypedValue.COMPLEX_UNIT_DIP, value, getResources().getDisplayMetrics());
    }

    private float sp(float value) {
        return TypedValue.applyDimension(
                TypedValue.COMPLEX_UNIT_SP, value, getResources().getDisplayMetrics());
    }
}
EOF

python3 - <<'PY'
from pathlib import Path

def replace_once(path, old, new, label):
    p = Path(path)
    text = p.read_text()
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one match, found {count}")
    p.write_text(text.replace(old, new, 1))

path = "app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java"

replace_once(
    path,
    "import android.view.View;\nimport android.widget.ImageButton;\nimport android.widget.ProgressBar;\n",
    "import android.view.MotionEvent;\nimport android.view.View;\nimport android.widget.ImageButton;\nimport android.widget.ProgressBar;\n",
    "CameraUIViewImpl imports"
)

replace_once(
    path,
    '    private static final String TAG = "CameraUIView";\n',
    '''    private static final String TAG = "CameraUIView";
    private static final CameraMode[] MODE_DISPLAY_ORDER = {
            CameraMode.MOTION,
            CameraMode.VIDEO,
            CameraMode.PHOTO,
            CameraMode.NIGHT,
            CameraMode.RAWVIDEO,
            CameraMode.UNLIMITED
    };
''',
    "CameraUIViewImpl display order"
)

replace_once(
    path,
    '''    private final TextView mVideoRecordingInfo;
    private LayoutMainTopbarBinding topbar;
''',
    '''    private final TextView mVideoRecordingInfo;
    private View formatSelectorPill;
    private View formatExpandedPanel;
    private View quadStatusContainer;
    private View quadStatusToggleButton;
    private TextView formatActiveLabel;
    private TextView quadStatusLabel;
    private boolean formatPanelOpen;
    private LayoutMainTopbarBinding topbar;
''',
    "CameraUIViewImpl fields"
)

replace_once(
    path,
    '''        this.initListeners();
        this.initModeSwitcher();
        this.currentState = new PhotoMotionModeState(); //init mode
''',
    '''        this.initListeners();
        this.initModeSwitcher();
        this.initLiquidUi();
        this.currentState = new PhotoMotionModeState(); //init mode
''',
    "CameraUIViewImpl constructor"
)

replace_once(
    path,
    '''    private void initModeSwitcher() {
        this.mModePicker.setValues(Arrays.stream(CameraMode.nameIds()).map(cameraFragment.activity::getString).toArray(String[]::new));
        this.mModePicker.setOverScrollMode(View.OVER_SCROLL_NEVER);
        this.mModePicker.setOnItemSelectedListener(index -> switchToMode(CameraMode.valueOf(index)));
        this.mModePicker.setSelectedItem(PreferenceKeys.getCameraModeOrdinal());
    }

''',
    '''    private void initModeSwitcher() {
        int[] modeNameIds = CameraMode.nameIds();
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

    private void initLiquidUi() {
        View root = cameraFragment.cameraFragmentBinding.getRoot();
        formatSelectorPill = root.findViewById(R.id.format_selector_pill);
        formatExpandedPanel = root.findViewById(R.id.format_expanded_panel);
        quadStatusContainer = root.findViewById(R.id.quad_status_container);
        quadStatusToggleButton = root.findViewById(R.id.quad_status_toggle_button);
        formatActiveLabel = root.findViewById(R.id.format_active_label);
        quadStatusLabel = root.findViewById(R.id.quad_status_label);

        View formatJpg = root.findViewById(R.id.format_jpg_button);
        View formatRaw = root.findViewById(R.id.format_raw_button);
        View formatRawJpg = root.findViewById(R.id.format_raw_jpg_button);
        View manualControls = root.findViewById(R.id.manual_controls_button);

        formatSelectorPill.setOnClickListener(v -> toggleFormatPanel());
        formatJpg.setOnClickListener(v -> selectFormat(0));
        formatRawJpg.setOnClickListener(v -> selectFormat(1));
        formatRaw.setOnClickListener(v -> selectFormat(2));
        quadStatusToggleButton.setOnClickListener(v -> {
            if (uiEventsListener != null) uiEventsListener.onClick(v);
        });
        if (manualControls != null) {
            manualControls.setOnClickListener(v -> {
                if (uiEventsListener != null) uiEventsListener.onClick(v);
            });
        }

        installPressAnimation(
                formatSelectorPill,
                formatJpg,
                formatRaw,
                formatRawJpg,
                quadStatusToggleButton,
                topbar.countdownTimerButton,
                topbar.flashButton,
                topbar.settingsButton,
                bottombuttons.galleryImageButton,
                bottombuttons.flipCameraButton,
                bottombuttons.shutterButton
        );
        refreshFormatStatus();
    }

    private void installPressAnimation(View... views) {
        for (View view : views) {
            if (view == null) continue;
            view.setOnTouchListener((target, event) -> {
                switch (event.getActionMasked()) {
                    case MotionEvent.ACTION_DOWN:
                        target.animate().scaleX(0.91f).scaleY(0.91f).alpha(0.84f)
                                .setDuration(90).start();
                        break;
                    case MotionEvent.ACTION_UP:
                    case MotionEvent.ACTION_CANCEL:
                        target.animate().scaleX(1f).scaleY(1f).alpha(1f)
                                .setDuration(210).start();
                        break;
                    default:
                        break;
                }
                return false;
            });
        }
    }

    private void toggleFormatPanel() {
        if (formatExpandedPanel == null) return;
        formatPanelOpen = !formatPanelOpen;
        if (formatPanelOpen) {
            refreshFormatStatus();
            formatExpandedPanel.setVisibility(View.VISIBLE);
            formatExpandedPanel.setAlpha(0f);
            formatExpandedPanel.setTranslationY(-12f);
            formatExpandedPanel.setScaleX(0.94f);
            formatExpandedPanel.setScaleY(0.94f);
            formatExpandedPanel.animate()
                    .alpha(1f)
                    .translationY(0f)
                    .scaleX(1f)
                    .scaleY(1f)
                    .setDuration(260)
                    .start();
        } else {
            formatExpandedPanel.animate()
                    .alpha(0f)
                    .translationY(-12f)
                    .scaleX(0.94f)
                    .scaleY(0.94f)
                    .setDuration(190)
                    .withEndAction(() -> formatExpandedPanel.setVisibility(View.GONE))
                    .start();
        }
    }

    private void collapseFormatPanel() {
        if (!formatPanelOpen) return;
        toggleFormatPanel();
    }

    private void selectFormat(int value) {
        PreferenceKeys.setSaveRaw(value);
        refreshFormatStatus();
        collapseFormatPanel();
        cameraFragment.updateSettingsBar();
    }

    private void refreshFormatStatus() {
        if (formatActiveLabel == null) return;
        int saveRaw = PreferenceKeys.isSaveRaw();
        switch (saveRaw) {
            case 2:
                formatActiveLabel.setText("RAW");
                break;
            case 1:
                formatActiveLabel.setText("JPG + RAW");
                break;
            case 0:
            default:
                formatActiveLabel.setText("JPG");
                break;
        }

        boolean quadEnabled = enableQuadRes && PreferenceKeys.isQuadBayerOn();
        if (quadStatusContainer != null) {
            quadStatusContainer.setVisibility(quadEnabled ? View.VISIBLE : View.GONE);
        }
        if (quadStatusLabel != null) {
            quadStatusLabel.setText("48/64MP");
        }
        if (quadStatusToggleButton != null) {
            quadStatusToggleButton.setVisibility(enableQuadRes ? View.VISIBLE : View.GONE);
            if (quadStatusToggleButton instanceof TextView) {
                ((TextView) quadStatusToggleButton).setText(
                        PreferenceKeys.isQuadBayerOn()
                                ? "QUAD 48/64MP  ON"
                                : "QUAD 48/64MP  OFF");
            }
        }
    }

''',
    "CameraUIViewImpl mode and liquid UI"
)

replace_once(
    path,
    '''        this.topbar.setQuadVisible(enableQuadRes);
        cameraFragment.cameraFragmentBinding.invalidateAll();
''',
    '''        this.topbar.setQuadVisible(enableQuadRes);
        refreshFormatStatus();
        cameraFragment.cameraFragmentBinding.invalidateAll();
''',
    "CameraUIViewImpl refresh status"
)
PY

python3 - <<'PY'
from pathlib import Path

def replace_once(path, old, new, label):
    p = Path(path)
    text = p.read_text()
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one match, found {count}")
    p.write_text(text.replace(old, new, 1))

path = "app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIController.java"

replace_once(
    path,
    '''            case R.id.settings_button:
                cameraFragment.launchSettings();
                break;

''',
    '''            case R.id.settings_button: {
                boolean controlsVisible = cameraFragment.cameraFragmentBinding
                        .getUimodel().isSettingsBarVisibility();
                cameraFragment.cameraFragmentBinding
                        .getUimodel().setSettingsBarVisibility(!controlsVisible);
                break;
            }

            case R.id.manual_controls_button:
                cameraFragment.cameraFragmentBinding
                        .getUimodel().setSettingsBarVisibility(false);
                cameraFragment.toggleManualControls();
                break;

            case R.id.quad_status_toggle_button:
                PreferenceKeys.setQuadBayer(!PreferenceKeys.isQuadBayerOn());
                cameraFragment.showSnackBar(
                        cameraFragment.getString(R.string.quad_bayer_toggle_text)
                                + ':' + onOff(PreferenceKeys.isQuadBayerOn()));
                this.restartCamera();
                cameraFragment.updateSettingsBar();
                break;

''',
    "CameraUIController more/manual/quad"
)
PY

python3 - <<'PY'
from pathlib import Path

p = Path("app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java")
text = p.read_text()
anchor = '''    @Override
    public boolean onBackPressed() {
'''
method = '''    void toggleManualControls() {
        if (manualModeConsole.isPanelVisible()) {
            mSwipe.SwipeDown();
        } else {
            mSwipe.SwipeUp();
        }
    }

'''
if text.count(anchor) != 1:
    raise SystemExit("CameraFragment onBackPressed anchor mismatch")
if "void toggleManualControls()" in text:
    raise SystemExit("CameraFragment toggleManualControls already exists")
p.write_text(text.replace(anchor, method + anchor, 1))
PY

python3 - <<'PY'
from pathlib import Path

p = Path("app/src/main/java/com/particlesdevs/photoncamera/ui/camera/viewmodel/SettingsBarEntryProvider.java")
text = p.read_text()
old = '''    public SettingsBarEntryProvider() {
//        allEntries.add(hdrxEntry);
        allEntries.add(flashEntry);
        allEntries.add(timerEntry);
        allEntries.add(saveRawEntry);
        allEntries.add(quadEntry);
        allEntries.add(eisEntry);
        allEntries.add(fpsEntry);
        allEntries.add(gridEntry);
        allEntries.add(batterySaverEntry);
        allEntries.add(bracketingEntry);
        allEntries.add(histogramEntry);
        allEntries.add(aeMeteringEntry);
    }
'''
new = '''    public SettingsBarEntryProvider() {
        // Flash and timer live in the top-right controls.
        // RAW/JPG and Quad Bayer live in the top-left status selector.
        allEntries.add(eisEntry);
        allEntries.add(fpsEntry);
        allEntries.add(gridEntry);
        allEntries.add(batterySaverEntry);
        allEntries.add(bracketingEntry);
        allEntries.add(histogramEntry);
        allEntries.add(aeMeteringEntry);
    }
'''
if text.count(old) != 1:
    raise SystemExit("SettingsBarEntryProvider constructor mismatch")
p.write_text(text.replace(old, new, 1))
PY

python3 - <<'PY'
from pathlib import Path

p = Path("app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/settingsbar/SettingsBarLayout.java")
text = p.read_text()

old_bg = '        setBackgroundResource(R.drawable.exif_background);\n'
new_bg = '        setBackgroundResource(R.drawable.liquid_glass_panel);\n'
if text.count(old_bg) != 1:
    raise SystemExit("SettingsBarLayout background mismatch")
text = text.replace(old_bg, new_bg, 1)

old = '''        ImageButton settingsButton = new ImageButton(context);
        settingsButton.setImageResource(R.drawable.ic_settings);
        settingsButton.setBackgroundResource(getResolvedAttr(context, android.R.attr.selectableItemBackgroundBorderless));
        settingsButton.setPadding(dp(10), dp(5), dp(10), dp(5));
        settingsButton.setOnClickListener(v -> context.startActivity(new Intent(context, SettingsActivity.class)));
        LayoutParams buttonParam = new LayoutParams(dp(35), dp(35));
        buttonParam.setMargins(dp(10), dp(2.5f), dp(20), dp(2.5f));
        settingsButtonContainer.addView(settingsButton, buttonParam);
'''
new = '''        ImageButton manualButton = new ImageButton(context);
        manualButton.setId(R.id.manual_controls_button);
        manualButton.setImageResource(R.drawable.ic_exposure);
        manualButton.setContentDescription("Manual controls");
        manualButton.setBackgroundResource(R.drawable.liquid_glass_icon_button);
        manualButton.setPadding(dp(9), dp(9), dp(9), dp(9));

        ImageButton settingsButton = new ImageButton(context);
        settingsButton.setImageResource(R.drawable.ic_settings);
        settingsButton.setContentDescription("Open settings");
        settingsButton.setBackgroundResource(R.drawable.liquid_glass_icon_button);
        settingsButton.setPadding(dp(9), dp(9), dp(9), dp(9));
        settingsButton.setOnClickListener(v -> context.startActivity(new Intent(context, SettingsActivity.class)));

        LayoutParams buttonParam = new LayoutParams(dp(40), dp(40));
        buttonParam.setMargins(dp(6), dp(0), dp(6), dp(0));
        settingsButtonContainer.addView(manualButton, buttonParam);
        settingsButtonContainer.addView(settingsButton, buttonParam);
'''
if text.count(old) != 1:
    raise SystemExit("SettingsBarLayout buttons mismatch")
p.write_text(text.replace(old, new, 1))
PY

python3 - <<'PY'
from pathlib import Path

p = Path("app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/settingsbar/SettingsBarEntryView.java")
text = p.read_text()
old_bg = '                button.setBackgroundResource(R.drawable.aux_button_background);\n'
if text.count(old_bg) != 1:
    raise SystemExit("SettingsBarEntryView background mismatch")
text = text.replace(
    old_bg,
    '                button.setBackgroundResource(R.drawable.liquid_glass_icon_button);\n',
    1
)
anchor = '''                button.setOnClickListener(buttonModel.getButtonClickListener());
                button.setSelected(buttonModel.isSelected());
'''
replacement = '''                button.setOnClickListener(buttonModel.getButtonClickListener());
                button.setOnTouchListener((view, event) -> {
                    switch (event.getActionMasked()) {
                        case android.view.MotionEvent.ACTION_DOWN:
                            view.animate().scaleX(0.88f).scaleY(0.88f).alpha(0.82f)
                                    .setDuration(85).start();
                            break;
                        case android.view.MotionEvent.ACTION_UP:
                        case android.view.MotionEvent.ACTION_CANCEL:
                            view.animate().scaleX(1f).scaleY(1f).alpha(1f)
                                    .setDuration(190).start();
                            break;
                        default:
                            break;
                    }
                    return false;
                });
                button.setSelected(buttonModel.isSelected());
'''
if text.count(anchor) != 1:
    raise SystemExit("SettingsBarEntryView listener anchor mismatch")
p.write_text(text.replace(anchor, replacement, 1))
PY

python3 - <<'PY'
from pathlib import Path

p = Path("app/src/main/java/com/particlesdevs/photoncamera/ui/camera/binding/CustomBinding.java")
text = p.read_text()

anchor = 'import android.view.ViewGroup;\n'
if text.count(anchor) != 1:
    raise SystemExit("CustomBinding import anchor mismatch")
if 'import android.view.animation.OvershootInterpolator;' not in text:
    text = text.replace(anchor, anchor + 'import android.view.animation.OvershootInterpolator;\n', 1)

old = '''                viewGroup.post(() -> {
                    viewGroup.animate().setDuration(200).alpha(1).translationY(0).scaleX(1).scaleY(1).start();
                    viewGroup.setVisibility(View.VISIBLE);
                });
            else
                viewGroup.post(() -> viewGroup.animate().setDuration(200).alpha(0).translationY(-viewGroup.getResources().getDimension(R.dimen.standard_125))
                        .scaleX(0).scaleY(0).withEndAction(() -> viewGroup.setVisibility(View.INVISIBLE))
                        .start());
'''
new = '''                viewGroup.post(() -> {
                    viewGroup.setVisibility(View.VISIBLE);
                    viewGroup.setPivotX(viewGroup.getWidth() * 0.82f);
                    viewGroup.setPivotY(0f);
                    viewGroup.animate()
                            .setInterpolator(new OvershootInterpolator(0.85f))
                            .setDuration(320)
                            .alpha(1f)
                            .translationY(0f)
                            .scaleX(1f)
                            .scaleY(1f)
                            .start();
                });
            else
                viewGroup.post(() -> viewGroup.animate()
                        .setDuration(190)
                        .alpha(0f)
                        .translationY(-viewGroup.getResources().getDimension(R.dimen.standard_125) * 0.35f)
                        .scaleX(0.94f)
                        .scaleY(0.94f)
                        .withEndAction(() -> viewGroup.setVisibility(View.INVISIBLE))
                        .start());
'''
if text.count(old) != 1:
    raise SystemExit("CustomBinding settings animation mismatch")
p.write_text(text.replace(old, new, 1))
PY

python3 - <<'PY'
from pathlib import Path
p = Path("app/version.properties")
text = p.read_text()
if text.count("VERSION_BUILD=26172") != 1:
    raise SystemExit("Version build context mismatch")
p.write_text(text.replace("VERSION_BUILD=26172", "VERSION_BUILD=26173", 1))
PY

echo "Verifying UI implementation..."

grep -q '^VERSION_BUILD=26173$' "$VERSION" || fail "Build version was not incremented"
grep -Fq 'format_selector_pill' "$CAMERA_FRAGMENT_XML" || fail "Format selector missing"
grep -Fq 'quad_status_toggle_button' "$CAMERA_FRAGMENT_XML" || fail "Quad status control missing"
grep -Fq 'LiquidModePicker' "$MODESWITCHER_XML" || fail "Liquid mode picker route missing"
grep -Fq 'CameraMode.MOTION' "$CAMERA_UI" || fail "Motion-first display order missing"
grep -Fq 'CameraMode.VIDEO' "$CAMERA_UI" || fail "Video default mode missing"
grep -Fq 'manual_controls_button' "$SETTINGS_LAYOUT" || fail "Manual control entry missing"
grep -Fq 'allEntries.add(quadEntry)' "$SETTINGS_PROVIDER" && fail "Quad still duplicated in More panel"
grep -Fq 'allEntries.add(saveRawEntry)' "$SETTINGS_PROVIDER" && fail "RAW format still duplicated in More panel"
grep -Fq 'allEntries.add(flashEntry)' "$SETTINGS_PROVIDER" && fail "Flash still duplicated in More panel"
grep -Fq 'allEntries.add(timerEntry)' "$SETTINGS_PROVIDER" && fail "Timer still duplicated in More panel"

verify_hash "201a7e3938d36c4a42101374c46051b1d0ad7794e65009a653d9219ba3a1ef39" "$HDRX"
verify_hash "1c3f43bcf4733c3fac6fd0dcd88f8e645c9fd122589cdd170cd85ccf8ae1ff1c" "$PARAMS"
verify_hash "7a6c9beba00891bdc19f581e194b3cd1271cfa89b4c73ba3c0d8869d0100519e" "$NOISE"
verify_hash "99ef221fef9dbf1e1781a2fb0701e4fa8a78dba03c103f39e84bbf5ab5e0f8cc" "$POST"

grep -Fq 'GLFormat.DataType.FLOAT_32' "$PYRAMID"     || fail "R32F contribution texture missing after UI edits"
grep -Fq 'storageFormat=R32F' "$PYRAMID"     || fail "R32F contribution log marker missing after UI edits"
grep -Fq 'layout(r32f, binding = 4)' "$MOTION_SHADER"     || fail "r32f Motion image binding missing after UI edits"
grep -Fq 'layout(r32f, binding = 0)' "$INIT_SHADER"     || fail "r32f initializer binding missing after UI edits"

if grep -Fq 'layout(r16f' "$MOTION_SHADER" "$INIT_SHADER"; then
    fail "Invalid r16f image qualifier returned after UI edits"
fi

git diff --check || fail "git diff --check failed"

for file in \
    "$VERSION" \
    "$CAMERA_FRAGMENT_XML" \
    "$BOTTOMBAR_XML" \
    "$BOTTOMBUTTONS_XML" \
    "$MODESWITCHER_XML" \
    "$TOPBAR_XML" \
    "$CAMERA_UI" \
    "$CAMERA_CONTROLLER" \
    "$CAMERA_FRAGMENT" \
    "$SETTINGS_PROVIDER" \
    "$SETTINGS_LAYOUT" \
    "$SETTINGS_ENTRY_VIEW" \
    "$CUSTOM_BINDING" \
    "$LIQUID_MODE_PICKER" \
    "$PYRAMID" \
    "$HDRX" \
    "$PARAMS" \
    "$NOISE" \
    "$POST" \
    "$MOTION_SHADER" \
    "$INIT_SHADER" \
    app/src/main/res/drawable/liquid_glass_pill.xml \
    app/src/main/res/drawable/liquid_glass_icon_button.xml \
    app/src/main/res/drawable/liquid_glass_panel.xml \
    app/src/main/res/drawable/liquid_shutter_outer.xml \
    app/src/main/res/drawable/ic_quad_status.xml \
    app/src/main/res/values/styles.xml; do
    mkdir -p "$WORK/after/$(dirname "$file")"
    cp "$file" "$WORK/after/$file"
done

git diff --binary > "$WORK/working-tree-after-26173.patch"
git status --short > "$WORK/status-after.txt"
git diff --stat > "$WORK/diff-stat.txt"

echo
echo "============================================================"
echo " Building PhotonCamera 0.9726173"
echo "============================================================"

set +e
./gradlew clean assembleDebug 2>&1 | tee "$BUILD_LOG"
GRADLE_STATUS=${PIPESTATUS[0]}
set -e

if [ "$GRADLE_STATUS" -ne 0 ]; then
    grep -nE 'error:|FAILURE:|BUILD FAILED|AAPT: error|Android resource linking failed|cannot find symbol' \
        "$BUILD_LOG" > "$WORK/relevant-errors.txt" || true
    fail "Gradle build failed. Upload $WORK/relevant-errors.txt and $BUILD_LOG"
fi

BUILT_APK="$(
    find app/build/outputs/apk/debug \
        -type f \
        -name '*.apk' \
        -printf '%T@ %p\n' \
        | sort -nr \
        | head -n 1 \
        | cut -d' ' -f2-
)"

[ -n "$BUILT_APK" ] || fail "Gradle succeeded but no debug APK was found"
cp "$BUILT_APK" "$APK_OUT"
sha256sum "$APK_OUT" > "$APK_OUT.sha256"

echo
echo "============================================================"
echo " BUILD COMPLETE"
echo "============================================================"
echo "Build:         0.9726173 / VERSION_BUILD=26173"
echo "APK:           $APK_OUT"
echo "SHA-256:       $(cat "$APK_OUT.sha256")"
echo "Backup branch: $BACKUP_BRANCH"
echo "Backup patch:  $WORK/working-tree-before-26173.patch"
echo
echo "Integrated changes:"
echo "  - Motion contribution storage changed from invalid r16f to core r32f"
echo "  - 26172 local-contribution merge logic otherwise preserved"
echo "  - Apple-inspired responsive liquid-glass camera UI added"
echo
echo "Protected HDRX, Parameters, NoiseModeler and PostPipeline payloads"
echo "were verified byte-for-byte before and after the integrated edit."
echo
echo "Expected first Motion processing marker:"
echo "  MOTION_26172_CONTRIBUTION_TRACKING ... storageFormat=R32F"
echo
echo "Adaptive Noise Model: leave OFF."
