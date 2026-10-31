#!/usr/bin/env python3
"""Create 26893 ONLY by deterministic transforms of ACTUAL successful 26892
executed 17-stage Actions runner. Parent runner's historical commands retained;
current 26893 overlay receives additional proof. NO copied template substitute.
"""
from pathlib import Path
import hashlib,re,sys
R=(Path(sys.argv[1]) if len(sys.argv)>1 else Path('.')).resolve()
P=R/'build_26892_iris_rawr.sh'
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
EXPECTED='37b12a9cbb5918b49d279d40d51f11fa086a0682dd487f88b6ecc7f17313069d'
assert P.exists() and H(P)==EXPECTED,'successful Actions executed runner 26892 missing/mismatch'
s=P.read_text()
STAGES=('verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','verify_candidate_patches','prebuild_safety','assemble','postbuild_proof','clean_extract_replay')
rex=re.compile(r'\n([a-z_]+)\(\)\{')
assert tuple(x for x in rex.findall(s) if x in STAGES)==STAGES

def once(old,new):
 global s
 n=s.count(old);assert n==1,(old,n)
 s=s.replace(old,new,1)
def stage(n):
 a=s.index('\n'+n+'(){')+1;b=s.index('\n}',a)+2
 return s[a:b]
def edit(n,fn):
 global s
 old=stage(n);new=fn(old)
 assert old!=new and new.startswith(n+'(){') and new.endswith('}')
 s=s.replace(old,new,1)
def append(o,code):return o[:-2]+'\n'+code.strip('\n')+'\n}'

# Exactly one verified newer successful predecessor; failed HEAD is never authority.
for a,b in [
 ('REPO_SCAFFOLD_BASE_COMMIT="e9625509a0cb6b5d75e6b18bb1b87b9b9d7b5dee"','REPO_SCAFFOLD_BASE_COMMIT="8a62e61c9d34fca62a1d61e814fc90553eda39b2"'),
 ('RUNTIME_ARTIFACT_ID="13028418567"; RUNTIME_ACTIONS_RUN="41165932780"','RUNTIME_ARTIFACT_ID="13048932918"; RUNTIME_ACTIONS_RUN="41216852204"'),
 ('RUNTIME_AUTHORITY_COMMIT="e9625509a0cb6b5d75e6b18bb1b87b9b9d7b5dee"','RUNTIME_AUTHORITY_COMMIT="8a62e61c9d34fca62a1d61e814fc90553eda39b2"'),
 ('RUNTIME_ARTIFACT_SHA="16744811dc6145abf93297c0cd4f6cdf1b878946f19c17bf04cf7939179945ea"','RUNTIME_ARTIFACT_SHA="672c3442252db208132086423806d5258a2f537cb453a2b74a39156a8f76f408"'),
 ('RUNTIME_TAR_SHA="0541b1c0324f74dca4295d956cd94148e1aa71212f621657618a707ac59d6aff"','RUNTIME_TAR_SHA="ff4bdf32e5e60d2434eae06887e45e776b2d5727db6ee7e16a4a59404f47e8b9"'),
 ('VERSION_NAME="0.9726892"; VERSION_BUILD="26892"','VERSION_NAME="0.9726893"; VERSION_BUILD="26893"'),
 ('OUT="$ROOT/build_26892_iris_rawr_outputs"; WORK="$ROOT/.build_26892_iris_rawr_work"','OUT="$ROOT/build_26893_iris_rawr_outputs"; WORK="$ROOT/.build_26893_iris_rawr_work"'),
 ('ARTZIP="$WORK/26891_artifact.zip"; ARTDIR="$WORK/artifact_26891"','ARTZIP="$WORK/26892_artifact.zip"; ARTDIR="$WORK/artifact_26892"'),
 ('BASE="$WORK/exact_successful_26891_compiled_candidate"; CAND="$WORK/candidate_26892"','BASE="$WORK/exact_successful_26892_compiled_candidate"; CAND="$WORK/candidate_26893"'),
 ('# IRIS_26892_AUTHORITATIVE_ACTIONS_STAGE_ORDER','# IRIS_26893_AUTHORITATIVE_ACTIONS_STAGE_ORDER')]: once(a,b)
