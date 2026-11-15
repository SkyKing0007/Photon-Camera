# Photon 26940 V1 — Three-stage vscode.dev handoff — PREPARED FOR ACTIONS

**Strict runtime authority:** successful 26939 V1 GitHub Actions run `43719616599`, commit `04f76646776136206ff2d59684d25f5e57957e92`, artifact `14163927537` (`sha256:b30bf1157b34c5d30eb867405af92fd9ab6eb974c21112217ad600ca0b583c71`). Exact actually compiled 26939 candidate tar SHA-256: `db4f05d74c34c52b98ae5f91669ce9cf51df53bff6fe463941adf0ff2bcfdce4`.

**Scope:** 7 runtime changed files of 2050: 6 `app/src/main/cpp/iris26864/` files plus `app/version.properties`. Exactly 2043 protected files SHA-identical; no source files added/deleted; all pinned RAWR vendor, GLSL, Kotlin, Java, Spektra, native, LKR and DNG inputs unchanged.

**Behavior:** only the already-gated **Experiment B, Photo Super Res OFF, physical-lens-relative zoom below 1.10×, non-Night HDR+ Higher Quality** path borrows an isolated serialized Vulkan device and reusable RAWR `AndroidBurstCoordinator`. Its executor creates **32 required pipelines** (the full unused 23 Wronski-only shader pipelines are skipped exclusively inside this opted-in B OFF initialization). Reused coordinator releases its large HDR+ scratch arena at completion, and the original waited-fence/queue-idle protections and error quarantine remain. Super Res ON, A, A+B, Night, Motion, LONG, Spektra and >=1.10x routed A retain their original one-shot behavior. No image/math algorithm, RAW frame count, alignment, noise model, frequency merge, or color pipeline was changed.

### Mandatory upload order (one ZIP, three stages)

1. Extract ZIP and upload **every** `26940_V1_STAGE_1_UPLOAD_PATHS.txt` path to the exact path on branch `experimental-clean-photon-rebuild` using vscode.dev (never `dev`). Do **not** upload an APK. Upload only staged files, not this README separately beyond its inclusion in Stage 1.
2. Upload `.github/workflows/build-26940-change-aware.yml` from `26940_V1_STAGE_2_UPLOAD_PATHS.txt` after Stage 1 has committed.
3. Upload **only** `TRIGGER_26940.txt` last, from `26940_V1_STAGE_3_UPLOAD_PATHS.txt`, to trigger the single real protected Actions build.

Stage 1 alone is not a build. Stage 2 does not start the build. Stage 3 triggers Actions **after** staged source checks. Do not combine stages or modify source independently. No unnecessary backup branch. No automated source push or APK push.

### Verification authority

Inherited exactly the successful 26939 V1 guarded Actions graph, including SHA-pinned 141 historical commands, 26886/26887 regressions, 26903 archive receipt, 26904 V1/V2/V3 CMake and optimizer failure regressions, untouched 26935–26939 sealed regressions, actual SHA-addressed runner CMake cache, exact native RawLens from the published 26939 APK, real pinned GLSL 16.5.0/ESSL 300+310/SPIR-V compilation, real dual ABI NDK, Kotlin, Java, single Gradle `:app:assembleDebug`, original 26906 cache provenance tests, exact 26940 source manifests, full-index patches at 7/12/40, hash-sealed three-stage files, and completed APK + source TAR published together.

Android SDK, NDK and pinned GLSL toolchain intentionally run **inside GitHub Actions** and are mandatory; the absence of local Android tooling is not a handoff blocker. **PREPARED FOR ACTIONS** is not **BUILD-PROVEN**. The build must succeed and publish an artifact before any BUILD-PROVEN claim. Device latency and visual image quality are still unverified.

No repository source modifications, branch operations, workflow dispatches or user-account actions are performed by generating this prepared ZIP.
