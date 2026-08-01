#!/usr/bin/env bash
set -Eeuo pipefail

cd /workspaces/Photon-Camera

EXPECTED_BRANCH="experimental-effective-stack"
EXPECTED_HEAD="cedc3ab3e39ad49d42523cff7e3711f8baa69a13"
OLD_BUILD="26174"
NEW_BUILD="26175"
STAMP="$(date +%Y%m%d_%H%M%S)"

WORK="/workspaces/Photon-Camera/build_26175_iris_camera_brand_ui_resume_${STAMP}"
BACKUP_BRANCH="backup-before-iris-camera-brand-ui-26175-resume-${STAMP}"
APK_OUT="$WORK/IrisCamera-0.9726175-debug.apk"
BUILD_LOG="$WORK/build-26175.log"

VERSION="app/version.properties"
CAMERA_FRAGMENT_XML="app/src/main/res/layout/camera_fragment.xml"
BOTTOMBAR_XML="app/src/main/res/layout/layout_main_bottombar.xml"
BOTTOMBUTTONS_XML="app/src/main/res/layout/layout_bottombuttons.xml"
MODESWITCHER_XML="app/src/main/res/layout/layout_modeswitcher.xml"
TOPBAR_XML="app/src/main/res/layout/layout_main_topbar.xml"
STYLES_XML="app/src/main/res/values/styles.xml"
GLASS_PILL="app/src/main/res/drawable/liquid_glass_pill.xml"
LIQUID_MODE_PICKER="app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/modeswitcher/LiquidModePicker.java"
CAMERA_UI="app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java"
APP_GRADLE="app/build.gradle"
MANIFEST="app/src/main/AndroidManifest.xml"
PARSE_EXIF="app/src/main/java/com/particlesdevs/photoncamera/api/ParseExif.java"
AUX_LAYOUT="app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/AuxButtonsLayout.java"
AUX_VIEWMODEL="app/src/main/java/com/particlesdevs/photoncamera/ui/camera/viewmodel/AuxButtonsViewModel.java"
IRIS_OUTLINE_PILL="app/src/main/res/drawable/iris_outline_pill.xml"
IRIS_OUTLINE_CIRCLE="app/src/main/res/drawable/iris_outline_circle.xml"
IRIS_LENS_BACKGROUND="app/src/main/res/drawable/iris_lens_button_background.xml"
IRIS_LENS_TEXT="app/src/main/res/color/iris_lens_text.xml"

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
    echo " BUILD 26175 STOPPED"
    echo "============================================================"
    echo "Reason: $1"
    exit 1
}

echo "============================================================"
echo " Iris Camera 0.9726175 — branding, launcher icon and final UI continuation"
echo "============================================================"
echo "Branch required: $EXPECTED_BRANCH"
echo "Base HEAD:       $EXPECTED_HEAD"
echo "Current build:   $OLD_BUILD"
echo "New build:       $NEW_BUILD"
echo

[ "$(git branch --show-current)" = "$EXPECTED_BRANCH" ] \
    || fail "Wrong branch"

[ "$(git rev-parse HEAD)" = "$EXPECTED_HEAD" ] \
    || fail "Unexpected base HEAD"

grep -q "^VERSION_BUILD=${OLD_BUILD}$" "$VERSION" \
    || fail "Expected VERSION_BUILD=${OLD_BUILD}; do not rerun an earlier build script"

for file in \
    "$CAMERA_FRAGMENT_XML" \
    "$BOTTOMBAR_XML" \
    "$BOTTOMBUTTONS_XML" \
    "$MODESWITCHER_XML" \
    "$TOPBAR_XML" \
    "$STYLES_XML" \
    "$GLASS_PILL" \
    "$LIQUID_MODE_PICKER" \
    "$CAMERA_UI" \
    "$APP_GRADLE" \
    "$MANIFEST" \
    "$PARSE_EXIF" \
    "$AUX_LAYOUT" \
    "$AUX_VIEWMODEL" \
    "$PYRAMID" \
    "$HDRX" \
    "$PARAMS" \
    "$NOISE" \
    "$POST" \
    "$MOTION_SHADER" \
    "$INIT_SHADER"; do
    [ -f "$file" ] || fail "Missing expected file: $file"
done

grep -Fq 'android:id="@+id/top_black_shell"' "$CAMERA_FRAGMENT_XML" \
    || fail "Current compacting target does not contain the 26174 top shell"

grep -Fq 'app:adjustTopBar="@{uimodel.screenAspectRatio}"' "$CAMERA_FRAGMENT_XML" \
    || fail "Expected 26174 top-bar translation binding is missing"

grep -Fq 'android:layout_height="160dp"' "$BOTTOMBAR_XML" \
    || fail "Expected 26174 bottom bar dimensions are missing"

grep -Fq 'android:layout_width="88dp"' "$BOTTOMBUTTONS_XML" \
    || fail "Expected 26174 shutter dimensions are missing"

grep -Fq 'class LiquidModePicker extends HorizontalPicker' "$LIQUID_MODE_PICKER" \
    || fail "Expected 26174 liquid mode picker is missing"

grep -Fq 'Integer[] modeNameIds = CameraMode.nameIds();' "$CAMERA_UI" \
    || fail "26174 CameraMode compile correction is missing"

grep -Fq "applicationId 'com.particlesdevs.photoncamera'" "$APP_GRADLE" \
    || fail "Expected original PhotonCamera applicationId is missing"

grep -Fq '<string name="app_name" translatable="false">PhotonCamera</string>' \
    app/src/main/res/values/strings.xml \
    || fail "Expected original PhotonCamera app label is missing"

grep -Fq 'private static final Comparator<CameraLensData> SORT_BY_ZOOM_FACTOR' \
    "$AUX_VIEWMODEL" \
    || fail "Expected current auxiliary lens sorter is missing"

grep -Fq 'layout(r32f, binding = 4)' "$MOTION_SHADER" \
    || fail "26174 HDRX R32F Motion shader correction is missing"

grep -Fq 'layout(r32f, binding = 0)' "$INIT_SHADER" \
    || fail "26174 HDRX R32F initializer correction is missing"

grep -Fq 'storageFormat=R32F' "$PYRAMID" \
    || fail "26174 R32F contribution marker is missing"

echo "Saving processing hashes and current UI sources..."

sha256sum \
    "$PYRAMID" \
    "$HDRX" \
    "$PARAMS" \
    "$NOISE" \
    "$POST" \
    "$MOTION_SHADER" \
    "$INIT_SHADER" \
    > "$WORK/protected-processing-before.sha256"

for file in \
    "$VERSION" \
    "$CAMERA_FRAGMENT_XML" \
    "$BOTTOMBAR_XML" \
    "$BOTTOMBUTTONS_XML" \
    "$MODESWITCHER_XML" \
    "$TOPBAR_XML" \
    "$STYLES_XML" \
    "$GLASS_PILL" \
    "$LIQUID_MODE_PICKER" \
    "$CAMERA_UI" \
    "$APP_GRADLE" \
    "$MANIFEST" \
    "$PARSE_EXIF" \
    "$AUX_LAYOUT" \
    "$AUX_VIEWMODEL"; do
    mkdir -p "$WORK/before/$(dirname "$file")"
    cp "$file" "$WORK/before/$file"
done

git status --short > "$WORK/status-before.txt"

while IFS= read -r -d '' file; do
    mkdir -p "$WORK/before/$(dirname "$file")"
    cp "$file" "$WORK/before/$file"
done < <(find app/src/main/res -path '*/values*/strings.xml' -print0)

mapfile -d '' launcher_files < <(
    find app/src/main/res -type f \
        \( -name 'ic_launcher.*' -o -name 'ic_gallery_launcher.*' \) \
        -print0
)

if [ "${#launcher_files[@]}" -gt 0 ]; then
    tar -czf "$WORK/launcher-resources-before.tar.gz" "${launcher_files[@]}"
fi

git branch "$BACKUP_BRANCH" HEAD
git diff --binary > "$WORK/working-tree-before-26175.patch"
git diff --cached --binary > "$WORK/index-before-26175.patch"

echo "Backup branch: $BACKUP_BRANCH"
echo "Backup patch:  $WORK/working-tree-before-26175.patch"
echo

echo "Applying Iris Camera branding, launcher icon and final responsive UI..."

python3 - <<'PY'
from pathlib import Path
import base64
import re

app_gradle = Path("app/build.gradle")
gradle = app_gradle.read_text()

old_app_id = "applicationId 'com.particlesdevs.photoncamera'"
new_app_id = "applicationId 'com.skyyking.iriscam'"

if gradle.count(old_app_id) != 1:
    raise SystemExit(
        "applicationId context mismatch: "
        + str(gradle.count(old_app_id))
    )

gradle = gradle.replace(old_app_id, new_app_id, 1)

old_output = 'outputFileName = "PhotonCamera-${versionName}${versionBuild}-${variant.name}.apk"'
new_output = 'outputFileName = "IrisCamera-${versionName}${versionBuild}-${variant.name}.apk"'

