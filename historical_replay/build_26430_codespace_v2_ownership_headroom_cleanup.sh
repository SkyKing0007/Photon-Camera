#!/usr/bin/env bash
set -euo pipefail

SRC="/workspaces/Photon-Camera-fresh-iris"
OUTDIR="/workspaces/Photon-Camera/fresh_iris_outputs"
BRANCH="experimental-clean-photon-rebuild"
EXPECTED_HEAD_SHORT="aac8ea5a"
STAMP="$(date +%Y%m%d_%H%M%S)"

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

sha() {
  sha256sum "$1" | awk '{print toupper($1)}'
}

cd "$SRC" || fail "Missing Codespace worktree: $SRC"
mkdir -p "$OUTDIR"

echo "======================================================================"
echo "26430 CODESPACE - V2 OWNERSHIP CLEANUP / HEADROOM RENDER"
echo "======================================================================"

echo "=== GATE 0: EXACT 26429 WORKING LINEAGE ==="
[[ "$(git branch --show-current)" == "$BRANCH" ]] || fail "Wrong branch"
[[ "$(git rev-parse --short=8 HEAD)" == "$EXPECTED_HEAD_SHORT" ]] ||   fail "Expected pushed 26428 HEAD $EXPECTED_HEAD_SHORT; actual $(git rev-parse --short=8 HEAD)"

# 26429 was intentionally built on top of pushed 26428 and not committed.
# Prove the tracked working diff contains ONLY the five 26429 source files.
mapfile -t DIFF_FILES < <(git diff --name-only -- app | sort)
EXPECTED_DIFF=(
  "app/src/main/assets/shaders/motionv2/color_transform.glsl"
  "app/src/main/assets/shaders/motionv2/direct_rgb_accumulate.glsl"
  "app/src/main/assets/shaders/motionv2/direct_rgb_init.glsl"
  "app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java"
  "app/version.properties"
)
mapfile -t EXPECTED_DIFF_SORTED < <(printf '%s\n' "${EXPECTED_DIFF[@]}" | sort)

[[ "${#DIFF_FILES[@]}" -eq "${#EXPECTED_DIFF_SORTED[@]}" ]] || {
  printf 'Current tracked diff:\n%s\n' "${DIFF_FILES[*]}"
  fail "Unexpected tracked working-tree changes exist before 26430"
}
for i in "${!EXPECTED_DIFF_SORTED[@]}"; do
  [[ "${DIFF_FILES[$i]}" == "${EXPECTED_DIFF_SORTED[$i]}" ]] || {
    printf 'Current tracked diff:\n%s\n' "${DIFF_FILES[*]}"
    fail "Tracked working tree is not the exact successful 26429 lineage"
  }
done

# Require the successful 26429 build proof before replacing any source.
LATEST_26429_LOG="$(find "$OUTDIR" -maxdepth 1 -type f   -name 'build_26429_shared_guide_reference_structure_*.txt'   -printf '%T@ %p\n' | sort -nr | head -1 | cut -d' ' -f2- || true)"
[[ -n "$LATEST_26429_LOG" && -f "$LATEST_26429_LOG" ]] ||   fail "26429 build log not found"
grep -q 'BUILD SUCCESSFUL' "$LATEST_26429_LOG" ||   fail "Latest 26429 log does not prove BUILD SUCCESSFUL"

declare -A EXPECTED
EXPECTED['app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java']='76CAC4E7FE2B185068ADE3F34D5BB04FA60E81FFF3E05D3027897501A9764874'
EXPECTED['app/src/main/assets/shaders/motionv2/direct_rgb_init.glsl']='8E0D3A176280C49D17094BC318382F9C1AF97C76FFFA85ACA7B19053F516C5C1'
EXPECTED['app/src/main/assets/shaders/motionv2/direct_rgb_accumulate.glsl']='A7BF945D386C881A9259A9626D2A7F69AE8A5DA998387248D484D91B9A50E221'
EXPECTED['app/src/main/assets/shaders/motionv2/color_transform.glsl']='37D1312419889F869164911AEC982DA7C8F7FA7FE719D04F4B5D3ED00F88B33A'
EXPECTED['app/src/main/assets/shaders/motionv2/denoise.glsl']='5A939C709C181E61534233BECFABDE9C7C9A5A6296F3F362135832D03DC0FC0C'
EXPECTED['app/version.properties']='344FFA4C4A7E7F52E0827A62E044647ADBD568093CC8D2B74E1A49CD3B2BAB90'
EXPECTED['app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java']='5D99C5E183D51D9A25FB906DD4EFA9463D10E189757B46297E8C5A68130E1C12'
EXPECTED['app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Denoise.java']='7474026F8573A5F727B809B738EA8D13F2B2EE7E484E360224F14CE1C3EF70AF'
EXPECTED['app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java']='D9D112951CF56F3E7D367E4016CA092DFB77BEA03575CAF0792020AFEAB6E27F'
EXPECTED['app/src/main/assets/shaders/motionv2/render.glsl']='7A9053712E89B6C837F99F6259DF770C6D90672E66DE5DEA55379730093B30C2'
EXPECTED['app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java']='17409FE5322F5F83DEE3159D7E54F9810A897C3D86DAF4F0A0F3692122D4D96A'
EXPECTED['app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2CfaInput.java']='C3699054F6A25308576618754A2B5317AD387DD0E8A424435779934E0EE968F2'
EXPECTED['app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2Alignment.java']='80548631423555C5C104A76E5B5950FFB44C69008D85D47440C8E01D7A0B2BA8'

declare -A CAND_HASH
CAND_HASH['app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java']='4D222AB51E82ADFDC136C4F3A21A562EDB85184CE3749CACE0AC760620120B63'
CAND_HASH['app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Denoise.java']='C451D4D98BAEA223638CDA2CA116400881440A153720A358BF1C00D1AC381C20'
CAND_HASH['app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java']='8CF11431F6819DD28748D4B3EF967AFAE2F28C28D66529BE081E79F32CEADB91'
CAND_HASH['app/src/main/assets/shaders/motionv2/color_transform.glsl']='642DDD94D9374C9792A652561AE82C67ADD73D1FB810551A9CC157FD15AAADF1'
CAND_HASH['app/src/main/assets/shaders/motionv2/denoise.glsl']='420BAB6F8D917BF8A37D5B6F5864080A1179C04AB90FBD51C0474E45898C3A1C'
CAND_HASH['app/src/main/assets/shaders/motionv2/render.glsl']='21E48BA5F74B06CC4A31C1624321A00B9C2B8656B2AC263F2B6BAA6DFDA170A4'
CAND_HASH['app/version.properties']='C027D61E741DCBD751113FE085341D6FF3BCAE7CD625697ECAB1CF4267B3F7D0'

