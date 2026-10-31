#!/usr/bin/env python3
"""26892 guarded successor of ACTUAL executed successful 26891 runner.
Retains entire 17-stage order/compilers/historical validators; isolate new code.
"""
from pathlib import Path
import re,hashlib,sys
R=(Path(sys.argv[1]) if len(sys.argv)>1 else Path('.')).resolve()
p=R/'build_26891_iris_rawr.sh'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
EXPECTED='f0b25de61cc661a461c10e7665623ba15ddda0362ba047c05e543aaf670f094b'
assert p.is_file() and sha(p)==EXPECTED,'successful 26891 EXACT executed Actions runner missing/incorrect'
s=p.read_text()
STAGES=('verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','verify_candidate_patches','prebuild_safety','assemble','postbuild_proof','clean_extract_replay')
rex=re.compile(r'\n([a-z_]+)\(\)\{')
assert tuple(x for x in rex.findall(s) if x in STAGES)==STAGES

def once(old,new):
 global s
 assert s.count(old)==1,(old,s.count(old));s=s.replace(old,new,1)
def stage(name):
 a=s.index('\n'+name+'(){')+1;b=s.index('\n}',a)+2;return s[a:b]
def edit(name,fun):
 global s
 old=stage(name);new=fun(old)
 assert old!=new and new.startswith(name+'(){') and new.endswith('}')
 s=s.replace(old,new,1)
def append(old,cmd):return old[:-2]+'\n'+cmd.strip('\n')+'\n}'

def repl(old,new):
 global s
 assert old in s,(old,'not found')
 s=s.replace(old,new)

# Exact authority constants, no unbuilt HEAD or earlier candidate as runtime.
for a,b in [
 ('REPO_SCAFFOLD_BASE_COMMIT="90faa0f88ada86b030e24b6e10b6b1e4d762e3f2"','REPO_SCAFFOLD_BASE_COMMIT="e9625509a0cb6b5d75e6b18bb1b87b9b9d7b5dee"'),
 ('RUNTIME_ARTIFACT_ID="13024439725"; RUNTIME_ACTIONS_RUN="41156125594"','RUNTIME_ARTIFACT_ID="13028418567"; RUNTIME_ACTIONS_RUN="41165932780"'),
 ('RUNTIME_AUTHORITY_COMMIT="90faa0f88ada86b030e24b6e10b6b1e4d762e3f2"','RUNTIME_AUTHORITY_COMMIT="e9625509a0cb6b5d75e6b18bb1b87b9b9d7b5dee"'),
 ('RUNTIME_ARTIFACT_SHA="14d04be706379ad65966adbb0a343bbc6a3e35275455403ba949c13d8cdde681"','RUNTIME_ARTIFACT_SHA="16744811dc6145abf93297c0cd4f6cdf1b878946f19c17bf04cf7939179945ea"'),
 ('RUNTIME_TAR_SHA="6b7cc1377928ae384b95e0b862169f38d0e278cf90df8bdeb56cc9d30397c0fa"','RUNTIME_TAR_SHA="0541b1c0324f74dca4295d956cd94148e1aa71212f621657618a707ac59d6aff"'),
 ('VERSION_NAME="0.9726891"; VERSION_BUILD="26891"','VERSION_NAME="0.9726892"; VERSION_BUILD="26892"'),
 ('OUT="$ROOT/build_26891_iris_rawr_outputs"; WORK="$ROOT/.build_26891_iris_rawr_work"','OUT="$ROOT/build_26892_iris_rawr_outputs"; WORK="$ROOT/.build_26892_iris_rawr_work"'),
 ('ARTZIP="$WORK/26890_artifact.zip"; ARTDIR="$WORK/artifact_26890"','ARTZIP="$WORK/26891_artifact.zip"; ARTDIR="$WORK/artifact_26891"'),
 ('BASE="$WORK/exact_successful_26890_compiled_candidate"; CAND="$WORK/candidate_26891"','BASE="$WORK/exact_successful_26891_compiled_candidate"; CAND="$WORK/candidate_26892"'),
 ('# IRIS_26891_AUTHORITATIVE_ACTIONS_STAGE_ORDER','# IRIS_26892_AUTHORITATIVE_ACTIONS_STAGE_ORDER')]:once(a,b)
