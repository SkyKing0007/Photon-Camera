#!/usr/bin/env bash
set -euo pipefail

EXPECTED_BRANCH="experimental-clean-photon-rebuild"
EXPECTED_APP_BASE="8233415edf738bf35c0fe1c4907f5dfe51de31a4"
BACKUP_BRANCH="backup-26484-runtime-before-gl-layout-parser-fix"
BACKUP_EXPECTED="80901a1217a6fdfb7da9c229d3f2f13ac82d3e30"

BASE26383_PATCH="26483_successful_source.patch"
BASE26383_PATCH_SHA="a993c2c9e12cba8098623fab8b83f0965b9ad2016eded6fd857f55935a1c11db"
BASE26383_HASHES="26483_successful_after.sha256"
BASE26383_HASHES_SHA="7cba064adf92e6645a1f94ea44a5bd205a800cead9dcd8c392816de5f2725ca7"
DELTA26484="26484_delta_from_26483.patch"
DELTA26484_SHA="18fbb861c3c49f4ad8399f29aa60ca3e85df57ffacc794b8b6a2206b42197ac3"
TRANSFORM="transform_26485_runtime_shutter_full_fix_v1.py"
TRANSFORM_SHA="2e04a8e250d0fb64ca3e4a7763ed4943203d7f1ae740283018a7fb1b90c9a461"

NEW_VERSION="0.9726485"
NEW_BUILD="26485"
OUTDIR="build_26485_outputs"
APK_NAME="IrisCamera-${NEW_VERSION}-${NEW_BUILD}-runtime-shutter-full-fix-debug.apk"