declare -A CAND_B64
CAND_B64['app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java']='cGFja2FnZSBjb20ucGFydGljbGVzZGV2cy5waG90b25jYW1lcmEucHJvY2Vzc2luZy5vcGVuZ2wucG9zdHBpcGVsaW5lOwoKaW1wb3J0IGNvbS5wYXJ0aWNsZXNkZXZzLnBob3RvbmNhbWVyYS5wcm9jZXNzaW5nLm9wZW5nbC5ub2Rlcy5Ob2RlOwppbXBvcnQgY29tLnBhcnRpY2xlc2RldnMucGhvdG9uY2FtZXJhLnV0aWwuTG9nOwoKLyoqCiAqIElSSVNfMjY0MzBfTU9USU9OX1YyX0NPTE9SX1NBRkVUWV9PTkxZCiAqCiAqIEFwcGxpZXMgdGhlIHRpbWVzdGFtcC1vd25lZCBDYW1lcmEyIHJlZmVyZW5jZS1yZXN1bHQgY29sb3IgY29udHJhY3QgZGlyZWN0bHkuCiAqIE5vIFBob3RvbiBzZW5zb3JUb1Byb1Bob3RvLCBQcm9QaG90bywgQ0NULCBJbml0aWFsLCBvciBsZWdhY3kgY29sb3Igbm9kZS4KICoKICogMjY0MzAgbGluZWFnZSBydWxlOgogKiAyNjQyOSBmaXhlZCB0aGUgZG9taW5hbnQgQ0ZBIGVkZ2UgZmFsc2UtY29sb3IgZmFpbHVyZS4gSGlnaGxpZ2h0IGNvbG9yIHJlcGFpcgogKiBpcyB0aGVyZWZvcmUgcmVkdWNlZCB0byBhIG5lYXItcGh5c2ljYWwtc2Vuc29yLWNsaXAgc2FmZXR5IG5ldCBpbnN0ZWFkIG9mCiAqIGFjdGluZyBhcyBub3JtYWwgaGlnaGxpZ2h0IHRvbmUvZ2FtdXQgcHJvY2Vzc2luZy4KICovCnB1YmxpYyBmaW5hbCBjbGFzcyBNb3Rpb25WMkNvbG9yVHJhbnNmb3JtIGV4dGVuZHMgTm9kZSB7CiAgICBwdWJsaWMgTW90aW9uVjJDb2xvclRyYW5zZm9ybSgpIHsgc3VwZXIoIiIsICJNb3Rpb25WMkNvbG9yVHJhbnNmb3JtIik7IH0KICAgIEBPdmVycmlkZSBwdWJsaWMgdm9pZCBDb21waWxlKCkge30KCiAgICBAT3ZlcnJpZGUKICAgIHB1YmxpYyB2b2lkIFJ1bigpIHsKICAgICAgICBpZiAoIWJhc2VQaXBlbGluZS5tUGFyYW1ldGVycy5tb3Rpb25WMkFjdGl2ZSkgewogICAgICAgICAgICB0aHJvdyBuZXcgSWxsZWdhbFN0YXRlRXhjZXB0aW9uKCJNb3Rpb25WMkNvbG9yVHJhbnNmb3JtIG91dHNpZGUgTW90aW9uIFYyIik7CiAgICAgICAgfQogICAgICAgIGlmICghYmFzZVBpcGVsaW5lLm1QYXJhbWV0ZXJzLm1vdGlvblYyRGlyZWN0Q29sb3JWYWxpZCkgewogICAgICAgICAgICB0aHJvdyBuZXcgSWxsZWdhbFN0YXRlRXhjZXB0aW9uKAogICAgICAgICAgICAgICAgICAgICJNb3Rpb24gVjIgcmVxdWlyZXMgZGlyZWN0IENhbWVyYTIgQ09MT1JfQ09SUkVDVElPTl9HQUlOUyArIFRSQU5TRk9STSIpOwogICAgICAgIH0KCiAgICAgICAgZmxvYXRbXSBnID0gYmFzZVBpcGVsaW5lLm1QYXJhbWV0ZXJzLm1vdGlvblYyQ29sb3JHYWluczsKICAgICAgICBmbG9hdFtdIG0gPSBiYXNlUGlwZWxpbmUubVBhcmFtZXRlcnMubW90aW9uVjJDb2xvclRyYW5zZm9ybTsKICAgICAgICBpZiAoZyA9PSBudWxsIHx8IGcubGVuZ3RoICE9IDQgfHwgbSA9PSBudWxsIHx8IG0ubGVuZ3RoICE9IDkpIHsKICAgICAgICAgICAgdGhyb3cgbmV3IElsbGVnYWxTdGF0ZUV4Y2VwdGlvbigiSW52YWxpZCBNb3Rpb24gVjIgZGlyZWN0IGNvbG9yIG1ldGFkYXRhIGRpbWVuc2lvbnMiKTsKICAgICAgICB9CgogICAgICAgIGZsb2F0IGdyZWVuR2FpbiA9IDAuNWYgKiAoZ1sxXSArIGdbMl0pOwogICAgICAgIGZsb2F0IHNlbnNvckNsaXBMZXZlbCA9IE1hdGgubWF4KAogICAgICAgICAgICAgICAgMS4wZiwgYmFzZVBpcGVsaW5lLm1QYXJhbWV0ZXJzLm1vdGlvbkNhbm9uaWNhbEV4cG9zdXJlR2Fpbik7CgogICAgICAgIGdsUHJvZy51c2VBc3NldFByb2dyYW0oIm1vdGlvbnYyL2NvbG9yX3RyYW5zZm9ybSIpOwogICAgICAgIGdsUHJvZy5zZXRUZXh0dXJlKCJJbnB1dEJ1ZmZlciIsIHByZXZpb3VzTm9kZS5Xb3JraW5nVGV4dHVyZSk7CiAgICAgICAgZ2xQcm9nLnNldFZhcigic2Vuc29yR2FpbnMiLCBuZXcgZmxvYXRbXXtnWzBdLCBncmVlbkdhaW4sIGdbM119KTsKICAgICAgICBnbFByb2cuc2V0VmFyKCJzZW5zb3JDbGlwTGV2ZWwiLCBzZW5zb3JDbGlwTGV2ZWwpOwogICAgICAgIGdsUHJvZy5zZXRWYXIoImNvbG9yUm93MCIsIG5ldyBmbG9hdFtde21bMF0sbVsxXSxtWzJdfSk7CiAgICAgICAgZ2xQcm9nLnNldFZhcigiY29sb3JSb3cxIiwgbmV3IGZsb2F0W117bVszXSxtWzRdLG1bNV19KTsKICAgICAgICBnbFByb2cuc2V0VmFyKCJjb2xvclJvdzIiLCBuZXcgZmxvYXRbXXttWzZdLG1bN10sbVs4XX0pOwoKICAgICAgICBXb3JraW5nVGV4dHVyZSA9IGJhc2VQaXBlbGluZS5nZXRNYWluKCk7CiAgICAgICAgZ2xQcm9nLmRyYXdCbG9ja3MoV29ya2luZ1RleHR1cmUpOwogICAgICAgIGdsUHJvZy5jbG9zZWQgPSB0cnVlOwoKICAgICAgICBMb2cuZChOYW1lLCAiSVJJU18yNjQzMF9WMl9DT0xPUiIKICAgICAgICAgICAgICAgICsgIiBnYWluc1JHZUdvQj0iICsgamF2YS51dGlsLkFycmF5cy50b1N0cmluZyhnKQogICAgICAgICAgICAgICAgKyAiIGdyZWVuTWVhbj0iICsgZ3JlZW5HYWluCiAgICAgICAgICAgICAgICArICIgbWF0cml4Um93TWFqb3I9IiArIGphdmEudXRpbC5BcnJheXMudG9TdHJpbmcobSkKICAgICAgICAgICAgICAgICsgIiBzZW5zb3JDbGlwTGV2ZWw9IiArIHNlbnNvckNsaXBMZXZlbAogICAgICAgICAgICAgICAgKyAiIGNhbWVyYTJDb2xvckF1dGhvcml0eT10cnVlIgogICAgICAgICAgICAgICAgKyAiIHNlbnNvck9ubHlIaWdobGlnaHRTYWZldHk9dHJ1ZSIKICAgICAgICAgICAgICAgICsgIiB0cmFuc2Zvcm1lZE92ZXJmbG93TmV1dHJhbGl6YXRpb249ZmFsc2UiCiAgICAgICAgICAgICAgICArICIgbmVpZ2hib3JIdWVSZWNvbnN0cnVjdGlvbj1mYWxzZSIKICAgICAgICAgICAgICAgICsgIiBleHBsaWNpdERvdFJvd3M9dHJ1ZSIpOwogICAgfQp9Cg=='
CAND_B64['app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Denoise.java']='cGFja2FnZSBjb20ucGFydGljbGVzZGV2cy5waG90b25jYW1lcmEucHJvY2Vzc2luZy5vcGVuZ2wucG9zdHBpcGVsaW5lOwoKaW1wb3J0IGNvbS5wYXJ0aWNsZXNkZXZzLnBob3RvbmNhbWVyYS5wcm9jZXNzaW5nLm9wZW5nbC5ub2Rlcy5Ob2RlOwppbXBvcnQgY29tLnBhcnRpY2xlc2RldnMucGhvdG9uY2FtZXJhLnV0aWwuTG9nOwoKLyoqCiAqIElSSVNfMjY0MzBfTU9USU9OX1YyX09XTkVEX1JFU0lEVUFMX0NMRUFOVVAKICoKICogMjY0MTEncyByZWZlcmVuY2UtZXJhIGRlbm9pc2VyIGlzIHJldGlyZWQuCiAqCiAqIDI2NDMwIGNvbnN1bWVzIG9ubHkgTW90aW9uIFYyJ3MgbWVhc3VyZWQgZWZmZWN0aXZlIHRlbXBvcmFsIHN1cHBvcnQuCiAqIEl0IGRvZXMgTk9UIGNvbnN1bWUgYmFzZVBpcGVsaW5lLm5vaXNlUy9ub2lzZU8sIFBob3RvbiBub2lzZVJzdHIsCiAqIEVTRCBzdHJlbmd0aHMsIG9yIGdlbmVyaWMgcG9zdC1wcm9jZXNzaW5nIGRlbm9pc2UgY29udHJvbHMuCiAqCiAqIFRoZSB0ZW1wb3JhbCByZWNvbnN0cnVjdGlvbiBpcyBub3cgdGhlIHByaW1hcnkgZGVub2lzZXIuIFRoaXMgc3RhZ2UgcGVyZm9ybXMKICogb25seSBsaWdodCByZXNpZHVhbCAzeDMgY2xlYW51cCBhbmQgbmV2ZXIgc2hhcnBlbnMuCiAqLwpwdWJsaWMgZmluYWwgY2xhc3MgTW90aW9uVjJEZW5vaXNlIGV4dGVuZHMgTm9kZSB7CiAgICBwdWJsaWMgTW90aW9uVjJEZW5vaXNlKCkgeyBzdXBlcigiIiwgIk1vdGlvblYyRGVub2lzZSIpOyB9CiAgICBAT3ZlcnJpZGUgcHVibGljIHZvaWQgQ29tcGlsZSgpIHt9CgogICAgQE92ZXJyaWRlCiAgICBwdWJsaWMgdm9pZCBSdW4oKSB7CiAgICAgICAgaWYgKCFiYXNlUGlwZWxpbmUubVBhcmFtZXRlcnMubW90aW9uVjJBY3RpdmUpIHsKICAgICAgICAgICAgdGhyb3cgbmV3IElsbGVnYWxTdGF0ZUV4Y2VwdGlvbigiTW90aW9uVjJEZW5vaXNlIHVzZWQgb3V0c2lkZSBNb3Rpb24gVjIiKTsKICAgICAgICB9CgogICAgICAgIGZsb2F0IGVmZmVjdGl2ZVN1cHBvcnQgPSBNYXRoLm1heCgKICAgICAgICAgICAgICAgIDEuMGYsIGJhc2VQaXBlbGluZS5tUGFyYW1ldGVycy5tb3Rpb25WMkVmZmVjdGl2ZVN1cHBvcnQpOwoKICAgICAgICBnbFByb2cudXNlQXNzZXRQcm9ncmFtKCJtb3Rpb252Mi9kZW5vaXNlIik7CiAgICAgICAgZ2xQcm9nLnNldFRleHR1cmUoIklucHV0QnVmZmVyIiwgcHJldmlvdXNOb2RlLldvcmtpbmdUZXh0dXJlKTsKICAgICAgICBnbFByb2cuc2V0VmFyKCJlZmZlY3RpdmVTdXBwb3J0IiwgZWZmZWN0aXZlU3VwcG9ydCk7CgogICAgICAgIFdvcmtpbmdUZXh0dXJlID0gYmFzZVBpcGVsaW5lLmdldE1haW4oKTsKICAgICAgICBnbFByb2cuZHJhd0Jsb2NrcyhXb3JraW5nVGV4dHVyZSk7CiAgICAgICAgZ2xQcm9nLmNsb3NlZCA9IHRydWU7CgogICAgICAgIExvZy5kKE5hbWUsICJJUklTXzI2NDMwX1YyX09XTkVEX1JFU0lEVUFMX0NMRUFOVVAiCiAgICAgICAgICAgICAgICArICIgZWZmZWN0aXZlU3VwcG9ydD0iICsgZWZmZWN0aXZlU3VwcG9ydAogICAgICAgICAgICAgICAgKyAiIGtlcm5lbD0zeDMiCiAgICAgICAgICAgICAgICArICIgcGhvdG9uTm9pc2VTdGF0ZUNvbnN1bWVkPWZhbHNlIgogICAgICAgICAgICAgICAgKyAiIG5vaXNlUnN0ckNvbnN1bWVkPWZhbHNlIgogICAgICAgICAgICAgICAgKyAiIHRlbXBvcmFsUmVjb25zdHJ1Y3Rpb25QcmltYXJ5RGVub2lzZXI9dHJ1ZSIKICAgICAgICAgICAgICAgICsgIiBzaGFycGVuaW5nPWZhbHNlIik7CiAgICB9Cn0K'
CAND_B64['app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java']='cGFja2FnZSBjb20ucGFydGljbGVzZGV2cy5waG90b25jYW1lcmEucHJvY2Vzc2luZy5vcGVuZ2wucG9zdHBpcGVsaW5lOwoKaW1wb3J0IGNvbS5wYXJ0aWNsZXNkZXZzLnBob3RvbmNhbWVyYS5wcm9jZXNzaW5nLm9wZW5nbC5ub2Rlcy5Ob2RlOwppbXBvcnQgY29tLnBhcnRpY2xlc2RldnMucGhvdG9uY2FtZXJhLnV0aWwuTG9nOwoKLyoqCiAqIElSSVNfMjY0MzBfTU9USU9OX1YyX09XTkVEX0hFQURST09NX1JFTkRFUgogKgogKiBSZXBsYWNlcyB0aGUgc3RhbGUgZml4ZWQgMjY0MjAgMC43MCBzaG91bGRlci4KICogVGhlIE1vdGlvbi1vd25lZCBjYW5vbmljYWwgZXhwb3N1cmUgZ2FpbiB0ZWxscyB1cyB3aGVyZSBwaHlzaWNhbCBzZW5zb3Igd2hpdGUKICogbGl2ZXMgaW4gdGhlIGV4dGVuZGVkLWxpbmVhciByZWNvbnN0cnVjdGlvbiBkb21haW4uCiAqLwpwdWJsaWMgZmluYWwgY2xhc3MgTW90aW9uVjJSZW5kZXIgZXh0ZW5kcyBOb2RlIHsKICAgIHB1YmxpYyBNb3Rpb25WMlJlbmRlcigpIHsgc3VwZXIoIiIsICJNb3Rpb25WMlJlbmRlciIpOyB9CiAgICBAT3ZlcnJpZGUgcHVibGljIHZvaWQgQ29tcGlsZSgpIHt9CgogICAgQE92ZXJyaWRlCiAgICBwdWJsaWMgdm9pZCBSdW4oKSB7CiAgICAgICAgaWYgKCFiYXNlUGlwZWxpbmUubVBhcmFtZXRlcnMubW90aW9uVjJBY3RpdmUpIHsKICAgICAgICAgICAgdGhyb3cgbmV3IElsbGVnYWxTdGF0ZUV4Y2VwdGlvbigiTW90aW9uVjJSZW5kZXIgdXNlZCBvdXRzaWRlIE1vdGlvbiBWMiIpOwogICAgICAgIH0KCiAgICAgICAgZmxvYXQgY2Fub25pY2FsU2Vuc29yV2hpdGUgPSBNYXRoLm1heCgKICAgICAgICAgICAgICAgIDEuMGYsIGJhc2VQaXBlbGluZS5tUGFyYW1ldGVycy5tb3Rpb25DYW5vbmljYWxFeHBvc3VyZUdhaW4pOwoKICAgICAgICAvKgogICAgICAgICAqIEtlZXAgYSBzbWFsbCBzYWZldHkgbWFyZ2luIGJlbG93IHBoeXNpY2FsIHNlbnNvciB3aGl0ZS4gVW5saWtlIHRoZQogICAgICAgICAqIGZpeGVkIDI2NDIwIHNob3VsZGVyLCB0aGlzIGdyb3dzIHdpdGggdGhlIGhlYWRyb29tIGFjdHVhbGx5IHByZXNlcnZlZAogICAgICAgICAqIGJ5IHRoZSBvd25lZCBSQVcgbm9ybWFsaXphdGlvbi4KICAgICAgICAgKi8KICAgICAgICBmbG9hdCBzY2VuZVdoaXRlID0gTWF0aC5tYXgoCiAgICAgICAgICAgICAgICAxLjBmLCBNYXRoLm1pbig2LjBmLCAwLjkwZiAqIGNhbm9uaWNhbFNlbnNvcldoaXRlKSk7CgogICAgICAgIGdsUHJvZy51c2VBc3NldFByb2dyYW0oIm1vdGlvbnYyL3JlbmRlciIpOwogICAgICAgIGdsUHJvZy5zZXRUZXh0dXJlKCJJbnB1dEJ1ZmZlciIsIHByZXZpb3VzTm9kZS5Xb3JraW5nVGV4dHVyZSk7CiAgICAgICAgZ2xQcm9nLnNldFZhcigic2NlbmVXaGl0ZSIsIHNjZW5lV2hpdGUpOwoKICAgICAgICBXb3JraW5nVGV4dHVyZSA9IGJhc2VQaXBlbGluZS5nZXRNYWluKCk7CiAgICAgICAgZ2xQcm9nLmRyYXdCbG9ja3MoV29ya2luZ1RleHR1cmUpOwogICAgICAgIGdsUHJvZy5jbG9zZWQgPSB0cnVlOwoKICAgICAgICBMb2cuZChOYW1lLCAiSVJJU18yNjQzMF9WMl9SRU5ERVIiCiAgICAgICAgICAgICAgICArICIgY2Fub25pY2FsU2lnbmFsQWxyZWFkeUFwcGxpZWQ9dHJ1ZSIKICAgICAgICAgICAgICAgICsgIiBjYW5vbmljYWxTZW5zb3JXaGl0ZT0iICsgY2Fub25pY2FsU2Vuc29yV2hpdGUKICAgICAgICAgICAgICAgICsgIiBzY2VuZVdoaXRlPSIgKyBzY2VuZVdoaXRlCiAgICAgICAgICAgICAgICArICIgZml4ZWQwNzBTaG91bGRlcj1mYWxzZSIKICAgICAgICAgICAgICAgICsgIiBleHRlbmRlZExpbmVhckhlYWRyb29tQ29uc3VtZWQ9dHJ1ZSIKICAgICAgICAgICAgICAgICsgIiBodWVQcmVzZXJ2aW5nTHVtaW5hbmNlTWFwPXRydWUiCiAgICAgICAgICAgICAgICArICIgbG9jYWxUb25lPWZhbHNlIgogICAgICAgICAgICAgICAgKyAiIHNoYXJwZW5pbmc9ZmFsc2UiKTsKICAgIH0KfQo='
CAND_B64['app/src/main/assets/shaders/motionv2/color_transform.glsl']='cHJlY2lzaW9uIGhpZ2hwIGZsb2F0OwpwcmVjaXNpb24gbWVkaXVtcCBzYW1wbGVyMkQ7Cgp1bmlmb3JtIHNhbXBsZXIyRCBJbnB1dEJ1ZmZlcjsKdW5pZm9ybSB2ZWMzIHNlbnNvckdhaW5zOwp1bmlmb3JtIGZsb2F0IHNlbnNvckNsaXBMZXZlbDsKdW5pZm9ybSB2ZWMzIGNvbG9yUm93MDsKdW5pZm9ybSB2ZWMzIGNvbG9yUm93MTsKdW5pZm9ybSB2ZWMzIGNvbG9yUm93MjsKb3V0IHZlYzMgT3V0cHV0OwoKLyoKICogSVJJU18yNjQzMF9TRU5TT1JfQ0xJUF9DT0xPUl9TQUZFVFlfT05MWQogKgogKiAyNjQyOSByZXBhaXJlZCB0aGUgZG9taW5hbnQgUi9HL0IgZWRnZS1yZWdpc3RyYXRpb24vcm9idXN0bmVzcyBmYWlsdXJlLgogKiBUaGVyZWZvcmUgb3JkaW5hcnkgZXh0ZW5kZWQtbGluZWFyIGhpZ2hsaWdodHMgbXVzdCBwYXNzIHRocm91Z2ggdW50b3VjaGVkLgogKgogKiBPbmx5IGNhbWVyYS1zcGFjZSBzYW1wbGVzIGFwcHJvYWNoaW5nIHRoZSBwaHlzaWNhbCBzZW5zb3IgY2VpbGluZyBhcmUgYWxsb3dlZAogKiB0byBsb3NlIGNocm9tYSBhdXRob3JpdHkuIFRoZXJlIGlzIG5vIG91dHB1dC1zcGFjZSAib3ZlcmZsb3ciIG5ldXRyYWxpemF0aW9uLAogKiBubyBuZWlnaGJvcmluZyBodWUgZG9ub3IgYW5kIG5vIG5vcm1hbCBoaWdobGlnaHQgdG9uZSBtYXBwaW5nIGhlcmUuCiAqLwoKZmxvYXQgbWF4Myh2ZWMzIHYpIHsgcmV0dXJuIG1heCh2LnIsbWF4KHYuZyx2LmIpKTsgfQpmbG9hdCBtaW4zKHZlYzMgdikgeyByZXR1cm4gbWluKHYucixtaW4odi5nLHYuYikpOyB9Cgp2ZWMzIHRyYW5zZm9ybUJhbGFuY2VkKHZlYzMgYmFsYW5jZWQpIHsKICAgIHJldHVybiB2ZWMzKAogICAgICAgICAgICBkb3QoY29sb3JSb3cwLGJhbGFuY2VkKSwKICAgICAgICAgICAgZG90KGNvbG9yUm93MSxiYWxhbmNlZCksCiAgICAgICAgICAgIGRvdChjb2xvclJvdzIsYmFsYW5jZWQpKTsKfQoKdm9pZCBtYWluKCkgewogICAgaXZlYzIgeHk9aXZlYzIoZ2xfRnJhZ0Nvb3JkLnh5KTsKICAgIHZlYzMgY2FtZXJhUmdiPW1heCh0ZXhlbEZldGNoKElucHV0QnVmZmVyLHh5LDApLnJnYix2ZWMzKDAuMCkpOwoKICAgIGZsb2F0IHNlbnNvckNsaXA9bWF4KHNlbnNvckNsaXBMZXZlbCwxLjBlLTYpOwogICAgdmVjMyBzZW5zb3JSZWxhdGl2ZT1jYW1lcmFSZ2Ivc2Vuc29yQ2xpcDsKCiAgICAvKgogICAgICogU3RhcnQgd2l0aGRyYXdpbmcgY2hyb21hIGF1dGhvcml0eSBvbmx5IHZlcnkgbmVhciBwaHlzaWNhbCBSQVcgd2hpdGUuCiAgICAgKiBUaGlzIGlzIGRlbGliZXJhdGVseSBsYXRlciB0aGFuIDI2NDI3J3MgMC45MDAgdGhyZXNob2xkLgogICAgICovCiAgICB2ZWMzIHNlbnNvclJlbGlhYmxlPQogICAgICAgICAgICB2ZWMzKDEuMCktc21vb3Roc3RlcCgKICAgICAgICAgICAgICAgICAgICB2ZWMzKDAuOTU1KSwKICAgICAgICAgICAgICAgICAgICB2ZWMzKDAuOTk3KSwKICAgICAgICAgICAgICAgICAgICBzZW5zb3JSZWxhdGl2ZSk7CiAgICBmbG9hdCBzZW5zb3JMb3NzPTEuMC1taW4zKHNlbnNvclJlbGlhYmxlKTsKCiAgICB2ZWMzIGJhbGFuY2VkPWNhbWVyYVJnYipzZW5zb3JHYWluczsKICAgIHZlYzMgbGluZWFyU3JnYj1tYXgodHJhbnNmb3JtQmFsYW5jZWQoYmFsYW5jZWQpLHZlYzMoMC4wKSk7CgogICAgZmxvYXQgb3V0TWF4PW1heDMobGluZWFyU3JnYik7CiAgICBmbG9hdCBvdXRNaW49bWluMyhsaW5lYXJTcmdiKTsKICAgIGZsb2F0IHk9bWF4KAogICAgICAgICAgICBkb3QobGluZWFyU3JnYix2ZWMzKDAuMjEyNiwwLjcxNTIsMC4wNzIyKSksCiAgICAgICAgICAgIDAuMCk7CgogICAgLyoKICAgICAqIEEgY29sb3JmdWwgb3IgPjEuMCB0cmFuc2Zvcm1lZCBwaXhlbCBpcyBOT1QgYXV0b21hdGljYWxseSBpbnZhbGlkLgogICAgICogTmV1dHJhbGl6YXRpb24gcmVxdWlyZXMgZ2VudWluZSBwaHlzaWNhbCBzZW5zb3IgYXV0aG9yaXR5IGxvc3MuCiAgICAgKi8KICAgIGZsb2F0IGJyaWdodEhpZ2hsaWdodD1zbW9vdGhzdGVwKDAuNzgsMS4xNSx5KTsKICAgIGZsb2F0IGNoYW5uZWxTcHJlYWQ9CiAgICAgICAgICAgIChvdXRNYXgtb3V0TWluKS9tYXgob3V0TWF4LDEuMGUtNik7CiAgICBmbG9hdCBzcHJlYWRDb25jZXJuPXNtb290aHN0ZXAoMC4yNSwwLjYwLGNoYW5uZWxTcHJlYWQpOwoKICAgIGZsb2F0IHNhZmV0eUxvc3M9CiAgICAgICAgICAgIGJyaWdodEhpZ2hsaWdodAogICAgICAgICAgICAqIHNlbnNvckxvc3MKICAgICAgICAgICAgKiBtaXgoMC42NSwxLjAsc3ByZWFkQ29uY2Vybik7CgogICAgZmxvYXQgbmV1dHJhbGl6ZT1zbW9vdGhzdGVwKDAuMjgsMC44OCxzYWZldHlMb3NzKTsKICAgIGZsb2F0IG5ldXRyYWxFbmVyZ3k9bWF4KG91dE1heCx5KTsKICAgIHZlYzMgc2FmZVJnYj1taXgoCiAgICAgICAgICAgIGxpbmVhclNyZ2IsCiAgICAgICAgICAgIHZlYzMobmV1dHJhbEVuZXJneSksCiAgICAgICAgICAgIG5ldXRyYWxpemUpOwoKICAgIC8qCiAgICAgKiBGdWxseSBsb3N0IHBoeXNpY2FsIGhpZ2hsaWdodCBjb2xvciBiZWNvbWVzIGNvaGVyZW50IHdoaXRlLiBUaGlzIGlzIGEKICAgICAqIHRlcm1pbmFsIHNhZmV0eSBjb25kaXRpb24sIG5vdCBub3JtYWwgSERSIHJlbmRlcmluZy4KICAgICAqLwogICAgZmxvYXQgdGVybWluYWw9CiAgICAgICAgICAgIHNtb290aHN0ZXAoMC44OCwwLjk5NSxzZW5zb3JMb3NzKQogICAgICAgICAgICAqIHNtb290aHN0ZXAoMC45NSwxLjI1LHkpOwogICAgZmxvYXQgdGVybWluYWxFbmVyZ3k9bWF4MyhzYWZlUmdiKTsKICAgIHNhZmVSZ2I9bWl4KAogICAgICAgICAgICBzYWZlUmdiLAogICAgICAgICAgICB2ZWMzKHRlcm1pbmFsRW5lcmd5KSwKICAgICAgICAgICAgdGVybWluYWwpOwoKICAgIE91dHB1dD1tYXgoc2FmZVJnYix2ZWMzKDAuMCkpOwp9Cg=='
CAND_B64['app/src/main/assets/shaders/motionv2/denoise.glsl']='cHJlY2lzaW9uIGhpZ2hwIGZsb2F0OwpwcmVjaXNpb24gbWVkaXVtcCBzYW1wbGVyMkQ7Cgp1bmlmb3JtIHNhbXBsZXIyRCBJbnB1dEJ1ZmZlcjsKdW5pZm9ybSBmbG9hdCBlZmZlY3RpdmVTdXBwb3J0OwpvdXQgdmVjMyBPdXRwdXQ7CgovKgogKiBJUklTXzI2NDMwX0xJR0hUX1NVUFBPUlRfT1dORURfUkVTSURVQUxfQ0xFQU5VUAogKgogKiBUaGUgMjY0MjkgdGVtcG9yYWwgcmVjb25zdHJ1Y3Rpb24gaXMgdGhlIHByaW1hcnkgZGVub2lzZXIuCiAqCiAqIFRoaXMgc3RhZ2U6CiAqIC0gY29uc3VtZXMgbm8gUGhvdG9uIG5vaXNlUy9ub2lzZU8vbm9pc2VSc3RyIHN0YXRlOwogKiAtIHVzZXMgYSAzeDMgZWRnZS1hd2FyZSBuZWlnaGJvcmhvb2QgaW5zdGVhZCBvZiB0aGUgb2xkIDV4NSBjbGVhbnVwOwogKiAtIGFwcGxpZXMgb25seSBzbWFsbCBsdW1hL2Nocm9tYSByZXNpZHVhbCBjb3JyZWN0aW9uOwogKiAtIHByb3RlY3RzIGRldGFpbCBhbmQgYnJpZ2h0IGhpZ2hsaWdodHM7CiAqIC0gcGVyZm9ybXMgbm8gc2hhcnBlbmluZy4KICovCgpmbG9hdCBsdW1pbmFuY2UodmVjMyBjKSB7CiAgICByZXR1cm4gZG90KGMsdmVjMygwLjIxMjYsMC43MTUyLDAuMDcyMikpOwp9Cgp2b2lkIG1haW4oKSB7CiAgICBpdmVjMiBwPWl2ZWMyKGdsX0ZyYWdDb29yZC54eSk7CiAgICBpdmVjMiBzej10ZXh0dXJlU2l6ZShJbnB1dEJ1ZmZlciwwKTsKICAgIHZlYzMgYz1tYXgodGV4ZWxGZXRjaChJbnB1dEJ1ZmZlcixwLDApLnJnYix2ZWMzKDAuMCkpOwogICAgZmxvYXQgeTA9bWF4KGx1bWluYW5jZShjKSwwLjApOwoKICAgIGZsb2F0IHN1cHBvcnRDb25maWRlbmNlPQogICAgICAgICAgICBjbGFtcCgoZWZmZWN0aXZlU3VwcG9ydC0yLjApLzguMCwwLjAsMS4wKTsKCiAgICBmbG9hdCB5TWluPXkwOwogICAgZmxvYXQgeU1heD15MDsKICAgIGZsb2F0IHN1bVc9MC4wOwogICAgZmxvYXQgc3VtRz0wLjA7CiAgICBmbG9hdCBzdW1SRz0wLjA7CiAgICBmbG9hdCBzdW1CRz0wLjA7CgogICAgLyoKICAgICAqIDN4MyBvbmx5LiBOZWlnaGJvciByZWplY3Rpb24gaXMgZHJpdmVuIGJ5IGFscmVhZHktdHJhbnNmb3JtZWQgbHVtaW5hbmNlLAogICAgICogbm90IGJ5IGdlbmVyaWMgUGhvdG9uIG5vaXNlIHR1bmluZy4KICAgICAqLwogICAgZmxvYXQgZWRnZVNjYWxlPTAuMDE4KzAuMDcwKnNxcnQobWF4KHkwLDAuMCkpOwoKICAgIGZvcihpbnQgb3k9LTE7b3k8PTE7b3krKykgewogICAgICAgIGZvcihpbnQgb3g9LTE7b3g8PTE7b3grKykgewogICAgICAgICAgICBpdmVjMiBxPWNsYW1wKAogICAgICAgICAgICAgICAgICAgIHAraXZlYzIob3gsb3kpLAogICAgICAgICAgICAgICAgICAgIGl2ZWMyKDApLAogICAgICAgICAgICAgICAgICAgIHN6LWl2ZWMyKDEpKTsKICAgICAgICAgICAgdmVjMyBzPW1heCh0ZXhlbEZldGNoKElucHV0QnVmZmVyLHEsMCkucmdiLHZlYzMoMC4wKSk7CiAgICAgICAgICAgIGZsb2F0IHlzPW1heChsdW1pbmFuY2UocyksMC4wKTsKCiAgICAgICAgICAgIHlNaW49bWluKHlNaW4seXMpOwogICAgICAgICAgICB5TWF4PW1heCh5TWF4LHlzKTsKCiAgICAgICAgICAgIGZsb2F0IGR5PWFicyh5cy15MCk7CiAgICAgICAgICAgIGZsb2F0IGVkZ2VXZWlnaHQ9ZXhwKAogICAgICAgICAgICAgICAgICAgIC0wLjUqZHkqZHkvCiAgICAgICAgICAgICAgICAgICAgbWF4KGVkZ2VTY2FsZSplZGdlU2NhbGUsMS4wZS02KSk7CiAgICAgICAgICAgIGZsb2F0IHNwYXRpYWw9CiAgICAgICAgICAgICAgICAgICAgKG94PT0wICYmIG95PT0wKSA/IDEuMCA6CiAgICAgICAgICAgICAgICAgICAgKChveD09MCB8fCBveT09MCkgPyAwLjcyIDogMC41MCk7CiAgICAgICAgICAgIGZsb2F0IHc9ZWRnZVdlaWdodCpzcGF0aWFsOwoKICAgICAgICAgICAgc3VtVys9dzsKICAgICAgICAgICAgc3VtRys9dypzLmc7CiAgICAgICAgICAgIHN1bVJHKz13KihzLnItcy5nKTsKICAgICAgICAgICAgc3VtQkcrPXcqKHMuYi1zLmcpOwogICAgICAgIH0KICAgIH0KCiAgICBmbG9hdCBpbnZXPTEuMC9tYXgoc3VtVywxLjBlLTYpOwogICAgZmxvYXQgZmlsdGVyZWRHPXN1bUcqaW52VzsKICAgIGZsb2F0IGZpbHRlcmVkUkc9c3VtUkcqaW52VzsKICAgIGZsb2F0IGZpbHRlcmVkQkc9c3VtQkcqaW52VzsKCiAgICBmbG9hdCBsb2NhbFJhbmdlPW1heCh5TWF4LXlNaW4sMC4wKTsKICAgIGZsb2F0IGRldGFpbFRocmVzaG9sZD0wLjAxMCswLjA3NSp5MDsKICAgIGZsb2F0IGRldGFpbEV2aWRlbmNlPXNtb290aHN0ZXAoCiAgICAgICAgICAgIGRldGFpbFRocmVzaG9sZCwKICAgICAgICAgICAgMy4wKmRldGFpbFRocmVzaG9sZCswLjAwMiwKICAgICAgICAgICAgbG9jYWxSYW5nZSk7CgogICAgLyoKICAgICAqIEF0IHN0cm9uZyB0ZW1wb3JhbCBzdXBwb3J0OgogICAgICogICBmbGF0IGx1bWEgPD0gfjEuNSUsIGRldGFpbGVkIGx1bWEgPD0gfjAuMyUKICAgICAqICAgZmxhdCBjaHJvbWEgPD0gfjUlLCAgIGRldGFpbGVkIGNocm9tYSA8PSB+MS41JQogICAgICoKICAgICAqIEF0IHdlYWsgc3VwcG9ydCB0aGUgcmVzaWR1YWwgY2xlYW51cCByaXNlcyBnZW50bHksIGJ1dCBuZXZlciBhcHByb2FjaGVzCiAgICAgKiB0aGUgb2xkIDI2NDExLzI2NDIzIDMwLTkwJSBjaHJvbWEgZmlsdGVyaW5nLgogICAgICovCiAgICBmbG9hdCBmbGF0THVtYT1taXgoMC4wNDUsMC4wMTUsc3VwcG9ydENvbmZpZGVuY2UpOwogICAgZmxvYXQgZGV0YWlsTHVtYT1taXgoMC4wMTIsMC4wMDMsc3VwcG9ydENvbmZpZGVuY2UpOwogICAgZmxvYXQgbHVtYVN0cmVuZ3RoPW1peCgKICAgICAgICAgICAgZmxhdEx1bWEsCiAgICAgICAgICAgIGRldGFpbEx1bWEsCiAgICAgICAgICAgIGRldGFpbEV2aWRlbmNlKTsKCiAgICBmbG9hdCBmbGF0Q2hyb21hPW1peCgwLjE4LDAuMDUsc3VwcG9ydENvbmZpZGVuY2UpOwogICAgZmxvYXQgZGV0YWlsQ2hyb21hPW1peCgwLjA2LDAuMDE1LHN1cHBvcnRDb25maWRlbmNlKTsKICAgIGZsb2F0IGNocm9tYVN0cmVuZ3RoPW1peCgKICAgICAgICAgICAgZmxhdENocm9tYSwKICAgICAgICAgICAgZGV0YWlsQ2hyb21hLAogICAgICAgICAgICBkZXRhaWxFdmlkZW5jZSk7CgogICAgLyoKICAgICAqIE5ldmVyIHNtZWFyIGNvbG9yIGJhY2sgYWNyb3NzIGJyaWdodCBjbGlwcGluZyBib3VuZGFyaWVzLgogICAgICovCiAgICBmbG9hdCBoaWdobGlnaHRQcm90ZWN0PXNtb290aHN0ZXAoMC42NSwwLjk1LHkwKTsKICAgIGx1bWFTdHJlbmd0aCo9MS4wLTAuOTIqaGlnaGxpZ2h0UHJvdGVjdDsKICAgIGNocm9tYVN0cmVuZ3RoKj0xLjAtMC45NipoaWdobGlnaHRQcm90ZWN0OwoKICAgIGZsb2F0IG91dEc9bWl4KGMuZyxmaWx0ZXJlZEcsbHVtYVN0cmVuZ3RoKTsKICAgIGZsb2F0IHJnPW1peChjLnItYy5nLGZpbHRlcmVkUkcsY2hyb21hU3RyZW5ndGgpOwogICAgZmxvYXQgYmc9bWl4KGMuYi1jLmcsZmlsdGVyZWRCRyxjaHJvbWFTdHJlbmd0aCk7CgogICAgT3V0cHV0PW1heCgKICAgICAgICAgICAgdmVjMyhvdXRHK3JnLG91dEcsb3V0RytiZyksCiAgICAgICAgICAgIHZlYzMoMC4wKSk7Cn0K'
CAND_B64['app/src/main/assets/shaders/motionv2/render.glsl']='cHJlY2lzaW9uIGhpZ2hwIGZsb2F0OwpwcmVjaXNpb24gbWVkaXVtcCBzYW1wbGVyMkQ7Cgp1bmlmb3JtIHNhbXBsZXIyRCBJbnB1dEJ1ZmZlcjsKdW5pZm9ybSBmbG9hdCBzY2VuZVdoaXRlOwpvdXQgdmVjMyBPdXRwdXQ7CgovKgogKiBJUklTXzI2NDMwX0NBTk9OSUNBTF9IRUFEUk9PTV9IRFJfVE9fU0RSCiAqCiAqIFJldGlyZXMgSVJJU18yNjQyMCdzIGZpeGVkIDAuNzAgYXN5bXB0b3RpYyBzaG91bGRlci4KICoKICogVmFsdWVzIGJlbG93IDAuNTAgbGluZWFyIGFyZSB1bnRvdWNoZWQuCiAqIEFib3ZlIHRoYXQsIHRoZSBhdmFpbGFibGUgZGlzcGxheSByYW5nZSBpcyBhbGxvY2F0ZWQgYWNjb3JkaW5nIHRvIHRoZQogKiBNb3Rpb24tb3duZWQgcGh5c2ljYWwgaGVhZHJvb20gKHNjZW5lV2hpdGUpLCBkZXJpdmVkIGZyb20gdGhlIGNhbm9uaWNhbCBSQVcKICogZXhwb3N1cmUgZ2Fpbi4gVGhpcyBwcmVzZXJ2ZXMgc3Vic3RhbnRpYWxseSBtb3JlIHdpbmRvdy9za3kgc2VwYXJhdGlvbi4KICovCgpmbG9hdCBtYXgzKHZlYzMgdikgewogICAgcmV0dXJuIG1heCh2LnIsbWF4KHYuZyx2LmIpKTsKfQoKZmxvYXQgbHVtaW5hbmNlKHZlYzMgYykgewogICAgcmV0dXJuIGRvdChjLHZlYzMoMC4yMTI2LDAuNzE1MiwwLjA3MjIpKTsKfQoKZmxvYXQgc3JnYkVuY29kZShmbG9hdCB4KSB7CiAgICB4PW1heCh4LDAuMCk7CiAgICByZXR1cm4geDw9MC4wMDMxMzA4CiAgICAgICAgICAgID8gMTIuOTIqeAogICAgICAgICAgICA6IDEuMDU1KnBvdyh4LDEuMC8yLjQpLTAuMDU1Owp9Cgp2ZWMzIHNyZ2JFbmNvZGUodmVjMyB4KSB7CiAgICByZXR1cm4gdmVjMygKICAgICAgICAgICAgc3JnYkVuY29kZSh4LnIpLAogICAgICAgICAgICBzcmdiRW5jb2RlKHguZyksCiAgICAgICAgICAgIHNyZ2JFbmNvZGUoeC5iKSk7Cn0KCmZsb2F0IG1hcEhlYWRyb29tTHVtaW5hbmNlKGZsb2F0IHkpIHsKICAgIGNvbnN0IGZsb2F0IHN0YXJ0PTAuNTA7CiAgICBpZih5PD1zdGFydCkgcmV0dXJuIHk7CgogICAgZmxvYXQgd2hpdGVQb2ludD1tYXgoc2NlbmVXaGl0ZSxzdGFydCswLjA1KTsKCiAgICAvKgogICAgICogSWYgdGhlcmUgaXMgbGl0dGxlIHBoeXNpY2FsIGhlYWRyb29tLCBzZW5zb3Igd2hpdGUgbWFwcyBjbG9zZSB0byBkaXNwbGF5CiAgICAgKiB3aGl0ZS4gSWYgTW90aW9uIHByZXNlcnZlZCBzZXZlcmFsIHRpbWVzIGRpc3BsYXktd2hpdGUgZW5lcmd5LCBzcHJlYWQgaXQKICAgICAqIGFjcm9zcyB0aGUgcmVtYWluaW5nIFNEUiByYW5nZSBpbnN0ZWFkIG9mIGNydXNoaW5nIGl0IGludG8gMC45My0xLjAwLgogICAgICovCiAgICBmbG9hdCB4PWNsYW1wKAogICAgICAgICAgICAoeS1zdGFydCkvbWF4KHdoaXRlUG9pbnQtc3RhcnQsMS4wZS02KSwKICAgICAgICAgICAgMC4wLAogICAgICAgICAgICAxLjApOwoKICAgIGNvbnN0IGZsb2F0IGxvZ1NoYXBlPTYuMDsKICAgIGZsb2F0IHNoYXBlZD0KICAgICAgICAgICAgbG9nKDEuMCtsb2dTaGFwZSp4KQogICAgICAgICAgICAvbG9nKDEuMCtsb2dTaGFwZSk7CgogICAgcmV0dXJuIHN0YXJ0KygxLjAtc3RhcnQpKnNoYXBlZDsKfQoKdmVjMyBtYXBFeHRlbmRlZExpbmVhckhlYWRyb29tKHZlYzMgcmdiKSB7CiAgICByZ2I9bWF4KHJnYix2ZWMzKDAuMCkpOwogICAgZmxvYXQgeT1tYXgobHVtaW5hbmNlKHJnYiksMC4wKTsKICAgIGlmKHk8PTEuMGUtNykgcmV0dXJuIHJnYjsKCiAgICBmbG9hdCBtYXBwZWRZPW1hcEhlYWRyb29tTHVtaW5hbmNlKHkpOwogICAgcmV0dXJuIHJnYioobWFwcGVkWS95KTsKfQoKLyoKICogSlBFRy9zUkdCIGNhbm5vdCBlbmNvZGUgYSBjaGFubmVsIGFib3ZlIDEuMC4gSWYgdG9uZS1tYXBwZWQgbHVtaW5hbmNlIGlzCiAqIHZhbGlkIGJ1dCBvbmUgc2F0dXJhdGVkIGNoYW5uZWwgc3RpbGwgZXhjZWVkcyB0aGUgZGlzcGxheSBnYW11dCwgc2hyaW5rCiAqIGNocm9tYSBhcm91bmQgdGhlIGx1bWluYW5jZSBheGlzIGluc3RlYWQgb2YgaW5kZXBlbmRlbnRseSBjbGlwcGluZyBSL0cvQi4KICovCnZlYzMgZml0RGlzcGxheUdhbXV0KHZlYzMgcmdiKSB7CiAgICByZ2I9bWF4KHJnYix2ZWMzKDAuMCkpOwogICAgZmxvYXQgcGVhaz1tYXgzKHJnYik7CiAgICBpZihwZWFrPD0xLjApIHJldHVybiByZ2I7CgogICAgZmxvYXQgeT1tYXgobHVtaW5hbmNlKHJnYiksMC4wKTsKICAgIGlmKHk+PTEuMCkgcmV0dXJuIHZlYzMoMS4wKTsKCiAgICBmbG9hdCBjaHJvbWFTY2FsZT0KICAgICAgICAgICAgY2xhbXAoCiAgICAgICAgICAgICAgICAgICAgKDEuMC15KQogICAgICAgICAgICAgICAgICAgIC9tYXgocGVhay15LDEuMGUtNiksCiAgICAgICAgICAgICAgICAgICAgMC4wLAogICAgICAgICAgICAgICAgICAgIDEuMCk7CgogICAgcmV0dXJuIHZlYzMoeSkrKHJnYi12ZWMzKHkpKSpjaHJvbWFTY2FsZTsKfQoKdm9pZCBtYWluKCkgewogICAgaXZlYzIgeHk9aXZlYzIoZ2xfRnJhZ0Nvb3JkLnh5KTsKICAgIHZlYzMgbGluZWFyU3JnYj1tYXgoCiAgICAgICAgICAgIHRleGVsRmV0Y2goSW5wdXRCdWZmZXIseHksMCkucmdiLAogICAgICAgICAgICB2ZWMzKDAuMCkpOwoKICAgIGxpbmVhclNyZ2I9bWFwRXh0ZW5kZWRMaW5lYXJIZWFkcm9vbShsaW5lYXJTcmdiKTsKICAgIGxpbmVhclNyZ2I9Zml0RGlzcGxheUdhbXV0KGxpbmVhclNyZ2IpOwoKICAgIE91dHB1dD1jbGFtcCgKICAgICAgICAgICAgc3JnYkVuY29kZShsaW5lYXJTcmdiKSwKICAgICAgICAgICAgdmVjMygwLjApLAogICAgICAgICAgICB2ZWMzKDEuMCkpOwp9Cg=='
CAND_B64['app/version.properties']='I1dlZCBBdWcgMDUgMjI6NTY6MDQgRURUIDIwMjYKVkVSU0lPTl9OQU1FPTAuOTcyNjQzMApWRVJTSU9OX0JVSUxEPTI2NDMwCg=='

