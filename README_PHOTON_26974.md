# Photon 26974 — Experiment C shutter freeze and RAW handler isolation

The successful 26973 build captures the correct UI selection, but device testing on 2026-11-21 produced a frozen viewfinder and no JPEG after a C shutter press. Captured log showed the ring at 12:34:25 with no subsequent C terminal/processing milestones. The precise internal stall is unproven; source-level contributors include preview stopping until full processing and synchronous RAW file spooling on the Camera2 capture Handler.

## C-only changes

- Independent C Motion shutter bypasses the A/B ZSL/deferred gate; a repeated C shutter is explicitly rejected while its owner is active.
- When Camera2 acknowledges the exact C sequence, a preview-only repeating request resumes while the C RAW ImageReader remains exclusively owned. Normal preview RAW target is restored only at the safe terminal/sequence-end fence.
- C RAW ImageReader file I/O is moved to a dedicated callback HandlerThread only after first exact C onCaptureStarted tags a RAW reference; other Camera2 callbacks and deadline dispatch are no longer serialized behind fd.sync.
- Independent bounded acquisition watchdog, progress + timeout + stage telemetry; C physical RAW checks, saved image authentication, zero fallback and 2–30-frame limit remain.
- Physical camera sequence-end/terminal RAW ownership fence retained. 26974 original change allowlist is exactly four files including version; all 2128 protected original files unchanged.

## Guarded build / results

Runtime authority: successful 26973 Actions run **44929274749**, commit `16e56f8eb740f2f18f7c77a85dd25d8d2a45cea7`, artifact **14717056814**.
Artifact ZIP SHA256 `d12b91a0d0fe811596f97a79fcbb6400f01a87a1ac2d64d7f71d6173a220efff`.
Actual compiled TAR SHA256 `93b677a856dc146e3e50b56a33b2d5adb114a3e111fe7f7d83be45e750638cac`.
Executed builder SHA256 `7bd94a6ffdbab9d487a736a9278559378d7ab226d35ee647efcc5fad7a4dcb02`; executed workflow SHA256 `5ded94f1857d7228c54a24ee72dc8fc3e5d6faee0a23a6ca9773129522134ad4`.
Successful published 26973 APK SHA256 `4795b0e925f38a5f6162a5b7a79cb2a1acede84e089e543c289122942c7e3017`.

The exact successful 26973 workflow's historical preflight step prefix is byte-identical; new 26974 validations are additive. Historical 26886/26887, 26903 and 26904 V1/V2/V3, pinned real glslang SPIR-V validation AND optimization, current Kotlin/Java, dual ABI NDK/CMake and full `:app:assembleDebug` remain mandatory in Actions. There is no 26974 APK or Actions proof until the new workflow succeeds; no image quality/reliability claim may be inferred from compilation.

## Upload order (GitHub vscode.dev, NEVER upload stage folder itself)

Extract the four-group ZIP. Stage 1A and 1B: upload every file inside each folder at the exact original repository-relative paths, committing each stage before the next. Stage 2: upload ONLY `.github/workflows/build-26974-change-aware.yml`. Stage 3: upload ONLY `TRIGGER_26974.txt` to trigger the guarded Actions workflow. Keep on `experimental-clean-photon-rebuild`, not `dev`. No change to old protected files, no APK commits/pushes, no backup branch.

DO NOT upload until this package's physical tests/negative tests pass. Following successful Actions artifact publication, test one C shutter at 2 RAW frames first, then up to 30, confirming restored preview, C stage logs, RAW cleanup and a real JPEG at physical RAW native output dimensions. Controlled device trial is NOT production ready.

## V2 targeted correction — 44933304868 verification-order failure

The V1 Actions job failed at step 51 because the live SHA check ran after prepare-base (which installs original 26973) but before install (which installs 26974). V2 verifies both frozen base and candidate with --frozen at step 51 and preserves the same mandatory --live check after install. All 2,132 compiled-source runtime files, 4 original edits, 2,128 protected originals, donor and shader bytes are **unchanged**. All actual GLSL/SPIR-V, Kotlin/Java, dual-ABI NDK, assembleDebug and historical failure gates remain mandatory; 26974 is NOT BUILD-PROVEN until successful Actions + published artifact. V2 trigger text is changed to force a new Actions run.