# Only new-run output directory names change, never historical shader or previous-test source names.
s=s.replace('$OUT/26892_','$OUT/26893_')
# The authority artifact root is now the SUCCESSFUL 26892 output directory.
# Repoint ONLY the historical 26888 compiled-SPIR-V ABI operand to that
# artifact's real entry; the original 26889 historical verifier and source
# universes stay byte-identical. Previous 26893 run 41236666825 failed here.
once('"$ARTDIR/build_26891_iris_rawr_outputs/26888_modified_shader_spirv/Iris26887BOffHdrqMerge_prod.spv"',
     '"$ARTDIR/build_26892_iris_rawr_outputs/26888_modified_shader_spirv/Iris26887BOffHdrqMerge_prod.spv"')

# Clean extract's transforming CURRENT candidate must use successor transform.
s=s.replace('verify_26892_candidate.py "$BASE" "$replay" --transform','verify_26893_candidate.py "$BASE" "$replay" --transform')
s=s.replace('verify_26892_candidate.py "$BASE" "$exp"','verify_26893_candidate.py "$BASE" "$exp"')
s=s.replace('verify_26892_patches.py "$BASE" "$exp"','verify_26893_patches.py "$BASE" "$exp"')
# All successful 26892 source-domain validators must run on the original actual 26891/26892 bytes.
H91='"$WORK/historical_26891_from_26892"'
H92='"$WORK/historical_26892_replayed"'
for n in ('verify_26892_candidate.py','verify_26892_semantics.py','verify_26892_patches.py','test_26892_negative_tamper.py'):
 for rhs in ('"$CAND"','"$exp"'):
  s=s.replace(n+' "$BASE" '+rhs,n+' '+H91+' '+H92)
# Original 26892 live shader compile on its OWN source universe, not modified 26893.
s=s.replace('verify_26892_expanded_glsl.py "$CAND"','verify_26892_expanded_glsl.py '+H92)
s=s.replace('verify_26892_expanded_glsl.py "$exp"','verify_26892_expanded_glsl.py '+H92)
# 26892 protected manifest excludes 26892 tone files; for 26893 these are intended changes.
s=s.replace('(cd "$CAND" && sha256sum -c "$ROOT/26892_UNCHANGED_PROTECTED.sha256"','(cd '+H92+' && sha256sum -c "$ROOT/26892_UNCHANGED_PROTECTED.sha256"')
# Prior 26891 global protected file universe is tested on historical 26891, not current changes.
s=s.replace('(cd "$CAND" && sha256sum -c "$ROOT/26891_UNCHANGED_PROTECTED.sha256"','(cd "$WORK/historical_26891_replayed" && sha256sum -c "$ROOT/26891_UNCHANGED_PROTECTED.sha256"')
# Move older 26892 expected-manifest checks to reconstructed predecessor source.
s=s.replace('(cd "$CAND" && sha256sum -c "$ROOT/26892_EXPECTED_CANDIDATE_FULL_APP.sha256"','(cd '+H92+' && sha256sum -c "$ROOT/26892_EXPECTED_CANDIDATE_FULL_APP.sha256"')
# In inherited 26892 postbuild proof a parent 26891 manifest was erroneously copied then
# overwritten; leave all historical invocations intact but require NEW final manifest.
# Original 26892 make_candidate must operate under historic $BASE/$CAND bindings.
old=stage('make_candidate')
historical=old.replace('make_candidate(){','historical_26892_make_candidate(){',1)
for n in ('verify_26892_candidate.py','verify_26892_semantics.py','verify_26892_patches.py','test_26892_negative_tamper.py'):
 historical=historical.replace(n+' '+H91+' '+H92,n+' "$BASE" "$CAND"')
