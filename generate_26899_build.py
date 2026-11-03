#!/usr/bin/env python3
"""Derive EXACT successful 26898 17-stage runner, preserving guards and compilers.
All 26898 historical commands execute against actual successful 26897->26898 bytes;
only current 26899 overlay + shader/patch checks are appended to inherited stages.
"""
from pathlib import Path
import hashlib,sys,re
R=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
parent=R/'build_26898_iris_rawr.sh'
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert parent.is_file() and H(parent)=='9c97ed074b1d4ec48528e1d63103aed3198d44406a0c3f4820ad3309c203c99a', '26898 exact executed successful runner required'
s=parent.read_text()
STAGES=('verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics',
'prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader',
'install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff',
'compile_native','verify_candidate_patches','prebuild_safety','assemble','postbuild_proof','clean_extract_replay')
rx=re.compile(r'(?m)^([a-z_]+)\(\)\{')
assert tuple(x for x in rx.findall(s) if x in STAGES)==STAGES

def once(a,b):
 global s
 assert s.count(a)==1,(a[:120],s.count(a))
 s=s.replace(a,b,1)
def section(name):
 a=s.index('\n'+name+'(){')+1;b=s.index('\n}',a)+2
 return s[a:b]
def rewrite(name,new):
 global s
 old=section(name)
 assert new.startswith(name+'(){') and new.endswith('}') and old!=new,name
 s=s.replace(old,new,1)
def append(name,code):
 old=section(name);rewrite(name,old[:-2]+'\n'+code.strip('\n')+'\n}')
H97='"$WORK/historical_26897_from_26898"';H98='"$WORK/historical_26898_replayed"'
for a,b in [
 ('REPO_SCAFFOLD_BASE_COMMIT="217fe8ca9d63b6c144af5a8197dd0adc0025eecb"','REPO_SCAFFOLD_BASE_COMMIT="94d8900987749c9ad0f7a18a64eeb0c7083e6d04"'),
 ('RUNTIME_ARTIFACT_ID="13200518421"; RUNTIME_ACTIONS_RUN="41568669521"','RUNTIME_ARTIFACT_ID="13241316001"; RUNTIME_ACTIONS_RUN="41656090620"'),
 ('RUNTIME_AUTHORITY_COMMIT="217fe8ca9d63b6c144af5a8197dd0adc0025eecb"','RUNTIME_AUTHORITY_COMMIT="94d8900987749c9ad0f7a18a64eeb0c7083e6d04"'),
 ('RUNTIME_ARTIFACT_SHA="e433a1004c69e60ffc523f4dbd4417fb63189762a366f91a7522605065324b45"','RUNTIME_ARTIFACT_SHA="3fa6f669ecebd7e5c460ea1228d086b7422a93c95c8bbd950f5b4fe24bf53b97"'),
 ('RUNTIME_TAR_SHA="23462eec3c2d03b55f97cdb63b686ea9133a4d5f9e50e9ffa0a26ba8a13eebe6"','RUNTIME_TAR_SHA="7ac15724f3cc30753f41f08038443e24b4931c8861fe10217cc4c3b059755a61"'),
 ('VERSION_NAME="0.9726898"; VERSION_BUILD="26898"','VERSION_NAME="0.9726899"; VERSION_BUILD="26899"'),
 ('OUT="$ROOT/build_26898_iris_rawr_outputs"; WORK="$ROOT/.build_26898_iris_rawr_work"','OUT="$ROOT/build_26899_iris_rawr_outputs"; WORK="$ROOT/.build_26899_iris_rawr_work"'),
 ('ARTZIP="$WORK/26897_artifact.zip"; ARTDIR="$WORK/artifact_26897"','ARTZIP="$WORK/26898_artifact.zip"; ARTDIR="$WORK/artifact_26898"'),
 ('BASE="$WORK/exact_successful_26897_compiled_candidate"; CAND="$WORK/candidate_26898"','BASE="$WORK/exact_successful_26898_compiled_candidate"; CAND="$WORK/candidate_26899"'),
 ('# IRIS_26898_AUTHORITATIVE_ACTIONS_STAGE_ORDER','# IRIS_26899_AUTHORITATIVE_ACTIONS_STAGE_ORDER'),
]:once(a,b)
# Only GENERATED output receipt paths migrate. All historical validators keep their original names.
s=s.replace('$OUT/26898_','$OUT/26899_')
# Adapt existing 26898 original generator to the parent artifact's verified historical TAR.
old=section('make_candidate')
historical=old.replace('make_candidate(){','historical_26898_make_candidate(){',1).replace(
 '$ARTDIR/build_26897_iris_rawr_outputs/26895_historical_candidate_app_source.tar.gz',
 '$ARTDIR/build_26898_iris_rawr_outputs/26895_historical_candidate_app_source.tar.gz')