for rel in "${!EXPECTED[@]}"; do
  [[ -f "$rel" ]] || fail "Missing 26429 lineage source: $rel"
  actual="$(sha "$rel")"
  [[ "$actual" == "${EXPECTED[$rel]}" ]] ||     fail "26429 lineage hash mismatch: $rel expected=${EXPECTED[$rel]} actual=$actual"
done

grep -q 'IRIS_26429_SHARED_GUIDE_ROBUSTNESS_REFERENCE_STRUCTURE' "app/src/main/assets/shaders/motionv2/direct_rgb_accumulate.glsl" ||   fail "26429 shared-guide accumulator marker missing"
grep -q 'rgbPredictionRobustness=false' "app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java" ||   fail "26429 RGB-prediction robustness removal missing"
grep -q 'referenceCfaStructure=' "app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java" ||   fail "26429 reference-structure ownership missing"
grep -q 'exposureFusion=false esd=false ablc=false' "app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java" ||   fail "Motion V2 legacy-node bypass telemetry missing"
grep -q 'initial=false autoExposure=false' "app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java" ||   fail "Motion V2 Initial/AutoExposure bypass telemetry missing"
grep -q 'captureSharpening=false correctingFlow=false sharpen2=false' "app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java" ||   fail "Motion V2 sharpening/correcting-flow bypass telemetry missing"