s=s.replace(old,historical+'''
make_candidate(){
 local H91="$WORK/historical_26891_from_26892" H92="$WORK/historical_26892_replayed"
 cp -a "$BASE" "$H91"; git -C "$H91" init -q
 (cd "$H91" && git apply --check --reverse "$ROOT/26892_FORWARD_FULL_INDEX.patch" && \\
  git apply --reverse "$ROOT/26892_FORWARD_FULL_INDEX.patch" && \\
  sha256sum -c "$ROOT/26892_BASE_FULL_APP.sha256" >/dev/null) || fail '26892 ACTUAL successful original-source rollback failed'
 rm -rf "$H91/.git"
 (local BASE="$H91" CAND="$H92"; historical_26892_make_candidate)
 diff -qr "$H92/app" "$BASE/app" >/dev/null || fail '26892 original generated successful source != actual compiled 26892'
 python3 -S verify_26892_candidate.py "$H91" "$BASE"
 python3 -S verify_26892_semantics.py "$H91" "$BASE"
 python3 -S verify_26892_patches.py "$H91" "$BASE" 26892_FORWARD_FULL_INDEX.patch 26892_ROLLBACK_FULL_INDEX.patch
 python3 -S test_26892_negative_tamper.py "$H91" "$BASE"
 python3 -S test_26892_tone_math.py
 python3 -S verify_26893_candidate.py "$BASE" "$CAND" --transform
 python3 -S verify_26893_semantics.py "$BASE" "$CAND"
 python3 -S test_26893_tone_math.py
}
''',1)

