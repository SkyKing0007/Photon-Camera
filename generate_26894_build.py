#!/usr/bin/env python3
"""Deterministically inherit EXACT SUCCESSFUL ACTIONS 26893 17-stage runner.
No replacement of historical commands or stage order. New runtime scope is
only B Super Res OFF spatial SDR/UHDR presentation; prior tests run on their
own rolled-back historical source bytes.
"""
from pathlib import Path
import hashlib,re,sys
R=(Path(sys.argv[1]) if len(sys.argv)>1 else Path('.')).resolve()
P=R/'build_26893_iris_rawr.sh'
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
EXPECTED='9a70b375fd5f0a1e5148cef7e4640b4014fe0a24d8e5f38fcada15bbc0713956'
assert P.is_file() and H(P)==EXPECTED,'26893 actual executed Actions runner NOT VERIFIED'
s=P.read_text()
STAGES=('verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','verify_candidate_patches','prebuild_safety','assemble','postbuild_proof','clean_extract_replay')
rex=re.compile(r'\n([a-z_]+)\(\)\{')
assert tuple(x for x in rex.findall(s) if x in STAGES)==STAGES

def once(old,new):
 global s
 assert s.count(old)==1,(old[:90],s.count(old))
 s=s.replace(old,new,1)
def section(n):
 start=s.index('\n'+n+'(){')+1
 end=s.index('\n}',start)+2
 return s[start:end]
def edit(n,f):
 global s
 old=section(n);new=f(old)
 assert old!=new and new.startswith(n+'(){') and new.endswith('}')
 s=s.replace(old,new,1)
def append(old,code):return old[:-2]+'\n'+code.strip('\n')+'\n}'
# Authority progression is the one and only permitted scaffold delta.
for a,b in [
 ('REPO_SCAFFOLD_BASE_COMMIT="8a62e61c9d34fca62a1d61e814fc90553eda39b2"','REPO_SCAFFOLD_BASE_COMMIT="0e80de60417b0d86da76d34580850b6d06f8f919"'),
 ('RUNTIME_ARTIFACT_ID="13048932918"; RUNTIME_ACTIONS_RUN="41216852204"','RUNTIME_ARTIFACT_ID="13057770110"; RUNTIME_ACTIONS_RUN="41239754473"'),
 ('RUNTIME_AUTHORITY_COMMIT="8a62e61c9d34fca62a1d61e814fc90553eda39b2"','RUNTIME_AUTHORITY_COMMIT="0e80de60417b0d86da76d34580850b6d06f8f919"'),
 ('RUNTIME_ARTIFACT_SHA="672c3442252db208132086423806d5258a2f537cb453a2b74a39156a8f76f408"','RUNTIME_ARTIFACT_SHA="41cbf627bdec83b145bf751ef10b1178a6eecb200c6820590da4530f6cc2cba7"'),
 ('RUNTIME_TAR_SHA="ff4bdf32e5e60d2434eae06887e45e776b2d5727db6ee7e16a4a59404f47e8b9"','RUNTIME_TAR_SHA="56c216da6a3fe895fed5eea04e70b3eaf4d3b7c534b6a89ba48d071e85c65d3b"'),
 ('VERSION_NAME="0.9726893"; VERSION_BUILD="26893"','VERSION_NAME="0.9726894"; VERSION_BUILD="26894"'),
 ('OUT="$ROOT/build_26893_iris_rawr_outputs"; WORK="$ROOT/.build_26893_iris_rawr_work"','OUT="$ROOT/build_26894_iris_rawr_outputs"; WORK="$ROOT/.build_26894_iris_rawr_work"'),
 ('ARTZIP="$WORK/26892_artifact.zip"; ARTDIR="$WORK/artifact_26892"','ARTZIP="$WORK/26893_artifact.zip"; ARTDIR="$WORK/artifact_26893"'),
 ('BASE="$WORK/exact_successful_26892_compiled_candidate"; CAND="$WORK/candidate_26893"','BASE="$WORK/exact_successful_26893_compiled_candidate"; CAND="$WORK/candidate_26894"'),
 ('# IRIS_26893_AUTHORITATIVE_ACTIONS_STAGE_ORDER','# IRIS_26894_AUTHORITATIVE_ACTIONS_STAGE_ORDER')]:once(a,b)