fail(){ echo "FAIL: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }

REPO="$(pwd)"
rm -rf "$OUTDIR"
mkdir -p "$OUTDIR"

AUDIT="$OUTDIR/26485_source_audit.txt"
CANDLOG="$OUTDIR/26485_temporary_candidate_build.log"
FINALLOG="$OUTDIR/26485_final_build.log"
SHADERLOG="$OUTDIR/26485_shader_validation.txt"
REPORT="$OUTDIR/26485_build_report.txt"
PREPATCH="$OUTDIR/26485_pre_edit_exact_26484_binary.patch"
DELTAOUT="$OUTDIR/26485_delta_from_26484.patch"
SOURCEPATCH="$OUTDIR/26485_source.patch"
AFTERHASH="$OUTDIR/26485_after.sha256"
PREBUILDHASH="$OUTDIR/26485_prebuild_canonical.sha256"

exec > >(tee "$AUDIT") 2>&1
echo "=== 26485 RUNTIME + FULL SHUTTER FIX ==="
date -Iseconds || true

BRANCH="${GITHUB_REF_NAME:-$(git branch --show-current)}"
[[ "$BRANCH" == "$EXPECTED_BRANCH" ]] || fail "wrong branch $BRANCH"
[[ "$BRANCH" != "dev" ]] || fail "dev protected"

git cat-file -e "$EXPECTED_APP_BASE^{commit}" || fail "protected app base missing"
git diff --quiet "$EXPECTED_APP_BASE" -- app/src/main app/version.properties \
    || fail "committed app source no longer equals protected app base"

[[ -f "$BASE26383_PATCH" && "$(sha "$BASE26383_PATCH")" == "$BASE26383_PATCH_SHA" ]] \
    || fail "26483 source patch identity"
[[ -f "$BASE26383_HASHES" && "$(sha "$BASE26383_HASHES")" == "$BASE26383_HASHES_SHA" ]] \
    || fail "26483 source manifest identity"
[[ -f "$DELTA26484" && "$(sha "$DELTA26484")" == "$DELTA26484_SHA" ]] \
    || fail "successful 26484 delta identity"
[[ -f "$TRANSFORM" && "$(sha "$TRANSFORM")" == "$TRANSFORM_SHA" ]] \
    || fail "26485 transform identity"

python3 -m py_compile "$TRANSFORM"
bash -n "$0"
pass "infrastructure syntax and identity"

remote="$(git ls-remote origin "refs/heads/$BACKUP_BRANCH" | awk '{print $1}')"
[[ "$remote" == "$BACKUP_EXPECTED" ]] \
    || fail "backup branch $BACKUP_BRANCH=$remote expected=$BACKUP_EXPECTED"
pass "backup branch exact pre-26485 checkpoint"

TMP="$(mktemp -d)"
BASE="$TMP/base26484"
CAND="$TMP/candidate26485"
cleanup(){
    set +e
    git worktree remove --force "$BASE" >/dev/null 2>&1 || true
    git worktree remove --force "$CAND" >/dev/null 2>&1 || true
    rm -rf "$TMP"
}
trap cleanup EXIT

# ----------------------------------------------------------------------
# CRITICAL 26484-build-failure prevention:
# Reconstruct successful 26484 as a COMPOSITION:
# protected app base -> exact successful 26483 -> exact successful 26484 delta
# -> deterministic 26484 version bump.
#
# We intentionally DO NOT use the prior "26484_successful_source.patch" as a
# baseline because that checkpoint export did not carry the full 26483 dependency
# graph. This is the exact class of mistake that produced the 65-symbol final
# compile failure during 26484 bring-up.
# ----------------------------------------------------------------------
reconstruct26484(){
    local d="$1"
    git worktree add --detach "$d" "$EXPECTED_APP_BASE" >/dev/null
    (
        cd "$d"
        git apply --check --binary "$REPO/$BASE26383_PATCH"
        git apply --binary "$REPO/$BASE26383_PATCH"
        sha256sum -c "$REPO/$BASE26383_HASHES" >/dev/null
        grep -q '^VERSION_NAME=0\.9726483$' app/version.properties
        grep -q '^VERSION_BUILD=26483$' app/version.properties

        git apply --check --binary "$REPO/$DELTA26484"
        git apply --binary "$REPO/$DELTA26484"

        python3 - <<'PY'
from pathlib import Path
p=Path("app/version.properties")
s=p.read_text()
if s.count("VERSION_NAME=0.9726483") != 1 or s.count("VERSION_BUILD=26483") != 1:
    raise SystemExit("26484 baseline version anchor mismatch")
p.write_text(s.replace("VERSION_NAME=0.9726483","VERSION_NAME=0.9726484",1)
              .replace("VERSION_BUILD=26483","VERSION_BUILD=26484",1))
PY
        grep -q '^VERSION_NAME=0\.9726484$' app/version.properties
        grep -q '^VERSION_BUILD=26484$' app/version.properties
    )
}

reconstruct26484 "$BASE"
pass "exact successful 26484 composite baseline reconstructed"

# Binary pre-edit patch BEFORE any 26485 source modification.
(
    cd "$BASE"
    git add -N app/src/main app/version.properties >/dev/null 2>&1 || true
    git diff --binary "$EXPECTED_APP_BASE" -- app/src/main app/version.properties
) > "$PREPATCH"
[[ -s "$PREPATCH" ]] || fail "26485 pre-edit exact-26484 binary patch empty"
pass "binary pre-edit patch created before 26485 modification"

reconstruct26484 "$CAND"
python3 "$REPO/$TRANSFORM" "$CAND"
pass "candidate/source validation PASS"

cat > "$TMP/allow.txt" <<'EOF'
app/src/main/assets/shaders/motionv2/mfsr_mgc_covariance.glsl
app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java
EOF

# Exact changed-file allowlist relative to the successful 26484 composite.
python3 - "$BASE" "$CAND" "$TMP/allow.txt" <<'PY'
from pathlib import Path
import hashlib,sys
a,b=Path(sys.argv[1]),Path(sys.argv[2])
allow=set(Path(sys.argv[3]).read_text().splitlines())
def hashes(root):
    d={}
    for p in (root/"app/src/main").rglob("*"):
        if p.is_file():
            rel=str(p.relative_to(root)).replace("\\","/")
            d[rel]=hashlib.sha256(p.read_bytes()).hexdigest()
    return d
x,y=hashes(a),hashes(b)
changed={k for k in x.keys()|y.keys() if x.get(k)!=y.get(k)}
if changed != allow:
    raise SystemExit("26485 changed-file allowlist mismatch changed="+repr(sorted(changed)))
print("candidate exact changed-file allowlist PASS")
PY

# Protected source equality against complete successful 26484 baseline.
python3 - "$BASE" "$CAND" "$TMP/allow.txt" <<'PY'
from pathlib import Path
import hashlib,sys
a,b=Path(sys.argv[1]),Path(sys.argv[2])
allow=set(Path(sys.argv[3]).read_text().splitlines())
for p in (a/"app/src/main").rglob("*"):
    if not p.is_file(): continue
    rel=str(p.relative_to(a)).replace("\\","/")
    if rel in allow: continue
    q=b/rel
    if not q.is_file() or hashlib.sha256(p.read_bytes()).digest()!=hashlib.sha256(q.read_bytes()).digest():
        raise SystemExit("protected successful-26484 source changed: "+rel)
print("protected successful-26484 source hashes PASS")
PY

CAP="$CAND/app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java"
COV="$CAND/app/src/main/assets/shaders/motionv2/mfsr_mgc_covariance.glsl"
WA="$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2WronskiAlignment.java"
CR="$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java"

# Preserve 26484 architecture plus require new fixes.
for spec in \
"$CAP:IRIS_26484_IMMEDIATE_MOTION_SHUTTER_ACK" \
"$CAP:IRIS_26484_UNLOCK_FOCUS_NULL_BUILDER_GUARD" \
"$CAP:IRIS_26481_EXACT_TIMESTAMP_METADATA_OWNERSHIP" \
"$CAP:IRIS_26485_FULL_PREBUFFER_AUTHORITATIVE_ZSL" \
"$CAP:IRIS_26485_FULL_PREBUFFER_IMMEDIATE_PROCESS" \
"$WA:IRIS_26484_BJZHOU_COMPLETE_FLOW_CHAIN" \
"$CR:IRIS_26484_BJZHOU_COUPLED_ALIGNMENT_REJECTION_OPPONENT_MERGE" \
"$COV:IRIS_26484_BJZHOU_STRUCTURE_ADAPTIVE_RGB_PRECISION"
do
    f="${spec%%:*}"; m="${spec#*:}"
    grep -q "$m" "$f" || fail "missing required marker $m"
done

grep -Fq 'mMotion26485PrebufferFullAtPress' "$CAP" \
    || fail "26485 shutter press full-buffer state missing"
grep -Fq 'validBuffered >= mMotionTopUpMinimumFrames' "$CAP" \
    || fail "26485 safe minimum frame gate missing"
grep -Fq 'iris26480ShortGateReady' "$CAP" \
    || fail "existing short-highlight readiness gate lost"
! grep -Fq 'if (captureBuilder == null || mCaptureSession == null)' "$CAP" \
    || fail "invalid 26484 captureBuilder ownership regression"
pass "26485 shutter ownership/no-regression gates"

# Java lexical structure on all Java owners touched by 26484/26485.
python3 - "$CAP" "$WA" "$CR" <<'PY'
from pathlib import Path
import sys
def code_only(src):
    out=[]; i=0; n=len(src); state="code"
    while i<n:
        if state=="code":
            if src.startswith("//",i): state="line"; out.extend("  "); i+=2; continue
            if src.startswith("/*",i): state="block"; out.extend("  "); i+=2; continue
            if src.startswith('"""',i): state="text"; out.extend("   "); i+=3; continue
            c=src[i]
            if c=='"': state="string"; out.append(" "); i+=1; continue
            if c=="'": state="char"; out.append(" "); i+=1; continue
            out.append(c); i+=1; continue
        if state=="line":
            c=src[i]; out.append("\n" if c=="\n" else " "); i+=1
            if c=="\n": state="code"
            continue
        if state=="block":
            if src.startswith("*/",i): out.extend("  "); i+=2; state="code"; continue
            out.append("\n" if src[i]=="\n" else " "); i+=1; continue
        if state=="text":
            if src.startswith('"""',i): out.extend("   "); i+=3; state="code"; continue
            out.append("\n" if src[i]=="\n" else " "); i+=1; continue
        if state in ("string","char"):
            c=src[i]
            if c=="\\":
                out.append(" "); i+=1
                if i<n: out.append("\n" if src[i]=="\n" else " "); i+=1
                continue
            out.append("\n" if c=="\n" else " "); i+=1
            if (state=="string" and c=='"') or (state=="char" and c=="'"): state="code"
    if state in ("block","string","char","text"):
        raise SystemExit("unterminated Java lexical state "+state)
    return "".join(out)
def verify(path):
    code=code_only(Path(path).read_text())
    pairs={"}":"{",")":"(","]":"["}
    stack=[]; line=1
    for c in code:
        if c=="\n": line+=1; continue
        if c in "{([": stack.append((c,line))
        elif c in "})]":
            if not stack or stack[-1][0]!=pairs[c]:
                raise SystemExit(f"Java delimiter mismatch {path} line={line}")
            stack.pop()
    if stack: raise SystemExit(f"Java unclosed delimiter {path} {stack[-1]}")
    print("Java lexical structure PASS",Path(path).name)
for f in sys.argv[1:]: verify(f)
PY

# Runtime parser compatibility audit across the COMPLETE 26484 shader set that
# participates in the new alignment/opponent path, not just the crashed shader.
cat > "$TMP/shaders.txt" <<'EOF'
app/src/main/assets/shaders/motionv2/direct_rgb_accumulate.glsl
app/src/main/assets/shaders/motionv2/mfsr_chroma_guide.glsl
app/src/main/assets/shaders/motionv2/mfsr_flow_expand.glsl
app/src/main/assets/shaders/motionv2/mfsr_lk_refine_level.glsl
app/src/main/assets/shaders/motionv2/mfsr_lk_select_candidate.glsl
app/src/main/assets/shaders/motionv2/mfsr_low_support_reference.glsl
app/src/main/assets/shaders/motionv2/mfsr_mgc_covariance.glsl
app/src/main/assets/shaders/motionv2/mfsr_robustness_half.glsl
EOF

python3 - "$CAND" "$TMP/shaders.txt" <<'PY'
from pathlib import Path
import sys,re
root=Path(sys.argv[1])
for rel in Path(sys.argv[2]).read_text().splitlines():
    p=root/rel
    if not p.is_file(): raise SystemExit("missing shader "+rel)
    for n,line in enumerate(p.read_text().splitlines(),1):
        if "layout" not in line: continue
        # Photon GLInterface.getLayouts() is line-oriented. More than one layout
        # declaration on a physical line is always unsafe for this parser.
        if line.count("layout(")>1:
            raise SystemExit(f"runtime layout parser hazard {rel}:{n}: {line}")
        if "layout(" in line:
            inside=line[line.find("(")+1:line.rfind(")")]
            for token in inside.split(","):
                t=token.replace(" ","")
                if t.startswith("binding="):
                    int(t.split("=",1)[1])  # exact failure class from 26484 runtime
print("Photon runtime layout-parser compatibility PASS for complete 26484 shader set")
PY

# Real GLSL compilation of all eight coupled shaders.
: > "$SHADERLOG"
compile_shader(){
    local f="$1"; local n="$(basename "$f")"
    python3 - "$f" "$TMP/$n.comp" <<'PY'
from pathlib import Path
import sys
s=Path(sys.argv[1]).read_text()
s=s.replace("#define LAYOUT //\nLAYOUT",
            "#version 310 es\nlayout(local_size_x=8,local_size_y=8,local_size_z=1) in;",1)
Path(sys.argv[2]).write_text(s)
PY
    glslangValidator -S comp "$TMP/$n.comp" >> "$SHADERLOG" 2>&1
}

shader_fail=0
while IFS= read -r rel; do
    if compile_shader "$CAND/$rel"; then
        echo "GLSL compile PASS $(basename "$rel")" >> "$SHADERLOG"
    else
        echo "GLSL compile FAIL $(basename "$rel")" >> "$SHADERLOG"
        shader_fail=1
    fi
done < "$TMP/shaders.txt"
if [[ "$shader_fail" -ne 0 ]]; then
    cat "$SHADERLOG"
    fail "one or more coupled 26484/26485 shaders failed glslangValidator"
fi
pass "all coupled 26484/26485 shaders glslangValidator PASS"

# Keep known Adreno guards.
while IFS= read -r rel; do
    f="$CAND/$rel"
    ! grep -Eq 'layout\((rg32f|rg16f|r16f)[^)]*\)[^;]*writeonly image2D' "$f" \
        || fail "Adreno hazardous writable format $(basename "$f")"
    ! grep -Eq '\b(float|vec[234]|int|ivec[234])\s+sample\b' "$f" \
        || fail "reserved GLSL identifier sample in $(basename "$f")"
done < "$TMP/shaders.txt"
pass "Adreno runtime-portability guard"

# Produce exact 26485 functional delta from successful 26484 BEFORE version bump.
(
    cd "$CAND"
    git diff --binary -- app/src/main
) > "$DELTAOUT"
[[ -s "$DELTAOUT" ]] || fail "26485 functional delta empty"

# Bump candidate version/build ONLY immediately before full temporary Gradle proof.
python3 - "$CAND/app/version.properties" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]); s=p.read_text()
if s.count("VERSION_NAME=0.9726484")!=1 or s.count("VERSION_BUILD=26484")!=1:
    raise SystemExit("candidate 26485 version anchors invalid")
