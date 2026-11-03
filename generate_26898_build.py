#!/usr/bin/env python3
"""Deterministic additive guarded successor of ACTUAL executed successful 26897.
Keep all 17 successful mechanics, compiler CLI calls, historical regressions,
rollbacks, prebuild/assemble/postbuild/clean-extract order unchanged; append
26898 checks against the exact successful 26897 compiled source universe.
"""
from pathlib import Path
import hashlib,re,sys
R=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
parent=R/'build_26897_iris_rawr.sh'
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
EXPECTED_PARENT='1a0b521c75e12003e0ab31e91bbe9ab8ae9c85b261ba8988ed37cf2e4cfc8dd3'
assert parent.is_file() and H(parent)==EXPECTED_PARENT, 'exact executed 26897 runner missing/mismatch'
s=parent.read_text()
STAGES=('verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics',
    'prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader',
    'install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff',
    'compile_native','verify_candidate_patches','prebuild_safety','assemble','postbuild_proof','clean_extract_replay')
rx=re.compile(r'(?m)^([a-z_]+)\(\)\{')
assert tuple(n for n in rx.findall(s) if n in STAGES)==STAGES
old_stage_signatures={name:s[s.index(name+'(){'):s.index('\n}',s.index(name+'(){'))+2] for name in STAGES}
def once(a,b):
    global s
    assert s.count(a)==1,(a[:130],s.count(a))
    s=s.replace(a,b,1)
def sec(name):
    start=s.index('\n'+name+'(){')+1
    end=s.index('\n}',start)+2
    return s[start:end]
def rewrite(name,new):
    global s
    old=sec(name); assert new.startswith(name+'(){') and new.endswith('}'),name
    assert old!=new,name
    s=s.replace(old,new,1)
def append(name,code):
    old=sec(name);rewrite(name,old[:-2]+'\n'+code.strip('\n')+'\n}')

for a,b in [
    ('REPO_SCAFFOLD_BASE_COMMIT="90710da1edd9daba93601a76ae931aa8a22e3fc6"',
     'REPO_SCAFFOLD_BASE_COMMIT="217fe8ca9d63b6c144af5a8197dd0adc0025eecb"'),
    ('RUNTIME_ARTIFACT_ID="13094804636"; RUNTIME_ACTIONS_RUN="41334644093"',
     'RUNTIME_ARTIFACT_ID="13200518421"; RUNTIME_ACTIONS_RUN="41568669521"'),
    ('RUNTIME_AUTHORITY_COMMIT="b7b89a46e679fc68543af91792396b75e0e68fbb"',
     'RUNTIME_AUTHORITY_COMMIT="217fe8ca9d63b6c144af5a8197dd0adc0025eecb"'),
    ('RUNTIME_ARTIFACT_SHA="a7e91e76204268d14d32449d9906a192b3e1e76bbd67852d02f6576d8df43b76"',
     'RUNTIME_ARTIFACT_SHA="e433a1004c69e60ffc523f4dbd4417fb63189762a366f91a7522605065324b45"'),
    ('RUNTIME_TAR_SHA="9df70bdc87756847b7c5a479cb3b22fee7a47920ac277a70d14a5402e3cb6942"',
     'RUNTIME_TAR_SHA="23462eec3c2d03b55f97cdb63b686ea9133a4d5f9e50e9ffa0a26ba8a13eebe6"'),
    ('VERSION_NAME="0.9726897"; VERSION_BUILD="26897"',
     'VERSION_NAME="0.9726898"; VERSION_BUILD="26898"'),
    ('OUT="$ROOT/build_26897_iris_rawr_outputs"; WORK="$ROOT/.build_26897_iris_rawr_work"',
     'OUT="$ROOT/build_26898_iris_rawr_outputs"; WORK="$ROOT/.build_26898_iris_rawr_work"'),
    ('ARTZIP="$WORK/26895_artifact.zip"; ARTDIR="$WORK/artifact_26895"',
     'ARTZIP="$WORK/26897_artifact.zip"; ARTDIR="$WORK/artifact_26897"'),
    ('BASE="$WORK/exact_successful_26895_compiled_candidate"; CAND="$WORK/candidate_26897"',
     'BASE="$WORK/exact_successful_26897_compiled_candidate"; CAND="$WORK/candidate_26898"'),
    ('# IRIS_26897_AUTHORITATIVE_ACTIONS_STAGE_ORDER','# IRIS_26898_AUTHORITATIVE_ACTIONS_STAGE_ORDER'),
]:once(a,b)
# Move receipt names only. Historical source and historical verification CLI
# input paths remain exact, not blindly renumbered or changed.
s=s.replace('$OUT/26897_','$OUT/26898_')
once('"$ARTDIR/build_26895_iris_rawr_outputs/26888_modified_shader_spirv/Iris26887BOffHdrqMerge_prod.spv"',
     '"$ARTDIR/build_26897_iris_rawr_outputs/26888_modified_shader_spirv/Iris26887BOffHdrqMerge_prod.spv"')