# Stage artifact status, compiler/receipt destinations for current run (historical artifacts untouched).
s=s.replace('$OUT/26891_','$OUT/26892_')
# Original 26891 verification must run against OWN successful original candidate, not the new 26892 overlay.
# H90/H91 are recreated by real historic full-index reversal and original generator below.
for func in ('verify_26891_candidate.py','verify_26891_semantics.py','verify_26891_patches.py'):
 s=s.replace(func+' "$BASE" "$CAND"',func+' "$WORK/historical_26890_from_26891" "$WORK/historical_26891_replayed"')
 s=s.replace(func+' "$BASE" "$exp"',func+' "$WORK/historical_26890_from_26891" "$WORK/historical_26891_replayed"')
s=s.replace('verify_26891_expanded_glsl.py "$CAND"','verify_26891_expanded_glsl.py "$WORK/historical_26891_replayed"')
s=s.replace('verify_26889_compiled_push_abi.py "$ARTDIR/build_26890_iris_rawr_outputs/','verify_26889_compiled_push_abi.py "$ARTDIR/build_26891_iris_rawr_outputs/')
s=s.replace('test_26891_negative_tamper.py "$BASE" "$CAND"','test_26891_negative_tamper.py "$WORK/historical_26890_from_26891" "$WORK/historical_26891_replayed"')
s=s.replace('test_26891_negative_tamper.py "$BASE" "$exp"','test_26891_negative_tamper.py "$WORK/historical_26890_from_26891" "$WORK/historical_26891_replayed"')

s=s.replace('verify_26891_expanded_glsl.py "$exp"','verify_26891_expanded_glsl.py "$WORK/historical_26891_replayed"')
# Original historic runner source used in 26891 exact generator and stored prior successful.
oldmake=stage('make_candidate')
historical=oldmake.replace('make_candidate(){','historical_26891_make_candidate(){',1)
# Original predecessor make_candidate using dynamically scoped BASE/CAND of H90/H91.
# Explicitly install the original unchanged body and rerun the same exact historical tests.
s=s.replace(oldmake,historical+'''\nmake_candidate(){
 local H90="$WORK/historical_26890_from_26891" H91="$WORK/historical_26891_replayed"
 cp -a "$BASE" "$H90"; git -C "$H90" init -q
 (cd "$H90" && git apply --check --reverse "$ROOT/26891_FORWARD_FULL_INDEX.patch" && \\
  git apply --reverse "$ROOT/26891_FORWARD_FULL_INDEX.patch" && \\
  sha256sum -c "$ROOT/26891_BASE_FULL_APP.sha256" >/dev/null) || fail '26891 original-source rollback failed'
 rm -rf "$H90/.git"
 (local BASE="$H90" CAND="$H91"; historical_26891_make_candidate)
 diff -qr "$H91/app" "$BASE/app" >/dev/null || fail 'original generated 26891 source != actual compiled 26891'
 python3 -S verify_26891_candidate.py "$H90" "$BASE"
 python3 -S verify_26891_semantics.py "$H90" "$BASE"
 python3 -S verify_26891_expanded_glsl.py "$BASE"
 python3 -S verify_26891_patches.py "$H90" "$BASE" 26891_FORWARD_FULL_INDEX.patch 26891_ROLLBACK_FULL_INDEX.patch
 python3 -S test_26891_negative_tamper.py "$H90" "$BASE"
 python3 -S verify_26892_candidate.py "$BASE" "$CAND" --transform
 python3 -S verify_26892_semantics.py "$BASE" "$CAND"
 python3 -S test_26892_tone_math.py
}\n''',1)
# Historical make_candidate version contains old already-redirected verify candidate call;
# correct them to original H90/H91 dynamic scope (not newly created work path) without changing body logic.
start=s.index('historical_26891_make_candidate(){');end=s.index('\nmake_candidate(){',start)
a=s[start:end]
a=a.replace('"$WORK/historical_26890_from_26891" "$WORK/historical_26891_replayed"','"$BASE" "$CAND"')
s=s[:start]+a+s[end:]