new='''make_candidate(){
 local H97="$WORK/historical_26897_from_26898" H98="$WORK/historical_26898_replayed"
 mkdir -p "$H97"
 local T97="$ARTDIR/build_26898_iris_rawr_outputs/26897_historical_candidate_app_source.tar.gz"
 [[ -f "$T97" && "$(sha "$T97")" == '23462eec3c2d03b55f97cdb63b686ea9133a4d5f9e50e9ffa0a26ba8a13eebe6' ]] || fail 'actual 26898 historical 26897 TAR SHA mismatch'
 tar -xzf "$T97" -C "$H97"
 (cd "$H97" && sha256sum -c "$ROOT/26898_BASE_FULL_APP.sha256" >/dev/null) || fail '26898 historical successful 26897 source manifest incorrect'
 (local BASE="$H97" CAND="$H98"; historical_26898_make_candidate)
 diff -qr "$H98/app" "$BASE/app" >/dev/null || fail '26898 generated historical candidate differs from successful compiled 26898 runtime'
 python3 -S verify_26898.py candidate "$H97" "$H98"
 python3 -S verify_26898.py semantics "$H97" "$H98"
 python3 -S verify_26898.py patch "$H97" "$H98" 26898_FORWARD_FULL_INDEX.patch 26898_ROLLBACK_FULL_INDEX.patch
 python3 -S verify_26898.py tamper "$H97" "$H98"
 python3 -S test_26898_modes.py "$H98"
 python3 -S verify_26899.py candidate "$BASE" "$CAND" --transform
 python3 -S verify_26899.py semantics "$BASE" "$CAND"
 python3 -S test_26899_modes.py "$CAND"
}'''
assert old in s
s=s.replace(old,historical+'\n'+new,1)

# Retain all inherited 26898 regression CLI calls, but point them at the
# original successfully compiled historical 26897/26898 bytes, never 26899.
for name in STAGES:
 if name in ('verify_scope','obtain_authority','make_candidate'):continue
 old=section(name);new=old
 for kind in ('candidate','semantics','patch','tamper'):
  new=new.replace('verify_26898.py '+kind+' "$BASE" "$CAND"',
                  'verify_26898.py '+kind+' '+H97+' '+H98)
 new=new.replace('test_26898_modes.py "$CAND"','test_26898_modes.py '+H98)
 for man in ('26898_UNCHANGED_PROTECTED.sha256','26898_EXPECTED_CANDIDATE_FULL_APP.sha256'):
  new=new.replace('(cd "$CAND" && sha256sum -c "$ROOT/'+man+'"',
                  '(cd '+H98+' && sha256sum -c "$ROOT/'+man+'"')
 if name=='prebuild_safety':
  new=new.replace('"$CAND/app/version.properties"','"$WORK/historical_26898_replayed/app/version.properties"')
 if name=='postbuild_proof':
  new=new.replace('cp 26898_EXPECTED_CANDIDATE_FULL_APP.sha256 "$OUT/26899_candidate_full_app.sha256"',
                  'cp 26898_EXPECTED_CANDIDATE_FULL_APP.sha256 "$OUT/26898_historical_candidate_full_app.sha256"')
  new=new.replace('"$OUT/26899_candidate_app_source.tar.gz','"$OUT/26898_historical_candidate_app_source.tar.gz')
  new=new.replace('(cd "$CAND" && tar --sort=name', '(cd '+H98+' && tar --sort=name')
 if name=='clean_extract_replay':
  new=new.replace('"$OUT/26899_candidate_app_source.tar.gz','"$OUT/26898_historical_candidate_app_source.tar.gz')
  new=new.replace('diff -qr "$CAND/app" "$exp98/app"','diff -qr '+H98+'/app "$exp98/app"')
 if name=='verify_candidate_patches':
  new=new.replace('"$OUT/26899_CURRENT_PATCH_PROOF.txt"','"$OUT/26898_HISTORICAL_PATCH_PROOF.txt"')
 if new!=old:rewrite(name,new)