s=s.replace('$OUT/26893_','$OUT/26894_')
# Actual 26893 successor artifact includes this historical compiled source SPV.
once('"$ARTDIR/build_26892_iris_rawr_outputs/26888_modified_shader_spirv/Iris26887BOffHdrqMerge_prod.spv"',
     '"$ARTDIR/build_26893_iris_rawr_outputs/26888_modified_shader_spirv/Iris26887BOffHdrqMerge_prod.spv"')
# Parent 26893 successful 17 stages stay verbatim when running historical
# operations, only success-gating current candidate is moved to 26894.
parent=section('make_candidate')
history=parent.replace('make_candidate(){','historical_26893_make_candidate(){',1)
s=s.replace(parent,history+'''\nmake_candidate(){
 local H92="$WORK/historical_26892_from_26893" H93="$WORK/historical_26893_replayed"
 cp -a "$BASE" "$H92"; git -C "$H92" init -q
 (cd "$H92" && git apply --check --reverse "$ROOT/26893_FORWARD_FULL_INDEX.patch" && \\
  git apply --reverse "$ROOT/26893_FORWARD_FULL_INDEX.patch" && \\
  sha256sum -c "$ROOT/26893_BASE_FULL_APP.sha256" >/dev/null) || fail '26893 ACTUAL successful original-source rollback failed'
 rm -rf "$H92/.git"
 (local BASE="$H92" CAND="$H93"; historical_26893_make_candidate)
 diff -qr "$H93/app" "$BASE/app" >/dev/null || fail '26893 original generated successful source != ACTUAL successful compiled 26893'
 python3 -S verify_26893_candidate.py "$H92" "$BASE"
 python3 -S verify_26893_semantics.py "$H92" "$BASE"
 python3 -S verify_26893_patches.py "$H92" "$BASE" 26893_FORWARD_FULL_INDEX.patch 26893_ROLLBACK_FULL_INDEX.patch
 python3 -S test_26893_negative_tamper.py "$H92" "$BASE"
 python3 -S test_26893_tone_math.py
 python3 -S verify_26894.py candidate "$BASE" "$CAND" --transform
 python3 -S verify_26894.py semantics "$BASE" "$CAND"
 python3 -S verify_26894.py tone
}
''',1)
assert 'historical_26893_make_candidate(){' in s
# Full source/receipt currently authoritative, from the ACTUAL successful Actions artifact.
edit('verify_scope',lambda _:'''verify_scope(){
 [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail 'wrong branch'
 git merge-base --is-ancestor "$RUNTIME_AUTHORITY_COMMIT" HEAD || fail 'success 26893 runtime authority not ancestor'
 [[ -z "$(git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD -- app/src app/version.properties)" ]] || fail 'unintended live runtime drift'
 [[ -z "$(git status --porcelain -- app/src app/version.properties)" ]] || fail 'uncommitted live runtime drift'
 diff -u 26894_REPOSITORY_UPLOAD_ALLOWLIST.txt <(git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD | LC_ALL=C sort) >/dev/null || fail '26894 committed stage-only upload scope drift'
 [[ "$(sha build_26893_iris_rawr.sh)" == '9a70b375fd5f0a1e5148cef7e4640b4014fe0a24d8e5f38fcada15bbc0713956' ]] || fail 'exact successful 26893 executed runner drift'
 pass '26894 single new trigger, actual successful 26893 authority and preserved 17-stage runner'
}''')
edit('obtain_authority',lambda _:'''obtain_authority(){
 [[ -n "$TOKEN" ]] || fail 'GITHUB_TOKEN missing'
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' \\
  "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/runs/${RUNTIME_ACTIONS_RUN}" -o "$WORK/26893_run.json"
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' \\
  "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${RUNTIME_ARTIFACT_ID}" -o "$WORK/26893_artifact_metadata.json"
 python3 -S - "$WORK/26893_run.json" "$WORK/26893_artifact_metadata.json" <<'PY_AUTH_94'
import json,sys
run=json.load(open(sys.argv[1]));art=json.load(open(sys.argv[2]))
assert run['id']==41239754473 and run['conclusion']=='success' and run['head_sha']=='0e80de60417b0d86da76d34580850b6d06f8f919' and run['head_branch']=='experimental-clean-photon-rebuild'
assert art['id']==13057770110 and art.get('expired') is False and art.get('digest')=='sha256:41cbf627bdec83b145bf751ef10b1178a6eecb200c6820590da4530f6cc2cba7'
print('PASS 26893 actual successful run AND final artifact ID/digest')
PY_AUTH_94
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' \\
  "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${RUNTIME_ARTIFACT_ID}/zip" -o "$ARTZIP"
 [[ "$(sha "$ARTZIP")" == "$RUNTIME_ARTIFACT_SHA" ]] || fail '26893 artifact ZIP digest mismatch'
 unzip -q "$ARTZIP" -d "$ARTDIR"
 local T="$ARTDIR/build_26893_iris_rawr_outputs/26893_candidate_app_source.tar.gz"
 [[ -f "$T" && "$(sha "$T")" == "$RUNTIME_TAR_SHA" ]] || fail '26893 compiled source TAR SHA mismatch'
 local EXEC="$ARTDIR/build_26893_iris_rawr_outputs/exact_generated_runner/build_26893_iris_rawr.sh"
 [[ -f "$EXEC" && "$(sha "$EXEC")" == '9a70b375fd5f0a1e5148cef7e4640b4014fe0a24d8e5f38fcada15bbc0713956' ]] || fail 'actual successful 26893 runner missing/mismatch'
 cmp -s "$EXEC" "$ROOT/build_26893_iris_rawr.sh" || fail 'original 26893 generator replay NOT actual executed bytes'
 test -f "$ARTDIR/build_26893_iris_rawr_outputs/exact_generated_runner/SUCCESSFUL_ACTIONS_EVIDENCE.json" || fail '26893 successful evidence missing'
 for k in 'REAL GLSL COMPILE: PASS' 'REAL SPIR-V VALIDATION: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS';do
  grep -F "$k" "$ARTDIR/build_26893_iris_rawr_outputs/26893_COMPILER_STATUS.txt" >/dev/null || fail "successful 26893 compiler receipt missing $k"
 done
 mkdir -p "$BASE";tar -xzf "$T" -C "$BASE"
 [[ "$(find "$BASE/app" -type f | wc -l)" -eq 2025 ]] || fail '26893 actual source file count mismatch'
 (cd "$BASE" && sha256sum -c "$ROOT/26894_BASE_FULL_APP.sha256" >/dev/null) || fail '26893 exact source SHA manifest mismatch'
 cmp -s "$ARTDIR/build_26893_iris_rawr_outputs/26893_candidate_full_app.sha256" "$ROOT/26894_BASE_FULL_APP.sha256" || fail 'actual compiled 26893 SHA receipt mismatch'
 pass '26893 compiled 2025 source, successful runner SHA, full artifact digest, real compiler receipts verified'
}''')
# Prior generation 26893 validation must run on its exact historical source,
# never on the newly changed 26894 candidate (but unchanged native validators
# may still run on CAND because those domains are fully protected).
H92='"$WORK/historical_26892_from_26893"';H93='"$WORK/historical_26893_replayed"'
for n in STAGES:
 if n in ('make_candidate','verify_scope','obtain_authority'):continue
 old=section(n);new=old
 for validator in ('verify_26893_candidate.py','verify_26893_semantics.py','verify_26893_patches.py','test_26893_negative_tamper.py'):
  new=new.replace(validator+' "$BASE" "$CAND"',validator+' '+H92+' '+H93)
  new=new.replace(validator+' "$BASE" "$exp"',validator+' '+H92+' '+H93)
  new=new.replace(validator+' "$BASE" "$replay" --transform',validator+' '+H92+' '+H93) if n!='clean_extract_replay' else new
 new=new.replace('verify_26893_expanded_glsl.py "$CAND"','verify_26893_expanded_glsl.py '+H93)
 # Exact prior source manifests must validate historical successful 26893,
 # not newly intended changed shader/Java in 26894.
 new=new.replace('(cd "$CAND" && sha256sum -c "$ROOT/26893_UNCHANGED_PROTECTED.sha256"','(cd '+H93+' && sha256sum -c "$ROOT/26893_UNCHANGED_PROTECTED.sha256"')
 new=new.replace('(cd "$CAND" && sha256sum -c "$ROOT/26893_EXPECTED_CANDIDATE_FULL_APP.sha256"','(cd '+H93+' && sha256sum -c "$ROOT/26893_EXPECTED_CANDIDATE_FULL_APP.sha256"')
 if n=='clean_extract_replay':
  new=new.replace('python3 -S verify_26893_candidate.py "$BASE" "$replay" --transform','python3 -S verify_26894.py candidate "$BASE" "$replay" --transform')
 if new!=old:s=s.replace(old,new,1)