echo "PASS: 26429 reconstruction + V2 isolation lineage proven"

echo "=== GATE 1: BACKUP BRANCH + PRE-EDIT PATCH ==="
SAFETY="$SRC/safety_26430_v2_ownership_cleanup_$STAMP"
CAND="$SAFETY/candidate"
ORIG="$SAFETY/originals"
mkdir -p "$CAND" "$ORIG"

BACKUP="backup/codespace-before-26430-v2-ownership-cleanup-$STAMP"
git branch "$BACKUP"

PREPATCH="$SAFETY/pre_26430_working_tree.patch"
git diff --binary HEAD -- app > "$PREPATCH"

TARGETS=(
  "app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java"
  "app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Denoise.java"
  "app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java"
  "app/src/main/assets/shaders/motionv2/color_transform.glsl"
  "app/src/main/assets/shaders/motionv2/denoise.glsl"
  "app/src/main/assets/shaders/motionv2/render.glsl"
  "app/version.properties"
)

for rel in "${TARGETS[@]}"; do
  mkdir -p "$ORIG/$(dirname "$rel")"
  cp -a "$rel" "$ORIG/$rel"
done

PROTECTED_BEFORE="$SAFETY/protected_hashes_before.txt"
PROTECTED_AFTER="$SAFETY/protected_hashes_after.txt"