edit('verify_package',lambda old:append(old,''' test -f TRIGGER_26893.txt && grep -Fx 'RUN_26893_BACKLIT_FOREGROUND_DARKEN_ONLY_CONTRAST_V1' TRIGGER_26893.txt >/dev/null || fail '26893 exact sole trigger'
 python3 -S stage_26893_root.py
 sha256sum -c 26893_HANDOFF_HASHES.sha256 >/dev/null || fail '26893 upload hashes drift'
 python3 -S -m py_compile generate_26893_build.py verify_26893_candidate.py verify_26893_semantics.py verify_26893_patches.py verify_26893_expanded_glsl.py test_26893_negative_tamper.py test_26893_tone_math.py test_26893_three_stage_negatives.py stage_26893_root.py photon_26893_replay_exact_26892_workflow.py
 test "$(find handoff_payload_26893 -type f | wc -l)" -eq 4 || fail '26893 4-source scope drift'
'''))
edit('verify_scope',lambda _:'''verify_scope(){
 [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail 'wrong branch'
 git merge-base --is-ancestor "$RUNTIME_AUTHORITY_COMMIT" HEAD || fail 'success 26892 runtime authority not ancestor'
 [[ -z "$(git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD -- app/src app/version.properties)" ]] || fail 'unintended live committed runtime drift'
 [[ -z "$(git status --porcelain -- app/src app/version.properties)" ]] || fail 'uncommitted live runtime drift'
 diff -u 26893_REPOSITORY_UPLOAD_ALLOWLIST.txt <(git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD | LC_ALL=C sort) >/dev/null || fail '26893 committed stage-only upload scope drift'
 [[ "$(sha build_26892_iris_rawr.sh)" == '37b12a9cbb5918b49d279d40d51f11fa086a0682dd487f88b6ecc7f17313069d' ]] || fail 'actual successful executed 26892 runner drift'
 pass '26893 sole trigger, exact successful 26892 compiled authority and runner'
}''')
edit('obtain_authority',lambda _:'''obtain_authority(){
 [[ -n "$TOKEN" ]] || fail 'GITHUB_TOKEN missing'
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' \\
  "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/runs/${RUNTIME_ACTIONS_RUN}" -o "$WORK/26892_run.json"
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' \\
  "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${RUNTIME_ARTIFACT_ID}" -o "$WORK/26892_artifact_metadata.json"
 python3 -S - "$WORK/26892_run.json" "$WORK/26892_artifact_metadata.json" <<'PY_AUTH_93'
import json,sys
run=json.load(open(sys.argv[1]));art=json.load(open(sys.argv[2]))
assert run['id']==41216852204 and run['conclusion']=='success' and run['head_sha']=='8a62e61c9d34fca62a1d61e814fc90553eda39b2' and run['head_branch']=='experimental-clean-photon-rebuild'
assert art['id']==13048932918 and art.get('expired') is False and art.get('digest')=='sha256:672c3442252db208132086423806d5258a2f537cb453a2b74a39156a8f76f408'
print('PASS successful 26892 run + final artifact metadata/digest')
PY_AUTH_93
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' \\
  "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${RUNTIME_ARTIFACT_ID}/zip" -o "$ARTZIP"
 [[ "$(sha "$ARTZIP")" == "$RUNTIME_ARTIFACT_SHA" ]] || fail '26892 Actions artifact digest mismatch'
 unzip -q "$ARTZIP" -d "$ARTDIR"
 local T="$ARTDIR/build_26892_iris_rawr_outputs/26892_candidate_app_source.tar.gz"
 [[ -f "$T" && "$(sha "$T")" == "$RUNTIME_TAR_SHA" ]] || fail '26892 actual successful internal compiled candidate TAR mismatch'
 local EXEC="$ARTDIR/build_26892_iris_rawr_outputs/exact_generated_runner/build_26892_iris_rawr.sh"
 [[ -f "$EXEC" && "$(sha "$EXEC")" == '37b12a9cbb5918b49d279d40d51f11fa086a0682dd487f88b6ecc7f17313069d' ]] || fail 'actual successful 26892 runner mismatch'
 cmp -s "$EXEC" "$ROOT/build_26892_iris_rawr.sh" || fail '26892 historical generator replay differs from actual executed Actions bytes'
 for k in 'REAL GLSL COMPILE: PASS' 'REAL SPIR-V VALIDATION: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS';do
  grep -F "$k" "$ARTDIR/build_26892_iris_rawr_outputs/26892_COMPILER_STATUS.txt" >/dev/null || fail "26892 successful compiler receipt missing $k"
 done
 mkdir -p "$BASE";tar -xzf "$T" -C "$BASE"
 [[ "$(find "$BASE/app" -type f | wc -l)" -eq 2025 ]] || fail '26892 file universe drift'
 (cd "$BASE" && sha256sum -c "$ROOT/26893_BASE_FULL_APP.sha256" >/dev/null) || fail '26892 exact compiled SHA manifest mismatch'
 cmp -s "$ARTDIR/build_26892_iris_rawr_outputs/26892_candidate_full_app.sha256" "$ROOT/26893_BASE_FULL_APP.sha256" || fail 'actual successful 26892 SHA receipt mismatch'
 pass 'exact 26892 successful 2025 compiled candidate, runner, receipts and artifact'
}''')