if gradle.count(old_output) != 1:
    raise SystemExit(
        "APK output naming context mismatch: "
        + str(gradle.count(old_output))
    )

app_gradle.write_text(
    gradle.replace(old_output, new_output, 1)
)

manifest_path = Path("app/src/main/AndroidManifest.xml")
manifest = manifest_path.read_text()
manifest = manifest.replace(
    'android:icon="@mipmap/ic_gallery_launcher"',
    'android:icon="@mipmap/ic_launcher"',
)
manifest_path.write_text(manifest)

replacement_values = {
    "app_name": "Iris Camera",
    "gallery_name": "Iris Gallery",
    "device_support": "Iris Camera Pro",
    "backup_file_name": "IRIS_BKP_%1$s",
}

string_files = sorted(
    Path("app/src/main/res").glob("values*/strings.xml")
)

if not string_files:
    raise SystemExit("No strings.xml files found")

for strings_path in string_files:
    source = strings_path.read_text()

    for name, value in replacement_values.items():
        pattern = re.compile(
            r'(<string\s+name="' + re.escape(name)
            + r'"[^>]*>).*?(</string>)',
            re.DOTALL,
        )

        matches = list(pattern.finditer(source))

        if len(matches) > 1:
            raise SystemExit(
                f"{strings_path}: duplicate {name} strings"
            )

        if len(matches) == 1:
            source = pattern.sub(
                    lambda match:
                            match.group(1)
                                    + value
                                    + match.group(2),
                    source,
                    count=1,
            )

    strings_path.write_text(source)

parse_exif_path = Path(
    "app/src/main/java/com/particlesdevs/photoncamera/api/ParseExif.java"
)
parse_exif = parse_exif_path.read_text()

old_copyright = 'public final String COPYRIGHT = "PhotonCamera";'
new_copyright = 'public final String COPYRIGHT = "Iris Camera";'

if parse_exif.count(old_copyright) != 1:
    raise SystemExit(
        "ParseExif COPYRIGHT context mismatch: "
        + str(parse_exif.count(old_copyright))
    )

parse_exif_path.write_text(
    parse_exif.replace(
        old_copyright,
        new_copyright,
        1,
    )
)

for path in Path("app/src/main/res").glob("mipmap-*/ic_launcher.*"):
    path.unlink()

for path in Path("app/src/main/res").glob("mipmap-*/ic_launcher_round.*"):
    path.unlink()

def write_icon(path_string, payload):
    path = Path(path_string)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        base64.b64decode(
            "".join(payload.split())
        )
    )

write_icon(
    "app/src/main/res/mipmap-mdpi/ic_launcher.png",
    """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
CGwAAAAASUVORK5CYII="""
)