# Preserve the actual 26897 historical generator unchanged and run it on its
# verified OWN successful 26895 source bytes, never on 26898 bytes.
old=sec('make_candidate')
historical=old.replace('make_candidate(){','historical_26897_make_candidate(){',1)
new='''make_candidate(){
 local H95="$WORK/historical_26895_from_26897" H97="$WORK/historical_26897_replayed"
 mkdir -p "$H95"
 local T95="$ARTDIR/build_26897_iris_rawr_outputs/26895_historical_candidate_app_source.tar.gz"
 [[ -f "$T95" && "$(sha "$T95")" == '9df70bdc87756847b7c5a479cb3b22fee7a47920ac277a70d14a5402e3cb6942' ]] || fail '26897 artifact historical 26895 TAR missing or modified'
 tar -xzf "$T95" -C "$H95"
 (cd "$H95" && sha256sum -c "$ROOT/26897_BASE_FULL_APP.sha256" >/dev/null) || fail '26897 historical 26895 source manifest mismatch'
 (local BASE="$H95" CAND="$H97"; historical_26897_make_candidate)
 diff -qr "$BASE/app" "$H97/app" >/dev/null || fail 'historical 26897 transform differs from exact successful compiled authority'
 python3 -S verify_26897.py candidate "$H95" "$H97"
 python3 -S verify_26897.py semantics "$H95" "$H97"
 python3 -S verify_26897.py patch "$H95" "$H97" 26897_FORWARD_FULL_INDEX.patch 26897_ROLLBACK_FULL_INDEX.patch
 python3 -S verify_26897.py tamper "$H95" "$H97"
 python3 -S test_26897_dng_modes.py "$H97"
 python3 -S verify_26898.py candidate "$BASE" "$CAND" --transform
 python3 -S verify_26898.py semantics "$BASE" "$CAND"
}'''
assert s.count(old)==1;s=s.replace(old,historical+'\n'+new,1)
H95='"$WORK/historical_26895_from_26897"'
H97='"$WORK/historical_26897_replayed"'
# All inherited 26897 tests and version receipts use the actual successful
# historical 26895->26897 candidate, never today's changed source.
for name in STAGES:
    if name in ('verify_scope','obtain_authority','make_candidate'):continue
    old=sec(name);new=old
    for kind in ('candidate','semantics','patch','tamper'):
        new=new.replace('verify_26897.py '+kind+' "$BASE" "$CAND"',
            'verify_26897.py '+kind+' '+H95+' '+H97)
    new=new.replace('test_26897_dng_modes.py "$CAND"', 'test_26897_dng_modes.py '+H97)
    for manifest in ('26897_UNCHANGED_PROTECTED.sha256','26897_EXPECTED_CANDIDATE_FULL_APP.sha256'):
        new=new.replace('(cd "$CAND" && sha256sum -c "$ROOT/'+manifest+'"',
            '(cd '+H97+' && sha256sum -c "$ROOT/'+manifest+'"')
    if name=='prebuild_safety':
        new=new.replace('"$CAND/app/version.properties"','"$WORK/historical_26897_replayed/app/version.properties"')
    if name=='postbuild_proof':
        new=new.replace('(cd "$CAND" && tar --sort=name',
             '(cd '+H97+' && tar --sort=name')
        # Parent's final candidate archive is historical on this successor;
        # keep its exact bytes separate from the NEW 26898 candidate TAR.
        new=new.replace('"$OUT/26898_candidate_full_app.sha256"',
            '"$OUT/26897_historical_candidate_full_app.sha256"')
        new=new.replace('"$OUT/26898_candidate_app_source.tar.gz',
            '"$OUT/26897_historical_candidate_app_source.tar.gz')
    if name=='clean_extract_replay':
        new=new.replace('diff -qr "$CAND/app" "$exp96/app" >/dev/null',
            'diff -qr '+H97+'/app "$exp96/app" >/dev/null')
        new=new.replace('"$OUT/26898_candidate_app_source.tar.gz',
            '"$OUT/26897_historical_candidate_app_source.tar.gz')
    if new!=old:rewrite(name,new)