p.write_text(s.replace("VERSION_NAME=0.9726484","VERSION_NAME=0.9726485",1)
              .replace("VERSION_BUILD=26484","VERSION_BUILD=26485",1))
PY

# Snapshot canonical source BEFORE Gradle so generated native headers can never
# silently become the next checkpoint.
python3 - "$CAND" "$TMP/candidate_prebuild.sha256" <<'PY'
from pathlib import Path
import hashlib,sys
root=Path(sys.argv[1]); out=Path(sys.argv[2])
ignore={
"app/src/main/cpp/deps/archive.h",
"app/src/main/cpp/deps/archive_entry.h",
"app/src/main/cpp/deps/technicallyflac.h",
"app/src/main/cpp/deps/tiny_dng_writer.h",
}
rows=[]
for p in (root/"app/src/main").rglob("*"):
    if p.is_file():
        rel=str(p.relative_to(root)).replace("\\","/")
        if rel in ignore: continue
        rows.append((rel,hashlib.sha256(p.read_bytes()).hexdigest()))
vp=root/"app/version.properties"
rows.append(("app/version.properties",hashlib.sha256(vp.read_bytes()).hexdigest()))
out.write_text("".join(f"{h}  {r}\n" for r,h in sorted(rows)))
PY

(
    cd "$CAND"
    chmod +x gradlew
    ./gradlew assembleDebug --no-daemon --stacktrace
) 2>&1 | tee "$CANDLOG"
[[ "${PIPESTATUS[0]}" -eq 0 ]] || fail "temporary candidate Gradle build"