# No earlier Actions failure is allowed to recur: the historical 26888 SPV
# operand comes from actual 26893 artifact output, verified post download.
edit('verify_package',lambda o:append(o,''' test -f TRIGGER_26894.txt && grep -Fx 'RUN_26894_SPATIAL_FOREGROUND_NOISE_SAFE_FLAT_CONTRAST_V1' TRIGGER_26894.txt >/dev/null || fail '26894 exact-byte new trigger'
 python3 -S stage_26894_root.py
 sha256sum -c 26894_HANDOFF_HASHES.sha256 >/dev/null || fail '26894 staged SHA seal drift'
 python3 -S -m py_compile generate_26894_build.py stage_26894_root.py verify_26894.py test_26894_three_stage_negatives.py
 test "$(find handoff_payload_26894 -type f | wc -l)" -eq 5 || fail '26894 five-source scope drift'
 python3 -S verify_26894.py tone
'''))
edit('verify_successful_mechanics',lambda o:append(o,''' python3 -S verify_26894.py candidate "$BASE" "$CAND"
 python3 -S verify_26894.py semantics "$BASE" "$CAND"
 python3 -S verify_26894.py tone
'''))
edit('compile_modified_runtime_shaders',lambda o:append(o,''' python3 -S verify_26894.py shader "$CAND" --compiler "$IRIS26864_GLSLANG" --out "$OUT/26894_real_expanded_essl310" | tee "$OUT/26894_REAL_CHANGED_SHADER_RECEIPT.txt"
 grep -Fx 'PASS 26894 THREE exact modified GLES310 runtime programs REAL PINNED COMPILE PASS' "$OUT/26894_REAL_CHANGED_SHADER_RECEIPT.txt" >/dev/null || fail '26894 THREE actual modified shaders NOT pinned compiled'
'''))
edit('verify_candidate_patches',lambda o:append(o,''' python3 -S verify_26894.py candidate "$BASE" "$CAND"
 python3 -S verify_26894.py semantics "$BASE" "$CAND"
 python3 -S verify_26894.py tone
 python3 -S verify_26894.py patch "$BASE" "$CAND" 26894_FORWARD_FULL_INDEX.patch 26894_ROLLBACK_FULL_INDEX.patch | tee "$OUT/26894_PATCH_VALIDATION.txt"
 python3 -S verify_26894.py tamper "$BASE" "$CAND"
'''))
edit('prebuild_safety',lambda o:append(o,''' python3 -S verify_26894.py candidate "$BASE" "$CAND"
 python3 -S verify_26894.py semantics "$BASE" "$CAND"
 (cd "$CAND" && sha256sum -c "$ROOT/26894_UNCHANGED_PROTECTED.sha256" >/dev/null) || fail '26894 protected source changed'
 test -s "$OUT/26894_REAL_CHANGED_SHADER_RECEIPT.txt" && grep -Fx 'PASS 26894 THREE exact modified GLES310 runtime programs REAL PINNED COMPILE PASS' "$OUT/26894_REAL_CHANGED_SHADER_RECEIPT.txt" >/dev/null || fail '26894 real changed GLSL compilation mandatory before APK'
 cat >> "$OUT/26894_PREBUILD_SAFETY.txt" <<'EOF_26894_SAFETY'
26894_exact_successful_26893_compiled_candidate_TAR=56c216da6a3fe895fed5eea04e70b3eaf4d3b7c534b6a89ba48d071e85c65d3b
26894_actual_executed_successful_26893_runner=9a70b375fd5f0a1e5148cef7e4640b4014fe0a24d8e5f38fcada15bbc0713956
26894_runtime=2025 to 2026 files, four modified existing + one added shader, 2021 immutable protected
26894_geometry=one B-SR-OFF 32px grid RG16F source guide, 4x4 local means, no CPU stalls, shared SDR UHDR
26894_regressions=actual 26891 garden shots3/4/2, 26892 garden, 26893 sun houses+flowers+road
26894_compiler_mandatory=three expanded GLES310 real pinned, Kotlin+Java, NDK two ABIs, full assemble
EOF_26894_SAFETY
'''))
edit('postbuild_proof',lambda o:append(o,''' python3 -S verify_26894.py candidate "$BASE" "$CAND"
 python3 -S verify_26894.py semantics "$BASE" "$CAND"
 (cd "$CAND" && sha256sum -c "$ROOT/26894_UNCHANGED_PROTECTED.sha256" >/dev/null)
 (cd "$CAND" && sha256sum -c "$ROOT/26894_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null)
 cp 26894_EXPECTED_CANDIDATE_FULL_APP.sha256 "$OUT/26894_candidate_full_app.sha256"
 (cd "$CAND" && tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -czf "$OUT/26894_candidate_app_source.tar.gz" app)
 sha256sum "$OUT/26894_candidate_app_source.tar.gz" > "$OUT/26894_candidate_app_source.tar.gz.sha256"
 cp 26894_FORWARD_FULL_INDEX.patch 26894_ROLLBACK_FULL_INDEX.patch "$OUT/"
'''))
edit('clean_extract_replay',lambda o:append(o,''' python3 -S verify_26894.py candidate "$BASE" "$CAND"
 python3 -S verify_26894.py semantics "$BASE" "$CAND"
 python3 -S verify_26894.py tone
 python3 -S verify_26894.py shader "$CAND" --compiler "$IRIS26864_GLSLANG" --out "$OUT/26894_final_real_essl310"
 python3 -S verify_26894.py patch "$BASE" "$CAND" 26894_FORWARD_FULL_INDEX.patch 26894_ROLLBACK_FULL_INDEX.patch
 python3 -S verify_26894.py tamper "$BASE" "$CAND"
 python3 -S test_26894_three_stage_negatives.py
 (cd "$CAND" && sha256sum -c "$ROOT/26894_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null)
 (cd "$CAND" && sha256sum -c "$ROOT/26894_UNCHANGED_PROTECTED.sha256" >/dev/null)
 sha256sum -c "$OUT/26894_candidate_app_source.tar.gz.sha256" >/dev/null
'''))
# inherited pre-existing 17 stage ordering and compiler commands untouched
assert tuple(x for x in rex.findall(s) if x in STAGES)==STAGES
assert s.count(' ./gradlew :app:assembleDebug --stacktrace 2>&1 | tee')==1
assert s.count(' ./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac')==1
assert s.count(" ./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]'")==1
assert s.count('python3 -S verify_26889_compiled_push_abi.py ')==1
assert 'build_26893_iris_rawr_outputs/26888_modified_shader_spirv/Iris26887BOffHdrqMerge_prod.spv' in s
assert 'VERSION_NAME="0.9726894"; VERSION_BUILD="26894"' in s
out=R/'build_26894_iris_rawr.sh';out.write_text(s)
sha=H(out)
(R/'26894_GENERATED_BUILD_SHA256.txt').write_text(sha+'  build_26894_iris_rawr.sh\n')
print('PASS 26894 generated EXACT 26893 successful 17 stages, historical rollback & three real changed shaders, SHA',sha,'lines',len(s.splitlines()))