rewrite('verify_scope','''verify_scope(){
 [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail 'wrong Photon Actions branch'
 git merge-base --is-ancestor "$REPO_SCAFFOLD_BASE_COMMIT" HEAD || fail '26897 actual successful commit not ancestor'
 [[ -z "$(git diff --name-only "$REPO_SCAFFOLD_BASE_COMMIT"..HEAD -- app/src app/version.properties)" ]] || fail 'unintended live source modifications'
 [[ -z "$(git status --porcelain -- app/src app/version.properties)" ]] || fail 'uncommitted live source modifications'
 diff -u 26898_REPOSITORY_UPLOAD_ALLOWLIST.txt <(git diff --name-only "$REPO_SCAFFOLD_BASE_COMMIT"..HEAD | LC_ALL=C sort) >/dev/null || fail '26898 repository upload scope not exactly sealed stage files'
 [[ "$(sha build_26897_iris_rawr.sh)" == '1a0b521c75e12003e0ab31e91bbe9ab8ae9c85b261ba8988ed37cf2e4cfc8dd3' ]] || fail '26897 actual successful executed runner drift'
 pass '26898 guarded scope: actual 26897 successful parent, strict uploader, no live source edits'
}''')
rewrite('obtain_authority','''obtain_authority(){
 [[ -n "$TOKEN" ]] || fail 'GITHUB_TOKEN missing'
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' \\
  "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/runs/${RUNTIME_ACTIONS_RUN}" -o "$WORK/26897_run.json"
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' \\
  "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${RUNTIME_ARTIFACT_ID}" -o "$WORK/26897_artifact_metadata.json"
 python3 -S - "$WORK/26897_run.json" "$WORK/26897_artifact_metadata.json" <<'PY_AUTH_26898'
import json,sys
run=json.load(open(sys.argv[1]));art=json.load(open(sys.argv[2]))
assert run['id']==41568669521 and run['conclusion']=='success' and run['head_sha']=='217fe8ca9d63b6c144af5a8197dd0adc0025eecb' and run['head_branch']=='experimental-clean-photon-rebuild'
assert art['id']==13200518421 and art.get('expired') is False and art.get('digest')=='sha256:e433a1004c69e60ffc523f4dbd4417fb63189762a366f91a7522605065324b45'
print('PASS exact successful 26897 run, commit, artifact, digest')
PY_AUTH_26898
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' \\
  "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${RUNTIME_ARTIFACT_ID}/zip" -o "$ARTZIP"
 [[ "$(sha "$ARTZIP")" == "$RUNTIME_ARTIFACT_SHA" ]] || fail 'actual 26897 artifact ZIP SHA incorrect'
 unzip -q "$ARTZIP" -d "$ARTDIR"
 local T="$ARTDIR/build_26897_iris_rawr_outputs/26897_candidate_app_source.tar.gz"
 [[ -f "$T" && "$(sha "$T")" == "$RUNTIME_TAR_SHA" ]] || fail 'actual compiled 26897 source TAR mismatch'
 local EXEC="$ARTDIR/build_26897_iris_rawr_outputs/exact_generated_runner/build_26897_iris_rawr.sh"
 [[ -f "$EXEC" && "$(sha "$EXEC")" == '1a0b521c75e12003e0ab31e91bbe9ab8ae9c85b261ba8988ed37cf2e4cfc8dd3' ]] || fail 'actual executed 26897 runner SHA mismatch'
 cmp -s "$EXEC" "$ROOT/build_26897_iris_rawr.sh" || fail 'generated runner differs from successful Actions executed runner'
 test -f "$ARTDIR/build_26897_iris_rawr_outputs/exact_generated_runner/SUCCESSFUL_ACTIONS_EVIDENCE.json" || fail 'missing executed runner receipt'
 for k in 'REAL GLSL COMPILE: PASS' 'REAL SPIR-V VALIDATION: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS';do
  grep -F "$k" "$ARTDIR/build_26897_iris_rawr_outputs/26897_COMPILER_STATUS.txt" >/dev/null || fail "actual 26897 compiler receipt missing $k"
 done
 mkdir -p "$BASE";tar -xzf "$T" -C "$BASE"
 [[ "$(find "$BASE/app" -type f | wc -l)" -eq 2025 ]] || fail '26897 compiled file count mismatch'
 (cd "$BASE" && sha256sum -c "$ROOT/26898_BASE_FULL_APP.sha256" >/dev/null) || fail 'actual 26897 source manifest mismatch'
 cmp -s "$ARTDIR/build_26897_iris_rawr_outputs/26897_candidate_full_app.sha256" "$ROOT/26898_BASE_FULL_APP.sha256" || fail 'actual 26897 source manifest not equal 26898 frozen base'
 pass '26897 successful compiled 2025 files + exact executed runner + real compilers confirmed'
}''')
append('verify_package',''' test -f TRIGGER_26898.txt && grep -Fx 'RUN_26898_ISOLATED_SABRE_DNG_BEFORE_B_JPEG_V1' TRIGGER_26898.txt >/dev/null || fail '26898 trigger changed'
 python3 -S stage_26898_root.py
 sha256sum -c 26898_HANDOFF_HASHES.sha256 >/dev/null || fail '26898 sealed uploaded bytes changed'
 python3 -S -m py_compile generate_26898_build.py verify_26898.py stage_26898_root.py test_26898_three_stage_negatives.py test_26898_modes.py
 test "$(find handoff_payload_26898 -type f | wc -l)" -eq 5 || fail '26898 five exact modified runtime paths required'
''')
append('verify_successful_mechanics',''' python3 -S verify_26898.py candidate "$BASE" "$CAND"
 python3 -S verify_26898.py semantics "$BASE" "$CAND"
 python3 -S test_26898_modes.py "$CAND"
''')
append('compile_modified_runtime_shaders',''' # 26898 changes NO ESSL/GLSL SPIR-V shader bytes. The inherited exact
 # successful 26897 compiler matrix above still executes unmodified.
 (cd "$CAND" && sha256sum -c "$ROOT/26898_UNCHANGED_PROTECTED.sha256" >/dev/null) || fail '26898 shader and DNG protected source changed'
''')
append('verify_candidate_patches',''' python3 -S verify_26898.py candidate "$BASE" "$CAND"
 python3 -S verify_26898.py semantics "$BASE" "$CAND"
 python3 -S verify_26898.py patch "$BASE" "$CAND" 26898_FORWARD_FULL_INDEX.patch 26898_ROLLBACK_FULL_INDEX.patch | tee "$OUT/26898_CURRENT_PATCH_PROOF.txt"
 python3 -S verify_26898.py tamper "$BASE" "$CAND"
''')
# Preserve original per-stage actual compiler invocation; no new compiler tool
# substitutions. Amend only current source/policy receipts.
old=sec('prebuild_safety')
new=old.replace('runtime_authority=successful 26895','runtime_authority=successful 26897')
new=new.replace('verification_mechanics=EXACT successful 26895 executed 17 stages','verification_mechanics=EXACT successful 26897 executed 17 stages')
new=new.replace('runtime_changed_files=3 modified existing, 2022 protected; independent early DNG publication, no A/Night/Spektra/RAW GPU algorithm changes',
    'runtime_changed_files=5 modified existing, 2020 protected; independent A DNG EGL context, early DNG-only stop, actual AHB GL receipts')