write_icon(
    "app/src/main/res/mipmap-hdpi/ic_launcher.png",
    """iVBORw0KGgoAAAANSUhEUgAAAEgAAABICAYAAABV7bNHAAAeRUlEQVR42n18a5Bd1XXmt/Y+59xHP9RqdUtgqyUs8bJiSwjb
CAQGy55M1djxDNhMPGPssT0zVBKbxDOZJP43hHFVqlKVKpKYykxlnDHBGQemeOSBGQPBGCzAgIEBzEMgI4zU6m6p3337vs7Z
e82P/b7duFVd3bp97nmsvda3vvWttS9h4IuZCYAgIgUA/X7/cJ7n18/Ozl51/PjPz5+Zmdm6uLCIdrsNBkAggAAhCKwZMssg
iAAiEBGYGcwMsDnGfZEggO01AWitQfY9YAYI4b0gexRBaw3W2r+Hme11NFRl/s9gsGYorcCaQUKgUa9jYmICO3e+Z+miiy86
vnPnzqNlWd5dFMWT9rklAE1EHNuDBo3jDpiZmTmyfXLyG/MLC5947dXXs1deeQVLS0uolIIUAjLLIIUEERnj2HNIKc1JiaLH
8rYAARBChBsggmYeOCK9QWMomAdnBrMGgaC1+d0ZyhmbNUMzG0MyQ2uNqlKoqhJEhLGxMRw4sB8HLtlfbd++/ZEzZ8788bnn
nvvooA2Su2FmQUT6gQceqF155ZV/MjIyctMrP3sF93//ASwtLql6vUFFLSf7ZQxDAiTM77FR4IwWrQVZK5H1LtiHJkEQQlgv
Y38ObT0DAFhr88AcuRycERjaGozZ/M6avdGMwZT9P6C15n5ZcbfT4S1jo/L66z+LAwf2Y3V5+bYnnnrq9z75yU/2nC0AQADA
zTffLIhIv/HGG6OHDx9+cHR09KZ777lP3377HWp9fR1Dw0NSZkKwZtLKrBjszWhtHsysJkNphlIKWnNkfQBsvMyFjfEZ8162
53OG0zYk3eq7b3gjmeu519l7YHhf7G1am/uyx1MmhRgZGZbdTg9/+ZffVnfd+X/06NjYTYcPX/HgG2+8MUok9M033ywAgBzm
AJCLi4sPj4+PX/3dO/6mfP75F/LR0VH7EDZ0hADZsBBSRPgj/GobDLF4Q+SP2eCy1qUIFDzFuLI/0Dy3MYaNtRBu3tDBs5w3
sfUsIkBrQGkFVVUetxAtFJixvLyCK644VH7l3385X1hYeHzbtm2/CkAB0MIB8uzs7K3j4+NX33PPfeUzz/40HxoaQqUUtDIX
16yhlYpuProxu9Ks2T+79xaEG3Hh5wwRP6jW7ENJ27/BhlowLCWGcda2gR3O4zzUnV+zX7hgZAvkSmFkZARPPPmT/N577yu3
bdt29ezp2VttkhKCiNTc9NxVk5OTX33uueerxx57PB9qWuNoDXsrYG1+ageK2mUL7Q3gskfsCWyzjuYQFs6gLqwcvDpgTVbY
hqLSGpq1MRI4OSZclz3WwRveXs+GW+J9bM6rlMJQs4mHHnw4f/HFl6qJ7RNfnZubu4qIlAAAWZO39Psl7r//+ySEiFYd4SGj
C6pKQVng8w9tw8vjButkteBu0GMJQqaJspALFX8epf3/YxCO6QNHeGjSuwX16J+2r8E+m1ba0wCtNUgQlNb4u/v+npgZkugW
ABAz77xz2cjw8DVHjx7l2dk5meeF9xCXJeKHdHnbZa7YXXVkSLc6ejADIXhMDMRKBSP5h7UrH3AleK51hXCPmiMQD+cnhG94
z9OeKpDFSqUU6rU6Tpx4Wz79k2d4aGTkmpmZmctEMTT0eZll8umfPKszmYHtypsLOLeOklF0/QCeIfS8Z7mVt8AYDGVDznpZ
cBz2Hsk6ZB/3oMHrtMcaFXmf9xTnuS6bDtAD/zuRPxc4LI4QAk8+9ZSu1+syE9nns3pRv+rkyVM4ffo01Wq1BHhJCAi7SgSG
0A6BjcXJZim/EjEpdIzYGZMZBGNsYXGHtYa2uMEJGPuTmIQADUc7HdgaQ0TkUYefHp+st2jWUdIId+m8MTZiXuR4++1f0Nzs
HBqNxlVCZGLvm28eR7/fJyKCqlSaOaIMlQAiB1cPnCO6mMcLbR8MG45hHYVNlML1htAKr7FPHJzwJH8/sX0tLnoi67KnwzyK
wtIaXUqJ9fV1evvtXyDPs72CgLHTp0+DiEgP4ImOgFkzRzReeyPaJTaQ4HBAO7LHfuVC2Bm64IA9dvXk2z14lPU8AGttKUPM
rThkzohQxkDuaIP3NA5G9MY09R5Nn56GkHIsq5TC6spqsK4FSQIATSApQhFpEZptyLmUS5bVcVx0aYDJMNCIU3sXJxse4cFM
wckx+LsHiu7NG90eY9NnlAG192wDYRqaQz2HhGBG5JQQeTVjZWUFzIyMmdEv+7ZGAqDtiUQARhMeGszScw2XOslDhavgzftI
2NWwdZOv3tlgilsxkwMM3vnQjIlkhDvOxOzAm8gzfU8SERfjIZz1ABQECqKT97pg7PdKAEDmGah7IyXeak9m/EUrBRLCO7XW
2gCuZapEZDyACNBsKz3nUcEDsjw3FT3DeyURwFL6G4RbFO1LepRlGeo0k0aNkdgcG7J7wErY0I+5VkocI0xkc8/GkNoaKIp5
p7O4ENFkDWDLBA1ARrKCs0OIfYAEvEZDKlTnJoUSpJSYn5/HmTNnokKTbN2ko6ICPgwIwOiWUex873shSKDSKuJR2hdunnzy
ILl0ZNH+DUiJaUwqFfsKAmBkgdZw8kan2bBmMAXHVVqZ4hQErYXBoljk8nUPG29iDYYpbmWW4bXXXsNPf/ocut1ugmsuirTS
/jwBQBlCCFxw/gW4/PLLw98JEfFzwB4ShAdlHWVFHRlIG9wkCkJcqPfMMmXkij1XH0UVOZOBYaUViIRRCkH+5pgcG01UN/PI
QoBcrWXT5/zZs3jmmWfR7XaR53miHhIZONfW+BhYZaUVXn3tVWwd34p979+Hvur747QKhNZ4pVmUgDVp3eYL2sj7fPkY0Ter
B5EvC3iAE3i26yvtAGiefyD6m725CE6DLCoIs3Nz6HTayPMs1ESx69uF19G1XJ0lyGDf9PQ0qqry2UYpZSGAIn6GhLGbmiuS
QWKVUmtfmGtbgoRqAshgM1JCpIh9xtGWUYMZAgKWToPYrLp5RERhwhCkvW4EG/OqUuj1elH1HlKuuQeKsgo8cw66tbmhXq+H
siy9rq2V9tnHlDkb+dCgBhTr2b6GdFmZBKqILGexWOVOQFZAdzmcIrXPJzoiEAzXEETIMmkznBXBrLgGkmBmyEz6VXf44ksa
qy97ToGgLcV4xHZRQIRMSivt2lBhslTBGFhVlfGcKMMxh+f0qkhU7UcVJ4TNxhniYlJHVa69EUGOLAbWrBEuIKWE1gozMzNY
WV3xqxAXoA5LpqenPSAm3Q2TDfwikCONkf7sMuPy8jJeeOF55FnuyV1gwcYIzaEmJicnUa/X0e/1o3o3FNAxW1dWCKSI47jz
ZptRexICAhpEMmKYAIQGQXjGKosCrdYaXnzxRczMzKCqVErSorStWUMKacV844ZSCCil0e/30S/7PlykkMjzHEWR2wUIANru
tPHyyy9js6+4ZBgbG8P+/fuxfft29PtlkEbsiVRcw0UGEUIE9g6YLOaFcpsWhS0bCBpgEdI4E0AGVKUU6Ha7ePbZZzEzM4s8
zyGzzHiA5U5CBv3IZRtmcxPdbhft9jrqjQbO2bED73nPuRgdGQUIWFtbw9zcGczNzWFlZQWNRhONRh1KmcJX2vCKSILHKbLl
z+LiIp599llcdtll2Lp1q8EVzQktcOHkDKttnRhrXxlsX0r71oiVPclghiaLR7ZpRzBxLkSGEyeOY2ZmFkVR+PcZ8hiBa1Qc
uvBaXl7C1NROXP/Zz2DPnvOglMLS4hJa6y2w1tg19V5cecXlyPIcp0/P4vEfP4633jqBkZER3yKyVZG5N+EFaF8P5nmOVquF
48eP49JLL/WZ0tCUKEMq9hnblC8iFOJkSw1jPfaxqAGQ1hC2Cej4A4FAlhP1+yVmZmdsvRNim6JOIVtscfjR63XBzPh3X/wi
9u17P55++if41m234dT0HKqyioLFXGPHjglcfugQ/u2/+Rymp2dw9z33oN1po9kYiugEeZ5DSXgbT11YWEBrrYVGsxH4m+NA
nFIRny+thkSm1IDXbBy2QBA0E0hraFtkhjYyIAjolyV6vZ6/OZCVV6JCk3z5IdBpt7FlyxZ87au/hTfffAN/8AffwHpbYXL7
XuzetRtCZNBcoqp6UKqLsuqhtb6Mv/v7f8D3H/i/+OxnrsN//vrv4K++czvOnDmDoaGhSHEMKmH4r3mtLEt0u13U63V/b3oQ
rH0iQCK6GZBGYJfguKJNFTpBImQVoT1ZcxoK4kYgAp4RCN1OB1u3juE/ff3ruPOuv8WPf3wUu3Yfwr7Ji9DpCFSaQUKjrLqA
XoFSRjVoNMcwNDyGbncVd951F1599VX8h698Bd+5/XbMzs2hOTQU2P9AyzqmLpVSkY5ESbHqcC2RY4OkjczEZKSzROKXwR/T
5dAiou0QXurgRCgPUqtzZ6UVpJT4rd/8Tdxxx1/j6WdewIFLrsVIYw+EnMD+g3tQcoHZ6UWsr8+h1Z5Dp7uAbn8Z3c4Cup2z
EDLHxDnn4aWXX8b/+s5f4Ytf+CJu+4v/jn6vhyzPE+mVogEJl66VqoxItwmBNOEfGDwIUQfEFfc25mIuFJREZUFc+24Ea5VW
wLE8amPbEca11VV87tf/NZ588gk8/cwz+MAH/zlqcgrvf/+H8Wff+o/4o//2adz4pY9gz9QU6nIEOeWQIEiSKIph1Id3QHGG
fr+Pie278PqxY3j4nx7GZ667Fp1Ox3sEERLdiL2WRV6J9LWZa2V7vGJoVtZKkc7levOaowrY9oxCQbfR4rEe7EPKraIOpK7d
aeOiiy/CyPAw7r7nPkzt/jCqcgjn7LoQ3/yja3HJJePotLs4e7aLZqOGIsvAuoJWJVTVQVW2oao+8sYWsKihX/awZXwHfvTY
Y2DW2LdvH9rt9chr0t6bA2Qd12WsE/0nkGQOsnJEewSsa4WGmw5pP/YkW9C5TqRSVegSbCLgA4R+r4erDh/Ggw89jKwYRb2+
DR3VxMc+fggrSy28fXwFK60KqwsacjUH1hQ6K8torc6h11mGqjrQVRuq7EIWQ6jYyL8yK/Dooz/Chy49iLKqkp59othHOGMw
SBmeE+vcHCkA/vlD0so8ifOhBS9nGi9SyTyPuwMVESqfHaL6qtvtYseOHSiKHC+9/DNsm7gAnV6FkclzsLjYwdGnzqDerGFM
5riwuRVn8wq6rEFVClW/RLe/CoUOsiI3qykkZDGEsreC5vAWvHn8OK7+6EexfXISq6uryIsC4LiGjCp21lCqCkMDUWiF4ywe
afJKJHnJVeukAoYtQl0Mx1Te68aaB/rn8AofM9DtdbF/9wdx8uRJ9HoVZFaggoQgxlPPvIXTZxlZVeCa3bshx4H+cIZV9NGp
2ih1B0r3UJZtKE3I8jpYl6CsBlCGLAOqqsLpmRns2jWF55573pBVy4niiS2GG8cJNSK57m1c9yWivvaZOHPjKYFNWqxSCna2
JWjPVpdm70Ghk5B0LMgcNzk5gZOnTkHkdaiqDy40+t1FLK+cRvtYH9Qew+wJxu5dW9BBhWWso1utoF+2UFVtMJeoeiVISPMN
DcgcWvdBssDc3BzOPfc9ybzRIFATYCFBQwi2tRYiOUdZAh0KZD8DRWTkDh3JEJYP23lCk7EECehoCiNxSy8jMJKGAhEajQaW
l5YgZYZKlUDVRrdzBpIyrK6dxfpqD6drEzg2MwqVVeh03kKvXERVtaC5BLOVK7QCydymcQlWBJnlWFtr4X3vqyUpnZLGbGDZ
jl071cBhEEVje548BgtbwYxDX1trbeudMCDlMpwPsWgQKWSP4K6uvazKEt1eD4IApXogWkeva2qhst9Dt72GrqyBhIRGhUq1
oMplaK5MgpU5iLXpBJA0IgsRQAasncckkx5+iSlZMDckqiESTXXjIFZQJgEyckfcG/eTWrAxa5tvZEMtHK+TqpcGRjU1Gymz
KAooVQJcoSrXwbqCqrpQZQ/9XisaqlJgrgBZQNSa0GUPMsvArCCLOkhKMAQADSEkAIE8yw2jj/tdRkWOcIW8TEzk+BLSvn5E
ZcxAaiCdWcosgyRpWjYMItO5SKbLdCRZMgaadaG51+50MDw8DFX1AWiosg1wBa16puNZrVnupAAhQDKHzEfR2LoXsjaK/upJ
VJ151Joj6PdaEDIDcwkpa1BaY2R0BJ1Ox2NgKHcQhZrjOsrqPc7r4o5I1FXWQRbxIB1EeOUta6xM3uopxPBAiMViJbwePTs7
i8lt20wGIg1wCa0AotJOyDJUv2Ol2sxPjoy97xAmP/gJvHP0bmD9BLRaR1n2IPM6uAIESWhdYfvkBKanTwcFM57NdiDNQTEd
FNY4yrphooWSIS/huohax2xZRwzTFHoOvrRWPm1y1C7RUTtXa0ZeFDh58iTGt21DURSoqj4EMVj1wbpEVXWR5RmElFYNMJpy
VuRoL76D9sIZTO37CCb2fggKDdSHtkOIAnluhLNmvYbx8XG8c/IUiqII3q85KVzdrIHSOokS9wxhLNA+twpk0UlN0bhsqMk4
nv6qlPlWyqfAeCIMSX4z78uzHPMLi+h2u9i7531YX1tBZjGFPcOtkNcayIq69wJWfVSrp1AtHsPIjq2o6udgy46DaGyZghAS
jcYIVlcWcNGF52N9vY2FxQVTsPrODG8Iede5cPcc6ExwBEMFlDeiC1LhxDKd0O90fIRZe7nA/1RVMuQZj585F86kxP976SVc
evAgtCqhdYU8M+HhjlGqgpQZiloDtXoDRa2GoibRXZvD28dOYGhsCuO7LoGWDWzZci7KfhdQXVz24Q/hueefR25l3g0THtF4
i9PagyFs+aGUdQiVsO54bEa41q6xcviptUJVVbapxgPGMWHn25Dp/XmvqtfrOHHiBFrr6zh8xRVYXZ6HzDJkUpruiZAgmUGx
htIVqqqPst9FZ20B7eU5yLKPqt3C6so72Lp1HJkkzJx8A0euvhILCwt4660TqNcbif6UeHU0tBWah+ZaIcTiGcqBIbC4WK18
Mao8zig79GROZoaxjeeEOcJkCgTx/I35ajaaeOSHP8S+fftwwQUXYmlhDnmeme6q5UwkMvNN0mZNAso21mdfxPKJx9AsF6Db
Z3H89afwwX17cfGFF+CBH/wAzWZzg9cMDiX41pN2Ye0mW5U3mpu39MbyE2iIiCKHipaj9kmQIylqwKXDnUGu9RPMtrtg+mbd
bh//8I//iOuuvRZSCLx+7HUMb5lAvdGwlbbLywzWJbhqA90zKDKNpmbM/+I4Tp14Cfv3nYd/9tHL8Tff+9+oKoVmowiXp9Bj
S4RBi6XKPpcbu3GKorDNTt+YZOMcSPti9iRKJ8NFrpuREMOo6RZ4BG2YEIkazKjXG1haWsbd99yLf/XpT2NqagqP//goWmur
GBreglq9ASEzW3PlpksLhdbiSUy/9QLyjPFrv3o5du88F3d897tYXF7C8NBwdI+pTsoJ6+cwyieEHz6NmxWeybFtKUUbcywP
cmkwLVjhplL99Bd86RFPhyb7uhxnskxfkIBmjWazibVWC9+782/xsWuuwRdu+DyOHTuGN948jqWVeVTKiPts927keYbxsTFc
ddmv4MLz92D61Cn8z29/G0prH1o0AHyxVMMDoe5rr8H3IC6jMJCk4IrVSBCLLRw1+sPWJHhZNbPW1h6oOdkg5oagnOhbq9VQ
VSV+8OAPsGPHObjkwAH82qf+BZTSWF9fR7vTARioN+oYGhpCkeeYnZ3Ffffei7kzs2g0miiKmt8A47dWpRZKZB93bNKP97MG
SKZv2c5laotLILJdjQE92s+N+naP9jUNosmIolYDWq1ISyJsVni4FRIAMplhZGQLFpeW8eBDD6JW1DG5fRLj4+Oo1+sgGKl2
cXER8/Pz6PW6yLICwyOjvniOmXCsLqTgbH4WRQFhQwtSJlTEz1xrdt1AsK85dcAgn8bdPi9yXdAghjOHGsXRgEa9hjzPUVZl
0ip6t69461OtVqBWFNBaYXZ2Dqemp31WA4Asy5HnBYaHR9w7o2nbAczZeCG/+7HZbBphLBoOIztuQ5zuIHLeFPanwU13KM8k
tR/IRAKCoW4Jm0FICAwPDWF1bc1q1JsbhjfZeiggwMSQlKHZzPyNxs18P+sYRmmTUeS0rmI/bWuqcoFmswkpM+hKgbKNQw7v
dq8q2umUYJDXmZPbBNIXwj4JbTfxNptNdLtdlGWZ7rEYfOtAWGCT13iD8h79nZFsJUC0qdhzQyGQZ5lh5EWRjCzHCxAbKc56
QghUlSGSPospFY2hOc3HMLhkpI7iPRY6jIvkeW7DQkKpKBMawjFgaUp4R2pCTrvIPDhNH20TTnYMh4cW0txPJjMIQdEWLeX7
+KGHxn7SyU2FeKjxPAim8+iKUU8GQWBdbYIpHBWyFnyFQJZlpiUj9YbdiKlr8wCR401Ek802ZUc6DsXgLxKvEFJACAlp57ld
4S0EJex6sBERe5AnikQBpCtl6xOlfOqMWXHc0Ug257LTsEXCmQKxpA1YwWA/BeIYOvmp+TS4N+2qxLEX77OwixWDuRnlYSgm
HwHxDoJ40f1siQoJyRBFiz+VqsBKR+8MM8wp2kclyIAQRSBoaADC8KKoNRxiPwolAYBlMB6leo7vc3nOQhsGwDfPcNbLB2oP
wiZZb8CTHUATETKRCeRFYXYFW/BNjAMkBmOOASISuhO5AIms6QX2wQ8ZIEo2CYc5Q0rVgWiXTCLSx9SBos6KG2KPNuEEkk3R
BAol3RiHTaqqPAnOcpljbGwLyqpKBxop7r7FrhzoCic1GxKAj8OBYs8BbVQAYnYL2pDKE/zBYK0YJmWNLd1skjtHOp4XDy24
GSYkoWtUjLGxMYOtICxfeOGFY1VVsdaKBrXmeOPgoHuyn+JAso1BDxSR8S4aX9LyRlDmKLo5GoqIR4EHw8KPT3LQ0f3D+3uI
FyfgKJGtNnWKQ8zMe/fuJaXUclZV1c8vu+wjHyqKgvv9kjYzjgsdIpHgiUuxeiD5uCmPQDjxLgx7IKNBg5g2rEQYC6ZEJQhp
m5JJsRQ7EzE47enRxn2sVa+H0dERvuTgJdTv938u1tfXjx44cAAXnH8+r6+3PGdQWntp0rVCYs1aaw1WOn09mROKmwE64Vjx
yAkPbPQP29F549gNR9fTPDDfnW7rDNcxopiKivGNoy/hoy9arRb279/Pe/bsQavVPiqWl5e/J6VUN3zh86Ld7tg0F+1MHtgz
H6TZIMGGCfrod6svObHc7YMI07SD3ROdNg8GtpkHOTj6cIDoPcm5OIy7MMPvjlbRnozB67opV1VVuOGGG0RVlqrVWv0eAcDC
wsIj9Vr94x878nF17NgxOTTUTPduRaGySRGSAvKGHtrmuBGfIwBuvA/WI2gUAoE4h6xIyYcaDN5fzH3irDvYaJRSYnV1FQcP
XqIeeeSf5Orq6g+3b9/+CQEArW7r5lq9hm9+8xYOboh0FC/ay66ZN4zqxSutI/d+t+P8qvNm4aH9LqDYs0JDIXiqjscHN9kc
HG8MDnga5sLdqIf5bCHgllv+kLMsQ6fTuRlmAyHLsdGxX/zGjb+x/eClBw8Robz//gfk0NCQ3/EXlxdxEcUxVkS9sWRmCDwA
oDHwY5OOSPqxGAnwD6T3OFVzfG7E3sLRthUke/nd1nwhJM6enccf3vxfyy996Uv57OzsX0xNTf0PZpbJx+PMz88/PDExcfXv
/u5/KW+99dZ8YmLS1Ca2JR3XiGIgn2wmUwwWnxjYKEdJc4A3qccobFgZKGwT+jGwCQ6b18ZJSLldjESEs2fP4Gtfu6m87bZv
5fPz849PTEz4j8eRt9xyCwDQkSNHqhtvvPFeIjp87bXX7hFE+qGHHtZKKVGv1cMkBwZvhmNfCdsBBlL4BkpPG18b3LEMbF4X
MCNJ7xgo7JNplcTWQYuVMkO328Hy8pL6vd//ffzprbdmy4vLjy0sLvzLyYnJNoPpyJEjvOlHdB06dOhPxsfHb3r00R/ht3/7
d/DKKy+rer1JzWaDhBCUDExuVHyi/4WPskm26nJ0w4g39L27kLUZb9qogMRem2olBLO1SzNzt9vldrvFUzt3yT/78z/Fdddd
h+XF5dueenrjR3S964e8nTx58sjOnTu/MT8//4k777wru+Ov78Crr72Gfr+PPMsgs8z2oYJ/U1o2ISnjBsIiqfCj6X4XVgT6
pfLt4MLQYMYb2ENbVRXKsoQQhPPOOw+f+9yv48tf/nJ13nnnPXLq1Kk/npqa+uUf8vauHxPY7h/OG/n1Z+bmrnrwwYfOf+KJ
J7a+/LOfYW5uDp1ON9nYTxS2cSaAO7DcgZnTgDakN8i8qdKY1mn+2HifSOLF5niZZZicmMAHfuUDuPyKQ0uf+tSnjl988cVH
AdxNRL/0YwL/PwrPhDGVipoBAAAAAElFTkSuQmCC"""
)