hash_protected() {
  local out="$1"
  : > "$out"
  while IFS= read -r -d '' f; do
    skip=0
    for t in "${TARGETS[@]}"; do
      [[ "$f" == "$t" ]] && skip=1 && break
    done
    [[ "$skip" -eq 1 ]] && continue
    printf '%s  %s\n' "$(sha "$f")" "$f" >> "$out"
  done < <(git ls-files -z app)
  sort -o "$out" "$out"
}

hash_protected "$PROTECTED_BEFORE"

echo "=== GATE 2: COMPLETE TEMPORARY CANDIDATES ==="
for rel in "${!CAND_B64[@]}"; do
  dst="$CAND/$rel"
  mkdir -p "$(dirname "$dst")"
  printf '%s' "${CAND_B64[$rel]}" | base64 -d > "$dst"
  actual="$(sha "$dst")"
  [[ "$actual" == "${CAND_HASH[$rel]}" ]] ||     fail "Candidate hash mismatch: $rel"
done

CCOLOR_JAVA="$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java"
CDENOISE_JAVA="$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Denoise.java"
CRENDER_JAVA="$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java"
CCOLOR="$CAND/app/src/main/assets/shaders/motionv2/color_transform.glsl"
CDENOISE="$CAND/app/src/main/assets/shaders/motionv2/denoise.glsl"
CRENDER="$CAND/app/src/main/assets/shaders/motionv2/render.glsl"
CVERSION="$CAND/app/version.properties"

