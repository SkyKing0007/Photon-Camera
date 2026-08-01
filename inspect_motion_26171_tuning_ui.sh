#!/usr/bin/env bash
set -Eeuo pipefail

cd /workspaces/Photon-Camera

REPORT="/workspaces/Photon-Camera/motion_26171_tuning_ui_exact_context.txt"

{
    echo "=== REPOSITORY STATE ==="
    echo "Branch: $(git branch --show-current)"
    echo "HEAD:   $(git rev-parse HEAD)"
    grep '^VERSION_BUILD=' app/version.properties || true
    git status --short
    echo

    echo "=== CURRENT 26170 MOTION NOISE FILES ==="
    for file in \
        app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java \
        app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/ESD3D2.java \
        app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionLumaDenoise.java \
        app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionChromaDenoise.java \
        app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/AutoExposure.java \
        app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/CaptureSharpening.java \
        app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Sharpen2.java \
        app/src/main/assets/shaders/denoise/esd3d2.glsl \
        app/src/main/assets/shaders/denoise/motionlumadenoise.glsl \
        app/src/main/assets/shaders/denoise/motionchromadenoise.glsl; do
        echo
        echo "----- FILE: $file -----"
        sed -n '1,760p' "$file"
    done
    echo

    echo "=== TUNABLE ANNOTATION AND INJECTOR ==="
    find app/src/main/java -type f \
        | grep -E '/Tunable.java$|/TunableInjector.java$' \
        | sort \
        | while IFS= read -r file; do
            echo
            echo "----- FILE: $file -----"
            sed -n '1,760p' "$file"
        done
    echo

    echo "=== TUNING SETTINGS UI CLASSES ==="
    grep -RIl \
        -E 'TunableInjector|@Tunable|SeekBar|Slider|EditText|NumberPicker|PreferenceFragment|PreferenceScreen|DialogPreference|EditTextPreference|SeekBarPreference' \
        app/src/main/java \
        | sort \
        | while IFS= read -r file; do
            echo
            echo "----- FILE: $file -----"
            sed -n '1,900p' "$file"
        done
    echo

    echo "=== TUNING XML AND LAYOUT RESOURCES ==="
    grep -RIl \
        -E 'SeekBar|Slider|EditText|NumberPicker|tunable|Tunable|preference|Preference' \
        app/src/main/res \
        | sort \
        | while IFS= read -r file; do
            echo
            echo "----- FILE: $file -----"
            sed -n '1,900p' "$file"
        done
    echo

    echo "=== GENERATED TUNABLE KEYS AND CATEGORIES ==="
    grep -RIn -B6 -A16 \
        -E 'pref_tunable_|category[[:space:]]*=|defaultValue[[:space:]]*=|step[[:space:]]*=|allowedPngSizes' \
        app/src/main/java/com/particlesdevs/photoncamera \
        | head -12000
    echo

    echo "=== SETTINGS STORAGE / RESET / IMPORT EXPORT ==="
    grep -RIn -B20 -A80 \
        -E 'SharedPreferences|reset.*tunable|tunable.*reset|export.*setting|import.*setting|PreferenceManager|setSummary|summaryProvider|showDialog|AlertDialog' \
        app/src/main/java/com/particlesdevs/photoncamera/settings \
        app/src/main/java/com/particlesdevs/photoncamera/ui \
        2>/dev/null \
        | head -12000
    echo

    echo "=== CURRENT MOTION BUILD MARKERS ==="
    grep -RIn \
        -E 'MOTION_26170_|MOTION_26169_|MOTION_26168_|MOTION_26166_' \
        app/src/main/java \
        app/src/main/assets/shaders \
        | head -5000
    echo

    echo "=== DIFF SUMMARY ==="
    git diff --stat
    echo
    echo "REPORT COMPLETE"
} | tee "$REPORT"

echo
echo "============================================================"
echo " UI AUDIT COMPLETE"
echo "============================================================"
echo "Report: $REPORT"
echo "No source files were modified."