edit('verify_package',lambda old:append(old,''' test -f TRIGGER_26892.txt && grep -Fx 'RUN_26892_SCENE_ADAPTIVE_SDR_BACKLIGHT_CONTRAST_V1' TRIGGER_26892.txt >/dev/null || fail '26892 immutable trigger'
 python3 -S stage_26892_root.py
 sha256sum -c 26892_HANDOFF_HASHES.sha256 >/dev/null || fail '26892 sealed payload tampered'
 python3 -S -m py_compile generate_26892_build.py verify_26892_candidate.py verify_26892_semantics.py verify_26892_patches.py stage_26892_root.py verify_26892_expanded_glsl.py test_26892_negative_tamper.py test_26892_tone_math.py photon_26892_replay_exact_26891_workflow.py
 [[ "$(find handoff_payload_26892 -type f | wc -l)" -eq 4 ]] || fail '26892 4-file exact allowlist drift'
'''))
edit('verify_scope',lambda _:'''verify_scope(){
 [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail 'wrong branch'
 git merge-base --is-ancestor "$RUNTIME_AUTHORITY_COMMIT" HEAD || fail 'successful 26891 compiled authority not ancestor'
 [[ -z "$(git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD -- app/src app/version.properties)" ]] || fail 'unintended committed live runtime delta'
 [[ -z "$(git status --porcelain -- app/src app/version.properties)" ]] || fail 'uncommitted live runtime delta'
 diff -u 26892_REPOSITORY_UPLOAD_ALLOWLIST.txt <(git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD | LC_ALL=C sort) >/dev/null || fail '26892 repository upload scope drift'
 [[ "$(sha build_26891_iris_rawr.sh)" == 'f0b25de61cc661a461c10e7665623ba15ddda0362ba047c05e543aaf670f094b' ]] || fail 'actual executed successful 26891 runner drift'
 pass '26892 committed-only stage upload, exact successful 26891 runner'
}''')
edit('obtain_authority',lambda _:'''obtain_authority(){
 [[ -n "$TOKEN" ]] || fail 'GITHUB_TOKEN missing'
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' \\
  "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/runs/${RUNTIME_ACTIONS_RUN}" -o "$WORK/26891_run.json"
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' \\
  "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${RUNTIME_ARTIFACT_ID}" -o "$WORK/26891_artifact_metadata.json"
 python3 -S - "$WORK/26891_run.json" "$WORK/26891_artifact_metadata.json" <<'PY_AUTH_92'
import json,sys
run=json.load(open(sys.argv[1]));art=json.load(open(sys.argv[2]))
assert run['id']==41165932780 and run['conclusion']=='success' and run['head_sha']=='e9625509a0cb6b5d75e6b18bb1b87b9b9d7b5dee' and run['head_branch']=='experimental-clean-photon-rebuild'
assert art['id']==13028418567 and art.get('expired') is False and art.get('digest')=='sha256:16744811dc6145abf93297c0cd4f6cdf1b878946f19c17bf04cf7939179945ea'
print('PASS successful 26891 run/job-linked artifact/digest')
PY_AUTH_92
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' \\
  "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${RUNTIME_ARTIFACT_ID}/zip" -o "$ARTZIP"
 [[ "$(sha "$ARTZIP")" == "$RUNTIME_ARTIFACT_SHA" ]] || fail '26891 artifact SHA mismatch'
 unzip -q "$ARTZIP" -d "$ARTDIR"
 local T="$ARTDIR/build_26891_iris_rawr_outputs/26891_candidate_app_source.tar.gz"
 [[ -f "$T" && "$(sha "$T")" == "$RUNTIME_TAR_SHA" ]] || fail '26891 actual compiled TAR mismatch'
 local EXEC="$ARTDIR/build_26891_iris_rawr_outputs/exact_generated_runner/build_26891_iris_rawr.sh"
 [[ -f "$EXEC" && "$(sha "$EXEC")" == 'f0b25de61cc661a461c10e7665623ba15ddda0362ba047c05e543aaf670f094b' ]] || fail '26891 executed runner mismatch'
 cmp -s "$EXEC" "$ROOT/build_26891_iris_rawr.sh" || fail '26891 reproduced runner differs from executed Actions bytes'
 for k in 'REAL GLSL COMPILE: PASS' 'REAL SPIR-V VALIDATION: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS';do
  grep -F "$k" "$ARTDIR/build_26891_iris_rawr_outputs/26891_COMPILER_STATUS.txt" >/dev/null || fail "successful 26891 compiler receipt missing $k"
 done
 mkdir -p "$BASE";tar -xzf "$T" -C "$BASE"
 [[ "$(find "$BASE/app" -type f | wc -l)" -eq 2025 ]] || fail '26891 compiled source count drift'
 (cd "$BASE" && sha256sum -c "$ROOT/26892_BASE_FULL_APP.sha256" >/dev/null) || fail '26891 compiled candidate hashes mismatch'
 cmp -s "$ARTDIR/build_26891_iris_rawr_outputs/26891_candidate_full_app.sha256" "$ROOT/26892_BASE_FULL_APP.sha256" || fail '26891 actual compiled SHA manifest mismatch'
 pass '26891 successful artifact, 2025 files, verified exact executed runner'
}''')