# Previous-change compatibility proof.
grep -q 'IRIS_26430_MOTION_V2_COLOR_SAFETY_ONLY' "$CCOLOR_JAVA" || fail "26430 color ownership marker missing"
grep -q 'sensorOnlyHighlightSafety=true' "$CCOLOR_JAVA" || fail "Sensor-only highlight safety telemetry missing"
grep -q 'transformedOverflowNeutralization=false' "$CCOLOR_JAVA" || fail "Old output-overflow neutralization not explicitly retired"

grep -q 'IRIS_26430_MOTION_V2_OWNED_RESIDUAL_CLEANUP' "$CDENOISE_JAVA" || fail "26430 denoise ownership marker missing"
! grep -q 'basePipeline\.noiseS' "$CDENOISE_JAVA" || fail "Photon noiseS still consumed by Motion V2"
! grep -q 'basePipeline\.noiseO' "$CDENOISE_JAVA" || fail "Photon noiseO still consumed by Motion V2"
! grep -q 'noiseRstr' "$CDENOISE_JAVA" || fail "Photon noiseRstr still consumed by Motion V2"

grep -q 'IRIS_26430_MOTION_V2_OWNED_HEADROOM_RENDER' "$CRENDER_JAVA" || fail "26430 render ownership marker missing"
grep -q 'motionCanonicalExposureGain' "$CRENDER_JAVA" || fail "Owned canonical headroom not bound to Render"
grep -q 'sceneWhite' "$CRENDER_JAVA" || fail "sceneWhite binding missing"

