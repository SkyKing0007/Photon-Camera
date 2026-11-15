# Photon 26941 V1 — three-stage vscode.dev handoff

**Status: PREPARED FOR ACTIONS; no successful 26941 Actions job or device-quality proof yet.**

## Prior successful runtime authority (exact)

- Repository/branch: `SkyKing0007/Photon-Camera` / `experimental-clean-photon-rebuild`
- **26940 V1** successful Actions run `43737095231`, commit `29bdfb706442417664273de14cec8d28363a9e9d`
- Published artifact `14170559036`, archive SHA-256 `404448bec80db528390f424d5b6610fac8a290d28812bb5a2bc896e6e8a83f0b`
- Actual compiled source TAR SHA-256 `0f102fdb0190fa5afa57a083e4d89d50e0fbaa4e1273078ccde0d0076d84d5a9`
- Actual executed 26940 builder SHA-256 `7d8e025f5c47a72d3b579f93203bbb872ba714689a3251e2a60b6adabf6ffe11`
- Actual executed 26940 workflow SHA-256 `4eb334e0a1ecb6e1d3171b940f4eaf4fc98bf9dc9af749f754cd1065fe215d2b`
- 26940 compiled APK SHA-256 `fad1a78a71f808b44c57150b9abdfe8e0b048836555b4d78e810ed9356a3c748`

## Runtime correction scope

26941 preserves the **exact 2050** last successful compiled-app source universe. Exactly **7 files changed**, **2043 protected files byte-identical**, zero added/deleted source, zero third-party vendor, NDK/CMake/Gradle infrastructure modifications (two explicitly allowlisted app-native C++ files changed).

1. **B HDR+ SR OFF at lens-relative zoom <1.10x only**: preserve 26940's 32-pipeline warm coordinator, but reset descriptor pools *on first actual dispatch per fenced chunk*, not unused pools after every chunk. Retain every RAWR shader, frequency pass, frame, merge calculation, final fence, scheduling boundary and queue dependency. Opt-in is thread-local and RAII-scoped; original eager pool reset remains default for all other modes. Does not remove essential GPU synchronization; speedup magnitude not established.
2. **SDR/UHDR B OFF <1.10x only**: matched SDR display-primary brightness/contrast guide in render and gainmap, with matching smooth highlight shoulder and a highlight-gated gain map. Preserve old >=1.10x, B ON, A, A+B, Night/Motion non-B behavior. Device visual quality and exact intended look remain unverified.
3. Hide three obsolete fallback gain/sigma sliders in Settings, while retaining native defaults, stored values, and ON mode logic.

**Important:** Earlier 26940 device performance gain was modest. This update targets actual repeated driver work; it is not guaranteed to reduce the 5-6 second frequency merge. It is not a logging build. No source commit/push is performed by this handoff itself.

## Exact 3-stage upload to vscode.dev

Use the enclosed **stage path lists**, in strict order, maintaining every relative directory:

- `26941_V1_STAGE_1_UPLOAD_PATHS.txt` — source payload, transformation script, validators, hash/patch seals, receipt and instructions.
- `26941_V1_STAGE_2_UPLOAD_PATHS.txt` — `.github/workflows/build-26941-change-aware.yml`
- `26941_V1_STAGE_3_UPLOAD_PATHS.txt` — `TRIGGER_26941.txt` (last, to trigger workflow).

**Do not upload this ZIP itself as a repository file**; extract and upload the listed paths in order to the existing experimental branch. Never upload an APK. Do not modify `dev`.

## Hard verification gates inherited unchanged

- 141 historical checks with SHA-pinned command list; targeted 26886/26887, 26903 receipt, 26904 V1 shader-reserved word and V2 Spektra CMake regressions; 26940 and earlier source seals, all independent.
- Exact official 26940 run/commit/artifact/compiled-TAR/builder/workflow/APK identity and hash checks before transformation.
- 2050-source allowlist, 2043 protected checks, precise seven-file overlay, negative tests, strict forward/reverse and independent rollback `core.abbrev=7,12,40`.
- Pinned **real** `glslang` 16.5 and SPIR-V optimizer/validator for current 26941 shader inputs plus original 26904 gates; real NDK CMake both Android ABIs, Kotlin, Java, full `:app:assembleDebug`; exactly one APK and one published artifact.
- Original RawLens 2.2.86 JNI libraries extracted offline with strict hashes from the real published 26940 APK; never use stale repository APK or native release URL.
- Exact source/compiled asset/APK checks, clean-extract seal, no fake/stub tool substitutions, fail closed.

Local verification proves source/patch/host shader-contract math and safety; real Android and device verification are performed **only by Actions/device** after upload. BUILD-PROVEN requires both a successful Actions run and published artifact; speed and IQ require actual device evidence.
