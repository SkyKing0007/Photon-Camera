# Photon 26936 V1 — ONE THREE-STAGE VSCode.dev handoff

**PREPARED FOR ACTIONS, not BUILD-PROVEN.** Not an APK, not a source checkout, and not an executable user script. User uploads the staged files; GitHub Actions performs the **real** Android full compile and artifact publication. No commit/push occurred from ChatGPT.

## Exactly three vscode.dev upload stages (branch: experimental-clean-photon-rebuild)

1. **STAGE_1_UPLOAD:** Upload *all contents* to the repository root, preserving file paths. This contains one seven-file runtime overlay under `handoff_payload_26936/app/`, exact hashes and patches, build runner, real pinned shader compiler and historical/current regressions. Do NOT upload the outer ZIP itself.
2. **STAGE_2_UPLOAD:** Upload `.github/workflows/build-26936-change-aware.yml` to the corresponding repo path. Preserve the previous historical workflow files. Do not edit `dev`.
3. **STAGE_3_UPLOAD:** Upload `TRIGGER_26936.txt` last to trigger the new guarded Actions job. The stage 3 upload will trigger only after source/verification/workflow are ready. If you use commits in vscode.dev, provide the exact commit message below.

**Commit message:** `Photon 26936: protect B ON GPU preview, smooth clipped highlights and set B OFF saturation 1.02`

## Runtime authority (not GitHub app/src)

- Exact last published successful Actions build **26935 V2**, run `43663685050`, job `132658299499`, commit `b14defae2aab3d470a41c96d688d66ba55f706ab`, artifact ID `14141841080`.
- 26935 official Actions artifact ZIP SHA-256: `22909e78c9a233eeca085f8bdec258bcd41afa78e22d8f66772f75098ca3f5eb`.
- 26935 **actual successful compiled source** TAR SHA-256: `68fc68e258d411f5187a181455487cc4ec268fbd8583f8f912fb6ffdd4513b26`.
- Actual executed 26935 builder SHA-256 `7f435e9915e6359e592610f8c2416bbdb0d75bea4966e49d6abfe1be3c0f9bfc`.
- Actual executed 26935 workflow SHA-256 `14e4d8da91d7f2b90007150e3c23be0784b6121aed5969d3c4ec6787d4e41366`.
- Published 26935 APK SHA-256 `9f7b571511f93826defe343c2a3cc567338abedecb03c1788e91962192325935`.
- The 26936 runner downloads ONLY that successful 26935 source and rehashes the published TAR, all 2,050 source files and inherited original 2.2.86 LKR native libraries from the prior APK; it never fetches RawLens GitHub release API (historical 403).
- Exact source allowlist: 7 changed, 0 new, 2,043 protected **byte-identical**. Scope is in `26936_CHANGED_RUNTIME_ALLOWLIST.txt`. No native/vendor, CMake/Gradle/NDK, routing, shutter, Spektra, DNG, A, Night, LONG, LKR 15 frames/3×2/50MP processing changed.

## What is changed, and what is not proven

1. B/SR ON during processing: GLES3 two-PBO GPU fence readback on original GL thread to avoid measured synchronous `glReadPixels` stalls; mandatory exact-timestamp and <=250ms freshness, no stale flicker phase; low-light and actual stripe compensation retain the original synchronous exact-frame anti-stripe/probe. If unsupported, fall back to original proven sync mode. Logs rate-limited. Actual video FPS still **device NOT RUN**.
2. Preview EGL `EGL_IMG_context_priority=HIGH` only if the driver advertises it and accepts it; otherwise the original ES2 context parameters. **Priority is a hint, not guaranteed GPU preemption**. B/ON background executor CPU nice +4 only during processor work, restored in finally. **No native/Vulkan scheduler change or worker tuning**; original vendor/native binaries unchanged, so substantial remaining shared GPU contention is possible and must be measured on device.
3. B/SR ON smooth white rolloff: avoids turning genuine yellow into white merely because any one color channel is bright. Preserves original Bayer R16F clipping texture, real R/G/B physical-source phase, calibrated WB neutral, LKR math. Physical fully clipped colors remain subject to approximation; visual comparison against Super Res OFF requires the device.
4. B/SR OFF only: saturation **1.07× -> 1.02×** for SDR and UHDR routes; user saturation slider still multiplies normally. Existing capture AE/highlight selection already shared with B/ON and B/OFF; this build does **not** invent underexposure or alter capture EV, frame count, or RAW normalization.
5. Original successful 26935 shutter grey-out and save publication release: **unchanged**.

## Unchanged build mechanics

Successful 26935 V2 141 precisely SHA-sealed historical executable invocations (26886/26887, 26903, 26904 V1 shader optimizer / V2 CMake failures, 26904 V3, through 26935), exact 26935 source authority, full-source manifests, strict allowlist, 12 actual host fail-closed mutations, independent full-index forward/reverse/rollback proofs at abbreviations 7/12/40, real pinned 16.5.0 glslang ESSL300/310 + SPIR-V optimizer/validator on current five shaders, original NDK/CMake both arm64-v8a/armeabi-v7a, Kotlin and Java compilation, exact one `:app:assembleDebug`, original native ELF/JNI verification and exactly one published new APK.

The first upload's Python and shell files are **Actions automation internals**, not scripts for the user to execute. **Do not manually run them**. Upload all files with names/path unchanged. No extra `.pyc`, `__pycache__`, backup branches or APK files are included.

## Passing status vs device uncertainty

Only after Actions run succeeds **AND publishes its 26936 artifact** may the result be called **BUILD-PROVEN**. That alone never proves responsive FPS or image quality. Screen recording, logcat and matched SDR/UHDR B OFF/B ON actual captures are required for on-device confirmation. If Actions fails, use the first actual compiler or SHA gate error; never bypass compilers or upload a partial build.