grep -q 'IRIS_26430_SENSOR_CLIP_COLOR_SAFETY_ONLY' "$CCOLOR" || fail "26430 color shader marker missing"
! grep -q 'transformedLoss' "$CCOLOR" || fail "26427 transformed-overflow neutralization survived"
! grep -q 'overflow=' "$CCOLOR" || fail "26427 output overflow gate survived"
! grep -q 'localReliableHue' "$CCOLOR" || fail "Legacy neighboring hue repair survived"

grep -q 'IRIS_26430_LIGHT_SUPPORT_OWNED_RESIDUAL_CLEANUP' "$CDENOISE" || fail "26430 denoise shader marker missing"
! grep -q 'uniform float noiseS' "$CDENOISE" || fail "Generic noiseS uniform survived"
! grep -q 'uniform float noiseO' "$CDENOISE" || fail "Generic noiseO uniform survived"
! grep -q 'for(int oy=-2' "$CDENOISE" || fail "Old 5x5 denoise kernel survived"
grep -q 'for(int oy=-1' "$CDENOISE" || fail "New 3x3 denoise kernel missing"

grep -q 'IRIS_26430_CANONICAL_HEADROOM_HDR_TO_SDR' "$CRENDER" || fail "26430 HDR->SDR marker missing"
! grep -q 'start=0.70' "$CRENDER" || fail "Stale fixed 0.70 shoulder survived"
! grep -q 'compressDisplayHighlights' "$CRENDER" || fail "Stale 26420 shoulder function survived"
grep -q 'uniform float sceneWhite' "$CRENDER" || fail "sceneWhite shader uniform missing"
grep -q 'mapExtendedLinearHeadroom' "$CRENDER" || fail "Headroom mapper missing"
grep -q 'fitDisplayGamut' "$CRENDER" || fail "Hue-preserving display-gamut fit missing"

grep -q '^VERSION_NAME=0\.9726430$' "$CVERSION" || fail "Candidate version name mismatch"
grep -q '^VERSION_BUILD=26430$' "$CVERSION" || fail "Candidate build mismatch"

echo "candidate/source validation PASS"

echo "=== GATE 3: GLSL LEXICAL + REAL COMPILER VALIDATION ==="
VALIDATOR_PY="$SAFETY/validate_26430_glsl.py"
cat > "$VALIDATOR_PY" <<'PY'
from pathlib import Path
import re,sys

def strip_comments(s):
    s=re.sub(r'/\*.*?\*/',' ',s,flags=re.S)
    s=re.sub(r'//.*',' ',s)
    return s

paths=[Path(p) for p in sys.argv[1:]]
reserved_runtime_regressions={
    'coherent',
}

for p in paths:
    text=p.read_text()
    code=strip_comments(text)

    if re.search(r'(?m)^\s*#version\b',text):
        raise SystemExit(f"FAIL: asset owns #version: {p}")

    # Regression for the two earlier runtime shader failures.
    tokens=set(re.findall(r'\b[A-Za-z_][A-Za-z0-9_]*\b',code))
    bad=sorted(tokens & reserved_runtime_regressions)
    if bad:
        raise SystemExit(f"FAIL: known reserved runtime token(s) {bad} in {p}")

render=strip_comments(Path(sys.argv[-1]).read_text())
if 'start=0.70' in render.replace(' ',''):
    raise SystemExit("FAIL: fixed 0.70 shoulder survived")

print("LEXICAL GLSL VALIDATION PASS")
PY

python3 "$VALIDATOR_PY" "$CCOLOR" "$CDENOISE" "$CRENDER"

if ! command -v glslangValidator >/dev/null 2>&1; then
  echo "glslangValidator missing; installing before real source is touched..."
  if command -v sudo >/dev/null 2>&1; then
    sudo apt-get update
    sudo apt-get install -y glslang-tools
  else
    fail "glslangValidator is required and sudo is unavailable"
  fi
fi
command -v glslangValidator >/dev/null 2>&1 || fail "glslangValidator unavailable"

WRAP_PY="$SAFETY/make_fragment_wrapper.py"
cat > "$WRAP_PY" <<'PY'
from pathlib import Path
import sys
src=Path(sys.argv[1]).read_text()
Path(sys.argv[2]).write_text('#version 310 es\n'+src)
PY