# Prove Gradle did not mutate canonical app source.
(
    cd "$CAND"
    sha256sum -c "$TMP/candidate_prebuild.sha256" >/dev/null
) || fail "temporary Gradle mutated canonical source"
pass "Temporary-copy validation: PASS"
pass "PRE-BUILD SAFETY PROOF PASSED"

# ----------------------------------------------------------------------
# FINAL BUILD — prevent recurrence of the 26484 65-symbol failure.
# Reconstruct the COMPLETE successful 26484 graph in the Action checkout,
# then overlay ONLY the already-built two-file 26485 source delta.
# ----------------------------------------------------------------------
git apply --check --binary "$BASE26383_PATCH"
git apply --binary "$BASE26383_PATCH"
sha256sum -c "$BASE26383_HASHES" >/dev/null

git apply --check --binary "$DELTA26484"
git apply --binary "$DELTA26484"

python3 - <<'PY'
from pathlib import Path
p=Path("app/version.properties"); s=p.read_text()
if s.count("VERSION_NAME=0.9726483")!=1 or s.count("VERSION_BUILD=26483")!=1:
    raise SystemExit("final 26484 reconstruction version anchor mismatch")
p.write_text(s.replace("VERSION_NAME=0.9726483","VERSION_NAME=0.9726484",1)
              .replace("VERSION_BUILD=26483","VERSION_BUILD=26484",1))
