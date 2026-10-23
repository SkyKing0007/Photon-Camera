PHOTON 26873 — GUARDED VSCODE.DEV B GPU RESIDENCY HANDOFF

Branch: experimental-clean-photon-rebuild
Runtime authority: successful 26872 Actions 40016268244 / commit 7007f9cdf0d3fb8f5662467f82d394f5b41e256e / artifact 12528194015.
Successful authority candidate tar SHA256: 663cd8ebaf42adc7748efff3acbe5a9bf02e4d5b647911578df028579b908c4d
Inherited mechanics: exact successful 26872 17-stage guarded workflow, original language compilers and 2-ABI NDK and :app:assembleDebug.

EXACT CHANGED RUNTIME SCOPE (6 files):
 app/src/main/cpp/iris26864/Iris26864FrozenDirectRawrRunner.cpp
 app/src/main/cpp/iris26864/Iris26864RealRawrCoordinator.cpp
 app/src/main/cpp/iris26864/Iris26864RealRawrCoordinator.hpp
 app/src/main/cpp/iris26864/Iris26864TwoSlotRaw16Uploader.cpp
 app/src/main/cpp/iris26864/Iris26864TwoSlotRaw16Uploader.hpp
 app/version.properties
New candidate has 1995 files; 1989 protected from successful 26872 source.

26873 GPU OWNERSHIP CHANGE:
 B HDR+ Higher Quality can allocate one capture-scoped GPU R16_UINT image per NORMAL frame,
 uploading each once, pinning until synchronous RAWR/HDRq/AMaZE consumer completes.
 The EXACT proven two-slot upload path remains for insufficient memory or allocation failure,
 with same frame count and same HDRq output, not a fallback to original Photon processing.
 Wronski true2x keeps its original two slots; all 15 captured frames including LONG remain.
 No changes to pre-/post-shutter ZSL, AE, preview 26872 stripe, WB, HDRq kernels, DNG, UHDR.

LOCAL PROOF: exact 26872 compiled candidate manifest, six changes, 1989 protected,
 forward/rollback binary full-index 7/12/40 and ownership tests PASS.
 REAL 26873 GLSL/KOTLIN/JAVA/NDK/APK compilers NOT RUN LOCALLY; only Actions proves them.

VSCODE.DEV THREE COMMITS ONE PUSH NO BACKUP:
 1) Extract ZIP and upload all files at exact repo paths EXCEPT workflow YAML and TRIGGER_26873.txt.
    Commit; DO NOT PUSH YET.
 2) Upload .github/workflows/build-26873-iris-rawr.yml. Commit; DO NOT PUSH YET.
 3) Upload TRIGGER_26873.txt. Commit, then PUSH ONCE.

No APKs, direct app/src writes, backup branch, or local shell/PowerShell execution.
All runtime replacement files live under handoff_payload_26873/app/.
The successful 26872 compiled candidate is reconstructed by Actions and overlaid only on that exact universe.