rewrite('verify_scope','''verify_scope(){
 [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail 'wrong Photon Actions branch'
 git merge-base --is-ancestor "$REPO_SCAFFOLD_BASE_COMMIT" HEAD || fail '26898 actual successful commit not ancestor'
 [[ -z "$(git diff --name-only "$REPO_SCAFFOLD_BASE_COMMIT"..HEAD -- app/src app/version.properties)" ]] || fail 'unintended live source modifications'
 [[ -z "$(git status --porcelain -- app/src app/version.properties)" ]] || fail 'uncommitted live source modifications'
 diff -u 26899_REPOSITORY_UPLOAD_ALLOWLIST.txt <(git diff --name-only "$REPO_SCAFFOLD_BASE_COMMIT"..HEAD | LC_ALL=C sort) >/dev/null || fail '26899 upload scope not exactly sealed stage files'
 [[ "$(sha build_26898_iris_rawr.sh)" == '9c97ed074b1d4ec48528e1d63103aed3198d44406a0c3f4820ad3309c203c99a' ]] || fail '26898 exact executed successful runner drift'
 pass '26899 guarded source/infra: exact successful 26898 parent, no live source mutations'
}''')
rewrite('obtain_authority','''obtain_authority(){
 [[ -n "$TOKEN" ]] || fail 'GITHUB_TOKEN missing'
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' \\
   "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/runs/${RUNTIME_ACTIONS_RUN}" -o "$WORK/26898_run.json"
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' \\
   "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${RUNTIME_ARTIFACT_ID}" -o "$WORK/26898_artifact_metadata.json"
 python3 -S - "$WORK/26898_run.json" "$WORK/26898_artifact_metadata.json" <<'PY_AUTH_26899'
import json,sys
run=json.load(open(sys.argv[1]));art=json.load(open(sys.argv[2]))
assert run['id']==41656090620 and run['conclusion']=='success' and run['head_sha']=='94d8900987749c9ad0f7a18a64eeb0c7083e6d04' and run['head_branch']=='experimental-clean-photon-rebuild'
assert art['id']==13241316001 and art.get('expired') is False and art.get('digest')=='sha256:3fa6f669ecebd7e5c460ea1228d086b7422a93c95c8bbd950f5b4fe24bf53b97'
print('PASS exact successful 26898 Actions run/job artifact digest')
PY_AUTH_26899
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' \\
  "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${RUNTIME_ARTIFACT_ID}/zip" -o "$ARTZIP"
 [[ "$(sha "$ARTZIP")" == "$RUNTIME_ARTIFACT_SHA" ]] || fail 'actual 26898 successful artifact ZIP sha wrong'
 unzip -q "$ARTZIP" -d "$ARTDIR"
 local T="$ARTDIR/build_26898_iris_rawr_outputs/26898_candidate_app_source.tar.gz"
 [[ -f "$T" && "$(sha "$T")" == "$RUNTIME_TAR_SHA" ]] || fail 'actual successful compiled 26898 TAR sha mismatch'
 local EXEC="$ARTDIR/build_26898_iris_rawr_outputs/exact_generated_runner/build_26898_iris_rawr.sh"
 [[ -f "$EXEC" && "$(sha "$EXEC")" == '9c97ed074b1d4ec48528e1d63103aed3198d44406a0c3f4820ad3309c203c99a' ]] || fail '26898 actual executed runner SHA incorrect'
 cmp -s "$EXEC" "$ROOT/build_26898_iris_rawr.sh" || fail '26898 generated runner differs from actual executed Actions runner'
 test -f "$ARTDIR/build_26898_iris_rawr_outputs/exact_generated_runner/SUCCESSFUL_ACTIONS_EVIDENCE.json" || fail '26898 executed runner receipt missing'
 for k in 'REAL GLSL COMPILE: PASS' 'REAL SPIR-V VALIDATION: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS';do
  grep -F "$k" "$ARTDIR/build_26898_iris_rawr_outputs/26898_COMPILER_STATUS.txt" >/dev/null || fail "real successful 26898 compiler receipt missing $k"
 done
 mkdir -p "$BASE";tar -xzf "$T" -C "$BASE"
 [[ "$(find "$BASE/app" -type f | wc -l)" -eq 2025 ]] || fail '26898 source universe unexpected'
 (cd "$BASE" && sha256sum -c "$ROOT/26899_BASE_FULL_APP.sha256" >/dev/null) || fail '26898 successful compiled full source manifest mismatch'
 cmp -s "$ARTDIR/build_26898_iris_rawr_outputs/26898_candidate_full_app.sha256" "$ROOT/26899_BASE_FULL_APP.sha256" || fail '26899 base manifest differs from actual compiled 26898 manifest'
 pass '26898 successful exact compiled source, runner, 2025 hashes, compilers, artifact validated'
}''')
# Additional pinned, REAL GLSL ES 310 compiler check is mandatory before
# Android assembly. The original 26898 shader universe/compiler calls unchanged.
append('compile_modified_runtime_shaders','''
 mkdir -p "$OUT/26899_real_expanded_essl310"
 local S99="$CAND/app/src/main/assets/shaders/motionv2/iris26899_b_off_zoom_luma_sharpen.glsl"
 local E99="$OUT/26899_real_expanded_essl310/iris26899_b_off_zoom_luma_sharpen.frag"
 test -s "$S99" || fail '26899 actual new shader missing'
 { printf '#version 310 es\\n\\n#line 1\\n';cat "$S99"; } > "$E99"
 if grep -En '(^|[^[:alnum:]_])(sample|input|output|common|filter)([^[:alnum:]_]|$)' "$E99" | grep -vE '^[[:digit:]]+:[[:space:]]*//';then fail 'reserved current shader identifier/token';fi
 "$IRIS26864_GLSLANG" -S frag "$E99" > "$OUT/26899_NEW_SHADER_GLSLANG_16_5_0.txt" 2>&1 || fail '26899 real PINNED GLES310 shader compile FAILED'
 sha256sum "$E99" "$S99" > "$OUT/26899_NEW_SHADER_SHA256.txt"
 echo 'PASS 26899 REAL PINNED GLSLANG 16.5.0 ESSL310 new two-scale luminance shader compile' | tee -a "$OUT/26899_NEW_SHADER_GLSLANG_16_5_0.txt"
 python3 -S verify_26899.py semantics "$BASE" "$CAND"
''')
append('verify_candidate_patches','''
 python3 -S verify_26899.py candidate "$BASE" "$CAND"
 python3 -S verify_26899.py semantics "$BASE" "$CAND"
 python3 -S verify_26899.py patch "$BASE" "$CAND" 26899_FORWARD_FULL_INDEX.patch 26899_ROLLBACK_FULL_INDEX.patch | tee "$OUT/26899_CURRENT_PATCH_PROOF.txt"
 python3 -S verify_26899.py tamper "$BASE" "$CAND"
''')
append('prebuild_safety','''
 test -s "$OUT/26899_NEW_SHADER_GLSLANG_16_5_0.txt" && grep -Fx 'PASS 26899 REAL PINNED GLSLANG 16.5.0 ESSL310 new two-scale luminance shader compile' "$OUT/26899_NEW_SHADER_GLSLANG_16_5_0.txt" >/dev/null || fail '26899 current shader real pinned compiler proof missing'
 python3 -S verify_26899.py candidate "$BASE" "$CAND"
 python3 -S verify_26899.py semantics "$BASE" "$CAND"
 (cd "$CAND" && sha256sum -c "$ROOT/26899_UNCHANGED_PROTECTED.sha256" >/dev/null) || fail '26899 2021 protected source byte drift'
 grep -Fx 'VERSION_NAME=0.9726899' "$CAND/app/version.properties" >/dev/null
 grep -Fx 'VERSION_BUILD=26899' "$CAND/app/version.properties" >/dev/null
 test -s "$OUT/26899_CURRENT_PATCH_PROOF.txt" || fail '26899 actual patches not executed'
 cat >> "$OUT/26899_PREBUILD_SAFETY.txt" <<'EOF_26899_SAFETY'
26899_exact_parent=success run 41656090620 job 125986647940 commit 94d8900987749c9ad0f7a18a64eeb0c7083e6d04 artifact 13241316001 digest 3fa6f669ecebd7e5c460ea1228d086b7422a93c95c8bbd950f5b4fe24bf53b97
26899_actual_compiled_parent_tar_sha256=7ac15724f3cc30753f41f08038443e24b4931c8861fe10217cc4c3b059755a61
26899_actual_successful_parent_runner_sha256=9c97ed074b1d4ec48528e1d63103aed3198d44406a0c3f4820ad3309c203c99a
26899_runtime=2025 prior to 2026 proposed, 4 modified + 1 new shader, 2021 protected
26899_scope=shutter frozen B Experiment, SuperRes OFF, global zoom >=1.10; new final encoded-SDR edge-aware Y only pass
26899_zoom_curve=+100pct 1.10..10x; +100..150pct 10..20x; +150..200pct 20..30x; capped +200pct >=30x
26899_no_changes=actual A, A+B, B SR ON, Night, Spektra, DNG, RAW fusion, frame counts, Wiener, AMaZE, shader owners besides newly named GLES, color pipeline, UHDR algorithm
26899_compiler=real pinned GLSL ES 310 new shader PASS + inherited native SPIRV, Kotlin Java 2 NDK ABIs and full :app:assembleDebug mandatory
26899_device_tests=NOT RUN ON ACTIONS; visual halos, 4.1x crop vs 20x, all physical lenses, DNG and UHDR device verification required
EOF_26899_SAFETY
''')
append('postbuild_proof','''
 python3 -S verify_26899.py candidate "$BASE" "$CAND"
 python3 -S verify_26899.py semantics "$BASE" "$CAND"
 (cd "$CAND" && sha256sum -c "$ROOT/26899_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null) || fail '26899 candidate source drift after assembly'
 (cd "$CAND" && sha256sum -c "$ROOT/26899_UNCHANGED_PROTECTED.sha256" >/dev/null) || fail '26899 protected DNG native A Night source drift'
 cp 26899_EXPECTED_CANDIDATE_FULL_APP.sha256 "$OUT/26899_candidate_full_app.sha256"
 cp 26899_FORWARD_FULL_INDEX.patch 26899_ROLLBACK_FULL_INDEX.patch 26899_CHANGED_ALLOWLIST.txt 26899_ADDITIONS.txt 26899_DELETIONS.txt 26899_UNCHANGED_PROTECTED.sha256 "$OUT/"
 (cd "$CAND" && tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -czf "$OUT/26899_candidate_app_source.tar.gz" app)
 sha256sum "$OUT/26899_candidate_app_source.tar.gz" > "$OUT/26899_candidate_app_source.tar.gz.sha256"
''')
append('clean_extract_replay','''
 python3 -S verify_26899.py candidate "$BASE" "$CAND"
 python3 -S verify_26899.py semantics "$BASE" "$CAND"
 python3 -S verify_26899.py patch "$BASE" "$CAND" 26899_FORWARD_FULL_INDEX.patch 26899_ROLLBACK_FULL_INDEX.patch
 python3 -S verify_26899.py tamper "$BASE" "$CAND"
 python3 -S test_26899_three_stage_negatives.py
 python3 -S test_26899_modes.py "$CAND"
 (cd "$CAND" && sha256sum -c "$ROOT/26899_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null)
 (cd "$CAND" && sha256sum -c "$ROOT/26899_UNCHANGED_PROTECTED.sha256" >/dev/null)
 sha256sum -c "$OUT/26899_candidate_app_source.tar.gz.sha256" >/dev/null
 local exp99="$WORK/extracted_actual_26899_candidate_tar";rm -rf "$exp99";mkdir -p "$exp99"
 tar -xzf "$OUT/26899_candidate_app_source.tar.gz" -C "$exp99"
 diff -qr "$CAND/app" "$exp99/app" >/dev/null || fail '26899 final compiled candidate TAR not byte-identical'
 (cd "$exp99" && sha256sum -c "$ROOT/26899_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null)
 pass '26899 inherited all 17 stages + new exact GLES310 2-scale B-only zoom + full final clean-extract'
''')
# Fix the last inherited 26898 source archive block in clean_extract_replay
# without touching any earlier historical 26897 and 26894 archive checks.
assert tuple(n for n in rx.findall(s) if n in STAGES)==STAGES
for n,cli in [('compile_languages','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace'),
('compile_native',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace"),
('assemble','./gradlew :app:assembleDebug --stacktrace')]:
 assert section(n).count(cli)==1,(n,cli)
assert 'python3 -S verify_26898.py candidate '+H97+' '+H98 in s
assert 'python3 -S verify_26899.py patch "$BASE" "$CAND" 26899_FORWARD_FULL_INDEX.patch 26899_ROLLBACK_FULL_INDEX.patch' in s
assert '26898_historical_candidate_app_source.tar.gz' in s and '26899_candidate_app_source.tar.gz' in s
out=R/'build_26899_iris_rawr.sh';out.write_text(s);out.chmod(0o755)
print('PASS 26899 deterministic generated SHA',H(out),'lines',len(s.splitlines()),'17 stage order/real compiler CLIs unchanged')