PY
pass "final complete successful 26484 dependency graph reconstructed"

# Overlay the exact candidate source files.
while IFS= read -r rel; do
    mkdir -p "$(dirname "$rel")"
    cp "$CAND/$rel" "$rel"
done < "$TMP/allow.txt"

# Version increment AND final Gradle build remain in one guarded command block.
{
python3 - <<'PY'
from pathlib import Path
p=Path("app/version.properties"); s=p.read_text()
if s.count("VERSION_NAME=0.9726484")!=1 or s.count("VERSION_BUILD=26484")!=1:
    raise SystemExit("final 26485 version anchors invalid")
p.write_text(s.replace("VERSION_NAME=0.9726484","VERSION_NAME=0.9726485",1)
              .replace("VERSION_BUILD=26484","VERSION_BUILD=26485",1))
PY

# Full candidate/final canonical source equality BEFORE Gradle.
python3 - "$CAND" "$(pwd)" <<'PY'
from pathlib import Path
import hashlib,sys
a,b=Path(sys.argv[1]),Path(sys.argv[2])
ignore={
"app/src/main/cpp/deps/archive.h",
"app/src/main/cpp/deps/archive_entry.h",
"app/src/main/cpp/deps/technicallyflac.h",
"app/src/main/cpp/deps/tiny_dng_writer.h",
}
def h(root):
    out={}
    for p in (root/"app/src/main").rglob("*"):
        if p.is_file():
            rel=str(p.relative_to(root)).replace("\\","/")
            if rel in ignore: continue
            out[rel]=hashlib.sha256(p.read_bytes()).hexdigest()
    vp=root/"app/version.properties"
    out["app/version.properties"]=hashlib.sha256(vp.read_bytes()).hexdigest()
    return out
x,y=h(a),h(b)
if x!=y:
    bad=sorted(k for k in x.keys()|y.keys() if x.get(k)!=y.get(k))
    raise SystemExit("candidate/final canonical source mismatch BEFORE final Gradle: "+repr(bad[:80]))
print("full candidate/final canonical source parity PASS")
PY

# Capture the COMPLETE canonical checkpoint BEFORE Gradle-generated source noise.
git add -N app/src/main app/version.properties >/dev/null 2>&1 || true
git diff --binary "$EXPECTED_APP_BASE" -- app/src/main app/version.properties > "$SOURCEPATCH"
[[ -s "$SOURCEPATCH" ]] || fail "complete 26485 source patch empty"

python3 - "$(pwd)" "$AFTERHASH" <<'PY'
from pathlib import Path
import hashlib,sys
root=Path(sys.argv[1]); out=Path(sys.argv[2])
ignore={
"app/src/main/cpp/deps/archive.h",
"app/src/main/cpp/deps/archive_entry.h",
"app/src/main/cpp/deps/technicallyflac.h",
"app/src/main/cpp/deps/tiny_dng_writer.h",
}
rows=[]
for p in (root/"app/src/main").rglob("*"):
    if p.is_file():
        rel=str(p.relative_to(root)).replace("\\","/")
        if rel in ignore: continue
        rows.append((rel,hashlib.sha256(p.read_bytes()).hexdigest()))
vp=root/"app/version.properties"
rows.append(("app/version.properties",hashlib.sha256(vp.read_bytes()).hexdigest()))
out.write_text("".join(f"{h}  {r}\n" for r,h in sorted(rows)))
PY
cp "$AFTERHASH" "$PREBUILDHASH"

chmod +x gradlew
./gradlew assembleDebug --no-daemon --stacktrace 2>&1 | tee "$FINALLOG"
}
[[ "${PIPESTATUS[0]}" -eq 0 ]] || fail "final 26485 Gradle build"