new=new.replace('protected_source=2022 files byte-identical to successful 26895 compiled candidate; DNG actual writer/Sabre math/A/Night/LONG/UHDR/vendor/GLSL protected',
    'protected_source=2020 files byte-identical to successful 26897 compiled candidate; original DNG writer/Sabre math/A/Night/LONG/UHDR/vendor/GLSL protected')
assert new!=old;rewrite('prebuild_safety',new)
append('prebuild_safety',''' python3 -S verify_26898.py candidate "$BASE" "$CAND"
 python3 -S verify_26898.py semantics "$BASE" "$CAND"
 (cd "$CAND" && sha256sum -c "$ROOT/26898_UNCHANGED_PROTECTED.sha256" >/dev/null) || fail '26898 frozen protected source changed before APK'
 test "$(grep -Fc 'VERSION_BUILD=26898' "$CAND/app/version.properties")" -eq 1 || fail '26898 incorrect version'
 test -s "$OUT/26898_CURRENT_PATCH_PROOF.txt" || fail '26898 actual patch verification not executed'
 cat >> "$OUT/26898_PREBUILD_SAFETY.txt" <<'EOF_26898_SAFETY'
26898_parent_run=41568669521
26898_parent_commit=217fe8ca9d63b6c144af5a8197dd0adc0025eecb
26898_parent_artifact=13200518421
26898_parent_compiled_tar_sha256=23462eec3c2d03b55f97cdb63b686ea9133a4d5f9e50e9ffa0a26ba8a13eebe6
26898_exact_executed_parent_runner_sha256=1a0b521c75e12003e0ab31e91bbe9ab8ae9c85b261ba8988ed37cf2e4cfc8dd3
26898_current_source=2025 files, 5 intentional changes, 2020 protected, no adds/deletes
26898_change_scope=Motion B optional Sabre DNG isolated no-share EGL and true DNG-only early exit; B GL detailed stage diagnostics
26898_protected=original Sabre DNG reconstruction, DNG writers/metadata, A, Night, LONG, Spektra, B HDRq/AMaZE math/GLSL/Vulkan executor, frame counts, color, DNG, UHDR
26898_compile=real pinned GLSL SPIRV Kotlin Java NDK two ABIs full assembly required
26898_device_outcome=NOT TESTED in Actions; installed-device JPG-only, DNG-only, JPG+DNG and A/Night proof mandatory
EOF_26898_SAFETY
''')
append('postbuild_proof',''' python3 -S verify_26898.py candidate "$BASE" "$CAND"
 python3 -S verify_26898.py semantics "$BASE" "$CAND"
 (cd "$CAND" && sha256sum -c "$ROOT/26898_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null) || fail '26898 final compiled source SHA drift'
 (cd "$CAND" && sha256sum -c "$ROOT/26898_UNCHANGED_PROTECTED.sha256" >/dev/null) || fail '26898 protected shader/DNG native/vendor source changed'
 cp 26898_EXPECTED_CANDIDATE_FULL_APP.sha256 "$OUT/26898_candidate_full_app.sha256"
 cp 26898_FORWARD_FULL_INDEX.patch 26898_ROLLBACK_FULL_INDEX.patch 26898_CHANGED_ALLOWLIST.txt 26898_ADDITIONS.txt 26898_DELETIONS.txt 26898_UNCHANGED_PROTECTED.sha256 "$OUT/"
 (cd "$CAND" && tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -czf "$OUT/26898_candidate_app_source.tar.gz" app)
 sha256sum "$OUT/26898_candidate_app_source.tar.gz" > "$OUT/26898_candidate_app_source.tar.gz.sha256"
''')
append('clean_extract_replay',''' python3 -S verify_26898.py candidate "$BASE" "$CAND"
 python3 -S verify_26898.py semantics "$BASE" "$CAND"
 python3 -S verify_26898.py patch "$BASE" "$CAND" 26898_FORWARD_FULL_INDEX.patch 26898_ROLLBACK_FULL_INDEX.patch
 python3 -S verify_26898.py tamper "$BASE" "$CAND"
 python3 -S test_26898_three_stage_negatives.py
 python3 -S test_26898_modes.py "$CAND"
 (cd "$CAND" && sha256sum -c "$ROOT/26898_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null)
 (cd "$CAND" && sha256sum -c "$ROOT/26898_UNCHANGED_PROTECTED.sha256" >/dev/null)
 sha256sum -c "$OUT/26898_candidate_app_source.tar.gz.sha256" >/dev/null
 local exp98="$WORK/extracted_actual_26898_candidate_tar";rm -rf "$exp98";mkdir -p "$exp98"
 tar -xzf "$OUT/26898_candidate_app_source.tar.gz" -C "$exp98"
 diff -qr "$CAND/app" "$exp98/app" >/dev/null || fail 'actual 26898 compiled TAR differs from compiler-tested candidate'
 grep -Fx 'VERSION_NAME=0.9726898' "$exp98/app/version.properties" >/dev/null
 grep -Fx 'VERSION_BUILD=26898' "$exp98/app/version.properties" >/dev/null
 (cd "$exp98" && sha256sum -c "$ROOT/26898_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null)
 pass '26898 exact inherited 17 stages plus current real-source DNG/JPG context, 2020 protected, native/GLSL compilers and clean-extract'
''')
# Executed historical commands and real compilers remain in each same-named
# original stage; generated script has exact 17 original stage call names/order.
assert tuple(n for n in rx.findall(s) if n in STAGES)==STAGES
for name,needle in [('compile_languages','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace'),
('compile_native',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace"),
('assemble','./gradlew :app:assembleDebug --stacktrace')]:
    assert sec(name).count(needle)==1,name
assert 'python3 -S verify_26897.py candidate '+H95+' '+H97 in s
assert 'python3 -S verify_26898.py patch "$BASE" "$CAND" 26898_FORWARD_FULL_INDEX.patch 26898_ROLLBACK_FULL_INDEX.patch' in s
out=R/'build_26898_iris_rawr.sh';out.write_text(s)
out.chmod(0o755)
print('PASS 26898 deterministic from ACTUAL 26897 executed runner sha=',H(out),'lines=',len(s.splitlines()),'all 17 historical stages')