write_icon(
    "app/src/main/res/mipmap-xhdpi/ic_launcher.png",
    """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"""
)

write_icon(
    "app/src/main/res/mipmap-xxhdpi/ic_launcher.png",
    """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
AAAAAElFTkSuQmCC"""
)

write_icon(
    "app/src/main/res/mipmap-xxxhdpi/ic_launcher.png",
    """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"""
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

camera = Path("app/src/main/res/layout/camera_fragment.xml")
text = camera.read_text()

replacements = [
    ('android:layout_height="72dp"', 'android:layout_height="60dp"', "top shell height"),
    ('android:layout_height="48dp"\n                android:minWidth="72dp"',
     'android:layout_height="36dp"\n                android:minWidth="54dp"',
     "format pill dimensions"),
    ('android:paddingStart="16dp"\n                android:paddingEnd="12dp"',
     'android:paddingStart="12dp"\n                android:paddingEnd="10dp"',
     "format pill padding"),
    ('android:elevation="8dp"', 'android:elevation="6dp"', "format pill elevation"),
    ('android:layout_marginStart="12dp"\n                android:layout_marginTop="12dp"',
     'android:layout_marginStart="10dp"\n                android:layout_marginTop="10dp"',
     "format pill margins"),
    ('android:textSize="13sp"\n                    android:textStyle="bold"\n                    android:letterSpacing="0.04"',
     'android:textSize="11sp"\n                    android:textStyle="bold"\n                    android:letterSpacing="0.02"',
     "format pill text"),
    ('android:layout_marginStart="10dp">', 'android:layout_marginStart="7dp">', "quad status gap"),
    ('android:layout_width="18dp"\n                        android:layout_height="18dp"',
     'android:layout_width="15dp"\n                        android:layout_height="15dp"',
     "quad icon size"),
    ('android:layout_marginStart="5dp"\n                        android:text="48/64MP"',
     'android:layout_marginStart="4dp"\n                        android:text="48/64MP"',
     "quad label gap"),
    ('android:textSize="11sp"\n                        android:textStyle="bold"',
     'android:textSize="10sp"\n                        android:textStyle="bold"',
     "quad label text"),
    ('android:layout_width="152dp"', 'android:layout_width="132dp"', "format panel width"),
    ('android:layout_marginTop="8dp">', 'android:layout_marginTop="6dp">', "format panel gap"),
    ('layout="@layout/layout_main_topbar"\n                android:layout_width="wrap_content"\n                android:layout_height="56dp"\n                app:adjustTopBar="@{uimodel.screenAspectRatio}"',
     'layout="@layout/layout_main_topbar"\n                android:layout_width="wrap_content"\n                android:layout_height="38dp"',
     "remove top-bar vertical translation"),
    ('android:layout_marginTop="8dp"\n                android:layout_marginEnd="10dp"',
     'android:layout_marginTop="10dp"\n                android:layout_marginEnd="8dp"',
     "top-bar margins"),
    ('layout="@layout/layout_main_bottombar"\n                    android:layout_width="0dp"\n                    android:layout_height="160dp"',
     'layout="@layout/layout_main_bottombar"\n                    android:layout_width="0dp"\n                    android:layout_height="128dp"',
     "camera bottom bar height"),
]

for old, new, label in replacements:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one match, found {count}")
    text = text.replace(old, new, 1)

old_aux = '''            <com.particlesdevs.photoncamera.ui.camera.views.AuxButtonsLayout
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
'''

new_aux = '''            <com.particlesdevs.photoncamera.ui.camera.views.AuxButtonsLayout
                    android:id="@+id/aux_buttons_container"
                    android:layout_width="wrap_content"
                    android:layout_height="40dp"
                    android:orientation="horizontal"
                    android:gravity="center"
                    android:paddingStart="0dp"
                    android:paddingEnd="0dp"
                    android:background="@android:color/transparent"
                    android:elevation="0dp"
                    setAuxButtonModel="@{auxmodel}"
                    setActiveId="@{auxmodel.currentCameraId}"
                    bindViewGroupChildrenRotate="@{uimodel}"
                    app:layout_constraintBottom_toTopOf="@id/layout_bottombar"
                    app:layout_constraintStart_toStartOf="parent"
                    app:layout_constraintEnd_toEndOf="parent"
                    android:layout_marginBottom="2dp" />
'''

if text.count(old_aux) != 1:
    raise SystemExit(
        "lens selector block: expected exactly one match, found "
        + str(text.count(old_aux))
    )

camera.write_text(text.replace(old_aux, new_aux, 1))

replace_once(
    "app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java",
    'formatActiveLabel.setText("JPG + RAW");',
    'formatActiveLabel.setText("JPG+RAW");',
    "compact active format text",
)

version = Path("app/version.properties")
vtext = version.read_text()
if vtext.count("VERSION_BUILD=26174") != 1:
    raise SystemExit("VERSION_BUILD=26174 context mismatch")
version.write_text(vtext.replace("VERSION_BUILD=26174", "VERSION_BUILD=26175", 1))
PY

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
            android:layout_height="38dp"
            android:minWidth="40dp"
            android:orientation="horizontal"
            android:gravity="center"
            android:paddingStart="2dp"
            android:paddingEnd="2dp"
            android:clipChildren="false"
            android:background="@drawable/iris_outline_pill"
            android:elevation="4dp"
            bindViewGroupChildrenRotate="@{uimodel}">

        <FrameLayout
                android:layout_width="34dp"
                android:layout_height="34dp"
                android:visibility="@{timer_visible ? View.VISIBLE : View.GONE}">

            <com.particlesdevs.photoncamera.ui.camera.views.TimerButton
                    android:id="@+id/countdown_timer_button"
                    android:layout_width="30dp"
                    android:layout_height="30dp"
                    android:layout_gravity="center"
                    android:background="@drawable/ic_timer"
                    android:onClick="@{top_bar_click_listener}"
                    android:contentDescription="Countdown timer"/>
        </FrameLayout>

        <FrameLayout
                android:layout_width="34dp"
                android:layout_height="34dp"
                android:visibility="@{flash_visible ? View.VISIBLE : View.GONE}">

            <com.particlesdevs.photoncamera.ui.camera.views.FlashButton
                    android:id="@+id/flash_button"
                    android:layout_width="30dp"
                    android:layout_height="30dp"
                    android:layout_gravity="center"
                    android:background="@drawable/ic_flash"
                    android:onClick="@{top_bar_click_listener}"
                    android:contentDescription="Flash control"/>
        </FrameLayout>

        <FrameLayout
                android:layout_width="34dp"
                android:layout_height="34dp">

            <ImageButton
                    android:id="@+id/settings_button"
                    android:layout_width="30dp"
                    android:layout_height="30dp"
                    android:layout_gravity="center"
                    android:background="@android:color/transparent"
                    android:src="@drawable/ic_settings"
                    android:padding="6dp"
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

cat > "$BOTTOMBAR_XML" <<'EOF'
<?xml version="1.0" encoding="utf-8"?>
<layout xmlns:android="http://schemas.android.com/apk/res/android"
        xmlns:app="http://schemas.android.com/apk/res-auto">

    <androidx.constraintlayout.widget.ConstraintLayout
            android:id="@+id/layout_bottombar"
            android:layout_width="match_parent"
            android:layout_height="128dp"
            android:background="#F6000000"
            android:clipChildren="false"
            android:clipToPadding="false">

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
                android:layout_width="154dp"
                android:layout_height="34dp"
                android:layout_marginBottom="17dp"
                android:elevation="14dp"
                app:layout_constraintStart_toStartOf="parent"
                app:layout_constraintEnd_toEndOf="parent"
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
                android:layout_width="76dp"
                android:layout_height="76dp"
                android:background="@drawable/liquid_shutter_outer"
                android:elevation="10dp"
                app:layout_constraintTop_toTopOf="parent"
                app:layout_constraintStart_toStartOf="parent"
                app:layout_constraintEnd_toEndOf="parent"
                android:layout_marginTop="0dp">

            <ImageButton
                    android:id="@+id/shutter_button"
                    android:layout_width="match_parent"
                    android:layout_height="match_parent"
                    android:layout_gravity="center"
                    android:background="@drawable/roundbutton"
                    android:clickable="true"
                    android:contentDescription="Shutter Button"
                    android:onClick="@{bottom_bar_click_listener}"
                    android:scaleX="0.80"
                    android:scaleY="0.80"
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
                    android:scaleX="1.12"
                    android:scaleY="1.12"
                    tools:progress="50"/>

            <TextView
                    android:id="@+id/frameCount"
                    android:layout_width="wrap_content"
                    android:layout_height="wrap_content"
                    android:layout_gravity="center"
                    android:text="@{timermodel.frameCount}"
                    android:textColor="@android:color/white"
                    android:textSize="25sp"
                    android:textAlignment="center"
                    android:visibility="visible"
                    tools:text="20"/>
        </FrameLayout>

        <FrameLayout
                android:id="@+id/galery_button_container"
                android:layout_width="40dp"
                android:layout_height="40dp"
                android:background="@drawable/iris_outline_circle"
                android:elevation="6dp"
                app:layout_constraintStart_toStartOf="parent"
                app:layout_constraintBottom_toBottomOf="parent"
                android:layout_marginStart="10dp"
                android:layout_marginBottom="14dp">

            <de.hdodenhof.circleimageview.CircleImageView
                    android:id="@+id/gallery_image_button"
                    android:layout_width="34dp"
                    android:layout_height="34dp"
                    android:layout_gravity="center"
                    android:background="@drawable/round"
                    android:onClick="@{bottom_bar_click_listener}"
                    imageFromBitmap="@{uimodel.bitmap}"
                    bindRotate="@{uimodel}"
                    app:civ_border_color="#FFFFFFFF"
                    app:civ_border_overlay="true"
                    app:civ_border_width="1dp"/>
        </FrameLayout>

        <FrameLayout
                android:id="@+id/camera_switch_container"
                android:layout_width="40dp"
                android:layout_height="40dp"
                android:background="@drawable/iris_outline_circle"
                android:elevation="6dp"
                app:layout_constraintEnd_toEndOf="parent"
                app:layout_constraintBottom_toBottomOf="parent"
                android:layout_marginEnd="10dp"
                android:layout_marginBottom="14dp">

            <ImageButton
                    android:id="@+id/flip_camera_button"
                    android:layout_width="34dp"
                    android:layout_height="34dp"
                    android:layout_gravity="center"
                    android:background="@android:color/transparent"
                    android:clickable="true"
                    android:onClick="@{bottom_bar_click_listener}"
                    android:contentDescription="Lens Switch Button"
                    android:padding="7dp"
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
            android:layout_width="154dp"
            android:layout_height="34dp"
            android:background="@drawable/iris_outline_pill"
            android:contentDescription="Camera mode selector"
            android:focusable="true"
            android:clickable="true"
            android:elevation="8dp"/>
</layout>
EOF

cat > "$LIQUID_MODE_PICKER" <<'EOF'
package com.particlesdevs.photoncamera.ui.camera.views.modeswitcher;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.RectF;
import android.util.AttributeSet;
import android.util.TypedValue;

import com.particlesdevs.photoncamera.ui.camera.views.modeswitcher.wefika.horizontalpicker.HorizontalPicker;

/**
 * Motion/Video-first mode selector with a moving transparent glass overlay.
 *
 * Photon keeps the complete mode list and normal horizontal swipe behavior.
 * Motion and Video are the first two visible choices; the remaining modes
 * appear naturally as the user continues to scroll.
 */
public class LiquidModePicker extends HorizontalPicker {
    private static final int SELECTED_YELLOW = 0xFFFFCC00;
    private static final int UNSELECTED_WHITE = 0xFFFFFFFF;

    private final Paint overlayFillPaint =
            new Paint(Paint.ANTI_ALIAS_FLAG);

    private final Paint overlayStrokePaint =
            new Paint(Paint.ANTI_ALIAS_FLAG);

    private final Paint textPaint =
            new Paint(Paint.ANTI_ALIAS_FLAG);

    private final RectF overlay = new RectF();

    public LiquidModePicker(Context context) {
        this(context, null);
    }

    public LiquidModePicker(
            Context context,
            AttributeSet attrs
    ) {
        super(context, attrs);

        setSideItems(0);
        setOverScrollMode(OVER_SCROLL_NEVER);
        setWillNotDraw(false);

        overlayFillPaint.setStyle(Paint.Style.FILL);
        overlayFillPaint.setColor(0x18FFFFFF);

        overlayStrokePaint.setStyle(Paint.Style.STROKE);
        overlayStrokePaint.setStrokeWidth(dp(1.0f));
        overlayStrokePaint.setColor(0x70FFFFFF);

        textPaint.setTextAlign(Paint.Align.CENTER);
        textPaint.setTypeface(
                android.graphics.Typeface.create(
                        android.graphics.Typeface.DEFAULT,
                        android.graphics.Typeface.BOLD
                )
        );
        textPaint.setTextSize(sp(10.5f));
    }

    @Override
    protected void onDraw(Canvas canvas) {
        final int width = getWidth();
        final int height = getHeight();
        final CharSequence[] labels = getValues();

        if (width <= 0
                || height <= 0
                || labels == null
                || labels.length == 0) {
            return;
        }

        float position =
                Math.max(
                        0.0f,
                        Math.min(
                                labels.length - 1.0f,
                                getScrollX()
                                        / (float) Math.max(1, width)
                        )
                );

        int leftIndex;
        float progress;

        if (position <= 1.0f
                || labels.length == 1) {
            leftIndex = 0;
            progress = Math.min(1.0f, position);
        } else {
            leftIndex =
                    Math.min(
                            labels.length - 2,
                            (int) Math.floor(position)
                    );

            progress =
                    Math.max(
                            0.0f,
                            Math.min(
                                    1.0f,
                                    position - leftIndex
                            )
                    );
        }

        int rightIndex =
                Math.min(
                        labels.length - 1,
                        leftIndex + 1
                );

        float pad = dp(2.5f);
        float half = width / 2.0f;
        float overlayLeft =
                pad
                        + progress
                                * half;

        overlay.set(
                overlayLeft,
                pad,
                overlayLeft
                        + half
                        - pad * 2.0f,
                height - pad
        );

        float radius = height / 2.0f;

        canvas.drawRoundRect(
                overlay,
                radius,
                radius,
                overlayFillPaint
        );

        canvas.drawRoundRect(
                overlay,
                radius,
                radius,
                overlayStrokePaint
        );

        float baseline =
                height / 2.0f
                        - (
                                textPaint.ascent()
                                        + textPaint.descent()
                        ) / 2.0f;

        int selectedSide =
                progress < 0.5f
                        ? 0
                        : 1;

        drawLabel(
                canvas,
                labels[leftIndex].toString(),
                half * 0.5f,
                baseline,
                selectedSide == 0
                        ? SELECTED_YELLOW
                        : UNSELECTED_WHITE
        );

        drawLabel(
                canvas,
                labels[rightIndex].toString(),
                half * 1.5f,
                baseline,
                selectedSide == 1
                        ? SELECTED_YELLOW
                        : UNSELECTED_WHITE
        );
    }

    private void drawLabel(
            Canvas canvas,
            String label,
            float x,
            float baseline,
            int color
    ) {
        textPaint.setColor(color);
        canvas.drawText(
                label,
                x,
                baseline,
                textPaint
        );
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
EOF

cat > "$AUX_VIEWMODEL" <<'EOF'
/*
 *
 *  PhotonCamera / Iris Camera UI
 *  AuxButtonsViewModel.java
 *
 */

package com.particlesdevs.photoncamera.ui.camera.viewmodel;

import android.hardware.camera2.CameraCharacteristics;

import androidx.lifecycle.ViewModel;

import com.particlesdevs.photoncamera.ui.camera.CameraFragment;
import com.particlesdevs.photoncamera.ui.camera.data.CameraLensData;
import com.particlesdevs.photoncamera.ui.camera.model.AuxButtonsModel;
import com.particlesdevs.photoncamera.ui.camera.views.AuxButtonsLayout;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Map;

/**
 * ViewModel which connects {@link AuxButtonsModel} with {@link CameraFragment}.
 *
 * Lens buttons are always sorted from the lowest optical zoom factor to the
 * highest. This gives 0.6x, 1x, 3x, 4.1x on the current device while staying
 * data-driven for other OEM camera arrangements.
 */
public class AuxButtonsViewModel extends ViewModel {
    private static final Comparator<CameraLensData> SORT_BY_ZOOM_FACTOR =
            Comparator.comparingDouble(CameraLensData::getZoomFactor)
                    .thenComparing(CameraLensData::getCameraId);

    private final AuxButtonsModel auxButtonsModel =
            new AuxButtonsModel();

    private boolean initialized = false;
    private boolean isEnabled = true;

    public void initCameraLists(
            Map<String, CameraLensData> cameraLensDataMap
    ) {
        if (!initialized) {
            List<CameraLensData> frontCameras =
                    new ArrayList<>();

            List<CameraLensData> backCameras =
                    new ArrayList<>();

            cameraLensDataMap.forEach(
                    (id, cameraLensData) -> {
                        if (cameraLensData.getFacing()
                                == CameraCharacteristics
                                        .LENS_FACING_BACK) {
                            backCameras.add(
                                    cameraLensData
                            );
                        } else if (
                                cameraLensData.getFacing()
                                        == CameraCharacteristics
                                                .LENS_FACING_FRONT
                        ) {
                            frontCameras.add(
                                    cameraLensData
                            );
                        }
                    }
            );

            backCameras.sort(
                    SORT_BY_ZOOM_FACTOR
            );

            frontCameras.sort(
                    SORT_BY_ZOOM_FACTOR
            );

            auxButtonsModel.setBackCameras(
                    backCameras
            );

            auxButtonsModel.setFrontCameras(
                    frontCameras
            );

            initialized = true;
        }
    }

    public void setAuxButtonListener(
            AuxButtonsLayout.AuxButtonListener auxButtonListener
    ) {
        auxButtonsModel.setAuxButtonListener(
                auxButtonListener
        );
    }

    public boolean isEnabled() {
        return isEnabled;
    }

    public void setEnabled(boolean enabled) {
        isEnabled = enabled;
        auxButtonsModel.setEnabled(enabled);
    }

    public void setActiveId(String cameraId) {
        auxButtonsModel.setCurrentCameraId(
                cameraId
        );
    }

    public AuxButtonsModel getAuxButtonsModel() {
        return auxButtonsModel;
    }
}
EOF

cat > "$AUX_LAYOUT" <<'EOF'
/*
 *
 *  PhotonCamera / Iris Camera UI
 *  AuxButtonsLayout.java
 *
 */

package com.particlesdevs.photoncamera.ui.camera.views;

import android.content.Context;
import android.util.AttributeSet;
import android.util.TypedValue;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;

import androidx.annotation.Nullable;

import com.particlesdevs.photoncamera.R;
import com.particlesdevs.photoncamera.ui.camera.binding.CustomBinding;
import com.particlesdevs.photoncamera.ui.camera.data.CameraLensData;
import com.particlesdevs.photoncamera.ui.camera.model.AuxButtonsModel;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;

/**
 * Compact horizontal optical-lens selector.
 */
public class AuxButtonsLayout extends LinearLayout {
    private static final Comparator<CameraLensData> SORT_BY_ZOOM_FACTOR =
            Comparator.comparingDouble(CameraLensData::getZoomFactor)
                    .thenComparing(CameraLensData::getCameraId);

    private final HashMap<Integer, String> auxButtonsMap =
            new HashMap<>();

    private AuxButtonListener auxButtonListener;
    private AuxButtonsModel auxButtonsModel;

    public AuxButtonsLayout(
            Context context,
            @Nullable AttributeSet attrs
    ) {
        super(context, attrs);
    }

    private static String getAuxButtonName(
            float zoomFactor
    ) {
        return String.format(
                Locale.US,
                "%.1fx",
                zoomFactor - 0.049f
        ).replace(".0", "");
    }

    public void setAuxButtonsModel(
            AuxButtonsModel auxButtonsModel
    ) {
        this.auxButtonsModel =
                auxButtonsModel;

        auxButtonListener =
                auxButtonsModel
                        .getAuxButtonListener();
    }

    public void setActiveId(String activeId) {
        refresh(activeId);
    }

    private void refresh(String cameraId) {
        if (auxButtonsModel == null) {
            return;
        }

        List<CameraLensData> front =
                auxButtonsModel
                        .getFrontCameras();

        List<CameraLensData> back =
                auxButtonsModel
                        .getBackCameras();

        if (front == null
                || back == null) {
            return;
        }

        if (!isFront(cameraId, front)) {
            setAuxButtons(
                    back,
                    cameraId
            );
        } else {
            setAuxButtons(
                    front,
                    cameraId
            );
        }
    }

    private boolean isFront(
            String cameraId,
            List<CameraLensData> frontCameras
    ) {
        return frontCameras.stream().anyMatch(
                cameraLensData ->
                        cameraLensData
                                .getCameraId()
                                .equals(cameraId)
        );
    }

    private void setAuxButtons(
            List<CameraLensData> source,
            String activeId
    ) {
        removeAllViews();
        auxButtonsMap.clear();

        List<CameraLensData> ordered =
                new ArrayList<>(source);

        ordered.sort(
                SORT_BY_ZOOM_FACTOR
        );

        for (CameraLensData cameraLensData
                : ordered) {
            addNewButton(
                    cameraLensData
                            .getCameraId(),
                    getAuxButtonName(
                            cameraLensData
                                    .getZoomFactor()
                    )
            );
        }

        setListenerAndSelected(
                activeId
        );

        updateVisibility();
    }

    private void setListenerAndSelected(
            String activeId
    ) {
        View.OnClickListener listener =
                this::onAuxButtonClick;

        for (int index = 0;
                index < getChildCount();
                index++) {
            View button =
                    getChildAt(index);

            button.setOnClickListener(
                    listener
            );

            boolean selected =
                    activeId.equals(
                            auxButtonsMap.get(
                                    button.getId()
                            )
                    );

            button.setSelected(
                    selected
            );
        }
    }

    private void updateVisibility() {
        setVisibility(
                getChildCount() > 1
                        ? View.VISIBLE
                        : View.INVISIBLE
        );
    }

    private void onAuxButtonClick(
            View view
    ) {
        if (!auxButtonsModel.isEnabled()) {
            return;
        }

        for (int index = 0;
                index < getChildCount();
                index++) {
            View child =
                    getChildAt(index);

            child.setSelected(
                    view.equals(child)
            );
        }

        if (auxButtonListener != null) {
            auxButtonListener
                    .onAuxButtonClicked(
                            auxButtonsMap.get(
                                    view.getId()
                            )
                    );
        }
    }

    private void addNewButton(
            String cameraId,
            String buttonText
    ) {
        Button button =
                new Button(getContext());

        LayoutParams params =
                new LayoutParams(
                        LayoutParams.WRAP_CONTENT,
                        dp(38)
                );

        params.setMargins(
                dp(2),
                0,
                dp(2),
                0
        );

        button.setLayoutParams(
                params
        );

        button.setMinWidth(
                dp(42)
        );

        button.setMinimumWidth(
                dp(42)
        );

        button.setPadding(
                dp(8),
                0,
                dp(8),
                0
        );

        button.setText(
                buttonText
        );

        button.setTextAppearance(
                R.style.AuxButtonText
        );

        button.setTextColor(
                getResources().getColorStateList(
                        R.color.iris_lens_text,
                        getContext().getTheme()
                )
        );

        button.setBackgroundResource(
                R.drawable
                        .iris_lens_button_background
        );

        button.setStateListAnimator(null);
        button.setTransformationMethod(null);
        button.setAllCaps(false);

        int buttonId =
                View.generateViewId();

        button.setId(
                buttonId
        );

        auxButtonsMap.put(
                buttonId,
                cameraId
        );

        addView(
                button
        );
    }

    private int dp(float value) {
        return Math.round(
                TypedValue.applyDimension(
                        TypedValue.COMPLEX_UNIT_DIP,
                        value,
                        getResources()
                                .getDisplayMetrics()
                )
        );
    }

    public interface AuxButtonListener {
        void onAuxButtonClicked(
                String cameraId
        );
    }
}
EOF

mkdir -p \
    app/src/main/res/drawable \
    app/src/main/res/color

cat > "$IRIS_OUTLINE_PILL" <<'EOF'
<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android"
       android:shape="rectangle">
    <solid android:color="#0AFFFFFF"/>
    <stroke
            android:width="1dp"
            android:color="#D9FFFFFF"/>
    <corners android:radius="22dp"/>
    <padding
            android:left="1dp"
            android:top="1dp"
            android:right="1dp"
            android:bottom="1dp"/>
</shape>
EOF

cat > "$IRIS_OUTLINE_CIRCLE" <<'EOF'
<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android"
       android:shape="oval">
    <solid android:color="#08000000"/>
    <stroke
            android:width="1dp"
            android:color="#FFFFFFFF"/>
</shape>
EOF

cat > "$IRIS_LENS_TEXT" <<'EOF'
<?xml version="1.0" encoding="utf-8"?>
<selector xmlns:android="http://schemas.android.com/apk/res/android">
    <item
            android:state_selected="true"
            android:color="#FFFFCC00"/>
    <item android:color="#FFFFFFFF"/>
</selector>
EOF

cat > "$IRIS_LENS_BACKGROUND" <<'EOF'
<?xml version="1.0" encoding="utf-8"?>
<selector xmlns:android="http://schemas.android.com/apk/res/android">
    <item android:state_selected="true">
        <shape android:shape="oval">
            <solid android:color="@android:color/transparent"/>
            <stroke
                    android:width="1dp"
                    android:color="#FFFFCC00"/>
            <size
                    android:width="38dp"
                    android:height="38dp"/>
        </shape>
    </item>

    <item>
        <shape android:shape="oval">
            <solid android:color="@android:color/transparent"/>
            <size
                    android:width="38dp"
                    android:height="38dp"/>
        </shape>
    </item>
</selector>
EOF

python3 - <<'PY'
from pathlib import Path

camera = Path(
    "app/src/main/res/layout/"
    "camera_fragment.xml"
)

text = camera.read_text()

old_background = (
        'android:background='
        '"@drawable/liquid_glass_pill"'
)

new_background = (
        'android:background='
        '"@drawable/iris_outline_pill"'
)

if text.count(old_background) < 1:
    raise SystemExit(
        "Camera format pill background "
        "context is missing"
    )

text = text.replace(
        old_background,
        new_background,
        1,
)

camera.write_text(text)
PY

python3 - <<'PY'
from pathlib import Path

styles = Path("app/src/main/res/values/styles.xml")
text = styles.read_text()

replacements = [
    ('<item name="android:layout_height">44dp</item>',
     '<item name="android:layout_height">38dp</item>',
     "LiquidGlassMenuText height"),
    ('<item name="android:paddingStart">14dp</item>',
     '<item name="android:paddingStart">12dp</item>',
     "LiquidGlassMenuText start padding"),
    ('<item name="android:paddingEnd">14dp</item>',
     '<item name="android:paddingEnd">12dp</item>',
     "LiquidGlassMenuText end padding"),
    ('<item name="android:textSize">13sp</item>',
     '<item name="android:textSize">12sp</item>',
     "LiquidGlassMenuText size"),
    ('<item name="android:layout_marginBottom">5dp</item>',
     '<item name="android:layout_marginBottom">4dp</item>',
     "LiquidGlassMenuText gap"),
]

for old, new, label in replacements:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one match, found {count}")
    text = text.replace(old, new, 1)

styles.write_text(text)

pill = Path("app/src/main/res/drawable/liquid_glass_pill.xml")
ptext = pill.read_text()

if ptext.count('<corners android:radius="28dp"/>') != 1:
    raise SystemExit("liquid glass pill radius context mismatch")

pill.write_text(
    ptext.replace(
        '<corners android:radius="28dp"/>',
        '<corners android:radius="22dp"/>',
        1,
    )
)
PY

echo "Verifying compact UI source..."

grep -q '^VERSION_BUILD=26175$' "$VERSION" \
    || fail "Build number was not incremented to 26175"

grep -Fq 'android:layout_height="60dp"' "$CAMERA_FRAGMENT_XML" \
    || fail "Compact top shell missing"

grep -Fq 'android:layout_height="36dp"' "$CAMERA_FRAGMENT_XML" \
    || fail "Compact format pill missing"

if grep -Fq 'app:adjustTopBar=' "$CAMERA_FRAGMENT_XML"; then
    fail "Old top-bar vertical translation is still present"
fi

grep -Fq 'android:layout_width="154dp"' "$BOTTOMBAR_XML" \
    || fail "Fixed-width mode selector missing"

grep -Fq 'android:layout_marginBottom="17dp"' "$BOTTOMBAR_XML" \
    || fail "Mode selector safe-bottom margin missing"

grep -Fq 'android:layout_width="76dp"' "$BOTTOMBUTTONS_XML" \
    || fail "Compact shutter missing"

grep -Fq 'android:layout_width="40dp"' "$BOTTOMBUTTONS_XML" \
    || fail "Compact corner controls missing"

grep -Fq 'setWillNotDraw(false);' "$LIQUID_MODE_PICKER" \
    || fail "Mode picker draw enablement missing"

grep -Fq 'getScrollX()' "$LIQUID_MODE_PICKER" \
    || fail "Moving mode overlay drawing missing"

grep -Fq 'formatActiveLabel.setText("JPG+RAW");' "$CAMERA_UI" \
    || fail "Compact active format label missing"

grep -Fq "applicationId 'com.skyyking.iriscam'" "$APP_GRADLE" \
    || fail "Iris Camera applicationId missing"

grep -Fq 'outputFileName = "IrisCamera-${versionName}${versionBuild}-${variant.name}.apk"' \
    "$APP_GRADLE" \
    || fail "Iris Camera APK output name missing"

grep -Fq '<string name="app_name" translatable="false">Iris Camera</string>' \
    app/src/main/res/values/strings.xml \
    || fail "Iris Camera app label missing"

grep -Fq 'public final String COPYRIGHT = "Iris Camera";' "$PARSE_EXIF" \
    || fail "Iris Camera EXIF label missing"

grep -Fq 'Comparator.comparingDouble(CameraLensData::getZoomFactor)' \
    "$AUX_VIEWMODEL" \
    || fail "Ascending OEM lens ordering missing"

grep -Fq 'R.color.iris_lens_text' "$AUX_LAYOUT" \
    || fail "Yellow/white lens text states missing"

grep -Fq '@drawable/iris_outline_pill' "$TOPBAR_XML" \
    || fail "Top-right outline pill missing"

grep -Fq 'getScrollX()' "$LIQUID_MODE_PICKER" \
    || fail "Moving mode overlay missing"

for density in mdpi hdpi xhdpi xxhdpi xxxhdpi; do
    [ -s "app/src/main/res/mipmap-${density}/ic_launcher.png" ] \
        || fail "Launcher icon missing for ${density}"
done

echo "Verifying HDRX and image-processing files stayed untouched..."

sha256sum -c "$WORK/protected-processing-before.sha256" \
    || fail "A protected processing file changed during UI correction"

git diff --check \
    || fail "git diff --check failed"

for file in \
    "$VERSION" \
    "$CAMERA_FRAGMENT_XML" \
    "$BOTTOMBAR_XML" \
    "$BOTTOMBUTTONS_XML" \
    "$MODESWITCHER_XML" \
    "$TOPBAR_XML" \
    "$STYLES_XML" \
    "$GLASS_PILL" \
    "$LIQUID_MODE_PICKER" \
    "$CAMERA_UI" \
    "$APP_GRADLE" \
    "$MANIFEST" \
    "$PARSE_EXIF" \
    "$AUX_LAYOUT" \
    "$AUX_VIEWMODEL" \
    "$IRIS_OUTLINE_PILL" \
    "$IRIS_OUTLINE_CIRCLE" \
    "$IRIS_LENS_BACKGROUND" \
    "$IRIS_LENS_TEXT"; do
    mkdir -p "$WORK/after/$(dirname "$file")"
    cp "$file" "$WORK/after/$file"
done

while IFS= read -r -d '' file; do
    mkdir -p "$WORK/after/$(dirname "$file")"
    cp "$file" "$WORK/after/$file"
done < <(find app/src/main/res -path '*/values*/strings.xml' -print0)

mapfile -d '' launcher_files_after < <(
    find app/src/main/res -type f \
        \( -name 'ic_launcher.*' -o -name 'ic_gallery_launcher.*' \) \
        -print0
)

if [ "${#launcher_files_after[@]}" -gt 0 ]; then
    tar -czf "$WORK/launcher-resources-after.tar.gz" "${launcher_files_after[@]}"
fi

git diff --binary > "$WORK/working-tree-after-26175.patch"
git status --short > "$WORK/status-after.txt"
git diff --stat > "$WORK/diff-stat.txt"

echo
echo "============================================================"
echo " Building Iris Camera 0.9726175"
echo "============================================================"

set +e
./gradlew clean assembleDebug 2>&1 | tee "$BUILD_LOG"
GRADLE_STATUS=${PIPESTATUS[0]}
set -e

if [ "$GRADLE_STATUS" -ne 0 ]; then
    grep -nE \
        'error:|FAILURE:|BUILD FAILED|AAPT: error|Android resource linking failed|cannot find symbol|incompatible types' \
        "$BUILD_LOG" \
        > "$WORK/relevant-errors.txt" || true

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

[ -n "$BUILT_APK" ] \
    || fail "Gradle succeeded but no debug APK was found"

cp "$BUILT_APK" "$APK_OUT"
sha256sum "$APK_OUT" > "$APK_OUT.sha256"

echo
echo "============================================================"
echo " BUILD COMPLETE"
echo "============================================================"
echo "Build:         Iris Camera 0.9726175 / VERSION_BUILD=26175"
echo "APK:           $APK_OUT"
echo "SHA-256:       $(cat "$APK_OUT.sha256")"
echo "Backup branch: $BACKUP_BRANCH"
echo "Backup patch:  $WORK/working-tree-before-26175.patch"
echo
echo "Iris Camera changes:"
echo "  - applicationId: com.skyyking.iriscam"
echo "  - visible app name: Iris Camera"
echo "  - approved grey-gradient camera launcher icon"
echo "  - APK naming changed to IrisCamera"
echo "  - ascending OEM lens order: lowest zoom to highest zoom"
echo "  - selected lens uses yellow text and a yellow outline"
echo "  - compact top-right pill with no divider bars"
echo "  - gallery, mode selector and camera switch share the lower row"
echo "  - moving transparent mode-selection overlay"
echo "  - Motion and Video remain the two default visible modes"
echo
echo "Internal Java namespace remains com.particlesdevs.photoncamera."
echo "HDRX R32F correction and all image-processing files remained unchanged."
echo "Adaptive Noise Model: leave OFF."