edit('verify_successful_mechanics',lambda old:append(old,''' [[ "$(sha build_26892_iris_rawr.sh)" == '37b12a9cbb5918b49d279d40d51f11fa086a0682dd487f88b6ecc7f17313069d' ]] || fail 'successful 26892 executed runner drift'
 python3 -S verify_26892_candidate.py "$WORK/historical_26891_from_26892" "$WORK/historical_26892_replayed"
 python3 -S verify_26892_semantics.py "$WORK/historical_26891_from_26892" "$WORK/historical_26892_replayed"
 python3 -S test_26892_tone_math.py
 python3 -S verify_26893_candidate.py "$BASE" "$CAND"
 python3 -S verify_26893_semantics.py "$BASE" "$CAND"
 python3 -S test_26893_tone_math.py
'''))
edit('compile_modified_runtime_shaders',lambda old:append(old,''' python3 -S verify_26893_expanded_glsl.py "$CAND" --compiler "$IRIS26864_GLSLANG" --out "$OUT/26893_actual_modified_sdr_essl310" | tee "$OUT/26893_real_sdr_gles_compiler_receipt.txt"
 grep -Fx 'PASS 26893 TWO exact changed render+gainmap ESSL310 programs; REAL PINNED COMPILE PASS' "$OUT/26893_real_sdr_gles_compiler_receipt.txt" >/dev/null || fail '26893 modified shader REAL PINNED compile missing'
'''))
edit('verify_candidate_patches',lambda old:append(old,''' python3 -S verify_26893_candidate.py "$BASE" "$CAND"
 python3 -S verify_26893_semantics.py "$BASE" "$CAND"
 python3 -S verify_26893_patches.py "$BASE" "$CAND" 26893_FORWARD_FULL_INDEX.patch 26893_ROLLBACK_FULL_INDEX.patch | tee "$OUT/26893_patch_validation.txt"
 python3 -S test_26893_negative_tamper.py "$BASE" "$CAND"
 python3 -S test_26893_tone_math.py
'''))
edit('prebuild_safety',lambda old:append(old,''' python3 -S verify_26893_candidate.py "$BASE" "$CAND"
 python3 -S verify_26893_semantics.py "$BASE" "$CAND"
 (cd "$CAND" && sha256sum -c "$ROOT/26893_UNCHANGED_PROTECTED.sha256" >/dev/null) || fail '26893 original 2021 protected source mismatch'
 test -s "$OUT/26893_real_sdr_gles_compiler_receipt.txt" && grep -F 'REAL PINNED COMPILE PASS' "$OUT/26893_real_sdr_gles_compiler_receipt.txt" >/dev/null || fail '26893 changed shader compiler gate NOT PASSED'
 cat >> "$OUT/26893_PREBUILD_SAFETY.txt" <<'EOF_26893_SAFETY'
26893_exact_successful_26892_compiled_candidate_TAR=ff4bdf32e5e60d2434eae06887e45e776b2d5727db6ee7e16a4a59404f47e8b9
26893_exact_successful_executed_26892_runner=37b12a9cbb5918b49d279d40d51f11fa086a0682dd487f88b6ecc7f17313069d
26893_runtime_scope=4 modified existing B-off SDR presentation owner source files; 2021 protected, zero add/delete
26893_reference_calibration=12 actual captured scenes, balanced garden angles preserve, backlit sky-safe, rose darken-only
26893_compiler=PINNED GLSL, Kotlin, Java, full native both ABIs + full assemble required
EOF_26893_SAFETY
'''))
# Add new post-build SHA export (inherited 26892 postbuild copy for current was wrong).
edit('postbuild_proof',lambda old:append(old,''' python3 -S verify_26893_candidate.py "$BASE" "$CAND"
 python3 -S verify_26893_semantics.py "$BASE" "$CAND"
 (cd "$CAND" && sha256sum -c "$ROOT/26893_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null)
 (cd "$CAND" && sha256sum -c "$ROOT/26893_UNCHANGED_PROTECTED.sha256" >/dev/null)
 cp 26893_EXPECTED_CANDIDATE_FULL_APP.sha256 "$OUT/26893_candidate_full_app.sha256"
 (cd "$CAND" && tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -czf "$OUT/26893_candidate_app_source.tar.gz" app)
 sha256sum "$OUT/26893_candidate_app_source.tar.gz" > "$OUT/26893_candidate_app_source.tar.gz.sha256"
 cp 26893_FORWARD_FULL_INDEX.patch 26893_ROLLBACK_FULL_INDEX.patch "$OUT/"
'''))
edit('clean_extract_replay',lambda old:append(old,''' python3 -S verify_26893_candidate.py "$BASE" "$CAND"
 python3 -S verify_26893_semantics.py "$BASE" "$CAND"
 python3 -S verify_26893_patches.py "$BASE" "$CAND" 26893_FORWARD_FULL_INDEX.patch 26893_ROLLBACK_FULL_INDEX.patch
 python3 -S test_26893_negative_tamper.py "$BASE" "$CAND"
 python3 -S test_26893_tone_math.py
 python3 -S verify_26893_expanded_glsl.py "$CAND"
 (cd "$CAND" && sha256sum -c "$ROOT/26893_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null)
 (cd "$CAND" && sha256sum -c "$ROOT/26893_UNCHANGED_PROTECTED.sha256" >/dev/null)
 sha256sum -c "$OUT/26893_candidate_app_source.tar.gz.sha256" >/dev/null
 [[ "$(sha build_26892_iris_rawr.sh)" == '37b12a9cbb5918b49d279d40d51f11fa086a0682dd487f88b6ecc7f17313069d' ]] || fail 'successful 26892 executed runner not preserved'
'''))
# Inherited postbuild uses current CAND for a 26891 manifest copy; redirect its copy to historic path.
s=s.replace('cp 26891_EXPECTED_CANDIDATE_FULL_APP.sha256 "$OUT/26893_candidate_full_app.sha256"','cp 26891_EXPECTED_CANDIDATE_FULL_APP.sha256 "$OUT/26893_historical_26891_candidate_full_app.sha256"')
s=s.replace('cp 26892_EXPECTED_CANDIDATE_FULL_APP.sha256 "$OUT/26893_candidate_full_app.sha256"','cp 26892_EXPECTED_CANDIDATE_FULL_APP.sha256 "$OUT/26893_historical_26892_candidate_full_app.sha256"')
# Previous full postbuild generates 26893 candidate TAR twice before new final export. Leave
# original full assembly proof order, final export is last and authoritative 26893 source bytes.
# Fix current version in inherited source proof paths; historic tests stay historic.
s=s.replace('VERSION_NAME=0.9726892\' "$exp/app/version.properties"','VERSION_NAME=0.9726893\' "$exp/app/version.properties"')
s=s.replace('VERSION_BUILD=26892\' "$exp/app/version.properties"','VERSION_BUILD=26893\' "$exp/app/version.properties"')
s=s.replace('runtime_authority=successful 26891 $RUNTIME_AUTHORITY_COMMIT','runtime_authority=successful 26892 $RUNTIME_AUTHORITY_COMMIT')
s=s.replace('runtime_changed_files=4 (4 existing, 0 additions/deletions); 2021 protected, B-off ONLY scene adaptive tone+contrast, 26891 HDRQ unchanged','runtime_changed_files=4 (4 existing, 0 additions/deletions); 2021 protected, B-off ONLY calibrated backlit + darken-only scene contrast, 26892 HDRQ unchanged')
s=s.replace('protected_source=2021 files byte-identical to successful 26891 compiled candidate','protected_source=2021 files byte-identical to successful 26892 compiled candidate')
s=s.replace('26892 4-path full-index','26893 4-path full-index')
# Current 26893 image math must be generated and handed off EXACTLY as shipped.
assert not any('"$ARTDIR/build_26891_iris_rawr_outputs/' in line for line in s.splitlines()),'stale 26891 artifact directory used under 26892 authority'
assert tuple(x for x in rex.findall(s) if x in STAGES)==STAGES,(rex.findall(s),STAGES)
for call in ['./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'./gradlew :app:assembleDebug --stacktrace']:
 assert call in s,call
assert 'verify_26893_expanded_glsl.py "$CAND" --compiler "$IRIS26864_GLSLANG"' in s
assert 'verify_26893_patches.py "$BASE" "$CAND" 26893_FORWARD_FULL_INDEX.patch 26893_ROLLBACK_FULL_INDEX.patch' in s
assert 'VERSION_BUILD="26893"' in s
assert s.count('\nmake_candidate(){')==1
out=R/'build_26893_iris_rawr.sh';out.write_text(s)
print('PASS 26893 generator from actual successful 26892 17-stage runner',H(out),'lines',len(s.splitlines()))
