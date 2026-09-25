#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
resolve_glslang_compiler(){ local root="$1" compiler="" compat=""; compiler="$(find "$root" -type f -name glslang -print -quit)"; if [[ -z "$compiler" ]]; then compat="$(find "$root" \( -type f -o -type l \) -name glslangValidator -print -quit)"; if [[ -n "$compat" ]]; then compiler="$(readlink -f "$compat" 2>/dev/null || true)"; fi; fi; [[ -n "$compiler" && -f "$compiler" ]] || return 1; printf '%s\n' "$compiler"; }
ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
UPLOAD_BASE_COMMIT="e6223da276e1eb439b572f17e0d4c2e959bf31f8"
RUNTIME_AUTHORITY_COMMIT="e6223da276e1eb439b572f17e0d4c2e959bf31f8"
BASE_RUN_ID="36176861812"
BASE_ARTIFACT_ID="10882518532"
BASE_ARTIFACT_NAME="photon-26705-normal-ae-short-headroom"
BASE_ARTIFACT_SHA="86095b5c6220a3a49d47d453eab1e90cf5e0e0beb997dd692bfb2591a01293d8"
BASE_TAR_SHA="6bfd4b2203b7483b7bde6324e54d13cb1afbacff8d04b7b347f19f29dad561ef"
VERSION_NAME="0.9726706"; VERSION_BUILD="26706"
GLSLANG_VERSION="16.5.0"
GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"
GLSLANG_URL="https://github.com/KhronosGroup/glslang/releases/download/16.5.0/glslang-16.5.0-linux-x86_64-release.tar.gz"
MECHANICS_AUTHORITY_COMMIT="9523e5d8a72e687385ba7fe9000072cb915404a1"
AUTH_26704_BUILD_SCRIPT_BLOB="02e9b9fc9ed02c30f01ca76af18cf7c67817174b"
AUTH_26704_WORKFLOW_BLOB="e7678fff1c3256d79ead17f8450bf67797dd3dc1"
AUTH_26705_R1_COMMIT="e6223da276e1eb439b572f17e0d4c2e959bf31f8"
AUTH_26705_R1_BUILD_SCRIPT_BLOB="df0004317fa1387c44209f6225d02b6d39697c53"
AUTH_26705_R1_WORKFLOW_BLOB="e01028079c65bdbbb67e34824526a6f5379d3350"
HANDOFF="$ROOT/26706_HANDOFF_HASHES.sha256"; UPLOADS="$ROOT/26706_UPLOAD_PATHS.txt"
BASE_FULL="$ROOT/26706_BASE_26705_FULL_APP.sha256"; CAND_FULL="$ROOT/26706_EXPECTED_CANDIDATE_FULL_APP.sha256"
BASE_PROTECTED="$ROOT/26706_PROTECTED_UNCHANGED_BASE.sha256"; CAND_PROTECTED="$ROOT/26706_PROTECTED_UNCHANGED_CANDIDATE.sha256"
BASE_NATIVE="$ROOT/26706_NATIVE_PROTECTED_BASE.sha256"; CAND_NATIVE="$ROOT/26706_NATIVE_PROTECTED_CANDIDATE.sha256"
BASE_NATIVE_FULL="$ROOT/26706_NATIVE_FULL_BASE.sha256"; CAND_NATIVE_FULL="$ROOT/26706_NATIVE_FULL_CANDIDATE.sha256"
BASE_VENDOR="$ROOT/26706_VENDOR_PROTECTED_BASE.sha256"; CAND_VENDOR="$ROOT/26706_VENDOR_PROTECTED_CANDIDATE.sha256"
BASE_DNG="$ROOT/26706_DNG_BASE.sha256"; CAND_DNG="$ROOT/26706_DNG_CANDIDATE.sha256"
SHADER_BASE="$ROOT/26706_ASSET_SHADER_UNIVERSE_BASE.sha256"; SHADER_CAND="$ROOT/26706_ASSET_SHADER_UNIVERSE_CANDIDATE.sha256"; SHADER_PIN="$ROOT/26706_RUNTIME_EXPANDED_SHADERS.sha256"
CHANGED="$ROOT/26706_RUNTIME_CHANGED_PATHS.txt"; ADDED="$ROOT/26706_ADDED_PATHS_MUST_BE_ABSENT.txt"; PREWRITE="$ROOT/26706_PREWRITE_26705_SOURCE_HASHES.sha256"; EXPECTED_CHANGED="$ROOT/26706_EXPECTED_CHANGED_SOURCE_HASHES.sha256"
FORWARD="$ROOT/26706_RUNTIME_DELTA_FROM_26705.patch"; ROLLBACK="$ROOT/26706_RUNTIME_ROLLBACK_TO_26705.patch"
TRANSFORM="$ROOT/transform_26706.py"; VALIDATE="$ROOT/validate_26706.py"; AUTHORITY="$ROOT/verify_26706_authority.py"; INFRA="$ROOT/verify_26706_infrastructure.py"; PATCHVERIFY="$ROOT/verify_26706_patches.py"; GATEVERIFY="$ROOT/verify_26706_regressions.py"; SHADERVERIFY="$ROOT/verify_26706_shaders.py"
BUILD_SCRIPT="$ROOT/build_26706_visual_highlight_spacing.sh"; WORKFLOW="$ROOT/.github/workflows/build-26706-visual-highlight-spacing.yml"
OUT="$ROOT/build_26706_visual_highlight_spacing_outputs"; WORK="$ROOT/.build_26706_visual_highlight_spacing_work"
ARTZIP="$WORK/26705_artifact.zip"; ARTDIR="$WORK/artifact_26705"; BASE="$WORK/exact_successful_26705_compiled_candidate"; AFTER="$WORK/candidate_26706"; AFTER2="$WORK/candidate_26706_replay"; LIVE_CANON="$WORK/live_compiler_candidate_snapshot"; POST="$WORK/postbuild_source_snapshot"; GLSLANG_DIR="$WORK/glslang-${GLSLANG_VERSION}"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-visual-highlight-spacing-debug.apk"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"; LOCAL_ART=""; LOCAL_ONLY=0
if [[ "${1:-}" == "--local-prebuild" ]]; then [[ -n "${2:-}" ]] || fail "--local-prebuild requires exact successful 26705 artifact ZIP"; LOCAL_ART="$2"; LOCAL_ONLY=1; elif [[ -n "${1:-}" ]]; then fail "unknown argument: $1"; fi
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR" "$BASE" "$AFTER" "$AFTER2"
cat > "$OUT/26706_COMPILER_STATUS.txt" <<'STATUS'
REAL GLSL COMPILE: NOT RUN YET
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
JNI CALLBACK CLASS ABI: NOT RUN YET
NATIVE/NDK COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
APK JNI CONTRACT: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
STATUS
cat > "$OUT/26706_STRICT_HANDOFF_REPORT.txt" <<'REPORT'
RUNTIME AUTHORITY: NOT RUN
VERIFICATION MECHANICS AUTHORITY: NOT RUN
BACKUP STATUS: NONE (user explicitly requested no backup; exact successful 26705 R1 authority + deterministic rollback patch)
CHANGED RUNTIME SCOPE: NOT RUN
INFRASTRUCTURE CHANGED FILES: 26706 identity/authority/scope/regression/shader-proof/build/workflow/handoff wrappers only; successful 26704 compiler-build mechanics preserved; successful 26705 R1 APK marker fix inherited
INFRASTRUCTURE DELTA FROM LAST SUCCESS: functional compiler/build stage order ZERO; exact successful 26704 dual-glslang/Gradle/NDK/patch/assemble ordering preserved; 26705 R1 inherited-marker APK verifier retained; shader proof covers exactly 3 modified runtime-expanded variants
RUNTIME OWNERSHIP: NOT RUN
26705 EXPOSURE/SHORT PRESERVATION: NOT RUN
PRODUCTION SHORT FUSION PRESERVATION: NOT RUN
VISUAL HIGHLIGHT SPACING: NOT RUN
SAMPLED FUSION OBSERVABILITY: NOT RUN
SPEKTRA PRESERVATION: NOT RUN
UHDR/GAINMAP PRESERVATION: NOT RUN
NATIVE INVARIANCE: NOT RUN
INHERITED 26705 CONTRACTS: NOT RUN
EXACT PRIOR RUNTIME AUTHORITY: NOT RUN
PROTECTED/DNG/NATIVE/VENDOR INVARIANCE: NOT RUN
RUNTIME-EXPANDED GLSL RESERVED SCAN: NOT RUN
REAL GLSL COMPILE: NOT RUN
REAL KOTLIN COMPILE: NOT RUN
REAL JAVA COMPILE: NOT RUN
JNI CALLBACK CLASS ABI: NOT RUN
REAL NATIVE/NDK COMPILE: NOT RUN
FORWARD PATCH FUZZ=0: NOT RUN
ROLLBACK PATCH FUZZ=0: NOT RUN
PRE-BUILD SAFETY PROOF: NOT RUN
FULL ANDROID ASSEMBLE: NOT RUN
EXACTLY ONE APK: NOT RUN
APK JNI CONTRACT: NOT RUN
POST-BUILD INVARIANCE: NOT RUN
CLEAN ARTIFACT SOURCE EXPORT: NOT RUN
TARGET VERSION/BUILD: 0.9726706 / 26706
REPORT
set_report(){ local key="$1" val="$2" tmp="$OUT/.report.tmp"; awk -v key="$key:" -v val="$val" 'BEGIN{f=0} index($0,key)==1{print key" "val;f=1;next}{print} END{if(!f)exit 42}' "$OUT/26706_STRICT_HANDOFF_REPORT.txt" > "$tmp" || fail "report key missing $key"; mv "$tmp" "$OUT/26706_STRICT_HANDOFF_REPORT.txt"; }
set_compiler(){ local key="$1" val="$2" tmp="$OUT/.compiler.tmp"; awk -v key="$key:" -v val="$val" 'BEGIN{f=0} index($0,key)==1{print key" "val;f=1;next}{print} END{if(!f)exit 42}' "$OUT/26706_COMPILER_STATUS.txt" > "$tmp" || fail "compiler key missing $key"; mv "$tmp" "$OUT/26706_COMPILER_STATUS.txt"; }
snapshot_candidate_from_authority(){ local authority_root="$1" live_root="$2" dest_root="$3"; rm -rf "$dest_root"; mkdir -p "$dest_root"; cp -a "$authority_root/." "$dest_root/"; rm -rf "$dest_root/app/src"; cp -a "$live_root/app/src" "$dest_root/app/"; cp -a "$live_root/app/build.gradle" "$dest_root/app/build.gradle"; cp -a "$live_root/app/version.properties" "$dest_root/app/version.properties"; }
compare_app_trees(){ python3 -S - "$1" "$2" <<'PY2'
from pathlib import Path
import hashlib,sys
def H(r):return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((Path(r)/'app').rglob('*')) if p.is_file()}
a=H(sys.argv[1]);b=H(sys.argv[2]);assert len(a)==len(b)==1823 and a==b,(len(a),len(b),sorted(set(a)^set(b))[:10]);print('PASS authority-seeded candidate byte-identical: 1823 files')
PY2
}
verify_package(){
 [[ -f "$HANDOFF" && -f "$UPLOADS" && -d "$ROOT/handoff_payload_26706" ]] || fail "sealed 26706 package incomplete"
 [[ "$(find "$ROOT/handoff_payload_26706" -type f | wc -l)" -eq 6 ]] || fail "runtime payload must contain exactly 6 files"
 [[ "$(wc -l < "$CHANGED")" -eq 6 ]] || fail "26706 changed-file count"
 [[ ! -s "$ADDED" ]] || fail "26706 added-file count"
 sha256sum -c "$HANDOFF" >/dev/null
 [[ "$(wc -l < "$BASE_FULL")" -eq 1823 && "$(wc -l < "$CAND_FULL")" -eq 1823 ]] || fail "full app count"
 [[ "$(wc -l < "$BASE_PROTECTED")" -eq 1817 && "$(wc -l < "$BASE_NATIVE")" -eq 819 && "$(wc -l < "$BASE_VENDOR")" -eq 778 && "$(wc -l < "$BASE_DNG")" -eq 7 ]] || fail "protected/native/vendor/DNG counts"
 [[ "$(wc -l < "$BASE_NATIVE_FULL")" -eq 819 && "$(wc -l < "$CAND_NATIVE_FULL")" -eq 819 ]] || fail "native-full count"
 [[ "$(wc -l < "$SHADER_BASE")" -eq 271 && "$(wc -l < "$SHADER_CAND")" -eq 271 && "$(wc -l < "$SHADER_PIN")" -eq 3 ]] || fail "shader counts"
 cmp "$BASE_PROTECTED" "$CAND_PROTECTED"; cmp "$BASE_NATIVE" "$CAND_NATIVE"; cmp "$BASE_VENDOR" "$CAND_VENDOR"; cmp "$BASE_DNG" "$CAND_DNG"
 bash -n "$BUILD_SCRIPT"
 python3 -S - "$TRANSFORM" "$VALIDATE" "$AUTHORITY" "$INFRA" "$PATCHVERIFY" "$GATEVERIFY" "$SHADERVERIFY" <<'PY2'
import ast,sys
from pathlib import Path
allowed=set(sys.stdlib_module_names)
for raw in sys.argv[1:]:
 p=Path(raw);src=p.read_text();tree=ast.parse(src,filename=str(p));bad=[]
 for n in ast.walk(tree):
  names=[]
  if isinstance(n,ast.Import):names=[a.name.split('.',1)[0] for a in n.names]
  elif isinstance(n,ast.ImportFrom) and n.module:names=[n.module.split('.',1)[0]]
  bad += [x for x in names if x not in allowed]
 if bad:raise SystemExit(f'FAIL non-stdlib dependency {p.name}: {sorted(set(bad))}')
 compile(src,str(p),'exec')
print('PASS sealed Python stdlib-only syntax/import gate')
PY2
 ! find "$ROOT" \( -type d -name '__pycache__' -o -type f -name '*.pyc' \) | grep -q . || fail "transient Python files packaged"
 ! find "$ROOT" -type f -name '*.apk' | grep -q . || fail "APK must not be packaged in handoff"
}
verify_scope(){
 if [[ "$LOCAL_ONLY" -eq 1 ]]; then set_report "CHANGED RUNTIME SCOPE" "PASS (local sealed candidate: exact 6 modified paths; 0 additions/removals; exact successful 26705 R1 compiled authority)"; return; fi
 [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch"
 git merge-base --is-ancestor "$UPLOAD_BASE_COMMIT" HEAD || fail "successful 26705 R1 authority commit not ancestor"
 [[ "$(git rev-parse "${MECHANICS_AUTHORITY_COMMIT}:build_26704_short_fusion_body_tone.sh")" == "$AUTH_26704_BUILD_SCRIPT_BLOB" ]] || fail "successful 26704 build-script blob changed"
 [[ "$(git rev-parse "${MECHANICS_AUTHORITY_COMMIT}:.github/workflows/build-26704-short-fusion-body-tone.yml")" == "$AUTH_26704_WORKFLOW_BLOB" ]] || fail "successful 26704 workflow blob changed"
 [[ "$(git rev-parse "${AUTH_26705_R1_COMMIT}:build_26705_normal_ae_short_headroom.sh")" == "$AUTH_26705_R1_BUILD_SCRIPT_BLOB" ]] || fail "successful 26705 R1 build-script blob changed"
 [[ "$(git rev-parse "${AUTH_26705_R1_COMMIT}:.github/workflows/build-26705-normal-ae-short-headroom.yml")" == "$AUTH_26705_R1_WORKFLOW_BLOB" ]] || fail "successful 26705 R1 workflow blob changed"
 git diff --name-only "$UPLOAD_BASE_COMMIT"..HEAD | sort > "$WORK/actual_upload_scope.txt"; sort "$UPLOADS" > "$WORK/expected_upload_scope.txt"; diff -u "$WORK/expected_upload_scope.txt" "$WORK/actual_upload_scope.txt" || fail "26706 upload scope mismatch"
 ! grep -Eq '^app/' "$WORK/actual_upload_scope.txt" || fail "handoff commit contains live app source"
 set_report "CHANGED RUNTIME SCOPE" "PASS (6 runtime paths carried only inside sealed payload; live app source not committed)"
}
obtain_authority(){
 if [[ -n "$LOCAL_ART" ]]; then cp "$LOCAL_ART" "$ARTZIP"; else
  [[ -n "$TOKEN" ]] || fail "GITHUB_TOKEN missing"
  curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${BASE_ARTIFACT_ID}/zip" -o "$ARTZIP"
 fi
 [[ "$(sha "$ARTZIP")" == "$BASE_ARTIFACT_SHA" ]] || fail "successful 26705 R1 artifact ZIP SHA"
 unzip -q "$ARTZIP" -d "$ARTDIR"
 local tarball="$ARTDIR/build_26705_normal_ae_short_headroom_outputs/26705_candidate_app_source.tar.gz"
 [[ -f "$tarball" && "$(sha "$tarball")" == "$BASE_TAR_SHA" ]] || fail "successful 26705 R1 compiled candidate TAR authority"
 tar -xzf "$tarball" -C "$BASE"
 (cd "$BASE" && sha256sum -c "$BASE_FULL" >/dev/null) || fail "exact successful 26705 R1 base manifest"
 set_report "RUNTIME AUTHORITY" "PASS (successful 26705 R1 commit ${RUNTIME_AUTHORITY_COMMIT}/run ${BASE_RUN_ID}/artifact ${BASE_ARTIFACT_ID}/artifact SHA ${BASE_ARTIFACT_SHA}/compiled candidate TAR ${BASE_TAR_SHA})"
 set_report "EXACT PRIOR RUNTIME AUTHORITY" "PASS (successful 26705 R1 compiled candidate is sole runtime authority)"
}
make_candidate(){
 python3 -S "$TRANSFORM" "$BASE" "$AFTER" | tee "$OUT/26706_transform.txt"; python3 -S "$TRANSFORM" "$BASE" "$AFTER2" | tee "$OUT/26706_transform_replay.txt"; compare_app_trees "$AFTER" "$AFTER2"
 python3 -S "$VALIDATE" "$BASE" "$AFTER" | tee "$OUT/26706_semantic_validation.txt"; python3 -S "$GATEVERIFY" "$BASE" "$AFTER" | tee "$OUT/26706_regressions.txt"; python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$AFTER" | tee "$OUT/26706_authority_candidate.txt"
 python3 -S "$SHADERVERIFY" "$ROOT" "$BASE" "$AFTER" | tee "$OUT/26706_shader_static_validation.txt"
 set_report "RUNTIME OWNERSHIP" "PASS (exact successful 26705 R1 candidate inherited; only global upper-tone spacing, sampled non-production fusion observability, and version changed)"
 set_report "26705 EXPOSURE/SHORT PRESERVATION" "PASS (CaptureController byte-identical: proper NORMAL AE, adaptive deep SHORT, settled-only 26680 latch retained)"
 set_report "PRODUCTION SHORT FUSION PRESERVATION" "PASS (universalNormalMasterShortFusion26651 byte-identical to successful 26705 R1; no SHORT ownership broadening)"
 set_report "VISUAL HIGHLIGHT SPACING" "PASS (26623 broad upper-tone mapping monotone; source guide <=0.65 invariant; broad pressure reserves more near-white/output spacing; visual flattening counts below hard sensor clip)"
 set_report "SAMPLED FUSION OBSERVABILITY" "PASS (64x48 sampled decision/radiance readback only; full-frame decision readback remains dormant; telemetry never feeds reconstruction)"
 set_report "SPEKTRA PRESERVATION" "PASS (successful 26705 R1 inherited Spektra geometry/orientation/native owners protected)"
 set_report "UHDR/GAINMAP PRESERVATION" "PASS (UHDR ownership/metadata unchanged; gainmap uses the same monotone 26706 display-tail spacing as SDR owner)"
 set_report "NATIVE INVARIANCE" "PASS (all 819 native files invariant; no JNI/native source changes)"
 set_report "INHERITED 26705 CONTRACTS" "PASS (26705 exposure/SHORT/chroma/body-tone/settings/HEIC/DNG/Sabre production fusion protected outside explicit scope)"
 set_report "PROTECTED/DNG/NATIVE/VENDOR INVARIANCE" "PASS (1817 protected; 819 native; 778 vendor; 7 DNG invariant; exactly 2/271 asset shaders intentionally changed)"
 set_report "RUNTIME-EXPANDED GLSL RESERVED SCAN" "PASS (3 exact modified runtime-expanded variants; complete reserved/structure/hash scan)"
}
verify_successful_26704_mechanics(){ python3 -S "$INFRA" "$BUILD_SCRIPT" "$WORKFLOW" | tee "$OUT/26706_infrastructure.txt"; set_report "VERIFICATION MECHANICS AUTHORITY" "PASS (exact successful 26704 compiler/build sequence ${AUTH_26704_BUILD_SCRIPT_BLOB}/${AUTH_26704_WORKFLOW_BLOB}; successful 26705 R1 wrapper ${AUTH_26705_R1_BUILD_SCRIPT_BLOB}/${AUTH_26705_R1_WORKFLOW_BLOB} including inherited body-tone APK marker regression; outer stage order unchanged)"; }
prepare_glslang(){ local archive="$WORK/glslang-${GLSLANG_VERSION}.tar.gz" compiler; curl -L --fail --retry 3 "$GLSLANG_URL" -o "$archive"; [[ "$(sha "$archive")" == "$GLSLANG_ARCHIVE_SHA" ]] || fail "glslang archive SHA"; rm -rf "$GLSLANG_DIR"; mkdir -p "$GLSLANG_DIR"; tar -xzf "$archive" -C "$GLSLANG_DIR"; compiler="$(resolve_glslang_compiler "$GLSLANG_DIR")" || fail "pinned glslang compiler missing"; "$compiler" --version | tee "$OUT/26706_glslang_version.txt"; export IRIS26706_GLSLANG="$compiler"; export IRIS26681_SPEKTRA_GLSLANG="$compiler"; [[ -x "$IRIS26706_GLSLANG" && -x "$IRIS26681_SPEKTRA_GLSLANG" ]] || fail "pinned glslang is not executable"; }
compile_modified_runtime_shaders(){ python3 -S "$SHADERVERIFY" "$ROOT" "$BASE" "$AFTER" --compiler "$IRIS26706_GLSLANG" | tee "$OUT/26706_shader_compiler_validation.txt"; }
compile_spektra_raw_shader(){ local compiler="$IRIS26706_GLSLANG" outspv="$WORK/SpektraRawDevelop.comp.spv"; "$compiler" -V "$AFTER/app/src/main/cpp/spektra/SpektraRawDevelop.comp" -o "$outspv" 2>&1 | tee "$OUT/26706_glslang_raw_develop.log"; [[ -s "$outspv" ]] || fail "Spektra RAW shader SPIR-V missing"; sha256sum "$AFTER/app/src/main/cpp/spektra/SpektraRawDevelop.comp" "$outspv" > "$OUT/26706_spektra_raw_shader_compile.sha256"; set_report "REAL GLSL COMPILE" "PASS (pinned glslang 16.5.0; exact 3 modified runtime-expanded shaders + inherited SpektraRawDevelop gate)"; set_compiler "REAL GLSL COMPILE" "PASS (pinned glslang 16.5.0; 3 modified runtime-expanded + inherited Spektra RAW)"; }
verify_candidate_patches(){ python3 -S "$PATCHVERIFY" "$ROOT" "$BASE" "$AFTER" | tee "$OUT/26706_patch_validation.txt"; set_report "FORWARD PATCH FUZZ=0" "PASS"; set_report "ROLLBACK PATCH FUZZ=0" "PASS"; }
install_frozen_candidate_live(){ rm -rf "$ROOT/app/src"; cp -a "$AFTER/app/src" "$ROOT/app/"; cp -a "$AFTER/app/build.gradle" "$ROOT/app/build.gradle"; cp -a "$AFTER/app/version.properties" "$ROOT/app/version.properties"; snapshot_candidate_from_authority "$BASE" "$ROOT" "$LIVE_CANON"; compare_app_trees "$AFTER" "$LIVE_CANON"; }
verify_compiled_jni_callback(){ local cls; cls="$(find "$ROOT/app/build" -type f -path '*/com/unspektrawesome/diagnostics/InternalLogRecorder.class' -print -quit)"; [[ -n "$cls" && -f "$cls" ]] || fail "compiled InternalLogRecorder.class missing"; javap -s "$cls" | tee "$OUT/26706_internal_log_recorder_javap.txt"; grep -Fq 'public static void recordNative(int, java.lang.String, java.lang.String);' "$OUT/26706_internal_log_recorder_javap.txt" || fail "compiled recordNative method missing"; grep -Fq 'descriptor: (ILjava/lang/String;Ljava/lang/String;)V' "$OUT/26706_internal_log_recorder_javap.txt" || fail "compiled recordNative JNI descriptor mismatch"; set_report "JNI CALLBACK CLASS ABI" "PASS"; set_compiler "JNI CALLBACK CLASS ABI" "PASS"; }
verify_compiled_motion_jni(){ local cls; cls="$(find "$ROOT/app/build" -type f -path '*/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.class' -print -quit)"; [[ -n "$cls" && -f "$cls" ]] || fail "compiled MotionV2Jpeg444Encoder.class missing"; javap -s -private "$cls" | tee "$OUT/26706_motionv2_encoder_javap.txt"; grep -Fq 'writeTrue2xNative' "$OUT/26706_motionv2_encoder_javap.txt" || fail "compiled writeTrue2xNative missing"; grep -Fq 'descriptor: (Landroid/graphics/Bitmap;Ljava/lang/String;IIIIIIIZF[F[F[FZ[FIII[FIIIFFFFFFFZZLjava/nio/ByteBuffer;IIIILandroid/graphics/Bitmap;[F[IIILjava/lang/String;FFLjava/lang/String;I)Z' "$OUT/26706_motionv2_encoder_javap.txt" || fail "compiled writeTrue2xNative 26706 descriptor mismatch"; grep -Fq 'jfloat sceneWhite,jfloat bodyToneStrength,jboolean motionHdrHandoff' "$AFTER/app/src/main/cpp/motionv2_jpeg444_jni.cpp" || fail "native 26706 bodyToneStrength contract missing"; }
verify_apk_jni_contract(){ python3 -S - "$FINAL" "$OUT/26706_apk_jni_contract.txt" <<'PY2'
import hashlib,sys,zipfile
apk,out=sys.argv[1],sys.argv[2]
with zipfile.ZipFile(apk) as z:
 names=z.namelist();dex=[n for n in names if n.startswith('classes') and n.endswith('.dex')];hits=[]
 for n in dex:
  data=z.read(n)
  if b'Lcom/unspektrawesome/diagnostics/InternalLogRecorder;' in data:hits.append((n,data))
 assert len(hits)==1 and b'recordNative' in hits[0][1]
 assert any(b'writeTrue2xNative' in z.read(n) and b'iris26704BodyToneStrength' in z.read(n) for n in dex)
 assert not any(b'iris26706BodyToneStrength' in z.read(n) for n in dex)
 so_name='lib/arm64-v8a/libunspektrawesome_vulkan.so';assert so_name in names;h=hashlib.sha256(z.read(so_name)).hexdigest();assert h=='f40b4707ae27e7d181563d99c31370d5a0e39daef1edb6366bba27da7a201dbd'
 motion='lib/arm64-v8a/libmotionv2jpeg.so';assert motion in names;md=z.read(motion);assert b'Java_com_particlesdevs_photoncamera_processing_ultrahdr_MotionV2Jpeg444Encoder_writeTrue2xNative' in md and b'uBodyToneStrength' in md
 result=f'PASS APK JNI CONTRACT: {hits[0][0]} recorder ABI; Spektra native invariant {h}; MotionV2 writeTrue2x + body-tone uniform present\n';open(out,'w').write(result);print(result,end='')
PY2
 set_report "APK JNI CONTRACT" "PASS"; set_compiler "APK JNI CONTRACT" "PASS"; }
postbuild_proof(){ snapshot_candidate_from_authority "$BASE" "$ROOT" "$POST"; compare_app_trees "$AFTER" "$POST"; (cd "$POST" && sha256sum -c "$CAND_PROTECTED" >/dev/null && sha256sum -c "$CAND_NATIVE" >/dev/null && sha256sum -c "$CAND_NATIVE_FULL" >/dev/null && sha256sum -c "$CAND_VENDOR" >/dev/null && sha256sum -c "$CAND_DNG" >/dev/null && sha256sum -c "$SHADER_CAND" >/dev/null) || fail "post-build invariance"; python3 -S "$VALIDATE" "$BASE" "$POST" | tee "$OUT/26706_postbuild_semantic_validation.txt"; python3 -S "$GATEVERIFY" "$BASE" "$POST" | tee "$OUT/26706_postbuild_regressions.txt"; python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$POST" | tee "$OUT/26706_postbuild_authority.txt"; python3 -S "$SHADERVERIFY" "$ROOT" "$BASE" "$POST" | tee "$OUT/26706_postbuild_shader_validation.txt"; set_report "POST-BUILD INVARIANCE" "PASS"; set_compiler "POST-BUILD INVARIANCE" "PASS"; tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -cf - -C "$POST" app | gzip -n > "$OUT/26706_candidate_app_source.tar.gz"; sha256sum "$OUT/26706_candidate_app_source.tar.gz" > "$OUT/26706_candidate_app_source.tar.gz.sha256"; cp "$CAND_FULL" "$OUT/26706_candidate_full_app.sha256"; cp "$CAND_NATIVE" "$OUT/26706_native_protected_postbuild.sha256"; cp "$CAND_NATIVE_FULL" "$OUT/26706_native_full_postbuild.sha256"; cp "$CAND_VENDOR" "$OUT/26706_vendor_protected_postbuild.sha256"; cp "$CAND_DNG" "$OUT/26706_dng_postbuild.sha256"; cp "$SHADER_CAND" "$OUT/26706_asset_shader_universe_postbuild.sha256"; cp "$SHADER_PIN" "$OUT/26706_runtime_expanded_shaders.sha256"; set_report "CLEAN ARTIFACT SOURCE EXPORT" "PASS (deterministic candidate tar + manifests + expanded shader pins)"; }
# IRIS_26706_AUTHORITATIVE_ACTIONS_STAGE_ORDER
verify_package
verify_scope
obtain_authority
make_candidate
verify_successful_26704_mechanics
if [[ -n "$LOCAL_ART" ]]; then
 verify_candidate_patches
 set_report "REAL GLSL COMPILE" "NOT RUN locally (Actions required)"; set_report "REAL KOTLIN COMPILE" "NOT RUN locally (Actions required)"; set_report "REAL JAVA COMPILE" "NOT RUN locally (Actions required)"; set_report "JNI CALLBACK CLASS ABI" "NOT RUN by real project javac locally (Actions required)"; set_report "REAL NATIVE/NDK COMPILE" "NOT RUN locally (Actions required)"; set_report "PRE-BUILD SAFETY PROOF" "NOT RUN (real compiler/NDK/full Android require Actions)"; set_report "FULL ANDROID ASSEMBLE" "NOT RUN locally (Actions required)"; set_report "EXACTLY ONE APK" "NOT RUN locally (Actions required)"; set_report "APK JNI CONTRACT" "NOT RUN (requires final Actions APK)"; set_report "POST-BUILD INVARIANCE" "NOT RUN locally (Actions required)"; set_report "CLEAN ARTIFACT SOURCE EXPORT" "NOT RUN locally (Actions required)"
 set_compiler "REAL GLSL COMPILE" "NOT RUN locally (Actions required)"; set_compiler "REAL KOTLIN COMPILE" "NOT RUN locally (Actions required)"; set_compiler "REAL JAVA COMPILE" "NOT RUN locally (Actions required)"; set_compiler "JNI CALLBACK CLASS ABI" "NOT RUN by real project javac locally (Actions required)"; set_compiler "NATIVE/NDK COMPILE" "NOT RUN locally (Actions required)"; set_compiler "FULL ANDROID ASSEMBLE" "NOT RUN locally (Actions required)"; set_compiler "APK JNI CONTRACT" "NOT RUN locally (Actions required)"; set_compiler "POST-BUILD INVARIANCE" "NOT RUN locally (Actions required)"
 cp "$OUT/26706_STRICT_HANDOFF_REPORT.txt" "$OUT/26706_local_prebuild_report.txt"
 pass "26706 LOCAL PREBUILD PREPARED: exact successful 26705 R1 compiled authority; exact successful 26704 mechanics + 26705 R1 APK-marker regression retained; all locally available gates passed; real compiler/build/APK gates explicitly unproven locally"
 exit 0
fi
prepare_glslang
compile_modified_runtime_shaders
compile_spektra_raw_shader
install_frozen_candidate_live
./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace 2>&1 | tee "$OUT/26706_gradle_language_compilers.log"
set_report "REAL KOTLIN COMPILE" "PASS"; set_report "REAL JAVA COMPILE" "PASS"; set_compiler "REAL KOTLIN COMPILE" "PASS"; set_compiler "REAL JAVA COMPILE" "PASS"
verify_compiled_jni_callback
verify_compiled_motion_jni
snapshot_candidate_from_authority "$BASE" "$ROOT" "$WORK/after_language_compiler_snapshot"; compare_app_trees "$AFTER" "$WORK/after_language_compiler_snapshot"
./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace 2>&1 | tee "$OUT/26706_gradle_native_compiler.log"
set_report "REAL NATIVE/NDK COMPILE" "PASS (both ABIs; successful-26704 native/compiler ordering retained)"; set_compiler "NATIVE/NDK COMPILE" "PASS (both ABIs)"
verify_candidate_patches
set_report "PRE-BUILD SAFETY PROOF" "PASS"; pass "26706 PRE-BUILD SAFETY PROOF PASSED"
./gradlew :app:assembleDebug --stacktrace 2>&1 | tee "$OUT/26706_gradle_assemble.log"
set_report "FULL ANDROID ASSEMBLE" "PASS"; set_compiler "FULL ANDROID ASSEMBLE" "PASS"
mapfile -t apks < <(find "$ROOT/app/build/outputs/apk/debug" -type f -name '*.apk' | sort)
[[ "${#apks[@]}" -eq 1 ]] || fail "expected exactly one Gradle debug APK"
mv "${apks[0]}" "$FINAL"; [[ -f "$FINAL" ]] || fail "final APK missing after move"; set_report "EXACTLY ONE APK" "PASS"; sha256sum "$FINAL" > "$OUT/26706_APK.sha256"
verify_apk_jni_contract
postbuild_proof
pass "26706 ACTIONS BUILD COMPLETE"
