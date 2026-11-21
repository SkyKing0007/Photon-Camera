# Photon 26971 — Corrected high-zoom direct-CFA scalar-detail integrity

**State: PREPARED FOR GITHUB ACTIONS; NOT BUILD-PROVEN; no APK in this ZIP.**

## Exact runtime authority

Successful **26970 V3** Actions run `44810169651`, repository commit `43f22345400474b4999bb1073c7b8beb555fd4d0`, published artifact `14666627344` SHA-256 `d7221b656d10d91082775cdca4d2a4adf49b8e939ddbe3707ce40a35fe67510b`. Actual compiled candidate TAR SHA-256: `d7341c28816a35b23fb9b579f5908d732eb2829b0f248fe1bebbfa22a626ee2d`. Actual executed builder SHA-256: `e68a55372e17266d4d8916dbbd7b104dd79edfd24d98534bb15c7329683d5676`; workflow SHA-256: `bf7c875eec9c9576051edf778c6a4183e9100b8eecd44b107de6f879c2dc1a7c`; original 26970 APK SHA-256: `4d48aeb49a1a83a6b2e279b9b21a51def7733d1d33b2d70874c1d7ee6334885f`.

**Never reconstruct from stale `app/src` of the repository branch.** The guarded workflow downloads and verifies the exact official 26970 published artifact and extracts its actual compiled TAR before installing this candidate.

## Changes — solely Experiment A high-zoom scalar detail

The user's original 26970 JPEGs show strong RGB-proportional strips at 50.05× and 60.22×, whose projected 2× RAW sidecar locations intersect internal 64-row positions of 128-row GPU tiles. The actual 26970 processing logs select the frozen A Sabre/VGN stacker and optional high-zoom direct-CFA *luma* detail sidecar at these digital zooms; B HDRQ Wiener processing and the 26970 B-only grain logic are not used.

1. Preserve native Sabre/VGN RGB/chroma/highlight reconstruction, alignment, original shaders, reference frames and output tone. Existing high-zoom direct-CFA scalar sidecar is still computed.
2. Produce an independent second estimate from exactly the same RAW evidence with the 128/512 tile grid shifted by an initial 64-row/256-column tile, with even CFA origins. Compare final scalar outputs within 0.055 EV to detect tile-origin-dependent corruption.
3. Enforce the shader's 2×2 zero-DC intent: four high-amplitude same-sign log gains in a Bayer quad are unsupported regardless of whether two GPU passes agree. Reject NaN, infinity and out-of-contract values and half-float diagnostic codes.
4. A small doubtful region yields *zero optional log-detail* with a short transition into verified detail; that exposes exactly the preexisting native Sabre/VGN image there, not spatial blur or fabricated detail. If more than 5% is doubtful, whole optional sidecar is set to exact zero. Native carrier is unchanged.
5. Explicitly reset GL pixel pack row length, skip rows/pixels, read buffer and alignment before detail readback. A temporary second R16F sidecar is deleted on success/failure. No user-visible diagnostic APK/settings.

This is a **failure-containment correction**, not a proven fix for corruption originating upstream in Sabre/VGN or a systematic fault shared identically across both reconstructions and satisfying the zero-DC constraints. An original same-burst device RAW replay would be necessary for causal certainty.

## Exact source scope

2056 successful 26970 files → 2057 candidate files. Modified:
`app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker26850.kt`, `app/version.properties`. Added: `app/src/main/java/com/hinnka/mycamera/processor/Iris26971HighZoomDetailIntegrity.kt`. Exactly **2054 protected files unchanged**; all native/vendor/CMake/GLSL, SR ON, B OFF low-zoom HDRQ, DNG, Night, A tone/SDR/UHDR, Spektra protected.

## Upload exactly three stages with vscode.dev

Use branch **`experimental-clean-photon-rebuild`**, never `dev`. Open repository through vscode.dev and **upload ZIP contents extracted locally**, preserving relative folder structure. Do not upload this outer ZIP itself or the APK.

1. **Stage 1:** Upload all paths listed in `26971_STAGE_1_UPLOAD_PATHS.txt`, including the three `handoff_payload_26971/app/...` sources, hash/manifests, builder, tests, compiler and sealed workflow reference. Commit to the experimental branch only with the user's approval. All stage 1 sources are merely staged until step 3 triggers the workflow.
2. **Stage 2:** Upload `.github/workflows/build-26971-change-aware.yml` as the only file listed in `26971_STAGE_2_UPLOAD_PATHS.txt` and commit, again only with approval.
3. **Stage 3:** Upload **only** `TRIGGER_26971.txt` as listed in `26971_STAGE_3_UPLOAD_PATHS.txt` and commit. Only this last stage triggers the guarded build on the intended branch.

The workflow preserves the proven 26970 historical verification steps and all older 26886/26887, 26903 and 26904 regression gates. It executes real pinned glslang, SPIR-V validator/optimizer, the full two-ABI NDK/CMake build, Kotlin, Java and `:app:assembleDebug`; it publishes exactly one APK and compiled TAR **only if every gate passes**. Do not reduce compiler warnings/`-Werror` or skip expensive steps. Cache keys include full native source/runner provenance.

This is not device image-quality proof. The user does not need to install a diagnostic APK; if the Actions job succeeds the published 26971 APK is a production test candidate for normal capture comparison.