# All original historical validator stages inherited, but the NEW image owners
# separately compiled in both SDR render and UHDR gainmap EXACT shader source.
edit('verify_successful_mechanics',lambda old:append(old,''' [[ "$(sha build_26891_iris_rawr.sh)" == 'f0b25de61cc661a461c10e7665623ba15ddda0362ba047c05e543aaf670f094b' ]] || fail 'successful 26891 runner differs from generated'
 python3 -S verify_26892_candidate.py "$BASE" "$CAND"
 python3 -S verify_26892_semantics.py "$BASE" "$CAND"
 python3 -S test_26892_tone_math.py
'''))
edit('compile_modified_runtime_shaders',lambda old:append(old,''' python3 -S verify_26892_expanded_glsl.py "$CAND" --compiler "$IRIS26864_GLSLANG" --out "$OUT/26892_scene_sdr_exact_essl310" | tee "$OUT/26892_scene_sdr_pinned_glsl.txt"
 grep -Fx 'PASS 26892 TWO exact changed render+gainmap ESSL310 programs; REAL PINNED COMPILE PASS' "$OUT/26892_scene_sdr_pinned_glsl.txt" >/dev/null || fail '26892 actual changed GLES render+gainmap not pinned compiled'
'''))
edit('verify_candidate_patches',lambda old:append(old,''' python3 -S verify_26892_candidate.py "$BASE" "$CAND"
 python3 -S verify_26892_semantics.py "$BASE" "$CAND"
 python3 -S verify_26892_patches.py "$BASE" "$CAND" 26892_FORWARD_FULL_INDEX.patch 26892_ROLLBACK_FULL_INDEX.patch | tee "$OUT/26892_patch_validation.txt"
 python3 -S test_26892_negative_tamper.py "$BASE" "$CAND"
 python3 -S test_26892_tone_math.py
'''))
edit('prebuild_safety',lambda old:append(old,''' python3 -S verify_26892_candidate.py "$BASE" "$CAND"
 python3 -S verify_26892_semantics.py "$BASE" "$CAND"
 (cd "$CAND" && sha256sum -c "$ROOT/26892_UNCHANGED_PROTECTED.sha256" >/dev/null) || fail '26892 2021 protected sources modified'
 test -s "$OUT/26892_scene_sdr_pinned_glsl.txt" && grep -F 'REAL PINNED COMPILE PASS' "$OUT/26892_scene_sdr_pinned_glsl.txt" >/dev/null || fail '26892 changed shaders MUST be compiled BEFORE build'
 cat >> "$OUT/26892_PREBUILD_SAFETY.txt" <<'EOF_26892_SAFETY'
26892_exact_successful_26891_compiled_TAR=0541b1c0324f74dca4295d956cd94148e1aa71212f621657618a707ac59d6aff
26892_actual_successful_26891_runner=f0b25de61cc661a461c10e7665623ba15ddda0362ba047c05e543aaf670f094b
26892_scope=4 existing B-SR-OFF SDR presentation/runtime files, 2021 original protected, 0 added/deleted
26892_contrast=no independent midtone/saturation increase; UHDR gainmap source-matched
26892_compile=real PINNED shader, Kotlin, Java, Android native+NDK required
EOF_26892_SAFETY
'''))
# prebuild inherited text still mentions 26891 (fine as inherited historic receipt but
# must not permit missing new proof). Remove historical 26891 current candidate proof run,
# now replaced with successful H90/H91 through global adjustment.
edit('postbuild_proof',lambda old:append(old,''' python3 -S verify_26892_candidate.py "$BASE" "$CAND"
 (cd "$CAND" && sha256sum -c "$ROOT/26892_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null)
 (cd "$CAND" && sha256sum -c "$ROOT/26892_UNCHANGED_PROTECTED.sha256" >/dev/null)
 cp 26892_EXPECTED_CANDIDATE_FULL_APP.sha256 "$OUT/26892_candidate_full_app.sha256"
 (cd "$CAND" && tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -czf "$OUT/26892_candidate_app_source.tar.gz" app)
 sha256sum "$OUT/26892_candidate_app_source.tar.gz" > "$OUT/26892_candidate_app_source.tar.gz.sha256"
 cp 26892_FORWARD_FULL_INDEX.patch 26892_ROLLBACK_FULL_INDEX.patch "$OUT/"
'''))
edit('clean_extract_replay',lambda old:append(old,''' python3 -S verify_26892_candidate.py "$BASE" "$CAND"
 python3 -S verify_26892_semantics.py "$BASE" "$CAND"
 python3 -S verify_26892_patches.py "$BASE" "$CAND" 26892_FORWARD_FULL_INDEX.patch 26892_ROLLBACK_FULL_INDEX.patch
 python3 -S test_26892_negative_tamper.py "$BASE" "$CAND"
 python3 -S test_26892_tone_math.py
 python3 -S verify_26892_expanded_glsl.py "$CAND"
 (cd "$CAND" && sha256sum -c "$ROOT/26892_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null)
 sha256sum -c "$OUT/26892_candidate_app_source.tar.gz.sha256" >/dev/null
 test "$(sha build_26891_iris_rawr.sh)" = 'f0b25de61cc661a461c10e7665623ba15ddda0362ba047c05e543aaf670f094b' || fail '26891 original executed runner not preserved'
'''))
# New CURRENT derived runner script cannot blindly retain old current candidate
# tests against the NEW 26892 source; all 26891 validators above have historical operands.
# Current stage final version and status write use 26892 only (preserve prior historic text).
s=s.replace('VERSION_NAME=0.9726891\' "$exp/app/version.properties"','VERSION_NAME=0.9726892\' "$exp/app/version.properties"')
s=s.replace('VERSION_BUILD=26891\' "$exp/app/version.properties"','VERSION_BUILD=26892\' "$exp/app/version.properties"')
s=s.replace('runtime_authority=successful 26890 $RUNTIME_AUTHORITY_COMMIT','runtime_authority=successful 26891 $RUNTIME_AUTHORITY_COMMIT')
# Parent prebuild/proof text still references 26891, replace current scoped statements.
s=s.replace('runtime_changed_files=6 (6 existing, 0 additions/deletions); 2019 protected, 26889 exact tone rollback, B-off native HDRQ normalization, B default and A-convention JPEG name retained','runtime_changed_files=4 (4 existing, 0 additions/deletions); 2021 protected, B-off ONLY scene adaptive tone+contrast, 26891 HDRQ unchanged')
s=s.replace('protected_source=2019 files byte-identical to successful 26890 compiled candidate','protected_source=2021 files byte-identical to successful 26891 compiled candidate')
s=s.replace('26891 6-path full-index','26892 4-path full-index')
# Some historical validator invocations in assemble postbuild use exp newest; correct the
# historical successful 26891 validator to the reconstructed original 26891 source.
s=s.replace('(cd "$CAND" && sha256sum -c "$ROOT/26891_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null)','(cd "$WORK/historical_26891_replayed" && sha256sum -c "$ROOT/26891_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null)')
s=s.replace('verify_26891_candidate.py "$BASE" "$replay" --transform','verify_26892_candidate.py "$BASE" "$replay" --transform')
s=s.replace('verify_26891_candidate.py "$BASE" "$exp"','verify_26892_candidate.py "$BASE" "$exp"')
s=s.replace('verify_26891_patches.py "$BASE" "$exp"','verify_26892_patches.py "$BASE" "$exp"')
# Critically clean-extract own 26892 candidate via current exact transform.
# Version must be bumped once and only one APK; inherited assembly commands preserved.
assert 'VERSION_BUILD="26892"' in s
assert tuple(x for x in rex.findall(s) if x in STAGES)==STAGES
for call in ['./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'./gradlew :app:assembleDebug --stacktrace']:
 assert call in s
assert 'verify_26892_expanded_glsl.py "$CAND" --compiler "$IRIS26864_GLSLANG"' in s
assert 'verify_26892_patches.py "$BASE" "$CAND" 26892_FORWARD_FULL_INDEX.patch 26892_ROLLBACK_FULL_INDEX.patch' in s
out=R/'build_26892_iris_rawr.sh';out.write_text(s)
print('PASS 26892 derived actual successful 26891 17-stage runner',sha(out),'lines',len(s.splitlines()))