COLOR_WRAP="$SAFETY/color_transform_26430.frag"
DENOISE_WRAP="$SAFETY/denoise_26430.frag"
RENDER_WRAP="$SAFETY/render_26430.frag"
python3 "$WRAP_PY" "$CCOLOR" "$COLOR_WRAP"
python3 "$WRAP_PY" "$CDENOISE" "$DENOISE_WRAP"
python3 "$WRAP_PY" "$CRENDER" "$RENDER_WRAP"

# Also recompile the two unchanged 26429 direct reconstruction shaders so the
# previous architecture remains part of this build's safety proof.
COMPUTE_WRAP_PY="$SAFETY/make_compute_wrapper.py"
cat > "$COMPUTE_WRAP_PY" <<'PY'
from pathlib import Path
import re,sys
src=Path(sys.argv[1]).read_text()
src=re.sub(
    r'(?m)^#define\s+LAYOUT\s+//\s*\nLAYOUT\s*\n',
    '',
    src,
    count=1)
prefix='#version 310 es\nlayout(local_size_x=8, local_size_y=8, local_size_z=1) in;\n'
Path(sys.argv[2]).write_text(prefix+src)
PY

INIT_WRAP="$SAFETY/direct_rgb_init_26429.comp"
ACC_WRAP="$SAFETY/direct_rgb_accumulate_26429.comp"
python3 "$COMPUTE_WRAP_PY" "app/src/main/assets/shaders/motionv2/direct_rgb_init.glsl" "$INIT_WRAP"
python3 "$COMPUTE_WRAP_PY" "app/src/main/assets/shaders/motionv2/direct_rgb_accumulate.glsl" "$ACC_WRAP"

GLSL_LOG="$SAFETY/glslang_validation.txt"
{
  echo "=== 26429 direct_rgb_init preserved ==="
  glslangValidator -S comp "$INIT_WRAP"
  echo "=== 26429 direct_rgb_accumulate preserved ==="
  glslangValidator -S comp "$ACC_WRAP"
  echo "=== 26430 color_transform ==="
  glslangValidator -S frag "$COLOR_WRAP"
  echo "=== 26430 denoise ==="
  glslangValidator -S frag "$DENOISE_WRAP"
  echo "=== 26430 render ==="
  glslangValidator -S frag "$RENDER_WRAP"
} 2>&1 | tee "$GLSL_LOG"

echo "GLSL COMPILER VALIDATION PASS"
echo "Temporary-copy validation: PASS"

echo "=== GATE 4: APPLY EXACT VALIDATED CANDIDATES ==="
for rel in "${!CAND_B64[@]}"; do
  cp "$CAND/$rel" "$rel"
done

echo "=== GATE 5: PRE-BUILD LINEAGE / OWNERSHIP SAFETY PROOF ==="
for rel in "${!CAND_HASH[@]}"; do
  actual="$(sha "$rel")"
  [[ "$actual" == "${CAND_HASH[$rel]}" ]] ||     fail "Applied source differs from validated candidate: $rel"
done

hash_protected "$PROTECTED_AFTER"
cmp -s "$PROTECTED_BEFORE" "$PROTECTED_AFTER" ||   fail "A protected tracked app file changed"

# Explicitly prove the validated 26429 image-formation foundation was preserved.
[[ "$(sha "app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java")" == "${EXPECTED['app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java']}" ]] || fail "26429 reconstruction Java changed"
[[ "$(sha "app/src/main/assets/shaders/motionv2/direct_rgb_init.glsl")" == "${EXPECTED['app/src/main/assets/shaders/motionv2/direct_rgb_init.glsl']}" ]] || fail "26429 direct RGB initializer changed"
[[ "$(sha "app/src/main/assets/shaders/motionv2/direct_rgb_accumulate.glsl")" == "${EXPECTED['app/src/main/assets/shaders/motionv2/direct_rgb_accumulate.glsl']}" ]] || fail "26429 direct RGB accumulator changed"
[[ "$(sha "app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2Alignment.java")" == "${EXPECTED['app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2Alignment.java']}" ]] || fail "Owned MotionV2Alignment changed"
[[ "$(sha "app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java")" == "${EXPECTED['app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java']}" ]] || fail "V2-isolated PostPipeline graph changed"
[[ "$(sha "app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2CfaInput.java")" == "${EXPECTED['app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2CfaInput.java']}" ]] || fail "Direct RGB input carrier changed"

# Prove stale processing can no longer negate the new foundation.
! grep -q 'basePipeline\.noiseS' "app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Denoise.java" || fail "Photon noiseS leaked back into Motion"
! grep -q 'basePipeline\.noiseO' "app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Denoise.java" || fail "Photon noiseO leaked back into Motion"
! grep -q 'uniform float noiseS' "app/src/main/assets/shaders/motionv2/denoise.glsl" || fail "Generic noiseS shader path leaked back"
! grep -q 'uniform float noiseO' "app/src/main/assets/shaders/motionv2/denoise.glsl" || fail "Generic noiseO shader path leaked back"
! grep -q 'start=0.70' "app/src/main/assets/shaders/motionv2/render.glsl" || fail "26420 fixed shoulder leaked back"
! grep -q 'transformedLoss' "app/src/main/assets/shaders/motionv2/color_transform.glsl" || fail "26427 output-space neutralization leaked back"

git diff --check -- "${TARGETS[@]}"
python3 "$VALIDATOR_PY" "app/src/main/assets/shaders/motionv2/color_transform.glsl" "app/src/main/assets/shaders/motionv2/denoise.glsl" "app/src/main/assets/shaders/motionv2/render.glsl"

echo "candidate/source validation PASS"
echo "Temporary-copy validation: PASS"
echo "PRE-BUILD SAFETY PROOF PASSED"

POSTPATCH="$SAFETY/post_26430_working_tree.patch"
git diff --binary HEAD -- app > "$POSTPATCH"

echo "=== GATE 6: BUILD 0.9726430 / 26430 ==="
chmod +x ./gradlew

BUILDLOG="$OUTDIR/build_26430_v2_ownership_cleanup_$STAMP.txt"
set +e
./gradlew :app:assembleDebug --stacktrace 2>&1 | tee "$BUILDLOG"
RC=${PIPESTATUS[0]}
set -e
[[ "$RC" -eq 0 ]] || fail "Gradle failed rc=$RC; see $BUILDLOG"
grep -q 'BUILD SUCCESSFUL' "$BUILDLOG" || fail "BUILD SUCCESSFUL not found"

APK_SRC="$(find app/build/outputs/apk -type f -name '*.apk' -printf '%T@ %p\n'   | sort -nr | head -1 | cut -d' ' -f2-)"
[[ -n "$APK_SRC" && -f "$APK_SRC" ]] || fail "Built APK not found"

# ONE APK ONLY. No duplicate output copy.
APK_NAME="IrisCamera-0.9726430-26430-v2-ownership-headroom-cleanup-debug.apk"
APK_ROOT="$SRC/$APK_NAME"
cp "$APK_SRC" "$APK_ROOT"

RESULT="$OUTDIR/26430_V2_OWNERSHIP_HEADROOM_CLEANUP_RESULT_$STAMP.txt"
cat > "$RESULT" <<EOF
26430 V2 OWNERSHIP + HEADROOM CLEANUP
Timestamp: $(date --iso-8601=seconds)
Branch: $BRANCH
Base committed HEAD: $(git rev-parse HEAD)
Version/build: 0.9726430 / 26430

PRESERVED / PROVEN:
- 26429 MotionV2CfaReconstruction byte-identical
- 26429 shared-guide direct RGB accumulator byte-identical
- 26429 reference-structure direct RGB initializer byte-identical
- owned MotionV2Alignment byte-identical
- direct-RGB MotionV2CfaInput byte-identical
- V2-isolated PostPipeline graph byte-identical
- ExposureFusion/ESD3D2/ABLC/Initial/AutoExposure/CaptureSharpening/CorrectingFlow/Sharpen2 remain bypassed
- no sharpening added

RETIRED STALE / CROSS-ARCHITECTURE BEHAVIOR:
- MotionV2Denoise no longer reads basePipeline.noiseS/noiseO
- generic Photon noiseRstr therefore cannot control Motion V2 residual cleanup
- old 5x5 30-90% chroma cleanup retired
- 26420 fixed 0.70 highlight shoulder retired
- 26427 transformed-RGB overflow neutralization retired
- neighboring-hue highlight reconstruction remains absent

NEW OWNED BEHAVIOR:
- light 3x3 residual cleanup driven only by measured Motion effective support
- near-physical-sensor-clip color safety only
- ordinary extended-linear highlights retain their color/headroom
- HDR->SDR white point derives from Motion canonical sensor-white headroom
- luminance headroom mapping preserves RGB ratios
- display-gamut overflow uses chroma compression rather than independent channel clipping

SAFETY:
- Backup branch: $BACKUP
- Pre-edit binary patch: $PREPATCH
- Post-edit binary patch: $POSTPATCH
- GLSL compiler proof: $GLSL_LOG
- candidate/source validation PASS
- Temporary-copy validation: PASS
- PRE-BUILD SAFETY PROOF PASSED
- BUILD SUCCESSFUL verified

APK (single copy): $APK_ROOT
Build log: $BUILDLOG

No commit.
No push.
dev untouched.
EOF

echo "======================================================================"
echo "BUILD SUCCESSFUL VERIFIED"
echo "APK: $APK_ROOT"
echo "RESULT: $RESULT"
echo "SAFETY: $SAFETY"
echo "Only one APK was created/copied for user access."
echo "No commit. No push. dev untouched."
echo "======================================================================"