# Full canonical source must still match the pre-build checkpoint after final Gradle.
sha256sum -c "$PREBUILDHASH" >/dev/null || fail "final Gradle mutated canonical source"

# Locate and publish exactly one APK.
mapfile -t apks < <(find app/build/outputs/apk -type f -name '*.apk' | sort)
[[ ${#apks[@]} -ge 1 ]] || fail "no APK output"
rm -f IrisCamera-0.9726485-26485-*.apk
cp "${apks[-1]}" "$APK_NAME"
[[ -s "$APK_NAME" ]] || fail "published 26485 APK missing"

mkdir -p "$OUTDIR/next_baseline_inputs"
cp "$SOURCEPATCH" "$OUTDIR/next_baseline_inputs/26485_successful_source.patch"
cp "$AFTERHASH" "$OUTDIR/next_baseline_inputs/26485_successful_after.sha256"
cp "$REPO/$TRANSFORM" "$OUTDIR/next_baseline_inputs/"

cat > "$REPORT" <<EOF
26485 RUNTIME + FULL SHUTTER FIX V1
Version=$NEW_VERSION
Build=$NEW_BUILD
Branch=$BRANCH
BackupBranch=$BACKUP_BRANCH
BackupExpected=$BACKUP_EXPECTED
Base26383PatchSHA=$BASE26383_PATCH_SHA
Base26383ManifestSHA=$BASE26383_HASHES_SHA
Successful26484DeltaSHA=$DELTA26484_SHA
TransformSHA=$TRANSFORM_SHA
APK=$APK_NAME
APK_SHA256=$(sha "$APK_NAME")
SourcePatchSHA256=$(sha "$SOURCEPATCH")
AfterManifestSHA256=$(sha "$AFTERHASH")
RuntimeFix=one layout declaration per physical line for mfsr_mgc_covariance; complete 26484 shader-set runtime-parser audit
ShutterFix=full rolling ZSL buffer at press is authoritative; valid safe group processes immediately instead of 1.4s normal top-up; existing short-highlight gate preserved
BuildFailurePrevention=final checkout reconstructs full successful 26483 plus successful 26484 delta before 26485 overlay; complete candidate/final canonical parity required before final Gradle
EOF

sha256sum "$APK_NAME" "$SOURCEPATCH" "$AFTERHASH" "$REPORT" "$DELTAOUT" \
    > "$OUTDIR/26485_artifact_hashes.sha256"

pass "26485 canonical checkpoint package created"
echo "26485_SOURCE_PATCH_SHA256=$(sha "$SOURCEPATCH")"
echo "26485_AFTER_MANIFEST_SHA256=$(sha "$AFTERHASH")"
echo "26485 BUILD SUCCESS"
